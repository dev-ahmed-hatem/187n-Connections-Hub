from urllib.parse import urlencode

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from rest_framework import generics, permissions

from .adapters import get_adapter
from .models import Provider
from .serializers import ProviderSerializer


class ProviderListView(generics.ListAPIView):
    """List active providers (used across all portals)."""

    serializer_class = ProviderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Provider.objects.filter(is_active=True)


def mock_authorize(request):
    """A stand-in for a provider's OAuth consent screen (mock providers only).

    GET without ?allow=1 renders a consent page. Clicking "Allow" re-hits this
    view with allow=1, which mints a code and redirects to the connect callback.
    """
    slug = request.GET.get('provider')
    state = request.GET.get('state')
    redirect_uri = request.GET.get('redirect_uri')
    if not (slug and state and redirect_uri):
        return HttpResponseBadRequest('Missing provider, state or redirect_uri.')

    provider = get_object_or_404(Provider, slug=slug, is_active=True)
    if not provider.is_mock:
        return HttpResponseBadRequest('Mock consent is only available for mock providers.')

    if request.GET.get('allow') == '1':
        adapter = get_adapter(provider)
        code = adapter.make_code(state)
        sep = '&' if '?' in redirect_uri else '?'
        return HttpResponseRedirect(
            f'{redirect_uri}{sep}{urlencode({"code": code, "state": state})}'
        )

    if request.GET.get('deny') == '1':
        sep = '&' if '?' in redirect_uri else '?'
        return HttpResponseRedirect(
            f'{redirect_uri}{sep}{urlencode({"error": "access_denied", "state": state})}'
        )

    allow_url = f'{request.path}?{urlencode({"provider": slug, "state": state, "redirect_uri": redirect_uri, "allow": "1"})}'
    deny_url = f'{request.path}?{urlencode({"provider": slug, "state": state, "redirect_uri": redirect_uri, "deny": "1"})}'
    return render(request, 'providers/mock_authorize.html', {
        'provider': provider,
        'allow_url': allow_url,
        'deny_url': deny_url,
    })
