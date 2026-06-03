# eFaas Mock Server

A local mock of the [eFaas](https://efaas.gov.mv/) OIDC/OAuth2 identity provider for development and testing — no dependency on the real eFaas server.

Implements standard OpenID Connect endpoints. Works with **any** language or framework (Laravel, Express, Django, Rails, mobile apps, SPA, etc.).

## Quick Start

```bash
# Direct
cd efaas-mock-server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py

# Docker
docker compose up -d
```

Server starts on `http://localhost:5000` by default with **100 pre-seeded accounts**.

## App Configuration

No client credentials are validated — use any values. Point your OAuth2/OIDC library at the mock server's base URL.

```
client_id     = any-value
client_secret = any-value
redirect_uri  = http://localhost:8000/callback
mode          = development
api_url       = http://localhost:5000
```

### Laravel with eFaas Socialite

```env
EFAAS_CLIENT_ID=any-value
EFAAS_CLIENT_SECRET=any-value
EFAAS_REDIRECT_URI=http://localhost:8000/oauth/efaas/callback
EFAAS_MODE=development
EFAAS_API_URL=http://localhost:5000
```

### Any OAuth2 Client

```env
OAUTH_AUTHORIZE_URL=http://localhost:5000/connect/authorize
OAUTH_TOKEN_URL=http://localhost:5000/connect/token
OAUTH_USERINFO_URL=http://localhost:5000/connect/userinfo
OAUTH_CLIENT_ID=any-value
OAUTH_CLIENT_SECRET=any-value
OAUTH_REDIRECT_URI=http://localhost:8000/callback
```

### Docker Networking

If your app is also running in Docker, `localhost` inside its container won't resolve to the mock server. Use the Compose service name instead:

```env
# Inside docker-compose, both services on the same network:
api_url=http://efaas:5000
```

The mock server's `SERVER_URL` should match what your app uses to reach it:

```yaml
# docker-compose.yml
services:
  efaas:
    environment:
      - SERVER_URL=http://efaas:5000
```

If you want the mock container to reach services running on the host machine, use `network_mode: host` on Linux.

## Login Flow

1. Your app redirects to `/connect/authorize`
2. A login page appears with two tabs:
   - **Select Existing User** — browse/search 100+ pre-seeded accounts, click to pick one
   - **Create New User** — fill in a form with name, DOB, gender, ID number, etc; created accounts are saved and reusable
3. On sign-in, the mock POST-redirects back to your app with `code`, `id_token`, `scope`, and `state`
4. Your app exchanges the code for tokens, fetches the user profile, and validates JWT signatures via JWKS

## Logout Testing

- Visit `/logout` to see active mock sessions and trigger a back-channel logout POST
- You can also call `/connect/endsession?id_token_hint=...` directly if you want to simulate a standard OIDC logout
- The back-channel POST sends `logout_token` as form data to the URI you provide in the UI

## User Avatars

Each user gets a unique 300x300 PNG avatar containing their initials on a coloured background (colour is deterministic per user — same user, same colour every time). The avatar is served by the `/user/photo` endpoint and is returned as base64-encoded PNG in the user info response.

The photo URL in the user profile is generated **dynamically from the incoming request's `Host` header**. This means the URL always matches what the client used to connect, regardless of port mappings, Docker networks, or reverse proxies. The `SERVER_URL` env var is also sanitised — `0.0.0.0` (the bind address) is never leaked into URLs since no client can connect to it.

## Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/connect/authorize` | GET/POST | Login page (user selection + creation) |
| `/connect/token` | POST | Exchanges auth code for tokens |
| `/connect/userinfo` | POST/GET | Returns user profile (Bearer token) |
| `/.well-known/openid-configuration/jwks` | GET | JWKS public keys for JWT validation |
| `/connect/endsession` | GET | Logout redirect |
| `/logout` | GET/POST | Logout UI and back-channel tester |
| `/user/photo` | GET | User avatar (300x300 PNG base64) |

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | Port to listen on |
| `HOST` | `0.0.0.0` | Host to bind to |
| `SERVER_URL` | `http://localhost:{PORT}` | Base URL — `0.0.0.0` is silently replaced with `localhost` |
| `SEED_COUNT` | `100` | Number of pre-seeded accounts |
| `RSA_PRIVATE_KEY_PEM` | — | Custom RSA private key in PEM |
| `DEBUG` | `false` | Enable debug |

## Features

- 100+ pre-seeded Maldivian accounts with realistic data (names in English and Dhivehi, ID numbers, addresses, varied user types)
- Create custom users on the fly — saved and available for reuse
- Search/filter existing users by name, email, ID number, or type
- Unique 300x300 avatar per user (initials on coloured background) served as base64 PNG
- Real RSA key signing with JWKS endpoint (JWT signatures are fully validatable)
- No client credentials validation — plug in any values
- PKCE support
- One-tap login passthrough
- Single-use authorization codes
- Photo URL generated dynamically from request Host header — works across Docker networks and port mappings
- Language-agnostic — works with any OAuth2/OIDC client

## Testing

```bash
pytest test_server.py -v   # 33 tests, no server process needed
```
