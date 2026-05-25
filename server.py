#!/usr/bin/env python3
"""
eFaas Mock Server - A local mock of the eFaas OIDC/OAuth2 identity provider
for development and testing without relying on the official eFaas server.

Implements standard OpenID Connect / OAuth2 endpoints. Works with any
language or framework — Laravel, Express, Django, Rails, mobile apps, etc.

Usage:
    pip install -r requirements.txt
    python server.py

    # Or with custom config:
    SERVER_URL=http://localhost:5000 python server.py

Environment variables:
    SERVER_URL          - Base URL of this mock server (default: http://localhost:{PORT})
    PORT                - Port to listen on (default: 5000)
    HOST                - Host to bind to (default: 0.0.0.0)
    DEBUG               - Enable debug mode (default: false)
    RSA_PRIVATE_KEY_PEM - Optional; provide your own RSA private key in PEM format
    SEED_COUNT          - Number of pre-seeded accounts (default: 100)

Example app configuration to connect to this mock:
    client_id     = any-value
    client_secret = any-value
    redirect_uri  = http://localhost:8000/callback
    efaas_mode    = development
    efaas_api_url = http://localhost:5000

Endpoints (standard OIDC/OAuth2):
    GET  /connect/authorize                      - Authorization (login page)
    POST /connect/authorize                      - Login submission
    POST /connect/token                          - Token exchange
    POST /connect/userinfo                       - User info (Bearer token)
    GET  /.well-known/openid-configuration/jwks  - JWKS public keys
    GET  /connect/endsession                     - End session / logout
    GET  /user/photo                             - User avatar (base64 PNG)
    GET  /                                       - Server status
"""

import os
import json
import uuid
import hashlib
import time
import random
import io
import base64 as b64
from datetime import datetime, timedelta
from urllib.parse import urlencode
from typing import Any

from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import jwt
from jwt.utils import base64url_encode
from PIL import Image, ImageDraw, ImageFont
from jinja2 import Template

# ──────────────────────────────────────────────
# FastAPI app
# ──────────────────────────────────────────────
app = FastAPI(title="eFaas Mock Server", version="3.0.0")

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
_PORT = int(os.environ.get("PORT", 5000))
_HOST = os.environ.get("HOST", "0.0.0.0")
_raw_server_url = os.environ.get("SERVER_URL", "")
if not _raw_server_url:
    _raw_server_url = f"http://localhost:{_PORT}"
if "0.0.0.0" in _raw_server_url:
    _raw_server_url = _raw_server_url.replace("0.0.0.0", "localhost")
SERVER_URL = _raw_server_url.rstrip("/")
ACCESS_TOKEN_TTL = 3600
ID_TOKEN_TTL = 300
AUTH_CODE_TTL = 600
DEFAULT_SEED_COUNT = int(os.environ.get("SEED_COUNT", 100))

# ──────────────────────────────────────────────
# In-memory stores
# ──────────────────────────────────────────────
auth_codes: dict[str, dict] = {}
users: dict[str, dict] = {}
_avatar_cache: dict[str, str] = {}

# ──────────────────────────────────────────────
# RSA Key Generation
# ──────────────────────────────────────────────

def _ensure_keypair():
    key_path = os.environ.get("RSA_KEY_PATH", "")
    if key_path:
        with open(key_path, "rb") as f:
            return serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
    env_key = os.environ.get("RSA_PRIVATE_KEY_PEM", "")
    if env_key:
        return serialization.load_pem_private_key(env_key.encode(), password=None, backend=default_backend())
    return rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())

_private_key = _ensure_keypair()
_public_key = _private_key.public_key()

def _public_key_der() -> bytes:
    return _public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

def _compute_kid() -> str:
    return hashlib.sha1(_public_key_der()).hexdigest().upper() + "RS256"

KID = _compute_kid()

def _rsa_public_numbers():
    return _public_key.public_numbers()

# ──────────────────────────────────────────────
# JWK / JWKS helpers
# ──────────────────────────────────────────────

def _int_to_base64url(n: int) -> str:
    if n == 0:
        return "AA"
    length = (n.bit_length() + 7) // 8
    return base64url_encode(n.to_bytes(length, byteorder="big")).decode("ascii")

def _make_jwk() -> dict:
    n_val, e_val = _rsa_public_numbers().n, _rsa_public_numbers().e
    x5t = base64url_encode(hashlib.sha1(_public_key_der()).digest()).decode("ascii")
    return {
        "kty": "RSA", "use": "sig", "kid": KID, "x5t": x5t,
        "e": _int_to_base64url(e_val), "n": _int_to_base64url(n_val), "alg": "RS256",
    }

def _make_jwks() -> dict:
    return {"keys": [_make_jwk()]}

# ──────────────────────────────────────────────
# JWT helpers
# ──────────────────────────────────────────────

def _make_access_token(sub: str, sid: str, client_id: str, scope: str) -> str:
    now = int(time.time())
    claims = {
        "nbf": now, "exp": now + ACCESS_TOKEN_TTL, "iss": SERVER_URL,
        "client_id": client_id, "sub": sub, "auth_time": now,
        "idp": "local", "jti": str(uuid.uuid4()).upper(),
        "sid": sid, "iat": now,
        "scope": scope.split(" ") if scope else [], "amr": ["pwd"],
    }
    headers = {
        "alg": "RS256", "kid": KID, "typ": "at+jwt",
        "x5t": base64url_encode(hashlib.sha1(_public_key_der()).digest()).decode("ascii"),
    }
    return jwt.encode(claims, _private_key, algorithm="RS256", headers=headers)

def _make_id_token(sub: str, sid: str, client_id: str, nonce: str | None,
                   access_token: str, scope: str | None, user: dict) -> str:
    now = int(time.time())
    at_hash_bytes = hashlib.sha256(access_token.encode("ascii")).digest()
    at_hash = base64url_encode(at_hash_bytes[:16]).decode("ascii")

    claims: dict[str, Any] = {
        "nbf": now, "exp": now + ID_TOKEN_TTL, "iss": SERVER_URL,
        "aud": client_id, "iat": now, "at_hash": at_hash,
        "sid": sid, "sub": sub, "auth_time": now,
        "idp": "local", "amr": ["pwd"],
        "middle_name": user.get("middle_name", ""),
        "gender": user.get("gender", ""),
        "idnumber": user.get("idnumber", ""),
        "email": user.get("email", ""),
        "birthdate": user.get("birthdate", ""),
        "passport_number": user.get("passport_number", ""),
        "is_workpermit_active": user.get("is_workpermit_active", ""),
        "updated_at": user.get("updated_at", ""),
        "country_dialing_code": user.get("country_dialing_code", ""),
        "country_code": user.get("country_code", ""),
        "country_code_alpha3": user.get("country_code_alpha3", ""),
        "verified": user.get("verified", ""),
        "verification_type": user.get("verification_type", ""),
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "full_name": user.get("full_name", ""),
        "first_name_dhivehi": user.get("first_name_dhivehi", ""),
        "middle_name_dhivehi": user.get("middle_name_dhivehi", ""),
        "last_name_dhivehi": user.get("last_name_dhivehi", ""),
        "full_name_dhivehi": user.get("full_name_dhivehi", ""),
        "permanent_address": user.get("permanent_address", ""),
        "user_type_description": user.get("user_type_description", ""),
        "mobile": user.get("mobile", ""),
        "photo": user.get("photo", ""),
        "country_name": user.get("country_name", ""),
        "last_verified_date": user.get("last_verified_date", ""),
    }
    if nonce:
        claims["nonce"] = nonce
    headers = {
        "alg": "RS256", "kid": KID, "typ": "JWT",
        "x5t": base64url_encode(hashlib.sha1(_public_key_der()).digest()).decode("ascii"),
    }
    return jwt.encode(claims, _private_key, algorithm="RS256", headers=headers)

# ──────────────────────────────────────────────
# Random user generation
# ──────────────────────────────────────────────

MALE_FIRST = [
    "Ahmed", "Mohamed", "Ali", "Hussain", "Ibrahim", "Ismail", "Hassan",
    "Abdulla", "Yoosuf", "Adam", "Moosa", "Nashid", "Naushad", "Shiyam",
    "Aslam", "Faisal", "Shamoon", "Naazim", "Rishwan", "Ashraf", "Musthafa",
    "Nasir", "Naseer", "Saeed", "Shakeeb", "Shifaz", "Zuhair", "Zaid",
    "Yameen", "Asif", "Inash", "Shaheen", "Faris", "Nabeel",
]

FEMALE_FIRST = [
    "Mariyam", "Fathimath", "Aishath", "Aminath", "Khadheeja", "Hawwa",
    "Shifza", "Zuhura", "Noora", "Amina", "Shaheena", "Moomina", "Niuma",
    "Ameena", "Hafsa", "Malsa", "Saara", "Shaina", "Sajida", "Shaufa",
    "Jumana", "Eeman", "Layan", "Iba", "Shaa", "Nahidha", "Aisha",
    "Fathun", "Nasra", "Mariya",
]

LAST_NAMES = [
    "Ahmed", "Ali", "Hassan", "Hussain", "Ibrahim", "Ismail", "Mohamed",
    "Abdulla", "Adam", "Moosa", "Naseer", "Latheef", "Waheed", "Rasheed",
    "Haleem", "Hameed", "Sameer", "Shaheem", "Shafeeq", "Shakeeb",
    "Nasheed", "Naeem", "Imad", "Saeed", "Manik", "Didi", "Fulhu",
    "Najeeb", "Jameel", "Shareef", "Habeeb", "Faiz", "Nazim",
]

DHIVEHI_MALE_FIRST = [
    "އަހުމަދު", "މުހައްމަދު", "އަލީ", "ހުސެއިން", "އިބްރާހިމް",
    "އިސްމާއިލް", "ހަސަން", "އަބްދުﷲ", "ޔޫސުފް", "އާދަމް",
]

DHIVEHI_FEMALE_FIRST = [
    "މަރިޔަމް", "ފާތިމަތު", "އައިޝަތު", "އަމީނަތު", "ޚަދީޖާ",
    "ހައްވާ", "ޒުހުރާ", "ނޫރާ", "އާމިނާ", "ޝަހީނާ",
]

DHIVEHI_LAST = [
    "އަހުމަދު", "އަލީ", "ހަސަން", "ހުސެއިން", "އިބްރާހިމް",
    "މުހައްމަދު", "އަބްދުﷲ", "ލަތީފް", "ވަހީދު", "ރަޝީދު",
]

ISLANDS = [
    ("Male'", "މާލެ", "K", "ކ"), ("Addu", "އައްޑޫ", "S", "ސ"),
    ("Fuvahmulah", "ފުވައްމުލައް", "Gn", "ޏ"), ("Hithadhoo", "ހިތަދޫ", "S", "ސ"),
    ("Kulhudhuffushi", "ކުޅުދުއްފުށި", "HDh", "ހދ"),
    ("Thinadhoo", "ތިނަދޫ", "GDh", "ގދ"),
    ("Villingili", "ވިލިގިލި", "Gn", "ޏ"),
    ("Naifaru", "ނައިފަރު", "Lh", "ޅ"),
    ("Mahibadhoo", "މަހިބަދޫ", "ADh", "އދ"),
    ("Eydhafushi", "އޭދަފުށި", "B", "ބ"),
]

WARDS = [
    ("Maafannu", "M", "މ"), ("Henveiru", "H", "ހ"),
    ("Galolhu", "G", "ގ"), ("Machchangolhi", "Ma", "މަ"),
    ("Hulhumale'", "H", "ހ"), ("Villimale'", "V", "ވ"),
]

ADDRESS_LINES = [
    ("Sosun Magu", "ސޯސަން މަގު"), ("Ameenee Magu", "އަމީނީ މަގު"),
    ("Chandhanee Magu", "ޗަންދަނީ މަގު"), ("Fareedhee Magu", "ފަރީދީ މަގު"),
    ("Majeedhee Magu", "މަޖީދީ މަގު"), ("Buruzu Magu", "ބުރުޒު މަގު"),
    ("Mulee-aage", "މުލީއާގެ"), ("Gaskara", "ގަސްކަރަ"),
    ("Fehi Mahchangolhi", "ފެހި މަހުޗަންގޮޅި"),
]

_HOUSE_NAMES = [
    "Blue Light", "Ocean Villa", "Sunset", "Palm", "Coral", "Seabreeze",
    "Paradise", "Lagoon", "Shell", "Star", "Moonlight", "Sunrise",
    "Peacock", "Coconut", "Banyan", "Hibiscus", "Jasmine", "Lily",
]


def _random_date(start_year=1960, end_year=2005) -> str:
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{month}/{day}/{year}"


def _random_mobile() -> str:
    return f"{random.choice([7, 9])}{random.randint(100000, 999999)}"


def _make_maldivian_address() -> str:
    addr = random.choice(ADDRESS_LINES)
    island = random.choice(ISLANDS)
    ward = random.choice(WARDS)
    house = random.choice(_HOUSE_NAMES)
    num = random.randint(1, 99)
    return json.dumps({
        "AddressLine1": house,
        "AddressLine2": f"{addr[0]} {num}",
        "Road": addr[0],
        "AtollAbbreviation": island[2],
        "AtollAbbreviationDhivehi": island[3],
        "IslandName": island[0],
        "IslandNameDhivehi": island[1],
        "HomeNameDhivehi": "",
        "Ward": ward[0],
        "WardAbbreviationEnglish": ward[1],
        "WardAbbreviationDhivehi": ward[2],
        "Country": "Maldives",
        "CountryISOThreeDigitCode": "462",
        "CountryISOThreeLetterCode": "MDV",
    })


def generate_user(user_type: str | None = None) -> dict:
    if user_type is None:
        user_type = random.choices(
            ["Maldivian", "Work Permit Holder", "Foreigner"],
            weights=[60, 25, 15],
        )[0]

    is_male = random.choice([True, False])
    gender = "M" if is_male else "F"

    if is_male:
        first_name = random.choice(MALE_FIRST)
        first_name_dhivehi = random.choice(DHIVEHI_MALE_FIRST)
    else:
        first_name = random.choice(FEMALE_FIRST)
        first_name_dhivehi = random.choice(DHIVEHI_FEMALE_FIRST)

    middle_name = random.choice(MALE_FIRST + FEMALE_FIRST) if random.random() > 0.6 else ""
    last_name = random.choice(LAST_NAMES)
    middle_name_dhivehi = random.choice(DHIVEHI_MALE_FIRST + DHIVEHI_FEMALE_FIRST) if middle_name else ""
    last_name_dhivehi = random.choice(DHIVEHI_LAST)

    full_name = f"{first_name} {middle_name} {last_name}".replace("  ", " ").strip()
    full_name_dhivehi = f"{first_name_dhivehi} {middle_name_dhivehi} {last_name_dhivehi}".replace("  ", " ").strip()

    birthdate = _random_date()
    mobile = _random_mobile()

    if user_type == "Maldivian":
        idnumber = f"A{random.randint(100000, 999999)}"
        passport_number = ""
        is_workpermit_active = "False"
        country_name = "Maldives"
        country_code = "462"
        country_code_alpha3 = "MDV"
        country_dialing_code = "+960"
    elif user_type == "Work Permit Holder":
        idnumber = f"WP{random.randint(100000, 999999)}"
        passport_number = f"{random.choice('ABCDEFGHJKLMNP')}{random.randint(1000000, 9999999)}"
        is_workpermit_active = random.choice(["True", "False"])
        country_name = random.choice(["Bangladesh", "India", "Sri Lanka", "Nepal", "Philippines"])
        country_code = {"Bangladesh": "050", "India": "356", "Sri Lanka": "144", "Nepal": "524", "Philippines": "608"}[country_name]
        country_code_alpha3 = {"Bangladesh": "BGD", "India": "IND", "Sri Lanka": "LKA", "Nepal": "NPL", "Philippines": "PHL"}[country_name]
        country_dialing_code = {"Bangladesh": "+880", "India": "+91", "Sri Lanka": "+94", "Nepal": "+977", "Philippines": "+63"}[country_name]
    else:
        idnumber = f"{random.choice('ABCDEFGHJKLMNP')}{random.randint(1000000, 9999999)}"
        passport_number = idnumber
        is_workpermit_active = "False"
        country_name = random.choice(["United Kingdom", "Germany", "France", "Italy", "China", "Japan", "Australia", "USA"])
        country_code = {"United Kingdom": "826", "Germany": "276", "France": "250", "Italy": "380", "China": "156", "Japan": "392", "Australia": "036", "USA": "840"}[country_name]
        country_code_alpha3 = {"United Kingdom": "GBR", "Germany": "DEU", "France": "FRA", "Italy": "ITA", "China": "CHN", "Japan": "JPN", "Australia": "AUS", "USA": "USA"}[country_name]
        country_dialing_code = {"United Kingdom": "+44", "Germany": "+49", "France": "+33", "Italy": "+39", "China": "+86", "Japan": "+81", "Australia": "+61", "USA": "+1"}[country_name]

    email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@example.com"

    verified = random.choice(["True", "False"])
    verification_type = "biometric" if verified == "True" else random.choice(["in-person", "NA"])

    last_verified_date = ""
    if verified == "True":
        last_verified = datetime(random.randint(2019, 2024), random.randint(1, 12), random.randint(1, 28),
                                 random.randint(8, 18), random.randint(0, 59), random.randint(0, 59))
        last_verified_date = last_verified.strftime("%m/%d/%Y %I:%M:%S %p")

    updated_at = datetime(random.randint(2022, 2025), random.randint(1, 12), random.randint(1, 28),
                          random.randint(8, 18), random.randint(0, 59), random.randint(0, 59))
    updated_at_str = updated_at.strftime("%m/%d/%Y %I:%M:%S %p")

    permanent_address = _make_maldivian_address()

    return {
        "sub": str(uuid.uuid4()),
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "full_name": full_name,
        "first_name_dhivehi": first_name_dhivehi,
        "middle_name_dhivehi": middle_name_dhivehi,
        "last_name_dhivehi": last_name_dhivehi,
        "full_name_dhivehi": full_name_dhivehi,
        "gender": gender,
        "idnumber": idnumber,
        "email": email,
        "birthdate": birthdate,
        "passport_number": passport_number,
        "is_workpermit_active": is_workpermit_active,
        "updated_at": updated_at_str,
        "country_dialing_code": country_dialing_code,
        "country_code": country_code,
        "country_code_alpha3": country_code_alpha3,
        "verified": verified,
        "verification_type": verification_type,
        "permanent_address": permanent_address,
        "user_type_description": user_type,
        "mobile": mobile,
        "photo": f"{SERVER_URL}/user/photo",
        "country_name": country_name,
        "last_verified_date": last_verified_date,
        "name": full_name,
        "avatar": f"{SERVER_URL}/user/photo",
        "nickname": first_name,
    }


def seed_users(count: int = DEFAULT_SEED_COUNT):
    for _ in range(count):
        user = generate_user()
        users[user["sub"]] = user
    test_user = {
        "sub": "3b46dc4b-f565-420b-af8f-9312c86e40cb",
        "first_name": "CSC", "middle_name": "Test User", "last_name": "18",
        "full_name": "CSC Test User 18",
        "first_name_dhivehi": "ސީއެސްސީ",
        "middle_name_dhivehi": "ޓެސްޓް ޔޫސަރ",
        "last_name_dhivehi": "18",
        "full_name_dhivehi": "ސީއެސްސީ ޓެސްޓް ޔޫސަރ 18",
        "gender": "M", "idnumber": "A900318", "email": "csc318@gmail.com",
        "birthdate": "10/22/1993", "passport_number": "LA19E7432",
        "is_workpermit_active": "False", "updated_at": "1/2/1995 12:00:00 AM",
        "country_dialing_code": "+960", "country_code": "462", "country_code_alpha3": "MDV",
        "verified": "False", "verification_type": "NA",
        "permanent_address": json.dumps({
            "AddressLine1": "asd", "AddressLine2": "", "Road": "",
            "AtollAbbreviation": "K", "AtollAbbreviationDhivehi": "ކ",
            "IslandName": "Male'", "IslandNameDhivehi": "މާލެ",
            "HomeNameDhivehi": "", "Ward": "Dhaftharu",
            "WardAbbreviationEnglish": "Dhaftharu", "WardAbbreviationDhivehi": "",
            "Country": "Maldives", "CountryISOThreeDigitCode": "462", "CountryISOThreeLetterCode": "MDV",
        }),
        "user_type_description": "Maldivian", "mobile": "7730018",
        "photo": f"{SERVER_URL}/user/photo", "country_name": "Maldives",
        "last_verified_date": "", "name": "CSC Test User 18",
        "avatar": f"{SERVER_URL}/user/photo", "nickname": "CSC",
    }
    users[test_user["sub"]] = test_user


seed_users()

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _cleanup_expired_codes():
    now = time.time()
    expired = [c for c, d in auth_codes.items() if d["expires_at"] < now]
    for c in expired:
        del auth_codes[c]


def _get_user_list(search: str = "", sort: str = "name") -> list[dict]:
    uu = list(users.values())
    if search:
        q = search.lower()
        uu = [u for u in uu
              if q in u.get("full_name", "").lower()
              or q in u.get("email", "").lower()
              or q in u.get("idnumber", "").lower()
              or q in u.get("user_type_description", "").lower()
              or q in u.get("first_name", "").lower()
              or q in u.get("last_name", "").lower()
              or q in u.get("first_name_dhivehi", "")]
    if sort == "name":
        uu.sort(key=lambda u: u.get("full_name", ""))
    elif sort == "recent":
        uu.sort(key=lambda u: u.get("sub", ""), reverse=True)
    elif sort == "type":
        uu.sort(key=lambda u: u.get("user_type_description", ""))
    return uu


def _oauth_params(request: Request) -> dict:
    """Extract common OAuth2 params from query params (falls back to defaults)."""
    return {
        "client_id": request.query_params.get("client_id", ""),
        "redirect_uri": request.query_params.get("redirect_uri", ""),
        "scope": request.query_params.get("scope", "openid"),
        "state": request.query_params.get("state", ""),
        "nonce": request.query_params.get("nonce", ""),
        "response_type": request.query_params.get("response_type", "code id_token"),
        "response_mode": request.query_params.get("response_mode", "form_post"),
        "code_challenge": request.query_params.get("code_challenge", ""),
        "code_challenge_method": request.query_params.get("code_challenge_method", ""),
    }


def _photo_url(request: Request) -> str:
    host = request.headers.get("host", "")
    scheme = request.url.scheme or "http"
    if host:
        return f"{scheme}://{host}/user/photo"
    return f"{SERVER_URL}/user/photo"


def _html(template_str: str, status_code: int = 200, **kwargs) -> HTMLResponse:
    return HTMLResponse(content=Template(template_str).render(**kwargs), status_code=status_code)


def _error_html(message: str, detail: str = "", status_code: int = 400) -> HTMLResponse:
    body = f"<h3>{message}</h3>" + (f"<p>{detail}</p>" if detail else "")
    return HTMLResponse(content=body, status_code=status_code)


# ──────────────────────────────────────────────
# Templates
# ──────────────────────────────────────────────

LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>eFaas Mock — Login</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background: #f0f2f5; color: #333; min-height: 100vh; }
  .banner { background: linear-gradient(135deg,#1a237e,#283593); color: #fff; padding: 16px 24px; text-align: center; font-size: 13px; }
  .banner strong { font-size: 16px; }
  .container { max-width: 960px; margin: 0 auto; padding: 24px 16px; }
  .tabs { display: flex; gap: 4px; margin-bottom: 24px; }
  .tab { flex: 1; padding: 12px; text-align: center; background: #e8eaed; border-radius: 8px 8px 0 0; cursor: pointer; font-weight: 600; font-size: 14px; transition: background .2s; user-select: none; }
  .tab.active { background: #fff; color: #1a237e; }
  .tab:hover:not(.active) { background: #d2d5d9; }
  .panel { display: none; background: #fff; border-radius: 0 0 12px 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
  .panel.active { display: block; }
  .search-box { width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; margin-bottom: 16px; outline: none; transition: border-color .2s; }
  .search-box:focus { border-color: #1a237e; }
  .user-grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(280px,1fr)); gap: 10px; max-height: 440px; overflow-y: auto; padding-right: 4px; }
  .user-card { border: 2px solid #e8eaed; border-radius: 8px; padding: 12px 14px; cursor: pointer; transition: all .15s; }
  .user-card:hover { border-color: #1a237e; background: #f5f6ff; box-shadow: 0 1px 6px rgba(26,35,126,.08); }
  .user-card.selected { border-color: #1a237e; background: #e8eaff; }
  .user-card .name { font-weight: 600; font-size: 14px; }
  .user-card .meta { font-size: 12px; color: #666; margin-top: 2px; }
  .user-card .type { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 10px; margin-top: 4px; }
  .type-maldivian { background: #e8f5e9; color: #2e7d32; }
  .type-workpermit { background: #fff3e0; color: #e65100; }
  .type-foreigner { background: #e3f2fd; color: #1565c0; }
  .results-info { font-size: 13px; color: #888; margin-bottom: 10px; }
  .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 16px; }
  .form-grid .full { grid-column: 1 / -1; }
  label { display: block; font-size: 13px; font-weight: 600; color: #555; margin-bottom: 4px; }
  input, select { width: 100%; padding: 10px 12px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 14px; outline: none; transition: border-color .2s; }
  input:focus, select:focus { border-color: #1a237e; }
  .btn { display: inline-flex; align-items: center; justify-content: center; padding: 12px 24px; font-size: 14px; font-weight: 600; border: none; border-radius: 8px; cursor: pointer; transition: all .15s; }
  .btn-primary { background: #1a237e; color: #fff; width: 100%; margin-top: 8px; }
  .btn-primary:hover { background: #283593; transform: translateY(-1px); box-shadow: 0 2px 8px rgba(26,35,126,.3); }
  .actions { display: flex; gap: 10px; margin-top: 20px; }
  .actions .btn { flex: 1; }
  .subtitle { font-size: 13px; color: #888; margin-bottom: 20px; }
  .no-results { text-align: center; padding: 40px; color: #999; font-size: 14px; }
  .pick-hint { font-size: 13px; color: #888; margin-bottom: 16px; text-align: center; }
  .selected-info { background: #e8eaff; border: 2px solid #1a237e; border-radius: 8px; padding: 10px 14px; margin-top: 14px; font-size: 13px; display: none; }
  .selected-info.show { display: block; }
</style>
</head>
<body>
<div class="banner">
  <strong>eFaas Mock Server</strong> — Development only. No real authentication.
</div>
<div class="container">

  <div class="tabs">
    <div class="tab active" onclick="switchTab('select')">Select Existing User <small>({{ total_users }})</small></div>
    <div class="tab" onclick="switchTab('create')">Create New User</div>
  </div>

  <div id="panel-select" class="panel active">
    <input type="text" class="search-box" id="search" placeholder="Search by name, email, ID number, type…" oninput="filterUsers()">
    <div class="results-info" id="results-info">Showing {{ total_users }} users</div>
    <div class="pick-hint" id="pick-hint">Select a user below, then click <strong>Sign In as Selected User</strong></div>
    <div class="user-grid" id="user-grid">
      {% for u in user_list %}
      <div class="user-card" data-sub="{{ u.sub }}" data-search="{{ u.full_name|lower }} {{ u.email|lower }} {{ u.idnumber|lower }} {{ u.user_type_description|lower }} {{ u.first_name|lower }} {{ u.last_name|lower }} {{ u.first_name_dhivehi }}" onclick="selectUser('{{ u.sub }}', this)">
        <div class="name">{{ u.full_name or u.first_name + ' ' + (u.middle_name or '') + ' ' + u.last_name }}</div>
        <div class="meta">{{ u.email }} &middot; {{ u.idnumber }}</div>
        <span class="type {% if u.user_type_description == 'Maldivian' %}type-maldivian{% elif u.user_type_description == 'Work Permit Holder' %}type-workpermit{% else %}type-foreigner{% endif %}">{{ u.user_type_description }}</span>
      </div>
      {% endfor %}
    </div>
    <div class="no-results" id="no-results" style="display:none">No users match your search.</div>

    <div class="selected-info" id="selected-info"></div>

    <form method="post" id="select-form">
      {% for key, val in params.items() %}
      <input type="hidden" name="{{ key }}" value="{{ val }}">
      {% endfor %}
      <input type="hidden" name="action" value="select">
      <input type="hidden" name="sub" id="selected-sub" value="">
      <button type="submit" class="btn btn-primary" id="btn-select" disabled>Sign In as Selected User</button>
    </form>
  </div>

  <div id="panel-create" class="panel">
    <p class="subtitle">Fill in the details below to create a new account. All new accounts are saved and reusable.</p>
    <form method="post" id="create-form">
      {% for key, val in params.items() %}
      <input type="hidden" name="{{ key }}" value="{{ val }}">
      {% endfor %}
      <input type="hidden" name="action" value="create">
      <div class="form-grid">
        <div><label>First Name *</label><input name="first_name" required placeholder="Ahmed"></div>
        <div><label>Last Name *</label><input name="last_name" required placeholder="Rasheed"></div>
        <div><label>Middle Name</label><input name="middle_name" placeholder="Ali"></div>
        <div><label>Gender *</label><select name="gender" required><option value="M">Male</option><option value="F">Female</option></select></div>
        <div><label>First Name (Dhivehi)</label><input name="first_name_dhivehi" placeholder="އަހުމަދު"></div>
        <div><label>Last Name (Dhivehi)</label><input name="last_name_dhivehi" placeholder="ރަޝީދު"></div>
        <div><label>ID Number *</label><input name="idnumber" required placeholder="A123456"></div>
        <div><label>User Type *</label><select name="user_type_description" id="user-type" required onchange="toggleFields()"><option value="Maldivian">Maldivian</option><option value="Work Permit Holder">Work Permit Holder</option><option value="Foreigner">Foreigner</option></select></div>
        <div><label>Email *</label><input type="email" name="email" required placeholder="ahmed@example.com"></div>
        <div><label>Mobile *</label><input name="mobile" required placeholder="7912345"></div>
        <div><label>Birthdate *</label><input name="birthdate" required placeholder="6/3/1990" value="6/3/1990"></div>
        <div><label>Country</label><input name="country_name" id="country-name" value="Maldives" placeholder="Maldives"></div>
        <div id="passport-group" style="display:none"><label>Passport Number</label><input name="passport_number" placeholder="LA19E7432"></div>
        <div id="workpermit-group" style="display:none"><label>Work Permit Active</label><select name="is_workpermit_active"><option value="True">Yes</option><option value="False">No</option></select></div>
        <div class="full"><label>Permanent Address (JSON)</label><input name="permanent_address_json" placeholder='{"AddressLine1":"Blue Light","IslandName":"Male&apos;","Country":"Maldives",...}'></div>
      </div>
      <div class="actions"><button type="submit" class="btn btn-primary">Create User &amp; Sign In</button></div>
    </form>
  </div>

</div>

<script>
var selectedSub = null;
function switchTab(tab) {
  document.querySelectorAll('.tab').forEach(function(t,i){
    t.classList.toggle('active', (tab==='select'&&i===0)||(tab==='create'&&i===1));
  });
  document.getElementById('panel-select').classList.toggle('active', tab==='select');
  document.getElementById('panel-create').classList.toggle('active', tab==='create');
}
function selectUser(sub, el) {
  document.querySelectorAll('.user-card').forEach(function(c){ c.classList.remove('selected'); });
  el.classList.add('selected');
  document.getElementById('selected-sub').value = sub;
  document.getElementById('btn-select').disabled = false;
  selectedSub = sub;
  var u = el.querySelector('.name').textContent;
  document.getElementById('selected-info').innerHTML = '<strong>Selected:</strong> ' + u + ' (sub: ' + sub.substring(0,8) + '…)';
  document.getElementById('selected-info').classList.add('show');
}
function filterUsers() {
  var q = document.getElementById('search').value.toLowerCase();
  var cards = document.querySelectorAll('.user-card');
  var count = 0;
  cards.forEach(function(c){
    var match = c.getAttribute('data-search').indexOf(q) !== -1;
    c.style.display = match ? '' : 'none';
    if (match) count++;
  });
  document.getElementById('results-info').textContent = q ? 'Found ' + count + ' user(s)' : 'Showing {{ total_users }} users';
  document.getElementById('no-results').style.display = count === 0 ? '' : 'none';
  document.getElementById('pick-hint').style.display = count === 0 ? 'none' : '';
}
function toggleFields() {
  var t = document.getElementById('user-type').value;
  document.getElementById('passport-group').style.display = (t==='Work Permit Holder'||t==='Foreigner') ? '' : 'none';
  document.getElementById('workpermit-group').style.display = (t==='Work Permit Holder') ? '' : 'none';
}
</script>
</body>
</html>"""

AUTO_POST_TEMPLATE = """<!DOCTYPE html>
<html>
<head><title>eFaas Mock — Redirecting…</title></head>
<body onload="document.getElementById('cb').submit()">
  <p style="font-family:sans-serif;text-align:center;padding-top:40px">Signing in, please wait…</p>
  <form id="cb" method="post" action="{{ redirect_uri }}">
    <input type="hidden" name="code" value="{{ code }}">
    <input type="hidden" name="id_token" value="{{ id_token }}">
    <input type="hidden" name="scope" value="{{ scope }}">
    <input type="hidden" name="session_state" value="{{ session_state }}">
    {% if state %}<input type="hidden" name="state" value="{{ state }}">{% endif %}
  </form>
</body>
</html>"""


def _do_login(sub: str, oauth: dict, request: Request):
    if not oauth.get("redirect_uri"):
        return _error_html("Missing redirect_uri",
                           "Cannot complete login without a redirect URI.", 400)
    if sub not in users:
        return _error_html("User not found.", status_code=400)

    user = users[sub]
    code = str(uuid.uuid4()).replace("-", "")
    sid = str(uuid.uuid4()).replace("-", "").upper()[:32]

    access_token = _make_access_token(sub, sid, oauth["client_id"], oauth["scope"])
    id_token = _make_id_token(sub, sid, oauth["client_id"], oauth.get("nonce"),
                              access_token, oauth["scope"], user)

    auth_codes[code] = {
        "client_id": oauth["client_id"],
        "redirect_uri": oauth["redirect_uri"],
        "scope": oauth["scope"],
        "nonce": oauth.get("nonce"),
        "state": oauth.get("state"),
        "expires_at": time.time() + AUTH_CODE_TTL,
        "user_sub": sub,
        "user": user,
        "sid": sid,
        "access_token": access_token,
        "code_challenge": oauth.get("code_challenge", ""),
        "code_challenge_method": oauth.get("code_challenge_method", ""),
    }

    session_state = f"{uuid.uuid4().hex}.{uuid.uuid4().hex}"

    if request.headers.get("accept", "").startswith("application/json"):
        return JSONResponse({
            "code": code, "id_token": id_token, "scope": oauth["scope"],
            "session_state": session_state, "state": oauth.get("state", ""),
        })

    return _html(AUTO_POST_TEMPLATE,
        redirect_uri=oauth["redirect_uri"],
        code=code, id_token=id_token,
        scope=oauth["scope"],
        session_state=session_state,
        state=oauth.get("state", ""),
    )


# ──────────────────────────────────────────────
# Route handlers
# ──────────────────────────────────────────────

@app.get("/")
def index():
    return {
        "service": "eFaas Mock Server",
        "version": "3.0.0",
        "framework": "FastAPI",
        "issuer": SERVER_URL,
        "total_users": len(users),
        "endpoints": {
            "authorization": f"{SERVER_URL}/connect/authorize",
            "token": f"{SERVER_URL}/connect/token",
            "userinfo": f"{SERVER_URL}/connect/userinfo",
            "jwks": f"{SERVER_URL}/.well-known/openid-configuration/jwks",
            "end_session": f"{SERVER_URL}/connect/endsession",
        },
        "key_id": KID,
    }


@app.get("/connect/authorize")
def authorize_get(request: Request,
                  search: str = Query(default=""),
                  sort: str = Query(default="name")):
    _cleanup_expired_codes()
    oauth = _oauth_params(request)
    user_list = _get_user_list(search=search, sort=sort)
    return _html(LOGIN_PAGE,
        params=oauth, user_list=user_list, total_users=len(users))


@app.post("/connect/authorize")
async def authorize_post(request: Request):
    _cleanup_expired_codes()
    form = await request.form()

    # Guard: reject stray callback POSTs (have code/id_token but no login action)
    has_callback_fields = bool(form.get("code") or form.get("id_token"))
    has_action = bool((form.get("action") or "").strip())
    if has_callback_fields and not has_action:
        return _error_html("Invalid request",
                           "This endpoint expects a login form submission.", 400)

    # Merge query params into form for OAuth params (form includes hidden fields)
    oauth = _oauth_params(request)
    for key in oauth:
        if key in form:
            oauth[key] = form[key]

    action = form.get("action", "auto")

    if action == "select":
        sub = form.get("sub", "")
        if sub not in users:
            sub = next(iter(users.keys()), "")
            if not sub:
                return _error_html("No users available. Please create one first.", status_code=400)
        return _do_login(sub, oauth, request)

    elif action == "create":
        return _handle_create_user(oauth, form, request)

    else:
        if not oauth.get("redirect_uri"):
            return _error_html("Missing redirect_uri",
                               "Make sure you are logging in through your application.", 400)
        sub = next(iter(users.keys()), str(uuid.uuid4()))
        if sub not in users:
            user = generate_user()
            users[user["sub"]] = user
            sub = user["sub"]
        return _do_login(sub, oauth, request)


def _handle_create_user(oauth: dict, form, request: Request):
    first_name = (form.get("first_name") or "").strip()
    last_name = (form.get("last_name") or "").strip()
    if not first_name or not last_name:
        return _error_html("First name and last name are required.", status_code=400)

    middle_name = (form.get("middle_name") or "").strip()
    gender = form.get("gender", "M")
    idnumber = (form.get("idnumber") or "").strip()
    email = (form.get("email") or "").strip()
    mobile = (form.get("mobile") or "").strip()
    birthdate = form.get("birthdate", "1/1/1990")
    user_type = form.get("user_type_description", "Maldivian")
    country_name = form.get("country_name", "Maldives")
    passport_number = (form.get("passport_number") or "").strip()
    is_workpermit_active = form.get("is_workpermit_active", "False")
    first_name_dhivehi = (form.get("first_name_dhivehi") or "").strip()
    last_name_dhivehi = (form.get("last_name_dhivehi") or "").strip()
    middle_name_dhivehi = (form.get("middle_name_dhivehi") or "").strip()
    permanent_address_json = (form.get("permanent_address_json") or "").strip()

    full_name = f"{first_name} {middle_name} {last_name}".replace("  ", " ").strip()
    full_name_dhivehi = f"{first_name_dhivehi} {middle_name_dhivehi} {last_name_dhivehi}".replace("  ", " ").strip()

    if permanent_address_json:
        try:
            json.loads(permanent_address_json)
        except json.JSONDecodeError:
            return _error_html("Invalid JSON in permanent address field.", status_code=400)
    else:
        permanent_address_json = json.dumps({
            "AddressLine1": "", "AddressLine2": "", "Road": "",
            "AtollAbbreviation": "K", "AtollAbbreviationDhivehi": "ކ",
            "IslandName": "Male'", "IslandNameDhivehi": "މާލެ",
            "HomeNameDhivehi": "", "Ward": "Maafannu",
            "WardAbbreviationEnglish": "M", "WardAbbreviationDhivehi": "މ",
            "Country": country_name, "CountryISOThreeDigitCode": "462",
            "CountryISOThreeLetterCode": "MDV",
        })

    country_codes = {
        "Maldives": ("462", "MDV", "+960"),
        "Bangladesh": ("050", "BGD", "+880"), "India": ("356", "IND", "+91"),
        "Sri Lanka": ("144", "LKA", "+94"), "Nepal": ("524", "NPL", "+977"),
        "Philippines": ("608", "PHL", "+63"),
        "United Kingdom": ("826", "GBR", "+44"), "Germany": ("276", "DEU", "+49"),
        "France": ("250", "FRA", "+33"), "Italy": ("380", "ITA", "+39"),
        "China": ("156", "CHN", "+86"), "Japan": ("392", "JPN", "+81"),
        "Australia": ("036", "AUS", "+61"), "USA": ("840", "USA", "+1"),
    }
    cc = country_codes.get(country_name, ("462", "MDV", "+960"))

    user_sub = str(uuid.uuid4())
    user = {
        "sub": user_sub, "first_name": first_name, "middle_name": middle_name,
        "last_name": last_name, "full_name": full_name,
        "first_name_dhivehi": first_name_dhivehi, "middle_name_dhivehi": middle_name_dhivehi,
        "last_name_dhivehi": last_name_dhivehi, "full_name_dhivehi": full_name_dhivehi,
        "gender": gender, "idnumber": idnumber, "email": email,
        "birthdate": birthdate, "passport_number": passport_number,
        "is_workpermit_active": is_workpermit_active,
        "updated_at": datetime.now().strftime("%m/%d/%Y %I:%M:%S %p"),
        "country_dialing_code": cc[2], "country_code": cc[0], "country_code_alpha3": cc[1],
        "verified": "False", "verification_type": "NA",
        "permanent_address": permanent_address_json,
        "user_type_description": user_type, "mobile": mobile,
        "photo": f"{SERVER_URL}/user/photo", "country_name": country_name,
        "last_verified_date": "", "name": full_name,
        "avatar": f"{SERVER_URL}/user/photo", "nickname": first_name,
    }

    users[user_sub] = user
    return _do_login(user_sub, oauth, request)


@app.post("/connect/token")
async def token(request: Request):
    _cleanup_expired_codes()
    form = await request.form()

    grant_type = form.get("grant_type", "")
    code = form.get("code", "")

    if grant_type != "authorization_code":
        return JSONResponse({"error": "unsupported_grant_type"}, 400)

    if code not in auth_codes:
        return JSONResponse({"error": "invalid_grant",
                             "error_description": "Invalid or expired authorization code"}, 400)

    stored = auth_codes[code]

    if stored.get("code_challenge"):
        code_verifier = form.get("code_verifier", "")
        method = stored.get("code_challenge_method", "S256")
        if method == "S256":
            expected = base64url_encode(
                hashlib.sha256(code_verifier.encode("ascii")).digest()
            ).decode("ascii")
        else:
            expected = code_verifier
        if expected != stored["code_challenge"]:
            return JSONResponse({"error": "invalid_grant",
                                 "error_description": "PKCE validation failed"}, 400)

    del auth_codes[code]

    return {
        "id_token": _make_id_token(
            stored["user_sub"], stored["sid"], stored["client_id"],
            stored.get("nonce"), stored["access_token"],
            stored["scope"], stored["user"],
        ),
        "access_token": stored["access_token"],
        "expires_in": ACCESS_TOKEN_TTL,
        "token_type": "Bearer",
        "scope": stored["scope"],
    }


@app.post("/connect/userinfo")
@app.get("/connect/userinfo")
def userinfo(request: Request):
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse({"error": "invalid_token"}, 401)

    token = auth_header[7:]
    try:
        claims = jwt.decode(token, _public_key, algorithms=["RS256"],
                           options={"verify_exp": True, "verify_aud": False})
    except jwt.ExpiredSignatureError:
        return JSONResponse({"error": "invalid_token", "error_description": "Token expired"}, 401)
    except jwt.InvalidTokenError:
        return JSONResponse({"error": "invalid_token", "error_description": "Token validation failed"}, 401)

    sub = claims.get("sub", "")
    user = users.get(sub, generate_user())

    return {
        "sub": user.get("sub", ""),
        "middle_name": user.get("middle_name", ""),
        "gender": user.get("gender", ""),
        "idnumber": user.get("idnumber", ""),
        "email": user.get("email", ""),
        "birthdate": user.get("birthdate", ""),
        "passport_number": user.get("passport_number", ""),
        "is_workpermit_active": user.get("is_workpermit_active", ""),
        "updated_at": user.get("updated_at", ""),
        "country_dialing_code": user.get("country_dialing_code", ""),
        "country_code": user.get("country_code", ""),
        "country_code_alpha3": user.get("country_code_alpha3", ""),
        "verified": user.get("verified", ""),
        "verification_type": user.get("verification_type", ""),
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "full_name": user.get("full_name", ""),
        "first_name_dhivehi": user.get("first_name_dhivehi", ""),
        "middle_name_dhivehi": user.get("middle_name_dhivehi", ""),
        "last_name_dhivehi": user.get("last_name_dhivehi", ""),
        "full_name_dhivehi": user.get("full_name_dhivehi", ""),
        "permanent_address": user.get("permanent_address", ""),
        "user_type_description": user.get("user_type_description", ""),
        "mobile": user.get("mobile", ""),
        "photo": _photo_url(request),
        "country_name": user.get("country_name", ""),
        "last_verified_date": user.get("last_verified_date", ""),
    }


@app.get("/.well-known/openid-configuration/jwks")
def jwks():
    return _make_jwks()


@app.get("/connect/endsession")
def endsession(
    post_logout_redirect_uri: str = Query(default=""),
    state: str = Query(default=""),
):
    if post_logout_redirect_uri:
        params = {}
        if state:
            params["state"] = state
        sep = "&" if "?" in post_logout_redirect_uri else "?"
        return RedirectResponse(url=post_logout_redirect_uri + sep + urlencode(params))
    return {"message": "Logged out successfully"}


@app.get("/user/photo")
def user_photo(request: Request):
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return {"data": {"photo": _generate_avatar_png(None, None, None)}}

    token = auth_header[7:]
    try:
        claims = jwt.decode(token, _public_key, algorithms=["RS256"],
                           options={"verify_exp": True, "verify_aud": False})
    except jwt.InvalidTokenError:
        return {"data": {"photo": _generate_avatar_png(None, None, None)}}

    sub = claims.get("sub", "")
    user = users.get(sub)
    if not user:
        return {"data": {"photo": _generate_avatar_png(None, None, None)}}

    return {"data": {"photo": _avatar_for_user(user, sub)}}


def _avatar_for_user(user: dict, sub: str) -> str:
    if sub in _avatar_cache:
        return _avatar_cache[sub]

    first = user.get("first_name", "")
    last = user.get("last_name", "")
    initials = (first[:1] + last[:1]).upper() or "?"

    color_seed = int(hashlib.md5(user.get("sub", "").encode()).hexdigest()[:8], 16)
    r = (color_seed >> 16) & 0xFF
    g = (color_seed >> 8) & 0xFF
    b = color_seed & 0xFF
    bg_color = (max(r, 80), max(g, 80), max(b, 80))

    png_b64 = _generate_avatar_png(initials, bg_color, sub)
    _avatar_cache[sub] = png_b64
    return png_b64


def _generate_avatar_png(initials: str | None, bg_color: tuple[int, int, int] | None,
                         seed: str | None = None) -> str:
    size = 300
    if bg_color is None:
        bg_color = (100, 100, 100)
    if initials is None:
        initials = "?"

    img = Image.new("RGBA", (size, size), bg_color + (255,))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    r_circle = size // 3
    lighter = tuple(min(c + 30, 255) for c in bg_color)
    draw.ellipse([cx - r_circle, cy - r_circle, cx + r_circle, cy + r_circle],
                 fill=lighter + (80,))

    font = None
    font_size = 120
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
    ]
    for path in font_paths:
        if os.path.isfile(path):
            font = ImageFont.truetype(path, font_size)
            break
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initials, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) // 2
    y = (size - th) // 2 - bbox[1]

    shadow_color = tuple(max(c - 30, 0) for c in bg_color)
    draw.text((x + 2, y + 2), initials, fill=shadow_color + (80,), font=font)
    draw.text((x, y), initials, fill=(255, 255, 255, 220), font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return b64.b64encode(buf.getvalue()).decode("ascii")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    debug = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")

    print(f"""
╔══════════════════════════════════════════════╗
║        eFaas Mock Server v3.0.0 (FastAPI)    ║
╠══════════════════════════════════════════════╣
║  Issuer:   {SERVER_URL:<34s} ║
║  Users:    {len(users):<34d} ║
║  Key ID:   {KID:<34s} ║
╠══════════════════════════════════════════════╣
║  Endpoints:                                  ║
║    Login:     /connect/authorize             ║
║    Token:     /connect/token                 ║
║    UserInfo:  /connect/userinfo              ║
║    JWKS:      /.well-known/openid-config...  ║
║    Logout:    /connect/endsession            ║
║    Photo:     /user/photo                    ║
╚══════════════════════════════════════════════╝
    """)

    uvicorn.run(app, host=_HOST, port=_PORT, log_level="debug" if debug else "info")
