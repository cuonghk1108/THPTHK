import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('teacher-classes')
while idx != -1:
    print(f"Match at {idx}:")
    print(text[max(0, idx-50):min(len(text), idx+600)])
    print("="*40)
    idx = text.find('teacher-classes', idx+1)
