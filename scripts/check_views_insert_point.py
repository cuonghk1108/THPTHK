import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('conduct/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = "'homeroom_teacher_name': teacher.full_name or teacher.username,"
idx = text.find(target)
assert idx != -1, "Target in conduct/views.py not found"

end_block = text.find("class StudentFeedbackViewSet(", idx)
assert end_block != -1, "StudentFeedbackViewSet not found"

print("Block found. Preview of end of TeacherClassViewSet:")
print(text[idx:idx+300])
