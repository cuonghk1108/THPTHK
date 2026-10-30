# -*- coding: utf-8 -*-
import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

test_file = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub\conduct\test_teacher_classes_and_feedback.py"

with open(test_file, "r", encoding="utf-8") as f:
    code = f.read()

target_setup = """        # Admin User
        self.admin_user = User.objects.create_user(
            username='admin_boss',
            password='password123',
            full_name='Phạm Quản Trị',
            role=User.ROLE_ADMIN,
            account_status=User.STATUS_APPROVED
        )"""

replacement_setup = """        # Admin User
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
        )"""

new_test = """
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
            'student_id': self.student_1.id,
            'content': 'Đoàn trường khen ngợi học sinh tích cực tham gia phong trào thanh niên tình nguyện.',
            'feedback_type': StudentFeedback.TYPE_PROGRESS,
            'priority': StudentFeedback.PRIORITY_NORMAL
        }
        res_fb = self.client.post('/api/conduct/student-feedback/', data=payload, format='json')
        self.assertEqual(res_fb.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_fb.data['teacher_role'], 'DOAN_TRUONG')
"""

if target_setup in code:
    code = code.replace(target_setup, replacement_setup)
    code = code.strip() + "\n" + new_test
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(code)
    print("SUCCESS: test_20 added to test_teacher_classes_and_feedback.py!")
else:
    print("WARNING: target_setup not found.")
