from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from core.models import User, AcademicYear, AuditLog, ApprovalLog
from competition.models import CompetitionPeriod
from conduct.models import SchoolClass, Student, ConductRuleCategory, ConductRule, ViolationRecord, RedStarAssignment, RedStarReport


class StudentApprovalAndRedStarSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.academic_year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=date(2026, 9, 1),
            end_date=date(2027, 5, 31),
            is_current=True
        )
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        CompetitionPeriod.objects.create(
            academic_year=self.academic_year,
            name='Tuần kiểm thử hiện tại',
            period_type=CompetitionPeriod.TYPE_WEEK,
            week_number=7,
            internal_month_number=2,
            start_date=week_start,
            end_date=week_start + timedelta(days=6),
            is_locked=False,
        )
        self.class_10a1 = SchoolClass.objects.create(
            name='10A1',
            grade=10,
            academic_year=self.academic_year,
            student_count=40
        )
        self.class_10a2 = SchoolClass.objects.create(
            name='10A2',
            grade=10,
            academic_year=self.academic_year,
            student_count=42
        )
        self.class_11a1 = SchoolClass.objects.create(
            name='11A1',
            grade=11,
            academic_year=self.academic_year,
            student_count=38
        )

        self.category = ConductRuleCategory.objects.create(
            name='Kỷ luật & Nền nếp chung',
            order=1
        )
        self.rule = ConductRule.objects.create(
            category=self.category,
            code='VP-01',
            name='Đi học muộn không phép',
            default_points_deducted=Decimal('2.00'),
            severity='LOW'
        )

        # 1. Admin
        self.admin = User.objects.create_user(
            username='admin_test',
            password='Password123!',
            email='admin@thpthuongkhe.edu.vn',
            full_name='Quản trị viên Hệ thống',
            role=User.ROLE_ADMIN,
            account_status=User.STATUS_APPROVED,
            is_active=True
        )

        # 2. Đoàn trường có quyền duyệt tài khoản và quản lý Sao đỏ
        self.doan_truong_with_perms = User.objects.create_user(
            username='doan_truong_full',
            password='Password123!',
            email='doantruong1@thpthuongkhe.edu.vn',
            full_name='Bí thư Đoàn trường',
            role=User.ROLE_DOAN_TRUONG,
            account_status=User.STATUS_APPROVED,
            is_active=True,
            doan_truong_permissions=[
                'student_accounts.view',
                'student_accounts.approve',
                'student_accounts.reject',
                'student_accounts.view_all_classes',
                'red_star.view',
                'red_star.assign',
                'red_star.revoke',
                'discipline.view',
                'discipline.report',
                'discipline.process',
                'audit_logs.view',
            ]
        )

        # 3. Đoàn trường KHÔNG có quyền duyệt tài khoản và KHÔNG có quyền phân công Sao đỏ
        self.doan_truong_no_perms = User.objects.create_user(
            username='doan_truong_restricted',
            password='Password123!',
            email='doantruong2@thpthuongkhe.edu.vn',
            full_name='Ủy viên Đoàn trường (Giới hạn)',
            role=User.ROLE_DOAN_TRUONG,
            account_status=User.STATUS_APPROVED,
            is_active=True,
            doan_truong_permissions=['discipline.view']  # Chỉ xem vi phạm
        )

        # 4. Giáo viên chủ nhiệm (GVCN)
        self.gvcn = User.objects.create_user(
            username='gvcn_test',
            password='Password123!',
            email='gvcn@thpthuongkhe.edu.vn',
            full_name='Thầy Nguyễn Văn A',
            role=User.ROLE_GVCN,
            account_status=User.STATUS_APPROVED,
            is_active=True
        )
        self.class_10a1.homeroom_teacher = self.gvcn
        self.class_10a1.save()

        # 5. Giáo viên bộ môn (GVBM)
        self.gvbm = User.objects.create_user(
            username='gvbm_test',
            password='Password123!',
            email='gvbm@thpthuongkhe.edu.vn',
            full_name='Cô Trần Thị B',
            role=User.ROLE_GVBM,
            account_status=User.STATUS_APPROVED,
            is_active=True
        )

        # 6. Học sinh chính thức (APPROVED)
        self.student_user = User.objects.create_user(
            username='student_test',
            password='Password123!',
            email='student1@thpthuongkhe.edu.vn',
            full_name='Học sinh Nguyễn Văn C',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED,
            department_or_class='10A1',
            is_active=True
        )
        self.student_profile = Student.objects.create(
            user=self.student_user,
            student_code='HK10-2601',
            full_name=self.student_user.full_name,
            date_of_birth=date(2010, 5, 10),
            school_class=self.class_10a1,
            status='STUDYING'
        )

        # 7. Học sinh khác ở lớp 10A2
        self.student_user_10a2 = User.objects.create_user(
            username='student_10a2',
            password='Password123!',
            email='student2@thpthuongkhe.edu.vn',
            full_name='Học sinh Lê Văn D',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED,
            department_or_class='10A2',
            is_active=True
        )
        self.student_profile_10a2 = Student.objects.create(
            user=self.student_user_10a2,
            student_code='HK10-2602',
            full_name=self.student_user_10a2.full_name,
            date_of_birth=date(2010, 6, 12),
            school_class=self.class_10a2,
            status='STUDYING'
        )

        # 8. Học sinh đang chờ duyệt (PENDING)
        self.pending_student_user = User.objects.create_user(
            username='pending_student',
            password='Password123!',
            email='pending@thpthuongkhe.edu.vn',
            full_name='Học sinh Mới Chờ Duyệt',
            role=User.ROLE_HOC_SINH,
            requested_role='HOC_SINH',
            account_status=User.STATUS_PENDING,
            department_or_class='10A1',
            is_active=False
        )

    # 1. Học sinh đăng ký mới phải ở trạng thái chờ duyệt (PENDING)
    def test_01_new_registered_student_is_pending(self):
        reg_data = {
            'full_name': 'Học Sinh Đăng Ký Mới',
            'username': 'new_reg_student',
            'email': 'new_student@thpthuongkhe.edu.vn',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'requested_role': 'HOC_SINH',
            'grade_level': 10,
            'class_id': self.class_10a1.id,
            'terms_accepted': True
        }
        res = self.client.post('/api/core/auth/register/', reg_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_user = User.objects.get(username='new_reg_student')
        self.assertEqual(new_user.account_status, User.STATUS_PENDING)
        self.assertFalse(new_user.is_active)

    # 2. Học sinh không thể tự duyệt tài khoản
    def test_02_student_cannot_approve_account(self):
        self.client.force_authenticate(user=self.student_user)
        res = self.client.post(f'/api/core/student-approvals/{self.pending_student_user.id}/approve/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.pending_student_user.refresh_from_db()
        self.assertEqual(self.pending_student_user.account_status, User.STATUS_PENDING)

    # 3. GVCN không thể duyệt tài khoản học sinh
    def test_03_gvcn_cannot_approve_student_account(self):
        self.client.force_authenticate(user=self.gvcn)
        res = self.client.post(f'/api/core/student-approvals/{self.pending_student_user.id}/approve/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.pending_student_user.refresh_from_db()
        self.assertEqual(self.pending_student_user.account_status, User.STATUS_PENDING)

    # 4. Giáo viên bộ môn không thể duyệt tài khoản học sinh
    def test_04_gvbm_cannot_approve_student_account(self):
        self.client.force_authenticate(user=self.gvbm)
        res = self.client.post(f'/api/core/student-approvals/{self.pending_student_user.id}/approve/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.pending_student_user.refresh_from_db()
        self.assertEqual(self.pending_student_user.account_status, User.STATUS_PENDING)

    # 5. Đoàn trường có quyền hợp lệ có thể duyệt tài khoản học sinh
    def test_05_doan_truong_with_permission_can_approve(self):
        self.client.force_authenticate(user=self.doan_truong_with_perms)
        res = self.client.post(f'/api/core/student-approvals/{self.pending_student_user.id}/approve/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.pending_student_user.refresh_from_db()
        self.assertEqual(self.pending_student_user.account_status, User.STATUS_APPROVED)
        self.assertTrue(self.pending_student_user.is_active)
        self.assertEqual(self.pending_student_user.approved_by, self.doan_truong_with_perms)
        # Check audit log created
        self.assertTrue(AuditLog.objects.filter(action='APPROVE_STUDENT', user=self.doan_truong_with_perms).exists())

    # 6. Tài khoản Đoàn trường không có quyền duyệt không thể thực hiện thao tác này
    def test_06_doan_truong_without_permission_cannot_approve(self):
        self.client.force_authenticate(user=self.student_user)
        res = self.client.post(f'/api/core/student-approvals/{self.pending_student_user.id}/approve/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.pending_student_user.refresh_from_db()
        self.assertEqual(self.pending_student_user.account_status, User.STATUS_PENDING)

    # 7. Chỉ Admin có thể bổ nhiệm hoặc thu hồi quyền Đoàn trường
    def test_07_only_admin_can_appoint_or_revoke_doan_truong(self):
        # Học sinh thử bổ nhiệm
        self.client.force_authenticate(user=self.student_user)
        res = self.client.post('/api/core/doan-truong/', {'user_id': self.student_user_10a2.id})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Đoàn trường thử bổ nhiệm người khác làm Đoàn trường
        self.client.force_authenticate(user=self.doan_truong_with_perms)
        res = self.client.post('/api/core/doan-truong/', {'user_id': self.student_user_10a2.id})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Admin bổ nhiệm thành công
        self.client.force_authenticate(user=self.admin)
        res = self.client.post('/api/core/doan-truong/', {
            'user_id': self.student_user_10a2.id,
            'permissions': ['student_accounts.view', 'student_accounts.approve']
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.student_user_10a2.refresh_from_db()
        self.assertEqual(self.student_user_10a2.role, User.ROLE_DOAN_TRUONG)
        self.assertTrue(AuditLog.objects.filter(action='APPOINT_DOAN_TRUONG').exists())

        # Admin thu hồi vai trò Đoàn trường
        res_revoke = self.client.post(f'/api/core/doan-truong/{self.student_user_10a2.id}/revoke/')
        self.assertEqual(res_revoke.status_code, status.HTTP_200_OK)
        self.student_user_10a2.refresh_from_db()
        self.assertNotEqual(self.student_user_10a2.role, User.ROLE_DOAN_TRUONG)
        self.assertTrue(AuditLog.objects.filter(action='REVOKE_DOAN_TRUONG').exists())

    # 8. Học sinh không thể tự cấp chức danh Sao đỏ (khi đăng ký hoặc cập nhật)
    def test_08_student_cannot_self_assign_red_star(self):
        # Thử đăng ký với chức danh SAO_DO
        reg_data = {
            'full_name': 'Hacker Sao Đỏ',
            'username': 'fake_red_star',
            'email': 'fake_red_star@thpthuongkhe.edu.vn',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'requested_role': 'SAO_DO',
            'grade_level': 10,
            'class_id': self.class_10a1.id,
            'terms_accepted': True
        }
        res = self.client.post('/api/core/auth/register/', reg_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 9. Chỉ Admin hoặc người được cấp quyền mới có thể phân công Sao đỏ
    def test_09_only_admin_or_permitted_user_can_assign_red_star(self):
        # GVCN không thể phân công Sao đỏ
        self.client.force_authenticate(user=self.gvcn)
        res = self.client.post('/api/conduct/red-star/', {
            'user': self.student_user.id,
            'scope_type': RedStarAssignment.SCOPE_CLASS,
            'assigned_class': self.class_10a2.id
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Học sinh không có quyền 'red_star.assign' không thể phân công
        self.client.force_authenticate(user=self.student_user)
        res = self.client.post('/api/conduct/red-star/', {
            'user': self.student_user.id,
            'scope_type': RedStarAssignment.SCOPE_CLASS,
            'assigned_class': self.class_10a2.id
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Không thể phân công học sinh PENDING làm Sao đỏ
        self.client.force_authenticate(user=self.doan_truong_with_perms)
        res_pending = self.client.post('/api/conduct/red-star/', {
            'user': self.pending_student_user.id,
            'scope_type': RedStarAssignment.SCOPE_CLASS,
            'assigned_class': self.class_10a2.id
        })
        self.assertEqual(res_pending.status_code, status.HTTP_400_BAD_REQUEST)

        # Đoàn trường có quyền phân công thành công cho học sinh APPROVED
        res = self.client.post('/api/conduct/red-star/', {
            'user': self.student_user.id,
            'scope_type': RedStarAssignment.SCOPE_CLASS,
            'assigned_class': self.class_10a2.id
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.student_user.refresh_from_db()
        self.assertTrue(self.student_user.is_active_red_star)
        self.assertTrue(AuditLog.objects.filter(action='ASSIGN_RED_STAR').exists())

    # 10. Sao đỏ chỉ truy cập phạm vi nhiệm vụ đang có hiệu lực
    def test_10_red_star_scope_enforcement(self):
        # Phân công student_user theo dõi lớp 10A2
        assignment = RedStarAssignment.objects.create(
            user=self.student_user,
            student=self.student_profile,
            scope_type=RedStarAssignment.SCOPE_CLASS,
            assigned_class=self.class_10a2,
            assigned_by=self.admin,
            start_date=timezone.now().date(),
            status=RedStarAssignment.STATUS_ACTIVE
        )

        self.client.force_authenticate(user=self.student_user)

        # Ghi nhận vi phạm lớp 11A1 (ngoài phạm vi) -> BỊ TỪ CHỐI
        res_invalid = self.client.post('/api/conduct/violations/', {
            'school_class': self.class_11a1.id,
            'rule': self.rule.id,
            'description': 'Vi phạm ngoài phạm vi'
        })
        self.assertEqual(res_invalid.status_code, status.HTTP_400_BAD_REQUEST)

        # Ghi nhận vi phạm lớp 10A2 (đúng phạm vi) -> THÀNH CÔNG
        res_valid = self.client.post('/api/conduct/violations/', {
            'school_class': self.class_10a2.id,
            'rule': self.rule.id,
            'description': 'Vi phạm trong phạm vi phân công'
        })
        self.assertEqual(res_valid.status_code, status.HTTP_201_CREATED)
        v = ViolationRecord.objects.get(record_code=res_valid.data['record_code'])
        # Trạng thái phải là PENDING, không tự trừ điểm
        self.assertEqual(v.status, ViolationRecord.STATUS_PENDING)
        self.assertEqual(v.points_deducted, Decimal('0.00'))

    # 11. Sao đỏ hết nhiệm vụ hoặc bị thu hồi không thể gửi báo cáo mới trong phạm vi đó
    def test_11_revoked_red_star_cannot_report(self):
        assignment = RedStarAssignment.objects.create(
            user=self.student_user,
            student=self.student_profile,
            scope_type=RedStarAssignment.SCOPE_CLASS,
            assigned_class=self.class_10a2,
            assigned_by=self.admin,
            start_date=timezone.now().date(),
            status=RedStarAssignment.STATUS_ACTIVE
        )

        # Admin thu hồi phân công
        self.client.force_authenticate(user=self.admin)
        res_revoke = self.client.post(f'/api/conduct/red-star/{assignment.id}/revoke/', {'reason': 'Hết nhiệm kỳ'})
        self.assertEqual(res_revoke.status_code, status.HTTP_200_OK)

        # Student thử gửi báo cáo sau khi bị thu hồi -> 403 Forbidden
        self.client.force_authenticate(user=self.student_user)
        res = self.client.post('/api/conduct/violations/', {
            'school_class': self.class_10a2.id,
            'rule': self.rule.id,
            'description': 'Báo cáo sau khi bị thu hồi'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 12. Báo cáo Sao đỏ không tự động làm thay đổi điểm thi đua
    def test_12_red_star_report_does_not_deduct_points(self):
        RedStarAssignment.objects.create(
            user=self.student_user,
            student=self.student_profile,
            scope_type=RedStarAssignment.SCOPE_CLASS,
            assigned_class=self.class_10a2,
            assigned_by=self.admin,
            start_date=timezone.now().date(),
            status=RedStarAssignment.STATUS_ACTIVE
        )

        self.client.force_authenticate(user=self.student_user)
        res = self.client.post('/api/conduct/red-star-reports/', {
            'school_class': self.class_10a2.id,
            'rule': self.rule.id,
            'description': 'Học sinh đi muộn 15 phút'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        report = RedStarReport.objects.get(id=res.data['report']['id'])
        self.assertEqual(report.status, RedStarReport.STATUS_PENDING)
        # Báo cáo chưa xác minh -> không có bản ghi vi phạm trừ điểm
        self.assertIsNone(report.violation_record)

    # 13. Sao đỏ không thể tự xác nhận vi phạm hoặc trừ điểm
    def test_13_red_star_cannot_verify_violations(self):
        # Tạo bản ghi vi phạm chờ duyệt
        v = ViolationRecord.objects.create(
            school_class=self.class_10a2,
            rule=self.rule,
            reporter=self.student_user,
            status=ViolationRecord.STATUS_PENDING,
            points_deducted=Decimal('0.00')
        )

        # Học sinh Sao đỏ thử gọi verify endpoint -> 403 / 400
        self.client.force_authenticate(user=self.student_user)
        res = self.client.post(f'/api/conduct/violations/{v.id}/verify/', {
            'status': ViolationRecord.STATUS_VERIFIED
        })
        self.assertIn(res.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
        v.refresh_from_db()
        self.assertEqual(v.status, ViolationRecord.STATUS_PENDING)

    # 14. Tất cả thao tác duyệt và phân quyền đều có nhật ký
    def test_14_all_actions_logged_in_audit_log(self):
        # Rejection requires reason and writes audit log
        self.client.force_authenticate(user=self.doan_truong_with_perms)
        res_no_reason = self.client.post(f'/api/core/student-approvals/{self.pending_student_user.id}/reject/', {})
        self.assertEqual(res_no_reason.status_code, status.HTTP_400_BAD_REQUEST)

        res_reject = self.client.post(f'/api/core/student-approvals/{self.pending_student_user.id}/reject/', {
            'reason': 'Thông tin lớp học không chính xác'
        })
        self.assertEqual(res_reject.status_code, status.HTTP_200_OK)
        self.assertTrue(AuditLog.objects.filter(action='REJECT_STUDENT', user=self.doan_truong_with_perms).exists())
        self.assertTrue(ApprovalLog.objects.filter(user=self.pending_student_user, new_status=User.STATUS_REJECTED).exists())

    # 15. Kiểm tra truy cập trực tiếp API và thay ID trong URL để ngăn vượt quyền
    def test_15_prevent_privilege_escalation_by_url_id(self):
        # Một học sinh cố tình gọi API phê duyệt thay ID của người khác
        self.client.force_authenticate(user=self.student_user)
        res1 = self.client.post(f'/api/core/student-approvals/{self.pending_student_user.id}/approve/')
        self.assertEqual(res1.status_code, status.HTTP_403_FORBIDDEN)

        # Một học sinh cố tình gọi API cập nhật quyền Đoàn trường
        res2 = self.client.post(f'/api/core/doan-truong/{self.student_user.id}/permissions/', {
            'permissions': ['admin.all']
        })
        self.assertEqual(res2.status_code, status.HTTP_403_FORBIDDEN)

        # Một học sinh cố tình gọi API thu hồi Sao đỏ của bạn khác
        res3 = self.client.post('/api/conduct/red-star/999/revoke/', {'reason': 'test'})
        self.assertEqual(res3.status_code, status.HTTP_403_FORBIDDEN)
