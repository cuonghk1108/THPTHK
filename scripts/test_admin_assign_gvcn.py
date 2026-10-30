import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')
import django
django.setup()

import unittest
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import force_authenticate
from core.views import UserManagementViewSet
from conduct.models import SchoolClass, AcademicYear, Teacher, TeacherClassAssignment, HomeroomAssignment, Student

User = get_user_model()

class TestAdminAssignGVCN(unittest.TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.year, _ = AcademicYear.objects.get_or_create(
            name='2026-2027',
            defaults={'start_date': '2026-09-01', 'end_date': '2027-06-30', 'is_current': True}
        )
        self.class10a1, _ = SchoolClass.objects.get_or_create(
            name='10A1',
            grade=10,
            academic_year=self.year,
            defaults={'class_order': 1, 'is_active': True}
        )
        self.class10a2, _ = SchoolClass.objects.get_or_create(
            name='10A2',
            grade=10,
            academic_year=self.year,
            defaults={'class_order': 2, 'is_active': True}
        )
        self.class11a1, _ = SchoolClass.objects.get_or_create(
            name='11A1',
            grade=11,
            academic_year=self.year,
            defaults={'class_order': 1, 'is_active': True}
        )

        self.admin_user, _ = User.objects.get_or_create(
            username='admin_test_gvcn',
            defaults={'role': User.ROLE_ADMIN, 'account_status': User.STATUS_APPROVED, 'is_staff': True, 'is_active': True}
        )

        self.teacher_user, _ = User.objects.get_or_create(
            username='teacher_test_gvcn',
            defaults={'role': User.ROLE_GVBM, 'account_status': User.STATUS_APPROVED, 'is_active': True, 'full_name': 'Nguyễn Văn Test'}
        )

        self.student_user, _ = User.objects.get_or_create(
            username='student_test_assign',
            defaults={'role': User.ROLE_HOC_SINH, 'account_status': User.STATUS_APPROVED, 'is_active': True, 'full_name': 'Trần Văn Học Sinh'}
        )

        # Clean assignments before each test
        TeacherClassAssignment.objects.filter(teacher=self.teacher_user).delete()
        HomeroomAssignment.objects.filter(teacher=self.teacher_user).delete()
        self.class10a1.homeroom_teacher = None
        self.class10a1.save(update_fields=['homeroom_teacher'])
        self.class10a2.homeroom_teacher = None
        self.class10a2.save(update_fields=['homeroom_teacher'])
        Student.objects.filter(user=self.student_user).delete()

    def test_assign_gvcn_with_homeroom_and_teaching_classes(self):
        view = UserManagementViewSet.as_view({'post': 'review'})

        # Assign GVCN to 10A1, teaching 10A1, 10A2, 11A1, subject: Vật lí
        data = {
            'action': 'approve',
            'assigned_role': 'GVCN',
            'homeroom_class': '10A1',
            'homeroom_class_id': self.class10a1.id,
            'subject': 'Vật lí',
            'teaching_classes': ['10A1', '10A2', '11A1'],
            'internal_notes': 'Thử nghiệm phân công GVCN 10A1'
        }

        request = self.factory.post(f'/api/core/users/{self.teacher_user.id}/review/', data=data, content_type='application/json')
        force_authenticate(request, user=self.admin_user)
        response = view(request, pk=self.teacher_user.id)

        self.assertEqual(response.status_code, 200, response.data)
        self.teacher_user.refresh_from_db()
        self.class10a1.refresh_from_db()

        # Check user role & department
        self.assertEqual(self.teacher_user.role, User.ROLE_GVCN)
        self.assertEqual(self.teacher_user.department_or_class, '10A1')

        # Check SchoolClass homeroom_teacher
        self.assertEqual(self.class10a1.homeroom_teacher, self.teacher_user)

        # Check HomeroomAssignment active
        hr_assign = HomeroomAssignment.objects.filter(teacher=self.teacher_user, school_class=self.class10a1, is_active=True).first()
        self.assertIsNotNone(hr_assign)

        # Check Teacher profile subject
        self.assertEqual(self.teacher_user.teacher_profile.subject, 'Vật lí')

        # Check Teaching assignments count
        teaching_count = TeacherClassAssignment.objects.filter(teacher=self.teacher_user, is_active=True).count()
        self.assertEqual(teaching_count, 3)

        # TEST: Switch homeroom class to 10A2
        data2 = {
            'action': 'approve',
            'assigned_role': 'GVCN',
            'homeroom_class': '10A2',
            'homeroom_class_id': self.class10a2.id,
            'subject': 'Vật lí',
            'teaching_classes': ['10A2', '11A1'],
        }
        request2 = self.factory.post(f'/api/core/users/{self.teacher_user.id}/review/', data=data2, content_type='application/json')
        force_authenticate(request2, user=self.admin_user)
        response2 = view(request2, pk=self.teacher_user.id)
        self.assertEqual(response2.status_code, 200)

        self.teacher_user.refresh_from_db()
        self.class10a1.refresh_from_db()
        self.class10a2.refresh_from_db()

        # 10A1 should no longer have teacher as homeroom
        self.assertIsNone(self.class10a1.homeroom_teacher)
        # 10A2 should now have teacher as homeroom
        self.assertEqual(self.class10a2.homeroom_teacher, self.teacher_user)
        # Old assignment for 10A1 inactive, new for 10A2 active
        self.assertFalse(HomeroomAssignment.objects.filter(teacher=self.teacher_user, school_class=self.class10a1, is_active=True).exists())
        self.assertTrue(HomeroomAssignment.objects.filter(teacher=self.teacher_user, school_class=self.class10a2, is_active=True).exists())

    def test_switch_role_from_gvcn_to_gvbm(self):
        view = UserManagementViewSet.as_view({'post': 'review'})

        # Change role to GVBM
        data = {
            'action': 'approve',
            'assigned_role': 'GVBM',
            'subject': 'Toán học',
            'teaching_classes': ['10A1'],
        }
        request = self.factory.post(f'/api/core/users/{self.teacher_user.id}/review/', data=data, content_type='application/json')
        force_authenticate(request, user=self.admin_user)
        response = view(request, pk=self.teacher_user.id)
        self.assertEqual(response.status_code, 200)

        self.teacher_user.refresh_from_db()
        self.class10a2.refresh_from_db()

        self.assertEqual(self.teacher_user.role, User.ROLE_GVBM)
        self.assertIsNone(self.class10a2.homeroom_teacher)
        self.assertFalse(HomeroomAssignment.objects.filter(teacher=self.teacher_user, is_active=True).exists())

    def test_assign_student_class(self):
        view = UserManagementViewSet.as_view({'post': 'review'})

        # Assign student to 11A1
        data = {
            'action': 'approve',
            'assigned_role': 'HOC_SINH',
            'class_id': self.class11a1.id,
            'department_or_class': '11A1',
        }
        request = self.factory.post(f'/api/core/users/{self.student_user.id}/review/', data=data, content_type='application/json')
        force_authenticate(request, user=self.admin_user)
        response = view(request, pk=self.student_user.id)
        self.assertEqual(response.status_code, 200)

        self.student_user.refresh_from_db()
        self.assertEqual(self.student_user.department_or_class, '11A1')
        self.assertEqual(self.student_user.student_profile.school_class, self.class11a1)

if __name__ == '__main__':
    unittest.main()
