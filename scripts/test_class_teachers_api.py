import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path: sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')
import django
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import force_authenticate
from conduct.views import TeacherClassViewSet
from conduct.models import SchoolClass, TeacherClassAssignment

User = get_user_model()
admin = User.objects.filter(role=User.ROLE_ADMIN).first()
teacher = User.objects.filter(role__in=[User.ROLE_GVBM, User.ROLE_GVCN], account_status=User.STATUS_APPROVED).first()
sclass = SchoolClass.objects.filter(name='10A1').first()

factory = RequestFactory()

# 1. Test assign_subject_teacher
view_assign = TeacherClassViewSet.as_view({'post': 'assign_subject_teacher'})
req1 = factory.post(
    f'/api/conduct/teacher-classes/{sclass.id}/assign-subject-teacher/',
    data={'teacher_id': teacher.id, 'subject': 'Toán học'},
    content_type='application/json'
)
force_authenticate(req1, user=admin)
res1 = view_assign(req1, pk=sclass.id)
assert res1.status_code == 200, res1.data
print("Test 1 PASS: assign_subject_teacher:", res1.data['message'])

# 2. Test assigned_teachers
view_list = TeacherClassViewSet.as_view({'get': 'assigned_teachers'})
req2 = factory.get(f'/api/conduct/teacher-classes/{sclass.id}/assigned-teachers/')
force_authenticate(req2, user=admin)
res2 = view_list(req2, pk=sclass.id)
assert res2.status_code == 200, res2.data
print("Test 2 PASS: assigned_teachers:", len(res2.data['subject_teachers']), "subject teachers found")

# 3. Test remove_subject_teacher
view_remove = TeacherClassViewSet.as_view({'post': 'remove_subject_teacher'})
req3 = factory.post(
    f'/api/conduct/teacher-classes/{sclass.id}/remove-subject-teacher/',
    data={'teacher_id': teacher.id, 'subject': 'Toán học'},
    content_type='application/json'
)
force_authenticate(req3, user=admin)
res3 = view_remove(req3, pk=sclass.id)
assert res3.status_code == 200, res3.data
print("Test 3 PASS: remove_subject_teacher:", res3.data['message'])

print("ALL BACKEND TESTS PASSED!")
