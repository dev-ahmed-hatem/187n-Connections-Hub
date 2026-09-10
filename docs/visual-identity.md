# 187N Connections Hub visual identity

Reference: `187N-ai/187n-site`, commit `dff11be0c9fcd3f73cecf83daf31d6a03fc27ece` (inspected 10 September 2026).

The Hub uses the flagship's warm charcoal, warm paper and clay-orange palette, original infinity mark, and self-hosted Space Grotesk, Bebas Neue and Drowner fonts. Source references are `src/styles/design.css`, `src/components/mission-control/mission-control.css`, `public/fonts/`, `public/logos/187n-infinity.png` and `public/favicon-32.png`. The site's Next.js application, backend and animated marketing demos are not dependencies of the Hub.

Implementation: `frontend/src/theme/hubTheme.ts` supplies Ant Design tokens; `frontend/src/styles/hub.css` supplies the brand and responsive layouts. Login, app navigation, dashboard, connection cards, forms, tables, notifications and dialogs use this shared layer. Dark mode is the default for new visits; existing light/dark preferences are respected. The login's paper panel remains light in either mode. Mobile navigation uses a dismissible drawer; reduced-motion preferences are respected. The old font packages were removed.

Authorization and real audit verification remain separate. The design contains no invented account metrics or sample connections: those are supplied by the existing authenticated API. Local browser checks use intercepted synthetic responses, never production accounts.

Validation covers the login, required fields and login submission, admin dashboard, light/dark switching, mobile menu navigation and dismissal, clients/users view, client connection cards, connection-test feedback, and Shopify modal opening/cancellation. Connection layouts were checked at 320, 390, 768, 1024 and 1440 pixels without horizontal page overflow. Browser checks verify presentation and frontend behavior, not live OAuth or customer-data access.

This styling is part of the audit preparation PR. Production deployment still requires explicit owner approval and the operational rollout steps in `docs/audit-readiness.md`.
