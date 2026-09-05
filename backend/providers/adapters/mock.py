"""A fully local, deterministic stand-in for a real OAuth provider.

Everything it returns is derived from a hash of (provider slug, state) so the
flow is reproducible across runs and tests — no randomness, no network.
"""

import hashlib
from urllib.parse import quote

from django.conf import settings
from django.urls import reverse

from .base import ProviderAdapter


def _digest(*parts) -> str:
    return hashlib.sha256(':'.join(str(p) for p in parts).encode()).hexdigest()


class MockAdapter(ProviderAdapter):
    def authorize_url(self, state: str, redirect_uri: str, params: dict | None = None) -> str:
        base = settings.BACKEND_BASE_URL.rstrip('/') + reverse('providers:mock_authorize')
        return (
            f'{base}?provider={self.provider.slug}'
            f'&state={quote(state)}&redirect_uri={quote(redirect_uri)}'
        )

    def make_code(self, state: str) -> str:
        return f'mockcode-{_digest(self.provider.slug, state)[:24]}'

    def external_account_id(self, state: str) -> str:
        # A stable pseudo "customer id": 10 digits derived from the hash.
        n = int(_digest('acct', self.provider.slug, state)[:12], 16) % (10 ** 10)
        return str(n).zfill(10)

    def exchange_code(self, code: str, state: str, params: dict | None = None) -> dict:
        d = _digest(self.provider.slug, state)
        meta = {'account_name': f'{self.provider.name} — Demo Account'}
        if self.provider.slug == 'google-ads':
            meta['login_customer_id'] = self.external_account_id(state)
        return {
            'refresh_token': f'mock-refresh-{d[:32]}',
            'access_token': f'mock-access-{d[32:64]}',
            'expires_in': settings.ACCESS_TOKEN_TTL_SECONDS,
            'external_account_id': self.external_account_id(state),
            'meta': meta,
        }

    def refresh(self, refresh_token: str) -> dict:
        d = _digest('refresh', refresh_token)
        return {
            'access_token': f'mock-access-{d[:32]}',
            'expires_in': settings.ACCESS_TOKEN_TTL_SECONDS,
        }

    def fetch_data(self, access_token: str, resource: str, params: dict, meta: dict) -> dict:
        seed = _digest(self.provider.slug, resource, access_token[:8])
        base = int(seed[:6], 16)

        def num(offset, mod, scale=1):
            return round((int(seed[offset:offset + 6], 16) % mod) * scale, 2)

        if self.provider.slug == 'google-ads':
            metrics = {
                'spend': num(0, 900000, 0.01),
                'clicks': base % 20000,
                'impressions': base % 500000,
                'conversions': base % 800,
            }
        elif self.provider.slug == 'meta-ads':
            metrics = {
                'spend': num(6, 700000, 0.01),
                'reach': base % 300000,
                'impressions': base % 900000,
                'link_clicks': base % 15000,
            }
        elif self.provider.slug == 'shopify':
            metrics = {
                'orders': base % 5000,
                'revenue': num(12, 2000000, 0.01),
                'sessions': base % 120000,
                'conversion_rate': num(18, 900, 0.01),
            }
        else:
            metrics = {'value': base % 10000}

        return {
            'provider': self.provider.slug,
            'resource': resource or 'stats',
            'range': params.get('range', 'last_30d') if params else 'last_30d',
            'account_id': meta.get('external_account_id') if meta else None,
            'metrics': metrics,
            'mock': True,
        }

    def revoke(self, refresh_token: str) -> None:
        return None
