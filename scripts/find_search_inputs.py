import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\templates\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '<input' in l and ('search' in l.lower() or 'filter' in l.lower() or 'tìm' in l.lower()):
        print(f"{i+1}: {l.strip()[:140]}")
