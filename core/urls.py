from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginAPIView, LogoutAPIView, CurrentUserAPIView,
    SystemStatsAPIView, AuditLogViewSet, UserManagementViewSet
)

router = DefaultRouter()
router.register(r'users', UserManagementViewSet, basename='user-management')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('auth/login/', LoginAPIView.as_view(), name='api-login'),
    path('auth/logout/', LogoutAPIView.as_view(), name='api-logout'),
    path('auth/me/', CurrentUserAPIView.as_view(), name='api-me'),
    path('system/stats/', SystemStatsAPIView.as_view(), name='api-system-stats'),
    path('', include(router.urls)),
]
