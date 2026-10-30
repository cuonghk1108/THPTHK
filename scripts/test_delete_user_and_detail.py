import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Xuan Cuong\Desktop\hk-student-hub')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')

import django
django.setup()

from core.models import User, AuditLog
from rest_framework.test import APIRequestFactory, force_authenticate
from core.views import UserManagementViewSet

factory = APIRequestFactory()

admin = User.objects.filter(is_superuser=True).first() or User.objects.filter(role=User.ROLE_ADMIN).first()
doan = User.objects.filter(role=User.ROLE_DOAN_TRUONG).first()
gvcn = User.objects.filter(role=User.ROLE_GVCN).first()

print(f"Admin: {admin.username}")

# 1. Create a dummy test user to delete
dummy_user, created = User.objects.get_or_create(
    username="test_user_to_delete_999",
    defaults={
        'full_name': "Nguyễn Văn Test Xóa",
        'email': "test_delete_999@test.com",
        'role': User.ROLE_HOC_SINH,
        'account_status': User.STATUS_PENDING
    }
)
print(f"Dummy user created/found: {dummy_user.id} ({dummy_user.username})")

view = UserManagementViewSet.as_view({'delete': 'destroy', 'get': 'retrieve'})

# Test A: GVCN tries to delete -> should be 403 Forbidden
req_gvcn = factory.delete(f'/api/core/users/{dummy_user.id}/')
force_authenticate(req_gvcn, user=gvcn)
res_gvcn = view(req_gvcn, pk=dummy_user.id)
print(f"Test A (GVCN delete): status={res_gvcn.status_code} (Expected 403)")
assert res_gvcn.status_code == 403, f"Expected 403, got {res_gvcn.status_code}"

# Test B: Admin tries to delete themselves -> should be 400 Bad Request
req_self = factory.delete(f'/api/core/users/{admin.id}/')
force_authenticate(req_self, user=admin)
res_self = view(req_self, pk=admin.id)
print(f"Test B (Admin self-delete): status={res_self.status_code} (Expected 400)")
assert res_self.status_code == 400, f"Expected 400, got {res_self.status_code}"

# Test C: Admin retrieves user detail -> should be 200 OK
req_detail = factory.get(f'/api/core/users/{dummy_user.id}/')
force_authenticate(req_detail, user=admin)
res_detail = view(req_detail, pk=dummy_user.id)
print(f"Test C (Admin retrieve detail): status={res_detail.status_code} (Expected 200)")
assert res_detail.status_code == 200, f"Expected 200, got {res_detail.status_code}"
assert res_detail.data['username'] == dummy_user.username

# Test D: Admin deletes dummy user -> should be 200 OK
req_del = factory.delete(f'/api/core/users/{dummy_user.id}/')
force_authenticate(req_del, user=admin)
res_del = view(req_del, pk=dummy_user.id)
print(f"Test D (Admin delete dummy user): status={res_del.status_code} message={res_del.data.get('message')}")
assert res_del.status_code == 200, f"Expected 200, got {res_del.status_code}"

# Verify dummy user no longer exists in DB
user_exists = User.objects.filter(id=dummy_user.id).exists()
print(f"Dummy user exists in DB: {user_exists} (Expected False)")
assert not user_exists, "User still exists in DB!"

# Verify AuditLog created
audit_log = AuditLog.objects.filter(action='DELETE_USER', resource_id=str(dummy_user.id)).first()
print(f"AuditLog created: {audit_log is not None} - Details: {audit_log.details if audit_log else None}")
assert audit_log is not None, "AuditLog was not created!"

print("ALL USER DELETION & DETAIL TESTS PASSED SUCCESSFULLY!")
