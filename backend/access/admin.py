from django.contrib import admin

from .models import AuditLog, Consumer, Grant, GrantRequest


@admin.register(Consumer)
class ConsumerAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'api_key_prefix', 'active', 'created_at')
    list_filter = ('active',)


@admin.register(Grant)
class GrantAdmin(admin.ModelAdmin):
    list_display = ('consumer', 'client_org', 'provider', 'active', 'created_at')
    list_filter = ('active', 'provider')


@admin.register(GrantRequest)
class GrantRequestAdmin(admin.ModelAdmin):
    list_display = ('consumer', 'client_org', 'provider', 'status', 'requested_by', 'created_at')
    list_filter = ('status', 'provider')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor_type', 'actor_label', 'action', 'client_org', 'provider', 'status')
    list_filter = ('action', 'status', 'actor_type')
    readonly_fields = [f.name for f in AuditLog._meta.fields]
