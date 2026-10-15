from django.db import models
from core.models import User
from conduct.models import SchoolClass, Student


class EarlyWarningRule(models.Model):
    TYPE_STUDENT_LATE = 'STUDENT_LATE_REPEAT'
    TYPE_STUDENT_REPEAT = 'STUDENT_GENERAL_REPEAT'
    TYPE_CLASS_SPIKE = 'CLASS_SPIKE'
    TYPE_CRITICAL = 'CRITICAL_VIOLATION'

    RULE_TYPE_CHOICES = [
        (TYPE_STUDENT_LATE, 'Học sinh đi học muộn lặp lại'),
        (TYPE_STUDENT_REPEAT, 'Học sinh có cùng lỗi vi phạm lặp lại'),
        (TYPE_CLASS_SPIKE, 'Số lượt vi phạm của lớp tăng đột biến'),
        (TYPE_CRITICAL, 'Phát sinh vi phạm nghiêm trọng cần quan tâm đặc biệt'),
    ]

    name = models.CharField(max_length=200, verbose_name='Tên cấu hình cảnh báo')
    rule_type = models.CharField(max_length=30, choices=RULE_TYPE_CHOICES, default=TYPE_STUDENT_LATE, verbose_name='Loại cảnh báo')
    threshold = models.PositiveIntegerField(default=3, verbose_name='Ngưỡng kích hoạt (số lần hoặc %)')
    time_window_days = models.PositiveIntegerField(default=7, verbose_name='Khung thời gian xem xét (số ngày)')
    is_active = models.BooleanField(default=True, verbose_name='Kích hoạt')
    suggested_action = models.TextField(
        blank=True, 
        verbose_name='Gợi ý biện pháp cho GVCN',
        help_text='Gợi ý hành động mang tính sư phạm, tìm hiểu nguyên nhân để hỗ trợ học sinh.'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['rule_type', 'threshold']
        verbose_name = 'Cấu hình quy tắc cảnh báo sớm'
        verbose_name_plural = 'Danh mục quy tắc cảnh báo sớm'

    def __str__(self):
        return f"{self.name} (Ngưỡng: {self.threshold} lần/{self.time_window_days} ngày)"


class EarlyWarningAlert(models.Model):
    SEVERITY_LOW = 'LOW'
    SEVERITY_MEDIUM = 'MEDIUM'
    SEVERITY_HIGH = 'HIGH'
    SEVERITY_URGENT = 'URGENT'

    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Mức độ nhắc nhở nhẹ'),
        (SEVERITY_MEDIUM, 'Mức độ cần lưu ý'),
        (SEVERITY_HIGH, 'Mức độ cảnh báo cao'),
        (SEVERITY_URGENT, 'Khẩn cấp cần phối hợp ngay'),
    ]

    STATUS_NEW = 'NEW'
    STATUS_RECEIVED = 'RECEIVED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_RESOLVED = 'RESOLVED'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Chờ tiếp nhận'),
        (STATUS_RECEIVED, 'GVCN đã tiếp nhận'),
        (STATUS_IN_PROGRESS, 'Đang trao đổi & hỗ trợ'),
        (STATUS_RESOLVED, 'Đã hoàn thành hỗ trợ'),
    ]

    rule = models.ForeignKey(EarlyWarningRule, on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts')
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='early_alerts', verbose_name='Lớp liên quan')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True, related_name='early_alerts', verbose_name='Học sinh liên quan')
    alert_title = models.CharField(max_length=255, verbose_name='Tiêu đề cảnh báo')
    details = models.TextField(verbose_name='Dữ liệu căn cứ (chỉ từ các vi phạm đã xác minh)')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default=SEVERITY_MEDIUM, verbose_name='Mức độ cảnh báo')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW, verbose_name='Trạng thái xử lý')
    homeroom_teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_alerts', verbose_name='GVCN tiếp nhận')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời điểm phát cảnh báo')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm hoàn thành')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Cảnh báo sớm nền nếp'
        verbose_name_plural = 'Danh sách cảnh báo sớm'

    def __str__(self):
        target = self.student.full_name if self.student else f"Lớp {self.school_class.name}"
        return f"[{self.get_severity_display()}] {target}: {self.alert_title}"


class HomeroomIntervention(models.Model):
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'Đang thực hiện theo dõi'),
        ('COMPLETED', 'Đã chuyển biến tốt / Hoàn thành'),
    ]

    alert = models.ForeignKey(EarlyWarningAlert, on_delete=models.CASCADE, related_name='interventions', verbose_name='Cảnh báo liên quan')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conduct_interventions', verbose_name='Giáo viên thực hiện')
    action_taken = models.TextField(verbose_name='Biện pháp đã thực hiện (gặp riêng, trao đổi gia đình, giao bạn hỗ trợ...)')
    outcome = models.TextField(blank=True, verbose_name='Kết quả ghi nhận sau hỗ trợ')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS', verbose_name='Tình trạng chuyển biến')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Nhật ký hỗ trợ học sinh của GVCN'
        verbose_name_plural = 'Nhật ký hỗ trợ học sinh của GVCN'

    def __str__(self):
        return f"Hỗ trợ cho [{self.alert.alert_title}] bởi Thầy/Cô {self.teacher.full_name or self.teacher.username}"
