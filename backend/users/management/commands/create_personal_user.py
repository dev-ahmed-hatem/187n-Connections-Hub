from getpass import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from .secure_demo_access import DEMO_USERS


class Command(BaseCommand):
    help = 'Create a named admin/developer using a hidden password prompt.'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--email', required=True)
        parser.add_argument('--role', choices=['admin', 'developer'], required=True)

    def handle(self, *args, **options):
        User = get_user_model()
        if options['username'] in DEMO_USERS or User.objects.filter(username=options['username']).exists():
            raise CommandError('Choose a new personal username; existing users are never overwritten.')
        user = User(username=options['username'], email=options['email'], role=options['role'])
        password = getpass('Password (store securely in password manager): ')
        if password != getpass('Confirm password: '):
            raise CommandError('Passwords do not match.')
        try:
            validate_email(user.email)
            validate_password(password, user)
        except ValidationError as exc:
            raise CommandError('; '.join(exc.messages))
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS('Personal user created. Verify login before disabling demo access.'))
