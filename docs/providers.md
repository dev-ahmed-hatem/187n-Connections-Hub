# Going live with real providers

The hub ships with a `MockAdapter` so everything works locally without credentials.
To connect **real** accounts, create the provider's OAuth app, put its credentials in
`backend/.env`, then flip the provider live:

```bash
python manage.py set_provider_mode shopify --live     # or --mock to revert
```

`set_provider_mode ... --live` validates that the required credentials are present and
fails loudly if any are missing. Each provider is independent — go live one at a time.

**Redirect URI to register in every provider console:**

```
${BACKEND_BASE_URL}/api/connections/callback
# local default: http://localhost:8000/api/connections/callback
```

> **Local HTTPS:** Shopify (and Meta in some cases) require an **HTTPS** redirect. For local
> testing, run a tunnel (ngrok / cloudflared) and point `BACKEND_BASE_URL` and
> `FRONTEND_BASE_URL` in `.env` at the tunnel URL. Google allows `http://localhost`.

---

## Shopify (needs an HTTPS tunnel for local testing)

Shopify **requires an HTTPS redirect**, so local testing needs a tunnel (ngrok/cloudflared).

1. Create a **Shopify Partner** account → **Apps → Create app**.
2. Run a tunnel (e.g. `cloudflared tunnel --url http://localhost:8000`) and set
   `BACKEND_BASE_URL` in `.env` to the tunnel URL. Set the app's **Allowed redirection URL** to
   `<tunnel>/api/connections/callback`.
3. Copy the **API key** and **API secret key**.
4. Create a **development store** (Partners → Stores → Add store).
5. `.env` (leave `SHOPIFY_SCOPES` blank for the broad read+write default):
   ```
   SHOPIFY_API_KEY=...
   SHOPIFY_API_SECRET=...
   SHOPIFY_API_VERSION=2025-01
   SHOPIFY_SCOPES=
   ```
6. `python manage.py set_provider_mode shopify --live`
7. Client portal → **Connect Shopify** → enter `your-dev-store.myshopify.com` → approve.

Notes: the OAuth callback is **HMAC-verified** with the API secret (forged callbacks are
rejected → `?error=verification_failed`). The offline access token does **not** expire; the shop
domain is the account id. On app uninstall the token dies → shows as `needs_reconnect`.

---

## Meta Ads (testable on localhost)

1. **developers.facebook.com → My Apps → Create App** (type: **Business**).
2. Add **Facebook Login** + **Marketing API** products.
3. Facebook Login → Settings → **Valid OAuth Redirect URIs**:
   `http://localhost:8000/api/connections/callback`
4. Copy **App ID** and **App Secret**. Keep the app in **Development** and add yourself as
   admin/tester — dev mode reaches your own ad accounts.
5. `.env` (leave `META_SCOPES` blank for the broad default
   `ads_read, ads_management, business_management`):
   ```
   META_APP_ID=...
   META_APP_SECRET=...
   META_API_VERSION=v21.0
   META_SCOPES=
   META_CONFIG_ID=        # only for Facebook Login for Business
   ```
6. `python manage.py set_provider_mode meta-ads --live`

Notes: no classic refresh token — the short-lived token is exchanged for a **long-lived**
(~60-day) token, re-exchanged on refresh. `ads_management`/`business_management` on **other
businesses'** accounts needs **App Review + Business verification** (your own accounts work in
dev mode). If the app enables "Require app secret," calls also need an `appsecret_proof`.

---

## Google Ads (most involved — start the developer-token application early)

1. **Google Cloud Console** → new project → enable the **Google Ads API**.
2. **APIs & Services → Credentials → Create OAuth client ID** (Web application). Add the
   hub callback as an authorized redirect URI. Copy **client id/secret**.
3. In your **Google Ads Manager Account (MCC) → Admin → API Center**, get a
   **developer token**. Test-account access is immediate; **Basic access** (for real
   production data) requires an application, usually approved in ~1–2 days — apply early.
4. Note your MCC **login-customer-id** (10 digits, no dashes).
5. `.env`:
   ```
   GOOGLE_ADS_CLIENT_ID=...
   GOOGLE_ADS_CLIENT_SECRET=...
   GOOGLE_ADS_DEVELOPER_TOKEN=...
   GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890
   GOOGLE_ADS_API_VERSION=v18
   ```
6. `python manage.py set_provider_mode google-ads --live`

Notes: for testing without Basic access, create a **test manager + test client account**.
This phase uses the configured/first accessible customer; a multi-account picker is a
follow-up.

---

## Reverting to mock

```bash
python manage.py set_provider_mode <slug> --mock
```

Mock and live can be mixed freely (e.g. Shopify live, Google still mock) while credentials
and approvals are pending.
