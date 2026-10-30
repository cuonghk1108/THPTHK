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
from conduct.models import SchoolClass

User = get_user_model()
admin = User.objects.filter(role=User.ROLE_ADMIN).first()
teacher = User.objects.filter(role=User.ROLE_GVBM).first()
sclass = SchoolClass.objects.filter(name='10A1').first()

factory = RequestFactory()
request = factory.post(
    f'/api/conduct/teacher-classes/{sclass.id}/assign-homeroom/',
    data={'teacher_id': teacher.id, 'notes': 'Test assign from teacher-classes', 'confirm_replace': True},
    content_type='application/json'
)
force_authenticate(request, user=admin)

view = TeacherClassViewSet.as_view({'post': 'assign_homeroom'})
res = view(request, pk=sclass.id)
print("Status code:", res.status_code)
print("Response data:", res.data)
