import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('core/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

text_norm = text.replace('\r\n', '\n')

old_code = """                    Student.objects.create(
                        user=target_user,
                        defaults={
                            'student_code': f"HK{sclass.grade}-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                            'full_name': target_user.full_name or target_user.username,
                            'date_of_birth': timezone.now().date(),
                            'gender': 'M',
                            'school_class': sclass,
                            'status': 'STUDYING'
                        }
                    )"""

new_code = """                    Student.objects.get_or_create(
                        user=target_user,
                        defaults={
                            'student_code': f"HK{sclass.grade}-{timezone.now().strftime('%y%m')}-{target_user.id:04d}",
                            'full_name': target_user.full_name or target_user.username,
                            'date_of_birth': timezone.now().date(),
                            'gender': 'M',
                            'school_class': sclass,
                            'status': 'STUDYING'
                        }
                    )"""

assert old_code in text_norm, "old_code not found in core/views.py"
text_norm = text_norm.replace(old_code, new_code)

with open('core/views.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(text_norm)

print("Fixed Student.objects.get_or_create in core/views.py!")
