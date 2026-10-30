from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import User, AcademicYear, Semester
from conduct.models import SchoolClass, ConductRuleCategory, ConductRule, ViolationRecord
from conduct.services import create_violation_record, get_class_score_snapshot
from competition.models import CompetitionPeriod, ClassCompetitionScore, ScoreCriterion
from competition.services import (
    init_standard_35_weeks_schedule,
    get_current_competition_period,
    recalculate_score_for_class_at_time
)


class SchoolYear35WeeksStabilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # 1. Admin & Đoàn trường users
        cls.admin = User.objects.create_superuser(
            username='admin_test',
            email='admin@huongkhe.edu.vn',
            password='adminpassword',
            role=User.ROLE_ADMIN,
            account_status=User.STATUS_APPROVED,
            can_verify_violations=True
        )

        cls.doan_truong = User.objects.create_user(
            username='doan_truong_test',
            email='doan@huongkhe.edu.vn',
            password='doanpassword',
            role=User.ROLE_DOAN_TRUONG,
            account_status=User.STATUS_APPROVED,
            can_verify_violations=True
        )

        cls.teacher = User.objects.create_user(
            username='teacher_test',
            email='gvbm@huongkhe.edu.vn',
            password='teacherpassword',
            role=User.ROLE_GVBM,
            account_status=User.STATUS_APPROVED
        )

        # 2. Academic Year 2026-2027
        cls.year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=date(2026, 9, 7),
            end_date=date(2027, 5, 23),
            is_current=True
        )

        # 3. Create 64 classes
        cls.classes = []
        for g, count in [(10, 22), (11, 21), (12, 21)]:
            for c in range(1, count + 1):
                cls.classes.append(
                    SchoolClass.objects.create(
                        name=f"{g}A{c}",
                        grade=g,
                        academic_year=cls.year
                    )
                )

        cls.class_10a1 = cls.classes[0]
        cls.class_11a1 = [c for c in cls.classes if c.grade == 11][0]
        cls.class_12a1 = [c for c in cls.classes if c.grade == 12][0]

        # 4. Score Criterion
        cls.criterion = ScoreCriterion.objects.create(
            academic_year=cls.year,
            name='Biểu điểm chuẩn THPT Hương Khê',
            initial_base_points=Decimal('100.00'),
            effective_from=date(2026, 9, 7),
            effective_to=date(2027, 5, 23),
            is_approved=True
        )

        # 5. Rule
        cls.cat = ConductRuleCategory.objects.create(name='Chuyên cần')
        cls.rule = ConductRule.objects.create(
            category=cls.cat,
            code='CC01',
            name='Đi học muộn',
            default_points_deducted=Decimal('2.00'),
            is_active=True
        )

    def setUp(self):
        self.client = APIClient()

    def test_01_init_standard_35_weeks_schedule_creates_exact_semesters_and_weeks(self):
        """Kiểm tra khởi tạo chính xác 18 tuần Học kỳ I và 17 tuần Học kỳ II (tổng 35 tuần)"""
        res = init_standard_35_weeks_schedule(academic_year=self.year)

        self.assertEqual(res['total_weeks'], 35)
        self.assertEqual(res['hk1_weeks'], 18)
        self.assertEqual(res['hk2_weeks'], 17)
        self.assertEqual(res['classes_count'], 64)

        # Kiểm tra 2 Học kỳ trong DB
        sem1 = Semester.objects.get(academic_year=self.year, semester_number=1)
        sem2 = Semester.objects.get(academic_year=self.year, semester_number=2)
        self.assertEqual(sem1.name, 'Học kỳ I')
        self.assertEqual(sem2.name, 'Học kỳ II')

        # Kiểm tra số lượng tuần học kỳ I (18 tuần)
        hk1_weeks = CompetitionPeriod.objects.filter(
            academic_year=self.year,
            period_type=CompetitionPeriod.TYPE_WEEK,
            semester=sem1
        ).order_by('week_number')
        self.assertEqual(hk1_weeks.count(), 18)
        self.assertEqual(list(hk1_weeks.values_list('week_number', flat=True)), list(range(1, 19)))

        # Kiểm tra số lượng tuần học kỳ II (17 tuần: 19..35)
        hk2_weeks = CompetitionPeriod.objects.filter(
            academic_year=self.year,
            period_type=CompetitionPeriod.TYPE_WEEK,
            semester=sem2
        ).order_by('week_number')
        self.assertEqual(hk2_weeks.count(), 17)
        self.assertEqual(list(hk2_weeks.values_list('week_number', flat=True)), list(range(19, 36)))

        # Kiểm tra properties: semester_week_number và display_week_label
        week_1 = hk1_weeks.first()
        self.assertEqual(week_1.semester_week_number, 1)
        self.assertIn('Học kỳ I', week_1.display_week_label)

        week_19 = hk2_weeks.first()
        self.assertEqual(week_19.semester_week_number, 1) # Tuần 1 của HK II
        self.assertIn('Tuần 1 - Học kỳ II', week_19.display_week_label)

        week_35 = hk2_weeks.last()
        self.assertEqual(week_35.semester_week_number, 17) # Tuần 17 của HK II
        self.assertIn('Tuần 17 - Học kỳ II', week_35.display_week_label)

    def test_02_all_64_classes_have_scores_in_all_35_weeks(self):
        """Tất cả 64 lớp phải có sẵn bản ghi điểm 100đ khởi điểm cho tất cả các tuần"""
        init_standard_35_weeks_schedule(academic_year=self.year)

        for week_num in [1, 7, 18, 19, 25, 35]:
            p = CompetitionPeriod.objects.get(
                academic_year=self.year,
                period_type=CompetitionPeriod.TYPE_WEEK,
                week_number=week_num
            )
            scores_count = ClassCompetitionScore.objects.filter(competition_period=p).count()
            self.assertEqual(scores_count, 64, f"Tuần {week_num} phải có đủ 64 lớp")

            score_10a1 = ClassCompetitionScore.objects.get(competition_period=p, school_class=self.class_10a1)
            self.assertEqual(score_10a1.base_points, Decimal('100.00'))
            self.assertEqual(score_10a1.total_score, Decimal('100.00'))

    def test_03_violation_in_hk1_deducts_points_and_updates_rankings(self):
        """Vi phạm xảy ra trong Học kỳ I (Tuần 7) trừ điểm tuần 7, tháng 10 và Học kỳ I"""
        init_standard_35_weeks_schedule(academic_year=self.year)

        period_w7 = CompetitionPeriod.objects.get(
            academic_year=self.year,
            period_type=CompetitionPeriod.TYPE_WEEK,
            week_number=7
        )

        # Vi phạm ngày giữa Tuần 7: 2026-10-21
        occurred_time = timezone.make_aware(
            timezone.datetime.combine(period_w7.start_date + timedelta(days=2), timezone.datetime.min.time())
        )

        # Ghi nhận vi phạm trực tiếp bởi Đoàn trường (-2đ)
        v = create_violation_record(
            reporter=self.admin,
            class_id=self.class_10a1.id,
            rule_id=self.rule.id,
            occurred_at=occurred_time,
            direct_deduct=True
        )
        self.assertEqual(v.status, ViolationRecord.STATUS_VERIFIED)

        # Kiểm tra điểm tuần 7 của lớp 10A1: 100 - 2 = 98đ
        score_w7 = ClassCompetitionScore.objects.get(competition_period=period_w7, school_class=self.class_10a1)
        self.assertEqual(score_w7.penalty_points, Decimal('2.00'))
        self.assertEqual(score_w7.total_score, Decimal('98.00'))
        self.assertEqual(score_w7.verified_violations_count, 1)

        # Các lớp khác vẫn 100đ và xếp hạng trên 10A1
        score_10a2 = ClassCompetitionScore.objects.get(competition_period=period_w7, school_class=self.classes[1])
        self.assertEqual(score_10a2.total_score, Decimal('100.00'))
        self.assertGreater(score_w7.rank, score_10a2.rank)

        # Tuần chưa chốt không được đưa vào kết quả tháng chính thức.
        period_m2 = CompetitionPeriod.objects.get(
            academic_year=self.year,
            period_type=CompetitionPeriod.TYPE_MONTH,
            internal_month_number=2,
        )
        self.assertFalse(ClassCompetitionScore.objects.filter(
            competition_period=period_m2, school_class=self.class_10a1,
        ).exists())
        with patch('django.utils.timezone.localdate', return_value=period_w7.end_date + timedelta(days=1)):
            from competition.services import lock_competition_period
            lock_competition_period(period_w7.id, self.admin)
        score_m2 = ClassCompetitionScore.objects.get(competition_period=period_m2, school_class=self.class_10a1)
        self.assertEqual(score_m2.penalty_points, Decimal('2.00'))
        self.assertEqual(score_m2.total_score, Decimal('98.00'))

    def test_04_violation_in_hk2_deducts_points_in_hk2_week(self):
        """Vi phạm trong Học kỳ II (Tuần 22, tức tuần 4 HK II) trừ điểm tuần 22 và Học kỳ II"""
        init_standard_35_weeks_schedule(academic_year=self.year)

        period_w22 = CompetitionPeriod.objects.get(
            academic_year=self.year,
            period_type=CompetitionPeriod.TYPE_WEEK,
            week_number=22
        )

        occurred_time = timezone.make_aware(
            timezone.datetime.combine(period_w22.start_date + timedelta(days=1), timezone.datetime.min.time())
        )

        # Tạo bản ghi vi phạm trực tiếp trong HK II và tính toán lại điểm
        ViolationRecord.objects.create(
            reporter=self.admin,
            school_class=self.class_11a1,
            rule=self.rule,
            points_deducted=Decimal('2.00'),
            occurred_at=occurred_time,
            status=ViolationRecord.STATUS_VERIFIED
        )
        recalculate_score_for_class_at_time(self.class_11a1, occurred_time)

        score_w22 = ClassCompetitionScore.objects.get(competition_period=period_w22, school_class=self.class_11a1)
        self.assertEqual(score_w22.penalty_points, Decimal('2.00'))
        self.assertEqual(score_w22.total_score, Decimal('98.00'))

        # Học kỳ chỉ cộng tuần đã chốt.
        period_sem2 = CompetitionPeriod.objects.get(
            academic_year=self.year,
            period_type=CompetitionPeriod.TYPE_SEMESTER,
            semester__semester_number=2
        )
        with patch('django.utils.timezone.localdate', return_value=period_w22.end_date + timedelta(days=1)):
            from competition.services import lock_competition_period
            lock_competition_period(period_w22.id, self.admin)
        score_sem2 = ClassCompetitionScore.objects.get(competition_period=period_sem2, school_class=self.class_11a1)
        self.assertEqual(score_sem2.penalty_points, Decimal('2.00'))

    def test_05_api_current_period_and_semester_filtering(self):
        """API lấy tuần hiện tại và lọc tuần theo học kỳ (semester_number=1 và semester_number=2)"""
        init_standard_35_weeks_schedule(academic_year=self.year)
        self.client.force_authenticate(user=self.admin)

        # 1. API current period
        res_cur = self.client.get('/api/competition/periods/current/')
        self.assertEqual(res_cur.status_code, 200)
        self.assertIn('week_number', res_cur.data)
        self.assertIn('display_week_label', res_cur.data)

        # 2. API lọc 18 tuần Học kỳ I
        res_hk1 = self.client.get('/api/competition/periods/?period_type=WEEK&semester_number=1')
        self.assertEqual(res_hk1.status_code, 200)
        self.assertEqual(len(res_hk1.data), 18)
        for w in res_hk1.data:
            self.assertLessEqual(w['week_number'], 18)
            self.assertEqual(w['semester_number'], 1)

        # 3. API lọc 17 tuần Học kỳ II
        res_hk2 = self.client.get('/api/competition/periods/?period_type=WEEK&semester_number=2')
        self.assertEqual(res_hk2.status_code, 200)
        self.assertEqual(len(res_hk2.data), 17)
        for w in res_hk2.data:
            self.assertGreaterEqual(w['week_number'], 19)
            self.assertEqual(w['semester_number'], 2)

    def test_06_api_init_standard_schedule_idempotent(self):
        """API chuẩn hóa 35 tuần hoạt động an toàn, idempotency và bảo toàn dữ liệu"""
        self.client.force_authenticate(user=self.admin)
        res = self.client.post('/api/competition/periods/init-standard-schedule/', {'academic_year': self.year.id})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['data']['total_weeks'], 35)

        # Chạy lại lần 2 vẫn 200 và giữ nguyên
        res2 = self.client.post('/api/competition/periods/init-standard-schedule/', {'academic_year': self.year.id})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.data['data']['total_weeks'], 35)
