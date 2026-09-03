from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, viewsets

from authentication.permissions import IsAdminOrReadOnly

from .models import Announcement, ConnectionRequest, Note
from .serializers import (
    AnnouncementSerializer,
    ConnectionRequestSerializer,
    NoteSerializer,
)


class AnnouncementViewSet(viewsets.ModelViewSet):
    """Admins post announcements; everyone reads the ones targeted at them."""

    serializer_class = AnnouncementSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        qs = Announcement.objects.all()
        if user.is_admin_role or user.is_developer_role:
            return qs
        # client: only active announcements aimed at them
        org_id = user.client_org_id
        return qs.filter(active=True).filter(
            Q(audience=Announcement.Audience.ALL)
            | Q(audience=Announcement.Audience.CLIENTS)
            | Q(audience=Announcement.Audience.CLIENT_ORG, client_org_id=org_id)
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class NoteViewSet(viewsets.ModelViewSet):
    """Blockers & notes attached to a client org."""

    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Note.objects.select_related('client_org')
        if user.is_client_role:
            qs = qs.filter(client_org_id=user.client_org_id)
        else:
            org_id = self.request.query_params.get('client_org')
            if org_id:
                qs = qs.filter(client_org_id=org_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ConnectionRequestViewSet(viewsets.ModelViewSet):
    """Developer → client requests to connect a provider."""

    serializer_class = ConnectionRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = ConnectionRequest.objects.select_related('client_org', 'provider', 'requested_by')
        if user.is_admin_role:
            return qs
        if user.is_developer_role:
            return qs.filter(requested_by=user)
        # client
        return qs.filter(client_org_id=user.client_org_id)

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.status in (
            ConnectionRequest.Status.CONNECTED,
            ConnectionRequest.Status.DECLINED,
        ) and instance.resolved_at is None:
            instance.resolved_at = timezone.now()
            instance.save(update_fields=['resolved_at'])
