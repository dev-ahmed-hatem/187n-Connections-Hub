"""Explicitly target one client's account and probe only read-only audit resources."""
import json
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from connections.models import Connection
from connections.services import get_valid_access_token
from providers.adapters import get_adapter
from providers.adapters.audit import period


class Command(BaseCommand):
    help = 'Read a real account sample. Never marks OAuth connections as audit-verified.'

    def add_arguments(self, parser):
        for key in ('org-slug', 'connection-id', 'expected-account', 'start-date', 'end-date'):
            parser.add_argument('--' + key, required=True)
        parser.add_argument('--platform', choices=['shopify', 'meta-ads', 'google-ads', 'ga4'], required=True)
        parser.add_argument('--business-id')
        parser.add_argument('--property-id')

    def handle(self, *args, **options):
        platform = options['platform']
        provider = 'google-ads' if platform == 'ga4' else platform
        conn = Connection.objects.select_related('provider', 'credential').filter(
            id=options['connection_id'], client_org__slug=options['org_slug'],
            provider__slug=provider, provider__is_active=True, status=Connection.Status.CONNECTED).first()
        if not conn or conn.provider.is_mock or not conn.credential:
            raise CommandError('No real authorized connection matching this client and platform.')
        expected = options['expected_account']
        if platform != 'ga4' and conn.external_account_id != expected:
            raise CommandError('Expected account differs from the selected connection.')
        if platform == 'ga4' and expected != 'properties/' + str(options.get('property_id')):
            raise CommandError('Expected GA4 property differs from property-id.')
        try:
            period(options)
            adapter = get_adapter(conn.provider)
            data = adapter.fetch_data(get_valid_access_token(conn),
                'audit-ga4' if platform == 'ga4' else 'audit', options,
                {**(conn.meta or {}), 'external_account_id': conn.external_account_id})
            if data.get('mock') or data.get('account_id') != expected or data.get('provider') != platform:
                raise ValueError('Unexpected provider response.')
        except Exception as exc:
            # Provider exceptions may contain tokens in request URLs. Never print them.
            raise CommandError(f'Audit probe failed ({type(exc).__name__}); check permissions and configuration in the provider console.') from None
        rows = len(data.get('rows', []))
        events = len(data.get('events', [])) if platform == 'ga4' else None
        status = 'sample_read_succeeded' if rows and (platform != 'ga4' or events) else 'api_succeeded_but_required_data_missing'
        summary = {k: data[k] for k in ['provider', 'account_id', 'period', 'currency', 'timezone', 'sample', 'truncated']}
        summary.update(status=status, checked_at=timezone.now().isoformat(), rows=rows,
                       full_audit_ready=False, event_rows=events)
        for key in ['refunds_basis', 'funnel', 'attribution']:
            if key in data:
                summary[key] = data[key]
        self.stdout.write(json.dumps(summary))
