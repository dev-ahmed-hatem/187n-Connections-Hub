"""A tiny blocking scheduler (no Celery). Run as its own process:

    python manage.py run_scheduler --interval 900

Every interval it refreshes near-expiry credentials and flags dead ones.
"""

import time

from django.core.management.base import BaseCommand

from connections.services import refresh_stale_credentials


class Command(BaseCommand):
    help = 'Blocking loop that periodically refreshes credentials.'

    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=900,
                            help='Seconds between runs (default 900).')
        parser.add_argument('--threshold', type=int, default=3600,
                            help='Refresh credentials expiring within N seconds (default 3600).')

    def handle(self, *args, **options):
        interval = options['interval']
        threshold = options['threshold']
        self.stdout.write(self.style.SUCCESS(
            f'Scheduler started: refresh every {interval}s (threshold {threshold}s). Ctrl-C to stop.'
        ))
        while True:
            try:
                refreshed, failed = refresh_stale_credentials(threshold)
                self.stdout.write(f'tick: refreshed {refreshed}, flagged {failed}')
            except Exception as exc:  # keep the loop alive
                self.stderr.write(f'tick error: {exc}')
            time.sleep(interval)
