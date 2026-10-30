import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path: sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')
import django
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from django.contrib.auth import get_user_model
from conduct.models import TeacherClassAssignment

User = get_user_model()
u = User.objects.filter(username='teacher_test_gvcn').first()
if u:
    for tca in TeacherClassAssignment.objects.filter(teacher=u):
        print(f"ID={tca.id}, Class={tca.school_class.name}, Subject={tca.subject}, is_active={tca.is_active}")
