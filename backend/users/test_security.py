from io import StringIO
from unittest.mock import patch
from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from access.models import Consumer
from connections.models import Connection, ProviderCredential
from providers.models import Provider
from users.models import ClientOrg

User = get_user_model()


class SecureOnboardingTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('personal-admin', password='Unique-operator!4792', role='admin')
        self.dev = User.objects.create_user('personal-dev', password='Unique-developer!4792', role='developer')
        self.demo = User.objects.create_user('admin', password='old-secret', role='admin')
        self.org = ClientOrg.objects.create(name='Northwind Coffee', slug='northwind-coffee')
        self.project, self.key = Consumer.create_with_key('Demo Operator', self.org, self.demo)
        p = Provider.objects.create(name='Shopify', slug='shopify')
        self.cred = ProviderCredential.objects.create(client_org=self.org, provider=p, enc_access_token='fixture-token')
        self.conn = Connection.objects.create(client_org=self.org, provider=p, credential=self.cred, external_account_id='fixture.myshopify.com')

    @override_settings(DEBUG=False, ALLOW_DEMO_SEED=True)
    def test_production_seed_is_blocked(self):
        with self.assertRaises(CommandError):
            call_command('seed_demo')

    def test_preview_and_replacement_guard(self):
        with self.assertRaises(CommandError):
            call_command('secure_demo_access', replacement_admin='admin', apply=True)
        call_command('secure_demo_access', replacement_admin=self.admin.username, stdout=StringIO())
        self.demo.refresh_from_db()
        self.assertTrue(self.demo.is_active)

    def test_hardening_preserves_vault_and_revokes_demo_key(self):
        call_command('secure_demo_access', replacement_admin=self.admin.username, apply=True, stdout=StringIO())
        self.demo.refresh_from_db(); self.project.refresh_from_db(); self.cred.refresh_from_db()
        self.assertFalse(self.demo.is_active)
        self.assertFalse(self.demo.has_usable_password())
        self.assertFalse(self.project.active)
        self.assertEqual(self.cred.enc_access_token, 'fixture-token')
        self.assertTrue(Connection.objects.filter(pk=self.conn.pk).exists())

    def test_separate_workspace_and_existing_guard(self):
        args = dict(org_name='Audit Client', org_slug='audit-client', client_username='personal-client',
                    client_email='client@example.org', developer=self.dev.username, admin=self.admin.username,
                    apply=True, stdout=StringIO())
        with self.assertRaises(CommandError):
            call_command('provision_audit', **args)
        call_command('secure_demo_access', replacement_admin=self.admin.username, apply=True, stdout=StringIO())
        with patch('users.management.commands.provision_audit.getpass', return_value='Unique-client!4792'):
            call_command('provision_audit', **args)
        project = Consumer.objects.get(client_org__slug='audit-client')
        self.assertFalse(project.allow_token_broker)
        self.assertTrue(project.members.filter(pk=self.dev.pk).exists())
        self.assertNotEqual(project.client_org_id, self.org.pk)
        with self.assertRaises(CommandError):
            call_command('provision_audit', **args)
