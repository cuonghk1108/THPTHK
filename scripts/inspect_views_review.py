import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('core/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'def review(self, request, pk=None):' in line:
        for j in range(i, min(len(lines), i + 150)):
            print(f'{j+1}: {lines[j]}', end='')
        break
