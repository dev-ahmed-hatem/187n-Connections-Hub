"""Connection lifecycle helpers shared by the connect flow and the access API."""

import secrets

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from providers.adapters import get_adapter

from .models import Connection, OAuthState, TokenSet


def generate_state() -> str:
    return secrets.token_urlsafe(24)


def _callback_url() -> str:
    return settings.BACKEND_BASE_URL.rstrip('/') + reverse('connections:callback')


def start_connection(client_org, provider, created_by=None, params=None) -> str:
    """Create an OAuth state and return the provider authorize URL."""
    params = params or {}
    state = generate_state()
    OAuthState.objects.create(
        state=state, client_org=client_org, provider=provider,
        created_by=created_by, meta=params,
    )
    adapter = get_adapter(provider)
    return adapter.authorize_url(state, _callback_url(), params)


def complete_connection(state: str, code: str) -> Connection:
    """Exchange the code, create/update the connection + encrypted tokens."""
    oauth_state = OAuthState.objects.select_related('client_org', 'provider').get(state=state)
    provider = oauth_state.provider
    adapter = get_adapter(provider)
    # Real providers need the exact redirect_uri at token-exchange time.
    exchange_params = {**(oauth_state.meta or {}), 'redirect_uri': _callback_url()}
    result = adapter.exchange_code(code, state, exchange_params)

    connection, _ = Connection.objects.update_or_create(
        client_org=oauth_state.client_org,
        provider=provider,
        defaults={
            'external_account_id': result.get('external_account_id', ''),
            'display_name': result.get('meta', {}).get('account_name', provider.name),
            'status': Connection.Status.CONNECTED,
            'meta': result.get('meta', {}),
            'last_checked': timezone.now(),
        },
    )

    expires_at = timezone.now() + timezone.timedelta(seconds=result.get('expires_in', 3600))
    TokenSet.objects.update_or_create(
        connection=connection,
        defaults={
            'enc_refresh_token': result.get('refresh_token', ''),
            'enc_access_token': result.get('access_token', ''),
            'access_expires_at': expires_at,
        },
    )

    oauth_state.delete()

    # Resolve any pending connection requests for this org+provider.
    from portal.models import ConnectionRequest
    ConnectionRequest.objects.filter(
        client_org=connection.client_org,
        provider=provider,
        status=ConnectionRequest.Status.PENDING,
    ).update(status=ConnectionRequest.Status.CONNECTED, resolved_at=timezone.now())

    return connection


def get_valid_access_token(connection: Connection) -> str:
    """Return a fresh access token, refreshing via the adapter if needed."""
    tokens = connection.tokens
    if tokens.is_access_expired and tokens.enc_refresh_token:
        adapter = get_adapter(connection.provider)
        refreshed = adapter.refresh(tokens.enc_refresh_token)
        tokens.enc_access_token = refreshed.get('access_token', '')
        tokens.access_expires_at = timezone.now() + timezone.timedelta(
            seconds=refreshed.get('expires_in', 3600)
        )
        tokens.save(update_fields=['enc_access_token', 'access_expires_at', 'updated_at'])
        connection.last_checked = timezone.now()
        connection.save(update_fields=['last_checked', 'updated_at'])
    return tokens.enc_access_token
