from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import User, AcademicYear, Semester
from competition.models import CompetitionPeriod
from conduct.models import (
    SchoolClass, Student, Teacher, ConductRuleCategory, ConductRule,
    TeacherClassAssignment, HomeroomAssignment, TeacherReflection, ReflectionHistory,
    ViolationRecord
)


class AccountSystemUpgradeTests(TestCase):
    """
    Bộ kiểm thử toàn diện cho hệ thống tài khoản, 64 lớp học,
    phân công giáo viên và phân quyền thi đua trường THPT Hương Khê.
    """

    def setUp(self):
        self.client = APIClient()

        # 1. Năm học
        self.ay, _ = AcademicYear.objects.get_or_create(
            name='Năm học 2026-2027',
            defaults={
                'start_date': date(2026, 9, 5),
                'end_date': date(2027, 5, 31),
                'is_current': True
            }
        )
        self.semester_1, _ = Semester.objects.get_or_create(
            academic_year=self.ay,
            semester_number=1,
            defaults={
                'name': 'Học kỳ I',
                'start_date': date(2026, 9, 7),
                'end_date': date(2027, 1, 10),
            },
        )
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        CompetitionPeriod.objects.get_or_create(
            academic_year=self.ay,
            period_type=CompetitionPeriod.TYPE_WEEK,
            week_number=7,
            defaults={
                'name': 'Tuần kiểm thử hiện tại',
                'semester': self.semester_1,
                'internal_month_number': 2,
                'start_date': week_start,
                'end_date': week_start + timedelta(days=6),
                'is_locked': False,
            },
        )

        # 2. Tạo một số lớp đại diện từ 64 lớp
        self.class_10a1 = SchoolClass.objects.create(name='10A1', grade=10, academic_year=self.ay, is_active=True)
        self.class_10a2 = SchoolClass.objects.create(name='10A2', grade=10, academic_year=self.ay, is_active=True)
        self.class_11a1 = SchoolClass.objects.create(name='11A1', grade=11, academic_year=self.ay, is_active=True)
        self.class_12a1 = SchoolClass.objects.create(name='12A1', grade=12, academic_year=self.ay, is_active=True)

        # 3. Tạo học sinh mẫu
        self.student_10a1 = Student.objects.create(
            school_class=self.class_10a1,
            student_code='HS10A1-001',
            full_name='Trần Văn Nam',
            date_of_birth=date(2010, 1, 1),
            gender='M'
        )
        self.student_10a2 = Student.objects.create(
            school_class=self.class_10a2,
            student_code='HS10A2-001',
            full_name='Lê Thị Mai',
            date_of_birth=date(2010, 2, 2),
            gender='F'
        )

        # 4. Tài khoản Admin
        self.admin = User.objects.create_user(
            username='admin_huongkhe',
            email='admin@thpthuongkhe.edu.vn',
            password='Password123!',
            role=User.ROLE_ADMIN,
            account_status=User.STATUS_APPROVED,
            is_staff=True,
            is_active=True
        )

        # 5. Tài khoản Giáo viên bộ môn (GVBM)
        self.gvbm = User.objects.create_user(
            username='gv_toan_nam',
            email='gvtoan@thpthuongkhe.edu.vn',
            password='Password123!',
            role=User.ROLE_GVBM,
            account_status=User.STATUS_APPROVED,
            department_or_class='Môn Toán',
            is_active=True
        )
        Teacher.objects.create(user=self.gvbm, teacher_code='GV-001', full_name='Thầy Nam', subject='Toán')

        # 6. Tài khoản Giáo viên chủ nhiệm (GVCN) 10A1
        self.gvcn_10a1 = User.objects.create_user(
            username='gvcn_10a1',
            email='gvcn10a1@thpthuongkhe.edu.vn',
            password='Password123!',
            role=User.ROLE_GVCN,
            account_status=User.STATUS_APPROVED,
            can_verify_violations=True,
            department_or_class='Môn Ngữ văn',
            is_active=True
        )
        Teacher.objects.create(user=self.gvcn_10a1, teacher_code='GV-002', full_name='Cô Hoa', subject='Ngữ văn')
        self.class_10a1.homeroom_teacher = self.gvcn_10a1
        self.class_10a1.save()
        HomeroomAssignment.objects.create(
            teacher=self.gvcn_10a1,
            school_class=self.class_10a1,
            assigned_by=self.admin,
            is_active=True
        )

        # 7. Tài khoản Học sinh
        self.user_student = User.objects.create_user(
            username='hs_nam_10a1',
            email='nam10a1@thpthuongkhe.edu.vn',
            password='Password123!',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED,
            is_active=True
        )
        self.student_10a1.user = self.user_student
        self.student_10a1.save()

        # 8. Nội quy vi phạm
        self.cat = ConductRuleCategory.objects.create(name='Nề nếp học tập')
        self.rule = ConductRule.objects.create(
            category=self.cat,
            code='NN-001',
            name='Không thuộc bài cũ',
            default_points_deducted=2.0,
            is_active=True
        )

    # -------------------------------------------------------------------------
    # NHÓM A: ĐĂNG KÝ TÀI KHOẢN (HỌC SINH / GIÁO VIÊN BỘ MÔN)
    # -------------------------------------------------------------------------
    def test_student_registration_success_with_valid_grade_and_class(self):
        """Học sinh đăng ký với khối và lớp khớp nhau thành công (chờ duyệt)"""
        res = self.client.post(
            '/api/core/auth/register/',
            data={
                'full_name': 'Nguyễn Văn Đạt',
                'username': 'hs_dat_10a1',
                'email': 'dat10a1@thpthuongkhe.edu.vn',
                'password': 'StrongPassword123!',
                'confirm_password': 'StrongPassword123!',
                'requested_role': 'HOC_SINH',
                'grade_level': 10,
                'class_id': self.class_10a1.id,
                'terms_accepted': True
            },
            format='json'
        )
        self.assertEqual(res.status_code, 201)
        user = User.objects.get(username='hs_dat_10a1')
        self.assertEqual(user.role, User.ROLE_HOC_SINH)
        self.assertEqual(user.account_status, User.STATUS_PENDING)

    def test_student_registration_rejected_when_grade_and_class_mismatch(self):
        """Học sinh chọn Khối 11 nhưng chọn Lớp 10A1 bị từ chối 400"""
        res = self.client.post(
            '/api/core/auth/register/',
            data={
                'full_name': 'Học Sinh Sai Khối',
                'username': 'hs_saikhoi',
                'email': 'saikhoi@thpthuongkhe.edu.vn',
                'password': 'StrongPassword123!',
                'confirm_password': 'StrongPassword123!',
                'requested_role': 'HOC_SINH',
                'grade_level': 11,
                'class_id': self.class_10a1.id,  # Lớp 10A1 thuộc khối 10
                'terms_accepted': True
            },
            format='json'
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn('class_id', res.json().get('details', {}))

    def test_teacher_registration_requires_subject_and_phone(self):
        """Giáo viên bộ môn đăng ký thành công với môn dạy và SĐT"""
        res = self.client.post(
            '/api/core/auth/register/',
            data={
                'full_name': 'Trần Văn Giáo Viên',
                'username': 'gv_tienganh_moi',
                'email': 'gvtienganh@thpthuongkhe.edu.vn',
                'phone': '0912345678',
                'password': 'StrongPassword123!',
                'confirm_password': 'StrongPassword123!',
                'requested_role': 'GVBM',
                'subject': 'Tiếng Anh',
                'terms_accepted': True
            },
            format='json'
        )
        self.assertEqual(res.status_code, 201)
        user = User.objects.get(username='gv_tienganh_moi')
        self.assertEqual(user.role, User.ROLE_GVBM)
        self.assertEqual(user.subject, 'Tiếng Anh')
        self.assertEqual(user.account_status, User.STATUS_PENDING)

    # -------------------------------------------------------------------------
    # NHÓM B: ADMIN PHÂN CÔNG LỚP CHO GIÁO VIÊN BỘ MÔN
    # -------------------------------------------------------------------------
    def test_admin_can_assign_multiple_classes_across_grades_to_gvbm(self):
        """Admin có quyền phân công nhiều lớp trên nhiều khối cho GVBM"""
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(
            f'/api/conduct/teachers/{self.gvbm.id}/assign-classes/',
            data={'class_ids': [self.class_10a1.id, self.class_11a1.id, self.class_12a1.id]},
            format='json'
        )
        self.assertEqual(res.status_code, 200)
        assignments = TeacherClassAssignment.objects.filter(teacher=self.gvbm, is_active=True)
        self.assertEqual(assignments.count(), 3)
        assigned_names = set(assignments.values_list('school_class__name', flat=True))
        self.assertEqual(assigned_names, {'10A1', '11A1', '12A1'})

    def test_non_admin_cannot_assign_classes(self):
        """Người dùng không phải Admin không được phép phân công lớp (403)"""
        self.client.force_authenticate(user=self.gvbm)
        res = self.client.post(
            f'/api/conduct/teachers/{self.gvbm.id}/assign-classes/',
            data={'class_ids': [self.class_10a1.id]},
            format='json'
        )
        self.assertEqual(res.status_code, 403)

    # -------------------------------------------------------------------------
    # NHÓM C: BỔ NHIỆM VÀ XUNG ĐỘT GIÁO VIÊN CHỦ NHIỆM (GVCN)
    # -------------------------------------------------------------------------
    def test_appoint_gvcn_conflict_check_and_replacement(self):
        """Bổ nhiệm GVCN lớp đã có GVCN trả về 409 khi confirm_replace=False, thành công khi confirm_replace=True"""
        self.client.force_authenticate(user=self.admin)

        # Lớp 10A1 đã có GVCN là self.gvcn_10a1
        # Thử bổ nhiệm self.gvbm làm GVCN lớp 10A1 mà không xác nhận thay thế
        res_conflict = self.client.post(
            f'/api/conduct/teachers/{self.gvbm.id}/appoint-homeroom/',
            data={'class_id': self.class_10a1.id, 'confirm_replace': False},
            format='json'
        )
        self.assertEqual(res_conflict.status_code, 409)
        self.assertIn('xung đột', res_conflict.json()['error'].lower())

        # Thử lại với confirm_replace=True
        res_replace = self.client.post(
            f'/api/conduct/teachers/{self.gvbm.id}/appoint-homeroom/',
            data={'class_id': self.class_10a1.id, 'confirm_replace': True, 'notes': 'Thay thế theo phân công mới'},
            format='json'
        )
        self.assertEqual(res_replace.status_code, 200)

        # Kiểm tra lớp 10A1 đã được chuyển sang GVCN mới
        self.class_10a1.refresh_from_db()
        self.assertEqual(self.class_10a1.homeroom_teacher, self.gvbm)

        # Phân công cũ của gvcn_10a1 bị đánh dấu is_active=False
        old_assignment = HomeroomAssignment.objects.get(teacher=self.gvcn_10a1, school_class=self.class_10a1)
        self.assertFalse(old_assignment.is_active)

    def test_revoke_homeroom_teacher(self):
        """Admin có quyền miễn nhiệm GVCN lớp học"""
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(
            f'/api/conduct/teachers/{self.gvcn_10a1.id}/revoke-homeroom/',
            data={'class_id': self.class_10a1.id},
            format='json'
        )
        self.assertEqual(res.status_code, 200)
        self.class_10a1.refresh_from_db()
        self.assertIsNone(self.class_10a1.homeroom_teacher)

    # -------------------------------------------------------------------------
    # NHÓM D: QUYỀN HẠN PHẢN ÁNH CỦA GVBM VÀ BẢO VỆ CHẶN TRỪ ĐIỂM
    # -------------------------------------------------------------------------
    def test_gvbm_strictly_forbidden_from_creating_violation_directly(self):
        """QUY TẮC BẮT BUỘC: GVBM TUYỆT ĐỐI KHÔNG ĐƯỢC trừ điểm trực tiếp qua API vi phạm (403)"""
        self.client.force_authenticate(user=self.gvbm)
        res = self.client.post(
            '/api/conduct/violations/',
            data={
                'school_class': self.class_10a1.id,
                'student': self.student_10a1.id,
                'rule': self.rule.id,
                'description': 'Học sinh nói chuyện trong giờ'
            },
            format='json'
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn('không có quyền', res.json()['error'].lower())

    def test_gvbm_can_submit_reflection_for_assigned_class_without_points(self):
        """GVBM chỉ có quyền gửi phản ánh cho lớp được phân công, không bị trừ điểm thi đua"""
        # Phân công GVBM vào lớp 10A1
        TeacherClassAssignment.objects.create(
            teacher=self.gvbm,
            school_class=self.class_10a1,
            subject='Toán',
            assigned_by=self.admin,
            is_active=True
        )

        self.client.force_authenticate(user=self.gvbm)
        res = self.client.post(
            '/api/conduct/reflections/',
            data={
                'class_id': self.class_10a1.id,
                'student_id': self.student_10a1.id,
                'reflection_type': 'HOC_TAP',
                'urgency': 'NORMAL',
                'content': 'Học sinh chưa hoàn thành bài tập về nhà môn Toán',
            },
            format='json'
        )
        self.assertEqual(res.status_code, 201)
        ref_id = res.json().get('reflection_id') or res.json().get('id')
        ref = TeacherReflection.objects.get(id=ref_id)
        self.assertEqual(ref.status, TeacherReflection.STATUS_NEW)
        # Không có bản ghi vi phạm trừ điểm nào được tạo
        self.assertIsNone(ref.violation_record)
        self.assertEqual(ViolationRecord.objects.count(), 0)

    def test_gvbm_cannot_submit_reflection_for_unassigned_class(self):
        """GVBM không được gửi phản ánh cho lớp mà mình không được phân công giảng dạy (403)"""
        self.client.force_authenticate(user=self.gvbm)
        res = self.client.post(
            '/api/conduct/reflections/',
            data={
                'class_id': self.class_10a2.id,  # GVBM chưa được phân công dạy 10A2
                'content': 'Phản ánh lớp không dạy',
            },
            format='json'
        )
        self.assertEqual(res.status_code, 403)

    # -------------------------------------------------------------------------
    # NHÓM E: GVCN XỬ LÝ PHẢN ÁNH (ĐÓNG, BIỂU DƯƠNG, HOẶC CHUYỂN VI PHẠM)
    # -------------------------------------------------------------------------
    def test_gvcn_can_process_reflection_close_without_penalty(self):
        """GVCN xử lý phản ánh: Đóng hồ sơ, nhắc nhở (không trừ điểm thi đua)"""
        # Tạo phản ánh từ GVBM
        ref = TeacherReflection.objects.create(
            teacher=self.gvbm,
            school_class=self.class_10a1,
            student=self.student_10a1,
            student_name_snapshot='Trần Văn Nam',
            reflection_type='HOC_TAP',
            urgency='NORMAL',
            content='Chưa làm bài tập Toán',
            occurred_at=timezone.now(),
            status=TeacherReflection.STATUS_NEW
        )

        self.client.force_authenticate(user=self.gvcn_10a1)
        res = self.client.post(
            f'/api/conduct/reflections/{ref.id}/process/',
            data={
                'action': 'close',
                'notes': 'GVCN đã trao đổi riêng và nhắc nhở học sinh làm bù bài tập'
            },
            format='json'
        )
        self.assertEqual(res.status_code, 200)
        ref.refresh_from_db()
        self.assertEqual(ref.status, TeacherReflection.STATUS_CLOSED)
        self.assertEqual(ViolationRecord.objects.count(), 0)  # Không phát sinh trừ điểm

    def test_gvcn_can_convert_reflection_to_official_violation_with_deduction(self):
        """GVCN xử lý phản ánh: Chuyển thành vi phạm chính thức và trừ điểm thi đua lớp"""
        ref = TeacherReflection.objects.create(
            teacher=self.gvbm,
            school_class=self.class_10a1,
            student=self.student_10a1,
            student_name_snapshot='Trần Văn Nam',
            reflection_type='NE_NEP',
            urgency='HIGH',
            content='Vi phạm nhiều lần không thuộc bài cũ môn Toán',
            occurred_at=timezone.now(),
            status=TeacherReflection.STATUS_NEW
        )

        self.client.force_authenticate(user=self.gvcn_10a1)
        res = self.client.post(
            f'/api/conduct/reflections/{ref.id}/process/',
            data={
                'action': 'convert_violation',
                'rule_id': self.rule.id,
                'notes': 'Đã xác nhận lỗi lặp lại, chuyển thành biên bản vi phạm trừ điểm'
            },
            format='json'
        )
        self.assertEqual(res.status_code, 200)
        ref.refresh_from_db()
        self.assertEqual(ref.status, TeacherReflection.STATUS_RESOLVED)
        self.assertIsNotNone(ref.violation_record)
        self.assertEqual(ref.violation_record.status, ViolationRecord.STATUS_VERIFIED)
        self.assertEqual(ref.violation_record.points_deducted, 2)

    def test_gvcn_class_isolation_cannot_process_other_class_reflection(self):
        """GVCN lớp 10A1 không được xem hoặc xử lý phản ánh của lớp 10A2 (404/403)"""
        # Tạo phản ánh cho lớp 10A2
        ref_10a2 = TeacherReflection.objects.create(
            teacher=self.gvbm,
            school_class=self.class_10a2,
            student=self.student_10a2,
            student_name_snapshot='Lê Thị Mai',
            reflection_type='NE_NEP',
            content='Phản ánh lớp 10A2',
            occurred_at=timezone.now(),
            status=TeacherReflection.STATUS_NEW
        )

        self.client.force_authenticate(user=self.gvcn_10a1)

        # Xem danh sách: không có phản ánh của 10A2
        res_list = self.client.get('/api/conduct/reflections/')
        self.assertEqual(res_list.status_code, 200)
        ref_ids = [r['id'] for r in res_list.json()['results']]
        self.assertNotIn(ref_10a2.id, ref_ids)

        # Thử xử lý phản ánh 10A2: bị từ chối
        res_proc = self.client.post(
            f'/api/conduct/reflections/{ref_10a2.id}/process/',
            data={'action': 'close', 'notes': 'Thử can thiệp lớp khác'},
            format='json'
        )
        self.assertIn(res_proc.status_code, [403, 404])
