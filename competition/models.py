from decimal import Decimal
from django.db import models
from core.models import User, AcademicYear, Semester
from conduct.models import SchoolClass, ViolationRecord


class ScoreCriterion(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='score_criteria', verbose_name='Năm học')
    name = models.CharField(max_length=200, verbose_name='Tên biểu điểm / Quy chế thi đua')
    initial_base_points = models.DecimalField(max_digits=5, decimal_places=2, default=100.00, verbose_name='Điểm khởi đầu mỗi kỳ')
    min_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name='Điểm sàn tối thiểu')
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=150.00, verbose_name='Điểm trần tối đa')
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

    def __str__(self):
        return f"{self.name} ({self.get_period_type_display()})"


class ClassCompetitionScore(models.Model):
    competition_period = models.ForeignKey(CompetitionPeriod, on_delete=models.CASCADE, related_name='class_scores', verbose_name='Kỳ thi đua')
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='competition_scores', verbose_name='Lớp / Chi đoàn')
    base_points = models.DecimalField(max_digits=5, decimal_places=2, default=100.00, verbose_name='Điểm khởi điểm')
    bonus_points = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name='Điểm cộng phong trào Đoàn')
    penalty_points = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name='Điểm trừ vi phạm (đã xác minh)')
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.00, verbose_name='Tổng điểm thi đua')
    
    rank = models.PositiveIntegerField(default=1, verbose_name='Thứ hạng toàn trường')
    rank_in_grade = models.PositiveIntegerField(default=1, verbose_name='Thứ hạng trong khối')
    rank_change = models.IntegerField(default=0, verbose_name='Thay đổi thứ hạng (so với kỳ trước)')
    verified_violations_count = models.PositiveIntegerField(default=0, verbose_name='Số lượt vi phạm đã xác minh')
    
    bonus_notes = models.TextField(blank=True, verbose_name='Chi tiết điểm cộng')
    notes = models.TextField(blank=True, verbose_name='Ghi chú đánh giá')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('competition_period', 'school_class')
        ordering = ['-total_score', 'school_class__name']
        verbose_name = 'Điểm thi đua Chi đoàn'
        verbose_name_plural = 'Bảng điểm thi đua các Chi đoàn'

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
