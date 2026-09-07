# Provider setup guides

Step-by-step OAuth app creation for each provider — the APIs/products to enable, app roles /
distribution, the exact scopes the hub requests, and the `.env` values.

- **[Google](google.md)** — Cloud project, **enable an API per scope** (scope ≠ enabled API),
  consent screen + test users, OAuth client, Ads developer token/MCC. (Broad "Google" connector.)
- **[Meta](meta.md)** — Business app, Facebook Login + Marketing API, **app roles/testers**,
  ads-only default scopes (extend for Pages/Instagram/Catalog/Leads). Localhost-testable.
- **[Shopify](shopify.md)** — Partner app + dev store, config-driven scopes (**Release** a
  version), protected customer data, HMAC-verified callback, **distribution** (dev store /
  custom / public). No tunnel when the backend is HTTPS.

Common to all:

- Register the redirect URI `<BACKEND_BASE_URL>/api/connections/callback` — **full URL with the
  `https://` scheme**, or Google/Meta return `invalid_request`.
- Put credentials in `backend/.env`.
- **Providers are live by default** (`Provider.is_mock` defaults to `False`) — no command needed
  on a fresh install. The MockAdapter remains for offline tests / debugging.

```bash
# Optional: only to flip a currently-mock row live, or validate credentials are complete.
python manage.py set_provider_mode <slug> --live    # google-ads | meta-ads | shopify
python manage.py set_provider_mode <slug> --mock    # go offline again
```

The command validates config and rolls back if anything is missing. Each provider is
independent — mock and live can be mixed while credentials/approvals are pending.
