from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from core.models import AuditLog
from conduct.models import SchoolClass, ViolationRecord
from .models import CompetitionPeriod, ClassCompetitionScore, ScoreCriterion


def get_current_score_criterion(academic_year):
    """Lấy quy chế biểu điểm đang áp dụng cho năm học"""
    criterion = ScoreCriterion.objects.filter(academic_year=academic_year, is_approved=True).first()
    if not criterion:
        # Giá trị mặc định an toàn
        return {
            'initial_base_points': Decimal('100.00'),
            'min_score': Decimal('0.00'),
            'max_score': Decimal('150.00')
        }
    return {
        'initial_base_points': criterion.initial_base_points,
        'min_score': criterion.min_score,
        'max_score': criterion.max_score
    }


@transaction.atomic
def recalculate_period_scores(period):
    """
    Tính toán tự động và xếp hạng thi đua Chi đoàn trong kỳ:
    Công thức: Điểm thi đua = Điểm khởi điểm + Tổng điểm cộng - Tổng điểm trừ (từ các bản ghi ĐÃ XÁC MINH).
    Chỉ tính các vi phạm có trạng thái VERIFIED hoặc ADJUSTED.
    """
    if isinstance(period, (int, str)):
        period = CompetitionPeriod.objects.get(id=period)

    if period.is_locked:
        # Kỳ đã chốt sổ, không tự ý sửa đổi
        return

    criterion = get_current_score_criterion(period.academic_year)
    base_points = criterion['initial_base_points']
    min_score = criterion['min_score']
    max_score = criterion['max_score']

    # Lấy toàn bộ lớp học trong năm học
    classes = SchoolClass.objects.filter(academic_year=period.academic_year)

    # Tìm kỳ thi đua trước đó (để tính rank_change)
    previous_period = CompetitionPeriod.objects.filter(
        academic_year=period.academic_year,
        period_type=period.period_type,
        start_date__lt=period.start_date
    ).order_by('-start_date').first()

    prev_rank_map = {}
    if previous_period:
        for prev_score in ClassCompetitionScore.objects.filter(competition_period=previous_period):
            prev_rank_map[prev_score.school_class_id] = prev_score.rank

    scores_to_update = []
    for cls in classes:
        # Lấy hoặc tạo bản ghi điểm
        score_obj, created = ClassCompetitionScore.objects.get_or_create(
            competition_period=period,
            school_class=cls,
            defaults={'base_points': base_points, 'bonus_points': Decimal('0.00'), 'penalty_points': Decimal('0.00')}
        )

        # Tính tổng điểm trừ từ các vi phạm đã xác minh trong khoảng thời gian của kỳ
        verified_violations = ViolationRecord.objects.filter(
            school_class=cls,
            occurred_at__date__gte=period.start_date,
            occurred_at__date__lte=period.end_date,
            status__in=[ViolationRecord.STATUS_VERIFIED, ViolationRecord.STATUS_ADJUSTED]
        )

        total_penalty = verified_violations.aggregate(total=Sum('points_deducted'))['total'] or Decimal('0.00')
        violations_count = verified_violations.count()

        score_obj.base_points = base_points
        score_obj.penalty_points = total_penalty
        score_obj.verified_violations_count = violations_count
        score_obj.calculate_total(min_score=min_score, max_score=max_score)
        score_obj.save()
        scores_to_update.append(score_obj)

    # Xếp hạng toàn trường (Rank 1 -> N)
    scores_to_update.sort(key=lambda x: (-x.total_score, x.school_class.name))
    for idx, sc in enumerate(scores_to_update, start=1):
        sc.rank = idx
        # Tính biến động thứ hạng
        if sc.school_class_id in prev_rank_map:
            prev_r = prev_rank_map[sc.school_class_id]
            # Nếu kỳ trước hạng 5, kỳ này hạng 3 -> rank_change = +2 (tiến bộ)
            sc.rank_change = prev_r - sc.rank
        else:
            sc.rank_change = 0

    # Xếp hạng theo khối (10, 11, 12)
    for grade in [10, 11, 12]:
        grade_scores = [s for s in scores_to_update if s.school_class.grade == grade]
        grade_scores.sort(key=lambda x: (-x.total_score, x.school_class.name))
        for g_idx, sc in enumerate(grade_scores, start=1):
            sc.rank_in_grade = g_idx

    # Bulk update
    ClassCompetitionScore.objects.bulk_update(
        scores_to_update, 
        ['base_points', 'penalty_points', 'total_score', 'verified_violations_count', 'rank', 'rank_in_grade', 'rank_change']
    )


def recalculate_score_for_class_at_time(school_class, occurred_at):
    """
    Khi một vi phạm được xác minh hoặc điều chỉnh, tìm các kỳ thi đua chứa thời điểm đó và tính lại.
    """
    event_date = occurred_at.date() if hasattr(occurred_at, 'date') else occurred_at
    periods = CompetitionPeriod.objects.filter(
        academic_year=school_class.academic_year,
        start_date__lte=event_date,
        end_date__gte=event_date,
        is_locked=False
    )
    for p in periods:
        recalculate_period_scores(p)


def lock_competition_period(period_id, user):
    """Chốt kết quả kỳ thi đua, không cho tự động tính lại hoặc sửa đổi"""
    period = CompetitionPeriod.objects.get(id=period_id)
    recalculate_period_scores(period)  # Tính toán lần cuối trước khi chốt
    period.is_locked = True
    period.locked_at = timezone.now()
    period.locked_by = user
    period.save()

    AuditLog.objects.create(
        user=user,
        action='LOCK',
        resource_type='SCORE',
        resource_id=str(period.id),
        details=f"Chốt sổ kỳ thi đua [{period.name}]"
    )
    return period


def unlock_competition_period(period_id, user):
    """Mở lại kỳ thi đua (chỉ BGH hoặc Admin có quyền)"""
    period = CompetitionPeriod.objects.get(id=period_id)
    period.is_locked = False
    period.save()

    AuditLog.objects.create(
        user=user,
        action='UNLOCK',
        resource_type='SCORE',
        resource_id=str(period.id),
        details=f"Mở khóa chỉnh sửa kỳ thi đua [{period.name}]"
    )
    recalculate_period_scores(period)
    return period
