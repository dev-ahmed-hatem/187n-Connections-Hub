"""Access-control helpers shared by the Access API views."""

from .models import AuditLog, Consumer, Grant


def actor_info(request):
    """Return (actor_type, actor_label, consumer_or_none) for the caller."""
    auth = getattr(request, 'auth', None)
    if isinstance(auth, Consumer):
        return 'consumer', f'{auth.name} ({auth.api_key_prefix})', auth
    user = request.user
    return 'user', getattr(user, 'username', 'unknown'), None


def has_access(request, org, provider, scope=None) -> bool:
    """Consumers need an active grant covering `scope`; internal humans (dev/admin) pass.

    A grant with empty `scopes` means full access (backward compatible with
    seeded grants). Otherwise the requested `scope` must be listed.
    """
    _, _, consumer = actor_info(request)
    if consumer is not None:
        grant = Grant.objects.filter(
            consumer=consumer, client_org=org, provider=provider, active=True
        ).first()
        if grant is None:
            return False
        if scope and grant.scopes:
            return scope in grant.scopes
        return True
    user = request.user
    return bool(user and user.is_authenticated and (user.is_developer_role or user.is_admin_role))


def write_audit(request, action, org=None, provider=None, status='ok', meta=None):
    actor_type, actor_label, _ = actor_info(request)
    AuditLog.objects.create(
        actor_type=actor_type,
        actor_label=actor_label,
        action=action,
        client_org=org,
        provider=provider,
        status=status,
        meta=meta or {},
    )
