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

    @abc.abstractmethod
    def refresh(self, refresh_token: str) -> dict:
        """Return a fresh access token: {'access_token': str, 'expires_in': int}."""

    @abc.abstractmethod
    def fetch_data(self, access_token: str, resource: str, params: dict, meta: dict) -> dict:
        """Return provider data for a resource (e.g. 'stats')."""

    @abc.abstractmethod
    def revoke(self, refresh_token: str) -> None:
        """Revoke a grant (best-effort)."""
