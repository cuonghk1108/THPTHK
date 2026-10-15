import uuid
from django.db import models
from django.utils import timezone
from core.models import User, AcademicYear


class SchoolClass(models.Model):
    name = models.CharField(max_length=20, verbose_name='Tên lớp (VD: 10A1, 11A2)')
    grade = models.PositiveSmallIntegerField(choices=[(10, 'Khối 10'), (11, 'Khối 11'), (12, 'Khối 12')], verbose_name='Khối lớp')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='classes', verbose_name='Năm học')
    homeroom_teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='homeroom_classes', verbose_name='Giáo viên chủ nhiệm'
    )
    student_count = models.PositiveIntegerField(default=40, verbose_name='Sĩ số')
    room_number = models.CharField(max_length=50, blank=True, verbose_name='Phòng học')
    union_branch_name = models.CharField(max_length=100, blank=True, verbose_name='Tên Chi đoàn')

    class Meta:
        unique_together = ('name', 'academic_year')
        ordering = ['grade', 'name']
        verbose_name = 'Lớp học & Chi đoàn'
        verbose_name_plural = 'Danh sách Lớp học & Chi đoàn'

    def __str__(self):
        return f"Lớp {self.name} ({self.academic_year.name})"

    def save(self, *args, **kwargs):
        if not self.union_branch_name:
            self.union_branch_name = f"Chi đoàn {self.name}"
        super().save(*args, **kwargs)


class Student(models.Model):
    GENDER_CHOICES = [
        ('M', 'Nam'),
        ('F', 'Nữ'),
    ]
    STATUS_CHOICES = [
        ('STUDYING', 'Đang học'),
        ('SUSPENDED', 'Đình chỉ'),
        ('TRANSFERRED', 'Chuyển trường'),
        ('GRADUATED', 'Đã tốt nghiệp'),
    ]

    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_profile')
    student_code = models.CharField(max_length=30, unique=True, verbose_name='Mã học sinh nội bộ')
    full_name = models.CharField(max_length=150, verbose_name='Họ và tên')
    date_of_birth = models.DateField(verbose_name='Ngày sinh')
    gender = models.CharField(max_length=5, choices=GENDER_CHOICES, default='M', verbose_name='Giới tính')
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='students', verbose_name='Lớp học')
    is_union_member = models.BooleanField(default=True, verbose_name='Đoàn viên TNCS Hồ Chí Minh')
    is_red_star = models.BooleanField(default=False, verbose_name='Thành viên Đội Sao đỏ')
    parent_name = models.CharField(max_length=150, blank=True, verbose_name='Họ tên phụ huynh')
    parent_phone = models.CharField(max_length=20, blank=True, verbose_name='SĐT phụ huynh')
    address = models.CharField(max_length=255, blank=True, verbose_name='Địa chỉ cư trú')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='STUDYING', verbose_name='Tình trạng học')

    class Meta:
        ordering = ['school_class', 'full_name']
        verbose_name = 'Học sinh'
        verbose_name_plural = 'Danh sách học sinh'

    def __str__(self):
        return f"{self.full_name} ({self.student_code}) - Lớp {self.school_class.name}"


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    teacher_code = models.CharField(max_length=30, unique=True, verbose_name='Mã giáo viên')
    full_name = models.CharField(max_length=150, verbose_name='Họ và tên')
    subject = models.CharField(max_length=100, verbose_name='Môn giảng dạy')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Số điện thoại')

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Giáo viên'
        verbose_name_plural = 'Danh sách giáo viên'

    def __str__(self):
        return f"{self.full_name} - Môn {self.subject}"


class ConductRuleCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name='Tên nhóm nội quy')
    description = models.TextField(blank=True, verbose_name='Mô tả nhóm')
    icon = models.CharField(max_length=50, default='shield', verbose_name='Mã biểu tượng')
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Nhóm nội quy'
        verbose_name_plural = 'Danh mục nhóm nội quy'

    def __str__(self):
        return self.name


class ConductRule(models.Model):
    SEVERITY_CHOICES = [
        ('LOW', 'Nhẹ'),
        ('MEDIUM', 'Trung bình'),
        ('HIGH', 'Nghiêm trọng'),
        ('CRITICAL', 'Rất nghiêm trọng'),
    ]

    category = models.ForeignKey(ConductRuleCategory, on_delete=models.CASCADE, related_name='rules', verbose_name='Nhóm nội quy')
    code = models.CharField(max_length=30, unique=True, verbose_name='Mã quy định (VD: VP-01)')
    name = models.CharField(max_length=255, verbose_name='Tên hành vi vi phạm')
    default_points_deducted = models.DecimalField(
        max_digits=5, decimal_places=2, default=2.00, verbose_name='Điểm trừ mặc định'
    )
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='LOW', verbose_name='Mức độ vi phạm')
    description = models.TextField(blank=True, verbose_name='Chi tiết quy định và xử lý')
    is_active = models.BooleanField(default=True, verbose_name='Đang áp dụng')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'code']
        verbose_name = 'Nội quy nền nếp'
        verbose_name_plural = 'Danh mục nội quy nền nếp'

    def __str__(self):
        return f"[{self.code}] {self.name} (-{self.default_points_deducted}đ)"


def evidence_upload_path(instance, filename):
    return f"evidence/{timezone.now().strftime('%Y/%m')}/{uuid.uuid4().hex[:12]}_{filename}"


class ViolationRecord(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_VERIFIED = 'VERIFIED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_ADJUSTED = 'ADJUSTED'
    STATUS_APPEALING = 'APPEALING'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Chờ xác minh'),
        (STATUS_VERIFIED, 'Đã xác minh'),
        (STATUS_REJECTED, 'Không đủ căn cứ'),
        (STATUS_ADJUSTED, 'Đã điều chỉnh'),
        (STATUS_APPEALING, 'Đang khiếu nại / giải trình'),
    ]

    record_code = models.CharField(max_length=40, unique=True, verbose_name='Mã bản ghi vi phạm')
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='violations', verbose_name='Lớp vi phạm')
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='violations', verbose_name='Học sinh vi phạm')
    student_name_snapshot = models.CharField(max_length=150, blank=True, verbose_name='Tên học sinh ghi nhận')
    rule = models.ForeignKey(ConductRule, on_delete=models.CASCADE, related_name='violation_records', verbose_name='Lỗi vi phạm')
    occurred_at = models.DateTimeField(default=timezone.now, verbose_name='Thời điểm vi phạm')
    location = models.CharField(max_length=150, default='Khuôn viên trường', verbose_name='Vị trí ghi nhận')
    description = models.TextField(blank=True, verbose_name='Mô tả chi tiết sự việc')
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_violations', verbose_name='Người ghi nhận')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='Trạng thái xác minh')
    points_deducted = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, 
        verbose_name='Điểm trừ thực tế áp dụng (chỉ tính khi đã xác minh)'
    )
    
    # Evidence (Strictly protected, face cropping optional, privacy compliant)
    evidence_image = models.ImageField(upload_to=evidence_upload_path, null=True, blank=True, verbose_name='Ảnh minh chứng')
    evidence_notes = models.TextField(blank=True, verbose_name='Ghi chú minh chứng')

    # Verification details
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_violations', verbose_name='Người xác minh')
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm xác minh')
    verification_notes = models.TextField(blank=True, verbose_name='Ý kiến xác minh')

    # Appeal / Explanation workflow
    appeal_reason = models.TextField(blank=True, verbose_name='Lý do giải trình / khiếu nại')
    appeal_submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='appealed_violations', verbose_name='Người gửi khiếu nại')
    appeal_submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm khiếu nại')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-occurred_at']
        verbose_name = 'Bản ghi vi phạm nền nếp'
        verbose_name_plural = 'Danh sách bản ghi vi phạm'

    def __str__(self):
        target = self.student.full_name if self.student else f"Tập thể {self.school_class.name}"
        return f"[{self.record_code}] {target} - {self.rule.name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.record_code:
            now_str = timezone.now().strftime('%Y%m%d%H%M')
            short_id = uuid.uuid4().hex[:4].upper()
            self.record_code = f"VP-{now_str}-{short_id}"
        if self.student and not self.student_name_snapshot:
            self.student_name_snapshot = self.student.full_name
        super().save(*args, **kwargs)


class ViolationReviewHistory(models.Model):
    violation = models.ForeignKey(ViolationRecord, on_delete=models.CASCADE, related_name='reviews', verbose_name='Bản ghi vi phạm')
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Người thao tác')
    previous_status = models.CharField(max_length=20, verbose_name='Trạng thái cũ')
    new_status = models.CharField(max_length=20, verbose_name='Trạng thái mới')
    points_applied = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name='Điểm trừ áp dụng')
    reason = models.TextField(verbose_name='Lý do điều chỉnh / quyết định')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lịch sử thẩm định vi phạm'
        verbose_name_plural = 'Lịch sử thẩm định vi phạm'

    def __str__(self):
        return f"{self.violation.record_code}: {self.previous_status} -> {self.new_status} bởi {self.performed_by.username}"
