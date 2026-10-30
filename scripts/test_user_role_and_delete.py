import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, r'C:\Users\Xuan Cuong\Desktop\hk-student-hub')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.models import AuditLog

User = get_user_model()

def run_tests():
    print("=== STARTING USER ROLE & DELETION INTEGRATION TESTS ===")
    client = APIClient()

    # 1. Create test admin
    admin, _ = User.objects.get_or_create(
        username='test_admin_suite',
        defaults={
            'email': 'admin_suite@huongkhe.edu.vn',
            'full_name': 'Admin Test Suite',
            'role': User.ROLE_ADMIN,
            'account_status': User.STATUS_APPROVED,
            'is_active': True
        }
    )
    admin.set_password('AdminPass123!')
    admin.role = User.ROLE_ADMIN
    admin.account_status = User.STATUS_APPROVED
    admin.is_active = True
    admin.save()

    # 2. Create target user for role changes
    target, _ = User.objects.get_or_create(
        username='test_user_rolechange',
        defaults={
            'email': 'target_role@huongkhe.edu.vn',
            'full_name': 'Nguyễn Văn Target',
            'role': User.ROLE_HOC_SINH,
            'account_status': User.STATUS_PENDING,
            'requested_role': User.ROLE_GVCN,
            'department_or_class': '10A1',
            'is_active': True
        }
    )
    target.set_password('TargetPass123!')
    target.role = User.ROLE_HOC_SINH
    target.account_status = User.STATUS_PENDING
    target.save()

    # Login as admin
    client.force_authenticate(user=admin)

    # TEST A: Change role to GVCN (approve action)
    print("\n--- TEST A: Approve / Change role to GVCN ---")
    payload = {
        'action': 'approve',
        'assigned_role': 'GVCN',
        'department_or_class': '10A2',
        'can_verify_violations': True,
        'can_view_counseling': False,
        'internal_notes': 'Đã đối soát danh sách GV năm học mới'
    }
    res = client.post(f'/api/core/users/{target.id}/review/', payload, format='json')
    print(f"Status: {res.status_code}, Response: {res.data}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    target.refresh_from_db()
    assert target.role == 'GVCN', f"Role not updated: {target.role}"
    assert target.account_status == User.STATUS_APPROVED, f"Status not approved: {target.account_status}"
    assert target.department_or_class == '10A2'
    assert target.can_verify_violations is True
    print("-> TEST A PASSED: Role successfully changed to GVCN with custom permissions!")

    # TEST B: Suspend account
    print("\n--- TEST B: Suspend user account ---")
    payload_suspend = {
        'action': 'suspend',
        'reason': 'Vi phạm quy chế trường học',
        'internal_notes': 'Tạm khóa để xác minh'
    }
    res = client.post(f'/api/core/users/{target.id}/review/', payload_suspend, format='json')
    print(f"Status: {res.status_code}, Response: {res.data}")
    assert res.status_code == 200
    target.refresh_from_db()
    assert target.account_status == User.STATUS_SUSPENDED
    assert target.rejection_reason == 'Vi phạm quy chế trường học'
    print("-> TEST B PASSED: User successfully suspended!")

    # TEST C: Reactivate account
    print("\n--- TEST C: Reactivate user account ---")
    payload_reactivate = {
        'action': 'reactivate',
        'internal_notes': 'Đã hoàn thành xác minh'
    }
    res = client.post(f'/api/core/users/{target.id}/review/', payload_reactivate, format='json')
    print(f"Status: {res.status_code}, Response: {res.data}")
    assert res.status_code == 200
    target.refresh_from_db()
    assert target.account_status == User.STATUS_APPROVED
    assert target.is_active is True
    print("-> TEST C PASSED: User successfully reactivated!")

    # TEST D: Delete target user
    print("\n--- TEST D: Admin deletes user ---")
    target_id_str = str(target.id)
    res = client.delete(f'/api/core/users/{target.id}/')
    print(f"Status: {res.status_code}, Response: {res.data}")
    assert res.status_code == 200
    assert not User.objects.filter(id=target.id).exists(), "User should be deleted"
    log = AuditLog.objects.filter(action='DELETE_USER', resource_id=target_id_str).first()
    assert log is not None, "AuditLog for delete should be created"
    print(f"-> TEST D PASSED: User deleted and AuditLog logged: {log.details}")

    # TEST E: Self-delete prohibited
    print("\n--- TEST E: Self-delete blocked ---")
    res = client.delete(f'/api/core/users/{admin.id}/')
    print(f"Status: {res.status_code}, Response: {res.data}")
    assert res.status_code == 400
    print("-> TEST E PASSED: Self-delete correctly rejected with 400!")

    # TEST F: Non-admin deletion blocked
    print("\n--- TEST F: Non-admin delete blocked ---")
    student_user, _ = User.objects.get_or_create(
        username='test_student_deleter',
        defaults={
            'email': 'student_deleter@huongkhe.edu.vn',
            'full_name': 'Student Deleter',
            'role': User.ROLE_HOC_SINH,
            'account_status': User.STATUS_APPROVED,
            'is_active': True
        }
    )
    client.force_authenticate(user=student_user)
    res = client.delete(f'/api/core/users/{admin.id}/')
    print(f"Status: {res.status_code}, Response: {res.data}")
    assert res.status_code in [403, 401]
    print("-> TEST F PASSED: Non-admin delete correctly forbidden with 403!")

    # Clean up test accounts
    admin.delete()
    student_user.delete()
    print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")

if __name__ == '__main__':
    run_tests()
