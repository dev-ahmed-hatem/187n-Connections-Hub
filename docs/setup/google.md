> September 2026 audit update: consult [the audit rollout guide](../audit-readiness.md) for minimal permissions, production security and current Google Cloud API access. Legacy examples below are not the audit onboarding policy.

# Google — OAuth app setup

The Google connector is broad ("Google", not just Ads). Everything below must line up:
each **scope** you request needs its **API enabled** in the Cloud project *and* the scope
added to the **OAuth consent screen**.

> **Scope granted ≠ API enabled.** These are two independent switches. Consent can succeed and
> the token can carry a scope, yet a data call still fails **at fetch time** with
> `403 PERMISSION_DENIED / SERVICE_DISABLED` if that scope's API isn't enabled in the project.
> (We hit exactly this: Drive worked only after enabling the Drive API; Analytics 403'd until
> the Analytics Admin + Data APIs were enabled.) Enable every API in Part A for the scopes you
> keep.

Redirect URI used by the hub — register the **exact, full URL** (scheme included):
```
https://<your-backend-host>/api/connections/callback
# deployed example: https://hub187.pythonanywhere.com/api/connections/callback
# local dev:        http://localhost:8000/api/connections/callback
```
(Google allows `http://localhost` for dev — no tunnel needed. In prod use your HTTPS domain.)

> **Include the scheme.** The hub builds this from `BACKEND_BASE_URL`. If that env var is set
> without `https://` (e.g. `hub187.pythonanywhere.com`), Google receives a scheme-less
> `redirect_uri` and blocks sign-in with **Error 400: invalid_request**. Always set the full URL:
> `BACKEND_BASE_URL=https://hub187.pythonanywhere.com`.

---

## Part A — Cloud project + enable APIs

Google Cloud Console → create/select a project → **APIs & Services → Library** → enable each
API below (exact names as they appear in the Library):

| Scope you request | API to enable (exact name) |
|---|---|
| `https://www.googleapis.com/auth/adwords` | **Google Ads API** |
| `https://www.googleapis.com/auth/analytics.readonly` | **Google Analytics Admin API** *and* **Google Analytics Data API** |
| `https://www.googleapis.com/auth/webmasters.readonly` | **Google Search Console API** |
| `https://www.googleapis.com/auth/content` | **Content API for Shopping** |
| `https://www.googleapis.com/auth/business.manage` | **Google Business Profile API** *(requires access request — see gotchas)* |
| `https://www.googleapis.com/auth/spreadsheets.readonly` | **Google Sheets API** |
| `https://www.googleapis.com/auth/drive.readonly` | **Google Drive API** |
| `openid`, `email`, `profile` | none — OpenID Connect, no API to enable |

> Only enable the APIs for the scopes you actually keep in `GOOGLE_SCOPES`. Enabling an API
> you don't use is harmless; requesting a scope whose API is disabled fails.

## Part B — OAuth consent screen

**APIs & Services → OAuth consent screen**:
- **User type**: *Internal* if you have Google Workspace (no verification, org users only), else
  *External*.
- Add all the scopes you'll request (the full URLs from the table above + `openid`, `email`,
  `profile`).
- **External + Testing**: add every Google account that will connect under **Test users**
  (an "unverified app" warning is normal in testing).
- Going to **Production/Published** removes the 7-day refresh-token expiry but sensitive/
  restricted scopes (Drive, Analytics, Content, Business Profile) then need **Google app
  verification**.

## Part C — OAuth client (client id + secret)

**APIs & Services → Credentials → Create credentials → OAuth client ID**:
- Application type: **Web application**.
- **Authorized redirect URIs**: `http://localhost:8000/api/connections/callback`
- Create → copy **Client ID** and **Client secret**.

## Do we need a Manager account (MCC)?

**For Google Ads: yes.** Every Google Ads API call needs a **developer token**, and Google only
issues developer tokens to a **Manager (MCC) account** — you can't get one from a regular Google
Ads account. So:

- **No MCC → no developer token → no Google Ads API.** OAuth still connects the client's Google
  account, and **Analytics / Search Console / Merchant / Sheets / Drive still work without an
  MCC** — only Ads is blocked.
- An MCC here is just **the thing that owns your developer token**. The hub uses the **standard
  OAuth** model: the client grants access and you call *their* account with **your** developer
  token — their account does **not** need to be linked under your MCC. (Linking clients under an
  MCC is a separate, optional model the hub doesn't require.)

**Recommendation: create one.** It's free, takes minutes, needs no ad spend, doesn't affect
clients, and it's the only path to Ads API access. Test-account access is instant; **Basic
access** (real client data) is a short application (~1–2 days). Skip it only if the hub won't
handle Google Ads at all — then remove `https://www.googleapis.com/auth/adwords` from
`GOOGLE_SCOPES` and leave the developer token blank.

## Part D — Google Ads only: developer token + Manager account

Needed **only** for the `adwords` scope / Ads data (not for Analytics/Search Console/etc.):
- Create a free **Google Ads Manager account (MCC)** → **Admin → API Center** → copy the
  **developer token** (test-account access is instant; **Basic access** for real production data
  needs an application, ~1–2 days).
- Note the MCC **login-customer-id** (10 digits, no dashes).

## Part E — `.env` (backend/.env)

```
GOOGLE_ADS_CLIENT_ID=xxxx.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=xxxx
GOOGLE_ADS_DEVELOPER_TOKEN=            # Ads only
GOOGLE_ADS_LOGIN_CUSTOMER_ID=          # Ads only, digits only
GOOGLE_ADS_API_VERSION=v21
# Blank = the broad default scope set below. Override to match enabled APIs.
GOOGLE_SCOPES=
```

Default scopes requested when `GOOGLE_SCOPES` is blank:
```
openid
email
profile
https://www.googleapis.com/auth/adwords
https://www.googleapis.com/auth/analytics.readonly
https://www.googleapis.com/auth/webmasters.readonly
https://www.googleapis.com/auth/content
https://www.googleapis.com/auth/business.manage
https://www.googleapis.com/auth/spreadsheets.readonly
https://www.googleapis.com/auth/drive.readonly
```

## Part F — Live

Providers are **live by default** (`Provider.is_mock` defaults to `False`), so no command is
required on a fresh install. Only if a provider row is currently in mock mode:

```bash
python manage.py set_provider_mode google-ads --live   # validates config; --mock to revert
# restart the backend
```

The client portal's **Connect Google** button opens the real Google consent screen.
Analytics / Search Console / Merchant / Drive / Sheets data work with just the OAuth token
(once each API is enabled); **Ads** additionally needs the developer token.

## Gotchas

- **Business Profile API** (`business.manage`) is access-gated by Google — you must request
  access via their form/allowlist before it can be enabled/used. If you don't need it, drop it
  from `GOOGLE_SCOPES` and skip enabling that API.
- **Testing mode → refresh tokens expire in 7 days.** Publish to Production for durable tokens.
- **Sensitive/restricted scopes** (Drive, Analytics, Content, Business Profile) trigger the
  unverified-app warning in testing and require verification for External production use.
- Each requested scope's **API must be enabled** — a disabled API doesn't block consent, it
  fails the **data call** with `403 SERVICE_DISABLED`. Enable the API in Part A per scope.
- **Redirect must be a full `https://` URL.** A scheme-less `BACKEND_BASE_URL` → `invalid_request`.
