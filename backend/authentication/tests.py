from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()


class AccountTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('u', password='oldpass123', role=User.Role.CLIENT)
        self.client.force_authenticate(self.user)

    def test_change_password_wrong_old(self):
        res = self.client.post('/api/auth/change-password/',
                               {'old_password': 'nope', 'new_password': 'newpass123'}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_change_password_ok(self):
        res = self.client.post('/api/auth/change-password/',
                               {'old_password': 'oldpass123', 'new_password': 'newpass123'},
                               format='json')
        self.assertEqual(res.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

    def test_profile_patch(self):
        res = self.client.patch('/api/auth/me/', {'first_name': 'Neo'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Neo')


class SessionRevocationTests(APITestCase):
    def test_disabled_demo_cannot_use_access_or_refresh(self):
        user = User.objects.create_user('demo-principal', password='Original-test!4792', role='admin')
        tokens = self.client.post('/api/auth/login/', {'username': user.username, 'password': 'Original-test!4792'}, format='json').json()
        user.is_active = False; user.set_unusable_password(); user.save()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + tokens['access'])
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)
        self.client.credentials()
        self.assertEqual(self.client.post('/api/auth/refresh/', {'refresh': tokens['refresh']}, format='json').status_code, 401)

    def test_password_change_invalidates_old_access(self):
        user = User.objects.create_user('personal-admin', password='Original-test!4792', role='admin')
        tokens = self.client.post('/api/auth/login/', {'username': user.username, 'password': 'Original-test!4792'}, format='json').json()
        user.set_password('Changed-test!4792'); user.save()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + tokens['access'])
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)
