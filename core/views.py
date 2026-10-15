from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, AcademicYear, Semester, SystemSetting, AuditLog
from .serializers import UserSerializer, AcademicYearSerializer, SemesterSerializer, SystemSettingSerializer, AuditLogSerializer


def index_view(request):
    """Trang chủ ứng dụng HK Student Hub"""
    school_name = SystemSetting.get_setting('SCHOOL_NAME', 'TRƯỜNG THPT HƯƠNG KHÊ – HÀ TĨNH')
    slogan = SystemSetting.get_setting('APP_SLOGAN', 'Kỷ cương số – Thi đua minh bạch – Đồng hành cùng học sinh')
    return render(request, 'index.html', {
        'school_name': school_name,
        'slogan': slogan,
        'current_year': '2026-2027',
    })


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({'error': 'Vui lòng nhập tên đăng nhập và mật khẩu'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_active:
                return Response({'error': 'Tài khoản của bạn đã bị khóa hoặc chưa được kích hoạt bởi Quản trị viên'}, status=status.HTTP_403_FORBIDDEN)
            login(request, user)
            
            AuditLog.objects.create(
                user=user,
                action='LOGIN',
                resource_type='USER',
                resource_id=str(user.id),
                details=f"Đăng nhập thành công với chức vụ {user.get_role_display()}",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            serializer = UserSerializer(user)
            return Response({
                'message': f'Đăng nhập thành công! Chào mừng {user.full_name or user.username}',
                'user': serializer.data
            })
        return Response({'error': 'Tên đăng nhập hoặc mật khẩu không chính xác. Vui lòng kiểm tra lại.'}, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    def post(self, request):
        if request.user.is_authenticated:
            AuditLog.objects.create(
                user=request.user,
                action='LOGOUT',
                resource_type='USER',
                resource_id=str(request.user.id),
                details="Đăng xuất an toàn khỏi hệ thống"
            )
        logout(request)
        return Response({'message': 'Đã đăng xuất an toàn khỏi hệ thống'})


class CurrentUserAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            serializer = UserSerializer(request.user)
            extra_info = {}
            if request.user.is_gvcn and hasattr(request.user, 'homeroom_classes'):
                homeroom = request.user.homeroom_classes.first()
                if homeroom:
                    extra_info['homeroom_class_id'] = homeroom.id
                    extra_info['homeroom_class_name'] = homeroom.name
            elif request.user.is_student and hasattr(request.user, 'student_profile'):
                profile = request.user.student_profile
                extra_info['student_id'] = profile.id
                extra_info['student_code'] = profile.student_code
                extra_info['class_id'] = profile.school_class_id
                extra_info['class_name'] = profile.school_class.name

            data = serializer.data
            data['meta'] = extra_info
            return Response({'authenticated': True, 'user': data})
        return Response({'authenticated': False, 'user': None})


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    Phân hệ quản lý tài khoản và phân quyền:
    NGHIÊM NGẶT: CHỈ CÓ QUẢN TRỊ VIÊN HỆ THỐNG (ADMIN) MỚI CÓ QUYỀN TRUY CẬP VÀ DUYỆT CHỨC VỤ / QUYỀN HẠN.
    Người dùng thông thường bị chặn 403 Forbidden.
    """
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if not (request.user.is_admin or request.user.is_superuser):
            self.permission_denied(
                request,
                message='Chỉ có Quản trị viên hệ thống (Admin) mới có quyền duyệt chức vụ và cấp phát quyền hạn.'
            )

    @action(detail=True, methods=['post'], url_path='approve-role')
    def approve_role(self, request, pk=None):
        """Admin duyệt chức vụ và cấp phát quyền hạn cho người dùng"""
        user_obj = self.get_object()
        new_role = request.data.get('role')
        can_verify = request.data.get('can_verify_violations')
        can_counseling = request.data.get('can_view_counseling')
        is_active = request.data.get('is_active')

        old_role = user_obj.get_role_display()

        if new_role:
            valid_roles = [r[0] for r in User.ROLE_CHOICES]
            if new_role not in valid_roles:
                return Response({'error': f'Chức vụ không hợp lệ. Phải thuộc: {valid_roles}'}, status=status.HTTP_400_BAD_REQUEST)
            user_obj.role = new_role

        if can_verify is not None:
            user_obj.can_verify_violations = bool(can_verify)
        if can_counseling is not None:
            user_obj.can_view_counseling = bool(can_counseling)
        if is_active is not None:
            user_obj.is_active = bool(is_active)

        user_obj.save()

        AuditLog.objects.create(
            user=request.user,
            action='UPDATE_ROLE',
            resource_type='USER',
            resource_id=str(user_obj.id),
            details=(
                f"Quản trị viên {request.user.username} đã duyệt/thay đổi chức vụ của {user_obj.username} "
                f"từ [{old_role}] sang [{user_obj.get_role_display()}]. "
                f"Quyền xác minh: {user_obj.can_verify_violations}, Quyền tư vấn: {user_obj.can_view_counseling}"
            )
        )

        serializer = self.get_serializer(user_obj)
        return Response({
            'message': f'Đã duyệt và cập nhật chức vụ thành công cho người dùng: {user_obj.full_name or user_obj.username}',
            'user': serializer.data
        })


class SystemStatsAPIView(APIView):
    """Thống kê tổng quan phù hợp với vai trò của người đăng nhập"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from conduct.models import SchoolClass, Student, ViolationRecord
        from competition.models import ClassCompetitionScore, CompetitionPeriod
        from alerts.models import EarlyWarningAlert
        from counseling.models import CounselingRequest

        user = request.user
        current_year = AcademicYear.objects.filter(is_current=True).first()

        # Dữ liệu cơ bản
        total_classes = SchoolClass.objects.count()
        total_students = Student.objects.filter(status='STUDYING').count()
        
        # Vi phạm
        today = timezone.now().date()
        violations_today = ViolationRecord.objects.filter(occurred_at__date=today).count()
        violations_pending = ViolationRecord.objects.filter(status=ViolationRecord.STATUS_PENDING).count()
        violations_verified_week = ViolationRecord.objects.filter(
            occurred_at__date__gte=today - timezone.timedelta(days=7),
            status__in=[ViolationRecord.STATUS_VERIFIED, ViolationRecord.STATUS_ADJUSTED]
        ).count()

        # Kỳ thi đua mới nhất
        latest_period = CompetitionPeriod.objects.order_by('-start_date').first()
        
        # Cảnh báo nền nếp
        alerts_active = EarlyWarningAlert.objects.filter(
            status__in=[EarlyWarningAlert.STATUS_NEW, EarlyWarningAlert.STATUS_RECEIVED, EarlyWarningAlert.STATUS_IN_PROGRESS]
        ).count()

        stats = {
            'role': user.role,
            'role_display': user.get_role_display(),
            'total_classes': total_classes,
            'total_students': total_students,
            'violations_today': violations_today,
            'violations_pending': violations_pending,
            'violations_verified_week': violations_verified_week,
            'alerts_active': alerts_active,
            'current_period_name': latest_period.name if latest_period else 'Chưa mở kỳ thi đua',
            'current_year_name': current_year.name if current_year else '2026-2027',
        }

        # Nếu có quyền tư vấn tâm lý: thêm số liệu tổng hợp ẩn danh (chỉ số lượng)
        if user.has_counseling_access or user.is_bgh:
            stats['counseling_total'] = CounselingRequest.objects.count()
            stats['counseling_new'] = CounselingRequest.objects.filter(status=CounselingRequest.STATUS_NEW).count()
            stats['counseling_in_progress'] = CounselingRequest.objects.filter(
                status__in=[CounselingRequest.STATUS_IN_PROGRESS, CounselingRequest.STATUS_SCHEDULED]
            ).count()

        # Nếu là GVCN: Lọc thống kê riêng của lớp mình
        if user.is_gvcn:
            homeroom = user.homeroom_classes.first()
            if homeroom:
                stats['my_class_name'] = homeroom.name
                stats['my_class_student_count'] = homeroom.student_count
                stats['my_class_violations_pending'] = ViolationRecord.objects.filter(school_class=homeroom, status=ViolationRecord.STATUS_PENDING).count()
                stats['my_class_violations_verified'] = ViolationRecord.objects.filter(
                    school_class=homeroom, 
                    status__in=[ViolationRecord.STATUS_VERIFIED, ViolationRecord.STATUS_ADJUSTED]
                ).count()
                stats['my_class_alerts'] = EarlyWarningAlert.objects.filter(
                    school_class=homeroom,
                    status__in=[EarlyWarningAlert.STATUS_NEW, EarlyWarningAlert.STATUS_RECEIVED, EarlyWarningAlert.STATUS_IN_PROGRESS]
                ).count()

        # Nếu là Học sinh: Thông tin cá nhân
        if user.is_student and hasattr(user, 'student_profile'):
            student = user.student_profile
            stats['student_name'] = student.full_name
            stats['student_code'] = student.student_code
            stats['student_class'] = student.school_class.name
            stats['my_violations_verified'] = ViolationRecord.objects.filter(
                student=student, 
                status__in=[ViolationRecord.STATUS_VERIFIED, ViolationRecord.STATUS_ADJUSTED]
            ).count()
            stats['my_violations_pending'] = ViolationRecord.objects.filter(
                student=student, status=ViolationRecord.STATUS_PENDING
            ).count()

        return Response(stats)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_bgh:
            return AuditLog.objects.all()
        return AuditLog.objects.filter(user=user)
