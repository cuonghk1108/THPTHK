
def natural_class_sort_key(val):
    """
    Sắp xếp tự nhiên chuẩn theo số thứ tự lớp từ nhỏ đến lớn:
    Ví dụ: 10A1 -> 10A2 -> ... -> 10A9 -> 10A10 -> ... -> 10A22
    """
    if val is None:
        return (0, '', 0)
    if hasattr(val, 'name'):
        name = val.name
        grade = getattr(val, 'grade', 0)
    elif hasattr(val, 'school_class'):
        name = val.school_class.name
        grade = getattr(val.school_class, 'grade', 0)
    elif isinstance(val, dict):
        name = val.get('name') or val.get('class_name') or val.get('school_class_name') or ''
        grade = val.get('grade') or 0
    else:
        name = str(val)
        grade = 0
    import re
    m = re.match(r'^(\d+)([A-Za-zĐđ]+)(\d+)$', name.strip())
    if m:
        return (int(m.group(1)), m.group(2).upper(), int(m.group(3)))
    m2 = re.match(r'^(\d+)(.*)$', name.strip())
    if m2:
        try:
            num = int(re.search(r'\d+', m2.group(2)).group()) if re.search(r'\d+', m2.group(2)) else 0
        except Exception:
            num = 0
        return (int(m2.group(1)), m2.group(2).strip(), num)
    return (grade, name, 0)

import uuid
from django.db import models
from django.utils import timezone
from core.models import User, AcademicYear


class SchoolClass(models.Model):
    name = models.CharField(max_length=20, verbose_name='Tên lớp (VD: 10A1, 11A2)')
    grade = models.PositiveSmallIntegerField(choices=[(10, 'Khối 10'), (11, 'Khối 11'), (12, 'Khối 12')], verbose_name='Khối lớp')
    class_order = models.PositiveSmallIntegerField(default=1, verbose_name='Thứ tự lớp (1-22)')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='classes', verbose_name='Năm học')
    homeroom_teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='homeroom_classes', verbose_name='Giáo viên chủ nhiệm'
    )
    student_count = models.PositiveIntegerField(default=40, verbose_name='Sĩ số')
    room_number = models.CharField(max_length=50, blank=True, verbose_name='Phòng học')
    union_branch_name = models.CharField(max_length=100, blank=True, verbose_name='Tên Chi đoàn')
    monitor = models.ForeignKey('Student', on_delete=models.SET_NULL, null=True, blank=True, related_name='monitored_classes', verbose_name='Lớp trưởng')
    is_active = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    created_at = models.DateTimeField(auto_now_add=True, null=True, verbose_name='Thời điểm tạo')

    def save(self, *args, **kwargs):
        if self.name:
            import re
            m = re.match(r'^(\d+)[A-Za-zĐđ]+(\d+)$', self.name.strip())
            if m:
                self.class_order = int(m.group(2))
            else:
                m2 = re.search(r'(\d+)$', self.name.strip())
                if m2:
                    self.class_order = int(m2.group(1))
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('name', 'academic_year')
        ordering = ['grade', 'class_order', 'name']
        verbose_name = 'Lớp học & Chi đoàn'
        verbose_name_plural = 'Danh sách Lớp học & Chi đoàn'
        indexes = [
            models.Index(fields=['is_active', 'grade'], name='idx_class_active_grade'),
            models.Index(fields=['homeroom_teacher'], name='idx_class_homeroom'),
        ]

    def __str__(self):
        return f"Lớp {self.name} ({self.academic_year.name})"

    @property
    def class_code(self):
        return self.name

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
    is_class_monitor = models.BooleanField(default=False, db_index=True, verbose_name='Lớp trưởng')
    parent_name = models.CharField(max_length=150, blank=True, verbose_name='Họ tên phụ huynh')
    parent_phone = models.CharField(max_length=20, blank=True, verbose_name='SĐT phụ huynh')
    address = models.CharField(max_length=255, blank=True, verbose_name='Địa chỉ cư trú')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='STUDYING', verbose_name='Tình trạng học')

    class Meta:
        ordering = ['school_class', 'full_name']
        verbose_name = 'Học sinh'
        verbose_name_plural = 'Danh sách học sinh'
        indexes = [
            models.Index(fields=['school_class', 'status'], name='idx_student_class_status'),
            models.Index(fields=['student_code'], name='idx_student_code'),
        ]

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
    submission_key = models.UUIDField(null=True, blank=True, unique=True, verbose_name='Khóa chống gửi báo cáo trùng')
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
    score_before = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Điểm thi đua lớp trước khi trừ'
    )
    score_after = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Điểm thi đua lớp sau khi trừ'
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
        indexes = [
            models.Index(fields=['status', '-occurred_at'], name='idx_vr_status_occ'),
            models.Index(fields=['school_class', '-occurred_at'], name='idx_vr_class_occ'),
            models.Index(fields=['school_class', 'status'], name='idx_vr_class_status'),
            models.Index(fields=['-occurred_at'], name='idx_vr_occurred_at'),
            models.Index(fields=['status'], name='idx_vr_status'),
        ]

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
    score_before = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Điểm thi đua lớp trước thao tác'
    )
    score_after = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Điểm thi đua lớp sau thao tác'
    )
    reason = models.TextField(verbose_name='Lý do điều chỉnh / quyết định')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lịch sử thẩm định vi phạm'
        verbose_name_plural = 'Lịch sử thẩm định vi phạm'

    def __str__(self):
        return f"{self.violation.record_code}: {self.previous_status} -> {self.new_status} bởi {self.performed_by.username}"


class SmsConfiguration(models.Model):
    PROVIDER_TWILIO = 'TWILIO'
    PROVIDER_SPEEDSMS = 'SPEEDSMS'
    PROVIDER_CHOICES = [
        (PROVIDER_SPEEDSMS, 'SpeedSMS'),
        (PROVIDER_TWILIO, 'Twilio (cũ)'),
    ]

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    is_enabled = models.BooleanField(default=False, verbose_name='Bật gửi SMS')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default=PROVIDER_SPEEDSMS)
    recipient_phone = models.CharField(max_length=20, blank=True, verbose_name='Số điện thoại Đoàn trường')
    sms_type = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Loại tin nhắn SpeedSMS')
    sender = models.CharField(max_length=100, blank=True, verbose_name='Sender SpeedSMS')
    max_retries = models.PositiveSmallIntegerField(default=3, verbose_name='Số lần gửi lại tối đa')
    retry_delay_seconds = models.PositiveSmallIntegerField(default=30, verbose_name='Thời gian chờ thử lại (giây)')
    rate_limit_per_minute = models.PositiveSmallIntegerField(default=10, verbose_name='Giới hạn tin/phút')
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_sms_configurations',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cấu hình thông báo SMS'
        verbose_name_plural = 'Cấu hình thông báo SMS'

    @classmethod
    def load(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config

    def __str__(self):
        return 'Cấu hình thông báo SMS Đoàn trường'


class SmsNotification(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_SENDING = 'SENDING'
    STATUS_ACCEPTED = 'ACCEPTED'
    STATUS_SENT = 'SENT'
    STATUS_DELIVERED = 'DELIVERED'
    STATUS_FAILED = 'FAILED'
    STATUS_SKIPPED = 'SKIPPED'
    STATUS_LEGACY_SIMULATED = 'SIMULATED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Đang chờ gửi'),
        (STATUS_SENDING, 'Đang gửi'),
        (STATUS_ACCEPTED, 'Nhà cung cấp đã nhận yêu cầu'),
        (STATUS_SENT, 'Nhà cung cấp đã gửi'),
        (STATUS_DELIVERED, 'Đã chuyển đến người nhận'),
        (STATUS_FAILED, 'Gửi thất bại'),
        (STATUS_SKIPPED, 'Bỏ qua'),
        (STATUS_LEGACY_SIMULATED, 'Mô phỏng cũ, chưa gửi thật'),
    ]

    violation = models.ForeignKey(
        ViolationRecord,
        on_delete=models.CASCADE,
        related_name='sms_notifications',
        null=True,
        blank=True,
        verbose_name='Bản ghi vi phạm',
    )
    recipient_phone = models.CharField(max_length=20, blank=True, verbose_name='Số nhận SMS')
    provider = models.CharField(
        max_length=20,
        choices=SmsConfiguration.PROVIDER_CHOICES,
        default=SmsConfiguration.PROVIDER_SPEEDSMS,
    )
    is_test = models.BooleanField(default=False, verbose_name='Tin nhắn kiểm tra')
    idempotency_key = models.UUIDField(null=True, blank=True, unique=True, verbose_name='Khóa chống gửi trùng')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    provider_status = models.CharField(max_length=30, blank=True, verbose_name='Trạng thái nhà cung cấp')
    provider_message_id = models.CharField(max_length=100, blank=True, verbose_name='Mã tin nhắn nhà cung cấp')
    message_content = models.TextField(blank=True, verbose_name='Nội dung SMS đã gửi')
    provider_total_sms = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Số SMS tính phí')
    provider_total_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                               verbose_name='Chi phí nhà cung cấp')
    attempt_count = models.PositiveSmallIntegerField(default=0, verbose_name='Số lần đã thử gửi')
    max_retries = models.PositiveSmallIntegerField(default=3, verbose_name='Số lần gửi lại tối đa')
    next_attempt_at = models.DateTimeField(default=timezone.now, verbose_name='Thời điểm thử tiếp theo')
    needs_admin_attention = models.BooleanField(default=False, verbose_name='Cần quản trị viên kiểm tra')
    error_code = models.CharField(max_length=40, blank=True, verbose_name='Mã lỗi gần nhất')
    last_error = models.CharField(max_length=500, blank=True, verbose_name='Lỗi gần nhất')
    last_attempt_at = models.DateTimeField(null=True, blank=True, verbose_name='Lần thử gần nhất')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm nhà cung cấp gửi tin')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm chuyển đến người nhận')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Thông báo SMS vi phạm'
        verbose_name_plural = 'Lịch sử thông báo SMS'
        constraints = [
            models.UniqueConstraint(
                fields=['violation', 'recipient_phone'],
                condition=models.Q(violation__isnull=False),
                name='unique_violation_sms_recipient',
            ),
        ]
        indexes = [models.Index(fields=['status', 'next_attempt_at'], name='sms_queue_status_due_idx')]

    def __str__(self):
        code = self.violation.record_code if self.violation_id else 'SMS kiểm tra'
        return f'{code} – {self.get_status_display()}'


class SmsAttempt(models.Model):
    STATUS_STARTED = 'STARTED'
    STATUS_ACCEPTED = 'ACCEPTED'
    STATUS_SENT = 'SENT'
    STATUS_DELIVERED = 'DELIVERED'
    STATUS_FAILED = 'FAILED'
    STATUS_AMBIGUOUS = 'AMBIGUOUS'

    STATUS_CHOICES = [
        (STATUS_STARTED, 'Đang gửi'),
        (STATUS_ACCEPTED, 'Nhà cung cấp đã nhận'),
        (STATUS_SENT, 'Đã gửi'),
        (STATUS_DELIVERED, 'Đã chuyển đến người nhận'),
        (STATUS_FAILED, 'Gửi thất bại'),
        (STATUS_AMBIGUOUS, 'Chưa xác định kết quả'),
    ]

    notification = models.ForeignKey(SmsNotification, on_delete=models.CASCADE, related_name='attempts')
    attempt_number = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_STARTED)
    provider_status = models.CharField(max_length=30, blank=True)
    provider_message_id = models.CharField(max_length=100, blank=True)
    provider_total_sms = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Số SMS tính phí')
    provider_total_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                               verbose_name='Chi phí nhà cung cấp')
    error_code = models.CharField(max_length=40, blank=True)
    error_message = models.CharField(max_length=500, blank=True)
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Lần thử gửi SMS'
        verbose_name_plural = 'Lịch sử thử gửi SMS'
        constraints = [
            models.UniqueConstraint(
                fields=['notification', 'attempt_number'],
                name='unique_sms_attempt_number',
            ),
        ]


class SmsProviderStatusEvent(models.Model):
    notification = models.ForeignKey(
        SmsNotification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='provider_events',
    )
    provider_message_id = models.CharField(max_length=100, db_index=True)
    provider_phone = models.CharField(max_length=20, blank=True)
    provider_status = models.CharField(max_length=30)
    event_key = models.CharField(max_length=64, null=True, blank=True, unique=True)
    error_code = models.CharField(max_length=40, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['received_at']
        verbose_name = 'Sự kiện trạng thái từ nhà cung cấp SMS'
        verbose_name_plural = 'Sự kiện trạng thái SMS'

    def __str__(self):
        return f'{self.provider_message_id}: {self.provider_status}'


class ViolationEmailNotification(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_SENDING = 'SENDING'
    STATUS_SENT = 'SENT'
    STATUS_FAILED = 'FAILED'
    STATUS_SKIPPED = 'SKIPPED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Đang chờ gửi'),
        (STATUS_SENDING, 'Đang gửi'),
        (STATUS_SENT, 'SMTP đã chấp nhận'),
        (STATUS_FAILED, 'Gửi thất bại'),
        (STATUS_SKIPPED, 'Bỏ qua (chưa cấu hình email)'),
    ]

    violation = models.ForeignKey(
        ViolationRecord,
        on_delete=models.CASCADE,
        related_name='email_notifications',
        null=True,
        blank=True,
        verbose_name='Bản ghi vi phạm',
    )
    recipient_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='violation_email_notifications',
        verbose_name='Tài khoản Đoàn trường nhận'
    )
    recipient_email = models.EmailField(verbose_name='Email người nhận (Đoàn trường)')
    is_test = models.BooleanField(default=False, verbose_name='Email kiểm tra')
    idempotency_key = models.UUIDField(null=True, blank=True, unique=True, verbose_name='Khóa chống gửi trùng')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='Trạng thái gửi')
    subject = models.CharField(max_length=255, verbose_name='Tiêu đề email')
    body_text = models.TextField(blank=True, verbose_name='Nội dung văn bản thuần')
    body_html = models.TextField(blank=True, verbose_name='Nội dung HTML')
    attempt_count = models.PositiveSmallIntegerField(default=0, verbose_name='Số lần đã thử gửi')
    max_retries = models.PositiveSmallIntegerField(default=3, verbose_name='Số lần thử lại tối đa')
    next_attempt_at = models.DateTimeField(default=timezone.now, verbose_name='Thời điểm thử gửi tiếp theo')
    last_error = models.TextField(blank=True, verbose_name='Lỗi gần nhất')
    last_attempt_at = models.DateTimeField(null=True, blank=True, verbose_name='Lần thử gần nhất')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm gửi thành công')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời điểm tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Thời điểm cập nhật')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Thông báo Email vi phạm'
        verbose_name_plural = 'Lịch sử thông báo Email vi phạm'
        constraints = [
            models.UniqueConstraint(
                fields=['violation', 'recipient_email'],
                condition=models.Q(violation__isnull=False),
                name='unique_violation_email_recipient',
            ),
        ]
        indexes = [
            models.Index(fields=['status', 'created_at'], name='email_notif_status_created_idx'),
        ]

    def __str__(self):
        return f"Email {self.status}: {self.recipient_email} - {self.subject}"


class TeacherClassAssignment(models.Model):
    """
    Quản lý phân công giáo viên bộ môn giảng dạy nhiều lớp.
    Một giáo viên có thể dạy nhiều lớp thuộc cùng một khối hoặc nhiều khối khác nhau.
    """
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='teaching_assignments', verbose_name='Giáo viên bộ môn'
    )
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE, related_name='teacher_assignments', verbose_name='Lớp giảng dạy'
    )
    subject = models.CharField(max_length=100, verbose_name='Môn giảng dạy')
    assigned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_teaching_records', verbose_name='Người phân công'
    )
    start_date = models.DateField(default=timezone.now, verbose_name='Ngày bắt đầu')
    end_date = models.DateField(null=True, blank=True, verbose_name='Ngày kết thúc')
    is_active = models.BooleanField(default=True, verbose_name='Đang có hiệu lực')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['school_class__grade', 'school_class__name', 'subject']
        verbose_name = 'Phân công giáo viên bộ môn'
        verbose_name_plural = 'Danh sách phân công giáo viên bộ môn'
        constraints = [
            models.UniqueConstraint(
                fields=['teacher', 'school_class', 'subject'],
                condition=models.Q(is_active=True),
                name='unique_active_teacher_class_subject'
            )
        ]

    def __str__(self):
        teacher_name = self.teacher.full_name or self.teacher.username
        return f"{teacher_name} - {self.subject} ({self.school_class.name})"


class HomeroomAssignment(models.Model):
    """
    Quản lý bổ nhiệm giáo viên chủ nhiệm (GVCN) và lịch sử thay đổi GVCN.
    Mỗi lớp chỉ có tối đa một GVCN chính đang hoạt động (is_active=True) tại một thời điểm.
    """
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='homeroom_assignments', verbose_name='Giáo viên chủ nhiệm'
    )
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE, related_name='homeroom_assignments', verbose_name='Lớp chủ nhiệm'
    )
    assigned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_homeroom_records', verbose_name='Người bổ nhiệm'
    )
    start_date = models.DateField(default=timezone.now, verbose_name='Ngày bắt đầu nhiệm vụ')
    end_date = models.DateField(null=True, blank=True, verbose_name='Ngày kết thúc nhiệm kỳ')
    is_active = models.BooleanField(default=True, verbose_name='Đang đảm nhiệm')
    notes = models.TextField(blank=True, verbose_name='Ghi chú / Quyết định bổ nhiệm')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date', 'school_class']
        verbose_name = 'Phân công giáo viên chủ nhiệm'
        verbose_name_plural = 'Lịch sử phân công giáo viên chủ nhiệm'
        constraints = [
            models.UniqueConstraint(
                fields=['school_class'],
                condition=models.Q(is_active=True),
                name='unique_active_homeroom_per_class'
            )
        ]

    def __str__(self):
        status_text = "Đang đảm nhiệm" if self.is_active else "Lịch sử"
        teacher_name = self.teacher.full_name or self.teacher.username
        return f"{self.school_class.name}: {teacher_name} ({status_text})"


def reflection_upload_path(instance, filename):
    return f"reflections/{timezone.now().strftime('%Y/%m')}/{uuid.uuid4().hex[:12]}_{filename}"


class TeacherReflection(models.Model):
    """
    Phản ánh của Giáo viên bộ môn về tình hình nền nếp, hành vi học sinh.
    QUY TẮC: Phản ánh là thông tin phản ánh để xem xét, KHÔNG tự động trừ điểm thi đua học sinh.
    Chỉ khi người có thẩm quyền (GVCN / Admin) xác minh và xử lý thì mới chuyển thành vi phạm.
    """
    TYPE_ACADEMIC = 'ACADEMIC_DISCIPLINE'
    TYPE_ATTENDANCE = 'ATTENDANCE_LATE'
    TYPE_ATTITUDE = 'ATTITUDE'
    TYPE_REGULATION = 'SCHOOL_REGULATION'
    TYPE_VERIFICATION = 'NEEDS_VERIFICATION'
    TYPE_PRAISE = 'PRAISE'
    TYPE_OTHER = 'OTHER'

    TYPE_CHOICES = [
        (TYPE_ACADEMIC, 'Nền nếp học tập'),
        (TYPE_ATTENDANCE, 'Đi học muộn hoặc nghỉ học'),
        (TYPE_ATTITUDE, 'Thái độ trong giờ học'),
        (TYPE_REGULATION, 'Việc thực hiện nội quy'),
        (TYPE_VERIFICATION, 'Hành vi cần nhà trường xác minh'),
        (TYPE_PRAISE, 'Khen ngợi hoặc hành vi tích cực'),
        (TYPE_OTHER, 'Khác'),
    ]

    STATUS_NEW = 'NEW'
    STATUS_RECEIVED = 'RECEIVED'
    STATUS_VERIFYING = 'VERIFYING'
    STATUS_NEED_INFO = 'NEED_INFO'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CLOSED = 'CLOSED'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Mới gửi'),
        (STATUS_RECEIVED, 'Đã tiếp nhận'),
        (STATUS_VERIFYING, 'Đang xác minh'),
        (STATUS_NEED_INFO, 'Yêu cầu bổ sung thông tin'),
        (STATUS_RESOLVED, 'Đã xử lý'),
        (STATUS_REJECTED, 'Không đủ căn cứ'),
        (STATUS_CLOSED, 'Đã đóng'),
    ]

    URGENCY_LOW = 'LOW'
    URGENCY_MEDIUM = 'MEDIUM'
    URGENCY_HIGH = 'HIGH'

    URGENCY_CHOICES = [
        (URGENCY_LOW, 'Bình thường'),
        (URGENCY_MEDIUM, 'Cần chú ý'),
        (URGENCY_HIGH, 'Khẩn cấp'),
    ]

    reflection_code = models.CharField(max_length=40, unique=True, verbose_name='Mã phản ánh')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_reflections', verbose_name='Giáo viên phản ánh')
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='class_reflections', verbose_name='Lớp liên quan')
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_reflections', verbose_name='Học sinh liên quan')
    student_name_snapshot = models.CharField(max_length=150, blank=True, verbose_name='Tên học sinh / đối tượng')
    reflection_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_ACADEMIC, verbose_name='Loại phản ánh')
    content = models.TextField(verbose_name='Nội dung chi tiết sự việc')
    occurred_at = models.DateTimeField(default=timezone.now, verbose_name='Thời gian xảy ra sự việc')
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default=URGENCY_LOW, verbose_name='Mức độ khẩn cấp')
    evidence_image = models.ImageField(upload_to=reflection_upload_path, null=True, blank=True, verbose_name='Ảnh / Tài liệu minh chứng')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW, verbose_name='Trạng thái xử lý')
    feedback_notes = models.TextField(blank=True, verbose_name='Ý kiến phản hồi / Chỉ đạo xử lý')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_reflections', verbose_name='Người xử lý (GVCN / Admin)')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm xử lý')

    violation_record = models.ForeignKey(
        ViolationRecord, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='originating_reflections', verbose_name='Bản ghi vi phạm đã chuyển đổi'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Phản ánh của giáo viên bộ môn'
        verbose_name_plural = 'Danh sách phản ánh nền nếp'

    def __str__(self):
        target = self.student_name_snapshot or f"Tập thể {self.school_class.name}"
        teacher_name = self.teacher.full_name or self.teacher.username
        return f"[{self.reflection_code}] {teacher_name} -> {target} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.reflection_code:
            now_str = timezone.now().strftime('%Y%m%d%H%M')
            short_id = uuid.uuid4().hex[:4].upper()
            self.reflection_code = f"PA-{now_str}-{short_id}"
        if self.student and not self.student_name_snapshot:
            self.student_name_snapshot = self.student.full_name
        elif not self.student and not self.student_name_snapshot:
            self.student_name_snapshot = f"Tập thể {self.school_class.name}"
        super().save(*args, **kwargs)


class ReflectionHistory(models.Model):
    """Nhật ký xử lý phản ánh nền nếp"""
    reflection = models.ForeignKey(TeacherReflection, on_delete=models.CASCADE, related_name='histories', verbose_name='Phản ánh')
    action = models.CharField(max_length=30, verbose_name='Hành động')
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Người thực hiện')
    previous_status = models.CharField(max_length=20, verbose_name='Trạng thái trước')
    new_status = models.CharField(max_length=20, verbose_name='Trạng thái sau')
    notes = models.TextField(blank=True, verbose_name='Ghi chú thao tác')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lịch sử xử lý phản ánh'
        verbose_name_plural = 'Lịch sử xử lý phản ánh'

    def __str__(self):
        return f"{self.reflection.reflection_code}: {self.previous_status} -> {self.new_status} bởi {self.performed_by.username}"


class RedStarAssignment(models.Model):
    """
    Phân công chức danh và phạm vi nhiệm vụ Đội Sao đỏ / Cờ đỏ cho học sinh.
    Chỉ học sinh đã có tài khoản phê duyệt (APPROVED) mới được phân công.
    """
    SCOPE_CLASS = 'CLASS'
    SCOPE_MULTI_CLASS = 'MULTI_CLASS'
    SCOPE_GRADE = 'GRADE'
    SCOPE_AREA = 'AREA'
    SCOPE_ALL_SCHOOL = 'ALL_SCHOOL'

    SCOPE_CHOICES = [
        (SCOPE_CLASS, 'Một lớp cụ thể'),
        (SCOPE_MULTI_CLASS, 'Nhiều lớp'),
        (SCOPE_GRADE, 'Theo khối lớp'),
        (SCOPE_AREA, 'Khu vực / Ca trực'),
        (SCOPE_ALL_SCHOOL, 'Toàn trường'),
    ]

    STATUS_ACTIVE = 'ACTIVE'
    STATUS_SUSPENDED = 'SUSPENDED'
    STATUS_REVOKED = 'REVOKED'
    STATUS_EXPIRED = 'EXPIRED'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Đang hoạt động'),
        (STATUS_SUSPENDED, 'Tạm dừng'),
        (STATUS_REVOKED, 'Đã thu hồi'),
        (STATUS_EXPIRED, 'Đã hết hạn'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='red_star_assignments', verbose_name='Tài khoản học sinh')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True, related_name='red_star_assignments', verbose_name='Hồ sơ học sinh')
    scope_type = models.CharField(max_length=20, choices=SCOPE_CHOICES, default=SCOPE_CLASS, verbose_name='Loại phạm vi nhiệm vụ')
    assigned_class = models.ForeignKey(SchoolClass, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_red_star_single', verbose_name='Lớp phân công (1 lớp)')
    assigned_classes = models.ManyToManyField(SchoolClass, blank=True, related_name='assigned_red_star_multi', verbose_name='Danh sách lớp phân công')
    assigned_grade = models.PositiveSmallIntegerField(null=True, blank=True, choices=[(10, 'Khối 10'), (11, 'Khối 11'), (12, 'Khối 12')], verbose_name='Khối phân công')
    area_name = models.CharField(max_length=150, blank=True, verbose_name='Khu vực / Ca trực')

    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_red_star_assignments', verbose_name='Người phân công')
    start_date = models.DateField(default=timezone.now, verbose_name='Ngày bắt đầu')
    end_date = models.DateField(null=True, blank=True, verbose_name='Ngày kết thúc')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE, verbose_name='Trạng thái nhiệm vụ')
    notes = models.TextField(blank=True, verbose_name='Ghi chú / Quyết định phân công')

    revoked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='revoked_red_stars', verbose_name='Người thu hồi / tạm dừng')
    revoked_at = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm thu hồi')
    revoke_reason = models.TextField(blank=True, verbose_name='Lý do thu hồi / tạm dừng')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Phân công nhiệm vụ Sao đỏ'
        verbose_name_plural = 'Danh sách phân công nhiệm vụ Sao đỏ'
        indexes = [
            models.Index(fields=['student', 'status'], name='idx_rs_student_status'),
            models.Index(fields=['status', 'start_date', 'end_date'], name='idx_rs_status_dates'),
            models.Index(fields=['scope_type'], name='idx_rs_scope_type'),
        ]

    def __str__(self):
        user_name = self.user.full_name or self.user.username
        return f"Sao đỏ: {user_name} - {self.get_scope_display_text()} ({self.get_status_display()})"

    def is_active_now(self):
        today = timezone.now().date()
        if self.status != self.STATUS_ACTIVE:
            return False
        if self.start_date and self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True

    def can_cover_class(self, school_class):
        if not self.is_active_now():
            return False
        if self.scope_type == self.SCOPE_ALL_SCHOOL:
            return True
        if self.scope_type == self.SCOPE_GRADE:
            return school_class.grade == self.assigned_grade
        if self.scope_type == self.SCOPE_CLASS:
            return self.assigned_class_id == school_class.id
        if self.scope_type == self.SCOPE_MULTI_CLASS:
            return self.assigned_classes.filter(id=school_class.id).exists()
        if self.scope_type == self.SCOPE_AREA:
            return True
        return False

    def get_scope_display_text(self):
        if self.scope_type == self.SCOPE_ALL_SCHOOL:
            return "Toàn trường"
        if self.scope_type == self.SCOPE_GRADE:
            return f"Khối {self.assigned_grade}"
        if self.scope_type == self.SCOPE_CLASS:
            return f"Lớp {self.assigned_class.name}" if self.assigned_class else "1 Lớp"
        if self.scope_type == self.SCOPE_MULTI_CLASS:
            names = list(self.assigned_classes.values_list('name', flat=True)[:4])
            return ", ".join(names) if names else "Nhiều lớp"
        if self.scope_type == self.SCOPE_AREA:
            return f"Khu vực: {self.area_name or 'Chưa xác định'}"
        return self.get_scope_type_display()


class RedStarReport(models.Model):
    """
    Báo cáo ghi nhận nền nếp của Đội Sao đỏ.
    QUY TẮC BẮT BUỘC:
    1. Báo cáo của Sao đỏ KHÔNG TỰ ĐỘNG TRỪ ĐIỂM của học sinh hay của lớp.
    2. Báo cáo luôn bắt đầu ở trạng thái Chờ xác minh (PENDING).
    3. Sao đỏ không thể tự xác nhận vi phạm của chính mình tạo ra.
    """
    STATUS_PENDING = 'PENDING'
    STATUS_VERIFIED = 'VERIFIED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_RESOLVED = 'RESOLVED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Chờ xác minh'),
        (STATUS_VERIFIED, 'Đã xác minh'),
        (STATUS_REJECTED, 'Không hợp lệ / Không đủ căn cứ'),
        (STATUS_RESOLVED, 'Đã đóng / Xử lý xong'),
    ]

    report_code = models.CharField(max_length=40, unique=True, verbose_name='Mã báo cáo')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='red_star_reports', verbose_name='Sao đỏ báo cáo')
    assignment = models.ForeignKey(RedStarAssignment, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports', verbose_name='Phân công nhiệm vụ')
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='red_star_reports', verbose_name='Lớp được ghi nhận')
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='red_star_reports', verbose_name='Học sinh vi phạm (nếu xác định)')
    student_name_snapshot = models.CharField(max_length=150, blank=True, verbose_name='Họ tên học sinh')
    incident_type = models.CharField(max_length=255, verbose_name='Loại sự việc / Tên nội quy')
    rule = models.ForeignKey(ConductRule, on_delete=models.SET_NULL, null=True, blank=True, related_name='red_star_reports', verbose_name='Nội quy vi phạm')
    incident_time = models.DateTimeField(default=timezone.now, verbose_name='Thời gian xảy ra')
    location = models.CharField(max_length=150, default='Khuôn viên trường', verbose_name='Địa điểm')
    description = models.TextField(blank=True, verbose_name='Mô tả nội dung sự việc')
    evidence_image = models.ImageField(upload_to=evidence_upload_path, null=True, blank=True, verbose_name='Ảnh minh chứng')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='Trạng thái xử lý')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_red_star_reports', verbose_name='Người xác minh')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm xác minh')
    review_note = models.TextField(blank=True, verbose_name='Ý kiến xử lý')

    violation_record = models.ForeignKey(ViolationRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name='originating_red_star_reports', verbose_name='Bản ghi vi phạm đã chuyển tiếp')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-incident_time']
        verbose_name = 'Báo cáo nền nếp Sao đỏ'
        verbose_name_plural = 'Danh sách báo cáo nền nếp Sao đỏ'
        indexes = [
            models.Index(fields=['status', '-incident_time'], name='idx_rsr_status_time'),
            models.Index(fields=['school_class', 'status'], name='idx_rsr_class_status'),
            models.Index(fields=['status'], name='idx_rsr_status'),
        ]

    def __str__(self):
        target = self.student_name_snapshot or f"Lớp {self.school_class.name}"
        return f"[{self.report_code}] {target} - {self.incident_type} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.report_code:
            now_str = timezone.now().strftime('%Y%m%d%H%M')
            short_id = uuid.uuid4().hex[:4].upper()
            self.report_code = f"SD-{now_str}-{short_id}"
        if self.student and not self.student_name_snapshot:
            self.student_name_snapshot = self.student.full_name
        elif not self.student and not self.student_name_snapshot:
            self.student_name_snapshot = f"Tập thể {self.school_class.name}"
        super().save(*args, **kwargs)




class StudentFeedback(models.Model):
    """
    Module Phản hồi học sinh dành cho Giáo viên chủ nhiệm (GVCN) và Giáo viên bộ môn (GVBM).
    QUY TẮC NGHIỆP VỤ BẮT BUỘC:
    1. Phản hồi KHÔNG PHẢI là bản ghi vi phạm kỷ luật.
    2. Phản hồi TUYỆT ĐỐI KHÔNG TỰ ĐỘNG TRỪ ĐIỂM thi đua của học sinh hoặc của lớp.
    3. Trạng thái phản hồi: Đã gửi (SENT) -> Đã xem (SEEN) -> Đang xử lý (PROCESSING) -> Đã giải quyết (RESOLVED).
    4. Trạng thái 'Đã xem' chỉ được cập nhật khi người nhận thực sự mở xem phản hồi.
    5. Không tự động xóa phản hồi khi chuyển kỳ / năm học.
    """
    TYPE_ACADEMIC = 'ACADEMIC'
    TYPE_ATTITUDE = 'ATTITUDE'
    TYPE_DISCIPLINE = 'DISCIPLINE'
    TYPE_ATTENDANCE = 'ATTENDANCE'
    TYPE_PROGRESS = 'PROGRESS'
    TYPE_IMPROVEMENT = 'IMPROVEMENT'
    TYPE_COOPERATION = 'COOPERATION'
    TYPE_OTHER = 'OTHER'

    FEEDBACK_TYPE_CHOICES = [
        (TYPE_ACADEMIC, 'Kết quả học tập'),
        (TYPE_ATTITUDE, 'Thái độ và tinh thần học tập'),
        (TYPE_DISCIPLINE, 'Nền nếp và ý thức thực hiện nội quy'),
        (TYPE_ATTENDANCE, 'Chuyên cần'),
        (TYPE_PROGRESS, 'Sự tiến bộ của học sinh'),
        (TYPE_IMPROVEMENT, 'Điểm cần cải thiện'),
        (TYPE_COOPERATION, 'Đề xuất phối hợp hỗ trợ học sinh'),
        (TYPE_OTHER, 'Nội dung khác'),
    ]

    PRIORITY_NORMAL = 'NORMAL'
    PRIORITY_ATTENTION = 'ATTENTION'
    PRIORITY_URGENT = 'URGENT'

    PRIORITY_CHOICES = [
        (PRIORITY_NORMAL, 'Thông thường'),
        (PRIORITY_ATTENTION, 'Cần quan tâm'),
        (PRIORITY_URGENT, 'Khẩn cấp / Đặc biệt'),
    ]

    SCOPE_HOMEROOM_AND_TEACHERS = 'HOMEROOM_AND_TEACHERS'
    SCOPE_HOMEROOM_ONLY = 'HOMEROOM_ONLY'
    SCOPE_PARENTS_PUBLIC = 'PARENTS_PUBLIC'

    VISIBILITY_CHOICES = [
        (SCOPE_HOMEROOM_AND_TEACHERS, 'GVCN và các GV giảng dạy'),
        (SCOPE_HOMEROOM_ONLY, 'Chỉ GVCN và BGH'),
        (SCOPE_PARENTS_PUBLIC, 'Chia sẻ tới Phụ huynh & Học sinh'),
    ]

    STATUS_SENT = 'SENT'
    STATUS_SEEN = 'SEEN'
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_RESOLVED = 'RESOLVED'

    STATUS_CHOICES = [
        (STATUS_SENT, 'Đã gửi'),
        (STATUS_SEEN, 'Đã xem'),
        (STATUS_PROCESSING, 'Đang xử lý / Phối hợp'),
        (STATUS_RESOLVED, 'Đã giải quyết / Hoàn thành'),
    ]

    feedback_code = models.CharField(max_length=40, unique=True, verbose_name='Mã phản hồi')
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='feedbacks', verbose_name='Học sinh'
    )
    student_name_snapshot = models.CharField(max_length=150, blank=True, verbose_name='Họ tên học sinh')
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE, related_name='student_feedbacks', verbose_name='Lớp học'
    )
    class_name_snapshot = models.CharField(max_length=100, blank=True, verbose_name='Tên lớp')
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_student_feedbacks', verbose_name='Giáo viên gửi phản hồi'
    )
    teacher_role = models.CharField(max_length=30, default='GVBM', verbose_name='Vai trò người gửi')
    subject = models.CharField(max_length=100, blank=True, verbose_name='Môn học liên quan')

    feedback_type = models.CharField(
        max_length=50, choices=FEEDBACK_TYPE_CHOICES, default=TYPE_ATTITUDE, verbose_name='Loại phản hồi'
    )
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL, verbose_name='Mức độ ưu tiên'
    )
    visibility_scope = models.CharField(
        max_length=50, choices=VISIBILITY_CHOICES, default=SCOPE_HOMEROOM_AND_TEACHERS, verbose_name='Phạm vi chia sẻ'
    )

    content = models.TextField(verbose_name='Nội dung phản hồi')
    strengths = models.TextField(blank=True, verbose_name='Điểm mạnh / Tích cực')
    weaknesses = models.TextField(blank=True, verbose_name='Điểm cần cải thiện')
    cooperation_proposal = models.TextField(blank=True, verbose_name='Đề xuất phối hợp hỗ trợ')

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_SENT, verbose_name='Trạng thái xử lý'
    )
    seen_by = models.ManyToManyField(
        User, blank=True, related_name='seen_student_feedbacks', verbose_name='Người đã mở xem'
    )
    seen_at = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm xem lần đầu')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời điểm tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Thời điểm cập nhật')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Phản hồi học sinh'
        verbose_name_plural = 'Danh sách phản hồi học sinh'
        indexes = [
            models.Index(fields=['student', '-created_at'], name='idx_fb_student_created'),
            models.Index(fields=['school_class', '-created_at'], name='idx_fb_class_created'),
            models.Index(fields=['teacher', '-created_at'], name='idx_fb_teacher_created'),
            models.Index(fields=['status', '-created_at'], name='idx_fb_status_created'),
            models.Index(fields=['feedback_type'], name='idx_fb_type'),
            models.Index(fields=['priority'], name='idx_fb_priority'),
        ]

    def __str__(self):
        return f"[{self.feedback_code}] {self.student_name_snapshot} ({self.class_name_snapshot}) - {self.get_feedback_type_display()}"

    def save(self, *args, **kwargs):
        if not self.feedback_code:
            now_str = timezone.now().strftime('%Y%m%d')
            short_id = uuid.uuid4().hex[:4].upper()
            self.feedback_code = f"PH-{now_str}-{short_id}"
        if self.student and not self.student_name_snapshot:
            self.student_name_snapshot = self.student.full_name
        if self.school_class and not self.class_name_snapshot:
            self.class_name_snapshot = self.school_class.name
        super().save(*args, **kwargs)


class StudentFeedbackReply(models.Model):
    """
    Trao đổi, phản hồi và phối hợp giáo dục giữa GVCN và GVBM hoặc BGH.
    """
    feedback = models.ForeignKey(
        StudentFeedback, on_delete=models.CASCADE, related_name='replies', verbose_name='Phản hồi gốc'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='feedback_replies', verbose_name='Người gửi trao đổi'
    )
    author_role = models.CharField(max_length=50, blank=True, verbose_name='Vai trò người trao đổi')
    content = models.TextField(verbose_name='Nội dung trao đổi')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời điểm trao đổi')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Trao đổi phản hồi'
        verbose_name_plural = 'Danh sách trao đổi phản hồi'

    def __str__(self):
        author_name = self.author.full_name or self.author.username
        return f"Trao đổi bởi {author_name} ({self.author_role}) lúc {self.created_at}"
