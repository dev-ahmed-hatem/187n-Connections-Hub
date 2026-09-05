from django.apps import AppConfig


class ProvidersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'providers'

    def ready(self):
        # Register real adapters so non-mock providers resolve to them.
        from .adapters.registry import register_adapter
        from .adapters.google_ads import GoogleAdsAdapter
        from .adapters.meta_ads import MetaAdsAdapter
        from .adapters.shopify import ShopifyAdapter

        register_adapter('google-ads', GoogleAdsAdapter)
        register_adapter('meta-ads', MetaAdsAdapter)
        register_adapter('shopify', ShopifyAdapter)
