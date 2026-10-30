import os, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from conduct.models import SchoolClass, Student, ViolationRecord, ConductRule, ConductRuleCategory
from conduct.views import TeacherClassViewSet, ViolationRecordViewSet

User = get_user_model()
factory = APIRequestFactory()

print("="*60)
print("TESTING LỚP TRƯỞNG PERMISSIONS & APPEAL WORKFLOW")
print("="*60)

# Setup data
cls = SchoolClass.objects.filter(is_active=True).first()
other_cls = SchoolClass.objects.filter(is_active=True).exclude(id=cls.id).first()

admin = User.objects.filter(role=User.ROLE_ADMIN).first()
doan_truong = User.objects.filter(role=User.ROLE_DOAN_TRUONG).first()
gvcn_this = cls.homeroom_teacher
if not gvcn_this:
    gvcn_this = User.objects.filter(role=User.ROLE_GVCN).first()
    cls.homeroom_teacher = gvcn_this
    cls.save()

gvcn_other = other_cls.homeroom_teacher
if not gvcn_other or gvcn_other.id == gvcn_this.id:
    gvcn_other = User.objects.filter(role=User.ROLE_GVCN).exclude(id=gvcn_this.id).first()

gvbm = User.objects.filter(role=User.ROLE_GVBM).first()

# Pick 2 students in class
students = list(Student.objects.filter(school_class=cls, status='STUDYING')[:2])
if len(students) < 2:
    # Ensure students exist
    from datetime import date
    u1, _ = User.objects.get_or_create(username='test.student1', defaults={'role': User.ROLE_HOC_SINH, 'full_name': 'Học Sinh Một'})
    s1, _ = Student.objects.get_or_create(student_code='HS001', defaults={'full_name': 'Học Sinh Một', 'school_class': cls, 'date_of_birth': date(2008, 1, 1), 'user': u1})
    u2, _ = User.objects.get_or_create(username='test.student2', defaults={'role': User.ROLE_HOC_SINH, 'full_name': 'Học Sinh Hai'})
    s2, _ = Student.objects.get_or_create(student_code='HS002', defaults={'full_name': 'Học Sinh Hai', 'school_class': cls, 'date_of_birth': date(2008, 1, 2), 'user': u2})
    students = [s1, s2]

stu1, stu2 = students[0], students[1]
if not stu1.user:
    u1, _ = User.objects.get_or_create(username='test.stu1.user', defaults={'role': User.ROLE_HOC_SINH, 'full_name': stu1.full_name})
    stu1.user = u1
    stu1.save()
if not stu2.user:
    u2, _ = User.objects.get_or_create(username='test.stu2.user', defaults={'role': User.ROLE_HOC_SINH, 'full_name': stu2.full_name})
    stu2.user = u2
    stu2.save()

view_tc = TeacherClassViewSet.as_view({'post': 'assign_monitor', 'get': 'students'})

print(f"\n[TEST 1] Unauthorized users CANNOT assign Lớp trưởng for class {cls.name}")
for u, label in [(gvbm, "GVBM"), (stu1.user, "Student"), (gvcn_other, "GVCN of other class")]:
    if not u: continue
    req = factory.post(f'/api/conduct/teacher-classes/{cls.id}/assign-monitor/', {'student_id': stu1.id}, format='json')
    force_authenticate(req, user=u)
    res = view_tc(req, pk=cls.id)
    assert res.status_code == 403, f"Expected 403 for {label}, got {res.status_code}"
    print(f"PASS: {label} blocked with 403 Forbidden")

print(f"\n[TEST 2] GVCN of this class CAN assign Lớp trưởng")
req = factory.post(f'/api/conduct/teacher-classes/{cls.id}/assign-monitor/', {'student_id': stu1.id}, format='json')
force_authenticate(req, user=gvcn_this)
res = view_tc(req, pk=cls.id)
assert res.status_code == 200, f"Expected 200 for GVCN, got {res.status_code}: {res.data}"
cls.refresh_from_db()
stu1.refresh_from_db()
assert cls.monitor_id == stu1.id
assert stu1.is_class_monitor is True
assert stu1.user.is_class_monitor is True
print(f"PASS: GVCN assigned {stu1.full_name} as monitor of {cls.name}")

print(f"\n[TEST 3] Admin & Đoàn trường CAN assign Lớp trưởng")
req = factory.post(f'/api/conduct/teacher-classes/{cls.id}/assign-monitor/', {'student_id': stu2.id}, format='json')
force_authenticate(req, user=admin)
res = view_tc(req, pk=cls.id)
assert res.status_code == 200
cls.refresh_from_db()
stu1.refresh_from_db()
stu2.refresh_from_db()
assert cls.monitor_id == stu2.id
assert stu2.is_class_monitor is True
assert stu1.is_class_monitor is False, "Previous monitor should be unassigned"
print(f"PASS: Admin changed monitor to {stu2.full_name}, previous monitor unassigned")

if doan_truong:
    req = factory.post(f'/api/conduct/teacher-classes/{cls.id}/assign-monitor/', {'student_id': stu1.id}, format='json')
    force_authenticate(req, user=doan_truong)
    res = view_tc(req, pk=cls.id)
    assert res.status_code == 200
    cls.refresh_from_db()
    stu1.refresh_from_db()
    stu2.refresh_from_db()
    if hasattr(stu2, 'user') and stu2.user:
        stu2.user.refresh_from_db()
        if hasattr(stu2.user, 'student_profile'):
            stu2.user.student_profile.refresh_from_db()
    assert cls.monitor_id == stu1.id
    print(f"PASS: Đoàn trường assigned monitor to {stu1.full_name}")

print(f"\n[TEST 4] TeacherClassViewSet.students returns monitor info & can_assign_monitor")
req = factory.get(f'/api/conduct/teacher-classes/{cls.id}/students/')
force_authenticate(req, user=gvcn_this)
res = view_tc(req, pk=cls.id)
assert res.status_code == 200
assert res.data['monitor_id'] == stu1.id
assert res.data['can_assign_monitor'] is True
stu_item = next(s for s in res.data['students'] if s['id'] == stu1.id)
assert stu_item['is_class_monitor'] is True
print("PASS: TeacherClassViewSet.students accurately exposes monitor and permission flags")

print(f"\n[TEST 5] Lớp trưởng ({stu1.full_name}) can view and appeal violations of their class")
cat, _ = ConductRuleCategory.objects.get_or_create(name='Kỷ luật chung', defaults={'order': 1})
rule, _ = ConductRule.objects.get_or_create(code='KL01', defaults={'name': 'Đi học muộn', 'category': cat, 'default_points_deducted': 2})
# Create a violation for stu2 in class cls
viol, _ = ViolationRecord.objects.get_or_create(
    school_class=cls, student=stu2, rule=rule,
    defaults={'reporter': admin, 'status': ViolationRecord.STATUS_VERIFIED, 'points_deducted': 2}
)
viol.status = ViolationRecord.STATUS_VERIFIED
viol.save()

# Stu1 (monitor) should see this violation even though it is for stu2
view_vr = ViolationRecordViewSet.as_view({'get': 'list', 'post': 'appeal'})
req = factory.get('/api/conduct/violations/')
force_authenticate(req, user=stu1.user)
res = view_vr(req)
assert res.status_code == 200
viols_data = res.data if isinstance(res.data, list) else res.data.get('results', [])
assert any(v['id'] == viol.id for v in viols_data), "Monitor should see class violation"
print(f"PASS: Monitor sees class violation for classmate {stu2.full_name}")

# Stu1 appeals this violation
req = factory.post(f'/api/conduct/violations/{viol.id}/appeal/', {'reason': 'Em là lớp trưởng, bạn có giấy xin phép có xác nhận của phụ huynh'}, format='json')
force_authenticate(req, user=stu1.user)
res = view_vr(req, pk=viol.id)
assert res.status_code == 200, f"Expected 200 for appeal, got {res.status_code}: {res.data}"
viol.refresh_from_db()
assert viol.status == ViolationRecord.STATUS_APPEALING
assert 'giấy xin phép' in viol.appeal_reason
print("PASS: Monitor successfully submitted appeal for class violation")

print(f"\n[TEST 6] Regular student (stu2) CANNOT appeal violation of another student or class-wide")
viol3, _ = ViolationRecord.objects.get_or_create(
    school_class=cls, student=stu1, rule=rule,
    defaults={'reporter': admin, 'status': ViolationRecord.STATUS_VERIFIED, 'points_deducted': 2}
)
viol3.status = ViolationRecord.STATUS_VERIFIED
viol3.save()
req = factory.post(f'/api/conduct/violations/{viol3.id}/appeal/', {'reason': 'Học sinh khác khiếu nại hộ'}, format='json')
force_authenticate(req, user=stu2.user) # stu2 is NOT monitor
res = view_vr(req, pk=viol3.id)
assert res.status_code in [403, 404], f"Expected 403 or 404 for non-monitor non-owner student, got {res.status_code}"
print(f"PASS: Regular student blocked with {res.status_code} when trying to appeal another student's violation")

print("\n" + "="*60)
print("ALL BACKEND LỚP TRƯỞNG & APPEAL TESTS PASSED!")
print("="*60)
