import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('conduct/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = "homeroom_teacher_name': teacher.full_name or teacher.username"
idx = text.find(target)
if idx != -1:
    print(repr(text[idx:idx+100]))
else:
    print("Not found")
