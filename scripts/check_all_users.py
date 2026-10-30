import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path: sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')
import django
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from django.contrib.auth import get_user_model
User = get_user_model()

print(f"Total users: {User.objects.count()}")
for u in User.objects.all():
    print(f"ID={u.id}, username={u.username}, name='{u.full_name}', role={u.role}, status={u.account_status}, is_active={u.is_active}, dept='{u.department_or_class}'")
