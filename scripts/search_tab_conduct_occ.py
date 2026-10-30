import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'tab-conduct|Quản lý nề nếp', text, re.IGNORECASE)]
print(f"Occurrences: {len(matches)}")
for m in matches:
    print(text[max(0, m-50):min(len(text), m+150)])
    print('='*50)
