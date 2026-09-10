"""Provision a separate audit workspace. No passwords or API keys are printed."""
from getpass import getpass
import secrets
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import transaction
from access.models import Consumer, hash_api_key
from users.models import ClientOrg
from .secure_demo_access import DEMO_USERS


class Command(BaseCommand):
    help = 'Create an isolated audit organization, personal client and data-only project.'

    def add_arguments(self, parser):
        for key in ('org-name', 'org-slug', 'client-username', 'client-email', 'developer', 'admin'):
            parser.add_argument('--' + key, required=True)
        parser.add_argument('--apply', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        admin = User.objects.filter(username=options['admin'], is_active=True).first()
        dev = User.objects.filter(username=options['developer'], is_active=True, role=User.Role.DEVELOPER).first()
        if not admin or not admin.is_admin_role or admin.username in DEMO_USERS:
            raise CommandError('Use an existing active personal admin.')
        if not dev or dev.username in DEMO_USERS:
            raise CommandError('Use a confirmed existing personal developer.')
        if options['client_username'] in DEMO_USERS:
            raise CommandError('Demo identities cannot be used for a customer.')
        if options['org_slug'] in ('northwind-coffee', 'lumen-skincare', 'volt-fitness'):
            raise CommandError('A separate organization is required.')
        try:
            validate_email(options['client_email'])
        except ValidationError:
            raise CommandError('A valid personal client email is required.')
        if ClientOrg.objects.filter(slug=options['org_slug']).exists() or User.objects.filter(username=options['client_username']).exists():
            raise CommandError('Organization or username already exists; review it instead of overwriting.')
        if not options['apply']:
            self.stdout.write('Preview: create separate organization, personal client and audit project; assign confirmed developer; token broker disabled. No changes made.')
            return
        # Personal admin login must be verified before the separate hardening command.
        if User.objects.filter(username__in=DEMO_USERS, is_active=True).exists() or Consumer.objects.filter(name='Demo Operator', active=True).exists():
            raise CommandError('Disable demo access before onboarding customer data.')
        user = User(username=options['client_username'], email=options['client_email'], role=User.Role.CLIENT)
        password = getpass('New client password (store in password manager): ')
        if password != getpass('Confirm client password: '):
            raise CommandError('Passwords do not match.')
        try:
            validate_password(password, user)
        except ValidationError as exc:
            raise CommandError('; '.join(exc.messages))
        org = ClientOrg.objects.create(name=options['org_name'], slug=options['org_slug'])
        user.client_org = org
        user.set_password(password)
        user.save()
        # No distributable machine key is issued. Developer authenticates personally.
        project = Consumer.objects.create(name=options['org_name'] + ' account audit', client_org=org,
            owner=admin, allow_token_broker=False, api_key_hash=hash_api_key(secrets.token_urlsafe(48)))
        project.members.add(dev)
        self.stdout.write(self.style.SUCCESS('Audit workspace created. No provider authorization or data verification performed.'))
