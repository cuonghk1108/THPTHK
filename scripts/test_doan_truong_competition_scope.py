import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Xuan Cuong\Desktop\hk-student-hub')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')

import django
django.setup()

from core.models import User
from competition.services import get_competition_class_scope
from competition.views import CompetitionPeriodViewSet
from competition.models import CompetitionPeriod
from rest_framework.test import APIRequestFactory, force_authenticate

# Find or create a test DOAN_TRUONG user
doan_user = User.objects.filter(role=User.ROLE_DOAN_TRUONG).first()
print(f"Testing with DOAN_TRUONG user: {doan_user}")
if not doan_user:
    print("No DOAN_TRUONG user found in database!")
    sys.exit(1)

scope = get_competition_class_scope(doan_user)
print(f"get_competition_class_scope(doan_user) count: {scope.count()}")

factory = APIRequestFactory()

# Test dashboard action
request = factory.get('/api/competition/periods/dashboard/')
force_authenticate(request, user=doan_user)
view = CompetitionPeriodViewSet.as_view({'get': 'dashboard'})
res = view(request)
print(f"dashboard status: {res.status_code}")
print(f"dashboard classes count: {len(res.data.get('classes', []))}")

# Test scores action on Period 1
p1 = CompetitionPeriod.objects.get(id=1)
request = factory.get(f'/api/competition/periods/{p1.id}/scores/')
force_authenticate(request, user=doan_user)
view_scores = CompetitionPeriodViewSet.as_view({'get': 'scores'})
res_scores = view_scores(request, pk=p1.id)
print(f"scores status: {res_scores.status_code}")
if res_scores.status_code == 200:
    print(f"scores count: {len(res_scores.data.get('scores', []))}")
else:
    print(f"scores data: {res_scores.data}")

# Test class detail action on class 1
request = factory.get(f'/api/competition/periods/{p1.id}/classes/1/detail/')
force_authenticate(request, user=doan_user)
view_detail = CompetitionPeriodViewSet.as_view({'get': 'class_detail'})
res_detail = view_detail(request, pk=p1.id, class_id=1)
print(f"class_detail status: {res_detail.status_code}")
if res_detail.status_code != 200:
    print(f"class_detail error: {res_detail.data}")
