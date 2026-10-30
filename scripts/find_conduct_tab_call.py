import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "'conduct'" in l and ('tabName' in l or 'activeTab' in l or 'switchTab' in l or 'loadConduct' in l or 'initConduct' in l):
        print(f'{i+1}: {l.strip()[:140]}')
