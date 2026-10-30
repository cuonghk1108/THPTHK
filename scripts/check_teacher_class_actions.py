import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('conduct/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('class TeacherClassViewSet(')
idx_end = text.find('class ', idx+1)
class_text = text[idx:idx_end]

actions = re.findall(r'@action\([^\)]*\)\s*def\s+([a-zA-Z0-9_]+)', class_text)
print("Actions in TeacherClassViewSet:", actions)
