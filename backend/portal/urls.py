from rest_framework.routers import DefaultRouter

from .views import AnnouncementViewSet, ConnectionRequestViewSet, NoteViewSet

app_name = 'portal'

router = DefaultRouter()
router.register('announcements', AnnouncementViewSet, basename='announcement')
router.register('notes', NoteViewSet, basename='note')
router.register('connection-requests', ConnectionRequestViewSet, basename='connectionrequest')

urlpatterns = router.urls
