import abc


class ProviderAdapter(abc.ABC):
    """Interface every provider integration implements.

    The rest of the hub (connections, access) only ever talks to this
    interface, so swapping the MockAdapter for a real Google/Meta/Shopify
    adapter requires no caller changes — only a new subclass + credentials.
    """

    def __init__(self, provider):
        self.provider = provider

    @abc.abstractmethod
    def authorize_url(self, state: str, redirect_uri: str, params: dict | None = None) -> str:
        """Return the URL to send the user to for consent.

        `params` carries provider-specific start inputs (e.g. Shopify `shop`).
        """

    @abc.abstractmethod
    def exchange_code(self, code: str, state: str, params: dict | None = None) -> dict:
        """Exchange a consent code for tokens.

        `params` is whatever was captured at start time (stored on OAuthState.meta).

        Returns: {
            'refresh_token': str,
            'access_token': str,
            'expires_in': int,          # seconds
            'external_account_id': str,
            'meta': dict,               # provider-specific extras
        }
        """

    def list_accounts(self, access_token: str, meta: dict) -> list:
        """Return the accounts this grant can access.

        Each item: {external_account_id, display_name, meta}. Default is a single
        account derived from `meta` (providers with one account per grant, e.g.
        Shopify). Multi-account providers override this.
        """
        meta = meta or {}
        return [{
            'external_account_id': meta.get('external_account_id', ''),
            'display_name': meta.get('account_name', self.provider.name),
            'meta': meta,
        }]

    @abc.abstractmethod
    def refresh(self, refresh_token: str) -> dict:
        """Return a fresh access token: {'access_token': str, 'expires_in': int}."""

    @abc.abstractmethod
    def fetch_data(self, access_token: str, resource: str, params: dict, meta: dict) -> dict:
        """Return provider data for a resource (e.g. 'stats')."""

    @abc.abstractmethod
    def revoke(self, refresh_token: str) -> None:
        """Revoke a grant (best-effort)."""

    def verify_callback(self, query_params: dict) -> None:
        """Validate the raw OAuth callback params before exchange.

        Default: no-op. Providers that sign their callbacks (e.g. Shopify HMAC)
        override this and raise on tampering.
        """
        return None
