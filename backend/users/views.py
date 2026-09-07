from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from authentication.permissions import IsAdminOrReadOnly, IsAdminRole

from .models import ClientOrg
from .serializers import ClientOrgSerializer, UserCreateSerializer, UserSerializer

User = get_user_model()


class ClientOrgViewSet(viewsets.ModelViewSet):
    """Client orgs. Readable by any authenticated user (developers pick a client);
    only admins can create/update/delete. Client users see only their own org."""

    serializer_class = ClientOrgSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        qs = ClientOrg.objects.all()
        if user.is_authenticated and user.is_client_role and user.client_org_id:
            return qs.filter(id=user.client_org_id)
        return qs


class UserViewSet(viewsets.ModelViewSet):
    """Admin-only user management."""

    queryset = User.objects.all().order_by('username')
    permission_classes = [IsAdminRole]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def perform_destroy(self, instance):
        if instance.id == self.request.user.id:
            raise PermissionDenied('You cannot delete your own account.')
        instance.delete()
