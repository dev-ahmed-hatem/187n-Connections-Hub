from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.pagination import CustomPageNumberPagination
from authentication.permissions import IsAdminRole, IsDeveloperRole
from connections.models import Connection
from connections.services import get_valid_access_token
from providers.adapters import get_adapter
from providers.models import Provider
from users.models import ClientOrg

from .models import AuditLog, Consumer, Grant, GrantRequest
from .serializers import (
    AuditLogSerializer,
    ConsumerSerializer,
    GrantRequestSerializer,
    GrantSerializer,
)
from .services import actor_info, has_access, write_audit
from .throttling import ConsumerRateThrottle


class ConsumerViewSet(viewsets.ModelViewSet):
    """Developer project identities. Devs manage their own; admins see all.

    The raw API key is returned exactly once, on creation.
    """

    serializer_class = ConsumerSerializer
    permission_classes = [IsDeveloperRole]

    def get_queryset(self):
        user = self.request.user
        qs = Consumer.objects.select_related('owner')
        if user.is_admin_role:
            return qs
        return qs.filter(owner=user)

    def create(self, request, *args, **kwargs):
        name = request.data.get('name')
        if not name:
            return Response({'detail': 'name is required.'}, status=400)
        consumer, raw_key = Consumer.create_with_key(name=name, owner=request.user)
        data = ConsumerSerializer(consumer).data
        data['api_key'] = raw_key  # shown once
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='rotate-key')
    def rotate_key(self, request, pk=None):
        consumer = self.get_object()
        raw_key = consumer.rotate_key()
        data = ConsumerSerializer(consumer).data
        data['api_key'] = raw_key  # shown once; old key now invalid
        return Response(data)

    @action(detail=True, methods=['get'])
    def access(self, request, pk=None):
        """This project's granted clients/platforms, each with live connection status."""
        consumer = self.get_object()
        grants = Grant.objects.filter(consumer=consumer, active=True).select_related(
            'client_org', 'provider')
        conns = {
            (c.client_org_id, c.provider_id): c
            for c in Connection.objects.filter(
                client_org__in=[g.client_org_id for g in grants]).select_related('provider')
        }
        items = []
        for g in grants:
            conn = conns.get((g.client_org_id, g.provider_id))
            items.append({
                'grant_id': g.id,
                'client_org': g.client_org_id,
                'client_org_name': g.client_org.name,
                'provider': g.provider.slug,
                'provider_name': g.provider.name,
                'scopes': g.scopes,
                'connection_status': conn.status if conn else 'not_connected',
            })
        return Response({'consumer': consumer.id, 'consumer_name': consumer.name, 'access': items})


class GrantViewSet(viewsets.ModelViewSet):
    """The access gate. Only admins create/revoke grants; devs may read theirs."""

    serializer_class = GrantSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsDeveloperRole()]
        return [IsAdminRole()]

    def get_queryset(self):
        user = self.request.user
        qs = Grant.objects.select_related('consumer', 'client_org', 'provider')
        consumer_id = self.request.query_params.get('consumer')
        if consumer_id:
            qs = qs.filter(consumer_id=consumer_id)
        if user.is_admin_role:
            return qs
        return qs.filter(consumer__owner=user)

    def perform_create(self, serializer):
        serializer.save(granted_by=self.request.user)


class GrantRequestViewSet(viewsets.ModelViewSet):
    """Self-serve access requests. Developers create/list their own; admins
    approve (which creates the Grant) or deny."""

    serializer_class = GrantRequestSerializer
    permission_classes = [IsDeveloperRole]

    def get_queryset(self):
        user = self.request.user
        qs = GrantRequest.objects.select_related(
            'consumer', 'client_org', 'provider', 'requested_by'
        )
        if user.is_admin_role:
            return qs
        return qs.filter(consumer__owner=user)

    def perform_create(self, serializer):
        consumer = serializer.validated_data['consumer']
        user = self.request.user
        if not user.is_admin_role and consumer.owner_id != user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You can only request access for your own projects.')
        serializer.save(requested_by=user, status=GrantRequest.Status.PENDING)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminRole])
    def approve(self, request, pk=None):
        gr = self.get_object()
        if gr.status != GrantRequest.Status.PENDING:
            return Response({'detail': 'This request was already decided.'}, status=400)
        Grant.objects.update_or_create(
            consumer=gr.consumer, client_org=gr.client_org, provider=gr.provider,
            defaults={'active': True, 'scopes': gr.scopes or [], 'granted_by': request.user},
        )
        gr.status = GrantRequest.Status.APPROVED
        gr.decided_by = request.user
        gr.decided_at = timezone.now()
        gr.save(update_fields=['status', 'decided_by', 'decided_at'])
        return Response(GrantRequestSerializer(gr).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminRole])
    def deny(self, request, pk=None):
        gr = self.get_object()
        if gr.status != GrantRequest.Status.PENDING:
            return Response({'detail': 'This request was already decided.'}, status=400)
        gr.status = GrantRequest.Status.DENIED
        gr.decided_by = request.user
        gr.decided_at = timezone.now()
        gr.save(update_fields=['status', 'decided_by', 'decided_at'])
        return Response(GrantRequestSerializer(gr).data)


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

    def get_connection(self, org, provider):
        return Connection.objects.filter(
            client_org=org, provider=provider
        ).select_related('provider', 'tokens').first()


class AccessConnectionsView(_AccessBase):
    """List a client's connection statuses (discovery)."""

    def get(self, request, org_id):
        org = get_object_or_404(ClientOrg, id=org_id)
        conns = {
            c.provider_id: c
            for c in Connection.objects.filter(client_org=org).select_related('provider')
        }
        items = []
        for provider in Provider.objects.filter(is_active=True):
            c = conns.get(provider.id)
            items.append({
                'provider': provider.slug,
                'provider_name': provider.name,
                'status': c.status if c else 'not_connected',
                'external_account_id': c.external_account_id if c else None,
            })
        return Response({'client_org': org.id, 'connections': items})


class AccessDataView(_AccessBase):
    """Data-proxy: the hub calls the provider and returns clean data."""

    throttle_classes = [ConsumerRateThrottle]

    def get(self, request, org_id, provider_slug):
        org, provider = self.get_targets(org_id, provider_slug)
        if not has_access(request, org, provider, scope='read'):
            write_audit(request, 'data', org, provider, status='denied')
            return Response({'detail': 'No active grant (read) for this client/provider.'},
                            status=403)

        connection = self.get_connection(org, provider)
        if not connection or connection.status != Connection.Status.CONNECTED:
            write_audit(request, 'data', org, provider, status='error',
                        meta={'reason': 'not_connected'})
            return Response({'detail': 'Provider is not connected for this client.'}, status=409)

        access_token = get_valid_access_token(connection)
        adapter = get_adapter(provider)
        resource = request.query_params.get('resource', 'stats')
        params = request.query_params.dict()
        meta = dict(connection.meta or {})
        meta['external_account_id'] = connection.external_account_id
        data = adapter.fetch_data(access_token, resource, params, meta)
        write_audit(request, 'data', org, provider, meta={'resource': resource})
        return Response(data)


class AccessTokenView(_AccessBase):
    """Token-broker: return a short-lived access token for direct provider calls."""

    throttle_classes = [ConsumerRateThrottle]

    def post(self, request, org_id, provider_slug):
        org, provider = self.get_targets(org_id, provider_slug)
        if not has_access(request, org, provider, scope='token'):
            write_audit(request, 'token', org, provider, status='denied')
            return Response({'detail': 'No active grant (token) for this client/provider.'},
                            status=403)

        connection = self.get_connection(org, provider)
        if not connection or connection.status != Connection.Status.CONNECTED:
            write_audit(request, 'token', org, provider, status='error',
                        meta={'reason': 'not_connected'})
            return Response({'detail': 'Provider is not connected for this client.'}, status=409)

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
