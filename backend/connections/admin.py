from django.contrib import admin

from .models import Connection, OAuthState, ProviderCredential


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ('client_org', 'provider', 'status', 'external_account_id', 'credential', 'updated_at')
    list_filter = ('status', 'provider')
    search_fields = ('external_account_id', 'display_name')


@admin.register(ProviderCredential)
class ProviderCredentialAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_org', 'provider', 'access_expires_at', 'updated_at')
    list_filter = ('provider',)


@admin.register(OAuthState)
class OAuthStateAdmin(admin.ModelAdmin):
    list_display = ('state', 'client_org', 'provider', 'created_at')
