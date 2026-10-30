import logging
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.cache import cache
from core.cache_utils import get_cache_version

from core.models import AuditLog, AcademicYear, Semester
from conduct.models import natural_class_sort_key, SchoolClass, ViolationRecord
from .calendar import (
    DEFAULT_ACADEMIC_YEAR, DEFAULT_YEAR_START, DEFAULT_YEAR_END,
    DEFAULT_WEEK_COUNT, SEMESTER_WEEK_RANGES, COMPETITION_MONTH_WEEK_RANGES,
    internal_month_number_for_week, weeks_for_internal_month,
)
from .models import CompetitionPeriod, ClassCompetitionScore, ScoreCriterion, ScoreAdjustment

logger = logging.getLogger(__name__)


def _as_local_date(value):
    if isinstance(value, date) and not hasattr(value, 'hour'):
        return value
    if hasattr(value, 'tzinfo') and timezone.is_aware(value):
        return timezone.localtime(value).date()
    return value.date() if hasattr(value, 'date') else value


def get_current_score_criterion(academic_year):
    criterion = ScoreCriterion.objects.filter(
        academic_year=academic_year, is_approved=True
    ).order_by('-effective_from', '-id').first()
    if not criterion:
        # 100 is the existing school rule and the model's current default.
        return {
            'initial_base_points': Decimal('100.00'),
            'min_score': Decimal('0.00'),
            'max_score': Decimal('150.00'),
            'tie_breaker': ScoreCriterion.TIE_BREAKER_EQUAL,
        }
    return {
        'initial_base_points': criterion.initial_base_points,
        'min_score': criterion.min_score,
        'max_score': criterion.max_score,
        'tie_breaker': criterion.tie_breaker,
    }


def assign_ranks(scores, tie_breaker=ScoreCriterion.TIE_BREAKER_EQUAL):
    if not scores:
        return
    scores.sort(key=lambda item: (-item.total_score, natural_class_sort_key(item.school_class)))
    for index, score in enumerate(scores):
        if index == 0:
            score.rank = 1
            continue
        previous = scores[index - 1]
        same_result = score.total_score == previous.total_score
        if tie_breaker == ScoreCriterion.TIE_BREAKER_LESS_VIOLATIONS:
            same_result = same_result and score.verified_violations_count == previous.verified_violations_count
        score.rank = previous.rank if tie_breaker != ScoreCriterion.TIE_BREAKER_NAME and same_result else index + 1


def assign_grade_ranks(scores, tie_breaker=ScoreCriterion.TIE_BREAKER_EQUAL):
    for grade in (10, 11, 12):
        grade_scores = [score for score in scores if score.school_class.grade == grade]
        if not grade_scores:
            continue
        grade_scores.sort(key=lambda item: (-item.total_score, natural_class_sort_key(item.school_class)))
        for index, score in enumerate(grade_scores):
            if index == 0:
                score.rank_in_grade = 1
                continue
            previous = grade_scores[index - 1]
            same_result = score.total_score == previous.total_score
            if tie_breaker == ScoreCriterion.TIE_BREAKER_LESS_VIOLATIONS:
                same_result = same_result and score.verified_violations_count == previous.verified_violations_count
            score.rank_in_grade = previous.rank_in_grade if tie_breaker != ScoreCriterion.TIE_BREAKER_NAME and same_result else index + 1


def _month_map_is_complete(academic_year):
    weeks = list(CompetitionPeriod.objects.filter(
        academic_year=academic_year,
        period_type=CompetitionPeriod.TYPE_WEEK,
    ).order_by('week_number', 'id'))
    if len(weeks) != DEFAULT_WEEK_COUNT or [week.week_number for week in weeks] != list(range(1, DEFAULT_WEEK_COUNT + 1)):
        return False
    if any(week.start_date <= previous.end_date for previous, week in zip(weeks, weeks[1:])):
        return False
    return all(
        week.internal_month_number == internal_month_number_for_week(week.week_number)
        for week in weeks
    )


def _semester_map_is_complete(academic_year):
    weeks = list(CompetitionPeriod.objects.filter(
        academic_year=academic_year,
        period_type=CompetitionPeriod.TYPE_WEEK,
    ).select_related('semester').order_by('week_number', 'id'))
    if len(weeks) != DEFAULT_WEEK_COUNT or [week.week_number for week in weeks] != list(range(1, DEFAULT_WEEK_COUNT + 1)):
        return False
    if any(week.start_date <= previous.end_date for previous, week in zip(weeks, weeks[1:])):
        return False
    return all(
        week.semester_id
        and week.semester.academic_year_id == academic_year.id
        and week.semester.semester_number == (1 if week.week_number <= 18 else 2)
        for week in weeks
    )


def _period_weeks(period):
    weeks = CompetitionPeriod.objects.filter(
        academic_year=period.academic_year,
        period_type=CompetitionPeriod.TYPE_WEEK,
    )
    if period.period_type == CompetitionPeriod.TYPE_MONTH:
        if not period.internal_month_number:
            return CompetitionPeriod.objects.none()
        weeks = weeks.filter(internal_month_number=period.internal_month_number)
    elif period.period_type == CompetitionPeriod.TYPE_SEMESTER:
        if not period.semester_id:
            return CompetitionPeriod.objects.none()
        weeks = weeks.filter(semester_id=period.semester_id)
    elif period.period_type != CompetitionPeriod.TYPE_YEAR:
        return CompetitionPeriod.objects.none()
    return weeks.order_by('start_date', 'week_number')


def _expected_week_numbers(period):
    configured = set(_period_weeks(period).values_list('week_number', flat=True))
    if period.period_type == CompetitionPeriod.TYPE_MONTH and period.internal_month_number:
        if _month_map_is_complete(period.academic_year):
            return configured
        week_range = weeks_for_internal_month(period.internal_month_number)
        return set(range(week_range[0], week_range[1] + 1)) if week_range else set()
    if period.period_type == CompetitionPeriod.TYPE_SEMESTER and period.semester_id:
        if _semester_map_is_complete(period.academic_year):
            return configured
        week_range = SEMESTER_WEEK_RANGES.get(period.semester.semester_number)
        return set(range(week_range[0], week_range[1] + 1)) if week_range else set()
    if period.period_type == CompetitionPeriod.TYPE_YEAR:
        return set(range(1, DEFAULT_WEEK_COUNT + 1))
    if period.period_type == CompetitionPeriod.TYPE_WEEK and period.week_number:
        return {period.week_number}
    return set()


def get_period_status(period, today=None):
    today = today or timezone.localdate()
    cache_attr = f"_status_cache_{today}"
    if hasattr(period, cache_attr):
        return getattr(period, cache_attr)

    cache_key = None
    if getattr(period, 'pk', None):
        cache_key = f"comp_period_status_v{get_cache_version()}_{period.pk}_{today}_{getattr(period, 'is_locked', False)}"
        cached = cache.get(cache_key)
        if cached is not None:
            setattr(period, cache_attr, cached)
            return cached

    if period.is_locked:
        code = 'LOCKED'
    elif today < period.start_date:
        code = 'NOT_STARTED'
    elif today <= period.end_date:
        code = 'TEMPORARY'
    else:
        code = 'WAITING_LOCK'

    configured = list(_period_weeks(period)) if period.period_type != CompetitionPeriod.TYPE_WEEK else [period]
    expected = _expected_week_numbers(period)
    configured_numbers = {week.week_number for week in configured if week.week_number}
    locked_numbers = {week.week_number for week in configured if week.is_locked and week.week_number}
    if period.period_type == CompetitionPeriod.TYPE_WEEK:
        expected_semester_number = 1 if period.week_number and period.week_number <= 18 else 2
        calendar_review = (
            not period.week_number
            or CompetitionPeriod.objects.filter(
                academic_year=period.academic_year,
                period_type=CompetitionPeriod.TYPE_WEEK,
                week_number=period.week_number,
            ).exclude(pk=period.pk).exists()
            or period.internal_month_number != internal_month_number_for_week(period.week_number)
            or not period.semester_id
            or period.semester.academic_year_id != period.academic_year_id
            or period.semester.semester_number != expected_semester_number
            or CompetitionPeriod.objects.filter(
                academic_year=period.academic_year,
                period_type=CompetitionPeriod.TYPE_WEEK,
                start_date__lte=period.end_date,
                end_date__gte=period.start_date,
            ).exclude(pk=period.pk).exists()
        )
    elif period.period_type == CompetitionPeriod.TYPE_MONTH:
        calendar_review = period.internal_month_number is None or not _month_map_is_complete(period.academic_year)
    elif period.period_type == CompetitionPeriod.TYPE_SEMESTER:
        calendar_review = not _semester_map_is_complete(period.academic_year)
    elif period.period_type == CompetitionPeriod.TYPE_YEAR:
        calendar_review = not (
            _month_map_is_complete(period.academic_year)
            and _semester_map_is_complete(period.academic_year)
        )
    else:
        calendar_review = True
    legacy_bonus_query = ClassCompetitionScore.objects.filter(legacy_bonus_points__gt=0)
    if period.period_type == CompetitionPeriod.TYPE_WEEK:
        legacy_bonus_query = legacy_bonus_query.filter(competition_period=period)
    else:
        legacy_bonus_query = legacy_bonus_query.filter(competition_period__in=_period_weeks(period))
    res = {
        'code': code,
        'calendar_review': calendar_review,
        'display': {
            'NOT_STARTED': 'Chưa diễn ra',
            'TEMPORARY': 'Tạm tính',
            'WAITING_LOCK': 'Chờ chốt',
            'LOCKED': 'Đã chốt',
        }[code],
        'expected_week_numbers': sorted(expected),
        'configured_week_numbers': sorted(configured_numbers),
        'locked_week_numbers': sorted(locked_numbers),
        'expected_weeks': len(expected),
        'configured_weeks': len(configured_numbers),
        'included_weeks': int(period.is_locked) if period.period_type == CompetitionPeriod.TYPE_WEEK else len(locked_numbers),
        'complete_schedule': bool(expected) and expected.issubset(configured_numbers),
        'complete_result': bool(expected) and expected.issubset(locked_numbers),
        'requires_review': calendar_review or legacy_bonus_query.exists(),
    }
    setattr(period, cache_attr, res)
    if cache_key:
        cache.set(cache_key, res, timeout=60)
    return res


def get_valid_aggregate_class_ids(period):
    if period.period_type == CompetitionPeriod.TYPE_WEEK:
        return None
    weeks = list(_period_weeks(period).filter(is_locked=True))
    if not weeks:
        return set()
    week_ids = [week.id for week in weeks]
    counts = dict(ClassCompetitionScore.objects.filter(
        competition_period_id__in=week_ids,
    ).values('school_class_id').annotate(week_count=Count('id')).values_list('school_class_id', 'week_count'))
    return {class_id for class_id, count in counts.items() if count == len(week_ids)}


@transaction.atomic
def recalculate_period_scores(period, force=False):
    """Recalculate weekly source scores or sum already-closed weekly results."""
    if isinstance(period, (int, str)):
        period = CompetitionPeriod.objects.get(pk=period)
    period = CompetitionPeriod.objects.select_for_update().get(pk=period.pk)
    if period.period_type == CompetitionPeriod.TYPE_WEEK and period.week_number and not period.internal_month_number:
        from competition.calendar import internal_month_number_for_week
        period.internal_month_number = internal_month_number_for_week(period.week_number)
        period.save(update_fields=['internal_month_number'])

    if period.is_locked and not force:
        return
    if period.period_type != CompetitionPeriod.TYPE_WEEK and get_period_status(period)['calendar_review'] and not force:
        return

    criterion = get_current_score_criterion(period.academic_year)
    tie_breaker = criterion['tie_breaker']
    classes = list(SchoolClass.objects.filter(
        academic_year=period.academic_year
    ).order_by('grade', 'class_order', 'name'))
    classes_by_id = {item.id: item for item in classes}
    previous_periods = CompetitionPeriod.objects.filter(
        academic_year=period.academic_year,
        period_type=period.period_type,
        is_locked=True,
        is_published=True,
        start_date__lt=period.start_date,
    ).exclude(pk=period.pk)
    if period.period_type == CompetitionPeriod.TYPE_MONTH:
        previous_periods = previous_periods.filter(internal_month_number__isnull=False)
    previous_period = previous_periods.order_by('-start_date').first()
    previous_ranks = dict(
        ClassCompetitionScore.objects.filter(competition_period=previous_period)
        .values_list('school_class_id', 'rank')
    ) if previous_period else {}

    if period.period_type == CompetitionPeriod.TYPE_WEEK:
        overlapping_ranges = CompetitionPeriod.objects.filter(
            academic_year=period.academic_year,
            period_type=CompetitionPeriod.TYPE_WEEK,
            start_date__lte=period.end_date,
            end_date__gte=period.start_date,
        ).exclude(pk=period.pk).values_list('start_date', 'end_date')
        ambiguous_dates = Q(pk__in=[])
        for start_date, end_date in overlapping_ranges:
            ambiguous_dates |= Q(occurred_at__date__gte=start_date, occurred_at__date__lte=end_date)
        violations = {
            row['school_class_id']: row
            for row in ViolationRecord.objects.filter(
                school_class__academic_year=period.academic_year,
                occurred_at__date__gte=period.start_date,
                occurred_at__date__lte=period.end_date,
                status__in=(ViolationRecord.STATUS_VERIFIED, ViolationRecord.STATUS_ADJUSTED),
            ).exclude(ambiguous_dates).values('school_class_id').annotate(
                total_penalty=Sum('points_deducted'),
                violations_count=Count('id'),
            )
        }
        adjustments = {}
        for row in ScoreAdjustment.objects.filter(
            competition_period=period,
            status=ScoreAdjustment.STATUS_APPROVED,
        ).values('school_class_id', 'amount'):
            totals = adjustments.setdefault(row['school_class_id'], {
                'bonus': Decimal('0.00'), 'penalty': Decimal('0.00')
            })
            if row['amount'] > 0:
                totals['bonus'] += row['amount']
            else:
                totals['penalty'] += abs(row['amount'])

        scores = {
            score.school_class_id: score
            for score in ClassCompetitionScore.objects.filter(competition_period=period).select_related('school_class')
        }
        for school_class in classes:
            if school_class.id not in scores:
                scores[school_class.id] = ClassCompetitionScore.objects.create(
                    competition_period=period,
                    school_class=school_class,
                    base_points=criterion['initial_base_points'],
                    total_score=criterion['initial_base_points'],
                )

        scores_to_update = [score for score in scores.values() if score.school_class_id in classes_by_id]
        for score in scores_to_update:
            score.school_class = classes_by_id[score.school_class_id]
        for score in scores_to_update:
            violation = violations.get(score.school_class_id, {})
            adjustment = adjustments.get(score.school_class_id, {'bonus': Decimal('0.00'), 'penalty': Decimal('0.00')})
            score.base_points = criterion['initial_base_points']
            score.bonus_points = Decimal(str(score.legacy_bonus_points or 0)) + adjustment['bonus']
            score.penalty_points = (violation.get('total_penalty') or Decimal('0.00')) + adjustment['penalty']
            score.verified_violations_count = violation.get('violations_count', 0)
            score.calculate_total(min_score=criterion['min_score'], max_score=criterion['max_score'])
    else:
        # Kỳ tổng hợp (Tháng, Học kỳ, Năm học):
        # Lấy tất cả các tuần đã khóa (is_locked=True) HOẶC các tuần đã/đang diễn ra (start_date <= today)
        today = timezone.localdate()
        closed_weeks = list(
            _period_weeks(period).filter(Q(is_locked=True) | Q(start_date__lte=today))
        )
        if not closed_weeks:
            return
        week_ids = [week.id for week in closed_weeks]
        source_scores = list(ClassCompetitionScore.objects.filter(
            competition_period_id__in=week_ids,
            school_class__in=classes,
        ).select_related('school_class'))
        by_class = {}
        for score in source_scores:
            by_class.setdefault(score.school_class_id, {})[score.competition_period_id] = score
        existing = {
            score.school_class_id: score
            for score in ClassCompetitionScore.objects.filter(competition_period=period).select_related('school_class')
        }
        scores_to_update = []
        for class_id, week_scores in by_class.items():
            rows = [week_scores[w_id] for w_id in week_ids if w_id in week_scores]
            if not rows:
                continue
            aggregate = existing.get(class_id) or ClassCompetitionScore(
                competition_period=period,
                school_class=classes_by_id[class_id],
            )
            aggregate.school_class = classes_by_id[class_id]
            aggregate.base_points = sum((row.base_points for row in rows), Decimal('0.00'))
            aggregate.bonus_points = sum((row.bonus_points for row in rows), Decimal('0.00'))
            aggregate.penalty_points = sum((row.penalty_points for row in rows), Decimal('0.00'))
            aggregate.verified_violations_count = sum(row.verified_violations_count for row in rows)
            aggregate.total_score = sum((row.total_score for row in rows), Decimal('0.00'))
            aggregate.bonus_notes = '\n'.join(row.bonus_notes for row in rows if row.bonus_notes)
            scores_to_update.append(aggregate)
        new_scores = [score for score in scores_to_update if score.pk is None]
        if new_scores:
            ClassCompetitionScore.objects.bulk_create(new_scores, batch_size=500)

    assign_ranks(scores_to_update, tie_breaker)
    assign_grade_ranks(scores_to_update, tie_breaker)
    for score in scores_to_update:
        previous_rank = previous_ranks.get(score.school_class_id)
        score.rank_change = previous_rank - score.rank if previous_rank is not None else None
    ClassCompetitionScore.objects.bulk_update(
        scores_to_update,
        ['base_points', 'bonus_points', 'legacy_bonus_points', 'penalty_points', 'total_score',
         'verified_violations_count', 'bonus_notes', 'rank', 'rank_in_grade', 'rank_change'],
    )


def recalculate_score_for_class_at_time(school_class, occurred_at):
    """Refresh the containing open week and any open aggregate period."""
    try:
        event_date = _as_local_date(occurred_at)
        week = get_or_create_week_for_date(event_date, school_class.academic_year)
        if not week or week.is_locked:
            return
        recalculate_period_scores(week, force=True)
        parent_filter = Q(pk__in=[])
        if week.internal_month_number:
            parent_filter |= Q(period_type=CompetitionPeriod.TYPE_MONTH, internal_month_number=week.internal_month_number)
        if week.semester_id:
            parent_filter |= Q(period_type=CompetitionPeriod.TYPE_SEMESTER, semester_id=week.semester_id)
        parent_filter |= Q(period_type=CompetitionPeriod.TYPE_YEAR)

        parents = CompetitionPeriod.objects.filter(
            parent_filter,
            academic_year=school_class.academic_year,
            is_locked=False,
        )
        for parent in parents:
            recalculate_period_scores(parent, force=True)
    except Exception:
        logger.exception('Không thể tính lại điểm lớp %s tại thời điểm %s', school_class.name, occurred_at)


def get_current_competition_period(academic_year=None, period_type=CompetitionPeriod.TYPE_WEEK):
    today = timezone.localdate()
    periods = CompetitionPeriod.objects.filter(period_type=period_type)
    if period_type == CompetitionPeriod.TYPE_MONTH:
        periods = periods.filter(internal_month_number__isnull=False)
    if academic_year:
        periods = periods.filter(academic_year=academic_year)
    current = periods.filter(start_date__lte=today, end_date__gte=today).order_by('start_date').first()
    if current:
        return current
    upcoming = periods.filter(start_date__gt=today).order_by('start_date').first()
    if upcoming:
        return upcoming
    return periods.order_by('-end_date', '-start_date').first()


def get_competition_class_scope(user, academic_year=None):
    """Return the classes a role may view, or None for school-wide authority."""
    classes = SchoolClass.objects.all()
    if academic_year:
        classes = classes.filter(academic_year=academic_year)
    else:
        classes = classes.filter(is_active=True)
    if not user.is_active or not getattr(user, 'is_approved', False):
        return classes.none()
    if user.is_admin or user.is_bgh or user.is_doan_truong:
        return classes
    if user.is_student:
        student = getattr(user, 'student_profile', None)
        if not student:
            return classes.none()
        return classes.filter(pk=student.school_class_id)
    if user.is_gvcn:
        from conduct.models import natural_class_sort_key, HomeroomAssignment
        today = timezone.localdate()
        active_assignments = HomeroomAssignment.objects.filter(
            teacher=user, is_active=True, start_date__lte=today,
        ).filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
        return classes.filter(
            Q(homeroom_teacher=user) | Q(pk__in=active_assignments.values('school_class_id'))
        ).distinct()
    if user.is_gvbm:
        from conduct.models import natural_class_sort_key, TeacherClassAssignment
        today = timezone.localdate()
        assignments = TeacherClassAssignment.objects.filter(
            teacher=user, is_active=True, start_date__lte=today,
        ).filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
        return classes.filter(pk__in=assignments.values('school_class_id'))
    if user.is_sao_do:
        from conduct.models import natural_class_sort_key, RedStarAssignment
        today = timezone.localdate()
        assignments = RedStarAssignment.objects.filter(
            user=user,
            status=RedStarAssignment.STATUS_ACTIVE,
            start_date__lte=today,
        ).filter(Q(end_date__isnull=True) | Q(end_date__gte=today)).prefetch_related('assigned_classes')
        allowed_ids = set()
        all_school = False
        for assignment in assignments:
            if assignment.scope_type in [RedStarAssignment.SCOPE_ALL_SCHOOL, RedStarAssignment.SCOPE_AREA]:
                if assignment.scope_type == RedStarAssignment.SCOPE_ALL_SCHOOL:
                    all_school = True
            elif assignment.scope_type == RedStarAssignment.SCOPE_GRADE:
                allowed_ids.update(classes.filter(grade=assignment.assigned_grade).values_list('id', flat=True))
            elif assignment.scope_type == RedStarAssignment.SCOPE_CLASS and assignment.assigned_class_id:
                allowed_ids.add(assignment.assigned_class_id)
            elif assignment.scope_type == RedStarAssignment.SCOPE_MULTI_CLASS:
                allowed_ids.update(assignment.assigned_classes.values_list('id', flat=True))
        return classes if all_school else classes.filter(pk__in=allowed_ids)
    return classes.none()


def get_or_create_week_for_date(occurred_at, academic_year=None):
    """Return only the saved week containing a date; never guess a nearby week."""
    event_date = _as_local_date(occurred_at)
    if academic_year is None:
        academic_year = AcademicYear.objects.filter(is_current=True).first()
    if academic_year is None:
        return None
    matches = list(CompetitionPeriod.objects.filter(
        academic_year=academic_year,
        period_type=CompetitionPeriod.TYPE_WEEK,
        start_date__lte=event_date,
        end_date__gte=event_date,
    ).order_by('start_date', 'id')[:2])
    return matches[0] if len(matches) == 1 else None


def init_standard_35_weeks_schedule(academic_year=None, force_recalculate=False):
    """Create missing periods without rewriting dates or locked calendar rows."""
    if academic_year is None:
        academic_year = AcademicYear.objects.filter(is_current=True).first()
        if academic_year is None:
            academic_year, _ = AcademicYear.objects.get_or_create(
                name=DEFAULT_ACADEMIC_YEAR,
                defaults={
                    'start_date': DEFAULT_YEAR_START,
                    'end_date': DEFAULT_YEAR_END,
                    'is_current': True,
                },
            )

    issues = []
    week_one_rows = list(CompetitionPeriod.objects.filter(
        academic_year=academic_year,
        period_type=CompetitionPeriod.TYPE_WEEK,
        week_number=1,
    ).order_by('id')[:2])
    if len(week_one_rows) > 1:
        issues.append('Tuần 1 có nhiều bản ghi; cần Admin rà soát trước khi tạo lịch.')
    calendar_start = week_one_rows[0].start_date if len(week_one_rows) == 1 else DEFAULT_YEAR_START
    year_end = calendar_start + timedelta(weeks=DEFAULT_WEEK_COUNT) - timedelta(days=1)
    semester_ranges = {
        1: (calendar_start, calendar_start + timedelta(weeks=18) - timedelta(days=1)),
        2: (calendar_start + timedelta(weeks=18), year_end),
    }

    semesters = {}
    for number, (start, end) in semester_ranges.items():
        semester, _ = Semester.objects.get_or_create(
            academic_year=academic_year,
            semester_number=number,
            defaults={
                'name': 'Học kỳ I' if number == 1 else 'Học kỳ II',
                'start_date': start,
                'end_date': end,
                'is_current': start <= timezone.localdate() <= end,
            },
        )
        semesters[number] = semester

    weeks = {}
    all_periods = []
    for week_number in range(1, DEFAULT_WEEK_COUNT + 1):
        rows = list(CompetitionPeriod.objects.filter(
            academic_year=academic_year,
            period_type=CompetitionPeriod.TYPE_WEEK,
            week_number=week_number,
        ).order_by('id')[:2])
        if len(rows) > 1:
            issues.append(f'Tuần {week_number} có nhiều bản ghi; cần Admin rà soát.')
            continue
        start = calendar_start + timedelta(weeks=week_number - 1)
        end = start + timedelta(days=6)
        semester_number = 1 if week_number <= 18 else 2
        internal_month = internal_month_number_for_week(week_number)
        if rows:
            period = rows[0]
            if not period.is_locked:
                fields = []
                if period.internal_month_number is None:
                    period.internal_month_number = internal_month
                    fields.append('internal_month_number')
                if period.semester_id is None:
                    period.semester = semesters[semester_number]
                    fields.append('semester')
                if fields:
                    period.save(update_fields=fields)
            if period.start_date != start or period.end_date != end:
                issues.append(f'Tuần {week_number} có ngày đã điều chỉnh; giữ nguyên ngày đã lưu.')
            if period.is_locked and (period.semester_id is None or period.internal_month_number is None):
                issues.append(f'Tuần {week_number} đã chốt nhưng thiếu liên kết lịch; cần rà soát thủ công.')
        else:
            period = CompetitionPeriod.objects.create(
                academic_year=academic_year,
                period_type=CompetitionPeriod.TYPE_WEEK,
                week_number=week_number,
                internal_month_number=internal_month,
                name=f'Tuần {week_number} - Học kỳ {"I" if semester_number == 1 else "II"} ({academic_year.name})',
                semester=semesters[semester_number],
                start_date=start,
                end_date=end,
                is_published=True,
            )
        weeks[week_number] = period
        all_periods.append(period)

    for month_number, (first_week, last_week) in COMPETITION_MONTH_WEEK_RANGES.items():
        period = CompetitionPeriod.objects.filter(
            academic_year=academic_year,
            period_type=CompetitionPeriod.TYPE_MONTH,
            internal_month_number=month_number,
        ).first()
        if period:
            all_periods.append(period)
            continue
        month_weeks = [weeks.get(number) for number in range(first_week, last_week + 1)]
        if any(week is None for week in month_weeks):
            issues.append(f'Tháng thi đua {month_number} thiếu tuần; kỳ tháng chưa được tạo.')
            continue
        start = min(week.start_date for week in month_weeks)
        end = max(week.end_date for week in month_weeks)
        semester_number = 1 if month_number <= 5 else 2
        period = CompetitionPeriod.objects.create(
            academic_year=academic_year,
            period_type=CompetitionPeriod.TYPE_MONTH,
            month_number=month_number,
            internal_month_number=month_number,
            name=f'Tháng thi đua {month_number} ({academic_year.name})',
            semester=semesters[semester_number],
            start_date=start,
            end_date=end,
            is_published=True,
        )
        all_periods.append(period)

    for number, semester in semesters.items():
        period = CompetitionPeriod.objects.filter(
            academic_year=academic_year,
            period_type=CompetitionPeriod.TYPE_SEMESTER,
            semester=semester,
        ).first()
        if not period:
            period = CompetitionPeriod.objects.create(
                academic_year=academic_year,
                period_type=CompetitionPeriod.TYPE_SEMESTER,
                semester=semester,
                name=f'Thi đua Học kỳ {"I" if number == 1 else "II"} ({academic_year.name})',
                start_date=semester.start_date,
                end_date=semester.end_date,
                is_published=True,
            )
        all_periods.append(period)

    week_rows = list(CompetitionPeriod.objects.filter(
        academic_year=academic_year,
        period_type=CompetitionPeriod.TYPE_WEEK,
    ).order_by('start_date', 'id'))
    unmapped_violations = []
    for violation in ViolationRecord.objects.filter(
        school_class__academic_year=academic_year,
        occurred_at__isnull=False,
    ).only('record_code', 'occurred_at').iterator():
        event_date = _as_local_date(violation.occurred_at)
        matching_weeks = [week for week in week_rows if week.start_date <= event_date <= week.end_date]
        if len(matching_weeks) != 1:
            unmapped_violations.append(violation.record_code)
    if unmapped_violations:
        samples = ', '.join(unmapped_violations[:10])
        issues.append(
            f'{len(unmapped_violations)} báo cáo vi phạm không khớp duy nhất với một tuần đã lưu; '
            f'cần rà soát: {samples}'
        )

    year_period = CompetitionPeriod.objects.filter(
        academic_year=academic_year,
        period_type=CompetitionPeriod.TYPE_YEAR,
    ).first()
    if not year_period:
        year_period = CompetitionPeriod.objects.create(
            academic_year=academic_year,
            period_type=CompetitionPeriod.TYPE_YEAR,
            name=f'Thi đua Cả năm học ({academic_year.name})',
            start_date=semesters[1].start_date,
            end_date=semesters[2].end_date,
            is_published=True,
        )
    all_periods.append(year_period)

    classes = list(SchoolClass.objects.filter(academic_year=academic_year))
    criterion = get_current_score_criterion(academic_year)
    existing_pairs = set(ClassCompetitionScore.objects.filter(
        competition_period__in=list(weeks.values()),
    ).values_list('competition_period_id', 'school_class_id'))
    missing_scores = [
        ClassCompetitionScore(
            competition_period=week,
            school_class=school_class,
            base_points=criterion['initial_base_points'],
            total_score=criterion['initial_base_points'],
        )
        for week in weeks.values()
        for school_class in classes
        if (week.id, school_class.id) not in existing_pairs
    ]
    if missing_scores:
        ClassCompetitionScore.objects.bulk_create(missing_scores, batch_size=500)

    for week in weeks.values():
        if get_period_status(week)['calendar_review']:
            issues.append(f'{week.name} chưa được tính lại vì lịch cần rà soát.')
        else:
            recalculate_period_scores(week, force=force_recalculate)
    for period in all_periods:
        if period.period_type != CompetitionPeriod.TYPE_WEEK:
            if get_period_status(period)['calendar_review']:
                issues.append(f'{period.name} chưa được tổng hợp vì lịch cần rà soát.')
            else:
                recalculate_period_scores(period, force=force_recalculate)

    return {
        'total_weeks': len(weeks),
        'hk1_weeks': sum(1 for number in weeks if number <= 18),
        'hk2_weeks': sum(1 for number in weeks if number >= 19),
        'total_periods': len(all_periods),
        'classes_count': len(classes),
        'scores_initialized': len(missing_scores),
        'configuration_issues': issues,
    }


@transaction.atomic
def lock_competition_period(period_id, user):
    period = CompetitionPeriod.objects.select_for_update().get(pk=period_id)
    today = timezone.localdate()
    if period.is_locked:
        return period
    if period.end_date > today:
        raise ValueError('Chỉ được chốt kỳ sau khi kỳ đã kết thúc.')
    if period.period_type == CompetitionPeriod.TYPE_WEEK:
        if not period.week_number:
            raise ValueError('Chưa thể chốt tuần chưa có số thứ tự hợp lệ.')
        if CompetitionPeriod.objects.filter(
            academic_year=period.academic_year,
            period_type=CompetitionPeriod.TYPE_WEEK,
            week_number=period.week_number,
        ).exclude(pk=period.pk).exists():
            raise ValueError('Chưa thể chốt tuần bị trùng số thứ tự.')
        status = get_period_status(period)
        if status['requires_review']:
            raise ValueError('Chưa thể chốt tuần: cần rà soát liên kết tuần, tháng thi đua và học kỳ.')
        recalculate_period_scores(period, force=True)
    else:
        if period.period_type in (CompetitionPeriod.TYPE_MONTH, CompetitionPeriod.TYPE_YEAR) and not _month_map_is_complete(period.academic_year):
            raise ValueError('Chưa thể chốt kỳ: lịch tháng thi đua cần được rà soát đầy đủ.')
        if period.period_type in (CompetitionPeriod.TYPE_SEMESTER, CompetitionPeriod.TYPE_YEAR) and not _semester_map_is_complete(period.academic_year):
            raise ValueError('Chưa thể chốt kỳ: lịch học kỳ cần được rà soát đầy đủ.')
        expected = _expected_week_numbers(period)
        weeks = list(_period_weeks(period))
        configured = {week.week_number for week in weeks if week.week_number}
        locked = {week.week_number for week in weeks if week.is_locked and week.week_number}
        if not expected or not expected.issubset(configured) or not expected.issubset(locked):
            raise ValueError('Chưa thể chốt kỳ: cần đủ các tuần đã cấu hình và đã chốt.')
        if any(week.end_date > today for week in weeks):
            raise ValueError('Chưa thể chốt kỳ khi còn tuần chưa kết thúc.')
        recalculate_period_scores(period, force=True)

    period.is_locked = True
    period.locked_at = timezone.now()
    period.locked_by = user
    period.save(update_fields=['is_locked', 'locked_at', 'locked_by'])
    AuditLog.objects.create(
        user=user,
        action='LOCK',
        resource_type='SCORE',
        resource_id=str(period.id),
        details=f'Chốt sổ kỳ thi đua [{period.name}] ({period.get_period_type_display()}) bởi {user.full_name or user.username}',
    )
    if period.period_type == CompetitionPeriod.TYPE_WEEK:
        parents = CompetitionPeriod.objects.filter(
            academic_year=period.academic_year,
            period_type__in=(CompetitionPeriod.TYPE_MONTH, CompetitionPeriod.TYPE_SEMESTER, CompetitionPeriod.TYPE_YEAR),
            is_locked=False,
        )
        for parent in parents:
            if period in _period_weeks(parent):
                recalculate_period_scores(parent)
    return period


@transaction.atomic
def unlock_competition_period(period_id, user):
    period = CompetitionPeriod.objects.select_for_update().get(pk=period_id)
    period.is_locked = False
    period.locked_at = None
    period.locked_by = None
    period.save(update_fields=['is_locked', 'locked_at', 'locked_by'])
    AuditLog.objects.create(
        user=user,
        action='UNLOCK',
        resource_type='SCORE',
        resource_id=str(period.id),
        details=f'Mở khóa chỉnh sửa kỳ thi đua [{period.name}] ({period.get_period_type_display()}) bởi {user.full_name or user.username}',
    )
    recalculate_period_scores(period)
    if period.period_type == CompetitionPeriod.TYPE_WEEK:
        for parent in CompetitionPeriod.objects.filter(
            academic_year=period.academic_year,
            period_type__in=(CompetitionPeriod.TYPE_MONTH, CompetitionPeriod.TYPE_SEMESTER, CompetitionPeriod.TYPE_YEAR),
            is_locked=False,
        ):
            if period in _period_weeks(parent):
                recalculate_period_scores(parent)
    return period
