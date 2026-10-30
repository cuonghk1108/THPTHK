import os, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from conduct.views import SchoolClassViewSet, StudentViewSet
from conduct.models import SchoolClass, Student

User = get_user_model()
factory = APIRequestFactory()

print("="*60)
print("1. VERIFYING SCHOOL CLASS VIEWSET (TẤT CẢ 64 LỚP)")
print("="*60)

admin = User.objects.filter(role=User.ROLE_ADMIN).first()
gvcn = User.objects.filter(role=User.ROLE_GVCN).first()
gvbm = User.objects.filter(role=User.ROLE_GVBM).first()
saodo = User.objects.filter(role=User.ROLE_SAO_DO).first()
student = User.objects.filter(role=User.ROLE_HOC_SINH).exclude(id__in=User.objects.filter(role=User.ROLE_SAO_DO).values_list('id', flat=True)).first()
# Make sure student is not active red star
for s in User.objects.filter(role=User.ROLE_HOC_SINH):
    if not s.is_active_red_star:
        student = s
        break

view = SchoolClassViewSet.as_view({'get': 'list'})

for u, role_name in [(admin, "Admin"), (gvcn, "GVCN"), (gvbm, "GVBM"), (saodo, "Sao Đỏ")]:
    req = factory.get('/api/conduct/classes/')
    force_authenticate(req, user=u)
    res = view(req)
    assert res.status_code == 200, f"Expected 200 for {role_name}, got {res.status_code}"
    assert isinstance(res.data, list), f"Expected list response for {role_name}, got {type(res.data)}"
    assert len(res.data) == 64, f"Expected 64 classes for {role_name}, got {len(res.data)}"
    print(f"PASS: {role_name} receives all {len(res.data)} active classes across school")

# Test grade filters
for g, expected_count in [(10, 22), (11, 21), (12, 21)]:
    req = factory.get(f'/api/conduct/classes/?grade={g}')
    force_authenticate(req, user=gvcn)
    res = view(req)
    assert len(res.data) == expected_count, f"Expected {expected_count} classes for Khối {g}, got {len(res.data)}"
    # Verify class names start with grade
    assert all(c['grade'] == g for c in res.data)
    print(f"PASS: Filter grade={g} returns exactly {len(res.data)} classes (Khối {g})")

# Test regular student
req = factory.get('/api/conduct/classes/')
force_authenticate(req, user=student)
res = view(req)
assert len(res.data) == 1, f"Expected 1 class for regular student, got {len(res.data)}"
print(f"PASS: Regular student ({student.username}) receives only their own class ({res.data[0]['name']})")

print("\n" + "="*60)
print("2. VERIFYING STUDENT VIEWSET FOR VIOLATION RECORDING")
print("="*60)

# Check students in class 1
cls1 = SchoolClass.objects.first()
stu_count_cls1 = Student.objects.filter(school_class=cls1).count()
stu_view = StudentViewSet.as_view({'get': 'list'})

req_stu = factory.get(f'/api/conduct/students/?class_id={cls1.id}')
force_authenticate(req_stu, user=gvbm)
res_stu = stu_view(req_stu)
assert res_stu.status_code == 200
assert isinstance(res_stu.data, list), f"Expected list for students, got {type(res_stu.data)}"
assert len(res_stu.data) == stu_count_cls1
print(f"PASS: GVBM can fetch all {len(res_stu.data)} students of class '{cls1.name}' for violation/feedback recording")

print("\n" + "="*60)
print("3. VERIFYING TEMPLATES AND STATIC FILES")
print("="*60)

with open('templates/index.html', 'r', encoding='utf-8') as f:
    index_html = f.read()

assert 'id="modal-violation-grade"' in index_html, "Missing #modal-violation-grade in index.html"
assert 'id="modal-violation-class"' in index_html, "Missing #modal-violation-class in index.html"
assert 'id="violation-class-count-badge"' in index_html, "Missing #violation-class-count-badge in index.html"
assert 'handleGradeChangeForViolation(this.value)' in index_html, "Missing handleGradeChangeForViolation in index.html"
assert 'app.js?v=20261029_violation_grade_class' in index_html, "Missing updated app.js version in index.html"
print("PASS: templates/index.html contains all 2 cascading select elements and count badge")

with open('static/app.js', 'r', encoding='utf-8') as f:
    app_js = f.read()

assert 'function naturalSortClasses' in app_js, "Missing naturalSortClasses in app.js"
assert 'function populateModalViolationClasses' in app_js, "Missing populateModalViolationClasses in app.js"
assert 'function handleGradeChangeForViolation' in app_js, "Missing handleGradeChangeForViolation in app.js"
assert 'openQuickViolationModal' in app_js, "Missing openQuickViolationModal in app.js"
assert 'populateModalViolationClasses(' in app_js, "Missing populateModalViolationClasses call"
print("PASS: static/app.js contains all required cascading logic and natural sorting")

print("\n" + "="*60)
print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
print("="*60)
