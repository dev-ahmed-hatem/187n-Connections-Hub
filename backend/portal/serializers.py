from rest_framework import serializers

from .models import Announcement, Comment, ConnectionRequest, Note, Notification


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


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_role = serializers.CharField(source='author.role', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'note', 'author', 'author_username', 'author_role', 'body', 'created_at']
        read_only_fields = ['author', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'actor', 'actor_username', 'kind', 'title', 'body',
                  'url', 'read', 'created_at']
        read_only_fields = fields


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
