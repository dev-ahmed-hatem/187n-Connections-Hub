"""Real Shopify adapter.

Shopify OAuth is per-shop; the offline access token does not expire. The shop
domain is the account identity and is captured at start time (OAuthState.meta).
"""

import hashlib
import hmac as hmaclib
import re
from urllib.parse import urlencode

from .real_base import NON_EXPIRING_SECONDS, RealAdapter

SHOP_RE = re.compile(r'^[a-z0-9][a-z0-9-]*\.myshopify\.com$')


def _normalize_shop(shop: str) -> str:
    shop = (shop or '').strip().lower().replace('https://', '').replace('http://', '').rstrip('/')
    if shop and not shop.endswith('.myshopify.com'):
        shop = f'{shop}.myshopify.com'
    return shop


class ShopifyAdapter(RealAdapter):
    required_config = ('client_id', 'client_secret')

    def verify_callback(self, query_params):
        """Verify Shopify's HMAC signature on the OAuth callback + shop domain."""
        params = dict(query_params or {})
        provided = params.pop('hmac', None)
        params.pop('signature', None)
        if not provided:
            raise ValueError('Missing HMAC on Shopify callback.')
        message = '&'.join(f'{k}={params[k]}' for k in sorted(params))
        digest = hmaclib.new(
            self.config['client_secret'].encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        if not hmaclib.compare_digest(digest, provided):
            raise ValueError('Shopify HMAC verification failed.')
        if not SHOP_RE.match(_normalize_shop(params.get('shop', ''))):
            raise ValueError('Invalid Shopify shop domain.')

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
        version = self.config.get('api_version', '2025-01')
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
