"""Shared base for real (non-mock) provider adapters."""

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .base import ProviderAdapter

DEFAULT_TIMEOUT = 20
# Shopify offline tokens don't expire; store a far-future expiry so the vault
# never tries to refresh them.
NON_EXPIRING_SECONDS = 10 * 365 * 24 * 3600


class RealAdapter(ProviderAdapter):
    #: config keys that must be present in settings.PROVIDER_CONFIG[slug]
    required_config: tuple[str, ...] = ()

    def __init__(self, provider):
        super().__init__(provider)
        self.config = settings.PROVIDER_CONFIG.get(provider.slug, {})
        missing = [k for k in self.required_config if not self.config.get(k)]
        if missing:
            raise ImproperlyConfigured(
                f'Provider "{provider.slug}" is live but missing config: {missing}. '
                f'Set them in .env, or keep the provider on is_mock=True.'
            )

    def _get(self, url, **kwargs):
        resp = requests.get(url, timeout=DEFAULT_TIMEOUT, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _post(self, url, **kwargs):
        resp = requests.post(url, timeout=DEFAULT_TIMEOUT, **kwargs)
        resp.raise_for_status()
        return resp.json()
