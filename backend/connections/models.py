from django.conf import settings
from django.db import models
from django.utils import timezone

from .fields import EncryptedTextField


class Connection(models.Model):
    """A live link between a client org and a provider account."""

    class Status(models.TextChoices):
        CONNECTED = 'connected', 'Connected'
        NEEDS_RECONNECT = 'needs_reconnect', 'Needs reconnect'
        DISCONNECTED = 'disconnected', 'Disconnected'
        ERROR = 'error', 'Error'

    client_org = models.ForeignKey(
        'users.ClientOrg', on_delete=models.CASCADE, related_name='connections'
    )
    provider = models.ForeignKey(
        'providers.Provider', on_delete=models.CASCADE, related_name='connections'
    )
    external_account_id = models.CharField(max_length=128, blank=True)
    display_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CONNECTED
    )
    meta = models.JSONField(default=dict, blank=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['client_org', 'provider']
        unique_together = ('client_org', 'provider')

    def __str__(self):
        return f'{self.client_org} · {self.provider} [{self.status}]'


class TokenSet(models.Model):
    """The encrypted vault entry for a connection."""

    connection = models.OneToOneField(
        Connection, on_delete=models.CASCADE, related_name='tokens'
    )
    enc_refresh_token = EncryptedTextField(blank=True)
    enc_access_token = EncryptedTextField(blank=True)
    access_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_access_expired(self) -> bool:
        if not self.access_expires_at:
            return True
        # Refresh a little early to avoid edge-of-expiry failures.
        return timezone.now() >= self.access_expires_at - timezone.timedelta(seconds=30)

    def __str__(self):
        return f'Tokens for {self.connection_id}'


class OAuthState(models.Model):
    """A short-lived record of an in-flight OAuth authorization."""

    state = models.CharField(max_length=64, unique=True)
    client_org = models.ForeignKey('users.ClientOrg', on_delete=models.CASCADE)
    provider = models.ForeignKey('providers.Provider', on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'OAuthState {self.state} ({self.provider})'
