from django.contrib import admin

from .models import Connection, OAuthState, TokenSet


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ('client_org', 'provider', 'status', 'external_account_id', 'updated_at')
    list_filter = ('status', 'provider')
    search_fields = ('external_account_id', 'display_name')


@admin.register(TokenSet)
class TokenSetAdmin(admin.ModelAdmin):
    list_display = ('connection', 'access_expires_at', 'updated_at')


@admin.register(OAuthState)
class OAuthStateAdmin(admin.ModelAdmin):
    list_display = ('state', 'client_org', 'provider', 'created_at')
