from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from users.models import ClientOrg

from .models import Note, Notification

User = get_user_model()


class CommsTests(APITestCase):
    def setUp(self):
        self.org = ClientOrg.objects.create(name='Acme', slug='acme')
        self.admin = User.objects.create_user('admin', password='x', role=User.Role.ADMIN)
        self.dev = User.objects.create_user('dev', password='x', role=User.Role.DEVELOPER)
        self.client_user = User.objects.create_user(
            'c', password='x', role=User.Role.CLIENT, client_org=self.org)

    def test_staff_blocker_notifies_client(self):
        self.client.force_authenticate(self.dev)
        res = self.client.post('/api/portal/notes/', {
            'client_org': self.org.id, 'type': 'blocker', 'title': 'Fix it'}, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertTrue(Notification.objects.filter(
            recipient=self.client_user, kind='blocker').exists())

    def test_client_reply_notifies_staff(self):
        note = Note.objects.create(client_org=self.org, type=Note.Type.BLOCKER,
                                   title='X', created_by=self.dev)
        self.client.force_authenticate(self.client_user)
        res = self.client.post('/api/portal/comments/',
                               {'note': note.id, 'body': 'done'}, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertTrue(Notification.objects.filter(
            recipient=self.dev, kind='comment').exists())

    def test_client_resolves_and_notifies_creator(self):
        note = Note.objects.create(client_org=self.org, type=Note.Type.BLOCKER,
                                   title='X', created_by=self.dev)
        self.client.force_authenticate(self.client_user)
        res = self.client.post(f'/api/portal/notes/{note.id}/resolve/')
        self.assertEqual(res.status_code, 200)
        note.refresh_from_db()
        self.assertEqual(note.status, Note.Status.RESOLVED)
        self.assertTrue(Notification.objects.filter(
            recipient=self.dev, kind='resolved').exists())

    def test_client_cannot_create_announcement(self):
        self.client.force_authenticate(self.client_user)
        res = self.client.post('/api/portal/announcements/',
                               {'title': 'Hi', 'audience': 'all'}, format='json')
        self.assertEqual(res.status_code, 403)

    def test_client_cannot_comment_on_other_orgs_note(self):
        other = ClientOrg.objects.create(name='Other', slug='other')
        note = Note.objects.create(client_org=other, type=Note.Type.NOTE, title='X')
        self.client.force_authenticate(self.client_user)
        res = self.client.post('/api/portal/comments/',
                               {'note': note.id, 'body': 'peek'}, format='json')
        self.assertEqual(res.status_code, 403)
