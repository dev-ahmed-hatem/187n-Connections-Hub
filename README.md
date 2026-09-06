# Connections Hub

An internal platform where clients connect their **Google Ads / Meta Ads / Shopify**
accounts **once**, and any team project — once granted access — can pull **data** or a
**short-lived token** for that client, without ever handling the client's credentials.

This repo is scaffolded with **mock OAuth providers** so the whole flow works end-to-end
locally. Real, verified provider apps swap in later behind the same adapter interface —
no caller changes.

## Stack

- **Backend**: Django 5 + DRF, SQLite, SimpleJWT, Fernet-encrypted token vault. (Python 3.10)
- **Frontend**: React 19 + Vite + TypeScript, Ant Design, Redux Toolkit + RTK Query. (Node 20+)

## Layout

```
hub/
  backend/    Django project (apps: users, authentication, providers, connections, access, portal)
  frontend/   Vite React app (one role-based app: client / developer / admin areas)
```

## Run it

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate           # Windows;  source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env             # optional; sensible dev defaults are baked in
python manage.py migrate
python manage.py seed_demo       # creates demo users, providers, connections, a grant + API key
python manage.py runserver
```

`seed_demo` prints the demo logins and a one-time **Demo Operator API key**.

### Frontend

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173  (proxies to http://localhost:8000/api)
```

## Demo logins

| Username    | Password    | Role      | Sees                                    |
|-------------|-------------|-----------|-----------------------------------------|
| `admin`     | `admin123`  | admin     | grants, clients/users, announcements, audit |
| `dev`       | `dev12345`  | developer | client access, API keys                 |
| `northwind` | `client123` | client    | Northwind Coffee's connections & updates |
| `lumen`     | `client123` | client    | Lumen Skincare (has a "needs reconnect") |
| `volt`      | `client123` | client    | Volt Fitness (fully connected)          |

## Walk the flow

1. **Client** (`northwind`) → *Connections* → click **Connect** on Meta Ads → mock consent →
   **Allow** → status turns green.
2. **Developer** (`dev`) → *Client access* → pick **Northwind Coffee** → **Preview data**
   returns mock metrics; **Fetch token** returns a ~1-hour token.
3. **Developer** requests a connection for a not-connected platform → it appears in the
   **client's** *Updates & blockers* → client connects it.
4. **Admin** (`admin`) → *Audit log* shows every access call (including denied ones).

### Machine (API-key) access

```bash
KEY="<Demo Operator API key from seed_demo>"
# data-proxy (has a grant → 200):
curl "http://localhost:8000/api/access/clients/1/google-ads/data?range=last_30d" \
  -H "Authorization: ApiKey $KEY"
# token-broker:
curl -X POST "http://localhost:8000/api/access/clients/1/shopify/token" \
  -H "Authorization: ApiKey $KEY"
# without a grant → 403 (try meta-ads for client 1)
```

## Key design points

- **One OAuth app per provider**, owned by the hub — clients never create their own.
- **Token vault**: refresh/access tokens are Fernet-encrypted at rest; refresh tokens are
  never returned by any API.
- **Grant matrix** is the access gate: an API-key consumer gets `403` for any client/provider
  it hasn't been granted.
- **Adapter interface** (`providers/adapters/base.py`) isolates provider specifics — going
  live means adding a real adapter + credentials, nothing else.

## Going live with real providers

Real OAuth adapters for **Google Ads, Meta Ads, Shopify** are implemented
(`backend/providers/adapters/{google_ads,meta_ads,shopify}.py`). To connect real accounts:

1. Create the provider's OAuth app and put its credentials in `backend/.env`
   (see the per-provider block in `.env.example`).
2. Flip the provider live (validates config, fails loudly if incomplete):
   ```bash
   python manage.py set_provider_mode shopify --live     # --mock to revert
   ```

Full step-by-step setup (app creation, scopes, redirect URIs, test accounts, and the local
HTTPS tunnel needed for Shopify) is in **[docs/providers.md](docs/providers.md)**.

Mock and live can be mixed per provider while credentials/approvals are pending. The mock
stays the default from `seed_demo`.

## Background token refresh

Access tokens refresh on demand, but you can also keep credentials fresh proactively (no Celery):

```bash
python manage.py refresh_connections            # one-shot: refresh near-expiry credentials
python manage.py run_scheduler --interval 900   # blocking loop; run as its own process
```

Failures flip the affected connections to `needs_reconnect` so the client is prompted.

## Tests

```bash
cd backend && python manage.py test          # encryption, adapter, grant enforcement, API-key auth
cd frontend && npm run build                 # type-check + production build
```
