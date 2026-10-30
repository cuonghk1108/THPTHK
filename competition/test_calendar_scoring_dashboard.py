from datetime import date, timedelta
from decimal import Decimal
import uuid

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from competition.calendar import COMPETITION_MONTH_WEEK_RANGES
from competition.models import CompetitionPeriod, ClassCompetitionScore, ScoreAdjustment, ScoreCriterion
from competition.services import (
    get_or_create_week_for_date,
    get_period_status,
    get_valid_aggregate_class_ids,
    init_standard_35_weeks_schedule,
    lock_competition_period,
    recalculate_period_scores,
)
from conduct.models import SchoolClass, Student, ConductRule, ConductRuleCategory, ViolationRecord
from core.models import AcademicYear, Semester, User


class CompetitionCalendarScoringDashboardTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='calendar_admin',
            password='calendar-test-password',
            role=User.ROLE_ADMIN,
            account_status=User.STATUS_APPROVED,
        )
        self.year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=date(2026, 9, 7),
            end_date=date(2027, 5, 9),
            is_current=True,
        )
        self.semester_1 = Semester.objects.create(
            academic_year=self.year,
            semester_number=1,
            name='Học kỳ I',
            start_date=date(2026, 9, 7),
            end_date=date(2027, 1, 10),
        )
        self.semester_2 = Semester.objects.create(
            academic_year=self.year,
            semester_number=2,
            name='Học kỳ II',
            start_date=date(2027, 1, 11),
            end_date=date(2027, 5, 9),
        )
        self.class_10a1 = SchoolClass.objects.create(
            name='10A1', grade=10, academic_year=self.year,
        )
        self.class_10a2 = SchoolClass.objects.create(
            name='10A2', grade=10, academic_year=self.year,
        )
        self.criterion = ScoreCriterion.objects.create(
            academic_year=self.year,
            name='Quy chế thi đua 2026–2027',
            initial_base_points=Decimal('100.00'),
            min_score=Decimal('0.00'),
            max_score=Decimal('150.00'),
            effective_from=date(2026, 9, 7),
            effective_to=date(2027, 5, 9),
            is_approved=True,
        )
        category = ConductRuleCategory.objects.create(name='Nề nếp')
        self.rule = ConductRule.objects.create(
            category=category,
            code='CAL-01',
            name='Đi học muộn',
            default_points_deducted=Decimal('2.00'),
        )
        self.student_user = User.objects.create_user(
            username='student_10a1',
            password='student-test-password',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED,
        )
        self.student = Student.objects.create(
            user=self.student_user,
            student_code='CAL-HS-001',
            full_name='Học sinh 10A1',
            date_of_birth=date(2010, 1, 1),
            school_class=self.class_10a1,
        )
        self.schedule = init_standard_35_weeks_schedule(self.year)

    def period(self, period_type, **filters):
        return CompetitionPeriod.objects.get(
            academic_year=self.year,
            period_type=period_type,
            **filters,
        )

    def test_default_calendar_has_35_monday_to_sunday_weeks_and_ten_internal_months(self):
        weeks = CompetitionPeriod.objects.filter(
            academic_year=self.year,
            period_type=CompetitionPeriod.TYPE_WEEK,
        ).order_by('week_number')
        self.assertEqual(weeks.count(), 35)
        self.assertEqual((weeks.get(week_number=1).start_date, weeks.get(week_number=1).end_date),
                         (date(2026, 9, 7), date(2026, 9, 13)))
        self.assertEqual((weeks.get(week_number=18).start_date, weeks.get(week_number=18).end_date),
                         (date(2027, 1, 4), date(2027, 1, 10)))
        self.assertEqual((weeks.get(week_number=19).start_date, weeks.get(week_number=19).end_date),
                         (date(2027, 1, 11), date(2027, 1, 17)))
        self.assertEqual((weeks.get(week_number=35).start_date, weeks.get(week_number=35).end_date),
                         (date(2027, 5, 3), date(2027, 5, 9)))
        self.assertEqual(weeks.values_list('week_number', flat=True).distinct().count(), 35)
        self.assertEqual(CompetitionPeriod.objects.filter(
            academic_year=self.year,
            period_type=CompetitionPeriod.TYPE_MONTH,
            internal_month_number__isnull=False,
        ).count(), 10)
        for month_number, (first_week, last_week) in COMPETITION_MONTH_WEEK_RANGES.items():
            month = self.period(CompetitionPeriod.TYPE_MONTH, internal_month_number=month_number)
            self.assertEqual(month.start_date, weeks.get(week_number=first_week).start_date)
            self.assertEqual(month.end_date, weeks.get(week_number=last_week).end_date)
        self.assertEqual(self.period(CompetitionPeriod.TYPE_WEEK, week_number=19).semester_id, self.semester_2.id)

    def test_schedule_initializer_preserves_saved_week_dates(self):
        week_7 = self.period(CompetitionPeriod.TYPE_WEEK, week_number=7)
        adjusted_start = date(2026, 10, 20)
        week_7.start_date = adjusted_start
        week_7.end_date = adjusted_start + timedelta(days=6)
        week_7.save(update_fields=['start_date', 'end_date'])

        result = init_standard_35_weeks_schedule(self.year)
        week_7.refresh_from_db()

        self.assertEqual(week_7.start_date, adjusted_start)
        self.assertEqual(week_7.end_date, adjusted_start + timedelta(days=6))
        self.assertTrue(any('Tuần 7' in issue for issue in result['configuration_issues']))
        self.assertIsNone(get_or_create_week_for_date(date(2026, 10, 26), self.year))

    def test_only_approved_weekly_points_flow_into_month_and_semester_totals(self):
        week_1 = self.period(CompetitionPeriod.TYPE_WEEK, week_number=1)
        week_2 = self.period(CompetitionPeriod.TYPE_WEEK, week_number=2)
        week_3 = self.period(CompetitionPeriod.TYPE_WEEK, week_number=3)
        week_4 = self.period(CompetitionPeriod.TYPE_WEEK, week_number=4)
        month_1 = self.period(CompetitionPeriod.TYPE_MONTH, internal_month_number=1)
        semester_1 = self.period(CompetitionPeriod.TYPE_SEMESTER, semester=self.semester_1)
        occurred_at = timezone.make_aware(timezone.datetime(2026, 9, 9, 8, 0))

        ViolationRecord.objects.create(
            record_code='CAL-VERIFIED', school_class=self.class_10a1, rule=self.rule,
            points_deducted=Decimal('10.00'), status=ViolationRecord.STATUS_VERIFIED,
            occurred_at=occurred_at, reporter=self.admin,
        )
        ViolationRecord.objects.create(
            record_code='CAL-PENDING', school_class=self.class_10a1, rule=self.rule,
            points_deducted=Decimal('50.00'), status=ViolationRecord.STATUS_PENDING,
            occurred_at=occurred_at, reporter=self.admin,
        )
        ViolationRecord.objects.create(
            record_code='CAL-REJECTED', school_class=self.class_10a1, rule=self.rule,
            points_deducted=Decimal('30.00'), status=ViolationRecord.STATUS_REJECTED,
            occurred_at=occurred_at, reporter=self.admin,
        )
        ScoreAdjustment.objects.create(
            idempotency_key=uuid.uuid4(), competition_period=week_1,
            school_class=self.class_10a1, amount=Decimal('5.00'),
            reason='Điểm phong trào đã duyệt', status=ScoreAdjustment.STATUS_APPROVED,
            created_by=self.admin, approved_by=self.admin, approved_at=timezone.now(),
        )

        recalculate_period_scores(week_1)
        week_score = ClassCompetitionScore.objects.get(
            competition_period=week_1, school_class=self.class_10a1,
        )
        self.assertEqual(week_score.base_points, Decimal('100.00'))
        self.assertEqual(week_score.bonus_points, Decimal('5.00'))
        self.assertEqual(week_score.penalty_points, Decimal('10.00'))
        self.assertEqual(week_score.total_score, Decimal('95.00'))
        self.assertEqual(get_valid_aggregate_class_ids(month_1), set())

        for week in (week_1, week_2, week_3, week_4):
            lock_competition_period(week.id, self.admin)

        month_score = ClassCompetitionScore.objects.get(
            competition_period=month_1, school_class=self.class_10a1,
        )
        semester_score = ClassCompetitionScore.objects.get(
            competition_period=semester_1, school_class=self.class_10a1,
        )
        self.assertEqual(month_score.base_points, Decimal('400.00'))
        self.assertEqual(month_score.total_score, Decimal('395.00'))
        self.assertEqual(semester_score.base_points, Decimal('400.00'))
        self.assertEqual(semester_score.total_score, Decimal('395.00'))
        self.assertEqual(get_period_status(month_1)['included_weeks'], 4)
        self.assertTrue(get_period_status(month_1)['complete_result'])
        self.assertFalse(get_period_status(semester_1)['complete_result'])

    def test_dashboard_and_score_endpoints_are_scoped_and_scores_are_read_only(self):
        client = APIClient()
        client.force_authenticate(user=self.student_user)
        snapshot = client.get('/api/competition/periods/dashboard/')
        self.assertEqual(snapshot.status_code, 200)
        self.assertEqual([item['id'] for item in snapshot.data['classes']], [self.class_10a1.id])

        week_1 = self.period(CompetitionPeriod.TYPE_WEEK, week_number=1)
        score_list = client.get('/api/competition/periods/{}/scores/'.format(week_1.id))
        self.assertEqual(score_list.status_code, 200)
        self.assertEqual([row['class_name'] for row in score_list.data['scores']], ['10A1'])
        forbidden = client.get(
            f'/api/competition/periods/{week_1.id}/classes/{self.class_10a2.id}/detail/'
        )
        self.assertEqual(forbidden.status_code, 403)
        write_attempt = client.post('/api/competition/scores/', {}, format='json')
        self.assertEqual(write_attempt.status_code, 405)

        adjustment = ScoreAdjustment.objects.create(
            idempotency_key=uuid.uuid4(),
            competition_period=week_1,
            school_class=self.class_10a1,
            amount=Decimal('2.50'),
            reason='Ghi nhận hoạt động tình nguyện',
            status=ScoreAdjustment.STATUS_APPROVED,
            created_by=self.admin,
            approved_by=self.admin,
            approved_at=timezone.now(),
        )
        recalculate_period_scores(week_1)
        detail = client.get(
            f'/api/competition/periods/{week_1.id}/classes/{self.class_10a1.id}/detail/'
        )
        self.assertEqual(detail.status_code, 200)
        adjustment_event = next(
            event for event in detail.data['events']
            if event['event_type'] == 'SCORE_ADJUSTMENT'
        )
        self.assertEqual(adjustment_event['id'], adjustment.id)
        self.assertEqual(adjustment_event['amount'], 2.5)
        self.assertEqual(adjustment_event['approved_by_name'], self.admin.username)
