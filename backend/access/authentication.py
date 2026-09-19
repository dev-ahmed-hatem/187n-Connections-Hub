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

        # A project key must never inherit its owner's administrative privileges.
        import re
        if not re.fullmatch(r'/api/access/clients/[0-9]+/(?:connections|[a-z0-9-]+/(?:data|token))', request.path):
            raise exceptions.AuthenticationFailed('Project keys are restricted to the data access API.')
        raw = parts[1]
        try:
            consumer = Consumer.objects.select_related('owner').get(
                api_key_hash=hash_api_key(raw), active=True
            )
        except Consumer.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid or inactive API key.')

        # request.user just needs to be an authenticated user; access is enforced
        # via request.auth (the project) in has_access.
        principal = consumer.owner or consumer.members.filter(is_active=True).first()
        if principal is None or not principal.is_active:
            raise exceptions.AuthenticationFailed('Project has no active user.')

        return (principal, consumer)
