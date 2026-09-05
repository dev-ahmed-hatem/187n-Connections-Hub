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

    def test_scopes_enforced(self):
        # read-only grant: data allowed, token denied
        grant = Grant.objects.create(
            consumer=self.consumer, client_org=self.org, provider=self.provider,
            scopes=['read'])
        self._auth()
        self.assertEqual(self.client.get(self.data_url()).status_code, 200)
        self.assertEqual(
            self.client.post(f'/api/access/clients/{self.org.id}/google-ads/token').status_code,
            403)
        # empty scopes = full access
        grant.scopes = []
        grant.save()
        self.assertEqual(
            self.client.post(f'/api/access/clients/{self.org.id}/google-ads/token').status_code,
            200)

    def test_key_rotation_invalidates_old_key(self):
        Grant.objects.create(consumer=self.consumer, client_org=self.org, provider=self.provider)
        self._auth()
        self.assertEqual(self.client.get(self.data_url()).status_code, 200)
        new_key = self.consumer.rotate_key()
        # old key now rejected
        self.assertEqual(self.client.get(self.data_url()).status_code, 401)
        # new key works
        self.client.credentials(HTTP_AUTHORIZATION=f'ApiKey {new_key}')
        self.assertEqual(self.client.get(self.data_url()).status_code, 200)


class MultiAccountAccessTests(APITestCase):
    def setUp(self):
        self.org = ClientOrg.objects.create(name='Acme', slug='acme')
        self.provider = Provider.objects.create(slug='google-ads', name='Google Ads', is_mock=True)
        self.dev = User.objects.create_user(username='dev', password='x', role=User.Role.DEVELOPER)
        self.consumer, self.raw_key = Consumer.create_with_key('proj', self.dev)
        Grant.objects.create(consumer=self.consumer, client_org=self.org, provider=self.provider)
        self.accounts = ['1111111111', '2222222222']
        for acct in self.accounts:
            conn = Connection.objects.create(
                client_org=self.org, provider=self.provider, external_account_id=acct,
                status=Connection.Status.CONNECTED)
            TokenSet.objects.create(connection=conn, enc_access_token='a',
                                    access_expires_at=timezone.now() + timezone.timedelta(hours=1))
        self.client.credentials(HTTP_AUTHORIZATION=f'ApiKey {self.raw_key}')

    def url(self):
        return f'/api/access/clients/{self.org.id}/google-ads/data'

    def test_ambiguous_without_account_id(self):
        res = self.client.get(self.url())
        self.assertEqual(res.status_code, 400)
        self.assertCountEqual(res.json()['accounts'], self.accounts)

    def test_targeted_account(self):
        res = self.client.get(self.url(), {'account_id': self.accounts[0]})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['account_id'], self.accounts[0])

    def test_unknown_account(self):
        res = self.client.get(self.url(), {'account_id': '9999999999'})
        self.assertEqual(res.status_code, 404)


class GrantRequestTests(APITestCase):
    def setUp(self):
        self.org = ClientOrg.objects.create(name='Acme', slug='acme')
        self.provider = Provider.objects.create(slug='shopify', name='Shopify', is_mock=True)
        self.admin = User.objects.create_user(username='admin', password='x',
                                               role=User.Role.ADMIN, is_staff=True)
        self.dev = User.objects.create_user(username='dev', password='x',
                                            role=User.Role.DEVELOPER)
        self.consumer, _ = Consumer.create_with_key('proj', self.dev)

    def test_dev_request_then_admin_approve_creates_grant(self):
        from .models import GrantRequest
        self.client.force_authenticate(self.dev)
        res = self.client.post('/api/access/grant-requests/', {
            'consumer': self.consumer.id, 'client_org': self.org.id,
            'provider': self.provider.id, 'scopes': ['read']}, format='json')
        self.assertEqual(res.status_code, 201)
        req_id = res.json()['id']

        self.client.force_authenticate(self.admin)
        approve = self.client.post(f'/api/access/grant-requests/{req_id}/approve/')
        self.assertEqual(approve.status_code, 200)
        self.assertTrue(Grant.objects.filter(
            consumer=self.consumer, client_org=self.org, provider=self.provider,
            active=True).exists())
        self.assertEqual(GrantRequest.objects.get(id=req_id).status, 'approved')

    def test_dev_cannot_approve(self):
        from .models import GrantRequest
        gr = GrantRequest.objects.create(consumer=self.consumer, client_org=self.org,
                                         provider=self.provider, requested_by=self.dev)
        self.client.force_authenticate(self.dev)
        res = self.client.post(f'/api/access/grant-requests/{gr.id}/approve/')
        self.assertEqual(res.status_code, 403)
