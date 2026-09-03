from rest_framework.routers import DefaultRouter

from .views import ClientOrgViewSet, UserViewSet

app_name = 'users'

router = DefaultRouter()
router.register('orgs', ClientOrgViewSet, basename='clientorg')
router.register('accounts', UserViewSet, basename='user')

urlpatterns = router.urls
