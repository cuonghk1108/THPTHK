import os, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from conduct.models import SchoolClass, Student
from rest_framework.test import APIRequestFactory, force_authenticate
from conduct.views import SchoolClassViewSet, StudentViewSet

User = get_user_model()

print("Active classes in DB:", SchoolClass.objects.filter(is_active=True).count())
for g in [10, 11, 12]:
    print(f"Grade {g}:", SchoolClass.objects.filter(is_active=True, grade=g).count())

factory = APIRequestFactory()
admin = User.objects.filter(role=User.ROLE_ADMIN).first()
gvcn = User.objects.filter(role=User.ROLE_GVCN).first()
gvbm = User.objects.filter(role=User.ROLE_GVBM).first()
student = User.objects.filter(role=User.ROLE_HOC_SINH).first()
saodo = User.objects.filter(role=User.ROLE_SAO_DO).first()

print("\nTesting SchoolClassViewSet before update:")
for u, label in [(admin, "Admin"), (gvcn, "GVCN"), (gvbm, "GVBM"), (saodo, "Sao Đỏ"), (student, "Student")]:
    if not u: continue
    req = factory.get('/api/conduct/classes/')
    force_authenticate(req, user=u)
    view = SchoolClassViewSet.as_view({'get': 'list'})
    res = view(req)
    data = res.data
    count = len(data) if isinstance(data, list) else data.get('count', len(data.get('results', [])))
    print(f"User {label} ({u.username}) -> status {res.status_code}, count: {count}, is_list: {isinstance(data, list)}")
