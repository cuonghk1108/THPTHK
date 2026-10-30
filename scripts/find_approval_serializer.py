import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('core/serializers.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'class ApprovalActionSerializer' in line:
        for j in range(i, min(len(lines), i + 40)):
            print(f'{j+1}: {lines[j]}', end='')
        break
