# Shopify — OAuth app setup

Shopify **requires an HTTPS redirect**, so local testing needs a tunnel (ngrok / cloudflared).
The callback is **HMAC-verified** with your API secret — forged callbacks are rejected
(`?error=verification_failed`).

Redirect URI used by the hub (register the tunnel form of it):
```
<https-base>/api/connections/callback
# local example: https://<your-tunnel>.trycloudflare.com/api/connections/callback
```

---

## Part A — Tunnel (local testing)

```bash
cloudflared tunnel --url http://localhost:8000       # or: ngrok http 8000
```
Set in `backend/.env` (so authorize + callback URLs use HTTPS):
```
BACKEND_BASE_URL=https://<your-tunnel>
```

## Part B — Create the app

Shopify **Partners** account → **Apps → Create app** (custom or public).
- **App URL**: `<https-base>/`
- **Allowed redirection URL(s)**: `<https-base>/api/connections/callback`
- Copy the **API key** and **API secret key** (Client credentials).

## Part C — Development store

Partners → **Stores → Add store → Development store** — this is what you'll connect/test against.

## Part D — Scopes

The hub requests these exact Shopify access scopes (default; override with `SHOPIFY_SCOPES`).
Configure the **same** set on the app's API access:

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

(Some scopes like `read_customers`/`read_orders` are *protected customer data* — a public app
distributed via the App Store needs Shopify's protected-data approval; a custom app on your own
dev store does not.)

## Part E — `.env` (backend/.env)

```
SHOPIFY_API_KEY=your-api-key
SHOPIFY_API_SECRET=your-api-secret
SHOPIFY_API_VERSION=2025-01
# Blank = the broad read+write default above
SHOPIFY_SCOPES=
```

## Part F — Go live

```bash
python manage.py set_provider_mode shopify --live    # --mock to revert
# restart the backend
```

Client portal → **Connect Shopify** → enter the store domain (`your-store.myshopify.com`) →
approve. The offline token is stored (it does **not** expire).

## Gotchas

- **HTTPS is mandatory** for the redirect — the tunnel is not optional for local testing.
- The offline token dies when the merchant **uninstalls** the app → next test flips the
  connection to `needs_reconnect`.
- The shop domain **is** the account id; connecting a second store is a separate connection with
  its own credential.
- Keep `SHOPIFY_SCOPES` in `.env` in sync with the scopes configured on the Shopify app.
