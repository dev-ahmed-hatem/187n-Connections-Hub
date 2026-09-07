"""Fan-out helpers for in-app notifications."""

from django.contrib.auth import get_user_model

from .models import Notification

User = get_user_model()


def client_users(org):
    if not org:
        return []
    return list(User.objects.filter(client_org=org, role=User.Role.CLIENT, is_active=True))


def staff_users():
    return list(User.objects.filter(role=User.Role.ADMIN, is_active=True))


def all_client_users():
    return list(User.objects.filter(role=User.Role.CLIENT, is_active=True))


def all_users():
    return list(User.objects.filter(is_active=True))


def notify(recipients, actor, kind, title, body='', url=''):
    """Create a notification per recipient (skips the actor themselves)."""
    seen = set()
    rows = []
    for u in recipients:
        if not u or u.id in seen:
            continue
        if actor is not None and u.id == actor.id:
            continue
        seen.add(u.id)
        rows.append(Notification(recipient=u, actor=actor, kind=kind,
                                 title=title, body=body, url=url))
    if rows:
        Notification.objects.bulk_create(rows)
