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
    """A developer project identity that calls the Access API with an API key."""

    name = models.CharField(max_length=120)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='consumers'
    )
    api_key_hash = models.CharField(max_length=64, unique=True)
    api_key_prefix = models.CharField(max_length=16, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @classmethod
    def create_with_key(cls, name, owner):
        raw = generate_api_key()
        consumer = cls.objects.create(
            name=name,
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


class Grant(models.Model):
    """Authorizes a consumer to access a client org's provider connection.

    This is the deliberate gate: without an active grant, a consumer gets 403.
    """

    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='grants')
    client_org = models.ForeignKey(
        'users.ClientOrg', on_delete=models.CASCADE, related_name='grants'
    )
    provider = models.ForeignKey(
        'providers.Provider', on_delete=models.CASCADE, related_name='grants'
    )
    scopes = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('consumer', 'client_org', 'provider')

    def __str__(self):
        return f'{self.consumer} → {self.client_org}/{self.provider}'


class GrantRequest(models.Model):
    """A developer's self-serve request for a grant; an admin approves or denies.

    Approving creates the corresponding Grant. Keeps onboarding self-serve while
    the grant itself remains the admin-gated access decision.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        DENIED = 'denied', 'Denied'

    consumer = models.ForeignKey(
        Consumer, on_delete=models.CASCADE, related_name='grant_requests'
    )
    client_org = models.ForeignKey(
        'users.ClientOrg', on_delete=models.CASCADE, related_name='grant_requests'
    )
    provider = models.ForeignKey(
        'providers.Provider', on_delete=models.CASCADE, related_name='grant_requests'
    )
    scopes = models.JSONField(default=list, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='grant_requests',
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='grant_decisions',
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.consumer} → {self.client_org}/{self.provider} [{self.status}]'


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
