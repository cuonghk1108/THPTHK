import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('core/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

text_norm = text.replace('\r\n', '\n')

old_code = """            if classes_to_teach:
                TeacherClassAssignment.objects.filter(teacher=target_user, is_active=True).exclude(
                    school_class__in=classes_to_teach
                ).update(is_active=False, end_date=timezone.now().date())"""

new_code = """            if classes_to_teach:
                # Deactivate assignments not in classes_to_teach
                TeacherClassAssignment.objects.filter(teacher=target_user, is_active=True).exclude(
                    school_class__in=classes_to_teach
                ).update(is_active=False, end_date=timezone.now().date())
                # Deactivate assignments in classes_to_teach with old subject
                TeacherClassAssignment.objects.filter(teacher=target_user, is_active=True, school_class__in=classes_to_teach).exclude(
                    subject=subj
                ).update(is_active=False, end_date=timezone.now().date())"""

assert old_code in text_norm, "old_code not found in core/views.py"
text_norm = text_norm.replace(old_code, new_code)

with open('core/views.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(text_norm)

print("Updated TeacherClassAssignment subject sync in core/views.py!")
