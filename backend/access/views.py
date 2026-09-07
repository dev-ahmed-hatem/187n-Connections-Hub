from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.pagination import CustomPageNumberPagination
from authentication.permissions import IsAdminRole, IsDeveloperRole
from connections.models import Connection
from connections.services import get_valid_access_token
from portal.models import Notification
from portal.notifications import notify
from providers.adapters import get_adapter
from providers.models import Provider
from users.models import ClientOrg

from .models import AuditLog, Consumer, ProjectAccessRequest
from .serializers import (
    AuditLogSerializer,
    ConsumerSerializer,
    ProjectAccessRequestSerializer,
)
from .services import has_access, write_audit
from .throttling import ConsumerRateThrottle

User = get_user_model()


class ConsumerViewSet(viewsets.ModelViewSet):
    """Projects. Admins create & assign (client + members); developers see and use
    the projects they're a member of. Raw API key is returned once on create/rotate."""

    serializer_class = ConsumerSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminRole()]
        return [IsDeveloperRole()]

    def get_queryset(self):
        user = self.request.user
        qs = Consumer.objects.select_related('client_org').prefetch_related('members')
        if user.is_admin_role:
            return qs
        return qs.filter(members=user)

    def create(self, request, *args, **kwargs):
        name = request.data.get('name')
        client_org = request.data.get('client_org')
        if not name or not client_org:
            return Response({'detail': 'name and client_org are required.'}, status=400)
        org = get_object_or_404(ClientOrg, id=client_org)
        consumer, raw_key = Consumer.create_with_key(name=name, client_org=org, owner=request.user)
        members = request.data.get('members') or []
        if members:
            consumer.members.set(User.objects.filter(id__in=members))
        data = ConsumerSerializer(consumer).data
        data['api_key'] = raw_key  # shown once
        return Response(data, status=status.HTTP_201_CREATED)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    @action(detail=True, methods=['post'], url_path='rotate-key')
    def rotate_key(self, request, pk=None):
        consumer = self.get_object()  # dev limited to member projects by get_queryset
        raw_key = consumer.rotate_key()
        data = ConsumerSerializer(consumer).data
        data['api_key'] = raw_key
        return Response(data)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    @action(detail=True, methods=['get'])
    def access(self, request, pk=None):
        """This project's client + its connected platforms/accounts."""
        consumer = self.get_object()
        org = consumer.client_org
        by_provider = {}
        if org:
            for c in Connection.objects.filter(client_org=org).select_related('provider'):
                by_provider.setdefault(c.provider_id, []).append(c)
        platforms = []
        for provider in Provider.objects.filter(is_active=True):
            accounts = [{
                'connection_id': c.id,
                'external_account_id': c.external_account_id,
                'display_name': c.display_name,
                'status': c.status,
            } for c in by_provider.get(provider.id, [])]
            platforms.append({
                'provider': {'id': provider.id, 'slug': provider.slug, 'name': provider.name,
                             'short_code': provider.short_code, 'color': provider.color},
                'accounts': accounts,
            })
        return Response({
            'consumer': consumer.id, 'consumer_name': consumer.name,
            'client_org': org.id if org else None,
            'client_org_name': org.name if org else None,
            'platforms': platforms,
        })

    @extend_schema(responses=OpenApiTypes.OBJECT)
    @action(detail=False, methods=['get'])
    def requestable(self, request):
        """Active projects the current developer is not yet a member of."""
        qs = Consumer.objects.filter(active=True).exclude(
            members=request.user).select_related('client_org')
        return Response([
            {'id': c.id, 'name': c.name,
             'client_org_name': c.client_org.name if c.client_org else None}
            for c in qs
        ])


class ProjectAccessRequestViewSet(viewsets.ModelViewSet):
    """Developers request to join a project; admins approve (adds them as a member) or deny."""

    serializer_class = ProjectAccessRequestSerializer
    permission_classes = [IsDeveloperRole]

    def get_queryset(self):
        user = self.request.user
        qs = ProjectAccessRequest.objects.select_related(
            'consumer', 'consumer__client_org', 'requested_by')
        if user.is_admin_role:
            return qs
        return qs.filter(requested_by=user)

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user,
                        status=ProjectAccessRequest.Status.PENDING)

    def _decide(self, request, pk, status_value, add_member):
        req = self.get_object()
        if req.status != ProjectAccessRequest.Status.PENDING:
            return Response({'detail': 'This request was already decided.'}, status=400)
        if add_member and req.requested_by:
            req.consumer.members.add(req.requested_by)
        req.status = status_value
        req.decided_by = request.user
        req.decided_at = timezone.now()
        req.save(update_fields=['status', 'decided_by', 'decided_at'])
        if req.requested_by:
            notify([req.requested_by], request.user, Notification.Kind.REQUEST,
                   f'Project access {status_value}: {req.consumer.name}', '', '/dev/projects')
        return Response(ProjectAccessRequestSerializer(req).data)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    @action(detail=True, methods=['post'], permission_classes=[IsAdminRole])
    def approve(self, request, pk=None):
        return self._decide(request, pk, ProjectAccessRequest.Status.APPROVED, add_member=True)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    @action(detail=True, methods=['post'], permission_classes=[IsAdminRole])
    def deny(self, request, pk=None):
        return self._decide(request, pk, ProjectAccessRequest.Status.DENIED, add_member=False)


class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsDeveloperRole]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        qs = AuditLog.objects.select_related('client_org', 'provider')
        p = self.request.query_params
        if p.get('client_org'):
            qs = qs.filter(client_org_id=p['client_org'])
        if p.get('status'):
            qs = qs.filter(status=p['status'])
        if p.get('action'):
            qs = qs.filter(action=p['action'])
        if p.get('actor'):
            qs = qs.filter(actor_label__icontains=p['actor'])
        return qs


# --- Access API (data-proxy / token-broker) -------------------------------

class _AccessBase(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_targets(self, org_id, provider_slug):
        org = get_object_or_404(ClientOrg, id=org_id)
        provider = get_object_or_404(Provider, slug=provider_slug, is_active=True)
        return org, provider

    def resolve_connection(self, org, provider, account_id=None):
        """Return (connection, error_response). Picks the account when there's
        one; requires account_id when several are connected."""
        conns = list(Connection.objects.filter(
            client_org=org, provider=provider, status=Connection.Status.CONNECTED,
        ).select_related('provider', 'credential'))
        if not conns:
            return None, Response(
                {'detail': 'Provider is not connected for this client.'}, status=409)
        if account_id:
            match = next((c for c in conns if c.external_account_id == account_id), None)
            if not match:
                return None, Response(
                    {'detail': f'No connected account "{account_id}" for this provider.'},
                    status=404)
            return match, None
        if len(conns) == 1:
            return conns[0], None
        return None, Response({
            'detail': 'Multiple accounts connected; specify account_id.',
            'accounts': [c.external_account_id for c in conns],
        }, status=400)


@extend_schema(responses=OpenApiTypes.OBJECT)
class AccessConnectionsView(_AccessBase):
    """List a client's connected accounts per provider (discovery)."""

    def get(self, request, org_id):
        org = get_object_or_404(ClientOrg, id=org_id)
        by_provider = {}
        for c in Connection.objects.filter(client_org=org).select_related('provider'):
            by_provider.setdefault(c.provider_id, []).append(c)
        items = []
        for provider in Provider.objects.filter(is_active=True):
            accounts = [{
                'external_account_id': c.external_account_id,
                'display_name': c.display_name,
                'status': c.status,
            } for c in by_provider.get(provider.id, [])]
            items.append({
                'provider': provider.slug,
                'provider_name': provider.name,
                'accounts': accounts,
            })
        return Response({'client_org': org.id, 'connections': items})


@extend_schema(responses=OpenApiTypes.OBJECT)
class AccessDataView(_AccessBase):
    """Data-proxy: the hub calls the provider and returns clean data."""

    throttle_classes = [ConsumerRateThrottle]

    def get(self, request, org_id, provider_slug):
        org, provider = self.get_targets(org_id, provider_slug)
        if not has_access(request, org, provider):
            write_audit(request, 'data', org, provider, status='denied')
            return Response({'detail': 'No project grants access to this client.'}, status=403)

        connection, err = self.resolve_connection(
            org, provider, request.query_params.get('account_id'))
        if err is not None:
            write_audit(request, 'data', org, provider, status='error',
                        meta={'reason': 'account'})
            return err

        access_token = get_valid_access_token(connection)
        adapter = get_adapter(provider)
        resource = request.query_params.get('resource', 'stats')
        params = request.query_params.dict()
        meta = dict(connection.meta or {})
        meta['external_account_id'] = connection.external_account_id
        data = adapter.fetch_data(access_token, resource, params, meta)
        write_audit(request, 'data', org, provider, meta={'resource': resource})
        return Response(data)


@extend_schema(responses=OpenApiTypes.OBJECT)
class AccessTokenView(_AccessBase):
    """Token-broker: return a short-lived access token for direct provider calls."""

    throttle_classes = [ConsumerRateThrottle]

    def post(self, request, org_id, provider_slug):
        org, provider = self.get_targets(org_id, provider_slug)
        if not has_access(request, org, provider):
            write_audit(request, 'token', org, provider, status='denied')
            return Response({'detail': 'No project grants access to this client.'}, status=403)

        connection, err = self.resolve_connection(
            org, provider, request.data.get('account_id'))
        if err is not None:
            write_audit(request, 'token', org, provider, status='error',
                        meta={'reason': 'account'})
            return err

        access_token = get_valid_access_token(connection)
        write_audit(request, 'token', org, provider)
        payload = {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': settings.ACCESS_TOKEN_TTL_SECONDS,
            'provider': provider.slug,
            'external_account_id': connection.external_account_id,
        }
        if provider.slug == 'google-ads':
            payload['login_customer_id'] = (connection.meta or {}).get('login_customer_id')
        return Response(payload)


@extend_schema(responses=OpenApiTypes.OBJECT)
class AccessRequestConnectionView(_AccessBase):
    """A developer asks a client to connect a provider (surfaces in the portal)."""

    def post(self, request, org_id, provider_slug):
        org, provider = self.get_targets(org_id, provider_slug)
        from portal.models import ConnectionRequest, Note
        message = request.data.get('message', '')
        req = ConnectionRequest.objects.create(
            requested_by=request.user if request.user.is_authenticated else None,
            client_org=org,
            provider=provider,
            message=message,
        )
        Note.objects.create(
            client_org=org,
            type=Note.Type.BLOCKER,
            title=f'Connect {provider.name}',
            body=message or f'A developer requested a {provider.name} connection.',
            status=Note.Status.OPEN,
            created_by=request.user if request.user.is_authenticated else None,
        )
        write_audit(request, 'request_connection', org, provider)
        return Response({'id': req.id, 'status': req.status}, status=status.HTTP_201_CREATED)
