import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'btn-recalculate-score|btn-lock-period', text)]
print(f'Matches in app.js: {len(matches)}')
for m in matches:
    print(text[max(0, m-50):min(len(text), m+150)])
