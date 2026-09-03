from rest_framework import serializers

from .models import AuditLog, Consumer, Grant


class ConsumerSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Consumer
        fields = [
            'id', 'name', 'owner', 'owner_username',
            'api_key_prefix', 'active', 'created_at',
        ]
        read_only_fields = ['owner', 'api_key_prefix', 'created_at']


class GrantSerializer(serializers.ModelSerializer):
    consumer_name = serializers.CharField(source='consumer.name', read_only=True)
    client_org_name = serializers.CharField(source='client_org.name', read_only=True)
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    provider_slug = serializers.CharField(source='provider.slug', read_only=True)

    class Meta:
        model = Grant
        fields = [
            'id', 'consumer', 'consumer_name', 'client_org', 'client_org_name',
            'provider', 'provider_name', 'provider_slug', 'scopes', 'active',
            'granted_by', 'created_at',
        ]
        read_only_fields = ['granted_by', 'created_at']


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
