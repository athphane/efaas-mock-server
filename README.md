# eFaas Mock Server

A local mock of the [eFaas](https://efaas.gov.mv/) OIDC/OAuth2 identity provider, designed to work with the [Javaabu/EFaas-Socialite](https://github.com/Javaabu/EFaas-Socialite) Laravel package for development and testing without relying on the official eFaas server.

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

## Laravel .env Configuration

Any `CLIENT_ID` and `CLIENT_SECRET` values are accepted — the mock doesn't validate them.

```env
EFAAS_CLIENT_ID=any-client-id
EFAAS_CLIENT_SECRET=any-secret
EFAAS_REDIRECT_URI=http://localhost:8000/oauth/efaas/callback
EFAAS_MODE=development
EFAAS_API_URL=http://localhost:5000
```

### Docker Networking

If your Laravel app is also running in Docker, `localhost` inside the Laravel container won't resolve to the mock server. Use the Compose service name instead:

```env
# Inside docker-compose, both services on the same network:
EFAAS_API_URL=http://efaas:5000
```

The mock server's `SERVER_URL` should match what your Laravel app uses to reach it:

```yaml
# docker-compose.yml
services:
  efaas:
    environment:
      - SERVER_URL=http://efaas:5000   # same host the Laravel app sees
```

## Login Flow

1. Your app redirects to `/connect/authorize`
2. A login page appears with two tabs:
   - **Select Existing User** — browse/search 100+ pre-seeded accounts, click to pick one
   - **Create New User** — fill in a form with name, DOB, gender, ID number, etc; created accounts are saved and reusable
3. On sign-in, the mock POST-redirects back to your app with `code`, `id_token`, `scope`, and `state`
4. Socialite exchanges the code for tokens, fetches the user profile, and validates JWT signatures via JWKS

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
| `/user/photo` | GET | User avatar (300x300 PNG base64) |

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | Port to listen on |
| `HOST` | `0.0.0.0` | Host to bind to |
| `SERVER_URL` | `http://localhost:{PORT}` | Base URL — `0.0.0.0` is silently replaced with `localhost` |
| `SEED_COUNT` | `100` | Number of pre-seeded accounts |
| `RSA_PRIVATE_KEY_PEM` | — | Custom RSA private key in PEM |
| `DEBUG` | `false` | Enable Flask debug |

## Features

- 100+ pre-seeded Maldivian accounts with realistic data (names in English and Dhivehi, ID numbers, addresses, varied user types)
- Create custom users on the fly — saved and available for reuse
- Search/filter existing users by name, email, ID number, or type
- Unique 300x300 avatar per user (initials on coloured background) served as base64 PNG
- Real RSA key signing with JWKS endpoint (JWT signatures are fully validatable)
- No client_id/client_secret validation — plug in any values
- PKCE support
- One-tap login passthrough
- Single-use authorization codes
- Photo URL generated dynamically from request Host header — works across Docker networks and port mappings
