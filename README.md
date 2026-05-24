# eFaas Mock Server

A local mock of the [eFaas](https://efaas.gov.mv/) OIDC/OAuth2 identity provider, designed to work with the [Javaabu/EFaas-Socialite](https://github.com/Javaabu/EFaas-Socialite) Laravel package for development and testing without relying on the official eFaas server.

## Quick Start

```bash
cd efaas-mock-server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
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

## Login Flow

1. Your app redirects to `/connect/authorize`
2. A login page appears with two tabs:
   - **Select Existing User** — browse/search 100+ pre-seeded accounts, click to pick one
   - **Create New User** — fill in a form with name, DOB, gender, ID number, etc; created accounts are saved and reusable
3. On sign-in, the mock POST-redirects back to your app with `code`, `id_token`, `scope`, and `state`
4. Socialite exchanges the code for tokens, fetches the user profile, and validates JWT signatures via JWKS

## Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/connect/authorize` | GET/POST | Login page (user selection + creation) |
| `/connect/token` | POST | Exchanges auth code for tokens |
| `/connect/userinfo` | POST/GET | Returns user profile (Bearer token) |
| `/.well-known/openid-configuration/jwks` | GET | JWKS public keys for JWT validation |
| `/connect/endsession` | GET | Logout redirect |
| `/user/photo` | GET | Dummy user photo (base64 PNG) |

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | Port to listen on |
| `HOST` | `0.0.0.0` | Host to bind to |
| `SERVER_URL` | `http://localhost:{PORT}` | Base URL of this server |
| `SEED_COUNT` | `100` | Number of pre-seeded accounts |
| `RSA_PRIVATE_KEY_PEM` | — | Custom RSA private key in PEM |
| `DEBUG` | `false` | Enable Flask debug |

## Features

- 100+ pre-seeded Maldivian accounts with realistic data (names in English and Dhivehi, ID numbers, addresses, varied user types)
- Create custom users on the fly — saved and available for reuse
- Search/filter existing users by name, email, ID number, or type
- Real RSA key signing with JWKS endpoint (JWT signatures are fully validatable)
- No client_id/client_secret validation — plug in any values
- PKCE support
- One-tap login passthrough
- Single-use authorization codes
