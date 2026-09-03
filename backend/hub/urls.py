from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/users/', include('users.urls')),
    path('api/providers/', include('providers.urls')),
    path('api/connections/', include('connections.urls')),
    path('api/access/', include('access.urls')),
    path('api/portal/', include('portal.urls')),
]
