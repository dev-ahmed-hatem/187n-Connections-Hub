# Provider setup guides

Step-by-step OAuth app creation for each provider — the APIs/products to enable, the exact
scopes the hub requests, the `.env` values, and how to flip the provider live.

- **[Google](google.md)** — Cloud project, APIs to enable per scope, consent screen, OAuth
  client, Ads developer token/MCC. (Broad "Google" connector.)
- **[Meta](meta.md)** — Business app, Facebook Login + Marketing API, `ads_read` /
  `ads_management` / `business_management`. Localhost-testable.
- **[Shopify](shopify.md)** — Partner app, HTTPS tunnel, HMAC-verified callback, broad
  read+write scopes.

Common to all: register the redirect URI `<BACKEND_BASE_URL>/api/connections/callback`, put
credentials in `backend/.env`, then:

```bash
python manage.py set_provider_mode <slug> --live    # google-ads | meta-ads | shopify
```

The command validates the config and rolls back if anything is missing. Each provider is
independent — mock and live can be mixed while credentials/approvals are pending.
