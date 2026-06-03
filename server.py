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
import io
import base64 as b64
from datetime import datetime
from urllib.parse import urlencode

from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse

import jwt
from PIL import Image, ImageDraw, ImageFont
from jinja2 import Template

from constants import SERVER_URL, ACCESS_TOKEN_TTL, AUTH_CODE_TTL, COUNTRY_CODES, _HOST, _PORT
from crypto import KID, _private_key, _public_key, _make_jwks, _make_access_token, _make_id_token
from user_generator import users, _avatar_cache, generate_user
from templates import LOGIN_PAGE, AUTO_POST_TEMPLATE

app = FastAPI(title="eFaas Mock Server", version="3.0.0")

auth_codes: dict[str, dict] = {}

DEFAULT_SCOPES = ("openid", "efaas.profile")
AVAILABLE_SCOPES = (
    ("openid", "OpenID", "Required for sign-in"),
    ("efaas.profile", "eFaas Profile", "Required user profile claims"),
    ("efaas.email", "eFaas Email", "Email address"),
    ("efaas.mobile", "eFaas Mobile", "Mobile number"),
    ("efaas.birthdate", "eFaas Birthdate", "Date of birth"),
    ("efaas.photo", "eFaas Photo", "User avatar"),
    ("efaas.work_permit_status", "Work Permit Status", "Work permit flag"),
    ("efaas.passport_number", "Passport Number", "Passport number"),
    ("efaas.country", "Country", "Country claims"),
    ("efaas.permanent_address", "Permanent Address", "Permanent address"),
    ("profile", "Legacy profile", "Legacy scope kept for compatibility"),
)

SCOPE_CLAIMS = {
    "efaas.profile": (
        "first_name", "middle_name", "last_name", "full_name",
        "first_name_dhivehi", "middle_name_dhivehi", "last_name_dhivehi", "full_name_dhivehi",
        "gender", "idnumber", "verified", "verification_type", "last_verified_date",
        "user_type_description", "updated_at",
    ),
    "efaas.email": ("email",),
    "efaas.mobile": ("mobile", "country_dialing_code"),
    "efaas.birthdate": ("birthdate",),
    "efaas.photo": ("photo",),
    "efaas.work_permit_status": ("is_workpermit_active",),
    "efaas.passport_number": ("passport_number",),
    "efaas.country": ("country_name", "country_code", "country_code_alpha3", "country_dialing_code"),
    "efaas.permanent_address": ("permanent_address",),
}


def _cleanup_expired_codes():
    now = time.time()
    expired = [c for c, d in auth_codes.items() if d["expires_at"] < now]
    for c in expired:
        del auth_codes[c]


def _normalize_scopes(scope_value: str) -> str:
    scopes = []
    seen = set()
    for scope in (*DEFAULT_SCOPES, *(scope_value or "").split()):
        scope = scope.strip()
        if scope and scope not in seen:
            scopes.append(scope)
            seen.add(scope)
    return " ".join(scopes)


def _scope_set(scope_value: str) -> set[str]:
    return set(_normalize_scopes(scope_value).split())


def _user_claims_for_scopes(user: dict, scope_value: str, request: Request | None = None) -> dict:
    scopes = _scope_set(scope_value)
    claims = {"sub": user.get("sub", "")}

    if "efaas.profile" in scopes or "profile" in scopes:
        for key in SCOPE_CLAIMS["efaas.profile"]:
            claims[key] = user.get(key, "")

    for scope, keys in SCOPE_CLAIMS.items():
        if scope == "efaas.profile":
            continue
        if scope not in scopes:
            continue
        for key in keys:
            if key == "photo":
                claims[key] = _photo_url(request) if request else user.get(key, "")
            else:
                claims[key] = user.get(key, "")

    return claims


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
    return {
        "client_id": request.query_params.get("client_id", ""),
        "redirect_uri": request.query_params.get("redirect_uri", ""),
        "scope": _normalize_scopes(request.query_params.get("scope", "")),
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


def _do_login(sub: str, oauth: dict, request: Request):
    if not oauth.get("redirect_uri"):
        return _error_html("Missing redirect_uri",
                           "Cannot complete login without a redirect URI.", 400)
    if sub not in users:
        return _error_html("User not found.", status_code=400)

    user = users[sub]
    scope = _normalize_scopes(oauth.get("scope", ""))
    user_claims = _user_claims_for_scopes(user, scope, request)
    code = str(uuid.uuid4()).replace("-", "")
    sid = str(uuid.uuid4()).replace("-", "").upper()[:32]

    access_token = _make_access_token(sub, sid, oauth["client_id"], scope)
    id_token = _make_id_token(sub, sid, oauth["client_id"], oauth.get("nonce"),
                              access_token, scope, user_claims)

    auth_codes[code] = {
        "client_id": oauth["client_id"],
        "redirect_uri": oauth["redirect_uri"],
        "scope": scope,
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
            "code": code, "id_token": id_token, "scope": scope,
            "session_state": session_state, "state": oauth.get("state", ""),
        })

    return _html(AUTO_POST_TEMPLATE,
        redirect_uri=oauth["redirect_uri"],
        code=code, id_token=id_token,
        scope=scope,
        session_state=session_state,
        state=oauth.get("state", ""),
    )


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
            "AtollAbbreviation": "K", "AtollAbbreviationDhivehi": "\u0786",
            "IslandName": "Male'", "IslandNameDhivehi": "\u0789\u07a7\u078d\u07ac",
            "HomeNameDhivehi": "", "Ward": "Maafannu",
            "WardAbbreviationEnglish": "M", "WardAbbreviationDhivehi": "\u0789",
            "Country": country_name, "CountryISOThreeDigitCode": "462",
            "CountryISOThreeLetterCode": "MDV",
        })

    cc = COUNTRY_CODES.get(country_name, ("462", "MDV", "+960"))

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
    selected_scopes = oauth["scope"].split()
    return _html(LOGIN_PAGE,
        params=oauth, user_list=user_list, total_users=len(users),
        scope_options=AVAILABLE_SCOPES, selected_scopes=selected_scopes,
        selected_scope_value=oauth["scope"])


@app.post("/connect/authorize")
async def authorize_post(request: Request):
    _cleanup_expired_codes()
    form = await request.form()

    has_callback_fields = bool(form.get("code") or form.get("id_token"))
    has_action = bool((form.get("action") or "").strip())
    if has_callback_fields and not has_action:
        return _error_html("Invalid request",
                           "This endpoint expects a login form submission.", 400)

    oauth = _oauth_params(request)
    for key in oauth:
        if key in form:
            oauth[key] = form[key]
    oauth["scope"] = _normalize_scopes(oauth.get("scope", ""))

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
            from jwt.utils import base64url_encode
            expected = base64url_encode(
                hashlib.sha256(code_verifier.encode("ascii")).digest()
            ).decode("ascii")
        else:
            expected = code_verifier
        if expected != stored["code_challenge"]:
            return JSONResponse({"error": "invalid_grant",
                                 "error_description": "PKCE validation failed"}, 400)

    del auth_codes[code]

    user_claims = _user_claims_for_scopes(stored["user"], stored["scope"])

    return {
        "id_token": _make_id_token(
            stored["user_sub"], stored["sid"], stored["client_id"],
            stored.get("nonce"), stored["access_token"],
            stored["scope"], user_claims,
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
    scope = claims.get("scope", [])
    scope_value = " ".join(scope) if isinstance(scope, list) else str(scope)
    return _user_claims_for_scopes(user, scope_value, request)


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
