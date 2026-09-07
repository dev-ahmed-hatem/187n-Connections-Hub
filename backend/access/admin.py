from django.contrib import admin

from .models import AuditLog, Consumer, ProjectAccessRequest


@admin.register(Consumer)
class ConsumerAdmin(admin.ModelAdmin):
    list_display = ('name', 'client_org', 'api_key_prefix', 'active', 'created_at')
    list_filter = ('active', 'client_org')
    filter_horizontal = ('members',)


@admin.register(ProjectAccessRequest)
class ProjectAccessRequestAdmin(admin.ModelAdmin):
    list_display = ('consumer', 'requested_by', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor_type', 'actor_label', 'action', 'client_org', 'provider', 'status')
    list_filter = ('action', 'status', 'actor_type')
    readonly_fields = [f.name for f in AuditLog._meta.fields]
