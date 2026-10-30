import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from core.models import User, AcademicYear, Semester
from competition.models import CompetitionPeriod, ClassCompetitionScore, ScoreCriterion
from conduct.models import (
    SchoolClass, Student, ConductRuleCategory, ConductRule,
    ViolationRecord, ViolationReviewHistory, RedStarAssignment,
)
from conduct.services import create_violation_record, adjust_or_undo_violation, can_user_deduct_directly


class DirectDeductionWorkflowTests(TestCase):
    def setUp(self):
        # 1. Setup Academic year & semester & period
        self.academic_year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
            is_current=True,
        )
        self.semester = Semester.objects.create(
            academic_year=self.academic_year,
            semester_number=1,
            start_date=date(2026, 9, 1),
            end_date=date(2027, 1, 15),
            is_current=True,
        )
        today = timezone.now().date()
        self.period = CompetitionPeriod.objects.create(
            academic_year=self.academic_year,
            semester=self.semester,
            name='Tuần 7 - Học kỳ 1',
            week_number=7,
            internal_month_number=2,
            start_date=today - timedelta(days=2),
            end_date=today + timedelta(days=4),
            is_locked=False,
            is_published=True,
        )

        # 2. Setup Class & Students
        self.school_class = SchoolClass.objects.create(
            name='10A1',
            grade=10,
            academic_year=self.academic_year,
        )
        self.student = Student.objects.create(
            school_class=self.school_class,
            student_code='HK-1001',
            full_name='Nguyễn Văn Nam',
            date_of_birth=date(2010, 1, 1),
        )

        # 3. Setup Competition Score initialized to 100.00
        self.score_obj = ClassCompetitionScore.objects.create(
            competition_period=self.period,
            school_class=self.school_class,
            base_points=Decimal('100.00'),
            bonus_points=Decimal('0.00'),
            penalty_points=Decimal('0.00'),
            total_score=Decimal('100.00'),
            rank=1,
        )

        # 4. Setup Rule & Category
        self.category = ConductRuleCategory.objects.create(name='Chuyên cần & Tác phong')
        self.rule = ConductRule.objects.create(
            category=self.category,
            code='VP-01',
            name='Đi học muộn',
            default_points_deducted=Decimal('2.00'),
        )

        # 5. Setup Users with different roles
        self.doan_truong = User.objects.create_user(
            username='doantruong_user',
            password='Password123!',
            role=User.ROLE_DOAN_TRUONG,
            full_name='Cán bộ Đoàn Trường',
            account_status=User.STATUS_APPROVED,
        )
        self.admin = User.objects.create_user(
            username='admin_user',
            password='Password123!',
            role=User.ROLE_ADMIN,
            full_name='Quản trị viên Admin',
            account_status=User.STATUS_APPROVED,
        )
        self.sao_do = User.objects.create_user(
            username='saodo_user',
            password='Password123!',
            role=User.ROLE_SAO_DO,
            full_name='Đội viên Sao đỏ',
            account_status=User.STATUS_APPROVED,
        )
        RedStarAssignment.objects.create(
            user=self.sao_do,
            student=self.student,
            scope_type=RedStarAssignment.SCOPE_CLASS,
            assigned_class=self.school_class,
            start_date=today,
            status=RedStarAssignment.STATUS_ACTIVE,
        )
        RedStarAssignment.objects.create(
            user=self.sao_do,
            student=self.student,
            scope_type=RedStarAssignment.SCOPE_CLASS,
            assigned_class=self.school_class,
            start_date=today,
            status=RedStarAssignment.STATUS_ACTIVE,
        )
        self.student_user = User.objects.create_user(
            username='student_user',
            password='Password123!',
            role=User.ROLE_HOC_SINH,
            full_name='Học sinh Nguyễn Văn Nam',
            account_status=User.STATUS_APPROVED,
        )

        self.client = APIClient()

    def test_01_doan_truong_can_record_and_deduct_directly(self):
        """1. Vai trò Đoàn trường được phép trừ điểm trực tiếp không cần duyệt."""
        self.client.force_authenticate(self.doan_truong)
        response = self.client.post('/api/conduct/violations/', {
            'school_class': self.school_class.id,
            'student': self.student.id,
            'rule': self.rule.id,
            'location': 'Cổng trường',
            'description': 'Đi muộn 15 phút',
            'occurred_at': timezone.now().isoformat(),
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(can_user_deduct_directly(self.doan_truong))
        self.assertEqual(ViolationRecord.objects.count(), 1)
        record = ViolationRecord.objects.first()
        self.assertEqual(record.status, ViolationRecord.STATUS_VERIFIED)
        self.score_obj.refresh_from_db()
        self.assertEqual(self.score_obj.penalty_points, Decimal('2.00'))
        self.assertEqual(self.score_obj.total_score, Decimal('98.00'))

    def test_02_admin_direct_deduction_success(self):
        """
        2. Admin tạo vi phạm -> trừ điểm trực tiếp thành công.
        """
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/conduct/violations/', {
            'school_class': self.school_class.id,
            'student': self.student.id,
            'rule': self.rule.id,
            'location': 'Hành lang',
            'description': 'Vi phạm tác phong ghi nhận bởi Admin',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], ViolationRecord.STATUS_VERIFIED)
        self.assertEqual(response.data['points_deducted'], 2.0)

        self.score_obj.refresh_from_db()
        self.assertEqual(self.score_obj.total_score, Decimal('98.00'))

    def test_03_sao_do_cannot_deduct_directly_only_submit_pending(self):
        """
        3. Sao đỏ cố tình gửi direct_deduct=true -> 403 Forbidden.
        Gửi bình thường -> 201 Created, status=PENDING, 0 điểm trừ, điểm lớp giữ nguyên 100.
        """
        self.client.force_authenticate(self.sao_do)

        # Cố tình yêu cầu trừ trực tiếp
        forbidden_resp = self.client.post('/api/conduct/violations/', {
            'school_class': self.school_class.id,
            'student': self.student.id,
            'rule': self.rule.id,
            'direct_deduct': True,
        }, format='json')
        self.assertEqual(forbidden_resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('chưa được cấp quyền trừ điểm', forbidden_resp.data['error'])

        # Gửi bình thường (Chờ xác minh)
        normal_resp = self.client.post('/api/conduct/violations/', {
            'school_class': self.school_class.id,
            'student': self.student.id,
            'rule': self.rule.id,
            'description': 'Sao đỏ báo cáo',
        }, format='json')
        self.assertEqual(normal_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(normal_resp.data['status'], ViolationRecord.STATUS_PENDING)
        self.assertEqual(normal_resp.data['points_deducted'], 0.0)

        self.score_obj.refresh_from_db()
        self.assertEqual(self.score_obj.total_score, Decimal('100.00'))
        self.assertEqual(self.score_obj.penalty_points, Decimal('0.00'))

    def test_04_student_cannot_report_violations(self):
        """
        4. Học sinh cố tình tạo vi phạm -> 403 Forbidden.
        """
        self.client.force_authenticate(self.student_user)
        response = self.client.post('/api/conduct/violations/', {
            'school_class': self.school_class.id,
            'rule': self.rule.id,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_05_idempotent_submission_key_prevents_duplicate_deduction(self):
        """
        5. Gửi 2 lần với cùng submission_key -> không trừ điểm 2 lần.
        """
        self.client.force_authenticate(self.admin)
        sub_key = str(uuid.uuid4())

        # Lần 1
        resp1 = self.client.post('/api/conduct/violations/', {
            'school_class': self.school_class.id,
            'student': self.student.id,
            'rule': self.rule.id,
            'submission_key': sub_key,
        }, format='json')
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

        self.score_obj.refresh_from_db()
        self.assertEqual(self.score_obj.total_score, Decimal('98.00'))

        # Lần 2 (click đúp)
        resp2 = self.client.post('/api/conduct/violations/', {
            'school_class': self.school_class.id,
            'student': self.student.id,
            'rule': self.rule.id,
            'submission_key': sub_key,
        }, format='json')
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertEqual(resp1.data['id'], resp2.data['id'])

        # Điểm thi đua KHÔNG bị trừ thêm lần nữa
        self.score_obj.refresh_from_db()
        self.assertEqual(self.score_obj.total_score, Decimal('98.00'))
        self.assertEqual(ViolationRecord.objects.count(), 1)

    def test_06_invalid_class_or_rule_no_deduction(self):
        """
        6. Chọn lớp hoặc lỗi vi phạm không tồn tại -> 400 Bad Request, điểm lớp không đổi.
        """
        self.client.force_authenticate(self.admin)
        resp = self.client.post('/api/conduct/violations/', {
            'school_class': 999999,
            'rule': self.rule.id,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        self.score_obj.refresh_from_db()
        self.assertEqual(self.score_obj.total_score, Decimal('100.00'))

    def test_07_database_rollback_on_failure(self):
        """
        7. Đảm bảo tính nguyên tử (atomic transaction): nếu có lỗi xảy ra, toàn bộ thay đổi được rollback.
        """
        with patch('competition.services.recalculate_score_for_class_at_time', side_effect=RuntimeError('Lỗi tính toán mô phỏng')):
            with self.assertRaises(RuntimeError):
                create_violation_record(
                    reporter=self.admin,
                    class_id=self.school_class.id,
                    rule_id=self.rule.id,
                    direct_deduct=True,
                )

        # Vi phạm không được lưu và điểm không đổi
        self.assertEqual(ViolationRecord.objects.count(), 0)
        self.score_obj.refresh_from_db()
        self.assertEqual(self.score_obj.total_score, Decimal('100.00'))

    def test_08_undo_violation_restores_class_score(self):
        """
        8. Hoàn tác vi phạm (Undo): Revert điểm về 0, chuyển status sang REJECTED, điểm lớp phục hồi về 100.
        """
        # Tạo vi phạm đã trừ điểm
        v = create_violation_record(
            reporter=self.admin,
            class_id=self.school_class.id,
            rule_id=self.rule.id,
            direct_deduct=True,
        )
        self.score_obj.refresh_from_db()
        self.assertEqual(self.score_obj.total_score, Decimal('98.00'))

        # Gọi API undo
        self.client.force_authenticate(self.admin)
        resp = self.client.post(f'/api/conduct/violations/{v.id}/adjust-or-undo/', {
            'action': 'undo',
            'reason': 'Nhầm lẫn số áo học sinh khi ghi nhận',
        }, format='json')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        v.refresh_from_db()
        self.assertEqual(v.status, ViolationRecord.STATUS_REJECTED)
        self.assertEqual(v.points_deducted, Decimal('0.00'))

        # Điểm lớp được khôi phục về 100
        self.score_obj.refresh_from_db()
        self.assertEqual(self.score_obj.penalty_points, Decimal('0.00'))
        self.assertEqual(self.score_obj.total_score, Decimal('100.00'))

    def test_09_adjust_violation_updates_class_score(self):
        """
        9. Điều chỉnh điểm (Adjust): thay đổi mức điểm từ 2.0 -> 1.0, status ADJUSTED, điểm lớp = 99.00.
        """
        v = create_violation_record(
            reporter=self.admin,
            class_id=self.school_class.id,
            rule_id=self.rule.id,
            direct_deduct=True,
        )
        self.score_obj.refresh_from_db()
        self.assertEqual(self.score_obj.total_score, Decimal('98.00'))

        self.client.force_authenticate(self.admin)
        resp = self.client.post(f'/api/conduct/violations/{v.id}/adjust-or-undo/', {
            'action': 'adjust',
            'adjusted_points': 1.0,
            'reason': 'Học sinh có tinh thần khắc phục, giảm 1 điểm theo quy chế',
        }, format='json')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        v.refresh_from_db()
        self.assertEqual(v.status, ViolationRecord.STATUS_ADJUSTED)
        self.assertEqual(v.points_deducted, Decimal('1.00'))

        self.score_obj.refresh_from_db()
        self.assertEqual(self.score_obj.penalty_points, Decimal('1.00'))
        self.assertEqual(self.score_obj.total_score, Decimal('99.00'))

    def test_10_admin_query_history_and_filter_by_reporter_role(self):
        """
        10. Admin có thể tra cứu lịch sử thẩm định và lọc danh sách vi phạm theo người ghi nhận / vai trò.
        """
        # Tạo 1 bản ghi bởi Admin (đã được xác minh trực tiếp)
        v_admin = create_violation_record(
            reporter=self.admin,
            class_id=self.school_class.id,
            rule_id=self.rule.id,
            direct_deduct=True,
        )
        # Tạo 1 bản ghi bởi Sao đỏ (chờ xác minh)
        v_sd = create_violation_record(
            reporter=self.sao_do,
            class_id=self.school_class.id,
            rule_id=self.rule.id,
            direct_deduct=False,
        )

        self.client.force_authenticate(self.admin)

        # Lọc theo vai trò ADMIN
        resp_admin = self.client.get('/api/conduct/violations/?reporter_role=ADMIN')
        self.assertEqual(resp_admin.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in resp_admin.data['results']]
        self.assertIn(v_admin.id, ids)
        self.assertNotIn(v_sd.id, ids)

        # Lọc theo vai trò SAO_DO
        resp_sd = self.client.get('/api/conduct/violations/?reporter_role=SAO_DO')
        self.assertEqual(resp_sd.status_code, status.HTTP_200_OK)
        ids_sd = [item['id'] for item in resp_sd.data['results']]
        self.assertIn(v_sd.id, ids_sd)
        self.assertNotIn(v_admin.id, ids_sd)

        # Xem chi tiết bản ghi kiểm tra review history
        resp_detail = self.client.get(f'/api/conduct/violations/{v_admin.id}/')
        self.assertEqual(resp_detail.status_code, status.HTTP_200_OK)
        self.assertTrue(len(resp_detail.data['reviews']) >= 1)
        hist = resp_detail.data['reviews'][0]
        self.assertEqual(hist['new_status'], ViolationRecord.STATUS_VERIFIED)
        self.assertEqual(float(hist['score_before']), 100.0)
        self.assertEqual(float(hist['score_after']), 98.0)
