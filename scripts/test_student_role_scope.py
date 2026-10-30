import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

sys.stdout.reconfigure(encoding='utf-8')

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hk_hub_project.settings")
django.setup()

from django.test import Client
from django.utils import timezone
from core.models import User
from conduct.models import SchoolClass, AcademicYear, Student, ConductRuleCategory, ConductRule, ViolationRecord, TeacherClassAssignment, HomeroomAssignment
from competition.models import CompetitionPeriod, ClassCompetitionScore

def run_tests():
    print("=== STARTING STUDENT ROLE SCOPE VERIFICATION TESTS ===")
    
    # 1. Setup or get test academic year
    year = AcademicYear.objects.filter(is_current=True).first()
    if not year:
        year = AcademicYear.objects.create(name="2026-2027", is_current=True)
    
    # Setup test teacher
    teacher, _ = User.objects.get_or_create(username="test_gvcn_user", defaults={
        "full_name": "Nguyễn Văn Thầy",
        "email": "gvcn@thpthuongkhe.edu.vn",
        "role": User.ROLE_GVCN,
        "account_status": User.STATUS_APPROVED
    })
    teacher.set_password("pass123")
    teacher.save()

    # Setup test class 1
    class_1, _ = SchoolClass.objects.get_or_create(name="10A1", academic_year=year, defaults={
        "grade": 10,
        "is_active": True,
        "homeroom_teacher": teacher
    })
    
    # Setup test class 2
    class_2, _ = SchoolClass.objects.get_or_create(name="10A2", academic_year=year, defaults={
        "grade": 10,
        "is_active": True
    })

    # Setup test student 1 (in 10A1)
    user_stu1, _ = User.objects.get_or_create(username="test_stu_user1", defaults={
        "full_name": "Trần Học Sinh Một",
        "email": "stu1@thpthuongkhe.edu.vn",
        "role": User.ROLE_HOC_SINH,
        "account_status": User.STATUS_APPROVED,
        "department_or_class": "10A1"
    })
    user_stu1.set_password("pass123")
    user_stu1.role = User.ROLE_HOC_SINH
    user_stu1.account_status = User.STATUS_APPROVED
    user_stu1.department_or_class = "10A1"
    user_stu1.save()

    student_1, _ = Student.objects.get_or_create(student_code="HS001", defaults={
        "user": user_stu1,
        "full_name": user_stu1.full_name,
        "school_class": class_1,
        "status": "STUDYING",
        "gender": "M",
        "date_of_birth": "2009-01-15"
    })
    student_1.school_class = class_1
    student_1.user = user_stu1
    student_1.save()

    # Setup test student 2 (in 10A2)
    user_stu2, _ = User.objects.get_or_create(username="test_stu_user2", defaults={
        "full_name": "Lê Học Sinh Hai",
        "email": "stu2@thpthuongkhe.edu.vn",
        "role": User.ROLE_HOC_SINH,
        "account_status": User.STATUS_APPROVED,
        "department_or_class": "10A2"
    })
    user_stu2.set_password("pass123")
    user_stu2.role = User.ROLE_HOC_SINH
    user_stu2.account_status = User.STATUS_APPROVED
    user_stu2.department_or_class = "10A2"
    user_stu2.save()

    student_2, _ = Student.objects.get_or_create(student_code="HS002", defaults={
        "user": user_stu2,
        "full_name": user_stu2.full_name,
        "school_class": class_2,
        "status": "STUDYING",
        "gender": "F",
        "date_of_birth": "2009-05-20"
    })
    student_2.school_class = class_2
    student_2.user = user_stu2
    student_2.save()

    # Setup rule & violations
    rule = ConductRule.objects.first()
    if not rule:
        cat = ConductRuleCategory.objects.first() or ConductRuleCategory.objects.create(name="Chuyên cần")
        rule = ConductRule.objects.create(code="CC01", name="Đi học muộn", category=cat, default_points_deducted=2.0)

    v1, _ = ViolationRecord.objects.get_or_create(record_code="TEST-V01", defaults={
        "student": student_1,
        "school_class": class_1,
        "rule": rule,
        "reporter": teacher,
        "occurred_at": timezone.now(),
        "points_deducted": 2.0,
        "status": ViolationRecord.STATUS_VERIFIED
    })

    v2, _ = ViolationRecord.objects.get_or_create(record_code="TEST-V02", defaults={
        "student": student_2,
        "school_class": class_2,
        "rule": rule,
        "reporter": teacher,
        "occurred_at": timezone.now(),
        "points_deducted": 2.0,
        "status": ViolationRecord.STATUS_VERIFIED
    })

    client = Client()
    client.force_login(user_stu1)

    print("\n[TEST 1] Route guards for /competition and /conduct")
    resp_comp_route = client.get("/competition")
    assert resp_comp_route.status_code == 302 and resp_comp_route["Location"] == "/dashboard", f"Expected 302 to /dashboard, got {resp_comp_route.status_code}"
    print("PASS: /competition redirected student to /dashboard")

    resp_cond_route = client.get("/conduct")
    assert resp_cond_route.status_code == 302 and resp_cond_route["Location"] == "/dashboard", f"Expected 302 to /dashboard, got {resp_cond_route.status_code}"
    print("PASS: /conduct redirected student to /dashboard")

    print("\n[TEST 2] API Competition Scores Access Control")
    resp_scores = client.get("/api/competition/scores/")
    assert resp_scores.status_code == 403, f"Expected 403 Forbidden, got {resp_scores.status_code}"
    print("PASS: /api/competition/scores/ returned 403 Forbidden for student")

    resp_comp_dash = client.get("/api/competition/periods/dashboard/")
    assert resp_comp_dash.status_code == 200
    comp_dash_data = resp_comp_dash.json()
    assert comp_dash_data.get("classes") == [] and comp_dash_data.get("periods") == {}, f"Expected empty dashboard snapshot, got {comp_dash_data}"
    print("PASS: /api/competition/periods/dashboard/ returned empty competition snapshot for student")

    print("\n[TEST 3] TeacherClassViewSet List (Học sinh chỉ xem lớp của mình)")
    resp_classes = client.get("/api/conduct/teacher-classes/")
    assert resp_classes.status_code == 200
    classes_data = resp_classes.json()
    assert len(classes_data) == 1, f"Expected 1 class, got {len(classes_data)}"
    assert classes_data[0]["id"] == class_1.id, f"Expected class {class_1.id}, got {classes_data[0]['id']}"
    assert classes_data[0]["assignment_role"] == "HOC_SINH"
    print(f"PASS: /api/conduct/teacher-classes/ returned exactly student's class '{classes_data[0]['name']}' with role HOC_SINH")

    print("\n[TEST 4] TeacherClassViewSet Students Access Control")
    # Own class -> 200 OK
    resp_own_students = client.get(f"/api/conduct/teacher-classes/{class_1.id}/students/")
    assert resp_own_students.status_code == 200, f"Expected 200 for own class, got {resp_own_students.status_code}"
    stu_list = resp_own_students.json().get("students", [])
    assert any(s["id"] == student_1.id for s in stu_list)
    print("PASS: Student can view roster of own class")

    # Other class -> 403 Forbidden
    resp_other_students = client.get(f"/api/conduct/teacher-classes/{class_2.id}/students/")
    assert resp_other_students.status_code == 403, f"Expected 403 for other class, got {resp_other_students.status_code}"
    print("PASS: Student CANNOT view roster of other class (403 Forbidden)")

    print("\n[TEST 5] TeacherClassViewSet Assigned Teachers Access Control")
    resp_own_teachers = client.get(f"/api/conduct/teacher-classes/{class_1.id}/assigned-teachers/")
    assert resp_own_teachers.status_code == 200
    print("PASS: Student can view assigned teachers of own class")

    resp_other_teachers = client.get(f"/api/conduct/teacher-classes/{class_2.id}/assigned-teachers/")
    assert resp_other_teachers.status_code == 403
    print("PASS: Student CANNOT view assigned teachers of other class (403 Forbidden)")

    print("\n[TEST 6] Conduct Violations List Filter (Chỉ xem lỗi vi phạm của mình)")
    resp_viols = client.get("/api/conduct/violations/")
    assert resp_viols.status_code == 200
    viols_data = resp_viols.json()
    viol_results = viols_data if isinstance(viols_data, list) else viols_data.get("results", [])
    assert len(viol_results) >= 1
    for item in viol_results:
        assert item["student"] == student_1.id or item.get("student_code") == student_1.student_code, f"Found other student violation: {item}"
    print(f"PASS: /api/conduct/violations/ only returned student's own violations (no violation from student 2)")

    print("\n[TEST 7] Student cannot create violation records")
    resp_create_viol = client.post("/api/conduct/violations/", {
        "student": student_2.id,
        "school_class": class_2.id,
        "rule": rule.id,
        "occurred_at": timezone.now().isoformat()
    })
    assert resp_create_viol.status_code == 403, f"Expected 403 Forbidden, got {resp_create_viol.status_code}"
    print("PASS: Regular student cannot create violation record (403 Forbidden)")

    print("\n[TEST 8] Student Profile Detail Access Control")
    # Viewing own profile -> 200 OK, competition is empty
    resp_own_profile = client.get(f"/api/conduct/students/{student_1.id}/profile-detail/")
    assert resp_own_profile.status_code == 200
    own_prof_data = resp_own_profile.json()
    assert own_prof_data.get("competition") == {}, f"Expected empty competition dict, got {own_prof_data.get('competition')}"
    assert len(own_prof_data.get("violations", [])) >= 1
    print("PASS: Student viewing own profile gets 200 OK and competition data is omitted ({})")

    # Viewing other student profile -> 403 Forbidden or 404 Not Found (hidden by queryset)
    resp_other_profile = client.get(f"/api/conduct/students/{student_2.id}/profile-detail/")
    assert resp_other_profile.status_code in [403, 404], f"Expected 403 or 404, got {resp_other_profile.status_code}"
    print("PASS: Student viewing another student's profile gets 403 Forbidden / 404 Not Found")

    print("\n[TEST 9] System Stats Payload for Student")
    resp_stats = client.get("/api/core/system/stats/")
    assert resp_stats.status_code == 200
    stats_data = resp_stats.json()
    assert stats_data.get("scope") == "student"
    assert stats_data.get("class_score_info") is None, "Expected class_score_info to be None"
    assert "my_violations_list" in stats_data
    assert len(stats_data["my_violations_list"]) >= 1
    assert any(v["rule_name"] == rule.name for v in stats_data["my_violations_list"])
    print("PASS: SystemStatsAPIView returns student violations list and omits class competition ranking")

    print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
