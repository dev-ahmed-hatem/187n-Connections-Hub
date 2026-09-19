import hashlib
import secrets

from django.conf import settings
from django.db import models


def generate_api_key() -> str:
    """A raw API key, shown to the developer exactly once."""
    return 'hub_' + secrets.token_urlsafe(32)


def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class Consumer(models.Model):
    """A **project**: an API-key identity bound to ONE client, usable by its
    assigned developer members. Holding the key (or being a member) grants access
    to any of that client's connected platforms."""

    name = models.CharField(max_length=120)
    client_org = models.ForeignKey(
        'users.ClientOrg', null=True, blank=True, on_delete=models.CASCADE,
        related_name='projects',
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='member_projects'
    )
    owner = models.ForeignKey(  # creator (record only); access is via members/key
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='created_projects',
    )
    api_key_hash = models.CharField(max_length=64, unique=True)
    api_key_prefix = models.CharField(max_length=16, blank=True)
    active = models.BooleanField(default=True)
    allow_token_broker = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @classmethod
    def create_with_key(cls, name, client_org=None, owner=None):
        raw = generate_api_key()
        consumer = cls.objects.create(
            name=name,
            client_org=client_org,
            owner=owner,
            api_key_hash=hash_api_key(raw),
            api_key_prefix=raw[:12],
        )
        return consumer, raw

    def rotate_key(self):
        """Generate a new key, invalidating the old one. Returns the raw key once."""
        raw = generate_api_key()
        self.api_key_hash = hash_api_key(raw)
        self.api_key_prefix = raw[:12]
        self.save(update_fields=['api_key_hash', 'api_key_prefix'])
        return raw

    def __str__(self):
        return f'{self.name} ({self.api_key_prefix}…)'


class ProjectAccessRequest(models.Model):
    """A developer's self-serve request to join a project. Approving adds them
    to the project's members."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        DENIED = 'denied', 'Denied'

    consumer = models.ForeignKey(
        Consumer, on_delete=models.CASCADE, related_name='access_requests'
    )
    message = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='project_requests',
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='project_decisions',
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.requested_by} → {self.consumer} [{self.status}]'


class AuditLog(models.Model):
    """Append-only record of every access-API call."""

    actor_type = models.CharField(max_length=16, blank=True)  # 'consumer' | 'user'
    actor_label = models.CharField(max_length=255, blank=True)
    action = models.CharField(max_length=64)
    client_org = models.ForeignKey(
        'users.ClientOrg', null=True, blank=True, on_delete=models.SET_NULL
    )
    provider = models.ForeignKey(
        'providers.Provider', null=True, blank=True, on_delete=models.SET_NULL
    )
    status = models.CharField(max_length=16, default='ok')  # 'ok' | 'denied' | 'error'
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.status}] {self.actor_label} {self.action}'
