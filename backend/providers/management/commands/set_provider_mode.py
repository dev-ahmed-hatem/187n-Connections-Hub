"""Flip a provider between the mock adapter and its real (live) adapter.

    python manage.py set_provider_mode shopify --live
    python manage.py set_provider_mode shopify --mock

Going live validates the adapter config immediately, so a missing credential
fails here rather than mid-connect.
"""

from django.core.management.base import BaseCommand, CommandError

from providers.adapters import get_adapter
from providers.models import Provider


class Command(BaseCommand):
    help = 'Switch a provider between mock and live adapters.'

    def add_arguments(self, parser):
        parser.add_argument('slug')
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--live', action='store_true', help='Use the real adapter.')
        group.add_argument('--mock', action='store_true', help='Use the mock adapter.')

    def handle(self, *args, **options):
        try:
            provider = Provider.objects.get(slug=options['slug'])
        except Provider.DoesNotExist:
            raise CommandError(f'No provider with slug "{options["slug"]}".')

        provider.is_mock = bool(options['mock'])
        provider.save(update_fields=['is_mock'])

        if not provider.is_mock:
            # Validate credentials are present for the real adapter.
            try:
                get_adapter(provider)
            except Exception as exc:
                # Roll back so we don't leave a live provider that can't work.
                provider.is_mock = True
                provider.save(update_fields=['is_mock'])
                raise CommandError(f'Cannot go live: {exc}')

        mode = 'MOCK' if provider.is_mock else 'LIVE'
        self.stdout.write(self.style.SUCCESS(f'{provider.slug} is now {mode}.'))
