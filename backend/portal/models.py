from django.conf import settings
from django.db import models


class Announcement(models.Model):
    class Audience(models.TextChoices):
        ALL = 'all', 'Everyone'
        CLIENTS = 'clients', 'All clients'
        CLIENT_ORG = 'client_org', 'Specific client'

    class Severity(models.TextChoices):
        INFO = 'info', 'Info'
        WARNING = 'warning', 'Warning'
        CRITICAL = 'critical', 'Critical'

    audience = models.CharField(max_length=16, choices=Audience.choices, default=Audience.ALL)
    client_org = models.ForeignKey(
        'users.ClientOrg', null=True, blank=True, on_delete=models.CASCADE,
        related_name='announcements',
    )
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    severity = models.CharField(max_length=12, choices=Severity.choices, default=Severity.INFO)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Note(models.Model):
    """A blocker or note attached to a client org (optionally a connection)."""

    class Type(models.TextChoices):
        BLOCKER = 'blocker', 'Blocker'
        NOTE = 'note', 'Note'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        RESOLVED = 'resolved', 'Resolved'

    client_org = models.ForeignKey(
        'users.ClientOrg', on_delete=models.CASCADE, related_name='portal_notes'
    )
    connection = models.ForeignKey(
        'connections.Connection', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='notes',
    )
    type = models.CharField(max_length=12, choices=Type.choices, default=Type.NOTE)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.type}] {self.title}'


class ConnectionRequest(models.Model):
    """A developer asking a client org to connect a given provider."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONNECTED = 'connected', 'Connected'
        DECLINED = 'declined', 'Declined'

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='connection_requests',
    )
    client_org = models.ForeignKey(
        'users.ClientOrg', on_delete=models.CASCADE, related_name='connection_requests'
    )
    provider = models.ForeignKey(
        'providers.Provider', on_delete=models.CASCADE, related_name='connection_requests'
    )
    message = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.provider} for {self.client_org} [{self.status}]'


class Comment(models.Model):
    """A reply in a note/blocker thread (two-way team ↔ client communication)."""

    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment on note {self.note_id}'


class Notification(models.Model):
    """An in-app notification for a single user (drives the bell + unread count)."""

    class Kind(models.TextChoices):
        ANNOUNCEMENT = 'announcement', 'Announcement'
        NOTE = 'note', 'Note'
        BLOCKER = 'blocker', 'Blocker'
        COMMENT = 'comment', 'Comment'
        REQUEST = 'request', 'Connection request'
        RESOLVED = 'resolved', 'Resolved'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='+',
    )
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.NOTE)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    url = models.CharField(max_length=255, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{"read" if self.read else "unread"}] {self.title} → {self.recipient_id}'
