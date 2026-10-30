# -*- coding: utf-8 -*-
import datetime
from django.utils import timezone
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from core.models import User, AcademicYear, Notification
from conduct.models import (
    SchoolClass, Student, TeacherClassAssignment, HomeroomAssignment,
    ConductRuleCategory, ConductRule, ViolationRecord,
    StudentFeedback, StudentFeedbackReply,
)


class TeacherClassesAndFeedbackTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.academic_year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=datetime.date(2026, 9, 1),
            end_date=datetime.date(2027, 5, 31),
            is_current=True,
        )

        # 1. Users
        # GVCN User
        self.gvcn_user = User.objects.create_user(
            username='gvcn_lan',
            password='password123',
            full_name='Nguyễn Thị Lan',
            role=User.ROLE_GVCN,
            account_status=User.STATUS_APPROVED
        )

        # GVBM User (Toán)
        self.gvbm_user = User.objects.create_user(
            username='gvbm_hung',
            password='password123',
            full_name='Trần Quốc Hùng',
            role=User.ROLE_GVBM,
            account_status=User.STATUS_APPROVED
        )

        # Another GVBM User (Văn) - Not assigned to Class 10A1
        self.other_gvbm = User.objects.create_user(
            username='gvbm_hoa',
            password='password123',
            full_name='Lê Thị Hoa',
            role=User.ROLE_GVBM,
            account_status=User.STATUS_APPROVED
        )

        # Admin User
        self.admin_user = User.objects.create_user(
            username='admin_boss',
            password='password123',
            full_name='Phạm Quản Trị',
            role=User.ROLE_ADMIN,
            account_status=User.STATUS_APPROVED
        )

        # Đoàn trường User
        self.doan_truong_user = User.objects.create_user(
            username='doan_truong_minh',
            password='password123',
            full_name='Đoàn Văn Minh',
            role=User.ROLE_DOAN_TRUONG,
            account_status=User.STATUS_APPROVED
        )

        # 2. Classes
        # Class 10A1: GVCN is gvcn_user
        self.class_10a1 = SchoolClass.objects.create(
            name='10A1',
            grade=10,
            academic_year=self.academic_year,
            homeroom_teacher=self.gvcn_user,
            student_count=40,
            room_number='P.201',
            is_active=True
        )

        # Class 10A2: No homeroom assigned yet
        self.class_10a2 = SchoolClass.objects.create(
            name='10A2',
            grade=10,
            academic_year=self.academic_year,
            student_count=38,
            room_number='P.202',
            is_active=True
        )

        # 3. Teaching Assignments
        # gvbm_user teaches Toán in 10A1
        self.assignment_toan = TeacherClassAssignment.objects.create(
            teacher=self.gvbm_user,
            school_class=self.class_10a1,
            subject='Toán',
            is_active=True
        )

        # other_gvbm teaches Văn in 10A2 only (not 10A1)
        self.assignment_van = TeacherClassAssignment.objects.create(
            teacher=self.other_gvbm,
            school_class=self.class_10a2,
            subject='Ngữ văn',
            is_active=True
        )

        # 4. Students in 10A1 (deliberately unordered to test Vietnamese sorting)
        self.student_an = Student.objects.create(
            student_code='HS1001',
            full_name='Nguyễn Văn An',
            gender='M',
            school_class=self.class_10a1,
            status='STUDYING',
            date_of_birth=datetime.date(2010, 1, 15)
        )
        self.student_tuan = Student.objects.create(
            student_code='HS1002',
            full_name='Lê Minh Tuấn',
            gender='M',
            school_class=self.class_10a1,
            status='STUDYING',
            date_of_birth=datetime.date(2010, 5, 20)
        )
        self.student_binh = Student.objects.create(
            student_code='HS1003',
            full_name='Trần Thái Bình',
            gender='M',
            school_class=self.class_10a1,
            status='STUDYING',
            date_of_birth=datetime.date(2010, 8, 10)
        )
        self.student_le_an = Student.objects.create(
            student_code='HS1004',
            full_name='Lê Bảo An',
            gender='F',
            school_class=self.class_10a1,
            status='STUDYING',
            date_of_birth=datetime.date(2010, 3, 12)
        )
        self.student_suspended = Student.objects.create(
            student_code='HS1005',
            full_name='Hoàng Đình Đạt',
            gender='M',
            school_class=self.class_10a1,
            status='SUSPENDED',
            date_of_birth=datetime.date(2010, 11, 2)
        )

        # Student in 10A2
        self.student_10a2 = Student.objects.create(
            student_code='HS2001',
            full_name='Vũ Thu Thảo',
            gender='F',
            school_class=self.class_10a2,
            status='STUDYING',
            date_of_birth=datetime.date(2010, 4, 18)
        )

    # 1. GVCN access assigned classes
    def test_01_gvcn_access_assigned_classes(self):
        self.client.force_authenticate(user=self.gvcn_user)
        response = self.client.get('/api/conduct/teacher-classes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        class_ids = [c['id'] for c in response.data]
        self.assertIn(self.class_10a1.id, class_ids)
        self.assertNotIn(self.class_10a2.id, class_ids)
        item = next(c for c in response.data if c['id'] == self.class_10a1.id)
        self.assertEqual(item['assignment_role'], 'GVCN')

    # 2. GVBM access assigned classes with subjects
    def test_02_gvbm_access_assigned_classes(self):
        self.client.force_authenticate(user=self.gvbm_user)
        response = self.client.get('/api/conduct/teacher-classes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        class_ids = [c['id'] for c in response.data]
        self.assertIn(self.class_10a1.id, class_ids)
        self.assertNotIn(self.class_10a2.id, class_ids)
        item = next(c for c in response.data if c['id'] == self.class_10a1.id)
        self.assertEqual(item['assignment_role'], 'GVBM')
        self.assertIn('Toán', item['subjects'])

    # 3. Class students roster sorted by Vietnamese name order
    def test_03_class_students_roster_vietnamese_sort(self):
        self.client.force_authenticate(user=self.gvcn_user)
        response = self.client.get(f'/api/conduct/teacher-classes/{self.class_10a1.id}/students/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        students = response.data['students']
        names = [s['full_name'] for s in students]
        # In Vietnamese order: 'Lê Bảo An' comes before 'Nguyễn Văn An' (same first name 'An', 'Lê' < 'Nguyễn')
        # Then 'Trần Thái Bình' (first name 'Bình')
        # Then 'Hoàng Đình Đạt' ('Đạt')
        # Then 'Lê Minh Tuấn' ('Tuấn')
        self.assertEqual(names[0], 'Lê Bảo An')
        self.assertEqual(names[1], 'Nguyễn Văn An')
        self.assertEqual(names[2], 'Trần Thái Bình')
        self.assertEqual(names[3], 'Hoàng Đình Đạt')
        self.assertEqual(names[4], 'Lê Minh Tuấn')

    # 4. Search with diacritics and unaccented query
    def test_04_class_students_search_diacritics(self):
        self.client.force_authenticate(user=self.gvbm_user)
        # Unaccented search "tuan" should match "Lê Minh Tuấn"
        res1 = self.client.get(f'/api/conduct/teacher-classes/{self.class_10a1.id}/students/?search=tuan')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res1.data['students']), 1)
        self.assertEqual(res1.data['students'][0]['full_name'], 'Lê Minh Tuấn')

        # Accented search "Tuấn"
        res2 = self.client.get(f'/api/conduct/teacher-classes/{self.class_10a1.id}/students/?search=Tuấn')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res2.data['students']), 1)
        self.assertEqual(res2.data['students'][0]['full_name'], 'Lê Minh Tuấn')

    # 5. Filter students by status
    def test_05_class_students_filter_status(self):
        self.client.force_authenticate(user=self.gvcn_user)
        response = self.client.get(f'/api/conduct/teacher-classes/{self.class_10a1.id}/students/?status=SUSPENDED')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['students']), 1)
        self.assertEqual(response.data['students'][0]['student_code'], 'HS1005')

    # 6. Feedback creation with 8 standardized categories and priority
    def test_06_feedback_creation_success(self):
        self.client.force_authenticate(user=self.gvbm_user)
        payload = {
            'student_id': self.student_tuan.id,
            'feedback_type': StudentFeedback.TYPE_ACADEMIC,
            'priority': StudentFeedback.PRIORITY_ATTENTION,
            'visibility_scope': StudentFeedback.SCOPE_HOMEROOM_AND_TEACHERS,
            'content': 'Em Tuấn có nhiều cố gắng trong giờ học Toán, làm bài tập đầy đủ.',
            'strengths': 'Chăm chỉ, tích cực phát biểu.',
            'weaknesses': 'Cần rèn luyện thêm kỹ năng tính toán phân số.',
            'cooperation_proposal': 'Nhờ GVCN nhắc nhở em duy trì phong độ.',
        }
        response = self.client.post('/api/conduct/feedbacks/', data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['feedback_code'].startswith('PH-'))
        self.assertEqual(response.data['status'], 'SENT')
        self.assertEqual(response.data['teacher_role'], 'GVBM')
        self.assertEqual(response.data['subject'], 'Toán')

        # Check in-app notification sent to GVCN
        notif = Notification.objects.filter(recipient=self.gvcn_user).first()
        self.assertIsNotNone(notif)
        self.assertIn('Lê Minh Tuấn', notif.title)

    # 7. Feedback NEVER creates violation and NEVER deducts competition points
    def test_07_feedback_does_not_create_violation_or_deduct_points(self):
        self.client.force_authenticate(user=self.gvbm_user)
        initial_violations_count = ViolationRecord.objects.count()
        payload = {
            'student_id': self.student_tuan.id,
            'feedback_type': StudentFeedback.TYPE_DISCIPLINE,
            'priority': StudentFeedback.PRIORITY_NORMAL,
            'content': 'Em nói chuyện riêng 1 lần trong giờ học.',
        }
        response = self.client.post('/api/conduct/feedbacks/', data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ViolationRecord.objects.count(), initial_violations_count)

    # 8. Teacher cannot feedback for student in unassigned class (403 Forbidden)
    def test_08_teacher_cannot_feedback_unassigned_class(self):
        # other_gvbm only teaches 10A2, trying to send feedback to student_tuan in 10A1
        self.client.force_authenticate(user=self.other_gvbm)
        payload = {
            'student_id': self.student_tuan.id,
            'content': 'Em không thuộc lớp của tôi.',
        }
        response = self.client.post('/api/conduct/feedbacks/', data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 9. Teacher cannot view unassigned class students (403 Forbidden)
    def test_09_teacher_cannot_view_unassigned_class_students(self):
        self.client.force_authenticate(user=self.other_gvbm)
        response = self.client.get(f'/api/conduct/teacher-classes/{self.class_10a1.id}/students/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 10. Rapid double submission prevention (debounce/duplicate lock)
    def test_10_duplicate_submission_prevention(self):
        self.client.force_authenticate(user=self.gvbm_user)
        payload = {
            'student_id': self.student_binh.id,
            'content': 'Nội dung phản hồi cần kiểm tra chống gửi lặp.',
        }
        res1 = self.client.post('/api/conduct/feedbacks/', data=payload, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        res2 = self.client.post('/api/conduct/feedbacks/', data=payload, format='json')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('gửi gần đây', res2.data['error'])

    # 11. GVCN marks seen when viewing feedback
    def test_11_gvcn_marks_seen_when_opening_feedback(self):
        fb = StudentFeedback.objects.create(
            student=self.student_an,
            student_name_snapshot=self.student_an.full_name,
            school_class=self.class_10a1,
            class_name_snapshot='10A1',
            teacher=self.gvbm_user,
            teacher_role='GVBM',
            subject='Toán',
            feedback_type=StudentFeedback.TYPE_ATTITUDE,
            content='Học sinh chú ý nghe giảng.',
            status=StudentFeedback.STATUS_SENT
        )
        self.client.force_authenticate(user=self.gvcn_user)
        response = self.client.post(f'/api/conduct/feedbacks/{fb.id}/mark-seen/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fb.refresh_from_db()
        self.assertEqual(fb.status, StudentFeedback.STATUS_SEEN)
        self.assertIn(self.gvcn_user, fb.seen_by.all())
        self.assertIsNotNone(fb.seen_at)

    # 12. Feedback reply workflow (multi-turn discussion and PROCESSING status)
    def test_12_feedback_reply_workflow(self):
        fb = StudentFeedback.objects.create(
            student=self.student_an,
            school_class=self.class_10a1,
            teacher=self.gvbm_user,
            teacher_role='GVBM',
            subject='Toán',
            content='Học sinh cần phối hợp hỗ trợ môn Toán.',
            status=StudentFeedback.STATUS_SENT
        )
        self.client.force_authenticate(user=self.gvcn_user)
        reply_payload = {'content': 'Cảm ơn thầy Hùng, tôi đã trao đổi với phụ huynh em An.'}
        response = self.client.post(f'/api/conduct/feedbacks/{fb.id}/reply/', data=reply_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fb.refresh_from_db()
        self.assertEqual(fb.status, StudentFeedback.STATUS_PROCESSING)
        self.assertEqual(fb.replies.count(), 1)
        self.assertEqual(fb.replies.first().author, self.gvcn_user)

    # 13. Feedback status resolution
    def test_13_feedback_status_resolution(self):
        fb = StudentFeedback.objects.create(
            student=self.student_an,
            school_class=self.class_10a1,
            teacher=self.gvbm_user,
            content='Học sinh đã hoàn thành mục tiêu cải thiện.',
            status=StudentFeedback.STATUS_PROCESSING
        )
        self.client.force_authenticate(user=self.gvcn_user)
        response = self.client.post(f'/api/conduct/feedbacks/{fb.id}/update-status/', data={'status': 'RESOLVED'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fb.refresh_from_db()
        self.assertEqual(fb.status, StudentFeedback.STATUS_RESOLVED)

    # 14. GVBM cannot see HOMEROOM_ONLY feedback written by GVCN
    def test_14_gvbm_cannot_see_homeroom_only_feedback(self):
        # GVCN creates private feedback for student_an
        private_fb = StudentFeedback.objects.create(
            student=self.student_an,
            school_class=self.class_10a1,
            teacher=self.gvcn_user,
            teacher_role='GVCN',
            visibility_scope=StudentFeedback.SCOPE_HOMEROOM_ONLY,
            content='Ghi chú nội bộ gia đình học sinh.',
            status=StudentFeedback.STATUS_SENT
        )
        # gvbm_user queries feedbacks
        self.client.force_authenticate(user=self.gvbm_user)
        response = self.client.get('/api/conduct/feedbacks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fb_ids = [f['id'] for f in response.data.get('results', response.data)]
        self.assertNotIn(private_fb.id, fb_ids)

    # 15. Student profile modal returns 4 tabs data
    def test_15_student_profile_detail_4_tabs(self):
        self.client.force_authenticate(user=self.gvcn_user)
        response = self.client.get(f'/api/conduct/students/{self.student_an.id}/profile-detail/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('general', response.data)
        self.assertIn('feedbacks', response.data)
        self.assertIn('violations', response.data)
        self.assertIn('competition', response.data)
        self.assertEqual(response.data['general']['full_name'], 'Nguyễn Văn An')
        self.assertEqual(response.data['general']['school_class_name'], '10A1')


    # 16. Admin views all classes in the system
    def test_16_admin_views_all_classes(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/conduct/teacher-classes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        class_ids = [c['id'] for c in response.data]
        self.assertIn(self.class_10a1.id, class_ids)
        self.assertIn(self.class_10a2.id, class_ids)
        # Check Admin can view eligible teachers list
        res_teachers = self.client.get('/api/conduct/teacher-classes/eligible-teachers/')
        self.assertEqual(res_teachers.status_code, status.HTTP_200_OK)
        self.assertTrue(len(res_teachers.data) >= 2)

    # 17. Admin assigns homeroom teacher to a class
    def test_17_admin_assigns_homeroom_teacher(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            'teacher_id': self.gvbm_user.id,
            'notes': 'Bổ nhiệm GVCN theo quyết định đầu năm học.'
        }
        response = self.client.post(f'/api/conduct/teacher-classes/{self.class_10a2.id}/assign-homeroom/', data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.class_10a2.refresh_from_db()
        self.assertEqual(self.class_10a2.homeroom_teacher, self.gvbm_user)
        hr_assignment = HomeroomAssignment.objects.filter(school_class=self.class_10a2, is_active=True).first()
        self.assertIsNotNone(hr_assignment)
        self.assertEqual(hr_assignment.teacher, self.gvbm_user)

    # 18. Admin replace homeroom teacher with conflict check & confirmation
    def test_18_admin_replace_homeroom_teacher_conflict_and_confirm(self):
        self.client.force_authenticate(user=self.admin_user)
        # class_10a1 currently has gvcn_user. Trying to appoint other_gvbm without confirmation:
        payload = {
            'teacher_id': self.other_gvbm.id,
            'notes': 'Thay đổi GVCN.'
        }
        res_conflict = self.client.post(f'/api/conduct/teacher-classes/{self.class_10a1.id}/assign-homeroom/', data=payload, format='json')
        self.assertEqual(res_conflict.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(res_conflict.data.get('conflict'))

        # Now confirm replacement:
        payload['confirm_replace'] = True
        res_ok = self.client.post(f'/api/conduct/teacher-classes/{self.class_10a1.id}/assign-homeroom/', data=payload, format='json')
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        self.class_10a1.refresh_from_db()
        self.assertEqual(self.class_10a1.homeroom_teacher, self.other_gvbm)

    # 19. Non-admin cannot assign homeroom teacher (403 Forbidden)
    def test_19_non_admin_cannot_assign_homeroom_teacher(self):
        self.client.force_authenticate(user=self.gvcn_user)
        payload = {'teacher_id': self.other_gvbm.id}
        response = self.client.post(f'/api/conduct/teacher-classes/{self.class_10a2.id}/assign-homeroom/', data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 20. Đoàn trường and Admin can view all classes and any class student roster in the school
    def test_20_doan_truong_and_admin_view_all_classes_and_students(self):
        # 1. Đoàn trường views all classes
        self.client.force_authenticate(user=self.doan_truong_user)
        res_classes = self.client.get('/api/conduct/teacher-classes/')
        self.assertEqual(res_classes.status_code, status.HTTP_200_OK)
        class_ids = [c['id'] for c in res_classes.data]
        self.assertIn(self.class_10a1.id, class_ids)
        self.assertIn(self.class_10a2.id, class_ids)
        for c in res_classes.data:
            self.assertEqual(c['assignment_role'], 'DOAN_TRUONG')
            self.assertEqual(c['assignment_role_display'], 'Bí thư Đoàn trường')

        # 2. Đoàn trường views students of 10A1 (even though not homeroom or teaching)
        res_students = self.client.get(f'/api/conduct/teacher-classes/{self.class_10a1.id}/students/')
        self.assertEqual(res_students.status_code, status.HTTP_200_OK)
        self.assertTrue(len(res_students.data['students']) >= 2)

        # 3. Đoàn trường sends feedback on student in 10A1
        payload = {
            'student_id': self.student_an.id,
            'content': 'Đoàn trường khen ngợi học sinh tích cực tham gia phong trào thanh niên tình nguyện.',
            'feedback_type': StudentFeedback.TYPE_PROGRESS,
            'priority': StudentFeedback.PRIORITY_NORMAL
        }
        res_fb = self.client.post('/api/conduct/feedbacks/', data=payload, format='json')
        self.assertEqual(res_fb.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_fb.data['teacher_role'], 'DOAN_TRUONG')
