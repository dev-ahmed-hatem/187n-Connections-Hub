from unittest.mock import MagicMock
from django.test import SimpleTestCase
from providers.adapters.audit import google, meta_ads, shopify, period
DATES = {'start_date': '2026-08-15', 'end_date': '2026-08-31'}

class AuditProbeTests(SimpleTestCase):
    def adapter(self):
        a = MagicMock(); a.config = {'api_version': 'v24'}; a.graph = 'https://graph.facebook.com/v21.0'
        return a

    def test_explicit_complete_period_required(self):
        for params in [{}, {'start_date': '2026-09-09', 'end_date': '2026-08-01'}, {'start_date': '2026-08-01', 'end_date': '2999-01-01'}]:
            with self.assertRaises(ValueError): period(params)

    def test_ads_campaign_query_without_developer_token(self):
        a = self.adapter()
        a._post.side_effect = [{'results': [{'customer': {'id': '1234567890', 'currencyCode': 'EUR', 'timeZone': 'Europe/Amsterdam'}}]}, {'results': [{'campaign': {'id': '123'}, 'metrics': {'costMicros': '1000000', 'conversions': 1}}]}]
        data = google(a, 'fixture', DATES, {'external_account_id': '1234567890'})
        self.assertEqual(data['currency'], 'EUR')
        self.assertIn('metrics.conversions', a._post.call_args.kwargs['json']['query'])
        self.assertNotIn('developer-token', a._post.call_args.kwargs['headers'])
        self.assertNotIn('mutate', a._post.call_args.args[0])

    def test_ads_wrong_account_fails_before_metrics(self):
        a = self.adapter(); a._post.return_value = {'results': [{'customer': {'id': '9999999999'}}]}
        with self.assertRaises(ValueError): google(a, 'fixture', DATES, {'external_account_id': '1234567890'})
        self.assertEqual(a._post.call_count, 1)

    def test_ga4_is_separate_and_requests_commerce_events(self):
        a = self.adapter(); a._get.return_value = {'name': 'properties/123', 'currencyCode': 'EUR', 'timeZone': 'Europe/Amsterdam'}
        a._post.side_effect = [{'rows': [{'metricValues': [{'value': '10'}]}]}, {'rows': []}]
        data = google(a, 'fixture', {**DATES, 'property_id': '123'}, {}, analytics=True)
        self.assertEqual(data['provider'], 'ga4'); self.assertEqual(a._post.call_count, 2)
        self.assertIn('purchase', str(a._post.call_args.kwargs['json'])); self.assertEqual(data['events'], [])
        with self.assertRaises(ValueError): google(a, 'fixture', {**DATES, 'property_id': '../456'}, {}, analytics=True)

    def test_meta_business_must_match(self):
        a = self.adapter(); a._get.return_value = {'id': 'act_123', 'business': {'id': '999'}}
        with self.assertRaises(ValueError): meta_ads(a, 'fixture', {**DATES, 'business_id': '456'}, {'external_account_id': 'act_123'})
        self.assertEqual(a._get.call_count, 1)

    def test_meta_reads_conversions_and_reports_truncation(self):
        a = self.adapter(); a._get.side_effect = [{'id': 'act_123', 'business': {'id': '456'}, 'currency': 'EUR', 'timezone_name': 'Europe/Amsterdam'}, {'data': [{'campaign_id': '5', 'spend': '1.00'}], 'paging': {'next': 'not-followed'}}]
        data = meta_ads(a, 'fixture', {**DATES, 'business_id': '456'}, {'external_account_id': 'act_123'})
        self.assertTrue(data['truncated']); self.assertIn('actions', a._get.call_args.kwargs['params']['fields'])
        self.assertNotIn('access_token', a._get.call_args.kwargs['params'])

    def test_shopify_query_has_no_mutation_or_customer_pii(self):
        a = self.adapter(); a.config = {'api_version': '2026-07'}
        a._post.return_value = {'data': {'shop': {'myshopifyDomain': 'fixture.myshopify.com', 'currencyCode': 'EUR', 'ianaTimezone': 'Europe/Amsterdam'}, 'currentAppInstallation': {'accessScopes': [{'handle': 'read_orders'}, {'handle': 'read_all_orders'}]}, 'orders': {'nodes': [{'id': 'gid://shopify/Order/1', 'refunds': []}], 'pageInfo': {'hasNextPage': True}}}}
        data = shopify(a, 'fixture', DATES, {'external_account_id': 'fixture.myshopify.com'})
        query = a._post.call_args.kwargs['json']['query']
        self.assertIn('refunds', query); self.assertNotIn('mutation', query); self.assertNotIn('email', query)
        self.assertTrue(data['truncated']); self.assertIn('unavailable', data['funnel'])

    def test_shopify_graphql_error_and_unsafe_domain_fail(self):
        a = self.adapter(); a._post.return_value = {'errors': [{'message': 'permission denied'}]}
        for shop in ['fixture.myshopify.com', 'evil.example/?token=']:
            with self.assertRaises(ValueError): shopify(a, 'fixture', DATES, {'external_account_id': shop})

    def test_provider_http_error_never_exposes_request_secret(self):
        import requests
        from unittest.mock import patch
        from providers.adapters.real_base import RealAdapter
        from providers.models import Provider
        with patch('providers.adapters.real_base.requests.get', side_effect=requests.HTTPError('https://example.org/?access_token=fixture-private')):
            with self.assertRaises(ValueError) as caught:
                RealAdapter._request(None, requests.get, 'https://example.org/')
        self.assertNotIn('fixture-private', str(caught.exception))

    def test_shopify_authorization_rejects_arbitrary_hosts(self):
        from providers.adapters.shopify import _normalize_shop
        for domain in ['attacker.example/?next=', 'a.myshopify.com/path', 'a.myshopify.com@attacker.example']:
            with self.assertRaises(ValueError): _normalize_shop(domain)
