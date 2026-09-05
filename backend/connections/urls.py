from django.urls import path

from .views import (
    ConnectionCallbackView,
    ConnectionDeleteView,
    ConnectionListView,
    ConnectionOverviewView,
    ConnectionStartView,
    ConnectionTestView,
)

app_name = 'connections'

urlpatterns = [
    path('', ConnectionListView.as_view(), name='list'),
    path('overview/', ConnectionOverviewView.as_view(), name='overview'),
    path('start/', ConnectionStartView.as_view(), name='start'),
    path('callback', ConnectionCallbackView.as_view(), name='callback'),
    path('<int:pk>/test', ConnectionTestView.as_view(), name='test'),
    path('<int:pk>/', ConnectionDeleteView.as_view(), name='delete'),
]
