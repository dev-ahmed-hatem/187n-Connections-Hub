from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ClientOrg

User = get_user_model()


class ClientOrgSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientOrg
        fields = ['id', 'name', 'slug', 'notes', 'created_at']
        read_only_fields = ['created_at']


class UserSerializer(serializers.ModelSerializer):
    client_org_name = serializers.CharField(source='client_org.name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'client_org', 'client_org_name', 'is_active',
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'client_org', 'password',
        ]

    def validate(self, attrs):
        validate_password(attrs["password"], User(**{k: v for k, v in attrs.items() if k != "password"}))
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
