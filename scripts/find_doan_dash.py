import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'renderDoanTruongDashboard' in line or ('isDoanTruong' in line and 'html +=' in line):
        print(f'{i+1}: {line.strip()[:140]}')
        for j in range(max(0, i-5), min(len(lines), i + 60)):
            print(f'{j+1}: {lines[j].strip()[:140]}')
        break
