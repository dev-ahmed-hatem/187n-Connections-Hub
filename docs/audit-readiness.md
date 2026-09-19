# Read-only account audit rollout

This change prepares secure onboarding and **sample API probes**, not a completed customer audit. OAuth `connected` means authorized, not that Ads, GA4 or commerce data has been verified. Do not attach real customer data while public demo principals remain active.

## Review and production gate

Obtain explicit owner approval before deploying or executing the account commands in production. Confirm the Vercel alias → project → production branch → commit and PythonAnywhere web app → WSGI path → checkout/commit. GitHub push access alone does not confer either permission. A preview build must use isolated backend/configuration, never seed or migrate production automatically.

Before rollout, back up the backend database and retain the **existing vault encryption key** securely. Test restoration and token decryption without printing plaintext. Do not replace `HUB_FIELD_ENCRYPTION_KEY` blindly: doing so strands existing credentials. If the published development key has ever protected real credentials, plan a controlled vault migration and provider credential rotation with the owner. Keep keys, passwords, OAuth codes and reports containing customer data out of git, build logs and PRs.

Required production configuration: `DJANGO_DEBUG=false`, an independently generated `DJANGO_SECRET_KEY`, a protected vault key, explicit hosts, HTTPS frontend/backend URLs, `CORS_ALLOW_ALL=false` and `CORS_ALLOWED_ORIGINS=https://<approved-frontend>`. The checked-in dev defaults are not production configuration. Review session/CSRF cookie security with the PythonAnywhere proxy configuration. Do not blindly enable HTTPS redirect behind a proxy without verifying forwarded HTTPS handling.

After backup and approval:

1. Deploy the reviewed backend commit and run `python manage.py migrate`, then `python manage.py check --deploy`. The additive `allow_token_broker` migration preserves all existing projects' behavior.
2. Create one named account per operator with `python manage.py create_personal_user --username <personal-login> --email <personal-email> --role admin`. Use `--role developer` for the confirmed assigned developer. Passwords are collected in a hidden prompt, never command arguments or command output; save them in the approved password manager. No mail is sent.
3. Verify each personal admin can actually log in. Preview `python manage.py secure_demo_access --replacement-admin <personal-login>`, then run with `--apply`. This disables all five seeded demo users and any `Demo Operator` API keys, without deleting client organizations, connections, credentials or projects. Inactive users cannot use access/refresh tokens; changing passwords invalidates previous JWT access tokens. Existing JWTs without the password claim require a new login after this change.
4. Deploy the frontend (no published demo credentials). Verify all former demo logins and keys fail, including old sessions, and personal login succeeds. `seed_demo` now requires both DEBUG and explicit `ALLOW_DEMO_SEED=true`; it cannot run in production.
5. Preview `python manage.py provision_audit --org-name <client-name> --org-slug <new-slug> --client-username <personal-client-login> --client-email <personal-email> --developer <confirmed-personal-dev> --admin <personal-admin>`, then use `--apply`. The command refuses existing names/organizations, demo identities and onboarding while demo principals remain active. It creates a new organization, personal client and project assigned to the confirmed developer. It never issues a machine key, sends messages, authorizes a provider or copies demo connections. Provider token brokering is disabled for that project.
6. Have the client authorize the correct assets themselves. Test each platform independently as below. Do not restore active demo access as a rollback; keep demo identities disabled and client credentials protected.

## Provider ownership and authorization

Record the owner/admin, app/project identifier, app mode, installed/approved scopes, authorized account identity, API access level, callback URL and consent date for each provider in a **private** handover. Test-user status must be checked in each app console; a working Hub admin login cannot prove it.

- **Shopify:** default new consent asks for `read_orders,read_products`. The collaborator code is only for requesting store access, not an API token. Confirm the exact `myshopify.com` domain and distribution/install eligibility. Have the merchant approve installation. Orders older than 60 days require separately approved `read_all_orders` in addition to orders access. The probe reads no names, emails or addresses. Standard order access does not provide a complete storefront session funnel. [Shopify Order permissions](https://shopify.dev/docs/api/admin-graphql/latest/objects/Order).
- **Meta Ads:** use `ads_read`, plus only additional permissions proven necessary for account discovery. A Business ID is not an `act_` ad account. Confirm the ad account belongs to that Business and the person has permitted asset access. The app owner must check Development/Live mode, approved permissions and eligibility before adding a tester. A tester must accept their own invitation and consent; tester status alone is not a universal bypass for review or business verification. [Meta Marketing API reference](https://developers.facebook.com/docs/marketing-api/insights/).
- **Google Ads:** `adwords` has no read-only OAuth variant; use a read-only Google Ads user and the audit data proxy, with token brokering disabled. **As of 9 September 2026 API access levels are associated with the OAuth Google Cloud project; a developer token is no longer the onboarding gate.** Verify the project's production API access and the exact customer, including manager routing where needed. Default API version is v24; explicit environment overrides must be reviewed. [Google migration notice](https://developers.google.com/google-ads/api/docs/api-policy/developer-token), [version schedule](https://developers.google.com/google-ads/api/docs/sunset-dates).
- **GA4:** independently verify Analytics Admin + Data APIs, `analytics.readonly`, and Viewer access to the exact property. A Google Ads success is not a GA4 success. The probe requests traffic, e-commerce and key-event metrics and a separate funnel-event report. [GA4 schema](https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema).
- **Google testing:** the app owner must check the Audience setting and add the client's actual Google account if External/Testing applies. Testing authorizations usually expire after seven days. Do not publish apps or expand scopes just to remove this limit without the owner's decision. [Google app audience](https://support.google.com/cloud/answer/15549945?hl=en).

New default scopes are limited; **existing explicit environment scopes and existing credentials are not rewritten**. Reducing a default does not revoke previous consent. Inspect actual permissions before client onboarding and obtain fresh minimal consent where required.

## Four independent data probes

Run from the authorized backend environment after onboarding. They use the encrypted vault; no token arguments or token output. Every command requires the client slug, exact connection row, expected account and explicit complete dates. Store customer identifiers only in private operational notes, not in this public repository.

```bash
python manage.py probe_audit --platform shopify --org-slug <client> --connection-id <shop-connection> --expected-account <shop.myshopify.com> --start-date YYYY-MM-DD --end-date YYYY-MM-DD
python manage.py probe_audit --platform meta-ads --org-slug <client> --connection-id <meta-connection> --expected-account act_<ad-account> --business-id <business> --start-date YYYY-MM-DD --end-date YYYY-MM-DD
python manage.py probe_audit --platform google-ads --org-slug <client> --connection-id <ads-connection> --expected-account <10-digit-customer> --start-date YYYY-MM-DD --end-date YYYY-MM-DD
python manage.py probe_audit --platform ga4 --org-slug <client> --connection-id <google-connection> --expected-account properties/<property> --property-id <property> --start-date YYYY-MM-DD --end-date YYYY-MM-DD
```

These are sample probes (50 Shopify orders, at most 100 Ads/Meta/GA4 report rows), not complete extracts. They expose only a sanitized result summary, counts, account, dates, currency, timezone and limitations. No connected status is upgraded by the command. Missing/empty required data remains explicitly incomplete. For a full audit, paginate the reports separately, reconcile totals, account-local dates and attribution, and document absent conversion events and currencies rather than treating missing data as zero.

Shopify refunds are attached to orders **created in the requested period** and can include refunds made later. This proves refund-field access but is not a refund-date ledger or proof that a nonempty refund record exists. A full financial reconciliation must include refunds for older orders and the appropriate date basis. GA4 events provide a separate view of the funnel; absent events are not fabricated. Meta uses ad-set attribution and conversion-date action reporting; Google uses configured conversion actions. Compare their attribution definitions before combining results.

## Local validation

Use Python 3.10+ and an isolated local database. `python manage.py test --noinput`, `python manage.py makemigrations --check --dry-run`, and `npm ci --ignore-scripts && npm run build` in the frontend. Tests exercise security boundaries and synthetic provider responses. Passing them never demonstrates real customer API access.
