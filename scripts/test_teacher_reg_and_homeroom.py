import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, r'C:\Users\Xuan Cuong\Desktop\hk-student-hub')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from conduct.models import SchoolClass, Teacher, TeacherClassAssignment, HomeroomAssignment

User = get_user_model()

def run_tests():
    print("=== STARTING TEACHER REGISTRATION & HOMEROOM ASSIGNMENT INTEGRATION TESTS ===")
    client = APIClient()

    # 0. Ensure school classes exist for grades 10, 11, 12
    c10 = SchoolClass.objects.filter(grade=10, is_active=True).first()
    c11 = SchoolClass.objects.filter(grade=11, is_active=True).first()
    c12 = SchoolClass.objects.filter(grade=12, is_active=True).first()

    assert c10 and c11 and c12, "Active classes for grades 10, 11, 12 must exist in DB"
    print(f"Using test classes: {c10.name} (Grade 10), {c11.name} (Grade 11), {c12.name} (Grade 12)")

    # 1. TEST A: Teacher registers with multiple subjects and multiple classes across grades
    print("\n--- TEST A: Teacher registers with multiple subjects & multiple classes across grades ---")
    reg_payload = {
        'full_name': 'Thầy Giáo Test Toàn Năng',
        'username': 'teacher_test_multiclass',
        'email': 'teacher_multiclass@huongkhe.edu.vn',
        'phone': '0912345678',
        'password': 'SecureTeacherPass123!',
        'confirm_password': 'SecureTeacherPass123!',
        'requested_role': 'GVBM',
        'subjects': ['Toán học', 'Tin học'],
        'teaching_classes': [c10.name, c11.name, c12.name],
        'terms_accepted': True
    }

    # Delete if exists from previous test
    User.objects.filter(username=reg_payload['username']).delete()

    res = client.post('/api/core/auth/register/', reg_payload, format='json')
    print(f"Register status: {res.status_code}, data: {res.data}")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}"

    # Verify User created in DB
    user = User.objects.get(username=reg_payload['username'])
    assert user.account_status == User.STATUS_PENDING
    assert user.role == User.ROLE_GVBM
    assert 'Toán học' in user.department_or_class and 'Tin học' in user.department_or_class

    # Verify Teacher Profile created
    teacher_prof = Teacher.objects.filter(user=user).first()
    assert teacher_prof is not None, "Teacher profile should be created"
    assert 'Toán học' in teacher_prof.subject and 'Tin học' in teacher_prof.subject
    print(f"-> Teacher profile created: {teacher_prof.full_name} - Môn: {teacher_prof.subject}")

    # Verify TeacherClassAssignments pre-created with is_active=False
    assignments = TeacherClassAssignment.objects.filter(teacher=user)
    print(f"Pre-created assignments count: {assignments.count()}")
    assert assignments.count() >= 3, "Assignments for the 3 classes should be pre-created"
    assert all(not a.is_active for a in assignments), "Assignments should be inactive before approval"
    print("-> TEST A PASSED: Teacher successfully registered with multiple subjects & classes across grades!")

    # 2. TEST B: Admin approves teacher -> assignments become active
    print("\n--- TEST B: Admin approves teacher account ---")
    admin, _ = User.objects.get_or_create(
        username='admin_test_approver',
        defaults={
            'email': 'admin_approver@huongkhe.edu.vn',
            'full_name': 'Admin Approver',
            'role': User.ROLE_ADMIN,
            'account_status': User.STATUS_APPROVED,
            'is_active': True
        }
    )
    admin.set_password('AdminPass123!')
    admin.role = User.ROLE_ADMIN
    admin.save()

    client.force_authenticate(user=admin)
    res_approve = client.post(f'/api/core/users/{user.id}/review/', {
        'action': 'approve',
        'assigned_role': 'GVBM',
        'department_or_class': user.department_or_class,
        'can_verify_violations': False,
        'can_view_counseling': False
    }, format='json')
    print(f"Approve status: {res_approve.status_code}, data: {res_approve.data}")
    assert res_approve.status_code == 200

    user.refresh_from_db()
    assert user.account_status == User.STATUS_APPROVED
    assert user.is_active is True

    # Check that teaching assignments are now active
    active_assignments = TeacherClassAssignment.objects.filter(teacher=user, is_active=True)
    assert active_assignments.count() >= 3, "Assignments should be activated upon approval"
    print("-> TEST B PASSED: Teacher approved and assignments successfully activated!")

    # 3. TEST C: Admin assigns teacher as Homeroom Teacher (GVCN) for class
    print(f"\n--- TEST C: Admin assigns teacher as Homeroom Teacher for class {c10.name} ---")
    res_assign = client.post(f'/api/conduct/teacher-classes/{c10.id}/assign-homeroom/', {
        'teacher_id': user.id,
        'notes': 'Phân công GVCN theo quyết định nhà trường',
        'confirm_replace': True
    }, format='json')
    print(f"Assign homeroom status: {res_assign.status_code}, data: {res_assign.data}")
    assert res_assign.status_code == 200

    c10.refresh_from_db()
    assert c10.homeroom_teacher == user, "Class homeroom_teacher should be updated"

    hr_assign = HomeroomAssignment.objects.filter(school_class=c10, teacher=user, is_active=True).first()
    assert hr_assign is not None, "HomeroomAssignment record should be created"

    user.refresh_from_db()
    assert user.role == User.ROLE_GVCN, "Teacher role should be promoted to GVCN"
    print(f"-> TEST C PASSED: Teacher successfully assigned as Homeroom Teacher for {c10.name}!")

    # 4. TEST D: Admin revokes homeroom assignment
    print(f"\n--- TEST D: Admin revokes homeroom assignment for class {c10.name} ---")
    res_revoke = client.post(f'/api/conduct/teacher-classes/{c10.id}/assign-homeroom/', {
        'teacher_id': None
    }, format='json')
    print(f"Revoke homeroom status: {res_revoke.status_code}, data: {res_revoke.data}")
    assert res_revoke.status_code == 200

    c10.refresh_from_db()
    assert c10.homeroom_teacher is None, "Class homeroom_teacher should be None after revoke"
    print("-> TEST D PASSED: Homeroom assignment successfully revoked!")

    # Clean up test accounts
    user.delete()
    admin.delete()
    print("\n=== ALL INTEGRATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == '__main__':
    run_tests()
