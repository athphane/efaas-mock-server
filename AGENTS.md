# AGENTS.md

## Setup and run

```bash
# Direct
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python server.py

# Docker
docker compose up -d --build
```

## Test commands

```bash
pytest test_server.py -v          # all 33 tests (no server process needed)
pytest test_server.py -v -k photo # single test filter
```

Tests import `server as app_module` directly via FastAPI's `TestClient` — never spawn a subprocess.

## Architecture

Single-file FastAPI app (`server.py`). Everything runs in one process with in-memory stores (no database, no persistence).

**Module-load side effects:**
- RSA keypair generated at import time (new keys each restart unless `RSA_PRIVATE_KEY_PEM` is set)
- 101 users pre-seeded at import time (`seed_users()` runs globally)
- All config read from env vars at module level

**Flow (OIDC Authorization Code):**
1. `GET /connect/authorize` — login page with user list + create form
2. `POST /connect/authorize` — `action=select` (existing user) or `action=create` (new user) → auto-submit form redirects back to client's `redirect_uri`
3. `POST /connect/token` — exchanges code for `access_token` + `id_token` (both signed JWTs)
4. `POST /connect/userinfo` — returns user profile (Bearer token required)
5. `GET /user/photo` — per-user 300×300 PNG avatar with initials

**Auth codes** are single-use, stored in `auth_codes: dict`, cleaned up periodically.

## Gotchas

- **No client validation.** `client_id` and `client_secret` are ignored on all endpoints. Any values work.
- **Separate GET/POST handlers** for `/connect/authorize` — no `request.method` branching. FastAPI routes use `@app.get` and `@app.post` decorators.
- **POST authorize needs `await request.form()`** — async form parsing is required.
- **Photo URL is dynamic.** The `/connect/userinfo` response generates the `photo` URL from the request's `Host` header, not from the stored `SERVER_URL`. This is intentional so it works across Docker networks and port mappings.
- **0.0.0.0 sanitised.** `SERVER_URL` replaces `0.0.0.0` with `localhost` at startup — `0.0.0.0` is a bind address, not reachable by clients.
- **Stray POST guard.** If a POST to `/connect/authorize` contains `code`/`id_token` but no `action`, it's rejected with 400 to prevent infinite redirect loops.
- **Templates.** Jinja2 `Template.render()` via the `_html()` helper. Not FastAPI's built-in templating.
- **Avatar cache.** `_avatar_cache` dict avoids regenerating PNGs for the same user.
- **Token expiry.** Access tokens expire in 3600s, ID tokens in 300s, auth codes in 600s. Defaults at module top.

## Key env vars

| Var | Note |
|-----|------|
| `SERVER_URL` | Used in `iss` JWT claim and endpoints list. Must match what clients can reach. |
| `PORT` / `HOST` | Bind address. `PORT` affects the default `SERVER_URL` too. |
| `SEED_COUNT` | Users pre-generated on startup. |
| `RSA_PRIVATE_KEY_PEM` | Use a fixed key across restarts so old tokens remain valid. |

## Dependencies

`fastapi`, `uvicorn`, `pyjwt[crypto]`, `cryptography`, `pillow`, `jinja2`, `python-multipart`. Test deps: `pytest`, `httpx` (pulled in by `fastapi.testclient`).
