from rest_framework import serializers

from .models import AuditLog, Consumer, ProjectAccessRequest


class ConsumerSerializer(serializers.ModelSerializer):
    """A project."""

    client_org_name = serializers.CharField(source='client_org.name', read_only=True)
    member_usernames = serializers.SerializerMethodField()

    class Meta:
        model = Consumer
        fields = [
            'id', 'name', 'client_org', 'client_org_name', 'members', 'member_usernames',
            'api_key_prefix', 'active', 'created_at',
        ]
        read_only_fields = ['api_key_prefix', 'created_at']

    def get_member_usernames(self, obj):
        return [u.username for u in obj.members.all()]


class ProjectAccessRequestSerializer(serializers.ModelSerializer):
    consumer_name = serializers.CharField(source='consumer.name', read_only=True)
    client_org_name = serializers.CharField(source='consumer.client_org.name', read_only=True)
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)

    class Meta:
        model = ProjectAccessRequest
        fields = [
            'id', 'consumer', 'consumer_name', 'client_org_name', 'message',
            'status', 'requested_by', 'requested_by_username',
            'decided_by', 'decided_at', 'created_at',
        ]
        read_only_fields = ['status', 'requested_by', 'decided_by', 'decided_at', 'created_at']


class AuditLogSerializer(serializers.ModelSerializer):
    client_org_name = serializers.CharField(source='client_org.name', read_only=True)
    provider_slug = serializers.CharField(source='provider.slug', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'actor_type', 'actor_label', 'action',
            'client_org', 'client_org_name', 'provider', 'provider_slug',
            'status', 'meta', 'created_at',
        ]
