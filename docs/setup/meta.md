# Meta (Facebook) — OAuth app setup

Meta's Graph API is one API; "services" (Ads, Pages, Instagram, Catalog, Leads) are gated by
**permissions (scopes)**. In **Development** mode a token can only reach assets owned by people
who hold an **app role** (admin / developer / tester) — there is no per-user allowlist beyond
app roles. Reaching a **real external client's** assets needs **App Review + Business
Verification**.

Redirect URI used by the hub — register the **exact, full https URL** (must include the scheme):
```
https://<your-backend-host>/api/connections/callback
# deployed example: https://hub187.pythonanywhere.com/api/connections/callback
# local dev:        http://localhost:8000/api/connections/callback   (Meta allows http://localhost)
```
> The hub builds this from `BACKEND_BASE_URL`. If that env var is missing the `https://`
> scheme, Meta rejects the request with **Error 400: invalid_request** — always set the full
> URL (`BACKEND_BASE_URL=https://hub187.pythonanywhere.com`).

---

## Part A — Create the app + products

developers.facebook.com → **My Apps → Create App**. When it asks what the app does, the
simplest compatible choice is **Other → Business** (this uses the classic scope-based OAuth the
hub's adapter sends). Then add these **Products**:
- **Facebook Login** (or *Facebook Login for Business* — see `META_CONFIG_ID` below)
- **Marketing API**

If the UI forces you to pick **use cases** instead, tick the ones matching what you need:
"Access the Marketing API" (ads), "Manage everything on your Page" (pages), an Instagram use
case, plus "Authenticate … with Facebook Login". Catalog/leads attach under the Business/Pages
use cases or are added in **App Review → Permissions and Features**.

## Part B — Facebook Login settings

App → **Facebook Login → Settings**:
- **Valid OAuth Redirect URIs**: your full callback URL from the top of this page.
- Client OAuth Login + Web OAuth Login: enabled.

## Part C — App credentials

App → **Settings → Basic**: copy **App ID** and **App Secret**. Leave **"Require App Secret"**
*off* for now — if you enable it, Graph calls also need an `appsecret_proof` (ask and it can be
added to the adapter).

## Part D — App roles (the "testers")

App → **App Roles → Roles** → add every person whose assets you'll touch in dev mode as an
**Admin, Developer, or Tester**, and have them **accept** the invite. Just logging in is *not*
enough — advanced permissions only work in Development mode for people who have accepted an app
role. (This is Meta's analogue to a testers list; there is no separate per-store allowlist.)

The token acts **as that person** and can only reach ad accounts / Pages / IG accounts /
catalogs / Business Managers that they are actually an admin/editor on — permissions gate the
*type* of action; asset roles gate *which* accounts.

## Part E — Permissions (scopes)

The code default (`DEFAULT_META_SCOPES`) is **ads-only**: `ads_read, ads_management,
business_management`. To reach Pages / Instagram / Catalog / Leads, set `META_SCOPES`
explicitly. Full "all services" set:

```
ads_read,ads_management,business_management,read_insights,
pages_show_list,pages_read_engagement,pages_read_user_content,pages_manage_metadata,
instagram_basic,instagram_manage_insights,
catalog_management,leads_retrieval
```

| Group | Scopes | Requires |
|---|---|---|
| **Ads** | `ads_read`, `ads_management`, `business_management`, `read_insights` | an ad account you have a role on |
| **Pages** | `pages_show_list`, `pages_read_engagement`, `pages_read_user_content`, `pages_manage_metadata` | at least one **Page** you admin |
| **Instagram** | `instagram_basic`, `instagram_manage_insights` | an IG **Business/Creator** account **linked to a Page** you admin |
| **Catalog / Leads** | `catalog_management`, `leads_retrieval` | a Business Manager / lead-form access |

- In **Development** mode these work for assets owned by app-role users — **no review**.
- On **other businesses'** accounts (production breadth) each permission needs **App Review**
  **and Business Verification**.
- `public_profile` is granted implicitly.

## Part F — Generate a token

Two ways:
- **Fastest (validation):** app dashboard → **Tools → Graph API Explorer** → select your app →
  add the permissions above → **Generate Access Token** → approve. Gives a **short-lived**
  (~1–2h) user token. Good for a quick `debug_token` / `/me/adaccounts` check.
- **Through the hub (real flow):** connect Meta from the client portal. The adapter exchanges
  the short-lived token for a **long-lived (~60-day)** token and stores that in the vault.

## Part G — `.env` (backend/.env)

```
META_APP_ID=your-app-id
META_APP_SECRET=your-app-secret
META_API_VERSION=v21.0
# Blank = ads-only default. Set the full list above to reach pages/IG/catalog/leads.
META_SCOPES=
# Optional: only for "Facebook Login for Business" configurations.
META_CONFIG_ID=
```

## Part H — Live

Providers are **live by default** (`Provider.is_mock` defaults to `False`), so no command is
required on a fresh install. Only if a provider row is currently in mock mode:
```bash
python manage.py set_provider_mode meta-ads --live    # validates config; --mock to revert
# restart the backend
```

The **Connect Meta** button opens the real Facebook consent screen; on approval the client's ad
accounts appear as connections.

## Gotchas

- **No classic refresh token.** The short-lived token is exchanged for a **long-lived (~60-day)**
  token; the hub re-exchanges it on refresh. Run `refresh_connections` / `run_scheduler` so it
  renews before expiry (else the connection flips to `needs_reconnect`).
- **Facebook Login for Business:** permissions live in a *configuration* object; create it, copy
  its id into `META_CONFIG_ID` (the adapter forwards it). Plain Facebook Login passes scopes
  directly (leave `META_CONFIG_ID` blank) — simplest for testing.
- **Pages/Instagram writes** need a **Page access token** derived from the user token
  (`GET /me/accounts` → the Page's `access_token`); the user/long-lived token alone reads.
- **Instagram** scopes are greyed out unless a Business/Creator IG account is linked to a Page
  you admin.
