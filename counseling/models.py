import uuid
from django.db import models
from core.models import User
from conduct.models import Student


class CounselingRequest(models.Model):
    TOPIC_ACADEMIC = 'ACADEMIC'
    TOPIC_PEER = 'PEER'
    TOPIC_FAMILY = 'FAMILY'
    TOPIC_ADAPTATION = 'ADAPTATION'
    TOPIC_SAFETY = 'SAFETY'
    TOPIC_OTHER = 'OTHER'

    TOPIC_CHOICES = [
        (TOPIC_ACADEMIC, 'Áp lực học tập, thi cử'),
        (TOPIC_PEER, 'Khó khăn trong quan hệ bạn bè'),
        (TOPIC_FAMILY, 'Mâu thuẫn hoặc biến cố gia đình'),
        (TOPIC_ADAPTATION, 'Khó khăn trong hòa nhập trường học'),
        (TOPIC_SAFETY, 'Bị bắt nạt hoặc cảm thấy không an toàn'),
        (TOPIC_OTHER, 'Tâm sự, chia sẻ chủ đề khác'),
    ]

    CHANNEL_IN_PERSON = 'IN_PERSON'
    CHANNEL_MESSAGING = 'MESSAGING'
    CHANNEL_EMAIL = 'EMAIL'
    CHANNEL_PHONE = 'PHONE'

    CHANNEL_CHOICES = [
        (CHANNEL_IN_PERSON, 'Hẹn gặp trực tiếp tại Phòng tư vấn tâm lý trường'),
        (CHANNEL_MESSAGING, 'Phản hồi tin nhắn bảo mật qua hệ thống'),
        (CHANNEL_EMAIL, 'Gửi thư phản hồi qua Email cá nhân'),
        (CHANNEL_PHONE, 'Gọi điện thoại trao đổi (tự nguyện cung cấp)'),
    ]

    STATUS_NEW = 'NEW'
    STATUS_RECEIVED = 'RECEIVED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_SCHEDULED = 'SCHEDULED'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_ESCALATED = 'ESCALATED'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Mới tiếp nhận'),
        (STATUS_RECEIVED, 'Đã tiếp nhận hồ sơ'),
        (STATUS_IN_PROGRESS, 'Đang lắng nghe & hỗ trợ'),
        (STATUS_SCHEDULED, 'Đã hẹn lịch trao đổi'),
        (STATUS_COMPLETED, 'Đã hoàn thành phiên hỗ trợ'),
        (STATUS_ESCALATED, 'Cần phối hợp chuyên môn can thiệp an toàn'),
    ]

    # Unique secret tracking code for anonymous tracking
    tracking_code = models.CharField(max_length=40, unique=True, verbose_name='Mã hồ sơ bảo mật (VD: GSC-2026-X8F9)')
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='counseling_requests', verbose_name='Học sinh (nếu công khai danh tính)')
    
    is_anonymous = models.BooleanField(default=False, verbose_name='Gửi dưới dạng ẩn danh')
    alias_name = models.CharField(max_length=100, blank=True, verbose_name='Bí danh tự chọn')
    
    topic = models.CharField(max_length=30, choices=TOPIC_CHOICES, verbose_name='Chủ đề cần sẻ chia')
    content = models.TextField(verbose_name='Nội dung tâm sự / vấn đề gặp phải')
    
    preferred_channel = models.CharField(max_length=30, choices=CHANNEL_CHOICES, default=CHANNEL_IN_PERSON, verbose_name='Hình thức hỗ trợ mong muốn')
    contact_info = models.CharField(max_length=200, blank=True, verbose_name='Thông tin liên hệ (tự nguyện)')
    preferred_schedule = models.CharField(max_length=200, blank=True, verbose_name='Khung giờ thuận tiện trao đổi')
    
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default=STATUS_NEW, verbose_name='Trạng thái xử lý')
    assigned_counselor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='assigned_counseling_cases', verbose_name='Chuyên viên tâm lý phụ trách'
    )
    scheduled_meeting = models.DateTimeField(null=True, blank=True, verbose_name='Lịch hẹn trao đổi trực tiếp')
    
    # Safety flag
    is_urgent_safety = models.BooleanField(default=False, verbose_name='Cần chú ý an toàn khẩn cấp')
    safety_notes = models.TextField(blank=True, verbose_name='Ghi chú cảnh báo an toàn')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời điểm gửi')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Đề nghị tư vấn tâm lý (Góc sẻ chia)'
        verbose_name_plural = 'Danh sách đề nghị tư vấn tâm lý'

    def __str__(self):
        name_display = self.alias_name if self.is_anonymous else (self.student.full_name if self.student else "Học sinh ẩn danh")
        return f"[{self.tracking_code}] {name_display} - {self.get_topic_display()} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            code_rand = uuid.uuid4().hex[:6].upper()
            self.tracking_code = f"GSC-2026-{code_rand}"
        super().save(*args, **kwargs)


class CounselingPrivateNote(models.Model):
    request = models.ForeignKey(CounselingRequest, on_delete=models.CASCADE, related_name='private_notes', verbose_name='Hồ sơ tư vấn')
    counselor = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Chuyên viên ghi nhận')
    note_content = models.TextField(verbose_name='Ghi chép chuyên môn riêng tư (Tuyệt đối bảo mật)')
    recommendation = models.TextField(blank=True, verbose_name='Đề xuất giải pháp đồng hành')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ghi chú chuyên môn tư vấn'
        verbose_name_plural = 'Các ghi chú chuyên môn tư vấn'

    def __str__(self):
        return f"Ghi chú bởi {self.counselor.username} lúc {self.created_at.strftime('%d/%m/%Y %H:%M')}"
