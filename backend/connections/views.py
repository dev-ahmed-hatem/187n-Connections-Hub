from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from providers.models import Provider
from providers.serializers import ProviderSerializer
from users.models import ClientOrg

from .models import Connection
from .serializers import ConnectionSerializer
from .services import complete_connection, start_connection


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

        connections = {
            c.provider_id: c
            for c in Connection.objects.filter(client_org=org).select_related('provider')
        }
        items = []
        for provider in Provider.objects.filter(is_active=True):
            conn = connections.get(provider.id)
            items.append({
                'provider': ProviderSerializer(provider).data,
                'status': conn.status if conn else 'not_connected',
                'connection_id': conn.id if conn else None,
                'external_account_id': conn.external_account_id if conn else None,
                'display_name': conn.display_name if conn else None,
                'last_checked': conn.last_checked if conn else None,
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

        authorize_url = start_connection(org, provider, created_by=request.user)
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
            connection = complete_connection(state, code)
        except Exception:
            return HttpResponseRedirect(f'{frontend}/client/connections?error=exchange_failed')
        return HttpResponseRedirect(
            f'{frontend}/client/connections?connected={connection.provider.slug}'
        )


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
