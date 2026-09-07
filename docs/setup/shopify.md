# Shopify — OAuth app setup

Shopify OAuth is **per-shop** (you authorize one store at a time; the shop domain *is* the
account id). The offline access token **does not expire**. The callback is **HMAC-verified**
with your API secret — forged callbacks are rejected (`?error=verification_failed`).

Shopify requires an **HTTPS** redirect:
```
<BACKEND_BASE_URL>/api/connections/callback
# deployed example: https://hub187.pythonanywhere.com/api/connections/callback
```
> **No tunnel needed if your backend is already HTTPS** (e.g. a PythonAnywhere / hosted
> deployment). A tunnel (ngrok / cloudflared) is only required when testing against a **local
> http** backend — see Part A. Ensure `BACKEND_BASE_URL` includes the `https://` scheme.

---

## Part A — Tunnel (ONLY for a local http backend)

Skip this entirely if your backend is deployed over HTTPS. For local dev:
```bash
cloudflared tunnel --url http://localhost:8000       # or: ngrok http 8000
```
Then set `BACKEND_BASE_URL=https://<your-tunnel>` in `backend/.env`.

## Part B — Partner account + development store

1. Sign up free at **partners.shopify.com** (no store required).
2. **Stores → Add store → Create development store** (e.g. `northwind-coffee.myshopify.com`).
   Optionally preload sample products/orders. This is what you connect/test against.

## Part C — Create the app + release the config

1. **Apps → Create app → Create app manually** → name it.
2. **Configuration** tab:
   - **App URL**: your frontend URL (e.g. `https://187n-hub.vercel.app`).
   - **Allowed redirection URL(s)**: your full callback URL from the top of this page.
   - **Admin API access scopes**: the same scope list you put in `SHOPIFY_SCOPES` (Part D).
     Modern Shopify apps are **config-driven** — scopes requested at OAuth time must be declared
     here or they won't be granted.
   - **Save**, then **Release** a new **version**. Configuration changes (App URL, redirect,
     scopes) only take effect once released.
3. **API credentials / Client credentials** → copy **Client ID** (API key) and **Client secret**.

## Part D — Scopes

The hub's broad default (blank `SHOPIFY_SCOPES`) is full read+write. Keep the **app config**
scopes identical:

```
read_orders        write_orders
read_products      write_products
read_customers     write_customers
read_inventory     write_inventory
read_fulfillments  write_fulfillments
read_discounts     write_discounts
read_price_rules   write_price_rules
read_draft_orders  write_draft_orders
read_content       write_content
read_reports
```

**Protected customer data access (required for Orders *and* Customers).** Any app touching the
Orders, Customers, Draft Orders, or Fulfillments APIs must enable this in the app config
(**API access → Protected customer data access → Request access**) and answer the data-protection
questions. On a **development store it is granted immediately** once configured; full Shopify
review is only needed to distribute to **live production merchants**. Without it, those scopes
fail even when granted.

To start minimal (read-only, no protected-data gate), set:
```
SHOPIFY_SCOPES=read_orders,read_products,read_inventory,read_fulfillments,read_content,read_reports
```
(the data preview only needs `read_orders,read_products`).

## Part E — `.env` (backend/.env)

```
SHOPIFY_API_KEY=your-client-id
SHOPIFY_API_SECRET=your-client-secret
SHOPIFY_API_VERSION=2025-01      # ⚠ bump to a currently-supported version — see gotchas
# Blank = the broad read+write default above
SHOPIFY_SCOPES=
```

## Part F — Live + connect

Providers are **live by default** — no command needed on a fresh install. (Only if the row is
mock: `python manage.py set_provider_mode shopify --live`.)

Client portal → **Connect Shopify** → enter the store domain (`your-store.myshopify.com`) →
approve on Shopify → HMAC-verified callback → offline token stored → developer **Preview data**
returns `orders`, `products`, `shop_name`, `currency`.

## Who can install (there is no "testers" list)

| Store | Can authorize your unlisted app? |
|---|---|
| A **development store** in your Partner account | ✅ Immediately, via OAuth — no review, no allowlist. |
| A **real / live merchant store** | ❌ Not until you set up distribution (below). |

- **Custom distribution** — for a specific real store. App → **Distribution → Custom** → enter
  the store's `.myshopify.com` → Shopify gives a one-time install link. **No App Store review.**
  Caveat: **one store per app, and the choice is permanent.** Best fit for onboarding known
  clients (recommended for this hub).
- **Public distribution** — any merchant can install, but requires **App Store review**:
  typically **~1–2 weeks** for a first response (often several weeks with revisions) **plus**
  real requirements — mandatory GDPR webhooks (`customers/data_request`, `customers/redact`,
  `shop/redact`), a full listing, privacy policy, performance criteria. Only pursue this to open
  the app to the whole Shopify market.

## Gotchas

- **API version:** `2025-01` may be past Shopify's ~12-month support window — set
  `SHOPIFY_API_VERSION` to a current stable version (check the app's **API versions** page, e.g.
  `2026-01`), or `fetch_data` calls 400.
- **Config = env:** scopes in `SHOPIFY_SCOPES` must match the app's **Admin API access scopes**
  (and be **released**), or the install won't grant them.
- The offline token dies when the merchant **uninstalls** the app → next test flips the
  connection to `needs_reconnect`.
- The shop domain **is** the account id; a second store is a separate connection + credential.
- **Token types:** the OAuth flow stores an app **offline token** (`shpat_…`, non-expiring). A
  store's **custom-app / staff token** (`shpua_…`) also works for Admin REST but is a different
  token type — fine for validation, not what the vault stores.
