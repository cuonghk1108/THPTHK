from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GoogleOAuthLoginView, GoogleOAuthCallbackView, CompleteProfileAPIView,
    LoginAPIView, LogoutAPIView, CurrentUserAPIView, ChangePasswordAPIView,
    ProfileAPIView, ProfileAvatarAPIView,
    SystemStatsAPIView, AuditLogViewSet, UserManagementViewSet,
    RegisterAPIView, NotificationViewSet,
    ForgotPasswordAPIView, ResetPasswordAPIView, ServerTimeAPIView,
    StudentApprovalViewSet, DoanTruongManagementViewSet
)

router = DefaultRouter()
router.register(r'users', UserManagementViewSet, basename='user-management')
router.register(r'student-approvals', StudentApprovalViewSet, basename='student-approval')
router.register(r'doan-truong', DoanTruongManagementViewSet, basename='doan-truong-management')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('auth/register/', RegisterAPIView.as_view(), name='api-register'),
    path('auth/google/', GoogleOAuthLoginView.as_view(), name='api-google-login'),
    path('auth/google/callback/', GoogleOAuthCallbackView.as_view(), name='api-google-callback'),
    path('auth/complete-profile/', CompleteProfileAPIView.as_view(), name='api-complete-profile'),
    path('auth/login/', LoginAPIView.as_view(), name='api-login'),
    path('auth/logout/', LogoutAPIView.as_view(), name='api-logout'),
    path('auth/forgot-password/', ForgotPasswordAPIView.as_view(), name='api-forgot-password'),
    path('auth/reset-password/', ResetPasswordAPIView.as_view(), name='api-reset-password'),
    path('auth/me/', CurrentUserAPIView.as_view(), name='api-me'),
    path('auth/change-password/', ChangePasswordAPIView.as_view(), name='api-change-password'),
    path('auth/profile/', ProfileAPIView.as_view(), name='api-profile'),
    path('auth/profile/avatar/', ProfileAvatarAPIView.as_view(), name='api-profile-avatar'),
    path('system/stats/', SystemStatsAPIView.as_view(), name='api-system-stats'),
    path('system/time/', ServerTimeAPIView.as_view(), name='api-server-time'),
    path('', include(router.urls)),
]
