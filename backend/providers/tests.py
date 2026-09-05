from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from providers.adapters.google_ads import GoogleAdsAdapter
from providers.adapters.meta_ads import MetaAdsAdapter
from providers.adapters.shopify import ShopifyAdapter
from providers.models import Provider

TEST_CONFIG = {
    'shopify': {'client_id': 'sk', 'client_secret': 'ss',
                'api_version': '2024-10', 'scopes': ['read_orders']},
    'meta-ads': {'client_id': 'mid', 'client_secret': 'msec',
                 'api_version': 'v21.0', 'scopes': ['ads_read']},
    'google-ads': {'client_id': 'gid', 'client_secret': 'gsec',
                   'developer_token': 'devtok', 'login_customer_id': '1234567890',
                   'api_version': 'v18', 'scopes': ['https://www.googleapis.com/auth/adwords']},
}

REDIRECT = 'http://localhost:8000/api/connections/callback'


def resp(json_data):
    m = MagicMock()
    m.json.return_value = json_data
    m.raise_for_status.return_value = None
    return m


@override_settings(PROVIDER_CONFIG=TEST_CONFIG)
class ShopifyAdapterTests(SimpleTestCase):
    def setUp(self):
        self.adapter = ShopifyAdapter(Provider(slug='shopify', name='Shopify', is_mock=False))

    def test_authorize_url(self):
        url = self.adapter.authorize_url('st8', REDIRECT, {'shop': 'demo-store'})
        self.assertIn('demo-store.myshopify.com/admin/oauth/authorize', url)
        self.assertIn('client_id=sk', url)
        self.assertIn('state=st8', url)

    @patch('providers.adapters.real_base.requests')
    def test_exchange_code(self, req):
        req.post.return_value = resp({'access_token': 'shpat_x', 'scope': 'read_orders'})
        out = self.adapter.exchange_code('code', 'st8', {'shop': 'demo-store'})
        self.assertEqual(out['access_token'], 'shpat_x')
        self.assertEqual(out['refresh_token'], '')  # non-expiring, no refresh
        self.assertEqual(out['external_account_id'], 'demo-store.myshopify.com')

    @patch('providers.adapters.real_base.requests')
    def test_fetch_data(self, req):
        req.get.side_effect = [
            resp({'count': 42}), resp({'count': 7}),
            resp({'shop': {'name': 'Demo', 'currency': 'USD'}}),
        ]
        data = self.adapter.fetch_data('shpat_x', 'stats', {},
                                       {'shop': 'demo-store.myshopify.com'})
        self.assertEqual(data['metrics']['orders'], 42)
        self.assertEqual(data['metrics']['products'], 7)
        self.assertFalse(data['mock'])


@override_settings(PROVIDER_CONFIG=TEST_CONFIG)
class MetaAdsAdapterTests(SimpleTestCase):
    def setUp(self):
        self.adapter = MetaAdsAdapter(Provider(slug='meta-ads', name='Meta Ads', is_mock=False))

    def test_authorize_url(self):
        url = self.adapter.authorize_url('mst', REDIRECT)
        self.assertIn('facebook.com/v21.0/dialog/oauth', url)
        self.assertIn('client_id=mid', url)
        self.assertIn('scope=ads_read', url)

    @patch('providers.adapters.real_base.requests')
    def test_exchange_code_long_lived_and_account(self, req):
        req.get.side_effect = [
            resp({'access_token': 'short'}),
            resp({'access_token': 'long', 'expires_in': 5184000}),
            resp({'data': [{'account_id': '999', 'name': 'Acme Ads'}]}),
        ]
        out = self.adapter.exchange_code('code', 'mst', {'redirect_uri': REDIRECT})
        self.assertEqual(out['access_token'], 'long')
        self.assertEqual(out['refresh_token'], 'long')  # re-exchanged on refresh
        self.assertEqual(out['external_account_id'], 'act_999')

    @patch('providers.adapters.real_base.requests')
    def test_fetch_data(self, req):
        req.get.return_value = resp({'data': [{'spend': '12.50', 'impressions': '1000',
                                               'clicks': '25', 'reach': '800'}]})
        data = self.adapter.fetch_data('long', 'stats', {}, {'ad_account_id': 'act_999'})
        self.assertEqual(data['metrics']['spend'], 12.5)
        self.assertEqual(data['metrics']['clicks'], 25)


@override_settings(PROVIDER_CONFIG=TEST_CONFIG)
class GoogleAdsAdapterTests(SimpleTestCase):
    def setUp(self):
        self.adapter = GoogleAdsAdapter(
            Provider(slug='google-ads', name='Google Ads', is_mock=False))

    def test_authorize_url(self):
        url = self.adapter.authorize_url('gst', REDIRECT)
        self.assertIn('accounts.google.com/o/oauth2/v2/auth', url)
        self.assertIn('access_type=offline', url)
        self.assertIn('prompt=consent', url)

    @patch('providers.adapters.real_base.requests')
    def test_exchange_code(self, req):
        req.post.return_value = resp({'access_token': 'ya29', 'refresh_token': '1//r',
                                      'expires_in': 3600})
        out = self.adapter.exchange_code('code', 'gst', {'redirect_uri': REDIRECT})
        self.assertEqual(out['access_token'], 'ya29')
        self.assertEqual(out['refresh_token'], '1//r')
        self.assertEqual(out['external_account_id'], '1234567890')  # from login_customer_id

    @patch('providers.adapters.real_base.requests')
    def test_fetch_data_sums_and_converts_micros(self, req):
        req.post.return_value = resp({'results': [
            {'metrics': {'costMicros': '2500000', 'clicks': '10', 'impressions': '100', 'conversions': 2}},
            {'metrics': {'costMicros': '1500000', 'clicks': '5', 'impressions': '50', 'conversions': 1}},
        ]})
        data = self.adapter.fetch_data('ya29', 'stats', {},
                                       {'external_account_id': '1234567890',
                                        'login_customer_id': '1234567890'})
        self.assertEqual(data['metrics']['spend'], 4.0)  # (2.5M + 1.5M) micros → 4.0
        self.assertEqual(data['metrics']['clicks'], 15)

    @override_settings(PROVIDER_CONFIG={'google-ads': {'client_id': '', 'client_secret': '',
                                                       'developer_token': ''}})
    def test_missing_config_raises(self):
        from django.core.exceptions import ImproperlyConfigured
        with self.assertRaises(ImproperlyConfigured):
            GoogleAdsAdapter(Provider(slug='google-ads', name='Google Ads', is_mock=False))
