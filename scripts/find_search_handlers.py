import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if any(k in l for k in ['onkeyup', 'oninput', 'debounce', 'competitionSearchQuery', 'filter-student-search']):
        print(f"{i+1}: {l.strip()[:140]}")
