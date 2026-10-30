import os, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(username='hocsinh.nam')
print("role:", u.role)
print("is_admin:", u.is_admin)
print("is_bgh:", u.is_bgh)
print("is_doan_truong:", u.is_doan_truong)
print("is_gvcn:", u.is_gvcn)
print("is_gvbm:", u.is_gvbm)
print("is_active_red_star:", u.is_active_red_star)
print("is_student:", u.is_student)
print("student_profile:", getattr(u, 'student_profile', None))
if hasattr(u, 'student_profile'):
    print("student_profile.school_class_id:", u.student_profile.school_class_id)
