"""Renew near-expiry provider credentials; flag failures as needs_reconnect."""

from django.core.management.base import BaseCommand

from connections.services import refresh_stale_credentials


class Command(BaseCommand):
    help = 'Refresh provider credentials at/near expiry (one-shot).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold', type=int, default=3600,
            help='Refresh credentials expiring within this many seconds (default 3600).',
        )

    def handle(self, *args, **options):
        refreshed, failed = refresh_stale_credentials(options['threshold'])
        self.stdout.write(self.style.SUCCESS(
            f'Refreshed {refreshed} credential(s); {failed} flagged needs_reconnect.'
        ))
