import os
import hashlib
import time
import uuid
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import jwt
from jwt.utils import base64url_encode

from constants import SERVER_URL, ACCESS_TOKEN_TTL, ID_TOKEN_TTL


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
                   access_token: str, scope: str | None, user_claims: dict | None = None) -> str:
    now = int(time.time())
    at_hash_bytes = hashlib.sha256(access_token.encode("ascii")).digest()
    at_hash = base64url_encode(at_hash_bytes[:16]).decode("ascii")

    claims: dict[str, Any] = {
        "nbf": now, "exp": now + ID_TOKEN_TTL, "iss": SERVER_URL,
        "aud": client_id, "iat": now, "at_hash": at_hash,
        "sid": sid, "sub": sub, "auth_time": now,
        "idp": "local", "amr": ["pwd"],
    }
    if user_claims:
        claims.update(user_claims)
    if nonce:
        claims["nonce"] = nonce
    headers = {
        "alg": "RS256", "kid": KID, "typ": "JWT",
        "x5t": base64url_encode(hashlib.sha1(_public_key_der()).digest()).decode("ascii"),
    }
    return jwt.encode(claims, _private_key, algorithm="RS256", headers=headers)
