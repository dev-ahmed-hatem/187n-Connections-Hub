"""API-key authentication for machine/project (Consumer) access.

    Authorization: ApiKey hub_xxxxxxxx

On success, `request.user` is the consumer's owner (so IsAuthenticated passes)
and `request.auth` is the Consumer instance (so views can enforce grants).
"""

from rest_framework import authentication, exceptions

from .models import Consumer, hash_api_key


class ApiKeyAuthentication(authentication.BaseAuthentication):
    keyword = 'ApiKey'

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode('utf-8')
        if not header:
            return None
        parts = header.split()
        if parts[0] != self.keyword:
            return None
        if len(parts) != 2:
            raise exceptions.AuthenticationFailed('Invalid ApiKey header.')

        raw = parts[1]
        try:
            consumer = Consumer.objects.select_related('owner').get(
                api_key_hash=hash_api_key(raw), active=True
            )
        except Consumer.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid or inactive API key.')

        if not consumer.owner.is_active:
            raise exceptions.AuthenticationFailed('Consumer owner is inactive.')

        return (consumer.owner, consumer)
