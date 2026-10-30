import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('core/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'target_user.role in [User.ROLE_GVBM, User.ROLE_GVCN]:' in line:
        for j in range(max(0, i - 10), min(len(lines), i + 80)):
            print(f'{j+1}: {lines[j]}', end='')
        break
