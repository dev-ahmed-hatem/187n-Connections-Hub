from rest_framework.throttling import SimpleRateThrottle

from .models import Consumer


class ConsumerRateThrottle(SimpleRateThrottle):
    """Throttle the Access API per API-key consumer. Human (JWT) callers are
    not throttled here."""

    scope = 'consumer'

    def get_cache_key(self, request, view):
        auth = getattr(request, 'auth', None)
        if isinstance(auth, Consumer):
            return self.cache_format % {'scope': self.scope, 'ident': auth.pk}
        return None
