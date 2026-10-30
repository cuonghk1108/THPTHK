import os, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from conduct.views import SchoolClassViewSet

User = get_user_model()
u = User.objects.get(username='google_1170995805')
factory = APIRequestFactory()
req = factory.get('/api/conduct/classes/')
force_authenticate(req, user=u)
view = SchoolClassViewSet.as_view({'get': 'list'})
res = view(req)
print("Regular student class count:", len(res.data))
if res.data:
    print("Class:", res.data[0]['name'])
