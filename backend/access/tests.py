from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from connections.models import Connection, TokenSet
from providers.models import Provider
from users.models import ClientOrg

from .models import Consumer, Grant

User = get_user_model()


class AccessApiTests(APITestCase):
    def setUp(self):
        self.org = ClientOrg.objects.create(name='Acme', slug='acme')
        self.provider = Provider.objects.create(
            slug='google-ads', name='Google Ads', is_mock=True
        )
        self.conn = Connection.objects.create(
            client_org=self.org, provider=self.provider,
            external_account_id='1234567890', status=Connection.Status.CONNECTED,
        )
        TokenSet.objects.create(
            connection=self.conn,
            enc_refresh_token='r', enc_access_token='a',
            access_expires_at=timezone.now() + timezone.timedelta(hours=1),
        )
        self.developer = User.objects.create_user(
            username='dev', password='x', role=User.Role.DEVELOPER
        )
        self.consumer, self.raw_key = Consumer.create_with_key('proj', self.developer)

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'ApiKey {self.raw_key}')

    def data_url(self, slug='google-ads'):
        return f'/api/access/clients/{self.org.id}/{slug}/data'

    def test_denied_without_grant(self):
        self._auth()
        res = self.client.get(self.data_url())
        self.assertEqual(res.status_code, 403)

    def test_allowed_with_grant(self):
        Grant.objects.create(consumer=self.consumer, client_org=self.org, provider=self.provider)
        self._auth()
        res = self.client.get(self.data_url())
        self.assertEqual(res.status_code, 200)
        self.assertIn('metrics', res.json())

    def test_invalid_api_key_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION='ApiKey not-a-real-key')
        res = self.client.get(self.data_url())
        self.assertIn(res.status_code, (401, 403))

    def test_token_broker_with_grant(self):
        Grant.objects.create(consumer=self.consumer, client_org=self.org, provider=self.provider)
        self._auth()
        res = self.client.post(f'/api/access/clients/{self.org.id}/google-ads/token')
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn('access_token', body)
        self.assertNotIn('refresh_token', body)  # never exposed
