"""Seed the hub with demo data so the whole flow is walkable immediately.

Idempotent: safe to run repeatedly. Prints a fresh demo API key each run.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from access.models import Consumer, Grant
from connections.models import Connection, TokenSet
from portal.models import Announcement, ConnectionRequest, Note
from providers.adapters import get_adapter
from providers.models import Provider
from users.models import ClientOrg

User = get_user_model()

PROVIDERS = [
    {'slug': 'google-ads', 'name': 'Google', 'short_code': 'G', 'color': '#4285F4'},
    {'slug': 'meta-ads', 'name': 'Meta', 'short_code': 'M', 'color': '#5b6ef0'},
    {'slug': 'shopify', 'name': 'Shopify', 'short_code': 'S', 'color': '#5aa15a'},
]

ORGS = [
    {'slug': 'northwind-coffee', 'name': 'Northwind Coffee'},
    {'slug': 'lumen-skincare', 'name': 'Lumen Skincare'},
    {'slug': 'volt-fitness', 'name': 'Volt Fitness'},
]

# org slug -> {provider slug: status}
CONNECTIONS = {
    'northwind-coffee': {'google-ads': 'connected', 'shopify': 'connected'},
    'lumen-skincare': {'google-ads': 'connected', 'meta-ads': 'needs_reconnect'},
    'volt-fitness': {'google-ads': 'connected', 'meta-ads': 'connected', 'shopify': 'connected'},
}


class Command(BaseCommand):
    help = 'Seed demo users, providers, client orgs, connections, grants and portal content.'

    def handle(self, *args, **options):
        providers = {}
        for p in PROVIDERS:
            obj, _ = Provider.objects.update_or_create(
                slug=p['slug'],
                defaults={'name': p['name'], 'short_code': p['short_code'],
                          'color': p['color'], 'is_mock': True, 'is_active': True},
            )
            providers[p['slug']] = obj

        orgs = {}
        for o in ORGS:
            obj, _ = ClientOrg.objects.update_or_create(slug=o['slug'], defaults={'name': o['name']})
            orgs[o['slug']] = obj

        # Users
        admin = self._user('admin', 'admin123', role=User.Role.ADMIN, superuser=True)
        developer = self._user('dev', 'dev12345', role=User.Role.DEVELOPER)
        self._user('northwind', 'client123', role=User.Role.CLIENT, client_org=orgs['northwind-coffee'])
        self._user('lumen', 'client123', role=User.Role.CLIENT, client_org=orgs['lumen-skincare'])
        self._user('volt', 'client123', role=User.Role.CLIENT, client_org=orgs['volt-fitness'])

        # Pre-seed connections
        for org_slug, provider_map in CONNECTIONS.items():
            for provider_slug, status in provider_map.items():
                self._seed_connection(orgs[org_slug], providers[provider_slug], status)

        # A demo consumer + grants (so the API-key path works out of the box)
        consumer = Consumer.objects.filter(name='Demo Operator', owner=developer).first()
        raw_key = None
        if consumer is None:
            consumer, raw_key = Consumer.create_with_key('Demo Operator', developer)
        for provider_slug in ('google-ads', 'shopify'):
            Grant.objects.update_or_create(
                consumer=consumer, client_org=orgs['northwind-coffee'],
                provider=providers[provider_slug],
                defaults={'active': True, 'granted_by': admin, 'scopes': ['read']},
            )

        # Portal content
        Announcement.objects.update_or_create(
            title='Welcome to the Connections Hub',
            defaults={'audience': Announcement.Audience.ALL,
                      'body': 'Connect your accounts once and we handle the rest.',
                      'severity': Announcement.Severity.INFO, 'active': True, 'created_by': admin},
        )
        Announcement.objects.update_or_create(
            title='Scheduled maintenance Sunday 02:00 UTC',
            defaults={'audience': Announcement.Audience.CLIENTS,
                      'body': 'Brief downtime expected while we upgrade the vault.',
                      'severity': Announcement.Severity.WARNING, 'active': True, 'created_by': admin},
        )
        Note.objects.update_or_create(
            client_org=orgs['lumen-skincare'], title='Reconnect Meta Ads',
            defaults={'type': Note.Type.BLOCKER,
                      'body': 'Your Meta Ads connection expired — please reconnect.',
                      'status': Note.Status.OPEN, 'created_by': admin},
        )
        ConnectionRequest.objects.update_or_create(
            client_org=orgs['northwind-coffee'], provider=providers['meta-ads'],
            requested_by=developer,
            defaults={'message': 'We need Meta Ads to launch the new operator.',
                      'status': ConnectionRequest.Status.PENDING},
        )

        self.stdout.write(self.style.SUCCESS('Demo data seeded.'))
        self.stdout.write('Logins (username / password):')
        self.stdout.write('  admin / admin123        (admin)')
        self.stdout.write('  dev / dev12345          (developer)')
        self.stdout.write('  northwind / client123   (client · Northwind Coffee)')
        self.stdout.write('  lumen / client123       (client · Lumen Skincare)')
        self.stdout.write('  volt / client123        (client · Volt Fitness)')
        if raw_key:
            self.stdout.write(self.style.WARNING(f'Demo Operator API key (shown once): {raw_key}'))
        else:
            self.stdout.write('Demo Operator consumer already existed (API key not reshown). '
                              'Delete it in admin to regenerate.')

    def _user(self, username, password, role, client_org=None, superuser=False):
        user, created = User.objects.get_or_create(username=username, defaults={
            'role': role, 'client_org': client_org,
            'is_staff': superuser or role == User.Role.ADMIN,
            'is_superuser': superuser,
        })
        if created:
            user.set_password(password)
            user.role = role
            user.client_org = client_org
            user.is_staff = superuser or role == User.Role.ADMIN
            user.is_superuser = superuser
            user.save()
        return user

    def _seed_connection(self, org, provider, status):
        # Mirror the real connect flow: one grant may expose several accounts.
        adapter = get_adapter(provider)
        state = f'seed-{org.slug}-{provider.slug}'
        result = adapter.exchange_code(adapter.make_code(state), state)
        expires_at = timezone.now() + timezone.timedelta(seconds=result['expires_in'])
        enum_meta = {**result['meta'], 'external_account_id': result.get('external_account_id', '')}
        accounts = adapter.list_accounts(result['access_token'], enum_meta)
        for acct in accounts:
            conn, _ = Connection.objects.update_or_create(
                client_org=org, provider=provider,
                external_account_id=acct['external_account_id'],
                defaults={'display_name': acct.get('display_name') or provider.name,
                          'status': status, 'meta': acct.get('meta', {}),
                          'last_checked': timezone.now()},
            )
            TokenSet.objects.update_or_create(
                connection=conn,
                defaults={'enc_refresh_token': result['refresh_token'],
                          'enc_access_token': result['access_token'],
                          'access_expires_at': expires_at},
            )
