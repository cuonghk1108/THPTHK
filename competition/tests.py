# -*- coding: utf-8 -*-
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from core.models import User, AcademicYear, Semester, AuditLog
from conduct.models import SchoolClass, Student, ConductRuleCategory, ConductRule, ViolationRecord
from competition.models import ScoreCriterion, CompetitionPeriod, ClassCompetitionScore
from competition.services import (
    recalculate_period_scores,
    recalculate_score_for_class_at_time,
    lock_competition_period,
    unlock_competition_period,
    assign_ranks,
)
from reports.services import export_competition_pdf, export_competition_excel

User = get_user_model()


class CompetitionRankingSystemTests(TestCase):
    """
    Bộ kiểm thử toàn diện hệ thống xếp hạng thi đua theo Tuần, Tháng, Học kỳ
    đáp ứng 12 tiêu chí nghiệp vụ của THPT Hương Khê.
    """

    def setUp(self):
        self.client = APIClient()

        # 1. Năm học & Học kỳ
        self.year_2026 = AcademicYear.objects.create(
            name='2026-2027',
            start_date=date(2026, 9, 5),
            end_date=date(2027, 5, 30),
            is_current=True
        )
        self.year_2025 = AcademicYear.objects.create(
            name='2025-2026',
            start_date=date(2025, 9, 5),
            end_date=date(2026, 5, 30),
            is_current=False
        )

        self.semester_1 = Semester.objects.create(
            academic_year=self.year_2026,
            semester_number=1,
            name='Học kỳ I',
            start_date=date(2026, 9, 5),
            end_date=date(2027, 1, 15),
            is_current=True
        )

        # 2. Quy chế điểm
        self.criterion = ScoreCriterion.objects.create(
            academic_year=self.year_2026,
            name='Quy chế thi đua 2026-2027',
            initial_base_points=Decimal('100.00'),
            min_score=Decimal('0.00'),
            max_score=Decimal('150.00'),
            tie_breaker=ScoreCriterion.TIE_BREAKER_EQUAL,
            effective_from=date(2026, 9, 5),
            effective_to=date(2027, 5, 30),
            is_approved=True
        )

        # 3. Lớp học
        self.class_10a1 = SchoolClass.objects.create(name='10A1', grade=10, academic_year=self.year_2026)
        self.class_10a2 = SchoolClass.objects.create(name='10A2', grade=10, academic_year=self.year_2026)
        self.class_10a3 = SchoolClass.objects.create(name='10A3', grade=10, academic_year=self.year_2026)
        self.class_old = SchoolClass.objects.create(name='10A1-Old', grade=10, academic_year=self.year_2025)

        # 4. Người dùng
        self.admin = User.objects.create_user(
            username='admin_test',
            full_name='Thầy Admin',
            role=User.ROLE_ADMIN,
            account_status=User.STATUS_APPROVED
        )
        self.doan_truong = User.objects.create_user(
            username='doan_test',
            full_name='Đoàn Trường',
            role=User.ROLE_DOAN_TRUONG,
            account_status=User.STATUS_APPROVED
        )
        self.student_10a1 = User.objects.create_user(
            username='hs_10a1',
            full_name='Học Sinh 10A1',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED
        )
        Student.objects.create(
            user=self.student_10a1,
            student_code='HS-10A1-01',
            full_name='Học Sinh 10A1',
            school_class=self.class_10a1,
            date_of_birth=date(2010, 1, 1)
        )

        self.student_10a2 = User.objects.create_user(
            username='hs_10a2',
            full_name='Học Sinh 10A2',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED
        )
        Student.objects.create(
            user=self.student_10a2,
            student_code='HS-10A2-01',
            full_name='Học Sinh 10A2',
            school_class=self.class_10a2,
            date_of_birth=date(2010, 2, 2)
        )

        # 5. Quy định vi phạm
        self.cat = ConductRuleCategory.objects.create(name='Nền nếp')
        self.rule_late = ConductRule.objects.create(
            category=self.cat,
            code='VP-01',
            name='Đi học muộn',
            default_points_deducted=Decimal('2.00')
        )
        self.rule_uniform = ConductRule.objects.create(
            category=self.cat,
            code='VP-02',
            name='Sai đồng phục',
            default_points_deducted=Decimal('3.00')
        )

        # 6. Các kỳ thi đua
        # Tuần 6: 2026-10-12 -> 2026-10-18
        self.period_w6 = CompetitionPeriod.objects.create(
            name='Tuần 6 - Học kỳ I',
            period_type=CompetitionPeriod.TYPE_WEEK,
            week_number=6,
            internal_month_number=2,
            academic_year=self.year_2026,
            semester=self.semester_1,
            start_date=date(2026, 10, 12),
            end_date=date(2026, 10, 18),
            is_locked=True
        )
        # Tuần 7: 2026-10-19 -> 2026-10-25
        self.period_w7 = CompetitionPeriod.objects.create(
            name='Tuần 7 - Học kỳ I',
            period_type=CompetitionPeriod.TYPE_WEEK,
            week_number=7,
            internal_month_number=2,
            academic_year=self.year_2026,
            semester=self.semester_1,
            start_date=date(2026, 10, 19),
            end_date=date(2026, 10, 25),
            is_locked=False
        )
        # Tháng 10/2026: 2026-10-01 -> 2026-10-31
        self.period_m10 = CompetitionPeriod.objects.create(
            name='Thi đua Tháng 10/2026',
            period_type=CompetitionPeriod.TYPE_MONTH,
            month_number=10,
            internal_month_number=2,
            academic_year=self.year_2026,
            semester=self.semester_1,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 31),
            is_locked=False
        )
        # Học kỳ I: 2026-09-05 -> 2027-01-15
        self.period_sem1 = CompetitionPeriod.objects.create(
            name='Thi đua Học kỳ I (2026-2027)',
            period_type=CompetitionPeriod.TYPE_SEMESTER,
            academic_year=self.year_2026,
            semester=self.semester_1,
            start_date=date(2026, 9, 5),
            end_date=date(2027, 1, 15),
            is_locked=False
        )

    def test_01_week_points_do_not_flow_into_incomplete_aggregates(self):
        """Điểm tuần được tính ngay; kỳ tháng/học kỳ thiếu lịch tuần thì cần rà soát."""
        # Vi phạm 2026-10-21 thuộc Tuần 7 theo lịch năm học 2026–2027.
        ViolationRecord.objects.create(
            record_code='VP-20261021-001',
            school_class=self.class_10a1,
            rule=self.rule_late,
            points_deducted=Decimal('2.00'),
            status=ViolationRecord.STATUS_VERIFIED,
            occurred_at=timezone.datetime(2026, 10, 21, 7, 30, tzinfo=timezone.get_current_timezone()),
            reporter=self.admin
        )

        # Chỉ các tuần đã chốt mới tham gia tổng hợp; lịch mẫu này thiếu các tuần còn lại.
        recalculate_period_scores(self.period_w6, force=True)
        recalculate_period_scores(self.period_w7)
        recalculate_period_scores(self.period_m10)
        recalculate_period_scores(self.period_sem1)

        score_w7 = ClassCompetitionScore.objects.get(competition_period=self.period_w7, school_class=self.class_10a1)
        self.assertEqual(score_w7.penalty_points, Decimal('2.00'))
        self.assertEqual(score_w7.total_score, Decimal('98.00'))

        self.assertFalse(ClassCompetitionScore.objects.filter(
            competition_period=self.period_m10, school_class=self.class_10a1,
        ).exists())

        self.assertFalse(ClassCompetitionScore.objects.filter(
            competition_period=self.period_sem1, school_class=self.class_10a1,
        ).exists())

    def test_02_boundary_events_not_double_counted(self):
        """Tiêu chuẩn 2: Sự kiện ở ranh giới hai kỳ không bị đếm trùng hoặc nhảy kỳ sai"""
        # Vi phạm ngày cuối Tuần 6 (2026-10-18)
        v_w6 = ViolationRecord.objects.create(
            record_code='VP-20261011-001',
            school_class=self.class_10a1,
            rule=self.rule_late,
            points_deducted=Decimal('2.00'),
            status=ViolationRecord.STATUS_VERIFIED,
            occurred_at=timezone.datetime(2026, 10, 18, 16, 0, tzinfo=timezone.get_current_timezone()),
            reporter=self.admin
        )
        # Vi phạm ngày đầu Tuần 7 (2026-10-19)
        v_w7 = ViolationRecord.objects.create(
            record_code='VP-20261012-001',
            school_class=self.class_10a1,
            rule=self.rule_uniform,
            points_deducted=Decimal('3.00'),
            status=ViolationRecord.STATUS_VERIFIED,
            occurred_at=timezone.datetime(2026, 10, 19, 7, 0, tzinfo=timezone.get_current_timezone()),
            reporter=self.admin
        )

        recalculate_period_scores(self.period_w6, force=True)
        recalculate_period_scores(self.period_w7)

        score_w6 = ClassCompetitionScore.objects.get(competition_period=self.period_w6, school_class=self.class_10a1)
        score_w7 = ClassCompetitionScore.objects.get(competition_period=self.period_w7, school_class=self.class_10a1)

        # Tuần 6 chỉ có 2đ trừ (từ v_w6)
        self.assertEqual(score_w6.penalty_points, Decimal('2.00'))
        self.assertEqual(score_w6.total_score, Decimal('98.00'))

        # Tuần 7 chỉ có 3đ trừ (từ v_w7), KHÔNG bị đếm trùng v_w6
        self.assertEqual(score_w7.penalty_points, Decimal('3.00'))
        self.assertEqual(score_w7.total_score, Decimal('97.00'))

    def test_03_cancelled_or_pending_violations_not_deducted(self):
        """Tiêu chuẩn 3: Vi phạm bị hủy hoặc chưa xác minh (PENDING, REJECTED) không bị trừ điểm"""
        ViolationRecord.objects.create(
            record_code='VP-PENDING',
            school_class=self.class_10a2,
            rule=self.rule_late,
            points_deducted=Decimal('2.00'),
            status=ViolationRecord.STATUS_PENDING,
            occurred_at=timezone.datetime(2026, 10, 21, 8, 0, tzinfo=timezone.get_current_timezone()),
            reporter=self.admin
        )
        ViolationRecord.objects.create(
            record_code='VP-REJECTED',
            school_class=self.class_10a2,
            rule=self.rule_uniform,
            points_deducted=Decimal('3.00'),
            status=ViolationRecord.STATUS_REJECTED,
            occurred_at=timezone.datetime(2026, 10, 14, 8, 30, tzinfo=timezone.get_current_timezone()),
            reporter=self.admin
        )

        recalculate_period_scores(self.period_w7)
        score_10a2 = ClassCompetitionScore.objects.get(competition_period=self.period_w7, school_class=self.class_10a2)

        self.assertEqual(score_10a2.penalty_points, Decimal('0.00'))
        self.assertEqual(score_10a2.total_score, Decimal('100.00'))

    def test_04_equal_rank_tie_breaking(self):
        """Tiêu chuẩn 4: Các lớp bằng điểm cùng chia sẻ thứ hạng (Đồng hạng minh bạch)"""
        # Lớp 10A1: 100đ, Lớp 10A2: 100đ, Lớp 10A3: 98đ
        ViolationRecord.objects.create(
            record_code='VP-10A3',
            school_class=self.class_10a3,
            rule=self.rule_late,
            points_deducted=Decimal('2.00'),
            status=ViolationRecord.STATUS_VERIFIED,
            occurred_at=timezone.datetime(2026, 10, 21, 8, 0, tzinfo=timezone.get_current_timezone()),
            reporter=self.admin
        )

        recalculate_period_scores(self.period_w7)

        s_10a1 = ClassCompetitionScore.objects.get(competition_period=self.period_w7, school_class=self.class_10a1)
        s_10a2 = ClassCompetitionScore.objects.get(competition_period=self.period_w7, school_class=self.class_10a2)
        s_10a3 = ClassCompetitionScore.objects.get(competition_period=self.period_w7, school_class=self.class_10a3)

        self.assertEqual(s_10a1.total_score, Decimal('100.00'))
        self.assertEqual(s_10a2.total_score, Decimal('100.00'))
        self.assertEqual(s_10a3.total_score, Decimal('98.00'))

        # Cả 10A1 và 10A2 cùng đồng hạng 1
        self.assertEqual(s_10a1.rank, 1)
        self.assertEqual(s_10a2.rank, 1)
        # Lớp tiếp theo xếp hạng 3 theo chuẩn Standard Competition Ranking (1, 1, 3)
        self.assertEqual(s_10a3.rank, 3)

    def test_05_academic_year_isolation(self):
        """Tiêu chuẩn 5: Năm học mới không bị trộn dữ liệu năm học cũ"""
        ViolationRecord.objects.create(
            record_code='VP-OLD-YEAR',
            school_class=self.class_old,
            rule=self.rule_late,
            points_deducted=Decimal('5.00'),
            status=ViolationRecord.STATUS_VERIFIED,
            occurred_at=timezone.datetime(2026, 10, 14, 8, 0, tzinfo=timezone.get_current_timezone()),
            reporter=self.admin
        )

        recalculate_period_scores(self.period_w7)

        # Lớp của năm 2025-2026 không xuất hiện trong kỳ thi đua của năm 2026-2027
        self.assertFalse(ClassCompetitionScore.objects.filter(competition_period=self.period_w7, school_class=self.class_old).exists())

    def test_06_previous_period_comparison_and_missing_data(self):
        """Tiêu chuẩn 6: So sánh thứ hạng và hiển thị 'Chưa có dữ liệu so sánh' (None) khi thiếu kỳ trước"""
        # Tuần 6: 10A1 hạng 2 (98đ), 10A2 hạng 1 (100đ)
        ViolationRecord.objects.create(
            record_code='VP-W6-10A1',
            school_class=self.class_10a1,
            rule=self.rule_late,
            points_deducted=Decimal('2.00'),
            status=ViolationRecord.STATUS_VERIFIED,
            occurred_at=timezone.datetime(2026, 10, 13, 8, 0, tzinfo=timezone.get_current_timezone()),
            reporter=self.admin
        )
        recalculate_period_scores(self.period_w6, force=True)

        # Tuần 7: 10A1 không có lỗi (100đ -> hạng 1), 10A2 có lỗi (98đ -> hạng 2)
        ViolationRecord.objects.create(
            record_code='VP-W7-10A2',
            school_class=self.class_10a2,
            rule=self.rule_late,
            points_deducted=Decimal('2.00'),
            status=ViolationRecord.STATUS_VERIFIED,
            occurred_at=timezone.datetime(2026, 10, 20, 8, 0, tzinfo=timezone.get_current_timezone()),
            reporter=self.admin
        )
        recalculate_period_scores(self.period_w7)

        s_w7_10a1 = ClassCompetitionScore.objects.get(competition_period=self.period_w7, school_class=self.class_10a1)
        s_w7_10a2 = ClassCompetitionScore.objects.get(competition_period=self.period_w7, school_class=self.class_10a2)

        # 10A1: kỳ trước hạng 3 (do 10A2, 10A3 đồng hạng 1), kỳ này hạng 1 -> rank_change = +2 (tiến bộ 2 bậc)
        self.assertEqual(s_w7_10a1.rank, 1)
        self.assertEqual(s_w7_10a1.rank_change, 2)

        # 10A2: kỳ trước hạng 1, kỳ này hạng 3 (do 10A1, 10A3 đồng hạng 1) -> rank_change = -2 (giảm 2 bậc)
        self.assertEqual(s_w7_10a2.rank, 3)
        self.assertEqual(s_w7_10a2.rank_change, -2)

        # Kiểm tra nếu ở Tuần 6 chưa có kỳ trước đó nữa: rank_change phải là None
        s_w6_10a1 = ClassCompetitionScore.objects.get(competition_period=self.period_w6, school_class=self.class_10a1)
        self.assertIsNone(s_w6_10a1.rank_change, "Kỳ đầu tiên không có kỳ trước thì rank_change phải là None")

    def test_07_locking_period_idempotency_and_audit_log(self):
        """Tiêu chuẩn 7: Chốt kỳ an toàn, bảo toàn lịch sử và lưu Audit Log"""
        with patch('django.utils.timezone.localdate', return_value=self.period_w7.end_date + timedelta(days=1)):
            lock_competition_period(self.period_w7.id, self.admin)
        self.period_w7.refresh_from_db()
        self.assertTrue(self.period_w7.is_locked)
        self.assertEqual(self.period_w7.locked_by, self.admin)

        # Kiểm tra Audit Log
        log = AuditLog.objects.filter(resource_type='SCORE', action='LOCK', resource_id=str(self.period_w7.id)).first()
        self.assertIsNotNone(log)
        self.assertIn('Chốt sổ', log.details)

        # Mở lại kỳ
        unlock_competition_period(self.period_w7.id, self.admin)
        self.period_w7.refresh_from_db()
        self.assertFalse(self.period_w7.is_locked)

    def test_08_delayed_violation_triggers_recalculation(self):
        """Tiêu chuẩn 8: Vi phạm bổ sung muộn tự động cập nhật kỳ đang mở tương ứng"""
        recalculate_period_scores(self.period_w7)
        score_before = ClassCompetitionScore.objects.get(competition_period=self.period_w7, school_class=self.class_10a1)
        self.assertEqual(score_before.total_score, Decimal('100.00'))

        # Thêm vi phạm muộn vào ngày 2026-10-15
        late_v = ViolationRecord.objects.create(
            record_code='VP-LATE',
            school_class=self.class_10a1,
            rule=self.rule_late,
            points_deducted=Decimal('2.00'),
            status=ViolationRecord.STATUS_VERIFIED,
            occurred_at=timezone.datetime(2026, 10, 22, 9, 0, tzinfo=timezone.get_current_timezone()),
            reporter=self.doan_truong
        )
        recalculate_score_for_class_at_time(self.class_10a1, late_v.occurred_at)

        score_after = ClassCompetitionScore.objects.get(competition_period=self.period_w7, school_class=self.class_10a1)
        self.assertEqual(score_after.total_score, Decimal('98.00'))

    def test_09_rbac_class_detail_security(self):
        """Tiêu chuẩn 9: Phân quyền xem chi tiết - Học sinh chỉ xem lớp mình, bị chặn xem lớp khác"""
        self.client.force_authenticate(user=self.student_10a1)

        # Học sinh 10A1 xem chi tiết lớp 10A1 -> Cho phép (200 OK)
        res_own = self.client.get(f'/api/competition/periods/{self.period_w7.id}/classes/{self.class_10a1.id}/detail/')
        self.assertEqual(res_own.status_code, status.HTTP_200_OK)
        self.assertEqual(res_own.data['school_class']['name'], '10A1')

        # Học sinh 10A1 cố tình truy cập lớp 10A2 -> Bị chặn (403 Forbidden)
        res_other = self.client.get(f'/api/competition/periods/{self.period_w7.id}/classes/{self.class_10a2.id}/detail/')
        self.assertEqual(res_other.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', res_other.data)

        # Admin / Đoàn trường có thể xem mọi lớp
        self.client.force_authenticate(user=self.admin)
        res_admin = self.client.get(f'/api/competition/periods/{self.period_w7.id}/classes/{self.class_10a2.id}/detail/')
        self.assertEqual(res_admin.status_code, status.HTTP_200_OK)

    def test_10_pdf_and_excel_exports_with_period_support(self):
        """Tiêu chuẩn 10: Xuất báo cáo PDF và Excel theo kỳ tương ứng"""
        # Xuất PDF tuần
        pdf_week = export_competition_pdf(self.period_w7.id, self.admin)
        self.assertTrue(pdf_week.startswith(b'%PDF-'))
        self.assertGreater(len(pdf_week), 5000)

        # Xuất Excel tháng
        excel_month = export_competition_excel(self.period_m10.id, self.admin)
        self.assertGreater(len(excel_month), 1000)

        # Xuất PDF học kỳ
        pdf_sem = export_competition_pdf(self.period_sem1.id, self.admin)
        self.assertTrue(pdf_sem.startswith(b'%PDF-'))

    def test_11_filters_meta_endpoint(self):
        """Tiêu chuẩn 11: Endpoint metadata trả về đầy đủ danh mục năm học, học kỳ và loại kỳ"""
        self.client.force_authenticate(user=self.student_10a1)
        res = self.client.get('/api/competition/periods/filters-meta/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('academic_years', res.data)
        self.assertIn('semesters', res.data)
        self.assertIn('period_types', res.data)
        self.assertIn('criterion', res.data)
        self.assertEqual(len(res.data['period_types']), 3)

    def test_12_period_validation_dates(self):
        """Tiêu chuẩn 12: Kiểm tra tính hợp lệ của ngày bắt đầu và kết thúc khi tạo kỳ"""
        self.client.force_authenticate(user=self.admin)
        payload_invalid = {
            'period_type': CompetitionPeriod.TYPE_WEEK,
            'academic_year': self.year_2026.id,
            'name': 'Kỳ sai ngày',
            'start_date': '2026-10-20',
            'end_date': '2026-10-10'  # Ngày kết thúc trước ngày bắt đầu
        }
        res = self.client.post('/api/competition/periods/', data=payload_invalid, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_13_doan_truong_competition_permissions(self):
        """Tiêu chuẩn 13: Đoàn trường có đầy đủ quyền theo dõi, chi tiết và xuất báo cáo thi đua chi đoàn toàn trường"""
        from competition.services import get_competition_class_scope, recalculate_period_scores
        
        # Khởi tạo điểm cho kỳ thi đua tuần 7
        recalculate_period_scores(self.period_w7, force=True)

        # 1. Scope của Đoàn trường phải bao gồm toàn bộ các lớp trong trường
        scope = get_competition_class_scope(self.doan_truong, self.year_2026)
        self.assertEqual(scope.count(), 3)  # 10A1, 10A2, 10A3

        self.client.force_authenticate(user=self.doan_truong)

        # 2. Xem Dashboard thi đua
        res_dash = self.client.get('/api/competition/periods/dashboard/')
        self.assertEqual(res_dash.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_dash.data.get('classes', [])), 3)

        # 3. Xem Bảng xếp hạng thi đua tuần
        res_scores = self.client.get(f'/api/competition/periods/{self.period_w7.id}/scores/')
        self.assertEqual(res_scores.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_scores.data.get('scores', [])), 3)

        # 4. Xem chi tiết thi đua từng lớp bất kỳ
        res_detail = self.client.get(f'/api/competition/periods/{self.period_w7.id}/classes/{self.class_10a2.id}/detail/')
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(res_detail.data['school_class']['name'], '10A2')

        # 5. Xuất báo cáo Excel và PDF với vai trò Đoàn trường
        excel_bytes = export_competition_excel(self.period_w7.id, self.doan_truong)
        self.assertGreater(len(excel_bytes), 1000)

        pdf_bytes = export_competition_pdf(self.period_w7.id, self.doan_truong)
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))
        self.assertGreater(len(pdf_bytes), 5000)
