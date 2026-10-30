import os
import sys

BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"
conduct_views_path = os.path.join(BASE_DIR, "conduct", "views.py")

with open(conduct_views_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 1. ViolationRecordViewSet create permission
viol_target = "permission_denied(request, message='Chỉ Quản trị viên hoặc Đoàn trường mới có thể chỉnh sửa hoặc xóa bản ghi vi phạm.')"
idx_viol = None
for i, l in enumerate(lines):
    if "Chỉ Quản trị viên hoặc Đoàn trường" in l:
        idx_viol = i
        break

assert idx_viol is not None, "idx_viol not found"
print(f"Found idx_viol at line {idx_viol + 1}")

already_viol = any("Học sinh không có quyền lập biên bản vi phạm" in l for l in lines[idx_viol:idx_viol+25])
if not already_viol:
    code_to_insert = [
        "        if self.action == 'create' and ((request.user.is_student or getattr(request.user, 'role', '') == 'HOC_SINH') and not getattr(request.user, 'is_active_red_star', False)):\n",
        "            self.permission_denied(request, message='Học sinh không có quyền lập biên bản vi phạm.')\n",
    ]
    lines = lines[:idx_viol+1] + code_to_insert + lines[idx_viol+1:]
    print("Inserted violation create check")
else:
    print("Violation create check already present")

# 2. TeacherClassViewSet.list student branch
tc_else_idx = None
for i, l in enumerate(lines):
    if "1. Homeroom assignments" in l:
        for j in range(i-1, max(0, i-20), -1):
            if lines[j].strip() == "else:":
                tc_else_idx = j
                break
        break

assert tc_else_idx is not None, "tc_else_idx not found"
print(f"Found tc_else_idx at line {tc_else_idx + 1}")

already_tc_list = any("assignment_role': 'HOC_SINH'" in l for l in lines[max(0, tc_else_idx-30):tc_else_idx+5])
if not already_tc_list:
    student_tc_branch = [
        "        elif user.is_student or getattr(user, 'role', '') == 'HOC_SINH':\n",
        "            student = getattr(user, 'student_profile', None)\n",
        "            sclass = student.school_class if student else None\n",
        "            if not sclass and user.department_or_class:\n",
        "                sclass = SchoolClass.objects.filter(name__iexact=user.department_or_class.strip(), is_active=True).first()\n",
        "            if sclass:\n",
        "                classes_map[sclass.id] = {\n",
        "                    'id': sclass.id,\n",
        "                    'name': sclass.name,\n",
        "                    'grade': sclass.grade,\n",
        "                    'academic_year_name': sclass.academic_year.name if sclass.academic_year else '',\n",
        "                    'student_count': sclass.students.filter(status='STUDYING').count() or sclass.student_count,\n",
        "                    'assignment_role': 'HOC_SINH',\n",
        "                    'assignment_role_display': f'Học sinh lớp {sclass.name}',\n",
        "                    'subjects': ['Lớp học của tôi'],\n",
        "                    'homeroom_teacher_name': sclass.homeroom_teacher.full_name if sclass.homeroom_teacher else 'Chưa phân công',\n",
        "                    'homeroom_teacher_id': sclass.homeroom_teacher_id,\n",
        "                }\n",
    ]
    lines = lines[:tc_else_idx] + student_tc_branch + lines[tc_else_idx:]
    print("Inserted TeacherClassViewSet.list student branch")
else:
    print("TeacherClassViewSet.list student branch already present")

# 3. TeacherClassViewSet.students access
idx_tc_stu = None
for i, l in enumerate(lines):
    if "def students(self, request, pk=None):" in l:
        for j in range(i, i + 100):
            if "if not has_access:" in lines[j]:
                idx_tc_stu = j
                break
        break

assert idx_tc_stu is not None, "idx_tc_stu not found"
print(f"Found idx_tc_stu at line {idx_tc_stu + 1}")

already_tc_stu = any("student.school_class_id == school_class.id" in l for l in lines[max(0, idx_tc_stu-20):idx_tc_stu])
if not already_tc_stu:
    student_access_code = [
        "        elif user.is_student or getattr(user, 'role', '') == 'HOC_SINH':\n",
        "            student = getattr(user, 'student_profile', None)\n",
        "            if student and student.school_class_id == school_class.id:\n",
        "                has_access = True\n",
        "            elif user.department_or_class and user.department_or_class.strip().lower() == school_class.name.strip().lower():\n",
        "                has_access = True\n",
    ]
    lines = lines[:idx_tc_stu] + student_access_code + lines[idx_tc_stu:]
    print("Inserted TeacherClassViewSet.students student access")
else:
    print("TeacherClassViewSet.students student access already present")

# 4. StudentFeedbackViewSet.get_queryset
idx_fb = None
for i, l in enumerate(lines):
    if "class StudentFeedbackViewSet" in l:
        for j in range(i, i + 120):
            if "if user.is_admin or user.is_bgh or user.is_doan_truong:" in lines[j]:
                for k in range(j, j + 25):
                    if lines[k].strip() == "else:":
                        idx_fb = k
                        break
                break
        break

assert idx_fb is not None, "idx_fb not found"
print(f"Found idx_fb at line {idx_fb + 1}")

already_fb = any("student__user=user" in l for l in lines[max(0, idx_fb-10):idx_fb+10])
if not already_fb:
    fb_student_code = [
        "        elif user.is_student or getattr(user, 'role', '') == 'HOC_SINH':\n",
        "            qs = qs.filter(student__user=user)\n",
        "            return qs\n",
    ]
    lines = lines[:idx_fb] + fb_student_code + lines[idx_fb:]
    print("Inserted StudentFeedbackViewSet student filter")
else:
    print("StudentFeedbackViewSet student filter already present")

with open(conduct_views_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("ALL PATCHES APPLIED SUCCESSFULLY TO conduct/views.py!")
