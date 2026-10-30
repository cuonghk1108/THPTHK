from decimal import Decimal
import uuid
from django.db import models
from core.models import User, AcademicYear, Semester
from conduct.models import SchoolClass, ViolationRecord


class ScoreCriterion(models.Model):
    TIE_BREAKER_EQUAL = 'EQUAL_RANK'
    TIE_BREAKER_LESS_VIOLATIONS = 'LESS_VIOLATIONS'
    TIE_BREAKER_NAME = 'CLASS_NAME'

    TIE_BREAKER_CHOICES = [
        (TIE_BREAKER_EQUAL, 'Đồng hạng minh bạch (Equal Rank)'),
        (TIE_BREAKER_LESS_VIOLATIONS, 'Ưu tiên lớp có ít lượt vi phạm hơn'),
        (TIE_BREAKER_NAME, 'Theo bảng chữ cái tên lớp'),
    ]

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='score_criteria', verbose_name='Năm học')
    name = models.CharField(max_length=200, verbose_name='Tên biểu điểm / Quy chế thi đua')
    initial_base_points = models.DecimalField(max_digits=5, decimal_places=2, default=100.00, verbose_name='Điểm khởi đầu mỗi kỳ')
    min_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name='Điểm sàn tối thiểu')
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=150.00, verbose_name='Điểm trần tối đa')
    tie_breaker = models.CharField(max_length=50, choices=TIE_BREAKER_CHOICES, default=TIE_BREAKER_EQUAL, verbose_name='Tiêu chí xử lý đồng điểm')
    is_approved = models.BooleanField(default=True, verbose_name='Đã được BGH phê duyệt')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Người phê duyệt')
    effective_from = models.DateField(verbose_name='Hiệu lực từ ngày')
    effective_to = models.DateField(verbose_name='Hiệu lực đến ngày')
    description = models.TextField(blank=True, verbose_name='Ghi chú quy chế')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-effective_from']
        verbose_name = 'Biểu điểm thi đua'
        verbose_name_plural = 'Danh mục biểu điểm thi đua'

    def __str__(self):
        return f"{self.name} (Khởi điểm: {self.initial_base_points}đ)"


class CompetitionPeriod(models.Model):
    TYPE_WEEK = 'WEEK'
    TYPE_MONTH = 'MONTH'
    TYPE_SEMESTER = 'SEMESTER'
    TYPE_YEAR = 'YEAR'

    PERIOD_TYPES = [
        (TYPE_WEEK, 'Thi đua theo Tuần'),
        (TYPE_MONTH, 'Thi đua theo Tháng'),
        (TYPE_SEMESTER, 'Thi đua theo Học kỳ'),
        (TYPE_YEAR, 'Thi đua cả Năm học'),
    ]

    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES, default=TYPE_WEEK, verbose_name='Loại kỳ thi đua')
    name = models.CharField(max_length=150, verbose_name='Tên kỳ thi đua (VD: Tuần 7 - Học kỳ 1)')
    week_number = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Số thứ tự tuần')
    month_number = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Tháng')
    internal_month_number = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Tháng thi đua nội bộ'
    )
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='competition_periods')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, null=True, blank=True, related_name='competition_periods')
    start_date = models.DateField(verbose_name='Ngày bắt đầu')
    end_date = models.DateField(verbose_name='Ngày kết thúc')
    
    is_locked = models.BooleanField(default=False, verbose_name='Đã chốt sổ thi đua (Khóa chỉnh sửa)')
    locked_at = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm chốt sổ')
    locked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='locked_periods')
    
    is_published = models.BooleanField(default=True, verbose_name='Đã công bố bảng xếp hạng')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Kỳ thi đua'
        verbose_name_plural = 'Danh sách kỳ thi đua'
        indexes = [
            models.Index(fields=['is_locked', '-start_date'], name='idx_period_locked_date'),
            models.Index(fields=['period_type', '-start_date'], name='idx_period_type_date'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['academic_year', 'internal_month_number'],
                condition=models.Q(period_type='MONTH', internal_month_number__isnull=False),
                name='uniq_internal_comp_month'
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_period_type_display()})"

    @property
    def period_code(self):
        if self.period_type == self.TYPE_WEEK:
            return f"TUAN-{self.week_number or self.id}"
        elif self.period_type == self.TYPE_MONTH:
            return f"THANG-{self.month_number or self.id}"
        elif self.period_type == self.TYPE_SEMESTER:
            return f"HK-{self.semester_id or self.id}"
        return f"KY-{self.id}"

    @property
    def semester_week_number(self):
        """Số thứ tự tuần trong học kỳ (HK I: 1..18, HK II: 1..17)"""
        if self.period_type != self.TYPE_WEEK or not self.week_number:
            return None
        if self.semester and self.semester.semester_number == 2:
            return self.week_number - 18 if self.week_number > 18 else self.week_number
        return self.week_number

    @property
    def display_week_label(self):
        """Nhãn tuần trực quan phân định theo học kỳ"""
        if self.period_type != self.TYPE_WEEK:
            return self.name
        if self.semester and self.semester.semester_number == 2:
            sem_w = self.week_number - 18 if (self.week_number and self.week_number > 18) else self.week_number
            return f"Tuần {self.week_number} (Tuần {sem_w} - Học kỳ II)"
        return f"Tuần {self.week_number} (Học kỳ I)"


class ClassCompetitionScore(models.Model):
    competition_period = models.ForeignKey(CompetitionPeriod, on_delete=models.CASCADE, related_name='class_scores', verbose_name='Kỳ thi đua')
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='competition_scores', verbose_name='Lớp / Chi đoàn')
    base_points = models.DecimalField(max_digits=9, decimal_places=2, default=100.00, verbose_name='Điểm khởi điểm')
    bonus_points = models.DecimalField(max_digits=9, decimal_places=2, default=0.00, verbose_name='Điểm cộng phong trào Đoàn')
    legacy_bonus_points = models.DecimalField(
        max_digits=9, decimal_places=2, default=0.00,
        verbose_name='Điểm cộng đã lưu trước khi chuẩn hóa'
    )
    penalty_points = models.DecimalField(max_digits=9, decimal_places=2, default=0.00, verbose_name='Điểm trừ vi phạm (đã xác minh)')
    total_score = models.DecimalField(max_digits=9, decimal_places=2, default=100.00, verbose_name='Tổng điểm thi đua')
    
    rank = models.PositiveIntegerField(default=1, verbose_name='Thứ hạng toàn trường')
    rank_in_grade = models.PositiveIntegerField(default=1, verbose_name='Thứ hạng trong khối')
    rank_change = models.IntegerField(null=True, blank=True, default=None, verbose_name='Thay đổi thứ hạng (so với kỳ trước)')
    verified_violations_count = models.PositiveIntegerField(default=0, verbose_name='Số lượt vi phạm đã xác minh')
    
    bonus_notes = models.TextField(blank=True, verbose_name='Chi tiết điểm cộng')
    notes = models.TextField(blank=True, verbose_name='Ghi chú đánh giá')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('competition_period', 'school_class')
        ordering = ['-total_score', 'school_class__name']
        verbose_name = 'Điểm thi đua Chi đoàn'
        verbose_name_plural = 'Bảng điểm thi đua các Chi đoàn'
        indexes = [
            models.Index(fields=['competition_period', 'rank'], name='idx_score_period_rank'),
            models.Index(fields=['competition_period', 'school_class'], name='idx_score_period_class'),
            models.Index(fields=['competition_period', '-total_score'], name='idx_score_period_score'),
        ]

    def __str__(self):
        return f"{self.school_class.name} - {self.competition_period.name}: {self.total_score}đ (Hạng {self.rank})"

    def calculate_total(self, min_score=Decimal('0.0'), max_score=Decimal('150.0')):
        calculated = self.base_points + self.bonus_points - self.penalty_points
        if calculated < min_score:
            calculated = min_score
        elif calculated > max_score:
            calculated = max_score
        self.total_score = calculated
        return self.total_score


class ScoreAdjustment(models.Model):
    """Auditable one-time point adjustments attached to a specific competition week."""

    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Chờ phê duyệt'),
        (STATUS_APPROVED, 'Đã phê duyệt'),
        (STATUS_REJECTED, 'Từ chối'),
    ]

    idempotency_key = models.UUIDField(null=True, blank=True, unique=True, default=None)
    competition_period = models.ForeignKey(
        CompetitionPeriod, on_delete=models.PROTECT, related_name='adjustments',
        verbose_name='Tuần thi đua'
    )
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.PROTECT, related_name='score_adjustments',
        verbose_name='Lớp'
    )
    amount = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Điểm điều chỉnh (+/-)')
    reason = models.TextField(verbose_name='Lý do điều chỉnh')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_score_adjustments',
        verbose_name='Người ghi nhận'
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_score_adjustments',
        verbose_name='Người phê duyệt'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['competition_period', 'school_class', 'status'], name='idx_adjustment_scope_status'),
        ]
        constraints = [
            models.CheckConstraint(condition=~models.Q(amount=0), name='score_adjustment_nonzero'),
        ]

    def __str__(self):
        return f"{self.school_class.name} {self.amount:+}đ · {self.competition_period.name}"
