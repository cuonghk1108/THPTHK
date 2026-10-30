import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'function loadConductViolations' in l or 'function refreshConduct' in l:
        print(f'{i+1}: {l.strip()[:100]}')
        for j in range(i, min(len(lines), i + 40)):
            print(f'{j+1}: {lines[j].strip()[:140]}')
        break
