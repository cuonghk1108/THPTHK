# -*- coding: utf-8 -*-
import sys
import os

MODELS_CODE = '''

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
'''

target_path = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\conduct\models.py'
with open(target_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'class StudentFeedback(' not in content:
    with open(target_path, 'a', encoding='utf-8') as f:
        f.write(MODELS_CODE)
    print("SUCCESS: StudentFeedback models appended to conduct/models.py")
else:
    print("ALREADY EXISTS: StudentFeedback already in conduct/models.py")
