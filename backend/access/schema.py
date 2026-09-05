"""drf-spectacular extension so API-key auth shows up in the OpenAPI docs."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class ApiKeyScheme(OpenApiAuthenticationExtension):
    target_class = 'access.authentication.ApiKeyAuthentication'
    name = 'ApiKeyAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Machine access. Send: `ApiKey hub_xxxxxxxx`',
        }
