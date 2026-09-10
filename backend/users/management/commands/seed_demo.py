"""Seed the hub with demo users, clients, providers, a project and portal content.

Idempotent. Does NOT create any platform connections — those come from real OAuth.
"""

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from access.models import Consumer
from portal.models import Announcement, ConnectionRequest, Note
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


class Command(BaseCommand):
    help = 'Seed demo users, providers, client orgs, a project and portal content (no connections).'

    def handle(self, *args, **options):
        if not settings.DEBUG or not settings.ALLOW_DEMO_SEED:
            raise CommandError('Demo seeding requires DEBUG and ALLOW_DEMO_SEED=true in a local environment.')
        providers = {}
        for p in PROVIDERS:
            obj, _ = Provider.objects.update_or_create(
                slug=p['slug'],
                defaults={'name': p['name'], 'short_code': p['short_code'],
                          'color': p['color'], 'is_mock': False, 'is_active': True},
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

        # A demo project bound to a client, with the developer as a member.
        consumer = Consumer.objects.filter(name='Demo Operator').first()
        raw_key = None
        if consumer is None:
            consumer, raw_key = Consumer.create_with_key(
                'Demo Operator', client_org=orgs['northwind-coffee'], owner=admin)
        else:
            consumer.client_org = orgs['northwind-coffee']
            consumer.save(update_fields=['client_org'])
        consumer.members.add(developer)

        # Portal content
        Announcement.objects.update_or_create(
            title='Welcome to the 187n Connections Hub',
            defaults={'audience': Announcement.Audience.ALL,
                      'body': 'Connect your accounts once and we handle the rest.',
                      'severity': Announcement.Severity.INFO, 'active': True, 'created_by': admin},
        )
        Note.objects.update_or_create(
            client_org=orgs['northwind-coffee'], title='Connect your platforms',
            defaults={'type': Note.Type.NOTE,
                      'body': 'Please connect the accounts your operator needs.',
                      'status': Note.Status.OPEN, 'created_by': admin},
        )
        ConnectionRequest.objects.filter(
            client_org=orgs['northwind-coffee'], provider=providers['google-ads'],
            requested_by=developer).delete()
        ConnectionRequest.objects.create(
            client_org=orgs['northwind-coffee'], provider=providers['google-ads'],
            requested_by=developer,
            message='We need Google connected to launch the operator.',
            status=ConnectionRequest.Status.PENDING)

        self.stdout.write(self.style.SUCCESS('Demo data seeded (no connections — connect via OAuth).'))

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
