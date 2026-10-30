import json
import uuid
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from core.models import User, AcademicYear, Semester, AuditLog, ALL_DOAN_TRUONG_PERMISSIONS
from conduct.models import SchoolClass, Student, Teacher, ConductRule, ConductRuleCategory, ViolationRecord, RedStarAssignment, RedStarReport
from competition.models import CompetitionPeriod, ClassCompetitionScore, ScoreCriterion, ScoreAdjustment
from competition.services import recalculate_score_for_class_at_time


class DoanTruongAuthorityComprehensiveTests(TestCase):
    """
    Bộ kiểm thử toàn diện cho hệ thống phân quyền Đoàn trường dưới Admin
    theo đúng các yêu cầu nghiệp vụ HK Student Hub.
    """
    def setUp(self):
        self.client = APIClient()

        # 1. Năm học & Học kỳ (2026-2027)
        self.year, _ = AcademicYear.objects.get_or_create(
            name='2026-2027',
            defaults={
                'start_date': timezone.datetime(2026, 9, 7).date(),
                'end_date': timezone.datetime(2027, 5, 30).date(),
                'is_current': True
            }
        )
        self.semester1, _ = Semester.objects.get_or_create(
            academic_year=self.year,
            semester_number=1,
            defaults={
                'name': 'Học kỳ I',
                'start_date': timezone.datetime(2026, 9, 7).date(),
                'end_date': timezone.datetime(2027, 1, 15).date(),
                'is_current': True
            }
        )
        self.week1, _ = CompetitionPeriod.objects.get_or_create(
            academic_year=self.year,
            semester=self.semester1,
            period_type=CompetitionPeriod.TYPE_WEEK,
            week_number=1,
            defaults={
                'name': 'Tuần 1',
                'start_date': timezone.datetime(2026, 9, 7).date(),
                'end_date': timezone.datetime(2026, 9, 13).date(),
                'internal_month_number': 1,
                'is_published': True,
                'is_locked': False
            }
        )
        if not self.week1.internal_month_number:
            self.week1.internal_month_number = 1
            self.week1.save(update_fields=['internal_month_number'])

        ScoreCriterion.objects.get_or_create(
            academic_year=self.year,
            defaults={
                'name': 'Tiêu chuẩn thi đua 2026-2027',
                'initial_base_points': Decimal('100.00'),
                'effective_from': timezone.datetime(2026, 9, 7).date(),
                'effective_to': timezone.datetime(2027, 5, 31).date(),
            }
        )
        self.incident_time = timezone.make_aware(timezone.datetime(2026, 9, 10, 8, 0))

        # 2. Người dùng theo các cấp phân quyền
        self.admin = User.objects.create_user(
            username='admin_boss',
            password='Password123!',
            role=User.ROLE_ADMIN,
            account_status=User.STATUS_APPROVED,
            is_active=True,
            is_staff=True
        )
        self.doan_truong = User.objects.create_user(
            username='doan_truong_canbo',
            password='Password123!',
            role=User.ROLE_DOAN_TRUONG,
            account_status=User.STATUS_APPROVED,
            is_active=True,
            doan_truong_permissions=list(ALL_DOAN_TRUONG_PERMISSIONS)
        )
        self.gvcn = User.objects.create_user(
            username='gvcn_user',
            password='Password123!',
            role=User.ROLE_GVCN,
            account_status=User.STATUS_APPROVED,
            is_active=True
        )
        self.gvbm = User.objects.create_user(
            username='gvbm_user',
            password='Password123!',
            role=User.ROLE_GVBM,
            account_status=User.STATUS_APPROVED,
            is_active=True
        )
        self.student_user = User.objects.create_user(
            username='student_user',
            password='Password123!',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED,
            is_active=True
        )
        self.sao_do_user = User.objects.create_user(
            username='sao_do_student',
            password='Password123!',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED,
            is_active=True
        )

        # 3. Dữ liệu lớp học & học sinh
        self.class10a1 = SchoolClass.objects.create(
            name='10A1_TEST',
            grade=10,
            academic_year=self.year,
            homeroom_teacher=self.gvcn,
            is_active=True
        )
        self.class10a2 = SchoolClass.objects.create(
            name='10A2_TEST',
            grade=10,
            academic_year=self.year,
            is_active=True
        )
        self.student_profile = Student.objects.create(
            user=self.student_user,
            student_code='HK10-9991',
            full_name='Nguyễn Văn Học Sinh',
            date_of_birth=timezone.datetime(2009, 1, 1).date(),
            gender='M',
            school_class=self.class10a1,
            status='STUDYING'
        )
        self.sao_do_profile = Student.objects.create(
            user=self.sao_do_user,
            student_code='HK10-9992',
            full_name='Trần Sao Đỏ',
            date_of_birth=timezone.datetime(2009, 5, 5).date(),
            gender='F',
            school_class=self.class10a2,
            status='STUDYING'
        )

        # Phân công Sao đỏ
        self.sao_do_assignment = RedStarAssignment.objects.create(
            user=self.sao_do_user,
            student=self.sao_do_profile,
            assigned_class=self.class10a1,
            status=RedStarAssignment.STATUS_ACTIVE,
            start_date=timezone.now().date(),
            assigned_by=self.doan_truong
        )

        # Điểm thi đua ban đầu
        self.score10a1 = ClassCompetitionScore.objects.create(
            competition_period=self.week1,
            school_class=self.class10a1,
            base_points=Decimal('100.00'),
            total_score=Decimal('100.00'),
            rank=1
        )

        # Nội quy vi phạm
        self.category = ConductRuleCategory.objects.create(
            name='Nền nếp chung Test',
            order=1
        )
        self.rule = ConductRule.objects.create(
            category=self.category,
            code='VP-TEST-01',
            name='Đi học muộn test',
            default_points_deducted=Decimal('2.00'),
            is_active=True
        )

    def test_doan_truong_can_view_school_wide_operational_data(self):
        """1. Đoàn trường xem được dữ liệu nghiệp vụ toàn trường (Lớp, Học sinh, Điểm, Vi phạm, Cảnh báo, Thống kê)"""
        self.client.force_authenticate(self.doan_truong)

        # Xem lớp học toàn trường
        res_classes = self.client.get('/api/conduct/classes/')
        self.assertEqual(res_classes.status_code, status.HTTP_200_OK)

        # Xem danh sách người dùng toàn trường
        res_users = self.client.get('/api/core/users/')
        self.assertEqual(res_users.status_code, status.HTTP_200_OK)

        # Xem thống kê tổng quan hệ thống
        res_stats = self.client.get('/api/core/system/stats/')
        self.assertEqual(res_stats.status_code, status.HTTP_200_OK)
        self.assertEqual(res_stats.data['scope'], 'school')

        # Xem điểm thi đua toàn trường
        res_scores = self.client.get('/api/competition/scores/')
        self.assertEqual(res_scores.status_code, status.HTTP_200_OK)

        # Xem nội quy vi phạm
        res_rules = self.client.get('/api/conduct/rules/')
        self.assertEqual(res_rules.status_code, status.HTTP_200_OK)

        # Xem nhật ký Audit Log
        res_audit = self.client.get('/api/core/audit-logs/')
        self.assertEqual(res_audit.status_code, status.HTTP_200_OK)

    def test_doan_truong_can_approve_and_reject_pending_student(self):
        """2. Đoàn trường phê duyệt tài khoản học sinh đang chờ duyệt"""
        pending_student = User.objects.create_user(
            username='pending_applicant_unique',
            password='Password123!',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_PENDING,
            requested_role=User.ROLE_HOC_SINH,
            is_active=False
        )
        self.client.force_authenticate(self.doan_truong)

        res = self.client.post(f'/api/core/student-approvals/{pending_student.id}/approve/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        pending_student.refresh_from_db()
        self.assertEqual(pending_student.account_status, User.STATUS_APPROVED)
        self.assertEqual(pending_student.approved_by_id, self.doan_truong.id)
        self.assertTrue(pending_student.is_active)

    def test_red_star_report_does_not_auto_deduct_points(self):
        """3 & 4. Báo cáo mới của Sao đỏ không tự động trừ điểm, chỉ trừ điểm sau khi Đoàn trường xác minh"""
        self.client.force_authenticate(self.sao_do_user)

        # Sao đỏ gửi báo cáo
        post_data = {
            'school_class': self.class10a1.id,
            'student': self.student_profile.id,
            'rule': self.rule.id,
            'location': 'Cổng trường',
            'description': 'Đi học muộn 15 phút',
            'incident_time': self.incident_time.isoformat(),
        }
        res = self.client.post('/api/conduct/red-star-reports/', post_data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        report_id = res.data['report']['id']

        # Kiểm tra điểm lớp 10A1: VẪN NGUYÊN 100 điểm (chưa bị trừ điểm!)
        self.score10a1.refresh_from_db()
        self.assertEqual(self.score10a1.total_score, Decimal('100.00'))

        # Giờ Đoàn trường xác minh báo cáo
        self.client.force_authenticate(self.doan_truong)
        verify_res = self.client.post(f'/api/conduct/red-star-reports/{report_id}/verify/', {
            'status': RedStarReport.STATUS_VERIFIED,
            'review_note': 'Đoàn trường thẩm tra chính xác.'
        })
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)

        # Kiểm tra điểm lớp 10A1: ĐÃ BỊ TRỪ ĐIỂM (100 - 2 = 98 điểm)
        self.score10a1.refresh_from_db()
        self.assertEqual(self.score10a1.total_score, Decimal('98.00'))

    def test_doan_truong_can_adjust_or_undo_violation(self):
        """5. Đoàn trường điều chỉnh hoặc hoàn tác vi phạm có lý do và lưu nhật ký"""
        violation = ViolationRecord.objects.create(
            record_code='VP-TEST-UNDO-001',
            school_class=self.class10a1,
            student=self.student_profile,
            rule=self.rule,
            points_deducted=Decimal('2.00'),
            status=ViolationRecord.STATUS_VERIFIED,
            reporter=self.doan_truong,
            verified_by=self.doan_truong,
            occurred_at=self.incident_time
        )
        recalculate_score_for_class_at_time(self.class10a1, violation.occurred_at)
        self.score10a1.refresh_from_db()
        self.assertEqual(self.score10a1.total_score, Decimal('98.00'))

        self.client.force_authenticate(self.doan_truong)

        # Hoàn tác vi phạm
        undo_res = self.client.post(f'/api/conduct/violations/{violation.id}/adjust-or-undo/', {
            'action': 'undo',
            'reason': 'Học sinh có lý do chính đáng được GVCN bảo lãnh'
        })
        self.assertEqual(undo_res.status_code, status.HTTP_200_OK)

        violation.refresh_from_db()
        self.assertEqual(violation.status, ViolationRecord.STATUS_REJECTED)
        self.score10a1.refresh_from_db()
        self.assertEqual(self.score10a1.total_score, Decimal('100.00'))

    def test_doan_truong_can_add_bonus_and_manage_periods(self):
        """6. Đoàn trường cộng điểm phong trào và chốt/mở kỳ thi đua"""
        self.client.force_authenticate(self.doan_truong)

        # Cộng điểm phong trào
        bonus_res = self.client.post(f'/api/competition/scores/{self.score10a1.id}/add-bonus/', {
            'bonus_points': '5.00',
            'note': 'Đoạt giải Nhất kéo co ngày 26/03',
            'idempotency_key': str(uuid.uuid4())
        })
        self.assertEqual(bonus_res.status_code, status.HTTP_200_OK)
        self.score10a1.refresh_from_db()
        self.assertEqual(self.score10a1.total_score, Decimal('105.00'))

        # Chốt sổ kỳ thi đua
        lock_res = self.client.post(f'/api/competition/periods/{self.week1.id}/lock/')
        self.assertEqual(lock_res.status_code, status.HTTP_200_OK)
        self.week1.refresh_from_db()
        self.assertTrue(self.week1.is_locked)

        # Mở lại kỳ thi đua
        unlock_res = self.client.post(f'/api/competition/periods/{self.week1.id}/unlock/')
        self.assertEqual(unlock_res.status_code, status.HTTP_200_OK)
        self.week1.refresh_from_db()
        self.assertFalse(self.week1.is_locked)

    def test_doan_truong_cannot_escalate_to_admin_or_alter_admin_accounts(self):
        """7 & 8. Đoàn trường KHÔNG THỂ tự nâng cấp hoặc cấp vai trò Admin, và KHÔNG THỂ sửa tài khoản Admin"""
        self.client.force_authenticate(self.doan_truong)

        # Cố gắng tạo tài khoản Admin -> BỊ CHẶN 403
        create_admin_res = self.client.post('/api/core/users/', {
            'username': 'fake_admin',
            'role': User.ROLE_ADMIN,
            'full_name': 'Kẻ Mạo Danh'
        })
        self.assertEqual(create_admin_res.status_code, status.HTTP_403_FORBIDDEN)

        # Cố gắng sửa/khóa tài khoản Admin thật -> BỊ CHẶN 403
        edit_admin_res = self.client.post(f'/api/core/users/{self.admin.id}/review/', {
            'action': 'suspend',
            'reason': 'Thử nghiệm phá hoại'
        })
        self.assertEqual(edit_admin_res.status_code, status.HTTP_403_FORBIDDEN)

        # Cố gắng duyệt học sinh thành Admin -> BỊ CHẶN 403
        promote_res = self.client.post(f'/api/core/users/{self.student_user.id}/review/', {
            'action': 'approve',
            'assigned_role': User.ROLE_ADMIN
        })
        self.assertEqual(promote_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_students_and_teachers_cannot_call_doan_truong_endpoints(self):
        """9. Học sinh và giáo viên không thể gọi API dành riêng cho Đoàn trường / Admin"""
        self.client.force_authenticate(self.student_user)

        # Học sinh gọi duyệt tài khoản -> 403
        self.assertEqual(
            self.client.post(f'/api/core/student-approvals/{self.sao_do_user.id}/approve/').status_code,
            status.HTTP_403_FORBIDDEN
        )

        # Học sinh gọi chốt sổ thi đua -> 403
        self.assertEqual(
            self.client.post(f'/api/competition/periods/{self.week1.id}/lock/').status_code,
            status.HTTP_403_FORBIDDEN
        )

        # Giáo viên bộ môn gọi phân công Sao đỏ -> 403
        self.client.force_authenticate(self.gvbm)
        self.assertEqual(
            self.client.post('/api/conduct/red-star/', {}).status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_revoking_doan_truong_takes_immediate_effect(self):
        """10. Thu hồi quyền Đoàn trường có hiệu lực thực tế ngay lập tức ở backend"""
        self.client.force_authenticate(self.admin)

        # Admin thu hồi quyền Đoàn trường của user
        revoke_res = self.client.post(f'/api/core/doan-truong/{self.doan_truong.id}/revoke/', {
            'target_role': User.ROLE_HOC_SINH
        })
        self.assertEqual(revoke_res.status_code, status.HTTP_200_OK)

        self.doan_truong.refresh_from_db()
        self.assertEqual(self.doan_truong.role, User.ROLE_HOC_SINH)

        # Tài khoản cũ cố thực hiện quyền Đoàn trường -> BỊ CHẶN 403
        self.client.force_authenticate(self.doan_truong)
        self.assertEqual(
            self.client.post(f'/api/core/student-approvals/{self.student_user.id}/approve/').status_code,
            status.HTTP_403_FORBIDDEN
        )
