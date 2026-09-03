from django.db import connection as db_connection
from django.test import TestCase
from django.utils import timezone

from providers.adapters import get_adapter
from providers.models import Provider
from users.models import ClientOrg

from .models import Connection, TokenSet


class EncryptionTests(TestCase):
    def setUp(self):
        self.org = ClientOrg.objects.create(name='Acme', slug='acme')
        self.provider = Provider.objects.create(slug='google-ads', name='Google Ads', is_mock=True)

    def test_token_round_trip_and_ciphertext_at_rest(self):
        conn = Connection.objects.create(client_org=self.org, provider=self.provider)
        TokenSet.objects.create(
            connection=conn,
            enc_refresh_token='super-secret-refresh',
            access_expires_at=timezone.now(),
        )
        # ORM decrypts transparently.
        self.assertEqual(TokenSet.objects.get(connection=conn).enc_refresh_token,
                         'super-secret-refresh')
        # Raw DB value is Fernet ciphertext, not the plaintext.
        with db_connection.cursor() as cur:
            cur.execute('SELECT enc_refresh_token FROM connections_tokenset')
            raw = cur.fetchone()[0]
        self.assertNotIn('super-secret-refresh', raw)
        self.assertTrue(raw.startswith('gAAAA'))


class MockAdapterTests(TestCase):
    def setUp(self):
        self.provider = Provider.objects.create(slug='shopify', name='Shopify', is_mock=True)

    def test_exchange_is_deterministic(self):
        adapter = get_adapter(self.provider)
        a = adapter.exchange_code(adapter.make_code('s1'), 's1')
        b = adapter.exchange_code(adapter.make_code('s1'), 's1')
        self.assertEqual(a['refresh_token'], b['refresh_token'])
        self.assertEqual(a['external_account_id'], b['external_account_id'])

    def test_fetch_data_shape(self):
        adapter = get_adapter(self.provider)
        data = adapter.fetch_data('mock-access-x', 'stats', {}, {})
        self.assertEqual(data['provider'], 'shopify')
        self.assertIn('metrics', data)
