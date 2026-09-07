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
