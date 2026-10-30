import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\templates\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    l = line.lower()
    if 'competition' in l or 'thi đua' in l:
        if any(k in l for k in ['nav', 'button', 'switchtab', 'role-', 'data-tab', 'id="tab-', "id='tab-"]):
            print(f'{i+1}: {line.strip()[:140]}')
