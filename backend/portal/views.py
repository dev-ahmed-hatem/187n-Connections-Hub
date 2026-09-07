from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from access.models import Consumer
from authentication.permissions import IsAdminOrReadOnly, IsStaffOrReadOnly

from . import notifications as notify_svc
from .models import Announcement, Comment, ConnectionRequest, Note, Notification


def dev_client_ids(user):
    """Client-org ids a developer is assigned to (via project membership)."""
    return set(Consumer.objects.filter(members=user).values_list('client_org_id', flat=True))
from .serializers import (
    AnnouncementSerializer,
    CommentSerializer,
    ConnectionRequestSerializer,
    NoteSerializer,
    NotificationSerializer,
)

CLIENT_UPDATES_URL = '/client/updates'
STAFF_MESSAGES_URL = '/staff/messages'


class AnnouncementViewSet(viewsets.ModelViewSet):
    """Only admins post announcements; everyone reads the ones aimed at them."""

    serializer_class = AnnouncementSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        qs = Announcement.objects.all()
        if user.is_admin_role or user.is_developer_role:
            return qs
        org_id = user.client_org_id
        return qs.filter(active=True).filter(
            Q(audience=Announcement.Audience.ALL)
            | Q(audience=Announcement.Audience.CLIENTS)
            | Q(audience=Announcement.Audience.CLIENT_ORG, client_org_id=org_id)
        )

    def perform_create(self, serializer):
        ann = serializer.save(created_by=self.request.user)
        if ann.audience == Announcement.Audience.ALL:
            recips = notify_svc.all_users()
        elif ann.audience == Announcement.Audience.CLIENTS:
            recips = notify_svc.all_client_users()
        else:
            recips = notify_svc.client_users(ann.client_org)
        notify_svc.notify(recips, self.request.user, Notification.Kind.ANNOUNCEMENT,
                          f'Announcement: {ann.title}', ann.body, CLIENT_UPDATES_URL)


class NoteViewSet(viewsets.ModelViewSet):
    """Blockers & notes attached to a client org (threaded via comments)."""

    serializer_class = NoteSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        qs = Note.objects.select_related('client_org')
        if user.is_client_role:
            return qs.filter(client_org_id=user.client_org_id)
        if user.is_developer_role:
            qs = qs.filter(client_org_id__in=dev_client_ids(user))
        org_id = self.request.query_params.get('client_org')
        return qs.filter(client_org_id=org_id) if org_id else qs

    def perform_create(self, serializer):
        user = self.request.user
        org = serializer.validated_data['client_org']
        if user.is_developer_role and org.id not in dev_client_ids(user):
            raise PermissionDenied('You can only message clients assigned to your projects.')
        note = serializer.save(created_by=user)
        kind = (Notification.Kind.BLOCKER if note.type == Note.Type.BLOCKER
                else Notification.Kind.NOTE)
        notify_svc.notify(notify_svc.client_users(note.client_org), user,
                          kind, f'New {note.type}: {note.title}', note.body, CLIENT_UPDATES_URL)

    def _set_status(self, request, pk, status_value):
        note = get_object_or_404(Note, id=pk)
        user = request.user
        if user.is_client_role and note.client_org_id != user.client_org_id:
            raise PermissionDenied('Not allowed.')
        note.status = status_value
        note.save(update_fields=['status'])
        # Notify the other side.
        if user.is_client_role:
            recips = notify_svc.staff_users() + ([note.created_by] if note.created_by else [])
        else:
            recips = notify_svc.client_users(note.client_org)
        notify_svc.notify(recips, user, Notification.Kind.RESOLVED,
                          f'{note.title} — {status_value}', '', CLIENT_UPDATES_URL)
        return Response(NoteSerializer(note).data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def resolve(self, request, pk=None):
        return self._set_status(request, pk, Note.Status.RESOLVED)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reopen(self, request, pk=None):
        return self._set_status(request, pk, Note.Status.OPEN)


class CommentViewSet(viewsets.ModelViewSet):
    """Replies in a note/blocker thread."""

    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post']

    def _note_or_403(self, note_id):
        note = get_object_or_404(Note.objects.select_related('client_org'), id=note_id)
        user = self.request.user
        if user.is_client_role and note.client_org_id != user.client_org_id:
            raise PermissionDenied('Not allowed.')
        if user.is_developer_role and note.client_org_id not in dev_client_ids(user):
            raise PermissionDenied('Not allowed.')
        return note

    def get_queryset(self):
        note_id = self.request.query_params.get('note')
        if not note_id:
            return Comment.objects.none()
        note = self._note_or_403(note_id)
        return Comment.objects.filter(note=note).select_related('author')

    def perform_create(self, serializer):
        note = self._note_or_403(serializer.validated_data['note'].id)
        comment = serializer.save(author=self.request.user)
        user = self.request.user
        if user.is_client_role:
            recips = notify_svc.staff_users() + ([note.created_by] if note.created_by else [])
            url = STAFF_MESSAGES_URL
        else:
            recips = notify_svc.client_users(note.client_org)
            url = CLIENT_UPDATES_URL
        notify_svc.notify(recips, user, Notification.Kind.COMMENT,
                          f'New reply on: {note.title}', comment.body, url)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """The current user's in-app notifications."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)[:100]

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        count = Notification.objects.filter(recipient=request.user, read=False).count()
        return Response({'count': count})

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        Notification.objects.filter(recipient=request.user, id=pk).update(read=True)
        return Response({'ok': True})

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        Notification.objects.filter(recipient=request.user, read=False).update(read=True)
        return Response({'ok': True})


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
        return qs.filter(client_org_id=user.client_org_id)

    def perform_create(self, serializer):
        req = serializer.save(requested_by=self.request.user)
        notify_svc.notify(notify_svc.client_users(req.client_org), self.request.user,
                          Notification.Kind.REQUEST,
                          f'Connect {req.provider.name} requested', req.message, CLIENT_UPDATES_URL)

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.status in (
            ConnectionRequest.Status.CONNECTED,
            ConnectionRequest.Status.DECLINED,
        ) and instance.resolved_at is None:
            instance.resolved_at = timezone.now()
            instance.save(update_fields=['resolved_at'])
        if instance.requested_by:
            notify_svc.notify([instance.requested_by], self.request.user,
                              Notification.Kind.REQUEST,
                              f'{instance.provider.name} request {instance.status}',
                              '', STAFF_MESSAGES_URL)