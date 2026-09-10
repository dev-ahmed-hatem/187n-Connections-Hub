"""Real Meta (Facebook) Ads adapter.

Meta has no classic refresh token: a short-lived token is exchanged for a
long-lived one (~60 days), which is later re-exchanged to extend it. We store
the long-lived token in both access and refresh slots so the vault's standard
refresh path re-exchanges it near expiry.
"""

from urllib.parse import urlencode

from .real_base import RealAdapter


class MetaAdsAdapter(RealAdapter):
    required_config = ('client_id', 'client_secret')

    @property
    def graph(self):
        return f'https://graph.facebook.com/{self.config.get("api_version", "v21.0")}'

    def authorize_url(self, state, redirect_uri, params=None):
        q = {
            'client_id': self.config['client_id'],
            'redirect_uri': redirect_uri,
            'scope': ','.join(self.config.get('scopes', ['ads_read'])),
            'response_type': 'code',
            'state': state,
        }
        # Optional Facebook Login for Business configuration.
        if self.config.get('config_id'):
            q['config_id'] = self.config['config_id']
        version = self.config.get('api_version', 'v21.0')
        return f'https://www.facebook.com/{version}/dialog/oauth?{urlencode(q)}'

    def exchange_code(self, code, state, params=None):
        redirect_uri = (params or {}).get('redirect_uri', '')
        short = self._get(f'{self.graph}/oauth/access_token', params={
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret'],
            'redirect_uri': redirect_uri,
            'code': code,
        })
        long = self._get(f'{self.graph}/oauth/access_token', params={
            'grant_type': 'fb_exchange_token',
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret'],
            'fb_exchange_token': short['access_token'],
        })
        token = long['access_token']
        expires_in = int(long.get('expires_in', 60 * 24 * 3600))

        ad_account_id, account_name = self._discover_account(token)
        return {
            'refresh_token': token,  # re-exchanged on refresh
            'access_token': token,
            'expires_in': expires_in,
            'external_account_id': ad_account_id,
            'meta': {'ad_account_id': ad_account_id, 'account_name': account_name},
        }

    def list_accounts(self, access_token, meta):
        data = self._get(f'{self.graph}/me/adaccounts', params={
            'fields': 'account_id,name', 'access_token': access_token})
        out = []
        for a in data.get('data', []):
            aid = f'act_{a["account_id"]}'
            out.append({'external_account_id': aid,
                        'display_name': a.get('name', 'Meta Ads'),
                        'meta': {'ad_account_id': aid, 'account_name': a.get('name', 'Meta Ads')}})
        return out or [{'external_account_id': '', 'display_name': 'Meta Ads', 'meta': {}}]

    def refresh(self, refresh_token):
        long = self._get(f'{self.graph}/oauth/access_token', params={
            'grant_type': 'fb_exchange_token',
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret'],
            'fb_exchange_token': refresh_token,
        })
        return {
            'access_token': long['access_token'],
            'expires_in': int(long.get('expires_in', 60 * 24 * 3600)),
        }

    def fetch_data(self, access_token, resource, params, meta):
        if resource == 'audit':
            from .audit import meta_ads
            return meta_ads(self, access_token, params or {}, meta or {})
        ad_account_id = (meta or {}).get('ad_account_id') or (meta or {}).get('external_account_id')
        insights = self._get(f'{self.graph}/{ad_account_id}/insights', params={
            'fields': 'spend,impressions,clicks,reach',
            'date_preset': 'last_30d',
            'access_token': access_token,
        })
        row = (insights.get('data') or [{}])[0]
        return {
            'provider': 'meta-ads',
            'resource': resource or 'stats',
            'account_id': ad_account_id,
            'metrics': {
                'spend': float(row.get('spend', 0) or 0),
                'impressions': int(row.get('impressions', 0) or 0),
                'clicks': int(row.get('clicks', 0) or 0),
                'reach': int(row.get('reach', 0) or 0),
            },
            'mock': False,
        }

    def revoke(self, refresh_token):
        return None

    def _discover_account(self, token):
        data = self._get(f'{self.graph}/me/adaccounts', params={
            'fields': 'account_id,name',
            'access_token': token,
        })
        accounts = data.get('data') or []
        if not accounts:
            return '', 'Meta Ads'
        first = accounts[0]
        return f'act_{first["account_id"]}', first.get('name', 'Meta Ads')
