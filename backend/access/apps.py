from django.apps import AppConfig


class AccessConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'access'

    def ready(self):
        # Register the OpenAPI security scheme for API-key auth.
        from . import schema  # noqa: F401
