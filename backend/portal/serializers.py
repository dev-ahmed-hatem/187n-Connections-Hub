from rest_framework import serializers

from .models import Announcement, ConnectionRequest, Note


class AnnouncementSerializer(serializers.ModelSerializer):
    client_org_name = serializers.CharField(source='client_org.name', read_only=True)

    class Meta:
        model = Announcement
        fields = [
            'id', 'audience', 'client_org', 'client_org_name', 'title', 'body',
            'severity', 'active', 'created_by', 'created_at',
        ]
        read_only_fields = ['created_by', 'created_at']


class NoteSerializer(serializers.ModelSerializer):
    client_org_name = serializers.CharField(source='client_org.name', read_only=True)

    class Meta:
        model = Note
        fields = [
            'id', 'client_org', 'client_org_name', 'connection', 'type',
            'title', 'body', 'status', 'created_by', 'created_at',
        ]
        read_only_fields = ['created_by', 'created_at']


class ConnectionRequestSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    provider_slug = serializers.CharField(source='provider.slug', read_only=True)
    client_org_name = serializers.CharField(source='client_org.name', read_only=True)
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)

    class Meta:
        model = ConnectionRequest
        fields = [
            'id', 'requested_by', 'requested_by_username', 'client_org', 'client_org_name',
            'provider', 'provider_name', 'provider_slug', 'message', 'status',
            'created_at', 'resolved_at',
        ]
        read_only_fields = ['requested_by', 'created_at', 'resolved_at']
