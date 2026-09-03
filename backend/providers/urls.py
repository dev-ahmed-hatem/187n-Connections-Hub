from django.urls import path

from .views import ProviderListView, mock_authorize

app_name = 'providers'

urlpatterns = [
    path('', ProviderListView.as_view(), name='list'),
    path('mock-oauth/authorize', mock_authorize, name='mock_authorize'),
]
