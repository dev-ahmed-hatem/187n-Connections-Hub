from django.db import connection as db_connection
from django.test import TestCase
from django.utils import timezone

from providers.adapters import get_adapter
from providers.models import Provider
from users.models import ClientOrg

from .models import Connection, ProviderCredential


class EncryptionTests(TestCase):
    def setUp(self):
        self.org = ClientOrg.objects.create(name='Acme', slug='acme')
        self.provider = Provider.objects.create(slug='google-ads', name='Google Ads', is_mock=True)

    def test_token_round_trip_and_ciphertext_at_rest(self):
        cred = ProviderCredential.objects.create(
            client_org=self.org, provider=self.provider,
            enc_refresh_token='super-secret-refresh',
            access_expires_at=timezone.now(),
        )
        # ORM decrypts transparently.
        self.assertEqual(ProviderCredential.objects.get(id=cred.id).enc_refresh_token,
                         'super-secret-refresh')
        # Raw DB value is Fernet ciphertext, not the plaintext.
        with db_connection.cursor() as cur:
            cur.execute('SELECT enc_refresh_token FROM connections_providercredential')
            raw = cur.fetchone()[0]
        self.assertNotIn('super-secret-refresh', raw)
        self.assertTrue(raw.startswith('gAAAA'))


class TestConnectionEndpointTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIClient
        User = get_user_model()
        self.org = ClientOrg.objects.create(name='Acme', slug='acme')
        self.provider = Provider.objects.create(slug='shopify', name='Shopify', is_mock=True)
        cred = ProviderCredential.objects.create(
            client_org=self.org, provider=self.provider, enc_access_token='a',
            access_expires_at=timezone.now() + timezone.timedelta(hours=1))
        self.conn = Connection.objects.create(
            client_org=self.org, provider=self.provider, credential=cred,
            external_account_id='demo.myshopify.com', status=Connection.Status.CONNECTED,
            meta={'shop': 'demo.myshopify.com'})
        self.user = User.objects.create_user(username='c', password='x',
                                             role=User.Role.CLIENT, client_org=self.org)
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def test_mock_connection_does_not_prove_real_data(self):
        res = self.api.post(f'/api/connections/{self.conn.id}/test')
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()['ok'])
        self.assertEqual(res.json()['status'], 'connected')


class MultiAccountConnectTests(TestCase):
    def setUp(self):
        self.org = ClientOrg.objects.create(name='Acme', slug='acme')
        self.provider = Provider.objects.create(slug='google-ads', name='Google Ads', is_mock=True)

    def test_connect_creates_a_connection_per_account(self):
        from connections.models import OAuthState
        from connections.services import complete_connection
        OAuthState.objects.create(state='s1', client_org=self.org, provider=self.provider)
        adapter = get_adapter(self.provider)
        complete_connection('s1', adapter.make_code('s1'))
        conns = Connection.objects.filter(client_org=self.org, provider=self.provider)
        self.assertEqual(conns.count(), 2)  # mock google-ads exposes 2 accounts
        self.assertEqual(len({c.external_account_id for c in conns}), 2)
        # Both accounts share ONE credential (the grant).
        self.assertEqual(len({c.credential_id for c in conns}), 1)
        self.assertEqual(ProviderCredential.objects.filter(
            client_org=self.org, provider=self.provider).count(), 1)


class CredentialRefreshTests(TestCase):
    def setUp(self):
        self.org = ClientOrg.objects.create(name='Acme', slug='acme')
        self.provider = Provider.objects.create(slug='google-ads', name='Google', is_mock=True)

    def test_refresh_stale_credentials_renews_expired(self):
        from connections.services import refresh_stale_credentials
        cred = ProviderCredential.objects.create(
            client_org=self.org, provider=self.provider,
            enc_refresh_token='mock-refresh-x', enc_access_token='old',
            access_expires_at=timezone.now() - timezone.timedelta(hours=1))
        refreshed, failed = refresh_stale_credentials(threshold_seconds=0)
        self.assertEqual((refreshed, failed), (1, 0))
        cred.refresh_from_db()
        self.assertGreater(cred.access_expires_at, timezone.now())

    def test_non_expiring_credential_skipped(self):
        from connections.services import refresh_stale_credentials
        ProviderCredential.objects.create(
            client_org=self.org, provider=self.provider,
            enc_refresh_token='', enc_access_token='shopify-offline',
            access_expires_at=timezone.now() - timezone.timedelta(hours=1))
        refreshed, failed = refresh_stale_credentials(threshold_seconds=0)
        self.assertEqual((refreshed, failed), (0, 0))


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
