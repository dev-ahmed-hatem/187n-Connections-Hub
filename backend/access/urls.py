from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AccessConnectionsView,
    AccessDataView,
    AccessRequestConnectionView,
    AccessTokenView,
    AuditLogListView,
    ConsumerViewSet,
    ProjectAccessRequestViewSet,
)

app_name = 'access'

router = DefaultRouter()
router.register('consumers', ConsumerViewSet, basename='consumer')
router.register('project-requests', ProjectAccessRequestViewSet, basename='projectrequest')

urlpatterns = [
    path('audit/', AuditLogListView.as_view(), name='audit'),
    path('clients/<int:org_id>/connections',
         AccessConnectionsView.as_view(), name='client-connections'),
    path('clients/<int:org_id>/<slug:provider_slug>/data',
         AccessDataView.as_view(), name='client-data'),
    path('clients/<int:org_id>/<slug:provider_slug>/token',
         AccessTokenView.as_view(), name='client-token'),
    path('clients/<int:org_id>/<slug:provider_slug>/request-connection',
         AccessRequestConnectionView.as_view(), name='client-request-connection'),
]

urlpatterns += router.urls
