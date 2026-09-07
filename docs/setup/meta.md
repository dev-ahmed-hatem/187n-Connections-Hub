# Meta (Facebook) Ads — OAuth app setup

Testable on **localhost** (Meta allows `http://localhost` redirects in development).

Redirect URI used by the hub (register it exactly):
```
http://localhost:8000/api/connections/callback
```

---

## Part A — Create the app + products

developers.facebook.com → **My Apps → Create App** → type **Business**. Then add these
**Products** to the app:
- **Facebook Login** (or *Facebook Login for Business* — see `META_CONFIG_ID` below)
- **Marketing API**

## Part B — Facebook Login settings

App → **Facebook Login → Settings**:
- **Valid OAuth Redirect URIs**: `http://localhost:8000/api/connections/callback`
- Client OAuth Login + Web OAuth Login: enabled.

## Part C — App credentials

App → **Settings → Basic**: copy **App ID** and **App Secret**.

## Part D — Permissions (scopes)

The hub requests these exact scopes (default; override with `META_SCOPES`):

| Scope (exact) | Purpose |
|---|---|
| `ads_read` | Read ad accounts, campaigns, insights |
| `ads_management` | Create/edit campaigns (take actions) |
| `business_management` | Read/manage Business Manager assets |

- In **Development** mode these work for ad accounts **you** (app admins/developers/testers)
  own — no review needed.
- Using them on **other businesses'** accounts (production breadth) requires **App Review** for
  each permission **and Business Verification**.
- `public_profile` is granted implicitly.

## Part E — `.env` (backend/.env)

```
META_APP_ID=your-app-id
META_APP_SECRET=your-app-secret
META_API_VERSION=v21.0
# Blank = broad default (ads_read, ads_management, business_management)
META_SCOPES=
# Optional: only if you use "Facebook Login for Business" configurations
META_CONFIG_ID=
```

## Part F — Go live

```bash
python manage.py set_provider_mode meta-ads --live   # --mock to revert
# restart the backend
```

The **Connect Meta** button now opens the real Facebook consent screen; on approval the client's
ad accounts appear as connections.

## Gotchas

- **No classic refresh token.** The short-lived token is exchanged for a **long-lived (~60-day)**
  token; the hub re-exchanges it on refresh. Run `refresh_connections` / `run_scheduler` so it
  renews before expiry (else the connection flips to `needs_reconnect`).
- If the app enables **"Require app secret"** (Settings → Advanced), Graph calls also need an
  `appsecret_proof` — tell me and I'll add it to the adapter.
- Business/system-user access to many clients is where App Review + Business Verification matter;
  your own accounts in dev mode don't need them.
