import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\templates\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if any(k in line for k in ['btn-lock-period', 'btn-recalculate', 'comp-admin-actions', 'openAddBonusModal']):
        print(f'HTML: {i+1}: {line.strip()[:140]}')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if any(k in line for k in ['btn-lock-period', 'btn-recalculate', 'comp-admin-actions', 'openAddBonusModal']):
        print(f'JS: {i+1}: {line.strip()[:140]}')
