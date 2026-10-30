import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'DOAN_TRUONG' in line or 'is_doan_truong' in line:
        print(f'{i+1}: {line.strip()[:140]}')
