from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from connections.models import Connection, ProviderCredential
from providers.models import Provider
from users.models import ClientOrg

from .models import Consumer, ProjectAccessRequest

User = get_user_model()


def make_connection(org, provider, account_id, cred=None):
    cred = cred or ProviderCredential.objects.create(
        client_org=org, provider=provider, enc_access_token='a',
        access_expires_at=timezone.now() + timezone.timedelta(hours=1))
    Connection.objects.create(
        client_org=org, provider=provider, credential=cred,
        external_account_id=account_id, status=Connection.Status.CONNECTED)
    return cred


class ApiKeyAccessTests(APITestCase):
    def setUp(self):
        self.org = ClientOrg.objects.create(name='Acme', slug='acme')
        self.other = ClientOrg.objects.create(name='Other', slug='other')
        self.provider = Provider.objects.create(slug='google-ads', name='Google', is_mock=True)
        make_connection(self.org, self.provider, '1234567890')
        self.admin = User.objects.create_user('admin', password='x', role=User.Role.ADMIN)
        self.project, self.raw_key = Consumer.create_with_key(
            'proj', client_org=self.org, owner=self.admin)

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'ApiKey {self.raw_key}')

    def data_url(self, org):
        return f'/api/access/clients/{org.id}/google-ads/data'

    def test_key_accesses_its_client(self):
        self._auth()
        res = self.client.get(self.data_url(self.org))
        self.assertEqual(res.status_code, 200)
        self.assertIn('metrics', res.json())

    def test_key_denied_for_other_client(self):
        self._auth()
        res = self.client.get(self.data_url(self.other))
        self.assertEqual(res.status_code, 403)

    def test_invalid_key_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION='ApiKey not-real')
        self.assertIn(self.client.get(self.data_url(self.org)).status_code, (401, 403))

    def test_token_broker(self):
        self._auth()
        res = self.client.post(f'/api/access/clients/{self.org.id}/google-ads/token')
        self.assertEqual(res.status_code, 200)
        self.assertIn('access_token', res.json())
        self.assertNotIn('refresh_token', res.json())

    def test_key_rotation_invalidates_old(self):
        self._auth()
        self.assertEqual(self.client.get(self.data_url(self.org)).status_code, 200)
        new_key = self.project.rotate_key()
        self.assertEqual(self.client.get(self.data_url(self.org)).status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION=f'ApiKey {new_key}')
        self.assertEqual(self.client.get(self.data_url(self.org)).status_code, 200)


class MemberAccessTests(APITestCase):
    def setUp(self):
        self.org = ClientOrg.objects.create(name='Acme', slug='acme')
        self.provider = Provider.objects.create(slug='google-ads', name='Google', is_mock=True)
        self.admin = User.objects.create_user('admin', password='x', role=User.Role.ADMIN)
        self.dev = User.objects.create_user('dev', password='x', role=User.Role.DEVELOPER)
        self.other_dev = User.objects.create_user('dev2', password='x', role=User.Role.DEVELOPER)
        self.project, _ = Consumer.create_with_key('proj', client_org=self.org, owner=self.admin)
        self.project.members.add(self.dev)

    def data_url(self, params=''):
        return f'/api/access/clients/{self.org.id}/google-ads/data{params}'

    def test_member_dev_can_access(self):
        make_connection(self.org, self.provider, '111')
        self.client.force_authenticate(self.dev)
        self.assertEqual(self.client.get(self.data_url()).status_code, 200)

    def test_non_member_dev_denied(self):
        make_connection(self.org, self.provider, '111')
        self.client.force_authenticate(self.other_dev)
        self.assertEqual(self.client.get(self.data_url()).status_code, 403)

    def test_multi_account_ambiguous_then_targeted(self):
        cred = make_connection(self.org, self.provider, '111')
        make_connection(self.org, self.provider, '222', cred=cred)
        self.client.force_authenticate(self.dev)
        self.assertEqual(self.client.get(self.data_url()).status_code, 400)
        self.assertEqual(self.client.get(self.data_url('?account_id=111')).status_code, 200)


class ProjectRequestTests(APITestCase):
    def setUp(self):
        self.org = ClientOrg.objects.create(name='Acme', slug='acme')
        self.admin = User.objects.create_user('admin', password='x', role=User.Role.ADMIN)
        self.dev = User.objects.create_user('dev', password='x', role=User.Role.DEVELOPER)
        self.project, _ = Consumer.create_with_key('proj', client_org=self.org, owner=self.admin)

    def test_request_then_approve_adds_member(self):
        self.client.force_authenticate(self.dev)
        res = self.client.post('/api/access/project-requests/',
                               {'consumer': self.project.id}, format='json')
        self.assertEqual(res.status_code, 201)
        req_id = res.json()['id']
        self.client.force_authenticate(self.admin)
        approve = self.client.post(f'/api/access/project-requests/{req_id}/approve/')
        self.assertEqual(approve.status_code, 200)
        self.assertTrue(self.project.members.filter(id=self.dev.id).exists())
        self.assertEqual(ProjectAccessRequest.objects.get(id=req_id).status, 'approved')

    def test_dev_cannot_approve(self):
        req = ProjectAccessRequest.objects.create(consumer=self.project, requested_by=self.dev)
        self.client.force_authenticate(self.dev)
        res = self.client.post(f'/api/access/project-requests/{req.id}/approve/')
        self.assertEqual(res.status_code, 403)
