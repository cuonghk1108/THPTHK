import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'nav-btn-competition' in line or 'switchTab(\'competition\'' in line or 'switchTab("competition"' in line or 'navigateTab(\'competition\'' in line or 'navigateTab("competition"' in line:
        print(f'{i+1}: {line.strip()[:140]}')

for i, line in enumerate(lines):
    if 'DOAN_TRUONG' in line and ('competition' in line.lower() or 'nav' in line.lower() or 'tab' in line.lower()):
        print(f'DOAN_TRUONG: {i+1}: {line.strip()[:140]}')
