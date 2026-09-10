> September 2026 audit update: consult [the audit rollout guide](audit-readiness.md) for minimal permissions, production security and current Google Cloud API access. Legacy examples below are not the audit onboarding policy.

# Going live with real providers

> Detailed per-provider setup (APIs to enable + exact scope names, app roles, distribution)
> lives in [`docs/setup/`](setup/README.md): [Google](setup/google.md) · [Meta](setup/meta.md) ·
> [Shopify](setup/shopify.md). This page is the quick reference.

Providers are **live by default** (`Provider.is_mock` defaults to `False`). To connect **real**
accounts you just create the provider's OAuth app and put its credentials in `backend/.env`.
The `MockAdapter` still exists as an opt-in escape hatch for offline tests / local debugging.

```bash
# NOT required on a fresh install — providers are already live. Use only to:
#   - flip a provider row that is currently mock, or
#   - validate that a provider's credentials are complete (fails loudly if not).
python manage.py set_provider_mode shopify --live     # or --mock to go offline
```

**Redirect URI to register in every provider console — full URL, scheme included:**

```
${BACKEND_BASE_URL}/api/connections/callback
# deployed example: https://hub187.pythonanywhere.com/api/connections/callback
# local default:    http://localhost:8000/api/connections/callback
```

> **`BACKEND_BASE_URL` must include the scheme.** If it's set scheme-less
> (`hub187.pythonanywhere.com`), the hub sends a scheme-less `redirect_uri` and Google/Meta
> reject sign-in with **Error 400: invalid_request**. Set `BACKEND_BASE_URL=https://…`.
>
> **HTTPS:** Shopify (and Meta in some cases) require an HTTPS redirect. A **deployed HTTPS
> backend needs no tunnel.** Only a **local http** backend needs a tunnel (ngrok / cloudflared)
> with `BACKEND_BASE_URL`/`FRONTEND_BASE_URL` pointed at it. Google allows `http://localhost`.

---

## Shopify (no tunnel needed if the backend is HTTPS)

1. **partners.shopify.com** → **Apps → Create app → manually**.
2. **Configuration**: set **App URL**, **Allowed redirection URL** (`<BACKEND_BASE_URL>/api/connections/callback`),
   and **Admin API access scopes** (same list as `SHOPIFY_SCOPES`) → **Save** → **Release** a version.
3. Copy **Client ID** / **Client secret**.
4. **Stores → Add store → Development store** — what you connect/test against.
5. For Orders/Customers scopes, enable **Protected customer data access** in the app config
   (instant on a dev store; review needed for live merchants).
6. `.env` (blank `SHOPIFY_SCOPES` = broad read+write default):
   ```
   SHOPIFY_API_KEY=...
   SHOPIFY_API_SECRET=...
   SHOPIFY_API_VERSION=2026-01     # use a currently-supported version
   SHOPIFY_SCOPES=
   ```
7. Client portal → **Connect Shopify** → enter `your-dev-store.myshopify.com` → approve.

Notes: callback is **HMAC-verified** (`?error=verification_failed` on mismatch); the offline
token does **not** expire; shop domain = account id. **Who can install:** dev stores install
freely (no testers list); a real store needs **Custom distribution** (one store, instant, no
review) or **Public** (App Store review — weeks + GDPR webhooks).

---

## Meta (testable on localhost)

1. **developers.facebook.com → My Apps → Create App** → **Other → Business**.
2. Add **Facebook Login** + **Marketing API** products.
3. Facebook Login → Settings → **Valid OAuth Redirect URIs**: your full callback URL.
4. **App Roles → Roles**: add anyone whose assets you'll touch as admin/developer/**tester**
   and have them accept — dev mode only reaches app-role users' assets.
5. Copy **App ID** / **App Secret** (Settings → Basic).
6. `.env` (blank `META_SCOPES` = **ads-only** default; set the full list for pages/IG/catalog):
   ```
   META_APP_ID=...
   META_APP_SECRET=...
   META_API_VERSION=v21.0
   META_SCOPES=          # ads_read,ads_management,business_management,read_insights,pages_show_list,...
   META_CONFIG_ID=       # only for Facebook Login for Business
   ```
7. Quick token: **Tools → Graph API Explorer** → add permissions → Generate. The hub exchanges
   it for a **long-lived (~60-day)** token on connect.

Notes: no classic refresh token (long-lived token re-exchanged on refresh — run
`refresh_connections`/`run_scheduler`). Pages/IG need a Page (and a linked Business/Creator IG).
Other businesses' accounts need **App Review + Business Verification**.

---

## Google (most involved — start the developer-token application early)

1. **Google Cloud Console** → new project → **APIs & Services → Library** → **enable every API**
   for the scopes you keep (Ads, Analytics Admin + Data, Search Console, Content, Sheets, Drive,
   Business Profile). *Granting a scope does not enable its API* — a disabled API 403s at fetch
   time (`SERVICE_DISABLED`).
2. **OAuth consent screen**: add the scopes; add **test users** (External + Testing); note that
   sensitive/restricted scopes (Drive, Analytics, Content) need verification for production.
3. **Credentials → Create OAuth client ID** (Web application) → add the full callback as an
   authorized redirect URI → copy **client id/secret**.
4. **Ads only:** get a **developer token** from a **Manager (MCC) account** (Admin → API Center;
   Basic access ~1–2 days) and note the MCC **login-customer-id** (digits only). Analytics /
   Search Console / Merchant / Drive / Sheets work **without** the developer token.
5. `.env`:
   ```
   GOOGLE_ADS_CLIENT_ID=...
   GOOGLE_ADS_CLIENT_SECRET=...
   GOOGLE_ADS_DEVELOPER_TOKEN=...       # Ads only
   GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890   # Ads only, digits only
   GOOGLE_ADS_API_VERSION=v21
   GOOGLE_SCOPES=                        # blank = broad default set
   ```
6. Client portal → **Connect Google** → real consent screen.

---

## Reverting to mock (offline debugging)

```bash
python manage.py set_provider_mode <slug> --mock
```

Mock and live can be mixed freely while credentials/approvals are pending.
