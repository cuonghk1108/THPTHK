from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import index_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index_view, name='home'),

    # REST APIs
    path('api/core/', include('core.urls')),
    path('api/conduct/', include('conduct.urls')),
    path('api/competition/', include('competition.urls')),
    path('api/alerts/', include('alerts.urls')),
    path('api/counseling/', include('counseling.urls')),
    path('api/reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
