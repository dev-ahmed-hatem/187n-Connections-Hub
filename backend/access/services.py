"""Access-control helpers shared by the Access API views."""

from .models import AuditLog, Consumer


def actor_info(request):
    """Return (actor_type, actor_label, consumer_or_none) for the caller."""
    auth = getattr(request, 'auth', None)
    if isinstance(auth, Consumer):
        return 'consumer', f'{auth.name} ({auth.api_key_prefix})', auth
    user = request.user
    return 'user', getattr(user, 'username', 'unknown'), None


def has_access(request, org, provider=None) -> bool:
    """Project-centric: access is granted per client (all its connected platforms).

    - API-key project: allowed if the project is active and bound to this client.
    - Admin: always. Developer: allowed if a member of any project for this client.
    """
    _, _, consumer = actor_info(request)
    if consumer is not None:
        return bool(consumer.active and consumer.client_org_id == org.id)
    user = request.user
    if not (user and user.is_authenticated):
        return False
    if user.is_admin_role:
        return True
    if user.is_developer_role:
        return Consumer.objects.filter(client_org=org, members=user).exists()
    return False


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
