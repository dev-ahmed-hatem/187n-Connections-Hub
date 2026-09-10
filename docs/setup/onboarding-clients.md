> September 2026 audit update: consult [the audit rollout guide](../audit-readiness.md) for minimal permissions, production security and current Google Cloud API access. Legacy examples below are not the audit onboarding policy.

# Onboarding real clients before your apps are verified

You can let **real clients** authorize their Meta and Shopify (and Google) accounts **without**
full app verification / App Store review — using each platform's "pre-verification" mechanism.
These paths are fine for a **handful of pilot clients**; scaling to many/any client eventually
needs the real review (see the ceilings below).

> There is **no single "testers list"** across platforms. Google and Meta have per-person
> allowlists; Shopify uses per-store install links instead.

---

## Google — Test users (Testing mode)

- **APIs & Services → OAuth consent screen → Test users → Add users** — add each client's Google
  account (up to **100**).
- They authorize despite the **"Google hasn't verified this app"** screen
  (Advanced → *proceed*).
- ⚠️ **In Testing, refresh tokens expire after 7 days** — connections keep breaking. Publish the
  consent screen to **Production** to remove that (sensitive/restricted scopes like Drive then
  require Google verification for External production, but basic OAuth keeps working).

**Ceiling:** 100 test users; durable tokens + sensitive scopes at scale → **Google app
verification**.

---

## Meta — add clients as **Testers** (App Roles)

In **Development** mode, anyone holding an **app role** can authorize and you reach *their*
assets with the advanced scopes — no App Review.

1. App → **App Roles → Roles → Add People** → add the client as **Tester** (or Developer).
2. The client **accepts** the invite (needs a Facebook account + a notification click).
3. They authorize via the hub; you now get their ads / Pages / Instagram / catalog / leads data.

**Requirements & friction:**
- Client must accept the invite and be an **admin on the ad account / Page** you want to reach.
- Manual, one client at a time; it's *development* mode — not meant for many live clients.

**Ceiling:** many/any client, or production breadth on other businesses' assets →
**App Review + Business Verification**. (Start Business Verification early — it takes days.)

---

## Shopify — **Custom distribution** per store (no testers list)

Shopify's review (App Store listing) is separate and **skippable for specific stores**.

1. App → **Distribution → Custom distribution** → enter the client's exact
   `their-store.myshopify.com`.
2. Shopify generates a **one-time install link** for that store.
3. The client opens it, approves the scopes, done — **on a live store, no review**.

**Requirements & friction:**
- **One store per custom app, and the choice is permanent.** For N clients → N custom apps
  (each with its own `SHOPIFY_API_KEY/SECRET`), *or* have the client create a custom app inside
  their own store admin and hand you its Admin API token (bypasses OAuth; still works for data).
- Orders/Customers scopes still need **Protected customer data access** configured (instant on
  the store).

**Ceiling:** any merchant self-serving from the App Store → **public distribution + App Store
review** (~weeks, plus mandatory GDPR webhooks, listing, privacy policy).

---

## At a glance

| Provider | Pre-verification path | Client friction | Ceiling before real review |
|---|---|---|---|
| **Google** | Test users (Testing mode) | Unverified warning; **7-day** refresh tokens | 100 users; prod/sensitive scopes → verification |
| **Meta** | Add as **Tester** (App Roles) | Accept invite; needs FB account | Dev-mode only; scale → App Review + Business Verification |
| **Shopify** | **Custom distribution** per store | One click | 1 store per custom app; any-merchant → App Store review |

## Recommended play for pilot clients now

- **Google:** add as **Test users**, and **publish to Production** early to kill the 7-day token
  expiry.
- **Meta:** add each client as a **Tester**; kick off **Business Verification** in parallel if
  you'll scale.
- **Shopify:** use **Custom distribution** per client store — cleanest, no review, live stores.

See also: [google.md](google.md) · [meta.md](meta.md) · [shopify.md](shopify.md) ·
[../providers.md](../providers.md).
