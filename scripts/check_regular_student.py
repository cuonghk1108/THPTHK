import os, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
for u in User.objects.filter(role=User.ROLE_HOC_SINH):
    if not u.is_active_red_star:
        print("Regular student:", u.username)
        break
