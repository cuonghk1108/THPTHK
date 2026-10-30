# -*- coding: utf-8 -*-
NEW_TESTS = '''
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
'''

target_path = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\conduct\test_teacher_classes_and_feedback.py'
with open(target_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'def test_16_admin_views_all_classes(' not in content:
    content += "\n" + NEW_TESTS
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Added tests 16-19 to test_teacher_classes_and_feedback.py")
else:
    print("ALREADY EXISTS")
