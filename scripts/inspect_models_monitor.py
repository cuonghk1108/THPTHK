import os, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')
import django
django.setup()

from conduct.models import SchoolClass, Student
from core.models import User

print("SchoolClass fields:", [f.name for f in SchoolClass._meta.fields])
print("Student fields:", [f.name for f in Student._meta.fields])
print("User properties:", [p for p in dir(User) if isinstance(getattr(User, p, None), property)])
