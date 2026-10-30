from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import index_view, ForgotPasswordAPIView, ResetPasswordAPIView

urlpatterns = [
    path('', index_view, name='home'),
    path('dashboard', index_view, name='dashboard'),
    path('dashboard/', index_view, name='dashboard-slash'),
    path('union/dashboard', index_view, name='union-dashboard-page'),
    path('union/dashboard/', index_view, name='union-dashboard-page-slash'),
    path('register', index_view, name='register-page'),
    path('register/', index_view, name='register-page-slash'),
    path('login', index_view, name='login-page'),
    path('login/', index_view, name='login-page-slash'),
    path('complete-profile', index_view, name='complete-profile-page'),
    path('complete-profile/', index_view, name='complete-profile-page-slash'),
    path('pending-approval', index_view, name='pending-approval-page'),
    path('pending-approval/', index_view, name='pending-approval-page-slash'),
    path('registration-pending', index_view, name='registration-pending-page'),
    path('registration-pending/', index_view, name='registration-pending-page-slash'),
    path('forgot-password', index_view, name='forgot-password-page'),
    path('forgot-password/', index_view, name='forgot-password-page-slash'),
    path('reset-password', index_view, name='reset-password-page'),
    path('reset-password/', index_view, name='reset-password-page-slash'),
    path('profile', index_view, name='profile-page'),
    path('profile/', index_view, name='profile-page-slash'),
    path('teacher-classes', index_view, name='teacher-classes-page'),
    path('teacher-classes/', index_view, name='teacher-classes-page-slash'),
    path('competition', index_view, name='competition-page'),
    path('competition/', index_view, name='competition-page-slash'),
    path('conduct', index_view, name='conduct-page'),
    path('conduct/', index_view, name='conduct-page-slash'),
    path('admin/users', index_view, name='admin-users-page'),
    path('admin/users/', index_view, name='admin-users-page-slash'),
    # Keep the custom, role-checked user manager ahead of Django Admin's
    # catch-all admin route so /admin/users reaches index_view.
    path('admin/', admin.site.urls),
    path('privacy-policy', index_view, name='privacy-policy-page'),
    path('privacy-policy/', index_view, name='privacy-policy-page-slash'),
    path('terms-of-service', index_view, name='terms-of-service-page'),
    path('terms-of-service/', index_view, name='terms-of-service-page-slash'),

    # REST APIs
    path('api/auth/forgot-password/', ForgotPasswordAPIView.as_view(), name='api-auth-forgot-password'),
    path('api/auth/reset-password/', ResetPasswordAPIView.as_view(), name='api-auth-reset-password'),
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
