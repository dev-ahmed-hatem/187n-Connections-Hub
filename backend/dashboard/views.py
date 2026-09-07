from django.db.models import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from access.models import AuditLog, Consumer, ProjectAccessRequest
from connections.models import Connection
from portal.models import ConnectionRequest, Note
from providers.models import Provider
from users.models import ClientOrg


def _status_counts(qs):
    counts = {row['status']: row['n'] for row in qs.values('status').annotate(n=Count('id'))}
    return counts


@extend_schema(responses=OpenApiTypes.OBJECT)
class DashboardView(APIView):
    """Role-appropriate summary for the landing dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_admin_role:
            return Response(self._admin())
        if user.is_developer_role:
            return Response(self._developer(user))
        return Response(self._client(user))

    def _admin(self):
        recent = AuditLog.objects.all()[:8]
        return {
            'role': 'admin',
            'clients': ClientOrg.objects.count(),
            'providers_live': Provider.objects.filter(is_mock=False, is_active=True).count(),
            'providers_mock': Provider.objects.filter(is_mock=True, is_active=True).count(),
            'projects': Consumer.objects.count(),
            'pending_requests': ProjectAccessRequest.objects.filter(
                status=ProjectAccessRequest.Status.PENDING).count(),
            'connections_by_status': _status_counts(Connection.objects.all()),
            'recent_audit': [
                {'actor': a.actor_label, 'action': a.action, 'status': a.status,
                 'provider': a.provider.slug if a.provider else None,
                 'created_at': a.created_at}
                for a in recent
            ],
        }

    def _developer(self, user):
        return {
            'role': 'developer',
            'my_projects': Consumer.objects.filter(members=user).count(),
            'my_pending_requests': ProjectAccessRequest.objects.filter(
                requested_by=user, status=ProjectAccessRequest.Status.PENDING).count(),
            'projects': list(
                Consumer.objects.filter(members=user).values('id', 'name', 'active')),
        }

    def _client(self, user):
        org = user.client_org
        conns = Connection.objects.filter(client_org=org) if org else Connection.objects.none()
        return {
            'role': 'client',
            'client_org_name': org.name if org else None,
            'total_providers': Provider.objects.filter(is_active=True).count(),
            'connections_by_status': _status_counts(conns),
            'open_blockers': Note.objects.filter(
                client_org=org, status=Note.Status.OPEN,
                type=Note.Type.BLOCKER).count() if org else 0,
            'pending_requests': ConnectionRequest.objects.filter(
                client_org=org, status=ConnectionRequest.Status.PENDING).count() if org else 0,
        }
