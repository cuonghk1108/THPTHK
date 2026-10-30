import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('core/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

content_norm = content.replace('\r\n', '\n')

sync_method_code = '''    def _sync_user_role_and_assignments(self, target_user, assigned_role, data, request):
        """
        Đồng bộ chính xác chức vụ, hồ sơ, phân công giảng dạy (nhiều lớp) và phân công GVCN (1 lớp duy nhất).
        Đảm bảo không bị xung đột, xóa bỏ các gán quyền cũ mâu thuẫn.
        """
        from conduct.models import SchoolClass, Teacher, TeacherClassAssignment, HomeroomAssignment, Student
        import json
        import re

        class_id = data.get('class_id')
        homeroom_class = data.get('homeroom_class')
        homeroom_class_id = data.get('homeroom_class_id')
        subject = data.get('subject')
        subjects = data.get('subjects') or []
        teaching_classes = data.get('teaching_classes') or []
        teaching_class_ids = data.get('teaching_class_ids') or []
        department_or_class = data.get('department_or_class')
        internal_notes = data.get('internal_notes', '')

        if assigned_role in [User.ROLE_GVBM, User.ROLE_GVCN]:
            # 1. Xác định môn học
            subj = (subject or '').strip()
            if not subj and subjects:
                subj = ', '.join([str(s).strip() for s in subjects if str(s).strip()])
            if not subj and department_or_class:
                dept = str(department_or_class).strip()
                if dept.startswith('Môn: '):
                    subj = dept[5:].strip()
                elif dept.startswith('Môn '):
                    subj = dept[4:].strip()
                elif not re.match(r'^\\d+[A-Za-zĐđ]+\\d*$', dept):
                    subj = dept
            if not subj:
                subj = 'Môn học'

            teacher_prof, _ = Teacher.objects.get_or_create(
                user=target_user,
                defaults={
                    'teacher_code': f"GV-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                    'full_name': target_user.full_name or target_user.username,
                    'subject': subj,
                    'phone': target_user.phone or ''
                }
            )
            if subj and teacher_prof.subject != subj:
                teacher_prof.subject = subj
                teacher_prof.save(update_fields=['subject'])

            # 2. Xử lý phân công các lớp giảng dạy (giáo viên được chọn nhiều lớp)
            classes_to_teach = []
            if teaching_class_ids:
                classes_to_teach = list(SchoolClass.objects.filter(id__in=teaching_class_ids, is_active=True))
            elif teaching_classes:
                clean_names = [str(c).strip() for c in teaching_classes if str(c).strip()]
                classes_to_teach = list(SchoolClass.objects.filter(name__in=clean_names, is_active=True))
            elif target_user.verification_info:
                try:
                    v_info = json.loads(target_user.verification_info)
                    if isinstance(v_info, dict):
                        v_c = v_info.get('teaching_classes') or []
                        classes_to_teach = list(SchoolClass.objects.filter(name__in=[str(x).strip() for x in v_c], is_active=True))
                except Exception:
                    pass

            if classes_to_teach:
                TeacherClassAssignment.objects.filter(teacher=target_user, is_active=True).exclude(
                    school_class__in=classes_to_teach
                ).update(is_active=False, end_date=timezone.now().date())

                for sc_obj in classes_to_teach:
                    tca, created = TeacherClassAssignment.objects.get_or_create(
                        teacher=target_user,
                        school_class=sc_obj,
                        subject=subj,
                        defaults={'is_active': True, 'assigned_by': request.user, 'start_date': timezone.now().date()}
                    )
                    if not created and not tca.is_active:
                        tca.is_active = True
                        tca.end_date = None
                        tca.save(update_fields=['is_active', 'end_date', 'updated_at'])
            else:
                TeacherClassAssignment.objects.filter(teacher=target_user, is_active=False).update(is_active=True)

            # 3. Phân công Giáo viên chủ nhiệm (GVCN)
            if assigned_role == User.ROLE_GVCN:
                hr_sc = None
                if homeroom_class_id:
                    hr_sc = SchoolClass.objects.filter(id=homeroom_class_id, is_active=True).first()
                elif homeroom_class:
                    hr_sc = SchoolClass.objects.filter(name__iexact=str(homeroom_class).strip(), is_active=True).first()
                elif department_or_class:
                    hr_sc = SchoolClass.objects.filter(name__iexact=str(department_or_class).strip(), is_active=True).first()

                if hr_sc:
                    # Thu hồi GVCN cũ trên lớp này (nếu đang là giáo viên khác)
                    HomeroomAssignment.objects.filter(school_class=hr_sc, is_active=True).exclude(
                        teacher=target_user
                    ).update(is_active=False, end_date=timezone.now().date())

                    # Thu hồi nhiệm vụ GVCN cũ của giáo viên này trên các lớp khác
                    HomeroomAssignment.objects.filter(teacher=target_user, is_active=True).exclude(
                        school_class=hr_sc
                    ).update(is_active=False, end_date=timezone.now().date())
                    SchoolClass.objects.filter(homeroom_teacher=target_user).exclude(
                        id=hr_sc.id
                    ).update(homeroom_teacher=None)

                    # Bổ nhiệm giáo viên này làm GVCN của hr_sc
                    hr_assign, _ = HomeroomAssignment.objects.get_or_create(
                        teacher=target_user,
                        school_class=hr_sc,
                        is_active=True,
                        defaults={
                            'assigned_by': request.user,
                            'start_date': timezone.now().date(),
                            'notes': internal_notes or 'Phân công GVCN khi xét duyệt / phân quyền'
                        }
                    )
                    if not hr_assign.is_active:
                        hr_assign.is_active = True
                        hr_assign.end_date = None
                        hr_assign.save(update_fields=['is_active', 'end_date', 'updated_at'])

                    hr_sc.homeroom_teacher = target_user
                    hr_sc.save(update_fields=['homeroom_teacher'])

                    target_user.department_or_class = hr_sc.name
                    target_user.save(update_fields=['department_or_class'])
            else:
                # Role là GVBM -> Thu hồi mọi vai trò GVCN trước đó
                SchoolClass.objects.filter(homeroom_teacher=target_user).update(homeroom_teacher=None)
                HomeroomAssignment.objects.filter(teacher=target_user, is_active=True).update(
                    is_active=False, end_date=timezone.now().date()
                )
                target_user.department_or_class = f"Môn {subj}"
                target_user.save(update_fields=['department_or_class'])

        elif assigned_role == User.ROLE_HOC_SINH:
            # Thu hồi nhiệm kỳ GVCN nếu trước đó từng có
            SchoolClass.objects.filter(homeroom_teacher=target_user).update(homeroom_teacher=None)
            HomeroomAssignment.objects.filter(teacher=target_user, is_active=True).update(
                is_active=False, end_date=timezone.now().date()
            )

            sclass = None
            if class_id:
                sclass = SchoolClass.objects.filter(id=class_id, is_active=True).first()
            elif department_or_class:
                sclass = SchoolClass.objects.filter(name__iexact=str(department_or_class).strip(), is_active=True).first()

            if sclass:
                target_user.department_or_class = sclass.name
                target_user.save(update_fields=['department_or_class'])

                student_prof = getattr(target_user, 'student_profile', None)
                if student_prof:
                    student_prof.school_class = sclass
                    student_prof.save(update_fields=['school_class'])
                else:
                    Student.objects.create(
                        user=target_user,
                        defaults={
                            'student_code': f"HK{sclass.grade}-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                            'full_name': target_user.full_name or target_user.username,
                            'date_of_birth': timezone.now().date(),
                            'gender': 'M',
                            'school_class': sclass,
                            'status': 'STUDYING'
                        }
                    )
        else:
            # Các vai trò khác (Admin, Đoàn trường, BGH, Sao đỏ, etc.)
            SchoolClass.objects.filter(homeroom_teacher=target_user).update(homeroom_teacher=None)
            HomeroomAssignment.objects.filter(teacher=target_user, is_active=True).update(
                is_active=False, end_date=timezone.now().date()
            )
            if department_or_class:
                target_user.department_or_class = department_or_class
                target_user.save(update_fields=['department_or_class'])
'''

# Find review() definition to insert helper right before review()
review_def = '    def review(self, request, pk=None):'
assert review_def in content_norm, "review definition not found"
content_norm = content_norm.replace(review_def, sync_method_code + '\n' + review_def)

# Now in review(), replace the old sync block with call to _sync_user_role_and_assignments
old_sync_start = "                # Đồng bộ hồ sơ Teacher / Student nếu chưa có\n                if target_user.role in [User.ROLE_GVBM, User.ROLE_GVCN]:"
old_sync_end = "                Notification.objects.create(\n                    recipient=target_user,"

start_pos = content_norm.find(old_sync_start)
end_pos = content_norm.find(old_sync_end, start_pos)
assert start_pos != -1, "old_sync_start not found"
assert end_pos != -1, "old_sync_end not found"

new_sync_call = """                # Đồng bộ hồ sơ và phân công vai trò (GVCN 1 lớp, giáo viên nhiều lớp, học sinh 1 lớp)
                self._sync_user_role_and_assignments(target_user, assigned_role, serializer.validated_data, request)

"""

content_norm = content_norm[:start_pos] + new_sync_call + content_norm[end_pos:]

# Also update approve_role() to call _sync_user_role_and_assignments if role is changed
old_approve_role_save = """        if phone is not None:
            user_obj.phone = phone.strip()

        user_obj.save()"""

new_approve_role_save = """        if phone is not None:
            user_obj.phone = phone.strip()

        user_obj.save()

        if new_role:
            self._sync_user_role_and_assignments(user_obj, new_role, request.data, request)"""

assert old_approve_role_save in content_norm, "old_approve_role_save not found"
content_norm = content_norm.replace(old_approve_role_save, new_approve_role_save)

with open('core/views.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content_norm)

print("core/views.py patched successfully!")
