from django.db import models


class Provider(models.Model):
    """A third-party platform the hub can connect to (Google Ads, Meta, Shopify…).

    `is_mock` routes the provider through the built-in MockAdapter so the whole
    OAuth + data flow works locally without real credentials. Flip it off and
    register a real adapter (same interface) to go live.
    """

    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    # Short label + color for UI chips (e.g. "G" on blue).
    short_code = models.CharField(max_length=4, blank=True)
    color = models.CharField(max_length=16, blank=True)
    scopes = models.JSONField(default=list, blank=True)
    is_mock = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
