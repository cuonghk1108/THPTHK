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

User = get_user_model()
admin = User.objects.filter(role=User.ROLE_ADMIN).first()

factory = RequestFactory()
request = factory.get('/api/conduct/teacher-classes/eligible-teachers/')
force_authenticate(request, user=admin)

view = TeacherClassViewSet.as_view({'get': 'eligible_teachers'})
res = view(request)
print("Status code:", res.status_code)
print("Eligible teachers count:", len(res.data))
for t in res.data:
    print(" -", t)
