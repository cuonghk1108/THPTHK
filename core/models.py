from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_ADMIN = 'ADMIN'
    ROLE_BGH = 'BGH'
    ROLE_DOAN_TRUONG = 'DOAN_TRUONG'
    ROLE_SAO_DO = 'SAO_DO'
    ROLE_GVCN = 'GVCN'
    ROLE_GVBM = 'GVBM'
    ROLE_HOC_SINH = 'HOC_SINH'
    ROLE_CHUYEN_VIEN_TAM_LY = 'CHUYEN_VIEN_TAM_LY'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Quản trị viên hệ thống'),
        (ROLE_BGH, 'Ban Giám hiệu'),
        (ROLE_DOAN_TRUONG, 'Đoàn trường'),
        (ROLE_SAO_DO, 'Đội Sao đỏ / Trực tuần'),
        (ROLE_GVCN, 'Giáo viên chủ nhiệm'),
        (ROLE_GVBM, 'Giáo viên bộ môn'),
        (ROLE_HOC_SINH, 'Học sinh'),
        (ROLE_CHUYEN_VIEN_TAM_LY, 'Chuyên viên tư vấn tâm lý'),
    ]

    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_HOC_SINH)
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

    class Meta:
        verbose_name = 'Người dùng'
        verbose_name_plural = 'Danh sách người dùng'

    def __str__(self):
        display_name = self.full_name or self.username
        return f"{display_name} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    @property
    def is_bgh(self):
        return self.role == self.ROLE_BGH

    @property
    def is_doan_truong(self):
        return self.role == self.ROLE_DOAN_TRUONG

    @property
    def is_sao_do(self):
        return self.role == self.ROLE_SAO_DO

    @property
    def is_gvcn(self):
        return self.role == self.ROLE_GVCN

    @property
    def is_student(self):
        return self.role == self.ROLE_HOC_SINH

    @property
    def has_counseling_access(self):
        return self.role == self.ROLE_CHUYEN_VIEN_TAM_LY or self.can_view_counseling


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

    def __str__(self):
        username = self.user.username if self.user else 'Khách / Hệ thống'
        return f"[{self.created_at.strftime('%d/%m/%Y %H:%M')}] {username} - {self.action} on {self.resource_type}"
