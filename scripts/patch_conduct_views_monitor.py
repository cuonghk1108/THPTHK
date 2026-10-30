import os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

path = r'conduct/views.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update ViolationRecordViewSet.get_queryset for student monitor
old_vr_student = r'(\s*elif user\.is_student:.*?)(\s*if hasattr\(user, \'student_profile\'\):.*?)(\s*qs = qs\.filter\(student=user\.student_profile\).*?)(\s*else:.*?\s*qs = qs\.none\(\))'

new_vr_student = """        elif user.is_student:
            if hasattr(user, 'student_profile'):
                student = user.student_profile
                if getattr(student, 'is_class_monitor', False) or (student.school_class and student.school_class.monitor_id == student.id):
                    # Lớp trưởng được xem toàn bộ vi phạm của lớp mình để khiếu nại những lỗi sai của lớp
                    qs = qs.filter(school_class=student.school_class)
                else:
                    # Học sinh bình thường CHỈ thấy vi phạm của bản thân mình
                    qs = qs.filter(student=student)
            else:
                qs = qs.none()"""

m1 = re.search(old_vr_student, text, flags=re.DOTALL)
if m1:
    text = text[:m1.start()] + new_vr_student + text[m1.end():]
    print("Updated ViolationRecordViewSet.get_queryset for monitor.")
else:
    print("WARNING: old_vr_student pattern not found!")

# 2. Update ViolationRecordViewSet.appeal permissions
old_appeal_perm = r'(# Kiểm tra quyền: Chỉ học sinh liên quan, GVCN của lớp đó hoặc Admin mới được gửi giải trình.*?)(if not \(is_owner_student or is_homeroom or user\.is_admin\):)'

new_appeal_perm = """# Kiểm tra quyền: Học sinh liên quan, GVCN của lớp đó, Lớp trưởng của lớp đó, Đoàn trường hoặc Admin
        is_owner_student = hasattr(user, 'student_profile') and violation.student_id == user.student_profile.id
        is_homeroom = user.is_gvcn and (
            violation.school_class.homeroom_teacher_id == user.id or
            HomeroomAssignment.objects.filter(school_class=violation.school_class, teacher=user, is_active=True).exists()
        )
        is_monitor = (
            hasattr(user, 'student_profile') and
            (getattr(user.student_profile, 'is_class_monitor', False) or (violation.school_class and violation.school_class.monitor_id == user.student_profile.id)) and
            violation.school_class_id == user.student_profile.school_class_id
        )

        if not (is_owner_student or is_homeroom or is_monitor or user.is_admin or user.is_doan_truong):"""

m2 = re.search(old_appeal_perm, text, flags=re.DOTALL)
if m2:
    text = text[:m2.start()] + new_appeal_perm + text[m2.end():]
    print("Updated ViolationRecordViewSet.appeal permissions for monitor.")
else:
    print("WARNING: old_appeal_perm pattern not found!")

# 3. In TeacherClassViewSet.list: add monitor_id, monitor_name, can_assign_monitor
# In admin dict:
admin_cls_pat = r"('homeroom_teacher_id': c\.homeroom_teacher_id,)"
def replace_admin_cls(match):
    return match.group(1) + "\n                    'monitor_id': c.monitor_id,\n                    'monitor_name': c.monitor.full_name if c.monitor else None,\n                    'can_assign_monitor': True,"

text = re.sub(admin_cls_pat, replace_admin_cls, text, count=1)
print("Updated admin classes in TeacherClassViewSet.list.")

# In student dict:
stu_cls_pat = r"('homeroom_teacher_id': sclass\.homeroom_teacher_id,)"
def replace_stu_cls(match):
    return match.group(1) + "\n                    'monitor_id': sclass.monitor_id,\n                    'monitor_name': sclass.monitor.full_name if sclass.monitor else None,\n                    'can_assign_monitor': False,"

text = re.sub(stu_cls_pat, replace_stu_cls, text, count=1)
print("Updated student classes in TeacherClassViewSet.list.")

# In homeroom dict:
hr_cls_pat = r"('homeroom_teacher_id': user\.id,)"
def replace_hr_cls(match):
    return match.group(1) + "\n                    'monitor_id': c.monitor_id,\n                    'monitor_name': c.monitor.full_name if c.monitor else None,\n                    'can_assign_monitor': True,"

text = re.sub(hr_cls_pat, replace_hr_cls, text, count=1)
print("Updated homeroom classes in TeacherClassViewSet.list.")

# In teaching dict:
tea_cls_pat = r"('homeroom_teacher_id': c\.homeroom_teacher_id,\s*\})"
def replace_tea_cls(match):
    return "'homeroom_teacher_id': c.homeroom_teacher_id,\n                        'monitor_id': c.monitor_id,\n                        'monitor_name': c.monitor.full_name if c.monitor else None,\n                        'can_assign_monitor': False,\n                    }"

text = re.sub(tea_cls_pat, replace_tea_cls, text, count=1)
print("Updated teaching classes in TeacherClassViewSet.list.")

# 4. In TeacherClassViewSet.students: add is_class_monitor and class monitor info
stu_item_pat = r"('feedback_count': fb_counts\.get\(s\.id, 0\),)"
def replace_stu_item(match):
    return match.group(1) + "\n                'is_class_monitor': bool(getattr(s, 'is_class_monitor', False) or (school_class.monitor_id == s.id)),"

text = re.sub(stu_item_pat, replace_stu_item, text, count=1)
print("Updated student items with is_class_monitor.")

stu_resp_pat = r"return Response\({\s*'class_id': school_class\.id,\s*'class_name': school_class\.name,\s*'grade': school_class\.grade,\s*'total_students': len\(students_list\),\s*'students': students_list\s*}\)"
new_stu_resp = """return Response({
            'class_id': school_class.id,
            'class_name': school_class.name,
            'grade': school_class.grade,
            'monitor_id': school_class.monitor_id,
            'monitor_name': school_class.monitor.full_name if school_class.monitor else None,
            'can_assign_monitor': bool(
                user.is_admin or user.is_bgh or user.is_doan_truong or
                (user.is_gvcn and (school_class.homeroom_teacher_id == user.id or HomeroomAssignment.objects.filter(school_class=school_class, teacher=user, is_active=True).exists()))
            ),
            'total_students': len(students_list),
            'students': students_list
        })"""

m3 = re.search(stu_resp_pat, text, flags=re.DOTALL)
if m3:
    text = text[:m3.start()] + new_stu_resp + text[m3.end():]
    print("Updated TeacherClassViewSet.students response.")
else:
    print("WARNING: stu_resp_pat not found!")

# 5. Add assign_monitor action to TeacherClassViewSet
new_assign_action = """    @action(detail=True, methods=['post'], url_path='assign-monitor')
    def assign_monitor(self, request, pk=None):
        \"\"\"
        Đoàn trường, Admin, và Giáo viên chủ nhiệm của lớp có quyền phân công hoặc hủy Lớp trưởng.
        \"\"\"
        user = request.user
        school_class = get_object_or_404(SchoolClass, pk=pk)

        # RBAC Check: Only Admin, BGH, Đoàn trường, or GVCN of THIS specific class
        is_admin_or_doan = user.is_admin or user.is_bgh or user.is_doan_truong
        is_homeroom_of_class = user.is_gvcn and (
            school_class.homeroom_teacher_id == user.id or
            HomeroomAssignment.objects.filter(school_class=school_class, teacher=user, is_active=True).exists()
        )

        if not (is_admin_or_doan or is_homeroom_of_class):
            return Response(
                {'error': 'Chỉ Quản trị viên, Đoàn trường hoặc Giáo viên chủ nhiệm của lớp này mới có quyền phân công Lớp trưởng.'},
                status=status.HTTP_403_FORBIDDEN
            )

        student_id = request.data.get('student_id')
        if student_id:
            student = get_object_or_404(Student, pk=student_id, school_class=school_class)
            # Remove previous monitors of this class
            Student.objects.filter(school_class=school_class, is_class_monitor=True).exclude(pk=student.id).update(is_class_monitor=False)
            student.is_class_monitor = True
            student.save(update_fields=['is_class_monitor'])
            school_class.monitor = student
            school_class.save(update_fields=['monitor'])

            try:
                AuditLog.objects.create(
                    user=user,
                    action='ASSIGN_MONITOR',
                    resource_type='SCHOOL_CLASS',
                    resource_id=school_class.name,
                    details=f"Phân công học sinh {student.full_name} ({student.student_code}) làm Lớp trưởng lớp {school_class.name}"
                )
            except Exception:
                pass

            return Response({
                'success': True,
                'message': f'Đã phân công học sinh {student.full_name} làm Lớp trưởng lớp {school_class.name}.',
                'class_id': school_class.id,
                'monitor_id': student.id,
                'monitor_name': student.full_name,
                'monitor_student_code': student.student_code,
            })
        else:
            # Unassign monitor
            if school_class.monitor:
                prev_monitor = school_class.monitor
                prev_monitor.is_class_monitor = False
                prev_monitor.save(update_fields=['is_class_monitor'])
            Student.objects.filter(school_class=school_class, is_class_monitor=True).update(is_class_monitor=False)
            school_class.monitor = None
            school_class.save(update_fields=['monitor'])

            try:
                AuditLog.objects.create(
                    user=user,
                    action='REMOVE_MONITOR',
                    resource_type='SCHOOL_CLASS',
                    resource_id=school_class.name,
                    details=f"Hủy phân công Lớp trưởng lớp {school_class.name}"
                )
            except Exception:
                pass

            return Response({
                'success': True,
                'message': f'Đã hủy phân công Lớp trưởng lớp {school_class.name}.',
                'class_id': school_class.id,
                'monitor_id': None,
                'monitor_name': None,
                'monitor_student_code': None,
            })

"""

# Insert assign_monitor right before eligible_teachers
el_pat = r"(\s*@action\(detail=False, methods=\['get'\], url_path='eligible-teachers'\))"
text = re.sub(el_pat, "\n\n" + new_assign_action + r"\1", text, count=1)
print("Inserted assign_monitor action into TeacherClassViewSet.")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("conduct/views.py successfully updated!")
