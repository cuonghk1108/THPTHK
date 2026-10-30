import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'renderLeaderboard' in line or 'switchDashboardTab' in line or 'dash-tab-leaderboard' in line:
        print(f'{i+1}: {line.strip()[:140]}')
