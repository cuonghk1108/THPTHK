import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('conduct/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

for m in re.finditer(r'TeacherClassAssignment', text):
    idx = m.start()
    print("Match at", idx)
    print(text[max(0, idx-50):min(len(text), idx+200)])
    print("-"*40)
