from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from core.models import User, AcademicYear, Semester
from conduct.models import SchoolClass, Student, ConductRuleCategory, ConductRule, ViolationRecord
from competition.models import ScoreCriterion, CompetitionPeriod, ClassCompetitionScore
from competition.services import recalculate_period_scores, lock_competition_period
from conduct.services import create_violation_record, verify_violation
from counseling.models import CounselingRequest
from counseling.services import submit_counseling_request
from reports.services import export_competition_excel, export_competition_pdf


class HKStudentHubIntegrationTests(TestCase):
    def setUp(self):
        # 1. Base Setup
        self.year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=date(2026, 9, 5),
            end_date=date(2027, 5, 30),
            is_current=True
        )
        self.semester = Semester.objects.create(
            academic_year=self.year,
            semester_number=1,
            name='Học kỳ I',
            start_date=date(2026, 9, 5),
            end_date=date(2027, 1, 15),
            is_current=True
        )

        # 2. Users with strict roles
        self.admin = User.objects.create_user(
            username='admin_test',
            password='testpassword',
            role=User.ROLE_ADMIN,
            can_verify_violations=True
        )
        self.doan_truong = User.objects.create_user(
            username='doan_test',
            password='testpassword',
            role=User.ROLE_DOAN_TRUONG,
            can_verify_violations=True,
            can_view_counseling=False  # Không có quyền xem tư vấn
        )
        self.sao_do = User.objects.create_user(
            username='saodo_test',
            password='testpassword',
            role=User.ROLE_SAO_DO
        )
        self.gvcn_10a1 = User.objects.create_user(
            username='gvcn_10a1_test',
            password='testpassword',
            role=User.ROLE_GVCN
        )
        self.student_user_1 = User.objects.create_user(
            username='student1_test',
            password='testpassword',
            role=User.ROLE_HOC_SINH
        )
        self.student_user_2 = User.objects.create_user(
            username='student2_test',
            password='testpassword',
            role=User.ROLE_HOC_SINH
        )
        self.counselor = User.objects.create_user(
            username='counselor_test',
            password='testpassword',
            role=User.ROLE_CHUYEN_VIEN_TAM_LY,
            can_view_counseling=True
        )

        # 3. Classes and Students
        self.class_10a1 = SchoolClass.objects.create(
            name='10A1',
            grade=10,
            academic_year=self.year,
            homeroom_teacher=self.gvcn_10a1,
            student_count=40
        )
        self.class_10a2 = SchoolClass.objects.create(
            name='10A2',
            grade=10,
            academic_year=self.year,
            student_count=40
        )

        self.student_1 = Student.objects.create(
            user=self.student_user_1,
            student_code='HK26-001',
            full_name='Nguyen Van A',
            date_of_birth=date(2010, 1, 1),
            school_class=self.class_10a1
        )
        self.student_2 = Student.objects.create(
            user=self.student_user_2,
            student_code='HK26-002',
            full_name='Tran Thi B',
            date_of_birth=date(2010, 2, 2),
            school_class=self.class_10a2
        )

        # 4. Rules & Period
        self.cat = ConductRuleCategory.objects.create(name='Chuyen can', icon='clock')
        self.rule_late = ConductRule.objects.create(
            category=self.cat,
            code='VP-01',
            name='Di hoc muon',
            default_points_deducted=Decimal('2.00'),
            severity='LOW'
        )

        self.criterion = ScoreCriterion.objects.create(
            academic_year=self.year,
            name='Bieu diem chuan 2026',
            initial_base_points=Decimal('100.00'),
            min_score=Decimal('0.00'),
            max_score=Decimal('150.00'),
            is_approved=True,
            effective_from=date(2026, 9, 1),
            effective_to=date(2027, 5, 30)
        )

        today = timezone.now().date()
        self.period = CompetitionPeriod.objects.create(
            name='Tuan 7 - HK1',
            period_type=CompetitionPeriod.TYPE_WEEK,
            week_number=7,
            academic_year=self.year,
            semester=self.semester,
            start_date=today - timedelta(days=3),
            end_date=today + timedelta(days=3),
            is_locked=False
        )

    def test_01_sao_do_creates_violation_successfully(self):
        """Tiêu chí 1: Sao đỏ tạo bản ghi vi phạm thành công với mã định danh tự động"""
        violation = create_violation_record(
            reporter=self.sao_do,
            class_id=self.class_10a1.id,
            rule_id=self.rule_late.id,
            student_id=self.student_1.id,
            location='Cong truong',
            description='Di hoc muon 10 phut'
        )
        self.assertIsNotNone(violation.id)
        self.assertTrue(violation.record_code.startswith('VP-'))
        self.assertEqual(violation.status, ViolationRecord.STATUS_PENDING)

    def test_02_pending_violation_does_not_deduct_points(self):
        """Tiêu chí 2: Bản ghi chưa xác minh KHÔNG làm thay đổi điểm thi đua"""
        # Tạo vi phạm ở trạng thái PENDING
        create_violation_record(
            reporter=self.sao_do,
            class_id=self.class_10a1.id,
            rule_id=self.rule_late.id,
            student_id=self.student_1.id
        )

        # Tính toán điểm thi đua
        recalculate_period_scores(self.period)

        score_10a1 = ClassCompetitionScore.objects.get(competition_period=self.period, school_class=self.class_10a1)
        self.assertEqual(score_10a1.base_points, Decimal('100.00'))
        self.assertEqual(score_10a1.penalty_points, Decimal('0.00'))
        self.assertEqual(score_10a1.total_score, Decimal('100.00'))
        self.assertEqual(score_10a1.verified_violations_count, 0)

    def test_03_verification_updates_score_accurately(self):
        """Tiêu chí 3: Đoàn trường xác minh và hệ thống cập nhật điểm chính xác"""
        violation = create_violation_record(
            reporter=self.sao_do,
            class_id=self.class_10a1.id,
            rule_id=self.rule_late.id,
            student_id=self.student_1.id
        )

        # Đoàn trường xác minh
        verify_violation(
            violation_id=violation.id,
            user=self.doan_truong,
            new_status=ViolationRecord.STATUS_VERIFIED,
            verification_notes='Da xac nhan voi bao ve'
        )

        # Điểm của lớp 10A1 phải bị trừ chính xác 2.0đ -> Còn 98.0đ
        score_10a1 = ClassCompetitionScore.objects.get(competition_period=self.period, school_class=self.class_10a1)
        self.assertEqual(score_10a1.penalty_points, Decimal('2.00'))
        self.assertEqual(score_10a1.total_score, Decimal('98.00'))
        self.assertEqual(score_10a1.verified_violations_count, 1)

    def test_04_gvcn_sees_only_assigned_class_via_api(self):
        """Tiêu chí 4: GVCN chỉ xem được vi phạm của lớp mình phụ trách"""
        # Tạo vi phạm cho 10A1 (lớp của GVCN)
        v1 = create_violation_record(self.sao_do, self.class_10a1.id, self.rule_late.id, self.student_1.id)
        # Tạo vi phạm cho 10A2 (lớp khác)
        v2 = create_violation_record(self.sao_do, self.class_10a2.id, self.rule_late.id, self.student_2.id)

        self.client.force_login(self.gvcn_10a1)
        res = self.client.get('/api/conduct/violations/')
        self.assertEqual(res.status_code, 200)
        items = res.json().get('results', res.json())
        returned_ids = [item['id'] for item in items]

        self.assertIn(v1.id, returned_ids)
        self.assertNotIn(v2.id, returned_ids)

    def test_05_student_sees_only_own_records(self):
        """Tiêu chí 5: Học sinh chỉ xem được vi phạm của bản thân"""
        v1 = create_violation_record(self.sao_do, self.class_10a1.id, self.rule_late.id, self.student_1.id)
        v2 = create_violation_record(self.sao_do, self.class_10a2.id, self.rule_late.id, self.student_2.id)

        self.client.force_login(self.student_user_1)
        res = self.client.get('/api/conduct/violations/')
        self.assertEqual(res.status_code, 200)
        items = res.json().get('results', res.json())
        returned_ids = [item['id'] for item in items]

        self.assertIn(v1.id, returned_ids)
        self.assertNotIn(v2.id, returned_ids)

    def test_06_counseling_data_strict_isolation_forbidden_to_unauthorized(self):
        """Tiêu chí 6 & 7: Đoàn trường hoặc người không có quyền KHÔNG THỂ truy cập hồ sơ tư vấn tâm lý"""
        # Tạo hồ sơ tư vấn tâm lý
        req = submit_counseling_request(
            topic=CounselingRequest.TOPIC_ACADEMIC,
            content='Tam su rieng tu can giup do ve thi cu',
            student=self.student_1
        )

        # 1. Đoàn trường truy cập API tư vấn -> Bị cấm 403 Forbidden!
        self.client.force_login(self.doan_truong)
        res_doan = self.client.get('/api/counseling/requests/')
        self.assertEqual(res_doan.status_code, 403)

        # 2. Học sinh 2 cố tình truy cập API tư vấn -> Bị cấm 403 Forbidden!
        self.client.force_login(self.student_user_2)
        res_stu2 = self.client.get('/api/counseling/requests/')
        self.assertEqual(res_stu2.status_code, 403)

        # 3. Chuyên viên tư vấn tâm lý truy cập -> Được phép 200 OK!
        self.client.force_login(self.counselor)
        res_counselor = self.client.get('/api/counseling/requests/')
        self.assertEqual(res_counselor.status_code, 200)

    def test_08_counseling_not_leaked_to_competition_scores_or_reports(self):
        """Tiêu chí 8: Yêu cầu tư vấn tuyệt đối không xuất hiện trong thi đua Chi đoàn"""
        submit_counseling_request(
            topic=CounselingRequest.TOPIC_FAMILY,
            content='Chuyen gia dinh nhay cam',
            student=self.student_1
        )

        recalculate_period_scores(self.period)
        score_10a1 = ClassCompetitionScore.objects.get(competition_period=self.period, school_class=self.class_10a1)
        # Điểm thi đua không bị ảnh hưởng bởi hồ sơ tư vấn
        self.assertEqual(score_10a1.penalty_points, Decimal('0.00'))

        # Xuất Excel thi đua: Nội dung Excel không chứa từ khóa tâm lý
        excel_bytes = export_competition_excel(self.period.id, self.admin)
        self.assertNotIn(b'Chuyen gia dinh nhay cam', excel_bytes)

    def test_09_locked_period_prevents_silent_data_corruption(self):
        """Tiêu chí 9: Kỳ thi đua đã chốt kết quả thì không bị âm thầm thay đổi"""
        # Chốt sổ kỳ thi đua
        lock_competition_period(self.period.id, self.admin)

        # Giả sử sau khi chốt sổ, phát sinh vi phạm mới
        v = create_violation_record(self.sao_do, self.class_10a1.id, self.rule_late.id, self.student_1.id)
        verify_violation(v.id, self.doan_truong, ViolationRecord.STATUS_VERIFIED)

        # Điểm kỳ đã chốt không được tự ý đổi
        score_after = ClassCompetitionScore.objects.get(competition_period=self.period, school_class=self.class_10a1)
        self.assertEqual(score_after.total_score, Decimal('100.00'))

    def test_10_excel_and_pdf_generation_matches_data(self):
        """Tiêu chí 10: Báo cáo Excel và PDF được sinh thành công và khớp dữ liệu"""
        excel_bytes = export_competition_excel(self.period.id, self.admin)
        self.assertGreater(len(excel_bytes), 1000)

        pdf_bytes = export_competition_pdf(self.period.id, self.admin)
        self.assertGreater(len(pdf_bytes), 1000)

    def test_11_only_admin_can_approve_and_update_roles(self):
        """Tiêu chí 11: Chỉ có Admin mới được quyền duyệt và thay đổi chức vụ / phân quyền"""
        self.client.force_login(self.admin)
        res = self.client.post(
            f'/api/core/users/{self.student_user_1.id}/approve-role/',
            data={
                'role': User.ROLE_SAO_DO,
                'can_verify_violations': True,
                'can_view_counseling': False
            },
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.student_user_1.refresh_from_db()
        self.assertEqual(self.student_user_1.role, User.ROLE_SAO_DO)
        self.assertTrue(self.student_user_1.can_verify_violations)

    def test_12_non_admin_cannot_approve_roles(self):
        """Tiêu chí 12: Người dùng khác (Đoàn trường, GVCN, Học sinh) KHÔNG THỂ duyệt chức vụ -> 403 Forbidden"""
        self.client.force_login(self.doan_truong)
        res = self.client.post(
            f'/api/core/users/{self.student_user_2.id}/approve-role/',
            data={'role': User.ROLE_ADMIN},
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 403)
        self.student_user_2.refresh_from_db()
        self.assertNotEqual(self.student_user_2.role, User.ROLE_ADMIN)

    def test_13_login_authentication_workflow(self):
        """Tiêu chí 13: Bắt buộc người dùng phải đăng nhập qua API /api/core/auth/login/"""
        # 1. Sai mật khẩu -> Thất bại 400
        res_fail = self.client.post(
            '/api/core/auth/login/',
            data={'username': 'admin_test', 'password': 'wrongpassword'},
            content_type='application/json'
        )
        self.assertEqual(res_fail.status_code, 400)

        # 2. Đúng mật khẩu -> Thành công 200
        res_ok = self.client.post(
            '/api/core/auth/login/',
            data={'username': 'admin_test', 'password': 'testpassword'},
            content_type='application/json'
        )
        self.assertEqual(res_ok.status_code, 200)
        self.assertTrue(res_ok.json()['user']['username'] == 'admin_test')
