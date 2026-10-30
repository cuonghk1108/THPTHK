import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('conduct/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('class TeacherClassViewSet(')
print(text[idx:idx+2500])
