from django.contrib import admin

from .models import Announcement, ConnectionRequest, Note


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'audience', 'severity', 'active', 'created_at')
    list_filter = ('audience', 'severity', 'active')


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'client_org', 'type', 'status', 'created_at')
    list_filter = ('type', 'status')


@admin.register(ConnectionRequest)
class ConnectionRequestAdmin(admin.ModelAdmin):
    list_display = ('provider', 'client_org', 'status', 'requested_by', 'created_at')
    list_filter = ('status', 'provider')
