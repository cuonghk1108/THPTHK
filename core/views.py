import time
import logging
import uuid
import secrets
import json
import urllib.request
from datetime import timedelta, date

from PIL import Image, UnidentifiedImageError
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q
from django.db import DatabaseError, transaction
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from urllib.parse import urlencode
from rest_framework import viewsets, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .models import (
    User, AcademicYear, Semester, SystemSetting, AuditLog, ApprovalLog, Notification,
    ALL_DOAN_TRUONG_PERMISSIONS, DEFAULT_DOAN_TRUONG_PERMISSIONS
)
from .serializers import (
    CompleteProfileSerializer,
    UserSerializer, UserCreateSerializer, PasswordChangeSerializer,
    AcademicYearSerializer, SemesterSerializer, SystemSettingSerializer,
    AuditLogSerializer, RegisterSerializer, ApprovalActionSerializer,
    ApprovalLogSerializer, NotificationSerializer, ProfileSerializer, ProfileUpdateSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer,
    StudentAccountSerializer, StudentApprovalActionSerializer, StudentBulkApprovalSerializer,
    DoanTruongMemberSerializer, DoanTruongPermissionUpdateSerializer
)
from .email import send_password_reset_email

logger = logging.getLogger(__name__)


@never_cache
@ensure_csrf_cookie
def index_view(request):
    """Serve the public pages and protect the authenticated workspace."""
    from conduct.models import SchoolClass, Student
    school_name = SystemSetting.get_setting('SCHOOL_NAME', 'TRƯỜNG THPT HƯƠNG KHÊ – HÀ TĨNH')
    slogan = SystemSetting.get_setting('APP_SLOGAN', 'Kỷ cương số – Thi đua minh bạch – Đồng hành cùng học sinh')
    normalized_path = request.path.rstrip('/') or '/'
    protected_routes = {'/dashboard', '/profile', '/admin/users', '/competition', '/conduct', '/teacher-classes'}
    user = request.user
    is_approved_session = bool(
        user.is_authenticated and user.is_active and user.account_status == User.STATUS_APPROVED
    )
    public_user = user if is_approved_session else None
    public_user_class = ''
    public_user_avatar_url = ''
    public_user_display_name = ''
    public_user_initials = ''
    if public_user:
        public_user_display_name = public_user.full_name or public_user.username or 'Người dùng'
        public_user_initials = ''.join(part[0] for part in public_user_display_name.split()[:2]).upper() or 'HK'
        public_user_class = public_user.department_or_class or ''
        if public_user.is_student:
            try:
                public_user_class = public_user.student.school_class.name
            except Exception:
                try:
                    public_user_class = public_user.student_profile.school_class.name
                except Exception:
                    pass
        try:
            if public_user.avatar:
                public_user_avatar_url = public_user.avatar.url
            elif public_user.google_avatar_url:
                public_user_avatar_url = public_user.google_avatar_url
        except Exception:
            logger.warning('Could not resolve the current user avatar URL.', exc_info=True)

    # Nếu người dùng chưa đăng nhập nhưng cố vào route bảo vệ hoặc complete-profile / pending-approval
    if not user.is_authenticated:
        if normalized_path in protected_routes or normalized_path in {'/complete-profile', '/pending-approval'}:
            return redirect(f"/login?{urlencode({'next': request.get_full_path()})}")

    # Nếu người dùng ĐÃ đăng nhập:
    if user.is_authenticated:
        # 1. TÀI KHOẢN ĐÃ ĐƯỢC PHÊ DUYỆT (APPROVED) HOẶC LÀ ADMIN/SUPERUSER:
        # BỎ QUA HOÀN THIỆN HỒ SƠ VÀ TRANG CHỜ DUYỆT -> VÀO THẲNG DASHBOARD!
        if is_approved_session or user.account_status == User.STATUS_APPROVED or user.is_superuser or user.is_staff:
            if not getattr(user, 'profile_completed', True):
                User.objects.filter(pk=user.pk).update(profile_completed=True)
                user.profile_completed = True
            if normalized_path in {'/login', '/register', '/complete-profile', '/pending-approval', '/registration-pending'}:
                return redirect('/dashboard')

        # 2. Người dùng bị từ chối hoặc tạm khóa
        elif user.account_status in [User.STATUS_REJECTED, User.STATUS_SUSPENDED, User.STATUS_DISABLED]:
            if normalized_path in protected_routes or normalized_path in {'/login', '/register', '/complete-profile'}:
                return redirect('/pending-approval')

        # 3. Người dùng chưa hoàn thiện hồ sơ (Google mới đăng ký lần đầu và CHƯA được phê duyệt): bắt buộc vào /complete-profile
        elif not getattr(user, 'profile_completed', True):
            if normalized_path in protected_routes or normalized_path in {'/login', '/register', '/pending-approval', '/registration-pending'}:
                return redirect('/complete-profile')

        # 4. Người dùng đang ở trạng thái PENDING (đã nộp hồ sơ, chờ duyệt)
        elif user.account_status == User.STATUS_PENDING:
            if normalized_path in protected_routes or normalized_path in {'/login', '/register', '/complete-profile'}:
                return redirect('/pending-approval')

    if normalized_path in protected_routes:
        if not is_approved_session:
            return redirect(f"/login?{urlencode({'next': request.get_full_path()})}")
        if normalized_path == '/admin/users' and not (user.is_admin or user.is_superuser):
            return redirect('/dashboard')
        if (user.is_student or user.role == User.ROLE_HOC_SINH) and normalized_path in {'/competition', '/conduct'}:
            return redirect('/dashboard')

    school_classes = []
    if normalized_path in {'/register', '/complete-profile'}:
        school_classes = list(
            SchoolClass.objects.filter(is_active=True)
            .values('id', 'name', 'grade')
            .order_by('grade', 'class_order', 'name')
        )
    current_year = AcademicYear.objects.filter(is_current=True).values_list('name', flat=True).first() or ''

    return render(request, 'index.html', {
        'school_classes': school_classes,
        'school_name': school_name,
        'slogan': slogan,
        'current_year': current_year,
        'sample_database': settings.USE_SAMPLE_DATABASE,
        'show_public_home': request.path == '/',
        'show_public_auth': normalized_path in {
            '/login', '/register', '/registration-pending', '/pending-approval',
            '/complete-profile', '/forgot-password', '/reset-password'
        },
        'show_app': normalized_path in protected_routes,
        'is_authenticated': is_approved_session,
        'auth_user': user if user.is_authenticated else None,
        'public_user': public_user,
        'public_user_class': public_user_class,
        'public_user_avatar_url': public_user_avatar_url,
        'public_user_display_name': public_user_display_name,
        'public_user_initials': public_user_initials,
        'show_login_form': normalized_path == '/login',
        'show_register_form': normalized_path == '/register',
        'show_complete_profile': normalized_path == '/complete-profile',
        'show_pending_approval': normalized_path in {'/pending-approval', '/registration-pending'},
        'show_registration_pending': normalized_path in {'/pending-approval', '/registration-pending'},
        'show_forgot_password_form': normalized_path == '/forgot-password',
        'show_reset_password_form': normalized_path == '/reset-password',
        'show_privacy_policy': normalized_path == '/privacy-policy',
        'show_terms_of_service': normalized_path == '/terms-of-service',
        'google_oauth_configured': getattr(settings, 'GOOGLE_OAUTH_CONFIGURED', False),
        'oauth_error': request.GET.get('error', ''),
        'oauth_error_email': request.GET.get('email', ''),
        'privacy_version': SystemSetting.get_setting('PRIVACY_POLICY_VERSION', 'v1.0-draft'),
        'privacy_updated_at': SystemSetting.get_setting('PRIVACY_POLICY_UPDATED_AT', '15/10/2026'),
        'terms_version': SystemSetting.get_setting('TERMS_OF_SERVICE_VERSION', 'v1.0-draft'),
        'terms_updated_at': SystemSetting.get_setting('TERMS_OF_SERVICE_UPDATED_AT', '15/10/2026'),
        'legal_doc_status': SystemSetting.get_setting('LEGAL_DOC_STATUS', 'Bản dự thảo – chờ nhà trường phê duyệt'),
    })



class GoogleOAuthLoginView(APIView):
    """
    Khởi tạo luồng xác thực Google OAuth 2.0.
    Tạo state CSRF an toàn trong session và chuyển hướng sang Google Consent Screen.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '').strip()
        client_secret = getattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', '').strip()

        if not client_id or not client_secret:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept', ''):
                return Response(
                    {'error': 'Hệ thống chưa được cấu hình Google OAuth Client ID. Vui lòng liên hệ Quản trị viên để thiết lập biến môi trường GOOGLE_OAUTH_CLIENT_ID và GOOGLE_OAUTH_CLIENT_SECRET.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return redirect('/login?error=google_not_configured')

        state = secrets.token_urlsafe(32)
        request.session['google_oauth_state'] = state

        host = request.get_host().lower()
        if 'localhost' in host or '127.0.0.1' in host:
            callback_url = request.build_absolute_uri('/api/core/auth/google/callback/')
        else:
            callback_url = getattr(settings, 'GOOGLE_OAUTH_CALLBACK_URL', '').strip()
            if not callback_url:
                callback_url = request.build_absolute_uri('/api/core/auth/google/callback/')
                if callback_url.startswith('http://'):
                    callback_url = 'https://' + callback_url[7:]
        logger.info(f"Google OAuth Login redirect_uri: {callback_url}")

        google_auth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            'client_id': client_id,
            'redirect_uri': callback_url,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': state,
            'prompt': 'select_account',
            'access_type': 'online',
        }
        auth_url = f"{google_auth_endpoint}?{urlencode(params)}"
        return redirect(auth_url)


class GoogleOAuthCallbackView(APIView):
    """
    Xử lý phản hồi OAuth từ Google.
    - Tìm kiếm hoặc tạo mới tài khoản gắn với Google ID (sub).
    - Mọi tài khoản mới tạo LUÔN có trạng thái PENDING và profile_completed=False.
    - Chuyển hướng người dùng sang /complete-profile để chọn Học sinh/Giáo viên và khai báo hồ sơ.
    - Bắt buộc Quản trị viên phê duyệt thủ công trước khi tài khoản được hoạt động.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        error = request.GET.get('error')
        if error:
            logger.warning(f"Google OAuth callback error from provider: {error}")
            return redirect('/login?error=google_cancelled')

        code = request.GET.get('code')
        state = request.GET.get('state')
        session_state = request.session.pop('google_oauth_state', None)

        if not state or not session_state or state != session_state:
            logger.warning("Google OAuth state mismatch or missing")
            return redirect('/login?error=google_state_mismatch')

        if not code:
            return redirect('/login?error=google_missing_code')

        client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '').strip()
        client_secret = getattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', '').strip()
        host = request.get_host().lower()
        if 'localhost' in host or '127.0.0.1' in host:
            callback_url = request.build_absolute_uri('/api/core/auth/google/callback/')
        else:
            callback_url = getattr(settings, 'GOOGLE_OAUTH_CALLBACK_URL', '').strip()
            if not callback_url:
                callback_url = request.build_absolute_uri('/api/core/auth/google/callback/')
                if callback_url.startswith('http://'):
                    callback_url = 'https://' + callback_url[7:]
        logger.info(f"Google OAuth Callback redirect_uri: {callback_url}")

        token_endpoint = "https://oauth2.googleapis.com/token"
        token_payload = urlencode({
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': callback_url,
            'grant_type': 'authorization_code',
        }).encode('utf-8')

        token_req = urllib.request.Request(
            token_endpoint,
            data=token_payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        try:
            with urllib.request.urlopen(token_req, timeout=10) as resp:
                token_data = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            logger.error(f"Google OAuth token exchange failed: {e}", exc_info=True)
            return redirect('/login?error=google_token_failed')

        access_token = token_data.get('access_token')
        if not access_token:
            return redirect('/login?error=google_token_failed')

        userinfo_endpoint = "https://openidconnect.googleapis.com/v1/userinfo"
        userinfo_req = urllib.request.Request(
            userinfo_endpoint,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        try:
            with urllib.request.urlopen(userinfo_req, timeout=10) as resp:
                user_info = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            logger.error(f"Google userinfo request failed: {e}", exc_info=True)
            return redirect('/login?error=google_profile_failed')

        google_sub = user_info.get('sub')
        google_email = (user_info.get('email') or '').strip().lower()
        google_name = (user_info.get('name') or '').strip()
        google_picture = user_info.get('picture') or ''

        if not google_sub or not google_email:
            return redirect('/login?error=google_profile_failed')

        with transaction.atomic():
            # A. Người dùng đã liên kết Google ID
            user = User.objects.filter(google_id=google_sub).first()

            # B. Nếu chưa có google_id nhưng tài khoản đã tồn tại trong database (theo email hoặc username)
            if not user:
                user = User.objects.filter(
                    Q(email__iexact=google_email) | Q(username__iexact=google_email)
                ).first()
                if user:
                    # Tự động liên kết Google ID và chấp nhận (accept) đăng nhập ngay lập tức
                    user.google_id = google_sub
                    update_fields = ['google_id']
                    if google_picture and not user.google_avatar_url:
                        user.google_avatar_url = google_picture
                        update_fields.append('google_avatar_url')
                    user.save(update_fields=update_fields)

                    AuditLog.objects.create(
                        user=user,
                        action='UPDATE_PROFILE',
                        resource_type='USER',
                        resource_id=str(user.id),
                        details=f"Tài khoản {user.username} ({user.email}) đã tự động liên kết thành công với Google ID ({google_sub}) khi đăng nhập.",
                        ip_address=request.META.get('REMOTE_ADDR')
                    )

            if user:
                if google_picture and not user.google_avatar_url:
                    user.google_avatar_url = google_picture
                    user.save(update_fields=['google_avatar_url'])

                login(request, user)

                # NẾU TÀI KHOẢN ĐÃ ĐƯỢC PHÊ DUYỆT: BỎ QUA HOÀN THIỆN HỒ SƠ, VÀO THẲNG DASHBOARD
                if user.account_status == User.STATUS_APPROVED or user.is_superuser or user.is_staff:
                    if not user.profile_completed:
                        User.objects.filter(pk=user.pk).update(profile_completed=True)
                        user.profile_completed = True
                    return redirect('/dashboard')
                elif not user.profile_completed:
                    return redirect('/complete-profile')
                elif user.account_status == User.STATUS_SUSPENDED:
                    return redirect('/login?error=account_suspended')
                elif user.account_status == User.STATUS_REJECTED:
                    return redirect('/login?error=account_rejected')
                else:
                    return redirect('/pending-approval')

            # C. Người dùng mới hoàn toàn (chưa tồn tại trong database -> bắt điền thông tin)
            base_username = f"google_{google_sub[:10]}"
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User.objects.create(
                username=username,
                email=google_email,
                full_name=google_name or 'Người dùng Google',
                google_id=google_sub,
                google_avatar_url=google_picture,
                account_status=User.STATUS_PENDING,
                profile_completed=False,
                role=User.ROLE_HOC_SINH,
                requested_role=None,
                is_active=True,
            )
            user.set_unusable_password()
            user.save()

            AuditLog.objects.create(
                user=user,
                action='REGISTER',
                resource_type='USER',
                resource_id=str(user.id),
                details=f"Đăng ký tài khoản mới qua Google OAuth ({google_email}). Trạng thái: Chờ hoàn thiện hồ sơ.",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            login(request, user)
            return redirect('/complete-profile')


class CompleteProfileAPIView(APIView):
    """
    API Hoàn thiện hồ sơ đăng ký tài khoản (sau khi đăng nhập Google lần đầu).
    - Nhận thông tin phân loại: Học sinh hoặc Giáo viên.
    - Lưu trữ thông tin định danh và lớp/bộ môn.
    - Đặt trạng thái PENDING và thông báo cho Quản trị viên để xét duyệt.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from conduct.models import SchoolClass, Student
        user = request.user
        if user.account_status == User.STATUS_APPROVED or user.is_superuser or user.is_staff:
            if not user.profile_completed:
                User.objects.filter(pk=user.pk).update(profile_completed=True)
                user.profile_completed = True
            return Response(
                {
                    'message': 'Tài khoản của bạn đã được Quản trị viên phê duyệt trước đó.',
                    'redirect_url': '/dashboard'
                },
                status=status.HTTP_200_OK
            )

        serializer = CompleteProfileSerializer(data=request.data)
        if not serializer.is_valid():
            first_err = next(iter(serializer.errors.values()))
            if isinstance(first_err, list):
                first_err = first_err[0]
            return Response({'error': str(first_err), 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        role_type = data['role_type']
        full_name = data['full_name'].strip()
        phone = data.get('phone', '').strip()

        with transaction.atomic():
            user.full_name = full_name
            if phone:
                user.phone = phone

            verification_payload = {
                'role_type': role_type,
                'submitted_via': 'Google OAuth' if user.google_id else 'Direct Form',
            }

            if role_type == CompleteProfileSerializer.ROLE_TYPE_STUDENT:
                grade = data['grade']
                class_name = data.get('class_name', '').strip()
                class_id = data.get('class_id')

                school_class = None
                if class_id:
                    school_class = SchoolClass.objects.filter(id=class_id, is_active=True).first()
                if not school_class and class_name:
                    school_class = SchoolClass.objects.filter(name__iexact=class_name, is_active=True).first()

                if not school_class:
                    return Response({'error': 'Lớp học đã chọn không tồn tại hoặc chưa kích hoạt.'}, status=status.HTTP_400_BAD_REQUEST)

                user.requested_role = User.ROLE_HOC_SINH
                user.department_or_class = school_class.name
                verification_payload.update({
                    'grade': grade,
                    'class_name': school_class.name,
                    'class_id': school_class.id,
                    'dob': str(data.get('dob')) if data.get('dob') else '',
                    'gender': data.get('gender', ''),
                    'student_code': data.get('student_code', ''),
                })

                student, _ = Student.objects.get_or_create(
                    user=user,
                    defaults={
                        'student_code': data.get('student_code') or f"HS{user.id:04d}",
                        'full_name': full_name,
                        'school_class': school_class,
                        'gender': data.get('gender') or 'Nam',
                        'date_of_birth': data.get('dob') or date(2009, 1, 1),
                        'status': 'STUDYING',
                    }
                )
                student.full_name = full_name
                student.school_class = school_class
                if data.get('dob'):
                    student.date_of_birth = data['dob']
                if data.get('gender'):
                    student.gender = data['gender']
                if data.get('student_code'):
                    student.student_code = data['student_code']
                student.save()

            elif role_type == CompleteProfileSerializer.ROLE_TYPE_TEACHER:
                subjects_data = data.get('subjects') or []
                if not subjects_data and data.get('subject'):
                    subjects_data = [s.strip() for s in data['subject'].split(',') if s.strip()]
                clean_subjects = []
                for s in subjects_data:
                    sc = s.strip()
                    if sc.startswith('Môn '):
                        sc = sc[4:].strip()
                    if sc and sc not in clean_subjects:
                        clean_subjects.append(sc)

                subject_str = ", ".join(clean_subjects) if clean_subjects else (data.get('subject', '').strip() or 'Chưa phân công')
                teacher_type = data.get('teacher_type') or 'gvbm'
                homeroom_class = data.get('homeroom_class', '').strip()
                teaching_classes = data.get('teaching_classes', [])

                user.requested_role = User.ROLE_GVCN if teacher_type == 'gvcn' else User.ROLE_GVBM
                user.department_or_class = homeroom_class if (teacher_type == 'gvcn' and homeroom_class) else (f"Môn: {subject_str}" if subject_str else 'Giáo viên')
                verification_payload.update({
                    'subject': subject_str,
                    'subjects': clean_subjects,
                    'teacher_type': teacher_type,
                    'homeroom_class': homeroom_class,
                    'teaching_classes': teaching_classes,
                    'teacher_code': data.get('teacher_code', ''),
                })

                # Pre-create teaching assignments (inactive until admin approves)
                if teaching_classes:
                    from conduct.models import TeacherClassAssignment, SchoolClass
                    for c_name in teaching_classes:
                        sc = SchoolClass.objects.filter(name__iexact=str(c_name).strip(), is_active=True).first()
                        if sc:
                            primary_subj = clean_subjects[0] if clean_subjects else 'Bộ môn'
                            TeacherClassAssignment.objects.get_or_create(
                                teacher=user,
                                school_class=sc,
                                subject=primary_subj,
                                defaults={'is_active': False}
                            )

            user.verification_info = json.dumps(verification_payload, ensure_ascii=False)
            user.profile_completed = True
            user.submitted_at = timezone.now()
            user.account_status = User.STATUS_PENDING
            user.save()

            admin_users = User.objects.filter(
                Q(role__in=[User.ROLE_ADMIN, User.ROLE_SUPER_ADMIN]) | Q(is_superuser=True),
                account_status=User.STATUS_APPROVED,
                is_active=True
            ).distinct()

            req_role_name = 'Học sinh' if role_type == 'student' else ('Giáo viên chủ nhiệm' if data.get('teacher_type') == 'gvcn' else 'Giáo viên bộ môn')
            for adm in admin_users:
                Notification.objects.create(
                    recipient=adm,
                    notification_type=Notification.TYPE_REGISTRATION,
                    title=f"Hồ sơ mới nộp từ Google: {user.full_name}",
                    message=f"Người dùng {user.full_name} ({user.email}) đã hoàn thiện hồ sơ với đối tượng [{req_role_name}], lớp/đơn vị [{user.department_or_class}]. Vui lòng xét duyệt.",
                    link="/admin/users"
                )

            ApprovalLog.objects.create(
                user=user,
                reviewer=None,
                previous_status='INCOMPLETE',
                new_status=User.STATUS_PENDING,
                assigned_role=user.requested_role or '',
                reason='Người dùng hoàn thiện hồ sơ đăng ký qua Google OAuth',
                internal_notes=f"Đơn vị: {user.department_or_class}"
            )

            AuditLog.objects.create(
                user=user,
                action='UPDATE_PROFILE',
                resource_type='USER',
                resource_id=str(user.id),
                details=f"Người dùng hoàn thiện và nộp hồ sơ ({req_role_name} - {user.department_or_class}). Chờ Quản trị viên phê duyệt.",
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return Response({
            'success': True,
            'message': 'Hồ sơ đã được gửi thành công. Vui lòng đợi Quản trị viên kiểm tra và phê duyệt.',
            'redirect_url': '/pending-approval'
        })


class RegisterAPIView(APIView):
    """
    API Đăng ký tài khoản dành cho học sinh, giáo viên, cán bộ trường.
    Quy tắc cốt lõi:
    - Bất kỳ tài khoản mới đăng ký đều có trạng thái PENDING.
    - KHÔNG được tự động đăng nhập.
    - KHÔNG được phép chọn vai trò Admin / Super Admin.
    - Phải được Quản trị viên (Admin) xét duyệt trước khi kích hoạt.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if settings.USE_SAMPLE_DATABASE:
            return Response(
                {'error': 'Hệ thống đang chạy chế độ dữ liệu mẫu chỉ đọc; không cho phép đăng ký mới.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))
            if isinstance(first_error, list):
                first_error = first_error[0]
            return Response({'error': str(first_error), 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = serializer.save()

            # Tạo thông báo đến toàn bộ Quản trị viên (Admin / Super Admin)
            admin_users = User.objects.filter(
                Q(role__in=[User.ROLE_ADMIN, User.ROLE_SUPER_ADMIN]) | Q(is_superuser=True),
                account_status=User.STATUS_APPROVED,
                is_active=True
            ).distinct()

            req_role_display = dict(RegisterSerializer.REQUESTED_ROLE_CHOICES).get(user.requested_role, user.requested_role)
            for adm in admin_users:
                Notification.objects.create(
                    recipient=adm,
                    notification_type=Notification.TYPE_REGISTRATION,
                    title=f"Yêu cầu đăng ký mới: {user.full_name or user.username}",
                    message=(
                        f"Người dùng {user.full_name} ({user.username}) đã gửi yêu cầu đăng ký tài khoản với "
                        f"đối tượng [{req_role_display}], lớp/đơn vị [{user.department_or_class}]. "
                        f"Vui lòng vào trang Quản trị để xét duyệt."
                    ),
                    link="/admin/users"
                )

            # Ghi nhật ký Audit Log
            AuditLog.objects.create(
                user=user,
                action='REGISTER',
                resource_type='USER',
                resource_id=str(user.id),
                details=(
                    f"Người dùng {user.full_name} ({user.username}) nộp đơn đăng ký tài khoản mới. "
                    f"Đối tượng đề nghị: {req_role_display}, Lớp/Đơn vị: {user.department_or_class}. Trạng thái: Chờ phê duyệt."
                ),
                ip_address=request.META.get('REMOTE_ADDR')
            )

            # Tạo bản ghi log khởi tạo
            ApprovalLog.objects.create(
                user=user,
                reviewer=None,
                previous_status='NEW',
                new_status=User.STATUS_PENDING,
                assigned_role='',
                reason='Người dùng tự đăng ký qua biểu mẫu công khai',
                internal_notes='Đang chờ Admin thụ lý xét duyệt'
            )

        return Response({
            'message': 'Đăng ký tài khoản thành công! Yêu cầu của bạn đang chờ Admin xét duyệt. Bạn sẽ được thông báo khi tài khoản được phê duyệt hoặc cần bổ sung thông tin.',
            'username': user.username,
            'full_name': user.full_name,
            'account_status': user.account_status,
        }, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    """
    Xác thực đăng nhập và kiểm tra nghiêm ngặt vòng đời tài khoản:
    - PENDING: Chờ quản trị viên xét duyệt.
    - REJECTED: Yêu cầu bị từ chối (hiển thị lý do).
    - SUSPENDED: Tạm khóa.
    - DISABLED: Đã vô hiệu hóa.
    - APPROVED: Cho phép đăng nhập.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        identifier = request.data.get('username')
        password = request.data.get('password')
        
        if not isinstance(identifier, str) or not isinstance(password, str):
            return Response({'error': 'Vui lòng nhập tên đăng nhập và mật khẩu'}, status=status.HTTP_400_BAD_REQUEST)

        identifier = identifier.strip()
        if not identifier or not password:
            return Response({'error': 'Vui lòng nhập tên đăng nhập và mật khẩu'}, status=status.HTTP_400_BAD_REQUEST)

        # Tìm tài khoản theo username hoặc email
        login_username = identifier
        exact_user = User.objects.filter(username=identifier).first()
        if exact_user:
            candidate_user = exact_user
        else:
            candidate_user = User.objects.filter(username__iexact=identifier).first()
            if not candidate_user:
                candidate_user = User.objects.filter(email__iexact=identifier).exclude(email='').first()

        # Kiểm tra sự tồn tại và mật khẩu của người dùng
        if candidate_user is None or not candidate_user.check_password(password):
            return Response(
                {'error': 'Tên đăng nhập hoặc mật khẩu không chính xác. Vui lòng kiểm tra lại.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # KIỂM TRA TRẠNG THÁI VÒNG ĐỜI TÀI KHOẢN (ACCOUNT STATUS)
        if candidate_user.account_status == User.STATUS_PENDING:
            return Response({
                'error': 'Tài khoản của bạn đang chờ quản trị viên xét duyệt. Vui lòng quay lại sau hoặc liên hệ nhà trường.',
                'account_status': User.STATUS_PENDING,
                'full_name': candidate_user.full_name or candidate_user.username
            }, status=status.HTTP_403_FORBIDDEN)

        if candidate_user.account_status == User.STATUS_REJECTED:
            reason_str = f" Lý do: {candidate_user.rejection_reason}" if candidate_user.rejection_reason else ""
            return Response({
                'error': f'Yêu cầu đăng ký chưa được chấp thuận.{reason_str} Vui lòng xem thông báo từ quản trị viên để biết thêm thông tin.',
                'account_status': User.STATUS_REJECTED,
                'rejection_reason': candidate_user.rejection_reason or ''
            }, status=status.HTTP_403_FORBIDDEN)

        if candidate_user.account_status == User.STATUS_SUSPENDED:
            return Response({
                'error': 'Tài khoản hiện đang bị tạm khóa. Vui lòng liên hệ bộ phận quản trị hệ thống.',
                'account_status': User.STATUS_SUSPENDED
            }, status=status.HTTP_403_FORBIDDEN)

        if candidate_user.account_status == User.STATUS_DISABLED or not candidate_user.is_active:
            return Response({
                'error': 'Tài khoản đã bị vô hiệu hóa hoặc chưa được kích hoạt bởi Quản trị viên.',
                'account_status': User.STATUS_DISABLED
            }, status=status.HTTP_403_FORBIDDEN)

        if candidate_user.account_status != User.STATUS_APPROVED:
            return Response({
                'error': 'Tài khoản của bạn chưa được cấp quyền truy cập hệ thống. Vui lòng liên hệ quản trị viên.',
                'account_status': candidate_user.account_status
            }, status=status.HTTP_403_FORBIDDEN)

        # Tài khoản đã APPROVED và is_active -> Đăng nhập phiên
        login(request, candidate_user)

        if not settings.USE_SAMPLE_DATABASE:
            AuditLog.objects.create(
                user=candidate_user,
                action='LOGIN',
                resource_type='USER',
                resource_id=str(candidate_user.id),
                details=f"Đăng nhập thành công với vai trò {candidate_user.get_role_display()} ({candidate_user.get_account_status_display()})",
                ip_address=request.META.get('REMOTE_ADDR')
            )

        serializer = UserSerializer(candidate_user)
        return Response({
            'message': f'Đăng nhập thành công! Chào mừng {candidate_user.full_name or candidate_user.username}',
            'user': serializer.data
        })


class LogoutAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if request.user.is_authenticated and not settings.USE_SAMPLE_DATABASE:
            AuditLog.objects.create(
                user=request.user,
                action='LOGOUT',
                resource_type='USER',
                resource_id=str(request.user.id),
                details="Đăng xuất an toàn khỏi hệ thống"
            )
        logout(request)
        return Response({'message': 'Đã đăng xuất an toàn khỏi hệ thống'})


class ForgotPasswordAPIView(APIView):
    """
    API yêu cầu đặt lại mật khẩu qua email.
    Bảo mật:
    - Luôn trả về thông báo trung tính, không tiết lộ email có tồn tại hay không.
    - Giới hạn tần suất yêu cầu (rate limiting) chống spam/brute-force.
    - Token ngẫu nhiên, an toàn theo tiêu chuẩn HMAC của Django.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Địa chỉ email không hợp lệ.', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        ip_address = request.META.get('REMOTE_ADDR')

        # Rate limiting: tối đa 5 yêu cầu trong 10 phút từ cùng IP
        recent_requests_count = AuditLog.objects.filter(
            action='FORGOT_PASSWORD_REQUEST',
            created_at__gte=timezone.now() - timezone.timedelta(minutes=10),
            ip_address=ip_address
        ).count()
        if recent_requests_count >= 5:
            return Response(
                {'error': 'Bạn đã gửi quá nhiều yêu cầu khôi phục. Vui lòng chờ 10 phút trước khi thử lại.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Hỗ trợ tìm kiếm theo cả email hoặc tên đăng nhập
        user = User.objects.filter(
            Q(email__iexact=email) | Q(username__iexact=email),
            is_active=True,
            account_status=User.STATUS_APPROVED
        ).first()

        neutral_message = (
            "Nếu địa chỉ email hợp lệ và đủ điều kiện khôi phục, bạn sẽ nhận được "
            "email hướng dẫn đặt lại mật khẩu. Vui lòng kiểm tra hộp thư đến và thư rác."
        )

        if user and user.email:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Xác định frontend_base: Ưu tiên domain edumentor từ request nếu có, hoặc FRONTEND_BASE_URL (https://edumentor.io.vn)
            host = request.get_host()
            if 'edumentor' in host:
                frontend_base = f"https://{host}"
            elif getattr(settings, 'FRONTEND_BASE_URL', ''):
                frontend_base = settings.FRONTEND_BASE_URL.rstrip('/')
            else:
                scheme = 'https' if (request.is_secure() or request.META.get('HTTP_X_FORWARDED_PROTO') == 'https') else request.scheme
                frontend_base = f"{scheme}://{host}"
            reset_url = f"{frontend_base}/reset-password?uid={uid}&token={token}"

            try:
                send_password_reset_email(user, reset_url)
                AuditLog.objects.create(
                    user=user,
                    action='FORGOT_PASSWORD_REQUEST',
                    resource_type='USER',
                    resource_id=str(user.id),
                    details=f"Yêu cầu đặt lại mật khẩu cho tài khoản {user.username} qua email {user.email}.",
                    ip_address=ip_address
                )
            except Exception as e:
                logger.error("Gửi email đặt lại mật khẩu thất bại (%s: %s).", type(e).__name__, str(e))
                AuditLog.objects.create(
                    user=user,
                    action='FORGOT_PASSWORD_REQUEST_FAILED',
                    resource_type='USER',
                    resource_id=str(user.id),
                    details=f"Gửi email đặt lại mật khẩu thất bại ({type(e).__name__}).",
                    ip_address=ip_address
                )
                if settings.DEBUG:
                    return Response(
                        {
                            'error': f'Lỗi kết nối máy chủ gửi thư ({type(e).__name__}). Trong môi trường phát triển (DEBUG), bạn có thể truy cập liên kết đặt lại bên dưới.',
                            'debug_reset_url': reset_url
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                return Response(
                    {'error': 'Hệ thống gửi email thông báo tạm thời gặp sự cố kết nối. Vui lòng liên hệ Quản trị viên nhà trường hoặc thử lại sau.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
        else:
            AuditLog.objects.create(
                user=None,
                action='FORGOT_PASSWORD_REQUEST',
                resource_type='USER',
                details=f"Yêu cầu đặt lại mật khẩu từ IP {ip_address} cho tài khoản/email không tồn tại hoặc chưa duyệt: {email}.",
                ip_address=ip_address
            )

        return Response({'message': neutral_message}, status=status.HTTP_200_OK)


class ResetPasswordAPIView(APIView):
    """
    API xác nhận đặt lại mật khẩu mới bằng token.
    Bảo mật:
    - Xác thực uid và token bằng default_token_generator.
    - Token chỉ dùng một lần (khi password thay đổi, token tự động bị vô hiệu hóa).
    - Kiểm tra độ dài mật khẩu và mật khẩu xác nhận.
    - Ghi nhận AuditLog.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            first_err = next(iter(serializer.errors.values()))
            if isinstance(first_err, list):
                first_err = first_err[0]
            return Response({'error': str(first_err)}, status=status.HTTP_400_BAD_REQUEST)

        uid_b64 = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            uid = force_str(urlsafe_base64_decode(uid_b64))
            user = User.objects.get(pk=uid, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'error': 'Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Token hợp lệ -> Đổi mật khẩu
        user.set_password(new_password)
        if getattr(user, 'must_change_password', False):
            user.must_change_password = False
        user.save()

        AuditLog.objects.create(
            user=user,
            action='RESET_PASSWORD_SUCCESS',
            resource_type='USER',
            resource_id=str(user.id),
            details=f"Người dùng {user.username} đã đặt lại mật khẩu thành công qua email.",
            ip_address=request.META.get('REMOTE_ADDR')
        )

        return Response(
            {'message': 'Đặt lại mật khẩu thành công. Vui lòng đăng nhập bằng mật khẩu mới.'},
            status=status.HTTP_200_OK
        )



class CurrentUserAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            # Double check account status in session
            if request.user.account_status != User.STATUS_APPROVED or not request.user.is_active:
                logout(request)
                return Response({'authenticated': False, 'user': None})

            serializer = UserSerializer(request.user)
            extra_info = {}
            user = request.user

            # Lấy thông tin lớp chủ nhiệm nếu là GVCN (qua HomeroomAssignment hoặc homeroom_classes)
            active_homeroom = None
            if hasattr(user, 'homeroom_assignments'):
                active_hr_assignment = user.homeroom_assignments.filter(is_active=True).select_related('school_class').first()
                if active_hr_assignment:
                    active_homeroom = active_hr_assignment.school_class
            if not active_homeroom and hasattr(user, 'homeroom_classes'):
                active_homeroom = user.homeroom_classes.filter(is_active=True).first()

            if active_homeroom:
                extra_info['homeroom_class_id'] = active_homeroom.id
                extra_info['homeroom_class_name'] = active_homeroom.name
                extra_info['homeroom_grade'] = active_homeroom.grade

            # Lấy danh sách lớp giảng dạy nếu là GVBM
            if hasattr(user, 'teaching_assignments'):
                assignments = user.teaching_assignments.filter(is_active=True).select_related('school_class')
                extra_info['teaching_classes'] = [
                    {
                        'id': a.school_class.id,
                        'name': a.school_class.name,
                        'grade': a.school_class.grade,
                        'subject': a.subject,
                        'student_count': a.school_class.student_count
                    }
                    for a in assignments
                ]
            else:
                extra_info['teaching_classes'] = []

            # Thông tin học sinh
            if user.is_student and hasattr(user, 'student_profile'):
                profile = user.student_profile
                extra_info['student_id'] = profile.id
                extra_info['student_code'] = profile.student_code
                extra_info['class_id'] = profile.school_class_id
                extra_info['class_name'] = profile.school_class.name
                extra_info['grade'] = profile.school_class.grade
                hr_teacher = profile.school_class.homeroom_teacher
                extra_info['homeroom_teacher_name'] = hr_teacher.full_name or hr_teacher.username if hr_teacher else 'Chưa phân công'

            # Thông tin yêu cầu đổi lớp đang chờ duyệt nếu có
            if user.verification_info and user.verification_info.startswith('{'):
                try:
                    v_info = json.loads(user.verification_info)
                    if isinstance(v_info, dict):
                        extra_info['pending_class_change'] = v_info.get('pending_class_change')
                except Exception:
                    pass

            data = serializer.data
            data['is_gvcn'] = user.is_gvcn
            data['is_gvbm'] = user.is_gvbm
            data['is_admin'] = user.is_admin
            data['is_student'] = user.is_student
            data['meta'] = extra_info
            return Response({'authenticated': True, 'user': data})
        return Response({'authenticated': False, 'user': None})


class ProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(ProfileSerializer(request.user, context={'request': request}).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data, partial=True, context={'request': request})
        if not serializer.is_valid():
            first_err = next(iter(serializer.errors.values()))
            if isinstance(first_err, list):
                first_err = first_err[0]
            return Response({'error': str(first_err), 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        updates = serializer.validated_data
        changed_fields = []
        info_message = None

        with transaction.atomic():
            # 1. Cập nhật Họ và tên
            if 'full_name' in updates and user.full_name != updates['full_name']:
                user.full_name = updates['full_name']
                changed_fields.append(('full_name', 'Họ tên hiển thị'))
                if hasattr(user, 'student_profile'):
                    user.student_profile.full_name = updates['full_name']
                    user.student_profile.save(update_fields=['full_name'])
                if hasattr(user, 'teacher_profile'):
                    user.teacher_profile.full_name = updates['full_name']
                    user.teacher_profile.save(update_fields=['full_name'])

            # 2. Cập nhật Số điện thoại
            if 'phone' in updates and user.phone != updates['phone']:
                user.phone = updates['phone']
                changed_fields.append(('phone', 'Số điện thoại'))
                if hasattr(user, 'teacher_profile'):
                    user.teacher_profile.phone = updates['phone']
                    user.teacher_profile.save(update_fields=['phone'])

            # 3. Cập nhật Email (kiểm tra trùng lặp qua serializer)
            if 'email' in updates and user.email != updates['email']:
                user.email = updates['email']
                changed_fields.append(('email', 'Email'))

            # 4. Đổi Mật khẩu
            if 'new_password' in updates and updates['new_password']:
                user.set_password(updates['new_password'])
                user.must_change_password = False
                if hasattr(request, 'session'):
                    update_session_auth_hash(request, user)
                changed_fields.append(('password', 'Mật khẩu'))
                info_message = 'Đã cập nhật mật khẩu mới thành công.'

            # 5. Xử lý hủy yêu cầu đổi lớp học sinh
            if updates.get('cancel_class_change'):
                if user.verification_info and user.verification_info.startswith('{'):
                    try:
                        v_info = json.loads(user.verification_info)
                        if 'pending_class_change' in v_info:
                            del v_info['pending_class_change']
                            user.verification_info = json.dumps(v_info, ensure_ascii=False) if v_info else ''
                            changed_fields.append(('verification_info', 'Hủy yêu cầu đổi lớp'))
                            info_message = 'Đã hủy yêu cầu chuyển lớp.'
                    except Exception:
                        pass

            # 6. Xử lý yêu cầu đổi lớp của học sinh (BẮT BUỘC ADMIN DUYỆT)
            target_class_id = updates.get('target_class_id')
            target_class_name = updates.get('target_class_name')
            if (target_class_id or target_class_name) and not updates.get('cancel_class_change'):
                if user.role == User.ROLE_HOC_SINH or user.is_student:
                    from conduct.models import SchoolClass
                    target_class = None
                    if target_class_id:
                        target_class = SchoolClass.objects.filter(id=target_class_id, is_active=True).first()
                    elif target_class_name:
                        target_class = SchoolClass.objects.filter(name__iexact=str(target_class_name).strip(), is_active=True).first()

                    if not target_class:
                        return Response({'error': 'Lớp học yêu cầu chuyển đến không tồn tại hoặc đã bị khóa.'}, status=status.HTTP_400_BAD_REQUEST)

                    curr_sc = getattr(getattr(user, 'student_profile', None), 'school_class', None)
                    if (curr_sc and curr_sc.id == target_class.id) or (user.department_or_class == target_class.name):
                        return Response({'error': f'Bạn hiện đang học ở lớp {target_class.name} rồi! Vui lòng chọn lớp khác.'}, status=status.HTTP_400_BAD_REQUEST)

                    # Ghi nhận yêu cầu đổi lớp vào verification_info (KHÔNG THAY ĐỔI LỚP THỰC TẾ TRƯỚC KHI ADMIN DUYỆT)
                    v_info = {}
                    if user.verification_info and user.verification_info.startswith('{'):
                        try:
                            v_info = json.loads(user.verification_info)
                        except Exception:
                            v_info = {}

                    v_info['pending_class_change'] = {
                        'target_class_id': target_class.id,
                        'target_class_name': target_class.name,
                        'previous_class': curr_sc.name if curr_sc else (user.department_or_class or ''),
                        'reason': updates.get('class_change_reason', '').strip(),
                        'requested_at': timezone.now().isoformat()
                    }
                    user.verification_info = json.dumps(v_info, ensure_ascii=False)
                    changed_fields.append(('verification_info', f'Gửi yêu cầu đổi sang lớp {target_class.name} (chờ Admin duyệt)'))
                    info_message = f'Yêu cầu chuyển sang lớp {target_class.name} đã được gửi và đang chờ Quản trị viên xét duyệt.'

                    # Gửi thông báo đến Quản trị viên
                    admins = User.objects.filter(role__in=[User.ROLE_ADMIN, User.ROLE_SUPER_ADMIN], is_active=True)
                    for adm in admins:
                        Notification.objects.create(
                            recipient=adm,
                            notification_type=Notification.TYPE_SYSTEM,
                            title='Yêu cầu đổi lớp từ học sinh',
                            message=f'Học sinh {user.full_name or user.username} ({curr_sc.name if curr_sc else user.department_or_class or ""}) gửi yêu cầu chuyển sang lớp {target_class.name}.',
                            link='/#users'
                        )

            # 7. Xử lý giáo viên đổi lớp (KHÔNG CẦN CAN THIỆP CỦA ADMIN - HIỆU LỰC NGAY LẬP TỨC)
            if 'teaching_classes' in updates and (user.is_gvbm or user.is_gvcn or user.role in [User.ROLE_GVBM, User.ROLE_GVCN]):
                from conduct.models import SchoolClass, TeacherClassAssignment, Teacher
                new_classes_raw = updates.get('teaching_classes') or []
                matched_classes = SchoolClass.objects.filter(
                    Q(name__in=new_classes_raw) | Q(id__in=[c for c in new_classes_raw if str(c).isdigit()]),
                    is_active=True
                )

                subj = updates.get('subject') or (updates.get('subjects')[0] if updates.get('subjects') else '')
                if not subj and hasattr(user, 'teacher_profile') and user.teacher_profile.subject:
                    subj = user.teacher_profile.subject
                if not subj:
                    subj = 'Bộ môn'

                # Hủy kích hoạt phân công cho các lớp không còn dạy
                TeacherClassAssignment.objects.filter(teacher=user, is_active=True).exclude(
                    school_class__in=matched_classes
                ).update(is_active=False)

                # Kích hoạt hoặc tạo mới phân công cho các lớp được chọn
                for sc in matched_classes:
                    assn, _ = TeacherClassAssignment.objects.get_or_create(
                        teacher=user,
                        school_class=sc,
                        subject=subj,
                        defaults={'is_active': True}
                    )
                    if not assn.is_active:
                        assn.is_active = True
                        assn.save(update_fields=['is_active'])

                # Đồng bộ Teacher profile và user.department_or_class
                class_names = list(matched_classes.order_by('grade', 'name').values_list('name', flat=True))
                if class_names:
                    user.department_or_class = ', '.join(class_names)
                    changed_fields.append(('department_or_class', 'Lớp giảng dạy'))

                if hasattr(user, 'teacher_profile'):
                    if subj:
                        user.teacher_profile.subject = subj
                        user.teacher_profile.save(update_fields=['subject'])
                changed_fields.append(('teaching_classes', f'Cập nhật {len(class_names)} lớp giảng dạy (hiệu lực ngay lập tức)'))
                info_message = f'Đã cập nhật danh sách {len(class_names)} lớp giảng dạy thành công.'

            # 8. Lưu các trường thay đổi và ghi AuditLog
            if changed_fields:
                up_fields = [f for f, _ in changed_fields if f in ['full_name', 'phone', 'email', 'department_or_class', 'verification_info', 'password', 'must_change_password']]
                if up_fields:
                    user.save(update_fields=list(set(up_fields)))
                AuditLog.objects.create(
                    user=user,
                    action='UPDATE_PROFILE',
                    resource_type='USER',
                    resource_id=str(user.id),
                    details='Cập nhật hồ sơ: ' + ', '.join(label for _, label in changed_fields) + '.',
                    ip_address=request.META.get('REMOTE_ADDR'),
                )

        data = ProfileSerializer(user, context={'request': request}).data
        res_data = {'profile': data, **data}
        if info_message:
            res_data['message'] = info_message
        return Response(res_data)


class ProfileAvatarAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded = request.FILES.get('avatar')
        if uploaded is None:
            return Response({'error': 'Vui lòng chọn ảnh đại diện.'}, status=status.HTTP_400_BAD_REQUEST)

        max_size = getattr(settings, 'AVATAR_MAX_UPLOAD_SIZE', 5 * 1024 * 1024)
        if uploaded.size > max_size:
            return Response({'error': 'Ảnh đại diện không được vượt quá 5 MB.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with Image.open(uploaded) as image:
                image_format = image.format
                image.verify()
            uploaded.seek(0)
            with Image.open(uploaded) as image:
                width, height = image.size
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            return Response({'error': 'Tệp tải lên không phải ảnh hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

        extensions = {'JPEG': 'jpg', 'PNG': 'png', 'WEBP': 'webp'}
        extension = extensions.get(image_format)
        if extension is None:
            return Response({'error': 'Chỉ chấp nhận ảnh JPG, PNG hoặc WebP.'}, status=status.HTTP_400_BAD_REQUEST)
        if width * height > getattr(settings, 'AVATAR_MAX_PIXELS', 20_000_000):
            return Response({'error': 'Kích thước ảnh quá lớn.'}, status=status.HTTP_400_BAD_REQUEST)

        uploaded.seek(0)
        uploaded.name = f'{uuid.uuid4().hex}.{extension}'
        user = request.user
        old_name = user.avatar.name if user.avatar else ''
        try:
            with transaction.atomic():
                user.avatar.save(uploaded.name, uploaded, save=False)
                saved_name = user.avatar.name
                user.save(update_fields=['avatar'])
                AuditLog.objects.create(
                    user=user,
                    action='UPDATE_PROFILE_AVATAR',
                    resource_type='USER',
                    resource_id=str(user.id),
                    details='Người dùng đã cập nhật ảnh đại diện.',
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
        except (DatabaseError, OSError):
            if user.avatar.name and user.avatar.name != old_name:
                default_storage.delete(user.avatar.name)
            user.avatar.name = old_name
            raise

        if old_name and old_name != saved_name:
            try:
                default_storage.delete(old_name)
            except OSError:
                logger.warning('Could not remove replaced profile avatar for user %s', user.pk)
        return Response(ProfileSerializer(user, context={'request': request}).data)


class ChangePasswordAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0]
            return Response({'error': str(first_error)}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(serializer.validated_data['current_password']):
            return Response(
                {'error': 'Mật khẩu hiện tại không chính xác.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.must_change_password = False
            user.save(update_fields=['password', 'must_change_password'])
            if hasattr(request, 'session'):
                update_session_auth_hash(request, user)
            AuditLog.objects.create(
                user=user,
                action='CHANGE_PASSWORD',
                resource_type='USER',
                resource_id=str(user.id),
                details='Người dùng đã đổi mật khẩu.',
                ip_address=request.META.get('REMOTE_ADDR'),
            )

        return Response({
            'message': 'Đổi mật khẩu thành công.',
            'user': UserSerializer(request.user).data,
        })


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    Phân hệ Quản trị Phê duyệt & Quản lý Người dùng:
    - Bắt buộc kiểm tra quyền Admin / Super Admin ở cả backend và từng thao tác.
    - Cung cấp:
      * Thống kê tài khoản (Tổng, Chờ duyệt, Đã duyệt, Bị từ chối, Tạm khóa)
      * Lọc, tìm kiếm, xem chi tiết
      * Phê duyệt (gán vai trò, phân quyền chuyên biệt)
      * Từ chối (nhập lý do)
      * Yêu cầu bổ sung thông tin
      * Tạm khóa / Kích hoạt lại
      * Xem lịch sử xét duyệt ApprovalLog
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def check_permissions(self, request):
        super().check_permissions(request)
        if not (request.user.is_admin or request.user.is_superuser or request.user.is_doan_truong):
            self.permission_denied(
                request,
                message='Chỉ có Quản trị viên hệ thống (Admin) hoặc Đoàn trường mới có quyền truy cập danh sách người dùng.'
            )

    def get_queryset(self):
        qs = User.objects.all().order_by('-date_joined')

        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(account_status=status_param)

        role_param = self.request.query_params.get('role')
        if role_param:
            qs = qs.filter(role=role_param)

        requested_role_param = self.request.query_params.get('requested_role')
        if requested_role_param:
            qs = qs.filter(requested_role=requested_role_param)

        search_param = self.request.query_params.get('search')
        if search_param:
            q = search_param.strip()
            qs = qs.filter(
                Q(username__icontains=q) |
                Q(full_name__icontains=q) |
                Q(email__icontains=q) |
                Q(department_or_class__icontains=q) |
                Q(phone__icontains=q)
            )

        return qs

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Thống kê tổng quan tình trạng tài khoản cho Dashboard Admin"""
        from django.db.models import Count, Q
        agg = User.objects.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(account_status=User.STATUS_PENDING)),
            approved=Count('id', filter=Q(account_status=User.STATUS_APPROVED)),
            rejected=Count('id', filter=Q(account_status=User.STATUS_REJECTED)),
            suspended=Count('id', filter=Q(account_status=User.STATUS_SUSPENDED)),
        )
        return Response(agg)

    def destroy(self, request, *args, **kwargs):
        """Xóa vĩnh viễn tài khoản bởi Quản trị viên (Admin / Super Admin)."""
        if not (request.user.is_admin or request.user.is_super_admin or request.user.is_superuser):
            return Response(
                {'error': 'Chỉ có Quản trị viên hệ thống (Admin) mới có quyền xóa tài khoản.'},
                status=status.HTTP_403_FORBIDDEN
            )

        target_user = self.get_object()

        # Không thể tự xóa chính mình
        if target_user.id == request.user.id:
            return Response(
                {'error': 'Bạn không thể tự xóa tài khoản của chính mình.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Quản trị viên thường không được xóa Super Admin
        if (target_user.is_super_admin or target_user.is_superuser) and not request.user.is_super_admin and not request.user.is_superuser:
            return Response(
                {'error': 'Chỉ có Quản trị viên tối cao (Super Admin) mới có quyền xóa tài khoản Super Admin khác.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Không được xóa Super Admin duy nhất còn lại
        if target_user.is_super_admin or target_user.is_superuser:
            super_admin_count = User.objects.filter(
                Q(role=User.ROLE_SUPER_ADMIN) | Q(is_superuser=True),
                account_status=User.STATUS_APPROVED,
                is_active=True
            ).count()
            if super_admin_count <= 1:
                return Response(
                    {'error': 'Không thể xóa Quản trị viên tối cao (Super Admin) duy nhất của hệ thống.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        username = target_user.username
        full_name = target_user.full_name or username
        role_display = target_user.get_role_display()

        with transaction.atomic():
            AuditLog.objects.create(
                user=request.user,
                action='DELETE_USER',
                resource_type='USER',
                resource_id=str(target_user.id),
                details=f"Quản trị viên {request.user.full_name or request.user.username} đã xóa vĩnh viễn tài khoản {username} ({role_display}).",
                ip_address=request.META.get('REMOTE_ADDR'),
            )
            target_user.delete()

        return Response({
            'message': f'Đã xóa vĩnh viễn tài khoản {username} ({full_name}) thành công.'
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Tạo tài khoản trực tiếp bởi Quản trị viên hoặc Đoàn trường"""
        if request.user.is_doan_truong:
            target_role = request.data.get('role')
            if target_role in [User.ROLE_ADMIN, User.ROLE_SUPER_ADMIN, User.ROLE_DOAN_TRUONG]:
                return Response(
                    {'error': 'Đoàn trường không có quyền tạo tài khoản Quản trị viên hoặc Đoàn trường.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        serializer = UserCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from secrets import token_urlsafe
        temporary_password = token_urlsafe(24)
        with transaction.atomic():
            user = serializer.save(temporary_password=temporary_password)
            if user.role == User.ROLE_DOAN_TRUONG:
                user.doan_truong_permissions = []
                user.can_verify_violations = False
                user.can_view_counseling = False
                user.save(update_fields=['doan_truong_permissions', 'can_verify_violations', 'can_view_counseling'])
            user.approved_by = request.user
            user.approved_at = timezone.now()
            user.save(update_fields=['approved_by', 'approved_at'])

            AuditLog.objects.create(
                user=request.user,
                action='CREATE_USER',
                resource_type='USER',
                resource_id=str(user.id),
                details=f"Quản trị viên đã tạo tài khoản {user.username} với vai trò {user.get_role_display()}.",
                ip_address=request.META.get('REMOTE_ADDR'),
            )
            ApprovalLog.objects.create(
                user=user,
                reviewer=request.user,
                previous_status='NEW',
                new_status=User.STATUS_APPROVED,
                assigned_role=user.role,
                reason='Tài khoản được tạo trực tiếp bởi Quản trị viên',
                internal_notes='Tạo chủ động'
            )

        return Response({
            'message': 'Tạo tài khoản thành công. Hãy gửi mật khẩu tạm thời an toàn cho người dùng.',
            'temporary_password': temporary_password,
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)

    def _handle_class_change_review(self, request, target_user, action_type, reason='', internal_notes=''):
        from conduct.models import SchoolClass, Student
        user = request.user
        if not (user.is_admin or user.is_super_admin or (user.is_doan_truong and user.has_custom_perm('student_accounts.approve'))):
            return Response({'error': 'Bạn không có quyền xét duyệt yêu cầu đổi lớp của học sinh.'}, status=status.HTTP_403_FORBIDDEN)

        v_info = {}
        if target_user.verification_info and target_user.verification_info.startswith('{'):
            try:
                v_info = json.loads(target_user.verification_info)
            except Exception:
                v_info = {}

        pending = v_info.get('pending_class_change') if isinstance(v_info, dict) else None
        if not pending:
            return Response({'error': 'Học sinh này hiện không có yêu cầu chuyển lớp nào đang chờ duyệt.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if action_type in ['approve', 'approve_class_change']:
                target_class_id = pending.get('target_class_id')
                target_class_name = pending.get('target_class_name')
                target_class = None
                if target_class_id:
                    target_class = SchoolClass.objects.filter(id=target_class_id, is_active=True).first()
                if not target_class and target_class_name:
                    target_class = SchoolClass.objects.filter(name__iexact=str(target_class_name).strip(), is_active=True).first()

                if not target_class:
                    return Response({'error': f'Lớp học đích ({target_class_name}) không tồn tại hoặc đã bị khóa.'}, status=status.HTTP_400_BAD_REQUEST)

                # Cập nhật hồ sơ Student
                if hasattr(target_user, 'student_profile'):
                    student = target_user.student_profile
                    student.school_class = target_class
                    student.save(update_fields=['school_class'])
                else:
                    Student.objects.create(
                        user=target_user,
                        student_code=f"HK{target_class.grade}-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                        full_name=target_user.full_name or target_user.username,
                        date_of_birth=timezone.now().date(),
                        gender='M',
                        school_class=target_class,
                        status='STUDYING'
                    )

                prev_class = pending.get('previous_class') or target_user.department_or_class or 'Lớp cũ'
                target_user.department_or_class = target_class.name
                del v_info['pending_class_change']
                target_user.verification_info = json.dumps(v_info, ensure_ascii=False) if v_info else ''
                target_user.save(update_fields=['department_or_class', 'verification_info'])

                ApprovalLog.objects.create(
                    user=target_user,
                    reviewer=user,
                    previous_status=target_user.account_status,
                    new_status=target_user.account_status,
                    assigned_role=target_user.role,
                    reason=f'Phê duyệt chuyển từ lớp {prev_class} sang {target_class.name}. {reason}'.strip(),
                    internal_notes=internal_notes or 'Phê duyệt chuyển lớp học sinh'
                )

                Notification.objects.create(
                    recipient=target_user,
                    notification_type=Notification.TYPE_APPROVAL,
                    title='Yêu cầu đổi lớp đã được phê duyệt!',
                    message=f'Chúc mừng! Yêu cầu chuyển từ lớp {prev_class} sang lớp {target_class.name} của bạn đã được Quản trị viên {user.full_name or user.username} phê duyệt thành công.',
                    link='/'
                )

                AuditLog.objects.create(
                    user=user,
                    action='APPROVE_CLASS_CHANGE',
                    resource_type='USER',
                    resource_id=str(target_user.id),
                    details=f'{user.username} đã phê duyệt chuyển học sinh {target_user.username} ({target_user.full_name}) từ {prev_class} sang {target_class.name}.',
                    ip_address=request.META.get('REMOTE_ADDR')
                )

                return Response({
                    'message': f'Đã phê duyệt chuyển học sinh {target_user.full_name or target_user.username} sang lớp {target_class.name}.',
                    'user': UserSerializer(target_user).data
                })

            else:
                prev_class = pending.get('previous_class') or target_user.department_or_class or ''
                req_class = pending.get('target_class_name') or 'lớp mới'
                del v_info['pending_class_change']
                target_user.verification_info = json.dumps(v_info, ensure_ascii=False) if v_info else ''
                target_user.save(update_fields=['verification_info'])

                ApprovalLog.objects.create(
                    user=target_user,
                    reviewer=user,
                    previous_status=target_user.account_status,
                    new_status=target_user.account_status,
                    assigned_role=target_user.role,
                    reason=f'Từ chối chuyển sang lớp {req_class}. Lý do: {reason or "Không được phê duyệt"}'.strip(),
                    internal_notes=internal_notes or 'Từ chối chuyển lớp học sinh'
                )

                Notification.objects.create(
                    recipient=target_user,
                    notification_type=Notification.TYPE_SYSTEM,
                    title='Yêu cầu đổi lớp không được phê duyệt',
                    message=f'Yêu cầu chuyển sang lớp {req_class} của bạn đã bị từ chối. Lý do: {reason or "Chưa đủ điều kiện chuyển lớp."}',
                    link='/'
                )

                AuditLog.objects.create(
                    user=user,
                    action='REJECT_CLASS_CHANGE',
                    resource_type='USER',
                    resource_id=str(target_user.id),
                    details=f'{user.username} đã từ chối yêu cầu đổi lớp của học sinh {target_user.username}.',
                    ip_address=request.META.get('REMOTE_ADDR')
                )

                return Response({
                    'message': f'Đã từ chối yêu cầu chuyển lớp của học sinh {target_user.full_name or target_user.username}.',
                    'user': UserSerializer(target_user).data
                })

    @action(detail=True, methods=['post'], url_path='review-class-change')
    def review_class_change(self, request, pk=None):
        target_user = self.get_object()
        action_type = request.data.get('action') or 'approve'
        reason = (request.data.get('reason') or '').strip()
        internal_notes = (request.data.get('internal_notes') or '').strip()
        return self._handle_class_change_review(request, target_user, action_type, reason, internal_notes)

    def _sync_user_role_and_assignments(self, target_user, assigned_role, data, request):
        """
        Đồng bộ chính xác chức vụ, hồ sơ, phân công giảng dạy (nhiều lớp) và phân công GVCN (1 lớp duy nhất).
        Đảm bảo không bị xung đột, xóa bỏ các gán quyền cũ mâu thuẫn.
        """
        from conduct.models import SchoolClass, Teacher, TeacherClassAssignment, HomeroomAssignment, Student
        import json
        import re

        class_id = data.get('class_id')
        homeroom_class = data.get('homeroom_class')
        homeroom_class_id = data.get('homeroom_class_id')
        subject = data.get('subject')
        subjects = data.get('subjects') or []
        teaching_classes = data.get('teaching_classes') or []
        teaching_class_ids = data.get('teaching_class_ids') or []
        department_or_class = data.get('department_or_class')
        internal_notes = data.get('internal_notes', '')

        if assigned_role in [User.ROLE_GVBM, User.ROLE_GVCN]:
            # 1. Xác định môn học
            subj = (subject or '').strip()
            if not subj and subjects:
                subj = ', '.join([str(s).strip() for s in subjects if str(s).strip()])
            if not subj and department_or_class:
                dept = str(department_or_class).strip()
                if dept.startswith('Môn: '):
                    subj = dept[5:].strip()
                elif dept.startswith('Môn '):
                    subj = dept[4:].strip()
                elif not re.match(r'^\d+[A-Za-zĐđ]+\d*$', dept):
                    subj = dept
            if not subj:
                subj = 'Môn học'

            teacher_prof, _ = Teacher.objects.get_or_create(
                user=target_user,
                defaults={
                    'teacher_code': f"GV-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                    'full_name': target_user.full_name or target_user.username,
                    'subject': subj,
                    'phone': target_user.phone or ''
                }
            )
            if subj and teacher_prof.subject != subj:
                teacher_prof.subject = subj
                teacher_prof.save(update_fields=['subject'])

            # 2. Xử lý phân công các lớp giảng dạy (giáo viên được chọn nhiều lớp)
            classes_to_teach = []
            if teaching_class_ids:
                classes_to_teach = list(SchoolClass.objects.filter(id__in=teaching_class_ids, is_active=True))
            elif teaching_classes:
                clean_names = [str(c).strip() for c in teaching_classes if str(c).strip()]
                classes_to_teach = list(SchoolClass.objects.filter(name__in=clean_names, is_active=True))
            elif target_user.verification_info:
                try:
                    v_info = json.loads(target_user.verification_info)
                    if isinstance(v_info, dict):
                        v_c = v_info.get('teaching_classes') or []
                        classes_to_teach = list(SchoolClass.objects.filter(name__in=[str(x).strip() for x in v_c], is_active=True))
                except Exception:
                    pass

            if classes_to_teach:
                # Deactivate assignments not in classes_to_teach
                TeacherClassAssignment.objects.filter(teacher=target_user, is_active=True).exclude(
                    school_class__in=classes_to_teach
                ).update(is_active=False, end_date=timezone.now().date())
                # Deactivate assignments in classes_to_teach with old subject
                TeacherClassAssignment.objects.filter(teacher=target_user, is_active=True, school_class__in=classes_to_teach).exclude(
                    subject=subj
                ).update(is_active=False, end_date=timezone.now().date())

                for sc_obj in classes_to_teach:
                    tca, created = TeacherClassAssignment.objects.get_or_create(
                        teacher=target_user,
                        school_class=sc_obj,
                        subject=subj,
                        defaults={'is_active': True, 'assigned_by': request.user, 'start_date': timezone.now().date()}
                    )
                    if not created and not tca.is_active:
                        tca.is_active = True
                        tca.end_date = None
                        tca.save(update_fields=['is_active', 'end_date', 'updated_at'])
            else:
                TeacherClassAssignment.objects.filter(teacher=target_user, is_active=False).update(is_active=True)

            # 3. Phân công Giáo viên chủ nhiệm (GVCN)
            if assigned_role == User.ROLE_GVCN:
                hr_sc = None
                if homeroom_class_id:
                    hr_sc = SchoolClass.objects.filter(id=homeroom_class_id, is_active=True).first()
                elif homeroom_class:
                    hr_sc = SchoolClass.objects.filter(name__iexact=str(homeroom_class).strip(), is_active=True).first()
                elif department_or_class:
                    hr_sc = SchoolClass.objects.filter(name__iexact=str(department_or_class).strip(), is_active=True).first()

                if hr_sc:
                    # Thu hồi GVCN cũ trên lớp này (nếu đang là giáo viên khác)
                    HomeroomAssignment.objects.filter(school_class=hr_sc, is_active=True).exclude(
                        teacher=target_user
                    ).update(is_active=False, end_date=timezone.now().date())

                    # Thu hồi nhiệm vụ GVCN cũ của giáo viên này trên các lớp khác
                    HomeroomAssignment.objects.filter(teacher=target_user, is_active=True).exclude(
                        school_class=hr_sc
                    ).update(is_active=False, end_date=timezone.now().date())
                    SchoolClass.objects.filter(homeroom_teacher=target_user).exclude(
                        id=hr_sc.id
                    ).update(homeroom_teacher=None)

                    # Bổ nhiệm giáo viên này làm GVCN của hr_sc
                    hr_assign, _ = HomeroomAssignment.objects.get_or_create(
                        teacher=target_user,
                        school_class=hr_sc,
                        is_active=True,
                        defaults={
                            'assigned_by': request.user,
                            'start_date': timezone.now().date(),
                            'notes': internal_notes or 'Phân công GVCN khi xét duyệt / phân quyền'
                        }
                    )
                    if not hr_assign.is_active:
                        hr_assign.is_active = True
                        hr_assign.end_date = None
                        hr_assign.save(update_fields=['is_active', 'end_date', 'updated_at'])

                    hr_sc.homeroom_teacher = target_user
                    hr_sc.save(update_fields=['homeroom_teacher'])

                    target_user.department_or_class = hr_sc.name
                    target_user.save(update_fields=['department_or_class'])
            else:
                # Role là GVBM -> Thu hồi mọi vai trò GVCN trước đó
                SchoolClass.objects.filter(homeroom_teacher=target_user).update(homeroom_teacher=None)
                HomeroomAssignment.objects.filter(teacher=target_user, is_active=True).update(
                    is_active=False, end_date=timezone.now().date()
                )
                target_user.department_or_class = f"Môn {subj}"
                target_user.save(update_fields=['department_or_class'])

        elif assigned_role == User.ROLE_HOC_SINH:
            # Thu hồi nhiệm kỳ GVCN nếu trước đó từng có
            SchoolClass.objects.filter(homeroom_teacher=target_user).update(homeroom_teacher=None)
            HomeroomAssignment.objects.filter(teacher=target_user, is_active=True).update(
                is_active=False, end_date=timezone.now().date()
            )

            sclass = None
            if class_id:
                sclass = SchoolClass.objects.filter(id=class_id, is_active=True).first()
            elif department_or_class:
                sclass = SchoolClass.objects.filter(name__iexact=str(department_or_class).strip(), is_active=True).first()

            if sclass:
                target_user.department_or_class = sclass.name
                target_user.save(update_fields=['department_or_class'])

                student_prof = getattr(target_user, 'student_profile', None)
                if student_prof:
                    student_prof.school_class = sclass
                    student_prof.save(update_fields=['school_class'])
                else:
                    Student.objects.get_or_create(
                        user=target_user,
                        defaults={
                            'student_code': f"HK{sclass.grade}-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                            'full_name': target_user.full_name or target_user.username,
                            'date_of_birth': timezone.now().date(),
                            'gender': 'M',
                            'school_class': sclass,
                            'status': 'STUDYING'
                        }
                    )
        else:
            # Các vai trò khác (Admin, Đoàn trường, BGH, Sao đỏ, etc.)
            SchoolClass.objects.filter(homeroom_teacher=target_user).update(homeroom_teacher=None)
            HomeroomAssignment.objects.filter(teacher=target_user, is_active=True).update(
                is_active=False, end_date=timezone.now().date()
            )
            if department_or_class:
                target_user.department_or_class = department_or_class
                target_user.save(update_fields=['department_or_class'])

    @action(detail=True, methods=['post'], url_path='review')
    def review(self, request, pk=None):
        """
        Quy trình xét duyệt toàn diện của Admin:
        - approve: Phê duyệt và gán vai trò
        - reject: Từ chối yêu cầu kèm lý do
        - request_info: Yêu cầu bổ sung thông tin
        - suspend: Tạm khóa tài khoản
        - reactivate: Kích hoạt lại tài khoản
        """
        target_user = self.get_object()
        serializer = ApprovalActionSerializer(data=request.data)
        if not serializer.is_valid():
            first_err = next(iter(serializer.errors.values()))
            if isinstance(first_err, list):
                first_err = first_err[0]
            return Response({'error': str(first_err), 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        action_type = serializer.validated_data['action']
        if action_type in ['approve_class_change', 'reject_class_change']:
            reason = serializer.validated_data.get('reason', '').strip()
            internal_notes = serializer.validated_data.get('internal_notes', '').strip()
            return self._handle_class_change_review(request, target_user, action_type, reason, internal_notes)
        assigned_role = serializer.validated_data.get('assigned_role')
        department_or_class = serializer.validated_data.get('department_or_class')
        can_verify = serializer.validated_data.get('can_verify_violations')
        can_counseling = serializer.validated_data.get('can_view_counseling')
        reason = serializer.validated_data.get('reason', '').strip()
        internal_notes = serializer.validated_data.get('internal_notes', '').strip()

        # Quy tắc: Đoàn trường không được thao tác trên tài khoản Quản trị viên
        if (target_user.is_admin or target_user.is_super_admin) and request.user.is_doan_truong:
            return Response(
                {'error': 'Cán bộ Đoàn trường không có quyền thao tác trên tài khoản Quản trị viên.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Quy tắc: Đoàn trường không được cấp quyền Quản trị viên hoặc Đoàn trường
        if request.user.is_doan_truong and assigned_role in [User.ROLE_ADMIN, User.ROLE_SUPER_ADMIN, User.ROLE_DOAN_TRUONG]:
            return Response(
                {'error': 'Cán bộ Đoàn trường chỉ được xét duyệt tài khoản học sinh và giáo viên, không được cấp quyền Quản trị viên hoặc Đoàn trường.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Quy tắc: Không thể tự phê duyệt hoặc thay đổi trạng thái của chính mình
        if target_user.id == request.user.id:
            return Response(
                {'error': 'Người dùng không thể tự phê duyệt hoặc thay đổi trạng thái của chính mình.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Quy tắc: Không được khóa hoặc hạ cấp Super Admin duy nhất
        if target_user.is_super_admin:
            # Admin thông thường không được phép chỉnh sửa Super Admin
            if not request.user.is_super_admin:
                return Response(
                    {'error': 'Chỉ có Quản trị viên tối cao (Super Admin) mới có quyền thao tác trên tài khoản Super Admin khác.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if action_type in ['reject', 'suspend']:
                super_admin_count = User.objects.filter(
                    Q(role=User.ROLE_SUPER_ADMIN) | Q(is_superuser=True),
                    account_status=User.STATUS_APPROVED,
                    is_active=True
                ).count()
                if super_admin_count <= 1:
                    return Response(
                        {'error': 'Không thể khóa hoặc vô hiệu hóa Quản trị viên tối cao (Super Admin) duy nhất của hệ thống.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        previous_status = target_user.account_status

        with transaction.atomic():
            if action_type == 'approve':
                target_user.account_status = User.STATUS_APPROVED
                target_user.profile_completed = True
                target_user.is_active = True
                target_user.role = assigned_role
                target_user.approved_by = request.user
                target_user.approved_at = timezone.now()
                target_user.rejection_reason = ''
                if department_or_class:
                    target_user.department_or_class = department_or_class
                if assigned_role == User.ROLE_DOAN_TRUONG:
                    target_user.doan_truong_permissions = []
                    target_user.can_verify_violations = False
                    target_user.can_view_counseling = False
                elif can_verify is not None:
                    target_user.can_verify_violations = bool(can_verify)
                if assigned_role != User.ROLE_DOAN_TRUONG and can_counseling is not None:
                    target_user.can_view_counseling = bool(can_counseling)
                if internal_notes:
                    target_user.internal_notes = internal_notes
                target_user.save()

                # Đồng bộ hồ sơ và phân công vai trò (GVCN 1 lớp, giáo viên nhiều lớp, học sinh 1 lớp)
                self._sync_user_role_and_assignments(target_user, assigned_role, serializer.validated_data, request)

                Notification.objects.create(
                    recipient=target_user,
                    notification_type=Notification.TYPE_APPROVAL,
                    title='Tài khoản của bạn đã được phê duyệt!',
                    message=(
                        f'Chúc mừng bạn! Yêu cầu đăng ký tài khoản đã được Quản trị viên {request.user.full_name or request.user.username} '
                        f'phê duyệt với vai trò [{target_user.get_role_display()}]. Bạn có thể đăng nhập và sử dụng hệ thống ngay bây giờ.'
                    ),
                    link='/'
                )
                success_message = f'Đã phê duyệt tài khoản {target_user.username} thành công với vai trò {target_user.get_role_display()}.'

            elif action_type == 'reject':
                target_user.account_status = User.STATUS_REJECTED
                target_user.is_active = True
                target_user.rejection_reason = reason
                if internal_notes:
                    target_user.internal_notes = internal_notes
                target_user.save()

                # Đồng bộ hồ sơ Teacher / Student nếu chưa có
                if target_user.role in [User.ROLE_GVBM, User.ROLE_GVCN]:
                    from conduct.models import Teacher
                    subj = target_user.department_or_class or 'Môn học'
                    if subj.startswith('Môn '):
                        subj = subj[4:].strip()
                    if not hasattr(target_user, 'teacher_profile'):
                        Teacher.objects.get_or_create(
                            user=target_user,
                            defaults={
                                'teacher_code': f"GV-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                                'full_name': target_user.full_name or target_user.username,
                                'subject': subj,
                                'phone': target_user.phone
                            }
                        )
                elif target_user.role == User.ROLE_HOC_SINH:
                    from conduct.models import Student, SchoolClass
                    if not hasattr(target_user, 'student_profile'):
                        sclass = SchoolClass.objects.filter(name=target_user.department_or_class, is_active=True).first()
                        if sclass:
                            Student.objects.get_or_create(
                                user=target_user,
                                defaults={
                                    'student_code': f"HK{sclass.grade}-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                                    'full_name': target_user.full_name or target_user.username,
                                    'date_of_birth': timezone.now().date(),
                                    'gender': 'M',
                                    'school_class': sclass,
                                    'status': 'STUDYING'
                                }
                            )

                Notification.objects.create(
                    recipient=target_user,
                    notification_type=Notification.TYPE_APPROVAL,
                    title='Thông báo về yêu cầu đăng ký tài khoản',
                    message=f'Yêu cầu đăng ký của bạn chưa được chấp thuận. Lý do: {reason}. Vui lòng liên hệ nhà trường để được hỗ trợ.',
                    link='/'
                )
                success_message = f'Đã từ chối yêu cầu đăng ký của {target_user.username}.'

            elif action_type == 'request_info':
                target_user.account_status = User.STATUS_PENDING
                target_user.rejection_reason = f'Yêu cầu bổ sung thông tin: {reason}'
                if internal_notes:
                    target_user.internal_notes = internal_notes
                target_user.save()

                # Đồng bộ hồ sơ Teacher / Student nếu chưa có
                if target_user.role in [User.ROLE_GVBM, User.ROLE_GVCN]:
                    from conduct.models import Teacher
                    subj = target_user.department_or_class or 'Môn học'
                    if subj.startswith('Môn '):
                        subj = subj[4:].strip()
                    if not hasattr(target_user, 'teacher_profile'):
                        Teacher.objects.get_or_create(
                            user=target_user,
                            defaults={
                                'teacher_code': f"GV-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                                'full_name': target_user.full_name or target_user.username,
                                'subject': subj,
                                'phone': target_user.phone
                            }
                        )
                elif target_user.role == User.ROLE_HOC_SINH:
                    from conduct.models import Student, SchoolClass
                    if not hasattr(target_user, 'student_profile'):
                        sclass = SchoolClass.objects.filter(name=target_user.department_or_class, is_active=True).first()
                        if sclass:
                            Student.objects.get_or_create(
                                user=target_user,
                                defaults={
                                    'student_code': f"HK{sclass.grade}-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                                    'full_name': target_user.full_name or target_user.username,
                                    'date_of_birth': timezone.now().date(),
                                    'gender': 'M',
                                    'school_class': sclass,
                                    'status': 'STUDYING'
                                }
                            )

                Notification.objects.create(
                    recipient=target_user,
                    notification_type=Notification.TYPE_APPROVAL,
                    title='Yêu cầu bổ sung thông tin tài khoản',
                    message=f'Quản trị viên yêu cầu bạn bổ sung thông tin để xét duyệt: {reason}',
                    link='/'
                )
                success_message = f'Đã gửi yêu cầu bổ sung thông tin đến {target_user.username}.'

            elif action_type == 'suspend':
                target_user.account_status = User.STATUS_SUSPENDED
                target_user.is_active = True
                target_user.rejection_reason = reason
                if internal_notes:
                    target_user.internal_notes = internal_notes
                target_user.save()

                # Đồng bộ hồ sơ Teacher / Student nếu chưa có
                if target_user.role in [User.ROLE_GVBM, User.ROLE_GVCN]:
                    from conduct.models import Teacher
                    subj = target_user.department_or_class or 'Môn học'
                    if subj.startswith('Môn '):
                        subj = subj[4:].strip()
                    if not hasattr(target_user, 'teacher_profile'):
                        Teacher.objects.get_or_create(
                            user=target_user,
                            defaults={
                                'teacher_code': f"GV-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                                'full_name': target_user.full_name or target_user.username,
                                'subject': subj,
                                'phone': target_user.phone
                            }
                        )
                elif target_user.role == User.ROLE_HOC_SINH:
                    from conduct.models import Student, SchoolClass
                    if not hasattr(target_user, 'student_profile'):
                        sclass = SchoolClass.objects.filter(name=target_user.department_or_class, is_active=True).first()
                        if sclass:
                            Student.objects.get_or_create(
                                user=target_user,
                                defaults={
                                    'student_code': f"HK{sclass.grade}-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                                    'full_name': target_user.full_name or target_user.username,
                                    'date_of_birth': timezone.now().date(),
                                    'gender': 'M',
                                    'school_class': sclass,
                                    'status': 'STUDYING'
                                }
                            )

                Notification.objects.create(
                    recipient=target_user,
                    notification_type=Notification.TYPE_APPROVAL,
                    title='Tài khoản tạm thời bị khóa',
                    message=f'Tài khoản của bạn hiện đang bị tạm khóa bởi Quản trị viên. Lý do: {reason}',
                    link='/'
                )
                success_message = f'Đã tạm khóa tài khoản {target_user.username}.'

            elif action_type == 'reactivate':
                target_user.account_status = User.STATUS_APPROVED
                target_user.is_active = True
                target_user.rejection_reason = ''
                if internal_notes:
                    target_user.internal_notes = internal_notes
                target_user.save()

                # Đồng bộ hồ sơ Teacher / Student nếu chưa có
                if target_user.role in [User.ROLE_GVBM, User.ROLE_GVCN]:
                    from conduct.models import Teacher
                    subj = target_user.department_or_class or 'Môn học'
                    if subj.startswith('Môn '):
                        subj = subj[4:].strip()
                    if not hasattr(target_user, 'teacher_profile'):
                        Teacher.objects.get_or_create(
                            user=target_user,
                            defaults={
                                'teacher_code': f"GV-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                                'full_name': target_user.full_name or target_user.username,
                                'subject': subj,
                                'phone': target_user.phone
                            }
                        )
                elif target_user.role == User.ROLE_HOC_SINH:
                    from conduct.models import Student, SchoolClass
                    if not hasattr(target_user, 'student_profile'):
                        sclass = SchoolClass.objects.filter(name=target_user.department_or_class, is_active=True).first()
                        if sclass:
                            Student.objects.get_or_create(
                                user=target_user,
                                defaults={
                                    'student_code': f"HK{sclass.grade}-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                                    'full_name': target_user.full_name or target_user.username,
                                    'date_of_birth': timezone.now().date(),
                                    'gender': 'M',
                                    'school_class': sclass,
                                    'status': 'STUDYING'
                                }
                            )

                Notification.objects.create(
                    recipient=target_user,
                    notification_type=Notification.TYPE_APPROVAL,
                    title='Tài khoản đã được kích hoạt lại',
                    message='Tài khoản của bạn đã được Quản trị viên mở khóa và kích hoạt lại thành công.',
                    link='/'
                )
                success_message = f'Đã kích hoạt lại tài khoản {target_user.username}.'

            # Ghi nhận ApprovalLog
            ApprovalLog.objects.create(
                user=target_user,
                reviewer=request.user,
                previous_status=previous_status,
                new_status=target_user.account_status,
                assigned_role=target_user.role,
                reason=reason,
                internal_notes=internal_notes
            )

            # Ghi nhận AuditLog
            AuditLog.objects.create(
                user=request.user,
                action='REVIEW_USER',
                resource_type='USER',
                resource_id=str(target_user.id),
                details=(
                    f"Quản trị viên {request.user.username} thực hiện thao tác [{action_type}] trên người dùng {target_user.username}. "
                    f"Trạng thái: {previous_status} -> {target_user.account_status}. Vai trò: {target_user.get_role_display()}."
                ),
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return Response({
            'message': success_message,
            'user': UserSerializer(target_user).data
        })

    @action(detail=True, methods=['get'], url_path='approval-history')
    def approval_history(self, request, pk=None):
        """Lấy lịch sử các lần xét duyệt, thay đổi trạng thái của tài khoản"""
        target_user = self.get_object()
        logs = target_user.approval_history.all().order_by('-created_at')
        serializer = ApprovalLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='approve-role')
    def approve_role(self, request, pk=None):
        if not (request.user.is_admin or request.user.is_superuser):
            return Response({'error': 'Chỉ Quản trị viên mới có quyền duyệt và phân quyền chức vụ.'}, status=status.HTTP_403_FORBIDDEN)
        """Duy trì tương thích với luồng duyệt chức vụ cũ"""
        user_obj = self.get_object()
        new_role = request.data.get('role')
        can_verify = request.data.get('can_verify_violations')
        can_counseling = request.data.get('can_view_counseling')
        is_active = request.data.get('is_active')
        phone = request.data.get('phone')

        if phone is not None and (not isinstance(phone, str) or len(phone) > 20):
            return Response({'error': 'Số điện thoại không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

        old_role = user_obj.get_role_display()

        if new_role:
            valid_roles = [r[0] for r in User.ROLE_CHOICES]
            if new_role not in valid_roles:
                return Response({'error': f'Chức vụ không hợp lệ. Phải thuộc: {valid_roles}'}, status=status.HTTP_400_BAD_REQUEST)
            user_obj.role = new_role

        if user_obj.role == User.ROLE_DOAN_TRUONG:
            user_obj.doan_truong_permissions = []
            user_obj.can_verify_violations = False
            user_obj.can_view_counseling = False
        elif can_verify is not None:
            user_obj.can_verify_violations = bool(can_verify)
        if can_counseling is not None:
            user_obj.can_view_counseling = bool(can_counseling)
        if is_active is not None:
            user_obj.is_active = bool(is_active)
            if user_obj.is_active and user_obj.account_status != User.STATUS_APPROVED:
                user_obj.account_status = User.STATUS_APPROVED
        if phone is not None:
            user_obj.phone = phone.strip()

        user_obj.save()

        if new_role:
            self._sync_user_role_and_assignments(user_obj, new_role, request.data, request)

        AuditLog.objects.create(
            user=request.user,
            action='UPDATE_ROLE',
            resource_type='USER',
            resource_id=str(user_obj.id),
            details=(
                f"Quản trị viên {request.user.username} đã duyệt/thay đổi chức vụ của {user_obj.username} "
                f"từ [{old_role}] sang [{user_obj.get_role_display()}]. "
                f"Quyền xác minh: {user_obj.can_verify_violations}, Quyền tư vấn: {user_obj.can_view_counseling}."
            )
        )

        serializer = self.get_serializer(user_obj)
        return Response({
            'message': f'Đã duyệt và cập nhật chức vụ thành công cho người dùng: {user_obj.full_name or user_obj.username}',
            'user': serializer.data
        })


class NotificationViewSet(viewsets.ModelViewSet):
    """Quản lý thông báo người dùng"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        count = Notification.objects.filter(recipient=request.user, read_at__isnull=True).count()
        return Response({'unread_count': count})

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        if not notif.read_at:
            notif.read_at = timezone.now()
            notif.save(update_fields=['read_at'])
        return Response({'message': 'Đã đánh dấu đã đọc.', 'is_read': True})

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        updated = Notification.objects.filter(recipient=request.user, read_at__isnull=True).update(read_at=timezone.now())
        return Response({'message': f'Đã đánh dấu {updated} thông báo đã đọc.'})


class SystemStatsAPIView(APIView):
    """Return only the current user's role scoped dashboard metrics."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from conduct.models import Student, ViolationRecord, SchoolClass
        from competition.models import ClassCompetitionScore, CompetitionPeriod
        from alerts.models import EarlyWarningAlert
        from django.core.cache import cache
        from django.db.models import Count, Q, Avg
        user = request.user
        if not user.is_active or user.account_status != User.STATUS_APPROVED:
            return Response({'error': 'Tài khoản chưa được kích hoạt.'}, status=status.HTTP_403_FORBIDDEN)

        from core.cache_utils import get_cache_version
        cache_key = f"sys_stats_v{get_cache_version()}_{user.id}_{user.role}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        active_alert_statuses = [
            EarlyWarningAlert.STATUS_NEW,
            EarlyWarningAlert.STATUS_RECEIVED,
            EarlyWarningAlert.STATUS_IN_PROGRESS,
        ]
        verified_statuses = [ViolationRecord.STATUS_VERIFIED, ViolationRecord.STATUS_ADJUSTED]
        today = timezone.localdate()
        if user.is_admin or user.is_bgh or user.is_doan_truong:
            from competition.services import get_current_competition_period, get_period_status
            from conduct.models import RedStarReport, RedStarAssignment
            current_year = AcademicYear.objects.filter(is_current=True).first()
            current_period = get_current_competition_period(current_year, CompetitionPeriod.TYPE_WEEK)
            current_semester_period = get_current_competition_period(current_year, CompetitionPeriod.TYPE_SEMESTER)
            scores = ClassCompetitionScore.objects.filter(competition_period=current_period) if current_period else ClassCompetitionScore.objects.none()
            average_score = None
            if scores.exists():
                from django.db.models import Avg
                average_score = scores.aggregate(average=Avg('total_score'))['average']
            current_week_filter = (
                {'occurred_at__date__gte': current_period.start_date,
                 'occurred_at__date__lte': current_period.end_date}
                if current_period else {}
            )
            total_teachers = User.objects.filter(role__in=[User.ROLE_GVCN, User.ROLE_GVBM], account_status=User.STATUS_APPROVED).count()
            pending_accounts = User.objects.filter(account_status=User.STATUS_PENDING).count()
            
            # Tối ưu: Gom các truy vấn count thành aggregate có điều kiện
            v_agg = ViolationRecord.objects.aggregate(
                today=Count('id', filter=Q(occurred_at__date=today)),
                pending=Count('id', filter=Q(status=ViolationRecord.STATUS_PENDING)),
                verified=Count('id', filter=Q(status__in=verified_statuses)),
                rejected=Count('id', filter=Q(status=ViolationRecord.STATUS_REJECTED)),
                appealed=Count('id', filter=Q(status=ViolationRecord.STATUS_APPEALING)),
                verified_week=Count('id', filter=Q(status__in=verified_statuses, **current_week_filter)),
            )

            rs_agg = RedStarReport.objects.aggregate(
                pending=Count('id', filter=Q(status=RedStarReport.STATUS_PENDING)),
                verified=Count('id', filter=Q(status=RedStarReport.STATUS_VERIFIED)),
                rejected=Count('id', filter=Q(status=RedStarReport.STATUS_REJECTED)),
            )

            u_agg = User.objects.aggregate(
                teachers=Count('id', filter=Q(role__in=[User.ROLE_GVCN, User.ROLE_GVBM], account_status=User.STATUS_APPROVED)),
                pending=Count('id', filter=Q(account_status=User.STATUS_PENDING)),
            )

            active_reporters = RedStarAssignment.objects.filter(status=RedStarAssignment.STATUS_ACTIVE).values('student').distinct().count()
            alerts_count = EarlyWarningAlert.objects.filter(status__in=active_alert_statuses).count()
            classes_count = SchoolClass.objects.filter(is_active=True).count()
            students_count = Student.objects.filter(status='STUDYING').count()

            data = {
                'scope': 'school',
                'violations_today': v_agg['today'],
                'violations_pending': v_agg['pending'],
                'violations_verified_week': v_agg['verified_week'],
                'violations_breakdown': {
                    'pending': v_agg['pending'],
                    'verified': v_agg['verified'],
                    'rejected': v_agg['rejected'],
                    'appealed': v_agg['appealed'],
                },
                'red_star_stats': {
                    'pending': rs_agg['pending'],
                    'verified': rs_agg['verified'],
                    'rejected': rs_agg['rejected'],
                    'active_reporters': active_reporters,
                },
                'alerts_active': alerts_count,
                'total_classes': classes_count,
                'total_students': students_count,
                'total_teachers': u_agg['teachers'],
                'pending_accounts': u_agg['pending'],
                'average_score': round(float(average_score), 1) if average_score is not None else None,
                'current_week': current_period.display_week_label if hasattr(current_period, 'display_week_label') else (current_period.name if current_period else None),
                'current_week_number': current_period.week_number if current_period else 7,
                'current_semester': current_semester_period.name if current_semester_period else (current_period.semester.name if current_period and current_period.semester else 'Học kỳ I'),
                'current_semester_number': current_period.semester.semester_number if (current_period and current_period.semester_id) else (current_semester_period.semester.semester_number if current_semester_period and current_semester_period.semester_id else 1),
                'current_week_status': get_period_status(current_period)['display'] if current_period else None,
                'user_role': user.role,
                'user_role_display': user.get_role_display(),
            }
            cache.set(cache_key, data, timeout=20)
            return Response(data)

        if user.is_gvcn:
            from competition.services import get_competition_class_scope, get_current_competition_period
            homeroom_classes = get_competition_class_scope(user)
            active_alerts = EarlyWarningAlert.objects.filter(school_class__in=homeroom_classes, status__in=active_alert_statuses)
            violations = ViolationRecord.objects.filter(school_class__in=homeroom_classes)
            
            current_year = AcademicYear.objects.filter(is_current=True).first()
            current_period = get_current_competition_period(current_year, CompetitionPeriod.TYPE_WEEK)
            homeroom_class = homeroom_classes.first()
            class_score_info = None
            if homeroom_class and current_period:
                cs = ClassCompetitionScore.objects.filter(competition_period=current_period, school_class=homeroom_class).first()
                if cs:
                    class_score_info = {
                        'total_score': float(cs.total_score),
                        'rank': cs.rank,
                        'rank_in_grade': cs.rank_in_grade,
                        'bonus_points': float(cs.bonus_points),
                        'penalty_points': float(cs.penalty_points),
                    }
            
            data = {
                'scope': 'homeroom',
                'my_class_count': homeroom_classes.count(),
                'my_class_names': list(homeroom_classes.values_list('name', flat=True)),
                'my_class_students': Student.objects.filter(school_class__in=homeroom_classes, status='STUDYING').count(),
                'my_class_violations_pending': violations.filter(status=ViolationRecord.STATUS_PENDING).count(),
                'my_class_violations_verified': violations.filter(status__in=verified_statuses).count(),
                'my_class_alerts': active_alerts.count(),
                'class_score_info': class_score_info,
                'user_role': user.role,
                'user_role_display': user.get_role_display(),
            }
            cache.set(cache_key, data, timeout=20)
            return Response(data)

        if getattr(user, 'is_active_red_star', False) or user.is_sao_do:
            from conduct.models import RedStarAssignment, RedStarReport
            active_assignments = user.red_star_assignments.filter(status=RedStarAssignment.STATUS_ACTIVE)
            my_reports = RedStarReport.objects.filter(reporter=user)
            return Response({
                'scope': 'red_star',
                'duty_count': active_assignments.count(),
                'reports_total': my_reports.count(),
                'reports_pending': my_reports.filter(status=RedStarReport.STATUS_PENDING).count(),
                'reports_verified': my_reports.filter(status=RedStarReport.STATUS_VERIFIED).count(),
                'reports_rejected': my_reports.filter(status=RedStarReport.STATUS_REJECTED).count(),
                'user_role': user.role,
                'user_role_display': 'Sao đỏ trực tuần',
            })

        if user.role == User.ROLE_GVBM or user.is_gvbm:
            meta_classes = getattr(user, 'teaching_classes', []) or []
            return Response({
                'scope': 'gvbm',
                'teaching_classes_count': len(meta_classes),
                'subject': getattr(user, 'subject', '') or 'Bộ môn',
                'user_role': user.role,
                'user_role_display': user.get_role_display(),
            })

        if user.is_student:
            student = getattr(user, 'student_profile', None)
            if not student:
                data = {
                    'scope': 'student', 'profile_available': False,
                    'my_violations_verified': 0, 'my_violations_pending': 0,
                    'user_role': user.role, 'user_role_display': user.get_role_display(),
                }
                cache.set(cache_key, data, timeout=20)
                return Response(data)
            own_violations = ViolationRecord.objects.filter(student=student).select_related('rule').order_by('-occurred_at')
            my_violations_list = [
                {
                    'id': v.id,
                    'record_code': v.record_code,
                    'occurred_at': v.occurred_at.strftime('%d/%m/%Y %H:%M') if v.occurred_at else '',
                    'rule_name': v.rule.name if v.rule else (v.custom_title or 'Vi phạm nội quy'),
                    'rule_code': v.rule.code if v.rule else '',
                    'location': v.location or 'Khuôn viên trường',
                    'points_deducted': float(v.points_deducted),
                    'status': v.status,
                    'status_display': v.get_status_display(),
                }
                for v in own_violations[:20]
            ]
            data = {
                'scope': 'student',
                'profile_available': True,
                'student_name': student.full_name,
                'student_code': student.student_code,
                'student_class': student.school_class.name if student.school_class_id else '',
                'student_class_id': student.school_class_id,
                'room_number': student.school_class.room_number if student.school_class_id else '',
                'homeroom_teacher': student.school_class.homeroom_teacher.full_name if (student.school_class_id and student.school_class.homeroom_teacher) else 'Chưa phân công',
                'my_violations_count': own_violations.count(),
                'my_violations_verified': own_violations.filter(status__in=verified_statuses).count(),
                'my_violations_pending': own_violations.filter(status=ViolationRecord.STATUS_PENDING).count(),
                'my_violations_list': my_violations_list,
                'class_score_info': None,
                'user_role': user.role,
                'user_role_display': user.get_role_display(),
            }
            cache.set(cache_key, data, timeout=20)
            return Response(data)

        return Response({
            'scope': 'general',
            'user_role': user.role,
            'user_role_display': user.get_role_display(),
        })


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if not (request.user.is_admin or request.user.is_bgh or request.user.is_doan_truong):
            self.permission_denied(request, message='Bạn không có quyền truy cập nhật ký hệ thống.')

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_bgh or user.is_doan_truong:
            return AuditLog.objects.all()
        return AuditLog.objects.filter(user=user)


class StudentApprovalViewSet(viewsets.ModelViewSet):
    """
    Phân hệ xét duyệt tài khoản học sinh:
    - Chỉ Quản trị viên (Admin) và Cán bộ Đoàn trường được cấp quyền ('student_accounts.approve', 'student_accounts.reject') mới được duyệt/từ chối.
    - GVCN, GVBM, Sao đỏ, Học sinh KHÔNG có quyền phê duyệt/từ chối (403 Forbidden).
    - Bộ lọc: Khối, Lớp, Trạng thái (PENDING, APPROVED, REJECTED, SUSPENDED), Tìm kiếm.
    - Thao tác: Phê duyệt (đơn lẻ / hàng loạt), Từ chối (bắt buộc nhập lý do).
    - Mọi thao tác đều được ghi lại trong ApprovalLog và AuditLog.
    """
    serializer_class = StudentAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def check_permissions(self, request):
        super().check_permissions(request)
        user = request.user
        is_admin = user.is_admin or user.is_superuser
        if self.action in ['approve', 'bulk_approve']:
            allowed = is_admin or (user.is_doan_truong and user.has_custom_perm('student_accounts.approve'))
        elif self.action in ['reject', 'bulk_reject']:
            allowed = is_admin or (user.is_doan_truong and user.has_custom_perm('student_accounts.reject'))
        else:
            allowed = is_admin or (
                user.is_doan_truong and any(
                    user.has_custom_perm(permission)
                    for permission in ['student_accounts.view', 'student_accounts.approve', 'student_accounts.reject']
                )
            )
        if not allowed:
            self.permission_denied(
                request,
                message='Chỉ Quản trị viên và Cán bộ Đoàn trường có quyền mới được truy cập danh sách xét duyệt học sinh.'
            )

    def create(self, request, *args, **kwargs):
        # This endpoint is read-only except for its explicitly defined actions.
        return Response({'error': 'Không thể tạo tài khoản qua màn hình xét duyệt.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def get_queryset(self):
        qs = User.objects.filter(
            role=User.ROLE_HOC_SINH,
        ).filter(
            Q(requested_role__isnull=True) | Q(requested_role='') | Q(requested_role=User.ROLE_HOC_SINH)
        ).select_related('approved_by', 'rejected_by').prefetch_related('student_profile__school_class').order_by('-date_joined')

        # Bộ lọc trạng thái
        status_param = self.request.query_params.get('status')
        if status_param and status_param.upper() != 'ALL':
            qs = qs.filter(account_status=status_param.upper())

        # Bộ lọc khối (10, 11, 12)
        grade_param = self.request.query_params.get('grade')
        if grade_param:
            try:
                g = int(grade_param)
                qs = qs.filter(
                    Q(student_profile__school_class__grade=g) |
                    Q(department_or_class__startswith=str(g)) |
                    Q(department_or_class__icontains=f" {g}") |
                    Q(department_or_class__icontains=f"{g}A")
                )
            except ValueError:
                pass

        # Bộ lọc lớp
        class_param = self.request.query_params.get('class_id')
        if class_param:
            qs = qs.filter(student_profile__school_class_id=class_param)

        class_name_param = self.request.query_params.get('class_name')
        if class_name_param:
            clean_c = class_name_param.strip()
            qs = qs.filter(
                Q(student_profile__school_class__name__iexact=clean_c) |
                Q(department_or_class__icontains=clean_c)
            )

        # Tìm kiếm
        search = self.request.query_params.get('search')
        if search:
            q = search.strip()
            qs = qs.filter(
                Q(username__icontains=q) |
                Q(full_name__icontains=q) |
                Q(email__icontains=q) |
                Q(phone__icontains=q) |
                Q(department_or_class__icontains=q) |
                Q(student_profile__student_code__icontains=q)
            )

        return qs

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Thống kê số lượng tài khoản học sinh theo trạng thái"""
        from django.db.models import Count, Q
        base = User.objects.filter(role=User.ROLE_HOC_SINH).filter(
            Q(requested_role__isnull=True) | Q(requested_role='') | Q(requested_role=User.ROLE_HOC_SINH)
        )
        agg = base.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(account_status=User.STATUS_PENDING)),
            approved=Count('id', filter=Q(account_status=User.STATUS_APPROVED)),
            rejected=Count('id', filter=Q(account_status=User.STATUS_REJECTED)),
            suspended=Count('id', filter=Q(account_status=User.STATUS_SUSPENDED)),
        )
        return Response(agg)

    @action(detail=True, methods=['post'], url_path='review-class-change')
    def review_class_change(self, request, pk=None):
        target_user = self.get_object()
        action_type = request.data.get('action') or 'approve'
        reason = (request.data.get('reason') or '').strip()
        internal_notes = (request.data.get('internal_notes') or '').strip()
        from .views import UserManagementViewSet
        viewset = UserManagementViewSet()
        return viewset._handle_class_change_review(request, target_user, action_type, reason, internal_notes)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """Phê duyệt 1 tài khoản học sinh"""
        user = request.user
        if not (user.is_admin or user.is_superuser or (user.is_doan_truong and user.has_custom_perm('student_accounts.approve'))):
            return Response(
                {'error': 'Bạn không có quyền phê duyệt tài khoản học sinh.'},
                status=status.HTTP_403_FORBIDDEN
            )

        target_user = self.get_object()
        prev_status = target_user.account_status

        with transaction.atomic():
            target_user.account_status = User.STATUS_APPROVED
            target_user.profile_completed = True
            target_user.is_active = True
            target_user.role = User.ROLE_HOC_SINH
            target_user.approved_by = user
            target_user.approved_at = timezone.now()
            target_user.rejection_reason = ''
            target_user.save()

            # Tự động đồng bộ hồ sơ Student nếu chưa có
            from conduct.models import Student, SchoolClass
            if not hasattr(target_user, 'student_profile'):
                dept = (target_user.department_or_class or '').strip()
                clean_dept = dept.replace('Lớp', '').replace('lop', '').strip()
                sclass = SchoolClass.objects.filter(name__iexact=clean_dept, is_active=True).first()
                if not sclass:
                    sclass = SchoolClass.objects.filter(name__iexact=dept, is_active=True).first()
                if sclass:
                    Student.objects.get_or_create(
                        user=target_user,
                        defaults={
                            'student_code': f"HK{sclass.grade}-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                            'full_name': target_user.full_name or target_user.username,
                            'date_of_birth': timezone.now().date(),
                            'gender': 'M',
                            'school_class': sclass,
                            'status': 'STUDYING'
                        }
                    )

            ApprovalLog.objects.create(
                user=target_user,
                reviewer=user,
                previous_status=prev_status,
                new_status=User.STATUS_APPROVED,
                assigned_role=User.ROLE_HOC_SINH,
                reason='Phê duyệt tài khoản học sinh',
                internal_notes='Thực hiện từ giao diện Duyệt tài khoản'
            )

            AuditLog.objects.create(
                user=user,
                action='APPROVE_STUDENT',
                resource_type='USER',
                resource_id=str(target_user.id),
                details=f"{user.username} đã phê duyệt tài khoản học sinh {target_user.username} ({target_user.full_name}).",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            Notification.objects.create(
                recipient=target_user,
                notification_type=Notification.TYPE_APPROVAL,
                title='Tài khoản học sinh đã được phê duyệt!',
                message=(
                    f"Chúc mừng bạn! Yêu cầu đăng ký tài khoản học sinh đã được {user.full_name or user.username} "
                    f"phê duyệt thành công. Bạn có thể sử dụng đầy đủ các tính năng của học sinh ngay bây giờ."
                ),
                link='/'
            )

        return Response({
            'message': f"Đã phê duyệt tài khoản học sinh {target_user.username} thành công.",
            'user': StudentAccountSerializer(target_user).data
        })

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """Từ chối 1 tài khoản học sinh (bắt buộc nhập lý do)"""
        user = request.user
        if not (user.is_admin or user.is_superuser or (user.is_doan_truong and user.has_custom_perm('student_accounts.reject'))):
            return Response(
                {'error': 'Bạn không có quyền từ chối tài khoản học sinh.'},
                status=status.HTTP_403_FORBIDDEN
            )

        target_user = self.get_object()
        reason = (request.data.get('reason') or request.data.get('rejection_reason') or '').strip()
        if not reason:
            return Response(
                {'error': 'Vui lòng nhập lý do từ chối tài khoản học sinh.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        prev_status = target_user.account_status

        with transaction.atomic():
            target_user.account_status = User.STATUS_REJECTED
            target_user.is_active = False
            target_user.rejected_by = user
            target_user.rejected_at = timezone.now()
            target_user.rejection_reason = reason
            target_user.save()

            ApprovalLog.objects.create(
                user=target_user,
                reviewer=user,
                previous_status=prev_status,
                new_status=User.STATUS_REJECTED,
                assigned_role=target_user.role,
                reason=reason,
                internal_notes='Từ chối từ giao diện Duyệt tài khoản'
            )

            AuditLog.objects.create(
                user=user,
                action='REJECT_STUDENT',
                resource_type='USER',
                resource_id=str(target_user.id),
                details=f"{user.username} đã từ chối tài khoản học sinh {target_user.username}. Lý do: {reason}",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            Notification.objects.create(
                recipient=target_user,
                notification_type=Notification.TYPE_APPROVAL,
                title='Thông báo về yêu cầu đăng ký tài khoản học sinh',
                message=f"Yêu cầu đăng ký tài khoản của bạn chưa được chấp thuận. Lý do: {reason}.",
                link='/'
            )

        return Response({
            'message': f"Đã từ chối tài khoản học sinh {target_user.username}.",
            'user': StudentAccountSerializer(target_user).data
        })

    @action(detail=False, methods=['post'], url_path='bulk-approve')
    def bulk_approve(self, request):
        """Phê duyệt hàng loạt tài khoản học sinh"""
        user = request.user
        if not (user.is_admin or user.is_superuser or (user.is_doan_truong and user.has_custom_perm('student_accounts.approve'))):
            return Response({'error': 'Bạn không có quyền phê duyệt tài khoản học sinh.'}, status=status.HTTP_403_FORBIDDEN)

        user_ids = request.data.get('user_ids', [])
        if not isinstance(user_ids, list) or not user_ids:
            return Response({'error': 'Vui lòng chọn ít nhất một tài khoản để phê duyệt.'}, status=status.HTTP_400_BAD_REQUEST)

        approved_count = 0
        from conduct.models import Student, SchoolClass

        with transaction.atomic():
            targets = User.objects.filter(
                id__in=user_ids,
                role=User.ROLE_HOC_SINH,
                account_status__in=[User.STATUS_PENDING, User.STATUS_REJECTED]
            ).filter(Q(requested_role__isnull=True) | Q(requested_role='') | Q(requested_role=User.ROLE_HOC_SINH))
            for target_user in targets:
                prev_status = target_user.account_status
                target_user.account_status = User.STATUS_APPROVED
                target_user.profile_completed = True
                target_user.is_active = True
                target_user.role = User.ROLE_HOC_SINH
                target_user.approved_by = user
                target_user.approved_at = timezone.now()
                target_user.rejection_reason = ''
                target_user.save()

                if not hasattr(target_user, 'student_profile'):
                    dept = (target_user.department_or_class or '').strip()
                    clean_dept = dept.replace('Lớp', '').replace('lop', '').strip()
                    sclass = SchoolClass.objects.filter(name__iexact=clean_dept, is_active=True).first()
                    if not sclass:
                        sclass = SchoolClass.objects.filter(name__iexact=dept, is_active=True).first()
                    if sclass:
                        Student.objects.get_or_create(
                            user=target_user,
                            defaults={
                                'student_code': f"HK{sclass.grade}-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                                'full_name': target_user.full_name or target_user.username,
                                'date_of_birth': timezone.now().date(),
                                'gender': 'M',
                                'school_class': sclass,
                                'status': 'STUDYING'
                            }
                        )

                ApprovalLog.objects.create(
                    user=target_user,
                    reviewer=user,
                    previous_status=prev_status,
                    new_status=User.STATUS_APPROVED,
                    assigned_role=User.ROLE_HOC_SINH,
                    reason='Phê duyệt hàng loạt',
                    internal_notes='Duyệt nhiều tài khoản'
                )
                AuditLog.objects.create(
                    user=user,
                    action='BULK_APPROVE_STUDENT',
                    resource_type='USER',
                    resource_id=str(target_user.id),
                    details=f"{user.username} duyệt hàng loạt tài khoản học sinh {target_user.username}.",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                approved_count += 1

        return Response({'message': f'Đã phê duyệt thành công {approved_count} tài khoản học sinh.', 'count': approved_count})

    @action(detail=False, methods=['post'], url_path='bulk-reject')
    def bulk_reject(self, request):
        """Từ chối hàng loạt tài khoản học sinh kèm lý do"""
        user = request.user
        if not (user.is_admin or user.is_superuser or (user.is_doan_truong and user.has_custom_perm('student_accounts.reject'))):
            return Response({'error': 'Bạn không có quyền từ chối tài khoản học sinh.'}, status=status.HTTP_403_FORBIDDEN)

        user_ids = request.data.get('user_ids', [])
        reason = (request.data.get('reason') or request.data.get('rejection_reason') or '').strip()
        if not isinstance(user_ids, list) or not user_ids:
            return Response({'error': 'Vui lòng chọn ít nhất một tài khoản để từ chối.'}, status=status.HTTP_400_BAD_REQUEST)
        if not reason:
            return Response({'error': 'Vui lòng nhập lý do từ chối cho các tài khoản đã chọn.'}, status=status.HTTP_400_BAD_REQUEST)

        rejected_count = 0
        with transaction.atomic():
            targets = User.objects.filter(id__in=user_ids, role=User.ROLE_HOC_SINH).filter(
                Q(requested_role__isnull=True) | Q(requested_role='') | Q(requested_role=User.ROLE_HOC_SINH)
            )
            for target_user in targets:
                prev_status = target_user.account_status
                target_user.account_status = User.STATUS_REJECTED
                target_user.is_active = False
                target_user.rejected_by = user
                target_user.rejected_at = timezone.now()
                target_user.rejection_reason = reason
                target_user.save()

                ApprovalLog.objects.create(
                    user=target_user,
                    reviewer=user,
                    previous_status=prev_status,
                    new_status=User.STATUS_REJECTED,
                    assigned_role=target_user.role,
                    reason=reason,
                    internal_notes='Từ chối hàng loạt'
                )
                AuditLog.objects.create(
                    user=user,
                    action='BULK_REJECT_STUDENT',
                    resource_type='USER',
                    resource_id=str(target_user.id),
                    details=f"{user.username} từ chối hàng loạt tài khoản học sinh {target_user.username}. Lý do: {reason}",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                rejected_count += 1

        return Response({'message': f'Đã từ chối thành công {rejected_count} tài khoản học sinh.', 'count': rejected_count})


class DoanTruongManagementViewSet(viewsets.ModelViewSet):
    """
    Phân hệ quản lý Đoàn trường dành riêng cho Quản trị viên (Admin):
    - Chỉ Admin/Super Admin có quyền bổ nhiệm, thu hồi vai trò Đoàn trường và cấp quyền chi tiết.
    - Đoàn trường, GVCN, GVBM, Sao đỏ, Học sinh KHÔNG có quyền truy cập (403 Forbidden).
    """
    serializer_class = DoanTruongMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_denied(request, message='Dùng thao tác phân quyền hoặc thu hồi đã được kiểm tra quyền.')
        if self.action in ['list', 'retrieve', 'available_permissions']:
            if not (request.user.is_admin or request.user.is_superuser or request.user.is_doan_truong):
                self.permission_denied(
                    request,
                    message='Chỉ Quản trị viên hệ thống (Admin) hoặc Đoàn trường mới có quyền xem danh sách cán bộ Đoàn trường.'
                )
        else:
            if not (request.user.is_admin or request.user.is_superuser):
                self.permission_denied(
                    request,
                    message='Chỉ Quản trị viên hệ thống (Admin) mới có quyền quản lý vai trò và phân quyền Đoàn trường.'
                )

    def get_queryset(self):
        return User.objects.filter(role=User.ROLE_DOAN_TRUONG).order_by('-date_joined')

    def create(self, request, *args, **kwargs):
        """Bổ nhiệm 1 người dùng làm Cán bộ Đoàn trường"""
        user_id = request.data.get('user_id')
        user_obj = None
        if user_id:
            user_obj = User.objects.filter(id=user_id).first()
        if not user_obj:
            username = request.data.get('username')
            if username:
                user_obj = User.objects.filter(username__iexact=username).first()

        if not user_obj:
            return Response({'error': 'Không tìm thấy tài khoản người dùng cần bổ nhiệm.'}, status=status.HTTP_400_BAD_REQUEST)
        if user_obj.pk == request.user.pk:
            return Response({'error': 'Không thể tự bổ nhiệm tài khoản quản trị đang đăng nhập.'}, status=status.HTTP_400_BAD_REQUEST)
        if user_obj.is_superuser or user_obj.is_admin:
            return Response({'error': 'Không thể đổi vai trò tài khoản quản trị viên.'}, status=status.HTTP_400_BAD_REQUEST)
        if user_obj.is_doan_truong:
            return Response({'error': 'Tài khoản này đã là cán bộ Đoàn trường. Hãy cập nhật quyền ở danh sách hiện tại.'}, status=status.HTTP_400_BAD_REQUEST)

        raw_perms = request.data.get('permissions')
        if raw_perms is not None and isinstance(raw_perms, list):
            perms = [p for p in raw_perms if p in ALL_DOAN_TRUONG_PERMISSIONS]
        else:
            perms = list(DEFAULT_DOAN_TRUONG_PERMISSIONS)

        with transaction.atomic():
            user_obj.role = User.ROLE_DOAN_TRUONG
            user_obj.account_status = User.STATUS_APPROVED
            user_obj.is_active = True
            user_obj.doan_truong_permissions = perms
            # Do not carry legacy discipline rights into the restricted role.
            user_obj.can_verify_violations = False
            user_obj.can_view_counseling = False
            user_obj.save()

            AuditLog.objects.create(
                user=request.user,
                action='APPOINT_DOAN_TRUONG',
                resource_type='USER',
                resource_id=str(user_obj.id),
                details=f"Quản trị viên {request.user.username} đã bổ nhiệm {user_obj.username} làm Cán bộ Đoàn trường với {len(perms)} quyền.",
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return Response({
            'message': f"Đã bổ nhiệm thành công {user_obj.full_name or user_obj.username} làm Cán bộ Đoàn trường.",
            'user': DoanTruongMemberSerializer(user_obj).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post', 'put'], url_path='permissions')
    def update_permissions(self, request, pk=None):
        """Cập nhật danh sách quyền cho tài khoản Đoàn trường"""
        target_user = self.get_object()
        serializer = DoanTruongPermissionUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        perms = serializer.validated_data['permissions']
        target_user.doan_truong_permissions = perms
        target_user.can_verify_violations = False
        target_user.can_view_counseling = False
        target_user.save(update_fields=['doan_truong_permissions', 'can_verify_violations', 'can_view_counseling'])

        AuditLog.objects.create(
            user=request.user,
            action='UPDATE_DOAN_TRUONG_PERMS',
            resource_type='USER',
            resource_id=str(target_user.id),
            details=f"Quản trị viên {request.user.username} đã cập nhật quyền Đoàn trường cho {target_user.username}: {', '.join(perms)}",
            ip_address=request.META.get('REMOTE_ADDR')
        )

        return Response({
            'message': f"Đã cập nhật phân quyền thành công cho cán bộ Đoàn trường {target_user.full_name or target_user.username}.",
            'permissions': perms
        })

    @action(detail=True, methods=['post'], url_path='revoke')
    def revoke(self, request, pk=None):
        """Thu hồi vai trò Đoàn trường"""
        target_user = self.get_object()
        target_role = request.data.get('target_role', User.ROLE_HOC_SINH)
        allowed_roles = {
            User.ROLE_HOC_SINH,
            User.ROLE_GVCN,
            User.ROLE_GVBM,
            User.ROLE_CHUYEN_VIEN_TAM_LY,
        }
        if target_role not in allowed_roles:
            return Response({'error': 'Vai trò đích không hợp lệ để thu hồi quyền Đoàn trường.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            target_user.role = target_role
            target_user.doan_truong_permissions = []
            target_user.can_verify_violations = False
            target_user.can_view_counseling = False
            target_user.save()

            AuditLog.objects.create(
                user=request.user,
                action='REVOKE_DOAN_TRUONG',
                resource_type='USER',
                resource_id=str(target_user.id),
                details=f"Quản trị viên {request.user.username} đã thu hồi vai trò Đoàn trường của {target_user.username}.",
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return Response({'message': f"Đã thu hồi vai trò Đoàn trường của {target_user.username}."})

    @action(detail=False, methods=['get'], url_path='available-permissions')
    def available_permissions(self, request):
        """Danh sách tất cả các quyền Đoàn trường có thể cấu hình"""
        perm_details = [
            {'code': 'student_accounts.view', 'name': 'Xem danh sách học sinh', 'description': 'Xem danh sách tài khoản học sinh đăng ký trong hệ thống.'},
            {'code': 'student_accounts.approve', 'name': 'Duyệt tài khoản học sinh', 'description': 'Phê duyệt tài khoản học sinh sang trạng thái hoạt động chính thức.'},
            {'code': 'student_accounts.reject', 'name': 'Từ chối tài khoản học sinh', 'description': 'Từ chối yêu cầu đăng ký học sinh kèm lý do cụ thể.'},
            {'code': 'red_star.view', 'name': 'Xem danh sách Sao đỏ', 'description': 'Xem danh sách học sinh đang đảm nhiệm chức danh Sao đỏ.'},
            {'code': 'red_star.assign', 'name': 'Phân công Sao đỏ', 'description': 'Phân công nhiệm vụ, ca trực và phạm vi lớp cho Đội Sao đỏ.'},
            {'code': 'red_star.revoke', 'name': 'Thu hồi / Tạm dừng Sao đỏ', 'description': 'Tạm dừng hoặc thu hồi nhiệm vụ Sao đỏ khi kết thúc nhiệm kỳ hoặc vi phạm.'},
        ]
        return Response({'permissions': perm_details})


class ServerTimeAPIView(APIView):
    """Cung cấp thời gian thực của máy chủ (GMT+7) phục vụ đồng bộ chính xác trên hệ thống"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        now = timezone.now()
        local_now = timezone.localtime(now)
        days = ['Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy', 'Chủ Nhật']
        day_str = days[local_now.weekday()]
        return Response({
            'server_time': now.isoformat(),
            'local_time': local_now.isoformat(),
            'formatted_time': local_now.strftime('%H:%M:%S'),
            'formatted_date': f"{day_str}, ngày {local_now.strftime('%d/%m/%Y')}",
            'timezone': str(timezone.get_current_timezone()),
            'timestamp': int(now.timestamp()),
            'timestamp_ms': int(now.timestamp() * 1000),
        })
