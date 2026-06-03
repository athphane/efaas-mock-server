#!/usr/bin/env python3
"""
eFaas Mock Server — Test Suite

Uses pytest + httpx to test all endpoints and flows.
The server module is imported directly (no subprocess needed).

Usage:
    pip install pytest httpx
    pytest test_server.py -v
"""

import os
import re
import json
import base64
import hashlib
import pytest
from fastapi.testclient import TestClient
import jwt as pyjwt
from jwt.algorithms import RSAAlgorithm
from jwt.utils import base64url_encode

import server as app_module

app = app_module.app

# ──────────────────────────────────────────────
# Test client
# ──────────────────────────────────────────────

@pytest.fixture
def client():
    return TestClient(app, base_url="http://testserver")


@pytest.fixture(autouse=True)
def _clear_logout_sessions():
    app_module.logout_sessions.clear()
    yield
    app_module.logout_sessions.clear()


# ──────────────────────────────────────────────
# Shared auth helpers
# ──────────────────────────────────────────────

def _oauth_params(extra=None):
    p = {
        "client_id": "test-client",
        "redirect_uri": "http://localhost:8000/callback",
        "scope": "openid efaas.profile efaas.email efaas.photo",
        "state": "test-state",
        "nonce": "test-nonce",
        "response_type": "code id_token",
        "response_mode": "form_post",
    }
    if extra:
        p.update(extra)
    return p


def _extract_form_value(html: str, name: str) -> str | None:
    m = re.search(rf'name="{name}"\s+value="([^"]+)"', html)
    return m.group(1) if m else None


def _do_login(client, sub: str, params=None):
    """Select a user and complete login, returning the authorization code."""
    if params is None:
        params = _oauth_params()
    r = client.get("/connect/authorize", params=params)
    assert r.status_code == 200
    r = client.post("/connect/authorize", data={**params, "action": "select", "sub": sub})
    assert r.status_code == 200
    return _extract_form_value(r.text, "code")


def _exchange_code(client, code: str, params=None):
    """Exchange an authorization code for tokens."""
    if params is None:
        params = _oauth_params()
    r = client.post("/connect/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "client_id": params["client_id"],
        "client_secret": "test-secret",
        "redirect_uri": params["redirect_uri"],
    })
    assert r.status_code == 200
    return r.json()


def _get_userinfo(client, access_token: str):
    r = client.post("/connect/userinfo", headers={
        "Authorization": f"Bearer {access_token}",
    })
    assert r.status_code == 200
    return r.json()


# ──────────────────────────────────────────────
# Tests — Meta
# ──────────────────────────────────────────────

def test_seeded_users():
    """Pre-seeded users exist."""
    assert len(app_module.users) >= 31


def test_known_test_user():
    """The CSC test user is present."""
    csc = app_module.users.get("3b46dc4b-f565-420b-af8f-9312c86e40cb")
    assert csc is not None
    assert csc["full_name"] == "CSC Test User 18"


def test_jwks_has_keys():
    """JWKS endpoint returns at least one key."""
    jwks = app_module._make_jwks()
    assert len(jwks["keys"]) >= 1
    assert jwks["keys"][0]["alg"] == "RS256"


def test_key_id_computed():
    """KID is a SHA1 hash + RS256 suffix."""
    assert app_module.KID.endswith("RS256")
    assert len(app_module.KID) in (45, 46)  # hexdigest may drop leading zero


def test_server_url_no_zero_ip():
    """0.0.0.0 never leaks into SERVER_URL."""
    assert "0.0.0.0" not in app_module.SERVER_URL
    assert app_module.SERVER_URL.startswith("http://")


# ──────────────────────────────────────────────
# Tests — Health / index
# ──────────────────────────────────────────────

def test_index(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "eFaas Mock Server"
    assert data["framework"] == "FastAPI"
    assert data["total_users"] >= 31
    assert "endpoints" in data


# ──────────────────────────────────────────────
# Tests — Login page
# ──────────────────────────────────────────────

def test_login_page_renders(client):
    r = client.get("/connect/authorize", params=_oauth_params())
    assert r.status_code == 200
    assert "Select Existing User" in r.text
    assert "Create New User" in r.text
    assert "eFaas Mock Server" in r.text


def test_login_page_shows_users(client):
    r = client.get("/connect/authorize", params=_oauth_params())
    assert 'data-sub="3b46dc4b-f565-420b-af8f-9312c86e40cb"' in r.text


def test_login_page_prompts_for_scopes(client):
    r = client.get("/connect/authorize", params={
        "client_id": "test-client",
        "redirect_uri": "http://localhost:8000/callback",
    })
    assert r.status_code == 200
    assert "Scopes" in r.text
    assert 'value="openid efaas.profile"' in r.text
    assert 'data-scope-choice value="efaas.email"' in r.text


def test_login_page_prefills_logout_defaults_from_redirect_uri(client):
    params = _oauth_params({"redirect_uri": "http://ncs.test/oauth/efaas/callback"})
    r = client.get("/connect/authorize", params=params)
    assert r.status_code == 200
    assert 'value="http://ncs.test/oauth/efaas/logout"' in r.text
    assert 'value="http://ncs.test"' in r.text


# ──────────────────────────────────────────────
# Tests — Full OAuth2 flow
# ──────────────────────────────────────────────

def test_full_flow_select_user(client):
    """Select pre-seeded CSC user and get userinfo."""
    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb")
    assert code is not None

    tokens = _exchange_code(client, code)
    assert "access_token" in tokens
    assert "id_token" in tokens
    assert tokens["token_type"] == "Bearer"

    user = _get_userinfo(client, tokens["access_token"])
    assert user["full_name"] == "CSC Test User 18"
    assert user["email"] == "csc318@gmail.com"
    assert user["user_type_description"] == "Maldivian"
    assert "0.0.0.0" not in user.get("photo", "")


def test_full_flow_normalizes_scopes(client):
    """Requested optional scopes keep the default OIDC scopes."""
    params = _oauth_params({"scope": "efaas.email"})
    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb", params)
    tokens = _exchange_code(client, code, params)

    assert tokens["scope"] == "openid efaas.profile efaas.email"


def test_full_flow_create_user(client):
    """Create a new user and verify it persists."""
    params = _oauth_params()
    r = client.get("/connect/authorize", params=params)
    assert r.status_code == 200

    r = client.post("/connect/authorize", data={
        **params,
        "action": "create",
        "first_name": "Pytest",
        "last_name": "Runner",
        "gender": "F",
        "idnumber": "A888888",
        "email": "pytest@example.com",
        "mobile": "7123456",
        "birthdate": "5/5/1995",
        "user_type_description": "Maldivian",
    })
    assert r.status_code == 200
    code = _extract_form_value(r.text, "code")
    assert code is not None

    tokens = _exchange_code(client, code)
    user = _get_userinfo(client,tokens["access_token"])
    assert user["full_name"] == "Pytest Runner"
    assert user["email"] == "pytest@example.com"
    saved_sub = user["sub"]

    # Reuse — log in again as same user
    code2 = _do_login(client, saved_sub)
    tokens2 = _exchange_code(client, code2)
    user2 = _get_userinfo(client,tokens2["access_token"])
    assert user2["full_name"] == "Pytest Runner"


def test_code_single_use(client):
    """Authorization codes can only be used once."""
    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb")
    _exchange_code(client, code)  # first use — OK

    r = client.post("/connect/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "client_id": "test-client",
        "client_secret": "test-secret",
        "redirect_uri": "http://localhost:8000/callback",
    })
    assert r.status_code == 400
    assert r.json()["error"] == "invalid_grant"


# ──────────────────────────────────────────────
# Tests — Stray POST / error guards
# ──────────────────────────────────────────────

def test_reject_stray_callback_post(client):
    """POST with code/id_token but no action is rejected."""
    r = client.post("/connect/authorize", data={
        "code": "fake", "id_token": "fake",
        "scope": "openid", "session_state": "x", "state": "x",
    })
    assert r.status_code == 400
    assert "Invalid request" in r.text


def test_reject_missing_redirect_uri(client):
    """POST without redirect_uri returns an error."""
    r = client.post("/connect/authorize", data={"client_id": "x"})
    assert r.status_code == 400
    assert "redirect_uri" in r.text.lower()


# ──────────────────────────────────────────────
# Tests — Token endpoint
# ──────────────────────────────────────────────

def test_token_rejects_bad_grant_type(client):
    r = client.post("/connect/token", data={"grant_type": "password"})
    assert r.status_code == 400
    assert r.json()["error"] == "unsupported_grant_type"


def test_token_rejects_invalid_code(client):
    r = client.post("/connect/token", data={
        "grant_type": "authorization_code",
        "code": "nonexistent-code",
        "client_id": "x",
        "client_secret": "x",
        "redirect_uri": "http://x.com",
    })
    assert r.status_code == 400
    assert "invalid_grant" in r.json()["error"]


# ──────────────────────────────────────────────
# Tests — Userinfo endpoint
# ──────────────────────────────────────────────

def test_userinfo_rejects_missing_auth(client):
    r = client.post("/connect/userinfo")
    assert r.status_code == 401
    assert r.json()["error"] == "invalid_token"


def test_userinfo_rejects_fake_token(client):
    r = client.post("/connect/userinfo", headers={
        "Authorization": "Bearer not-a-real-token",
    })
    assert r.status_code == 401
    assert "invalid_token" in r.json()["error"]


# ──────────────────────────────────────────────
# Tests — Photo endpoint
# ──────────────────────────────────────────────

def test_photo_returns_png_with_auth(client):
    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb")
    tokens = _exchange_code(client, code)

    r = client.get("/user/photo", headers={
        "Authorization": f"Bearer {tokens['access_token']}",
    })
    assert r.status_code == 200
    data = r.json()
    assert "data" in data
    assert "photo" in data["data"]
    png = base64.b64decode(data["data"]["photo"])
    assert png[:8] == b'\x89PNG\r\n\x1a\n'  # PNG magic bytes
    from PIL import Image
    import io
    img = Image.open(io.BytesIO(png))
    assert img.size == (300, 300)


def test_photo_returns_fallback_without_auth(client):
    r = client.get("/user/photo")
    assert r.status_code == 200
    png = base64.b64decode(r.json()["data"]["photo"])
    assert png[:4] == b'\x89PNG'


def test_photo_deterministic_per_user(client):
    """Same user always gets the same avatar bytes."""
    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb")
    tokens = _exchange_code(client, code)
    r1 = client.get("/user/photo", headers={
        "Authorization": f"Bearer {tokens['access_token']}",
    })
    r2 = client.get("/user/photo", headers={
        "Authorization": f"Bearer {tokens['access_token']}",
    })
    assert r1.json()["data"]["photo"] == r2.json()["data"]["photo"]


def test_photo_differs_between_users(client):
    """Different users get different avatars."""
    code1 = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb")
    at1 = _exchange_code(client, code1)["access_token"]

    first_sub = next(iter(app_module.users.keys()))
    code2 = _do_login(client, first_sub, _oauth_params({"state": "s2"}))
    at2 = _exchange_code(client, code2)["access_token"]

    r1 = client.get("/user/photo", headers={"Authorization": f"Bearer {at1}"})
    r2 = client.get("/user/photo", headers={"Authorization": f"Bearer {at2}"})
    assert r1.json()["data"]["photo"] != r2.json()["data"]["photo"]


# ──────────────────────────────────────────────
# Tests — JWKS + JWT validation
# ──────────────────────────────────────────────

def test_jwks_endpoint(client):
    r = client.get("/.well-known/openid-configuration/jwks")
    assert r.status_code == 200
    data = r.json()
    assert len(data["keys"]) >= 1
    key = data["keys"][0]
    assert key["kty"] == "RSA"
    assert key["use"] == "sig"
    assert key["kid"] == app_module.KID


def test_id_token_is_valid_jwt(client):
    """The returned id_token can be validated with the public key from JWKS."""
    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb")
    tokens = _exchange_code(client, code)

    jwks = client.get("/.well-known/openid-configuration/jwks").json()
    pub_key = RSAAlgorithm.from_jwk(jwks["keys"][0])

    decoded = pyjwt.decode(
        tokens["id_token"], pub_key, algorithms=["RS256"],
        options={"verify_aud": False},
    )
    assert decoded["iss"] == app_module.SERVER_URL
    assert decoded["sub"] == "3b46dc4b-f565-420b-af8f-9312c86e40cb"
    assert "sid" in decoded
    assert "at_hash" in decoded


def test_access_token_is_valid_jwt(client):
    """The returned access_token can be validated with the public key."""
    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb")
    tokens = _exchange_code(client, code)

    jwks = client.get("/.well-known/openid-configuration/jwks").json()
    pub_key = RSAAlgorithm.from_jwk(jwks["keys"][0])

    decoded = pyjwt.decode(
        tokens["access_token"], pub_key, algorithms=["RS256"],
        options={"verify_aud": False},
    )
    assert decoded["typ"] == "at+jwt" if "typ" in decoded else True
    assert "sub" in decoded
    assert "scope" in decoded


def test_id_token_contains_user_data(client):
    """The id_token carries user profile claims."""
    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb")
    tokens = _exchange_code(client, code)

    jwks = client.get("/.well-known/openid-configuration/jwks").json()
    pub_key = RSAAlgorithm.from_jwk(jwks["keys"][0])
    decoded = pyjwt.decode(tokens["id_token"], pub_key, algorithms=["RS256"],
                          options={"verify_aud": False})

    assert decoded.get("full_name") == "CSC Test User 18"
    assert decoded.get("email") == "csc318@gmail.com"
    assert decoded.get("gender") == "M"


def test_scoped_responses_omit_unrequested_claims(client):
    """Minimal scopes do not leak optional claims."""
    params = {
        "client_id": "test-client",
        "redirect_uri": "http://localhost:8000/callback",
        "scope": "openid",
        "state": "test-state",
        "nonce": "test-nonce",
        "response_type": "code id_token",
        "response_mode": "form_post",
    }
    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb", params)
    tokens = _exchange_code(client, code, params)

    jwks = client.get("/.well-known/openid-configuration/jwks").json()
    pub_key = RSAAlgorithm.from_jwk(jwks["keys"][0])
    decoded = pyjwt.decode(tokens["id_token"], pub_key, algorithms=["RS256"],
                          options={"verify_aud": False})

    assert decoded.get("full_name") == "CSC Test User 18"
    assert "email" not in decoded
    assert "photo" not in decoded

    user = _get_userinfo(client, tokens["access_token"])
    assert user.get("full_name") == "CSC Test User 18"
    assert "email" not in user
    assert "photo" not in user


# ──────────────────────────────────────────────
# Tests — Endsession
# ──────────────────────────────────────────────

def test_endsession_redirects(client):
    r = client.get("/connect/endsession", params={
        "post_logout_redirect_uri": "http://example.com/logout",
        "state": "logout-state",
    }, follow_redirects=False)
    assert r.status_code in (302, 307)
    location = r.headers["location"]
    assert "example.com/logout" in location
    assert "logout-state" in location


def test_endsession_no_redirect_returns_message(client):
    r = client.get("/connect/endsession")
    assert r.status_code == 200
    assert r.json()["message"] == "Logged out successfully"


def test_logout_ui_lists_active_sessions(client):
    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb")
    _exchange_code(client, code)

    r = client.get("/logout")
    assert r.status_code == 200
    assert "CSC Test User 18" in r.text
    assert "Logout this session" in r.text


def test_logout_submit_posts_backchannel_logout(client, monkeypatch):
    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb")
    tokens = _exchange_code(client, code)
    decoded = pyjwt.decode(tokens["id_token"], app_module._public_key, algorithms=["RS256"], options={"verify_aud": False})
    sid = decoded["sid"]

    captured = {}

    class _Resp:
        status_code = 200

        def raise_for_status(self):
            return None

    def fake_post(url, data=None, timeout=None):
        captured["url"] = url
        captured["data"] = data
        captured["timeout"] = timeout
        return _Resp()

    monkeypatch.setattr(app_module.httpx, "post", fake_post)

    r = client.post("/logout", data={
        "id_token_hint": tokens["id_token"],
        "backchannel_logout_uri": "http://example.com/backchannel/logout",
    }, follow_redirects=False)
    assert r.status_code in (302, 307)
    assert captured["url"] == "http://example.com/backchannel/logout"
    assert "logout_token" in captured["data"]
    logout_claims = pyjwt.decode(captured["data"]["logout_token"], app_module._public_key, algorithms=["RS256"], options={"verify_aud": False})
    assert logout_claims["sid"] == sid
    assert logout_claims["events"]["http://schemas.openid.net/event/backchannel-logout"] == {}
    assert sid not in app_module.logout_sessions


def test_logout_submit_tolerates_backchannel_timeout(client, monkeypatch):
    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb")
    tokens = _exchange_code(client, code)

    def fake_post(url, data=None, timeout=None):
        raise app_module.httpx.TimeoutException("timed out")

    monkeypatch.setattr(app_module.httpx, "post", fake_post)

    r = client.post("/logout", data={
        "id_token_hint": tokens["id_token"],
        "backchannel_logout_uri": "http://ncs.test/oauth/efaas/logout",
    }, follow_redirects=False)
    assert r.status_code in (200, 302, 307)
    assert "Logout complete" in r.text or r.status_code in (302, 307)
    assert "Back-channel URI" in r.text or r.status_code in (302, 307)


def test_endsession_uses_stored_backchannel_uri(client, monkeypatch):
    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb")
    tokens = _exchange_code(client, code)
    decoded = pyjwt.decode(tokens["id_token"], app_module._public_key, algorithms=["RS256"], options={"verify_aud": False})
    sid = decoded["sid"]
    app_module.logout_sessions[sid]["backchannel_logout_uri"] = "http://example.com/stored-backchannel"

    captured = {}

    class _Resp:
        status_code = 200

        def raise_for_status(self):
            return None

    def fake_post(url, data=None, timeout=None):
        captured["url"] = url
        captured["data"] = data
        return _Resp()

    monkeypatch.setattr(app_module.httpx, "post", fake_post)

    r = client.get("/connect/endsession", params={"id_token_hint": tokens["id_token"]}, follow_redirects=False)
    assert r.status_code in (302, 307)
    assert captured["url"] == "http://example.com/stored-backchannel"
    assert sid not in app_module.logout_sessions


def test_endsession_uses_redirect_uri_defaults_when_session_has_none(client, monkeypatch):
    params = _oauth_params({"redirect_uri": "http://ncs.test/oauth/efaas/callback"})
    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb", params=params)
    tokens = _exchange_code(client, code, params)
    decoded = pyjwt.decode(tokens["id_token"], app_module._public_key, algorithms=["RS256"], options={"verify_aud": False})
    sid = decoded["sid"]
    app_module.logout_sessions[sid]["backchannel_logout_uri"] = ""
    app_module.logout_sessions[sid]["post_logout_redirect_uri"] = ""

    captured = {}

    class _Resp:
        status_code = 200

        def raise_for_status(self):
            return None

    def fake_post(url, data=None, timeout=None):
        captured["url"] = url
        captured["data"] = data
        return _Resp()

    monkeypatch.setattr(app_module.httpx, "post", fake_post)

    r = client.get(
        "/connect/endsession",
        params={"id_token_hint": tokens["id_token"]},
        follow_redirects=False,
    )
    assert r.status_code in (302, 307)
    assert captured["url"] == "http://ncs.test/oauth/efaas/logout"
    assert sid not in app_module.logout_sessions


# ──────────────────────────────────────────────
# Tests — User creation with different types
# ──────────────────────────────────────────────

def test_create_work_permit_user(client):
    params = _oauth_params({"scope": "efaas.email efaas.photo efaas.mobile efaas.birthdate efaas.passport_number efaas.country efaas.work_permit_status"})
    r = client.post("/connect/authorize", data={
        **params,
        "action": "create",
        "first_name": "Wp", "last_name": "User",
        "gender": "M", "idnumber": "WP123456",
        "email": "wp@example.com", "mobile": "7000000",
        "birthdate": "1/1/1990",
        "user_type_description": "Work Permit Holder",
        "country_name": "Bangladesh",
        "passport_number": "AB1234567",
        "is_workpermit_active": "True",
    })
    assert r.status_code == 200
    code = _extract_form_value(r.text, "code")
    tokens = _exchange_code(client, code)
    user = _get_userinfo(client,tokens["access_token"])
    assert user["user_type_description"] == "Work Permit Holder"
    assert user["passport_number"] == "AB1234567"
    assert user["is_workpermit_active"] == "True"


def test_create_foreigner_user(client):
    params = _oauth_params({"scope": "efaas.email efaas.photo efaas.passport_number efaas.country"})
    r = client.post("/connect/authorize", data={
        **params,
        "action": "create",
        "first_name": "John", "last_name": "Doe",
        "gender": "M", "idnumber": "AB9876543",
        "email": "john@example.com", "mobile": "7000001",
        "birthdate": "6/15/1985",
        "user_type_description": "Foreigner",
        "country_name": "USA",
        "passport_number": "AB9876543",
    })
    assert r.status_code == 200
    code = _extract_form_value(r.text, "code")
    tokens = _exchange_code(client, code)
    user = _get_userinfo(client,tokens["access_token"])
    assert user["user_type_description"] == "Foreigner"
    assert user["country_name"] == "USA"


# ──────────────────────────────────────────────
# Tests — PKCE
# ──────────────────────────────────────────────

def test_pkce_flow(client):
    """PKCE with S256 challenge."""
    code_verifier = "test-code-verifier-abcdefghijklmnop"
    code_challenge = base64url_encode(
        hashlib.sha256(code_verifier.encode("ascii")).digest()
    ).decode("ascii")

    params = _oauth_params({
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": "pkce-state",
    })

    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb", params)
    assert code is not None

    r = client.post("/connect/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "client_id": params["client_id"],
        "client_secret": "test-secret",
        "redirect_uri": params["redirect_uri"],
        "code_verifier": code_verifier,
    })
    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens


def test_pkce_rejects_wrong_verifier(client):
    """PKCE with wrong code_verifier is rejected."""
    code_challenge = base64url_encode(
        hashlib.sha256("correct-verifier".encode("ascii")).digest()
    ).decode("ascii")

    params = _oauth_params({
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": "pkce-bad",
    })

    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb", params)

    r = client.post("/connect/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "client_id": params["client_id"],
        "client_secret": "test-secret",
        "redirect_uri": params["redirect_uri"],
        "code_verifier": "wrong-verifier",
    })
    assert r.status_code == 400
    assert r.json()["error"] == "invalid_grant"


# ──────────────────────────────────────────────
# Tests — Photo URL from userinfo
# ──────────────────────────────────────────────

def test_userinfo_photo_url_uses_request_host(client):
    """The photo URL in userinfo uses the request Host header."""
    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb")
    tokens = _exchange_code(client, code)

    r = client.post("/connect/userinfo", headers={
        "Authorization": f"Bearer {tokens['access_token']}",
        "Host": "custom-host:9999",
    })
    assert r.status_code == 200
    assert r.json()["photo"] == "http://custom-host:9999/user/photo"


# ──────────────────────────────────────────────
# Tests — Avatar cache
# ──────────────────────────────────────────────

def test_avatar_cache_works(client):
    """Avatar is cached after first generation."""
    code = _do_login(client, "3b46dc4b-f565-420b-af8f-9312c86e40cb")
    tokens = _exchange_code(client, code)

    # First request
    r1 = client.get("/user/photo", headers={
        "Authorization": f"Bearer {tokens['access_token']}",
    })
    assert "3b46dc4b-f565-420b-af8f-9312c86e40cb" in app_module._avatar_cache

    # Second request uses cache
    r2 = client.get("/user/photo", headers={
        "Authorization": f"Bearer {tokens['access_token']}",
    })
    cached = app_module._avatar_cache["3b46dc4b-f565-420b-af8f-9312c86e40cb"]
    assert r2.json()["data"]["photo"] == cached
