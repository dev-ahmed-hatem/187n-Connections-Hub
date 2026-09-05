"""Real Google Ads adapter (REST + GAQL, no SDK).

Standard OAuth2 offline flow (access + refresh token). API calls carry the
developer token and login-customer-id (MCC) headers.
"""

from urllib.parse import urlencode

from .real_base import RealAdapter

AUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'
REVOKE_ENDPOINT = 'https://oauth2.googleapis.com/revoke'
USERINFO_ENDPOINT = 'https://www.googleapis.com/oauth2/v3/userinfo'
API_ROOT = 'https://googleads.googleapis.com'

STATS_GAQL = (
    'SELECT metrics.cost_micros, metrics.clicks, metrics.impressions, '
    'metrics.conversions FROM customer WHERE segments.date DURING LAST_30_DAYS'
)


class GoogleAdsAdapter(RealAdapter):
    # developer_token is only needed for Ads API calls (accounts/data), not for
    # the OAuth handshake — so it's not required just to connect.
    required_config = ('client_id', 'client_secret')

    def authorize_url(self, state, redirect_uri, params=None):
        query = urlencode({
            'client_id': self.config['client_id'],
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.config.get('scopes', [
                'https://www.googleapis.com/auth/adwords'])),
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state,
        })
        return f'{AUTH_ENDPOINT}?{query}'

    def exchange_code(self, code, state, params=None):
        redirect_uri = (params or {}).get('redirect_uri', '')
        tok = self._post(TOKEN_ENDPOINT, data={
            'code': code,
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret'],
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        })
        customer_id = self.config.get('login_customer_id') or ''
        if not customer_id and self.config.get('developer_token'):
            customer_id = self._first_customer(tok['access_token'])
        return {
            'refresh_token': tok.get('refresh_token', ''),
            'access_token': tok['access_token'],
            'expires_in': int(tok.get('expires_in', 3600)),
            'external_account_id': customer_id,
            'meta': {
                'login_customer_id': self.config.get('login_customer_id') or customer_id,
                'account_name': f'Google Ads {customer_id}' if customer_id else 'Google Ads',
            },
        }

    def list_accounts(self, access_token, meta):
        # No developer token yet → OAuth-only: identify the connection by the
        # user's Google email so the connect flow is fully testable.
        if not self.config.get('developer_token'):
            info = {}
            try:
                info = self._userinfo(access_token)
            except Exception:
                pass
            email = info.get('email') or 'Google account'
            return [{
                'external_account_id': info.get('sub', '') or (meta or {}).get('external_account_id', ''),
                'display_name': email,
                'meta': {'account_name': email, 'email': email, 'pending_developer_token': True},
            }]
        version = self.config.get('api_version', 'v21')
        data = self._get(
            f'{API_ROOT}/{version}/customers:listAccessibleCustomers',
            headers={'Authorization': f'Bearer {access_token}',
                     'developer-token': self.config['developer_token']},
        )
        out = []
        for name in data.get('resourceNames', []):
            cid = name.split('/')[-1]
            out.append({
                'external_account_id': cid,
                'display_name': f'Google Ads {cid}',
                'meta': {'login_customer_id': self.config.get('login_customer_id') or cid,
                         'account_name': f'Google Ads {cid}'},
            })
        if out:
            return out
        cid = self.config.get('login_customer_id', '')
        return [{'external_account_id': cid, 'display_name': f'Google Ads {cid}',
                 'meta': {'login_customer_id': cid, 'account_name': f'Google Ads {cid}'}}]

    def refresh(self, refresh_token):
        tok = self._post(TOKEN_ENDPOINT, data={
            'refresh_token': refresh_token,
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret'],
            'grant_type': 'refresh_token',
        })
        return {'access_token': tok['access_token'], 'expires_in': int(tok.get('expires_in', 3600))}

    def fetch_data(self, access_token, resource, params, meta):
        meta = meta or {}
        if not self.config.get('developer_token'):
            return {
                'provider': 'google-ads',
                'resource': resource or 'stats',
                'account_id': meta.get('external_account_id'),
                'metrics': {},
                'note': 'Connected, but a Google Ads developer token (from a Manager '
                        'account) is required to pull data.',
                'mock': False,
            }
        customer_id = (meta.get('external_account_id') or '').replace('-', '')
        login_customer_id = (meta.get('login_customer_id')
                             or self.config.get('login_customer_id') or customer_id)
        version = self.config.get('api_version', 'v21')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'developer-token': self.config['developer_token'],
        }
        if login_customer_id:
            headers['login-customer-id'] = str(login_customer_id).replace('-', '')

        result = self._post(
            f'{API_ROOT}/{version}/customers/{customer_id}/googleAds:search',
            headers=headers, json={'query': STATS_GAQL},
        )
        cost = clicks = impressions = conversions = 0.0
        for row in result.get('results', []):
            m = row.get('metrics', {})
            cost += int(m.get('costMicros', 0))
            clicks += int(m.get('clicks', 0))
            impressions += int(m.get('impressions', 0))
            conversions += float(m.get('conversions', 0))
        return {
            'provider': 'google-ads',
            'resource': resource or 'stats',
            'account_id': customer_id,
            'metrics': {
                'spend': round(cost / 1_000_000, 2),
                'clicks': int(clicks),
                'impressions': int(impressions),
                'conversions': round(conversions, 2),
            },
            'mock': False,
        }

    def revoke(self, refresh_token):
        try:
            self._post(f'{REVOKE_ENDPOINT}?{urlencode({"token": refresh_token})}')
        except Exception:
            pass
        return None

    def _userinfo(self, access_token):
        return self._get(USERINFO_ENDPOINT,
                         headers={'Authorization': f'Bearer {access_token}'})

    def _first_customer(self, access_token):
        version = self.config.get('api_version', 'v21')
        data = self._get(
            f'{API_ROOT}/{version}/customers:listAccessibleCustomers',
            headers={
                'Authorization': f'Bearer {access_token}',
                'developer-token': self.config['developer_token'],
            },
        )
        names = data.get('resourceNames', [])
        return names[0].split('/')[-1] if names else ''
