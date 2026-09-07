from rest_framework.routers import DefaultRouter

from .views import (
    AnnouncementViewSet,
    CommentViewSet,
    ConnectionRequestViewSet,
    NoteViewSet,
    NotificationViewSet,
)

app_name = 'portal'

router = DefaultRouter()
router.register('announcements', AnnouncementViewSet, basename='announcement')
router.register('notes', NoteViewSet, basename='note')
router.register('comments', CommentViewSet, basename='comment')
router.register('notifications', NotificationViewSet, basename='notification')
router.register('connection-requests', ConnectionRequestViewSet, basename='connectionrequest')

urlpatterns = router.urls
