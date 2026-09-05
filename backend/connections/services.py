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

    now = timezone.now()
    expires_at = now + timezone.timedelta(seconds=result.get('expires_in', 3600))

    # One OAuth consent can expose several accounts — create a connection per
    # account, each with its own TokenSet (the shared grant token is copied on).
    enum_meta = {**result.get('meta', {}),
                 'external_account_id': result.get('external_account_id', '')}
    accounts = adapter.list_accounts(result.get('access_token', ''), enum_meta)
    connections = []
    for acct in accounts:
        connection, _ = Connection.objects.update_or_create(
            client_org=oauth_state.client_org,
            provider=provider,
            external_account_id=acct.get('external_account_id', ''),
            defaults={
                'display_name': acct.get('display_name') or provider.name,
                'status': Connection.Status.CONNECTED,
                'meta': acct.get('meta', {}),
                'last_checked': now,
            },
        )
        TokenSet.objects.update_or_create(
            connection=connection,
            defaults={
                'enc_refresh_token': result.get('refresh_token', ''),
                'enc_access_token': result.get('access_token', ''),
                'access_expires_at': expires_at,
            },
        )
        connections.append(connection)

    oauth_state.delete()

    # Resolve any pending connection requests for this org+provider.
    from portal.models import ConnectionRequest
    ConnectionRequest.objects.filter(
        client_org=oauth_state.client_org,
        provider=provider,
        status=ConnectionRequest.Status.PENDING,
    ).update(status=ConnectionRequest.Status.CONNECTED, resolved_at=now)

    return connections[0] if connections else None


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
