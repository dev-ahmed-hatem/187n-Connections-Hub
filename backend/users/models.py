from django.contrib.auth.models import AbstractUser
from django.db import models


class ClientOrg(models.Model):
    """A client company whose accounts get connected to the hub."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=120, unique=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom user with a hub role.

    - admin: manages orgs, users, consumers, grants, announcements.
    - developer: builds projects; fetches tokens/data; requests connections.
    - client: connects & monitors their own org's accounts.
    """

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        DEVELOPER = 'developer', 'Developer'
        CLIENT = 'client', 'Client'

    role = models.CharField(max_length=16, choices=Role.choices, default=Role.CLIENT)
    # Only set for client users — the org whose connections they manage.
    client_org = models.ForeignKey(
        ClientOrg,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='users',
    )

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_developer_role(self):
        return self.role == self.Role.DEVELOPER

    @property
    def is_client_role(self):
        return self.role == self.Role.CLIENT

    def __str__(self):
        return f'{self.username} ({self.role})'
