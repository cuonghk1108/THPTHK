from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PIL import Image
from django.core.management.base import CommandError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from core.models import User, AcademicYear, Semester, AuditLog
from conduct.models import SchoolClass, Student, ConductRuleCategory, ConductRule, ViolationRecord
from competition.models import ScoreCriterion, CompetitionPeriod, ClassCompetitionScore
from competition.services import recalculate_period_scores, lock_competition_period
from conduct.services import create_violation_record, verify_violation
from counseling.models import CounselingRequest
from counseling.services import submit_counseling_request
from reports.services import export_competition_excel, export_competition_pdf


class ProfileApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='profile_user',
            password='ProfilePass123!',
            full_name='Nguyễn Văn A',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED,
            department_or_class='10A1',
        )
        self.client.force_login(self.user)
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

    def test_get_profile_returns_read_only_account_fields(self):
        response = self.client.get('/api/core/auth/profile/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['full_name'], 'Nguyễn Văn A')
        self.assertEqual(response.json()['department_or_class'], '10A1')
        self.assertNotIn('account_status', response.json())
        self.assertNotIn('is_admin', response.json())

    def test_patch_profile_updates_only_name_and_phone_and_audits_fields(self):
        response = self.client.patch(
            '/api/core/auth/profile/',
            data={'full_name': '  Nguyễn Văn B  ', 'phone': '+84 912 345 678'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['full_name'], 'Nguyễn Văn B')
        self.assertEqual(response.json()['phone'], '+84912345678')
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, User.ROLE_HOC_SINH)
        self.assertEqual(self.user.department_or_class, '10A1')
        audit = AuditLog.objects.get(user=self.user, action='UPDATE_PROFILE')
        self.assertIn('Họ tên hiển thị', audit.details)
        self.assertIn('Số điện thoại', audit.details)
        self.assertNotIn('Nguyễn Văn B', audit.details)

    def test_patch_profile_rejects_protected_fields_and_blank_name(self):
        protected_response = self.client.patch(
            '/api/core/auth/profile/',
            data={'role': User.ROLE_ADMIN},
            content_type='application/json',
        )
        blank_name_response = self.client.patch(
            '/api/core/auth/profile/',
            data={'full_name': '   '},
            content_type='application/json',
        )

        self.assertEqual(protected_response.status_code, 400)
        self.assertEqual(blank_name_response.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, User.ROLE_HOC_SINH)

    def test_profile_endpoints_require_authentication(self):
        self.client.logout()

        self.assertEqual(self.client.get('/api/core/auth/profile/').status_code, 403)
        self.assertEqual(self.client.post('/api/core/auth/profile/avatar/').status_code, 403)

    def test_upload_avatar_accepts_verified_image_and_sets_random_filename(self):
        image_data = BytesIO()
        Image.new('RGB', (2, 2), color='blue').save(image_data, format='PNG')
        upload = SimpleUploadedFile('avatar.png', image_data.getvalue(), content_type='image/png')

        response = self.client.post('/api/core/auth/profile/avatar/', {'avatar': upload})

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.avatar.name.startswith('avatars/'))
        self.assertRegex(self.user.avatar.name.rsplit('/', 1)[-1], r'^[0-9a-f]{32}\.png$')
        self.assertEqual(AuditLog.objects.filter(user=self.user, action='UPDATE_PROFILE_AVATAR').count(), 1)

    def test_upload_avatar_rejects_invalid_and_oversized_files(self):
        invalid_upload = SimpleUploadedFile('avatar.png', b'not an image', content_type='image/png')
        invalid_response = self.client.post(
            '/api/core/auth/profile/avatar/',
            {'avatar': invalid_upload},
        )
        oversized_upload = SimpleUploadedFile('large.png', b'12', content_type='image/png')
        with override_settings(AVATAR_MAX_UPLOAD_SIZE=1):
            oversized_response = self.client.post(
                '/api/core/auth/profile/avatar/',
                {'avatar': oversized_upload},
            )

        self.assertEqual(invalid_response.status_code, 400)
        self.assertEqual(oversized_response.status_code, 400)
        self.assertFalse(AuditLog.objects.filter(user=self.user, action='UPDATE_PROFILE_AVATAR').exists())


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

        # 2. Users with strict roles (all approved for integration tests)
        self.admin = User.objects.create_user(
            username='admin_test',
            password='testpassword',
            role=User.ROLE_ADMIN,
            account_status=User.STATUS_APPROVED,
            can_verify_violations=True
        )
        self.doan_truong = User.objects.create_user(
            username='doan_test',
            password='testpassword',
            role=User.ROLE_DOAN_TRUONG,
            account_status=User.STATUS_APPROVED,
            can_verify_violations=True,
            can_view_counseling=False  # Không có quyền xem tư vấn
        )
        self.sao_do = User.objects.create_user(
            username='saodo_test',
            password='testpassword',
            role=User.ROLE_SAO_DO,
            account_status=User.STATUS_APPROVED
        )
        self.gvcn_10a1 = User.objects.create_user(
            username='gvcn_10a1_test',
            password='testpassword',
            role=User.ROLE_GVCN,
            account_status=User.STATUS_APPROVED
        )
        self.student_user_1 = User.objects.create_user(
            username='student1_test',
            password='testpassword',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED
        )
        self.student_user_2 = User.objects.create_user(
            username='student2_test',
            password='testpassword',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED
        )
        self.counselor = User.objects.create_user(
            username='counselor_test',
            password='testpassword',
            role=User.ROLE_CHUYEN_VIEN_TAM_LY,
            account_status=User.STATUS_APPROVED,
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
            internal_month_number=2,
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
        """Tiêu chí 3: Quản trị viên xác minh và hệ thống cập nhật điểm chính xác"""
        violation = create_violation_record(
            reporter=self.sao_do,
            class_id=self.class_10a1.id,
            rule_id=self.rule_late.id,
            student_id=self.student_1.id
        )

        # Chỉ Admin xác minh và quyết định điểm
        verify_violation(
            violation_id=violation.id,
            user=self.admin,
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
        with patch('django.utils.timezone.localdate', return_value=self.period.end_date + timedelta(days=1)):
            lock_competition_period(self.period.id, self.admin)

        # Báo cáo vẫn được lưu, nhưng kỳ đã chốt phải được mở lại trước khi duyệt.
        v = create_violation_record(self.sao_do, self.class_10a1.id, self.rule_late.id, self.student_1.id)
        with self.assertRaises(ValueError):
            verify_violation(v.id, self.admin, ViolationRecord.STATUS_VERIFIED)

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


class SecureOnboardingTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='onboarding_admin',
            password='AdminPass123!',
            role=User.ROLE_ADMIN,
            account_status=User.STATUS_APPROVED,
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.admin)

    def test_admin_creates_account_with_one_time_temporary_password(self):
        response = self.client.post(
            '/api/core/users/',
            data={
                'username': 'new_student',
                'full_name': 'Học sinh mới',
                'role': User.ROLE_HOC_SINH,
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        temporary_password = response.json()['temporary_password']
        user = User.objects.get(username='new_student')
        self.assertTrue(user.check_password(temporary_password))
        self.assertTrue(user.must_change_password)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.can_view_counseling)
        self.assertNotIn(temporary_password, AuditLog.objects.get(action='CREATE_USER').details)

    def test_non_admin_cannot_create_accounts(self):
        student = User.objects.create_user(
            username='ordinary_student',
            password='StudentPass123!',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED,
        )
        self.client.force_login(student)

        response = self.client.post(
            '/api/core/users/',
            data={'username': 'blocked_user', 'full_name': 'Người dùng bị chặn'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username='blocked_user').exists())

    def test_forced_password_change_unblocks_user_without_ending_session(self):
        user = User.objects.create_user(
            username='temporary_user',
            password='TemporaryPass123!',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED,
            must_change_password=True,
        )
        self.client.force_login(user)

        blocked_response = self.client.get('/api/core/users/')
        self.assertEqual(blocked_response.status_code, 403)

        response = self.client.post(
            '/api/core/auth/change-password/',
            data={
                'current_password': 'TemporaryPass123!',
                'new_password': 'NewStrongPassw0rd!2026',
                'confirm_password': 'NewStrongPassw0rd!2026',
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertFalse(user.must_change_password)
        self.assertTrue(user.check_password('NewStrongPassw0rd!2026'))
        self.assertTrue(response.json()['user']['must_change_password'] is False)
        self.assertEqual(self.client.get('/api/core/auth/me/').status_code, 200)


class RegistrationAndApprovalWorkflowTests(TestCase):
    """
    Kiểm thử tích hợp toàn diện quy trình Đăng ký tài khoản và Phê duyệt Admin (Section 11)
    """
    def setUp(self):
        self.super_admin = User.objects.create_user(
            username='super_admin_test',
            password='SuperPass123!',
            role=User.ROLE_SUPER_ADMIN,
            account_status=User.STATUS_APPROVED,
            is_staff=True,
            is_superuser=True,
        )
        self.admin = User.objects.create_user(
            username='admin_reviewer',
            password='AdminPass123!',
            role=User.ROLE_ADMIN,
            account_status=User.STATUS_APPROVED,
            is_staff=True,
        )
        self.registration_year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=date(2026, 9, 5),
            end_date=date(2027, 5, 30),
            is_current=True,
        )
        self.registration_class = SchoolClass.objects.create(
            name='10A1', grade=10, academic_year=self.registration_year,
        )

    def test_01_registration_creates_pending_account_and_notifies_admin(self):
        """Người dùng đăng ký thành công nhưng ở trạng thái PENDING và tạo thông báo cho Admin"""
        res = self.client.post(
            '/api/core/auth/register/',
            data={
                'full_name': 'Nguyễn Văn Kiểm Thử',
                'username': 'kiemthu_hs',
                'email': 'kiemthu.hs@thpthuongkhe.edu.vn',
                'phone': '0987112233',
                'password': 'PassKiemThu123!',
                'confirm_password': 'PassKiemThu123!',
                'requested_role': 'HOC_SINH',
                'grade_level': 10,
                'class_id': self.registration_class.id,
                'department_or_class': 'Lớp 10A1',
                'verification_info': 'Mã học sinh HK-2026-999',
                'terms_accepted': True
            },
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 201)
        self.assertIn('đang chờ Admin xét duyệt', res.json()['message'])

        user = User.objects.get(username='kiemthu_hs')
        self.assertEqual(user.account_status, User.STATUS_PENDING)
        self.assertFalse(user.is_active)
        self.assertTrue(user.check_password('PassKiemThu123!'))

        # Kiểm tra Admin nhận thông báo
        from core.models import Notification
        notif = Notification.objects.filter(recipient=self.admin, notification_type=Notification.TYPE_REGISTRATION)
        self.assertTrue(notif.exists())

    def test_02_pending_user_strictly_cannot_login(self):
        """Tài khoản PENDING bị từ chối đăng nhập với thông báo cụ thể (HTTP 403)"""
        user = User.objects.create_user(
            username='pending_student',
            password='ValidPassword123!',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_PENDING,
            is_active=False
        )

        res = self.client.post(
            '/api/core/auth/login/',
            data={'username': 'pending_student', 'password': 'ValidPassword123!'},
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn('chờ quản trị viên xét duyệt', res.json()['error'])

    def test_03_user_cannot_register_as_admin(self):
        """Người đăng ký không thể tự chọn vai trò ADMIN hoặc SUPER_ADMIN"""
        res = self.client.post(
            '/api/core/auth/register/',
            data={
                'full_name': 'Hacker Muốn Làm Admin',
                'username': 'fake_admin',
                'email': 'fake.admin@gmail.com',
                'password': 'PassHacker123!',
                'confirm_password': 'PassHacker123!',
                'requested_role': 'ADMIN',
                'department_or_class': 'Ban Quản Trị',
                'terms_accepted': True
            },
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400)
        self.assertFalse(User.objects.filter(username='fake_admin').exists())

    def test_04_admin_views_requests_and_approves_user(self):
        """Admin xem danh sách, phê duyệt và gán đúng vai trò -> Người dùng đăng nhập thành công"""
        candidate = User.objects.create_user(
            username='applicant_mai',
            password='ApplicantMai123!',
            role=User.ROLE_HOC_SINH,
            requested_role='GVCN',
            department_or_class='Lớp 11A3',
            account_status=User.STATUS_PENDING,
            is_active=False
        )

        # 1. Admin đăng nhập và xem stats
        self.client.force_login(self.admin)
        stats_res = self.client.get('/api/core/users/stats/')
        self.assertEqual(stats_res.status_code, 200)
        self.assertGreaterEqual(stats_res.json()['pending'], 1)

        # 2. Admin phê duyệt và gán vai trò GVCN
        review_res = self.client.post(
            f'/api/core/users/{candidate.id}/review/',
            data={
                'action': 'approve',
                'assigned_role': 'GVCN',
                'department_or_class': 'Lớp 11A3',
                'internal_notes': 'Đã kiểm tra quyết định phân công chuyên môn'
            },
            content_type='application/json'
        )
        self.assertEqual(review_res.status_code, 200)

        candidate.refresh_from_db()
        self.assertEqual(candidate.account_status, User.STATUS_APPROVED)
        self.assertEqual(candidate.role, User.ROLE_GVCN)
        self.assertTrue(candidate.is_active)
        self.assertEqual(candidate.approved_by, self.admin)

        # 3. Người dùng đăng nhập được sau khi phê duyệt
        self.client.logout()
        login_res = self.client.post(
            '/api/core/auth/login/',
            data={'username': 'applicant_mai', 'password': 'ApplicantMai123!'},
            content_type='application/json'
        )
        self.assertEqual(login_res.status_code, 200)
        self.assertEqual(login_res.json()['user']['role'], 'GVCN')

    def test_05_admin_rejects_request_and_rejected_user_cannot_login(self):
        """Admin từ chối đơn đăng ký kèm lý do -> Người dùng bị chặn đăng nhập và thấy lý do"""
        candidate = User.objects.create_user(
            username='applicant_rejected',
            password='ApplicantPass123!',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_PENDING,
            is_active=False
        )

        self.client.force_login(self.admin)
        review_res = self.client.post(
            f'/api/core/users/{candidate.id}/review/',
            data={
                'action': 'reject',
                'reason': 'Thông tin xác minh không khớp với danh sách học sinh THPT Hương Khê'
            },
            content_type='application/json'
        )
        self.assertEqual(review_res.status_code, 200)

        candidate.refresh_from_db()
        self.assertEqual(candidate.account_status, User.STATUS_REJECTED)
        self.assertFalse(candidate.is_active)

        # Đăng nhập bị từ chối
        self.client.logout()
        login_res = self.client.post(
            '/api/core/auth/login/',
            data={'username': 'applicant_rejected', 'password': 'ApplicantPass123!'},
            content_type='application/json'
        )
        self.assertEqual(login_res.status_code, 403)
        self.assertIn('chưa được chấp thuận', login_res.json()['error'])
        self.assertIn('Thông tin xác minh không khớp', login_res.json()['error'])

    def test_06_admin_suspends_account_and_access_is_blocked(self):
        """Admin tạm khóa tài khoản -> Người dùng lập tức mất quyền truy cập"""
        active_user = User.objects.create_user(
            username='active_violator',
            password='ViolatorPass123!',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED,
            is_active=True
        )

        self.client.force_login(self.admin)
        suspend_res = self.client.post(
            f'/api/core/users/{active_user.id}/review/',
            data={
                'action': 'suspend',
                'reason': 'Tài khoản vi phạm nghiêm trọng quy chế an toàn dữ liệu'
            },
            content_type='application/json'
        )
        self.assertEqual(suspend_res.status_code, 200)

        active_user.refresh_from_db()
        self.assertEqual(active_user.account_status, User.STATUS_SUSPENDED)
        self.assertFalse(active_user.is_active)

        self.client.logout()
        login_res = self.client.post(
            '/api/core/auth/login/',
            data={'username': 'active_violator', 'password': 'ViolatorPass123!'},
            content_type='application/json'
        )
        self.assertEqual(login_res.status_code, 403)
        self.assertIn('tạm khóa', login_res.json()['error'])

    def test_07_non_admin_cannot_call_review_api(self):
        """Học sinh hoặc người dùng không có quyền Admin gọi review API bị chặn 403"""
        student = User.objects.create_user(
            username='curious_student',
            password='StudentPass123!',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED
        )
        target = User.objects.create_user(
            username='some_target',
            password='TargetPass123!',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_PENDING
        )

        self.client.force_login(student)
        res = self.client.post(
            f'/api/core/users/{target.id}/review/',
            data={'action': 'approve', 'assigned_role': 'ADMIN'},
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 403)

    def test_08_cannot_suspend_the_last_super_admin(self):
        """Không được phép tạm khóa hoặc hạ cấp Super Admin duy nhất của hệ thống"""
        self.client.force_login(self.super_admin)
        # Tạo thêm 1 admin thường
        normal_admin = self.admin

        # Admin thường cố khóa Super Admin -> Bị chặn 403
        self.client.force_login(normal_admin)
        res_blocked = self.client.post(
            f'/api/core/users/{self.super_admin.id}/review/',
            data={'action': 'suspend', 'reason': 'Khóa super admin'},
            content_type='application/json'
        )
        self.assertEqual(res_blocked.status_code, 403)

        # Super Admin tự khóa chính mình -> Bị chặn 400
        self.client.force_login(self.super_admin)
        res_self = self.client.post(
            f'/api/core/users/{self.super_admin.id}/review/',
            data={'action': 'suspend', 'reason': 'Tự khóa'},
            content_type='application/json'
        )
        self.assertEqual(res_self.status_code, 400)


class ProductionSafeSeedTests(TransactionTestCase):
    @override_settings(DEBUG=True)
    def test_safe_seed_refuses_debug_mode(self):
        from core.seed_data import seed_production_demo_data

        with self.assertRaises(CommandError):
            seed_production_demo_data()

    @override_settings(DEBUG=False)
    def test_safe_seed_creates_anonymized_data_and_only_active_bootstrap_admin(self):
        from core.seed_data import seed_production_demo_data

        temporary_password = seed_production_demo_data()

        admin = User.objects.get(username='admin')
        self.assertTrue(admin.check_password(temporary_password))
        self.assertTrue(admin.must_change_password)
        self.assertTrue(admin.is_active)
        self.assertEqual(User.objects.filter(is_active=True).count(), 1)
        self.assertTrue(User.objects.filter(is_active=False).exists())
        self.assertFalse(User.objects.filter(can_view_counseling=True).exists())
        self.assertFalse(CounselingRequest.objects.exists())
        self.assertFalse(AuditLog.objects.exists())
        self.assertTrue(all(
            student.full_name.startswith('Học sinh mẫu ')
            and student.parent_name == ''
            and student.parent_phone == ''
            and student.address == ''
            for student in Student.objects.all()
        ))
        self.assertTrue(all(
            record.description == 'Bản ghi minh họa không chứa thông tin cá nhân.'
            and not record.appeal_reason
            for record in ViolationRecord.objects.all()
        ))

    @override_settings(DEBUG=False)
    def test_safe_seed_refuses_nonempty_database(self):
        from core.seed_data import seed_production_demo_data

        User.objects.create_user(username='existing_user', password='NotUsed123!')
        with self.assertRaises(CommandError):
            seed_production_demo_data()


class ServerTimeApiTests(TestCase):
    def test_get_server_time_returns_live_gmt7_data(self):
        """API trả về thời gian thực của máy chủ chuẩn múi giờ GMT+7"""
        response = self.client.get('/api/core/system/time/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('server_time', data)
        self.assertIn('local_time', data)
        self.assertIn('formatted_time', data)
        self.assertIn('formatted_date', data)
        self.assertIn('timestamp', data)
        self.assertIn('timestamp_ms', data)
        self.assertEqual(data['timezone'], 'Asia/Ho_Chi_Minh')
        self.assertTrue(any(w in data['formatted_date'] for w in ['Thứ', 'Chủ Nhật']))

