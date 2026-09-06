from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from providers.adapters import get_adapter
from providers.models import Provider
from providers.serializers import ProviderSerializer
from users.models import ClientOrg

from .models import Connection
from .serializers import ConnectionSerializer
from .services import complete_connection, get_valid_access_token, start_connection


def resolve_client_org(request):
    """Client users act on their own org; admins/devs pass ?client_org=<id>."""
    user = request.user
    if user.is_client_role and user.client_org_id:
        return user.client_org
    org_id = request.query_params.get('client_org') or request.data.get('client_org')
    if not org_id:
        return None
    return get_object_or_404(ClientOrg, id=org_id)


class ConnectionOverviewView(APIView):
    """Per-provider connection status for a client org (drives the status cards)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        org = resolve_client_org(request)
        if org is None:
            return Response({'detail': 'client_org is required.'}, status=400)

        by_provider = {}
        for c in Connection.objects.filter(client_org=org).select_related('provider'):
            by_provider.setdefault(c.provider_id, []).append(c)
        items = []
        for provider in Provider.objects.filter(is_active=True):
            accounts = [{
                'connection_id': c.id,
                'external_account_id': c.external_account_id,
                'display_name': c.display_name,
                'status': c.status,
                'last_checked': c.last_checked,
            } for c in by_provider.get(provider.id, [])]
            items.append({
                'provider': ProviderSerializer(provider).data,
                'accounts': accounts,
            })
        return Response({'client_org': org.id, 'client_org_name': org.name, 'items': items})


class ConnectionStartView(APIView):
    """Begin connecting a provider — returns the (mock) authorize URL."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        org = resolve_client_org(request)
        if org is None:
            return Response({'detail': 'client_org is required.'}, status=400)

        provider_ref = request.data.get('provider')
        if not provider_ref:
            return Response({'detail': 'provider is required.'}, status=400)
        provider = Provider.objects.filter(slug=provider_ref, is_active=True).first() \
            or get_object_or_404(Provider, id=provider_ref, is_active=True)

        params = request.data.get('params') or {}
        # Shopify (and any shop-scoped provider) needs the store domain up front.
        if provider.slug == 'shopify' and not params.get('shop'):
            return Response({'detail': 'shop is required for Shopify.'}, status=400)

        try:
            authorize_url = start_connection(org, provider, created_by=request.user, params=params)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=400)
        return Response({'authorize_url': authorize_url})


class ConnectionCallbackView(APIView):
    """OAuth redirect target. Completes the connection then bounces to the frontend."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        error = request.query_params.get('error')
        state = request.query_params.get('state')
        frontend = settings.FRONTEND_BASE_URL.rstrip('/')
        if error:
            return HttpResponseRedirect(f'{frontend}/client/connections?error={error}')
        code = request.query_params.get('code')
        if not (code and state):
            return HttpResponseRedirect(f'{frontend}/client/connections?error=invalid_callback')
        try:
            connection = complete_connection(state, code, request.query_params.dict())
        except ValueError:
            return HttpResponseRedirect(
                f'{frontend}/client/connections?error=verification_failed')
        except Exception:
            return HttpResponseRedirect(f'{frontend}/client/connections?error=exchange_failed')
        return HttpResponseRedirect(
            f'{frontend}/client/connections?connected={connection.provider.slug}'
        )


class ConnectionTestView(APIView):
    """Verify a connection by exercising the adapter; update status accordingly."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        conn = get_object_or_404(Connection.objects.select_related('provider'), id=pk)
        user = request.user
        if user.is_client_role and conn.client_org_id != user.client_org_id:
            return Response({'detail': 'Not allowed.'}, status=403)
        try:
            token = get_valid_access_token(conn)
            adapter = get_adapter(conn.provider)
            meta = dict(conn.meta or {})
            meta['external_account_id'] = conn.external_account_id
            adapter.fetch_data(token, 'stats', {}, meta)
            conn.status = Connection.Status.CONNECTED
            ok = True
        except Exception:
            conn.status = Connection.Status.NEEDS_RECONNECT
            ok = False
        conn.last_checked = timezone.now()
        conn.save(update_fields=['status', 'last_checked', 'updated_at'])
        return Response({'ok': ok, 'status': conn.status})


class ConnectionDeleteView(generics.DestroyAPIView):
    """Delete a connected account. Clients may delete their own org's; admins any."""

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        conn = get_object_or_404(Connection, id=self.kwargs['pk'])
        user = self.request.user
        if user.is_client_role and conn.client_org_id != user.client_org_id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Not allowed.')
        return conn


class ConnectionListView(generics.ListAPIView):
    """Raw connection rows for a client org."""

    serializer_class = ConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        org = resolve_client_org(self.request)
        if org is None:
            return Connection.objects.none()
        return Connection.objects.filter(client_org=org).select_related('provider', 'client_org')
