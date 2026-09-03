"""Renew near-expiry access tokens; flag failures as needing reconnect."""

from django.core.management.base import BaseCommand

from connections.models import Connection
from connections.services import get_valid_access_token


class Command(BaseCommand):
    help = 'Refresh access tokens for connected connections that are near expiry.'

    def handle(self, *args, **options):
        refreshed = 0
        failed = 0
        for conn in Connection.objects.filter(
            status=Connection.Status.CONNECTED
        ).select_related('provider', 'tokens'):
            tokens = getattr(conn, 'tokens', None)
            if not tokens or not tokens.is_access_expired:
                continue
            try:
                get_valid_access_token(conn)
                refreshed += 1
            except Exception:
                conn.status = Connection.Status.NEEDS_RECONNECT
                conn.save(update_fields=['status', 'updated_at'])
                failed += 1
        self.stdout.write(self.style.SUCCESS(
            f'Refreshed {refreshed} connection(s); {failed} flagged needs_reconnect.'
        ))
