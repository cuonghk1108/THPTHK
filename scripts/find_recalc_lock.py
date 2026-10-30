import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'function recalculateScores' in line or 'function toggleLockPeriod' in line:
        print(f'{i+1}: {line.strip()}')
        for j in range(i, min(len(lines), i + 30)):
            print(f'{j+1}: {lines[j].strip()}')
