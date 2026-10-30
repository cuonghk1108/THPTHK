from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings


class SampleDatabaseReadOnlyMiddleware(MiddlewareMixin):
    """Keep sample-mode deployments read-only except for session login/logout."""

    auth_paths = {
        '/api/core/auth/login/',
        '/api/core/auth/logout/',
        '/api/core/auth/register/',
        '/api/core/auth/complete-profile/',
        '/api/core/auth/forgot-password/',
        '/api/core/auth/reset-password/',
        '/api/auth/forgot-password/',
        '/api/auth/reset-password/',
        '/api/core/auth/profile/',
        '/api/core/auth/profile/avatar/',
    }

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not settings.USE_SAMPLE_DATABASE:
            return None

        if request.method in {'GET', 'HEAD', 'OPTIONS'} or request.path in self.auth_paths:
            return None

        return JsonResponse(
            {'error': 'Chế độ dữ liệu mẫu chỉ để xem; các thay đổi không được lưu lâu dài.'},
            status=405,
        )


class PasswordChangeRequiredMiddleware(MiddlewareMixin):
    allowed_paths = {
        '/',
        '/dashboard',
        '/dashboard/',
        '/profile',
        '/profile/',
        '/admin/users',
        '/admin/users/',
        '/api/core/auth/me/',
        '/api/core/auth/logout/',
        '/api/core/auth/change-password/',
    }

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = request.user
        if not user.is_authenticated or not user.must_change_password:
            return None

        if request.path in self.allowed_paths or request.path.startswith(('/static/', '/media/')):
            return None

        if request.path.startswith('/api/'):
            return JsonResponse(
                {'error': 'Bạn phải đổi mật khẩu trước khi tiếp tục.'},
                status=403,
            )

        return redirect('/')


class CloudflareRealIPMiddleware(MiddlewareMixin):
    """
    Phục hồi địa chỉ IP thật của người dùng từ Cloudflare Edge (CF-Connecting-IP),
    giúp Nhật ký kiểm toán (Audit Logs) ghi nhận chính xác danh tính học sinh & giáo viên.
    """
    def process_request(self, request):
        cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
        if cf_ip:
            request.META['REMOTE_ADDR'] = cf_ip.strip()
        elif 'HTTP_X_FORWARDED_FOR' in request.META:
            forwarded = request.META['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
            if forwarded:
                request.META['REMOTE_ADDR'] = forwarded


class AccountStatusEnforcementMiddleware(MiddlewareMixin):
    """
    Bảo vệ nghiêm ngặt: Mọi tài khoản mới đăng ký (qua Google OAuth hoặc đăng ký thường)
    phải được Quản trị viên (Admin) phê duyệt (account_status == STATUS_APPROVED)
    mới được phép truy cập Dashboard và các API nghiệp vụ nội bộ.
    """
    allowed_auth_api_prefixes = (
        '/api/core/auth/',
        '/api/auth/',
        '/api/core/system/time/',
        '/api/core/system/stats/',
    )

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = request.user
        if not user.is_authenticated or user.is_superuser:
            return None

        # Static and media files are always allowed
        if request.path.startswith(('/static/', '/media/')):
            return None

        # If user is approved, standard role-based access control applies
        from core.models import User
        if user.account_status == User.STATUS_APPROVED or user.is_superuser or user.is_staff:
            if not getattr(user, 'profile_completed', True):
                User.objects.filter(pk=user.pk).update(profile_completed=True)
                user.profile_completed = True
            return None

        # If calling an API
        if request.path.startswith('/api/'):
            # Allow authentication endpoints (login, logout, me, complete-profile)
            if any(request.path.startswith(prefix) for prefix in self.allowed_auth_api_prefixes):
                return None
            return JsonResponse(
                {
                    'error': 'Tài khoản chưa được Quản trị viên phê duyệt hoặc đang bị khóa. Bạn không có quyền truy cập dữ liệu nội bộ.',
                    'status': user.account_status,
                },
                status=403,
            )

        # For HTML page routes:
        # If user has not completed profile (and is NOT approved)
        if not getattr(user, 'profile_completed', True) and user.account_status != User.STATUS_APPROVED:
            if request.path.rstrip('/') in {'/complete-profile', '/privacy-policy', '/terms-of-service'}:
                return None
            return redirect('/complete-profile')

        # If user is PENDING, REJECTED, SUSPENDED, or DISABLED:
        if request.path.rstrip('/') in {'/pending-approval', '/registration-pending', '', '/privacy-policy', '/terms-of-service'}:
            return None

        return redirect('/pending-approval')
