"""Real Shopify adapter.

Shopify OAuth is per-shop; the offline access token does not expire. The shop
domain is the account identity and is captured at start time (OAuthState.meta).
"""

from urllib.parse import urlencode

from .real_base import NON_EXPIRING_SECONDS, RealAdapter


def _normalize_shop(shop: str) -> str:
    shop = (shop or '').strip().replace('https://', '').replace('http://', '').rstrip('/')
    if shop and not shop.endswith('.myshopify.com'):
        shop = f'{shop}.myshopify.com'
    return shop


class ShopifyAdapter(RealAdapter):
    required_config = ('client_id', 'client_secret')

    def authorize_url(self, state, redirect_uri, params=None):
        shop = _normalize_shop((params or {}).get('shop', ''))
        if not shop:
            raise ValueError('Shopify requires a shop domain.')
        query = urlencode({
            'client_id': self.config['client_id'],
            'scope': ','.join(self.config.get('scopes', [])),
            'redirect_uri': redirect_uri,
            'state': state,
        })
        return f'https://{shop}/admin/oauth/authorize?{query}'

    def exchange_code(self, code, state, params=None):
        shop = _normalize_shop((params or {}).get('shop', ''))
        data = self._post(
            f'https://{shop}/admin/oauth/access_token',
            json={
                'client_id': self.config['client_id'],
                'client_secret': self.config['client_secret'],
                'code': code,
            },
        )
        return {
            'refresh_token': '',  # offline token never expires
            'access_token': data['access_token'],
            'expires_in': NON_EXPIRING_SECONDS,
            'external_account_id': shop,
            'meta': {'shop': shop, 'account_name': shop, 'scope': data.get('scope', '')},
        }

    def list_accounts(self, access_token, meta):
        shop = (meta or {}).get('shop') or (meta or {}).get('external_account_id')
        return [{'external_account_id': shop, 'display_name': shop,
                 'meta': {'shop': shop, 'account_name': shop}}]

    def refresh(self, refresh_token):
        # Offline tokens don't expire; nothing to do.
        return {'access_token': refresh_token, 'expires_in': NON_EXPIRING_SECONDS}

    def fetch_data(self, access_token, resource, params, meta):
        shop = (meta or {}).get('shop') or (meta or {}).get('external_account_id')
        version = self.config.get('api_version', '2024-10')
        base = f'https://{shop}/admin/api/{version}'
        headers = {'X-Shopify-Access-Token': access_token}
        orders = self._get(f'{base}/orders/count.json', headers=headers)
        products = self._get(f'{base}/products/count.json', headers=headers)
        shop_info = self._get(f'{base}/shop.json', headers=headers).get('shop', {})
        return {
            'provider': 'shopify',
            'resource': resource or 'stats',
            'account_id': shop,
            'metrics': {
                'orders': orders.get('count', 0),
                'products': products.get('count', 0),
                'shop_name': shop_info.get('name'),
                'currency': shop_info.get('currency'),
            },
            'mock': False,
        }

    def revoke(self, refresh_token):
        # Shopify apps are uninstalled by the merchant; no token revoke endpoint.
        return None
