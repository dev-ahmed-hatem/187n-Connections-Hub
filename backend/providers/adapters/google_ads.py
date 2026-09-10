"""Real Google Ads adapter (REST + GAQL, no SDK).

Standard OAuth2 offline flow. API access is managed by the OAuth Cloud
project; manager routing uses login-customer-id when required.
"""

from datetime import date, timedelta
from urllib.parse import quote, urlencode

from .real_base import RealAdapter

AUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'
REVOKE_ENDPOINT = 'https://oauth2.googleapis.com/revoke'
USERINFO_ENDPOINT = 'https://www.googleapis.com/oauth2/v3/userinfo'
API_ROOT = 'https://googleads.googleapis.com'
ANALYTICS_ADMIN = 'https://analyticsadmin.googleapis.com/v1beta'
ANALYTICS_DATA = 'https://analyticsdata.googleapis.com/v1beta'
SEARCH_CONSOLE = 'https://searchconsole.googleapis.com/webmasters/v3'
CONTENT_API = 'https://shoppingcontent.googleapis.com/content/v2.1'

STATS_GAQL = (
    'SELECT metrics.cost_micros, metrics.clicks, metrics.impressions, '
    'metrics.conversions FROM customer WHERE segments.date DURING LAST_30_DAYS'
)


class GoogleAdsAdapter(RealAdapter):
    # API access is managed by the OAuth Cloud project (September 2026).
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
        version = self.config.get('api_version', 'v24')
        try:
            data = self._get(
                f'{API_ROOT}/{version}/customers:listAccessibleCustomers',
                headers={'Authorization': f'Bearer {access_token}'},
            )
        except Exception:
            # GA4 consent can remain usable when Ads access is unavailable.
            info = self._userinfo(access_token)
            return [{
                'external_account_id': info.get('sub', ''),
                'display_name': info.get('email') or 'Google account',
                'meta': {'account_name': info.get('email') or 'Google account',
                         'pending_ads_access': True},
            }]
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
        """Route data reads to the requested Google API."""
        if resource in ('audit', 'audit-ga4'):
            from .audit import google
            return google(self, access_token, params or {}, meta or {}, analytics=resource == 'audit-ga4')
        meta = meta or {}
        params = params or {}
        resource = (resource or 'stats').lower()
        if resource in ('stats', 'ads', 'google-ads'):
            return self._ads(access_token, meta)
        if resource in ('analytics', 'ga4'):
            return self._analytics(access_token, params)
        if resource in ('search-console', 'searchconsole', 'gsc'):
            return self._search_console(access_token, params)
        if resource == 'merchant':
            return self._merchant(access_token)
        return {'provider': 'google-ads', 'resource': resource,
                'account': self._userinfo(access_token), 'mock': False}

    def _ads(self, access_token, meta):
        from .audit import identifier
        customer_id = identifier((meta.get('external_account_id') or '').replace('-', ''), r'[0-9]{10}')
        login_customer_id = (meta.get('login_customer_id')
                             or self.config.get('login_customer_id') or customer_id)
        version = self.config.get('api_version', 'v24')
        headers = {
            'Authorization': f'Bearer {access_token}',
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
            'resource': 'stats',
            'account_id': customer_id,
            'metrics': {
                'spend': round(cost / 1_000_000, 2),
                'clicks': int(clicks),
                'impressions': int(impressions),
                'conversions': round(conversions, 2),
            },
            'mock': False,
        }

    def _analytics(self, access_token, params):
        h = {'Authorization': f'Bearer {access_token}'}
        pid = params.get('property_id')
        if not pid:
            data = self._get(f'{ANALYTICS_ADMIN}/accountSummaries', headers=h)
            props = []
            for acc in data.get('accountSummaries', []):
                for p in acc.get('propertySummaries', []):
                    props.append({'property': p.get('property'),
                                  'display_name': p.get('displayName')})
            return {'provider': 'google-ads', 'resource': 'analytics',
                    'properties': props, 'mock': False}
        prop = pid if str(pid).startswith('properties/') else f'properties/{pid}'
        body = {'dateRanges': [{'startDate': '28daysAgo', 'endDate': 'today'}],
                'metrics': [{'name': 'sessions'}, {'name': 'activeUsers'},
                            {'name': 'screenPageViews'}]}
        rep = self._post(f'{ANALYTICS_DATA}/{prop}:runReport', headers=h, json=body)
        vals = (rep.get('rows') or [{}])[0].get('metricValues', []) if rep.get('rows') else []
        names = ['sessions', 'activeUsers', 'screenPageViews']
        metrics = {n: (vals[i].get('value') if i < len(vals) else None)
                   for i, n in enumerate(names)}
        return {'provider': 'google-ads', 'resource': 'analytics',
                'account_id': prop, 'metrics': metrics, 'mock': False}

    def _search_console(self, access_token, params):
        h = {'Authorization': f'Bearer {access_token}'}
        site = params.get('site_url')
        if not site:
            data = self._get(f'{SEARCH_CONSOLE}/sites', headers=h)
            return {'provider': 'google-ads', 'resource': 'search-console',
                    'sites': [s.get('siteUrl') for s in data.get('siteEntry', [])],
                    'mock': False}
        end = date.today()
        start = end - timedelta(days=28)
        rep = self._post(
            f'{SEARCH_CONSOLE}/sites/{quote(site, safe="")}/searchAnalytics/query',
            headers=h, json={'startDate': start.isoformat(), 'endDate': end.isoformat(),
                             'dimensions': []},
        )
        row = (rep.get('rows') or [{}])[0]
        return {'provider': 'google-ads', 'resource': 'search-console', 'account_id': site,
                'metrics': {'clicks': row.get('clicks', 0), 'impressions': row.get('impressions', 0),
                            'ctr': row.get('ctr', 0), 'position': row.get('position', 0)},
                'mock': False}

    def _merchant(self, access_token):
        info = self._get(f'{CONTENT_API}/accounts/authinfo',
                         headers={'Authorization': f'Bearer {access_token}'})
        ids = [a.get('merchantId') or a.get('aggregatorId')
               for a in info.get('accountIdentifiers', [])]
        return {'provider': 'google-ads', 'resource': 'merchant',
                'merchant_accounts': ids, 'mock': False}

    def revoke(self, refresh_token):
        try:
            self._post(f'{REVOKE_ENDPOINT}?{urlencode({"token": refresh_token})}')
        except Exception:
            pass
        return None

    def _userinfo(self, access_token):
        return self._get(USERINFO_ENDPOINT,
                         headers={'Authorization': f'Bearer {access_token}'})
