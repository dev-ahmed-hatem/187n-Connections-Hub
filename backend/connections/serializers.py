from rest_framework import serializers

from providers.serializers import ProviderSerializer

from .models import Connection


class ConnectionSerializer(serializers.ModelSerializer):
    provider = ProviderSerializer(read_only=True)
    client_org_name = serializers.CharField(source='client_org.name', read_only=True)

    class Meta:
        model = Connection
        fields = [
            'id', 'client_org', 'client_org_name', 'provider',
            'external_account_id', 'display_name', 'status',
            'last_checked', 'created_at', 'updated_at',
        ]
