from django.contrib.auth.models import AbstractUser
from django.db import models


ALL_DOAN_TRUONG_PERMISSIONS = [
    'student_accounts.view',
    'student_accounts.approve',
    'student_accounts.reject',
    'user_profiles.view',
    'user_profiles.edit',
    'accounts.lock_unlock',
    'classes.view',
    'classes.manage',
    'conduct.view',
    'conduct.verify',
    'conduct.reject',
    'conduct.manage_rules',
    'competition.view',
    'competition.scores.manage',
    'competition.periods.manage',
    'red_star.view',
    'red_star.assign',
    'red_star.revoke',
    'reports.view',
    'reports.export',
    'alerts.view',
    'audit_logs.view',
]

DEFAULT_DOAN_TRUONG_PERMISSIONS = list(ALL_DOAN_TRUONG_PERMISSIONS)


class User(AbstractUser):
    ROLE_SUPER_ADMIN = 'SUPER_ADMIN'
    ROLE_ADMIN = 'ADMIN'
    ROLE_BGH = 'BGH'
    ROLE_DOAN_TRUONG = 'DOAN_TRUONG'
    ROLE_SAO_DO = 'SAO_DO'
    ROLE_GVCN = 'GVCN'
    ROLE_GVBM = 'GVBM'
    ROLE_HOC_SINH = 'HOC_SINH'
    ROLE_CHUYEN_VIEN_TAM_LY = 'CHUYEN_VIEN_TAM_LY'

    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, 'Quản trị viên tối cao (Super Admin)'),
        (ROLE_ADMIN, 'Quản trị viên hệ thống'),
        (ROLE_BGH, 'Ban Giám hiệu'),
        (ROLE_DOAN_TRUONG, 'Đoàn trường'),
        (ROLE_SAO_DO, 'Đội Sao đỏ / Trực tuần'),
        (ROLE_GVCN, 'Giáo viên chủ nhiệm'),
        (ROLE_GVBM, 'Giáo viên bộ môn'),
        (ROLE_HOC_SINH, 'Học sinh'),
        (ROLE_CHUYEN_VIEN_TAM_LY, 'Chuyên viên tư vấn tâm lý'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_SUSPENDED = 'SUSPENDED'
    STATUS_DISABLED = 'DISABLED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Chờ phê duyệt'),
        (STATUS_APPROVED, 'Đã phê duyệt'),
        (STATUS_REJECTED, 'Bị từ chối'),
        (STATUS_SUSPENDED, 'Tạm khóa'),
        (STATUS_DISABLED, 'Đã vô hiệu hóa'),
    ]

    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_HOC_SINH)
    account_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='Trạng thái tài khoản'
    )
    requested_role = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Đối tượng / Vai trò đề nghị'
    )
    department_or_class = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Lớp hoặc đơn vị công tác'
    )
    verification_info = models.TextField(
        blank=True,
        null=True,
        verbose_name='Thông tin xác minh / Ghi chú đăng ký'
    )
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name='Lý do từ chối (hiển thị cho người dùng)'
    )
    rejected_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_users',
        verbose_name='Người từ chối'
    )
    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Thời điểm từ chối'
    )
    internal_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Ghi chú nội bộ Admin'
    )
    doan_truong_permissions = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Danh sách quyền Đoàn trường'
    )
    approved_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_users',
        verbose_name='Người phê duyệt'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Thời điểm phê duyệt'
    )
    full_name = models.CharField(max_length=150, verbose_name='Họ và tên đầy đủ', blank=True)
    phone = models.CharField(max_length=20, blank=True, verbose_name='Số điện thoại')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    can_view_counseling = models.BooleanField(
        default=False, 
        verbose_name='Quyền truy cập hồ sơ tư vấn tâm lý',
        help_text='Chỉ cấp cho chuyên viên tâm lý hoặc nhân sự được BGH phân công chuyên biệt.'
    )
    can_verify_violations = models.BooleanField(
        default=False,
        verbose_name='Quyền xác minh vi phạm nền nếp'
    )
    must_change_password = models.BooleanField(default=False)
    google_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Google Subject ID'
    )
    google_avatar_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='URL ảnh đại diện Google'
    )
    profile_completed = models.BooleanField(
        default=True,
        verbose_name='Đã hoàn thiện hồ sơ đăng ký'
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Thời điểm gửi hồ sơ đăng ký'
    )

    class Meta:
        verbose_name = 'Người dùng'
        verbose_name_plural = 'Danh sách người dùng'
        indexes = [
            models.Index(fields=['account_status', 'role'], name='idx_user_status_role'),
            models.Index(fields=['role', 'account_status'], name='idx_user_role_status'),
            models.Index(fields=['department_or_class'], name='idx_user_dept_class'),
            models.Index(fields=['-date_joined'], name='idx_user_date_joined'),
            models.Index(fields=['google_id'], name='idx_user_google_id'),
        ]

    def __str__(self):
        display_name = self.full_name or self.username
        return f"{display_name} ({self.get_role_display()} - {self.get_account_status_display()})"

    @property
    def is_super_admin(self):
        return self.role == self.ROLE_SUPER_ADMIN or self.is_superuser

    @property
    def is_admin(self):
        return self.role in [self.ROLE_ADMIN, self.ROLE_SUPER_ADMIN] or self.is_superuser

    @property
    def is_bgh(self):
        return self.role == self.ROLE_BGH

    @property
    def is_doan_truong(self):
        return self.role == self.ROLE_DOAN_TRUONG

    def has_custom_perm(self, perm_code):
        if self.is_admin:
            return True
        if self.is_doan_truong:
            if perm_code in ['admin.all', 'settings.manage', 'audit_logs.delete']:
                return False
            return True
        return False

    def get_effective_permissions(self):
        if self.is_admin:
            return ALL_DOAN_TRUONG_PERMISSIONS + ['admin.all']
        if self.is_doan_truong:
            return list(ALL_DOAN_TRUONG_PERMISSIONS)
        return []


    @property
    def is_active_red_star(self):
        try:
            from django.utils import timezone
            from conduct.models import RedStarAssignment
            today = timezone.localdate()
            return self.red_star_assignments.filter(
                status=RedStarAssignment.STATUS_ACTIVE,
                start_date__lte=today
            ).filter(
                models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
            ).exists()
        except Exception:
            return False

    @property
    def is_sao_do(self):
        return self.role == self.ROLE_SAO_DO or self.is_active_red_star

    @property
    def is_gvcn(self):
        if self.role == self.ROLE_GVCN:
            return True
        return hasattr(self, 'homeroom_assignments') and self.homeroom_assignments.filter(is_active=True).exists()

    @property
    def is_gvbm(self):
        return self.role == self.ROLE_GVBM

    @property
    def is_student(self):
        return self.role == self.ROLE_HOC_SINH

    @property
    def is_class_monitor(self):
        if hasattr(self, 'student_profile') and self.student_profile:
            return bool(getattr(self.student_profile, 'is_class_monitor', False) or (self.student_profile.school_class and self.student_profile.school_class.monitor_id == self.student_profile.id))
        return False

    @property
    def has_counseling_access(self):
        if self.is_admin or self.is_doan_truong:
            return True
        return self.role == self.ROLE_CHUYEN_VIEN_TAM_LY or self.can_view_counseling

    @property
    def is_approved(self):
        return self.account_status == self.STATUS_APPROVED

    @property
    def subject(self):
        profile = getattr(self, 'teacher_profile', None)
        if profile and getattr(profile, 'subject', None):
            return profile.subject
        if self.department_or_class and self.department_or_class.startswith('Môn '):
            return self.department_or_class[4:].strip()
        return self.department_or_class or ''


class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True, verbose_name='Năm học (VD: 2026-2027)')
    start_date = models.DateField(verbose_name='Ngày bắt đầu')
    end_date = models.DateField(verbose_name='Ngày kết thúc')
    is_current = models.BooleanField(default=False, verbose_name='Năm học hiện tại')

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Năm học'
        verbose_name_plural = 'Danh sách năm học'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.exclude(id=self.id).update(is_current=False)
        super().save(*args, **kwargs)


class Semester(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    semester_number = models.PositiveSmallIntegerField(choices=[(1, 'Học kỳ I'), (2, 'Học kỳ II')])
    name = models.CharField(max_length=50, verbose_name='Tên học kỳ')
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        unique_together = ('academic_year', 'semester_number')
        ordering = ['academic_year', 'semester_number']
        verbose_name = 'Học kỳ'
        verbose_name_plural = 'Danh sách học kỳ'

    def __str__(self):
        return f"{self.name} - Năm học {self.academic_year.name}"

    def save(self, *args, **kwargs):
        if self.is_current:
            Semester.objects.exclude(id=self.id).update(is_current=False)
        super().save(*args, **kwargs)


class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True, verbose_name='Khóa cấu hình')
    value = models.TextField(verbose_name='Giá trị')
    description = models.CharField(max_length=255, blank=True, verbose_name='Mô tả cấu hình')
    is_public = models.BooleanField(default=True, verbose_name='Công khai cho giao diện')

    class Meta:
        verbose_name = 'Cấu hình hệ thống'
        verbose_name_plural = 'Các cấu hình hệ thống'

    def __str__(self):
        return f"{self.key}: {self.description or self.value}"

    @classmethod
    def get_setting(cls, key, default=''):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_setting(cls, key, value, description='', is_public=True):
        defaults = {'value': str(value), 'is_public': is_public}
        if description:
            defaults['description'] = description
        obj, _ = cls.objects.update_or_create(key=key, defaults=defaults)
        return obj


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=50, verbose_name='Hành động')
    resource_type = models.CharField(max_length=50, verbose_name='Loại đối tượng')
    resource_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='ID đối tượng')
    details = models.TextField(blank=True, verbose_name='Chi tiết thao tác')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='Địa chỉ IP')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời điểm thao tác')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Nhật ký thao tác'
        verbose_name_plural = 'Nhật ký thao tác hệ thống'
        indexes = [
            models.Index(fields=['user', '-created_at'], name='idx_audit_user_created'),
            models.Index(fields=['resource_type', 'resource_id'], name='idx_audit_resource'),
            models.Index(fields=['-created_at'], name='idx_audit_created'),
        ]

    def __str__(self):
        username = self.user.username if self.user else 'Khách / Hệ thống'
        return f"[{self.created_at.strftime('%d/%m/%Y %H:%M')}] {username} - {self.action} on {self.resource_type}"


class ApprovalLog(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='approval_history',
        verbose_name='Tài khoản được xét duyệt'
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducted_approvals',
        verbose_name='Người xét duyệt'
    )
    previous_status = models.CharField(max_length=20, verbose_name='Trạng thái trước')
    new_status = models.CharField(max_length=20, verbose_name='Trạng thái mới')
    assigned_role = models.CharField(max_length=30, blank=True, verbose_name='Vai trò được phân công')
    reason = models.TextField(blank=True, verbose_name='Lý do / Phản hồi cho người dùng')
    internal_notes = models.TextField(blank=True, verbose_name='Ghi chú nội bộ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời điểm xét duyệt')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lịch sử xét duyệt tài khoản'
        verbose_name_plural = 'Lịch sử xét duyệt tài khoản'

    def __str__(self):
        reviewer_name = self.reviewer.username if self.reviewer else 'Hệ thống'
        return f"[{self.created_at.strftime('%d/%m/%Y %H:%M')}] {reviewer_name} chuyển {self.user.username}: {self.previous_status} -> {self.new_status}"


class Notification(models.Model):
    TYPE_SYSTEM = 'SYSTEM'
    TYPE_REGISTRATION = 'REGISTRATION'
    TYPE_APPROVAL = 'APPROVAL'
    TYPE_CONDUCT = 'CONDUCT'
    TYPE_ALERT = 'ALERT'

    TYPE_CHOICES = [
        (TYPE_SYSTEM, 'Hệ thống'),
        (TYPE_REGISTRATION, 'Đăng ký mới'),
        (TYPE_APPROVAL, 'Xét duyệt tài khoản'),
        (TYPE_CONDUCT, 'Nền nếp & Vi phạm'),
        (TYPE_ALERT, 'Cảnh báo sớm'),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Người nhận'
    )
    notification_type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        default=TYPE_SYSTEM,
        verbose_name='Loại thông báo'
    )
    title = models.CharField(max_length=200, verbose_name='Tiêu đề')
    message = models.TextField(verbose_name='Nội dung')
    link = models.CharField(max_length=200, blank=True, verbose_name='Đường dẫn liên quan')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Đã xem lúc')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời điểm tạo')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Thông báo'
        verbose_name_plural = 'Danh sách thông báo'
        indexes = [
            models.Index(fields=['recipient', 'read_at'], name='idx_notif_recipient_read'),
            models.Index(fields=['recipient', '-created_at'], name='idx_notif_recip_created'),
        ]

    def __str__(self):
        return f"[{self.notification_type}] {self.title} -> {self.recipient.username}"

    @property
    def is_read(self):
        return self.read_at is not None

