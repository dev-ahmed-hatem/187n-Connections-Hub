"""Disable public demo principals without deleting organizations or credentials."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from access.models import Consumer

DEMO_USERS = ('admin', 'dev', 'northwind', 'lumen', 'volt')


class Command(BaseCommand):
    help = 'Preview disabling demo users and Demo Operator keys; --apply commits it.'

    def add_arguments(self, parser):
        parser.add_argument('--replacement-admin', required=True)
        parser.add_argument('--apply', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        admin = User.objects.filter(username=options['replacement_admin'], is_active=True).first()
        if not admin or not admin.is_admin_role or admin.username in DEMO_USERS or not admin.has_usable_password():
            raise CommandError('An active personal admin with a usable password is required first.')
        users = User.objects.filter(username__in=DEMO_USERS)
        projects = Consumer.objects.filter(name='Demo Operator')
        self.stdout.write(f'Demo users: {users.count()}; demo projects: {projects.count()}. No client data will be deleted.')
        if not options['apply']:
            self.stdout.write('Preview only. Verify personal admin login before applying.')
            return
        for user in users:
            user.is_active = False
            user.set_unusable_password()
            user.save(update_fields=['is_active', 'password'])
        projects.update(active=False)
        self.stdout.write(self.style.SUCCESS('Demo principals disabled; organizations, connections and encrypted credentials preserved.'))
