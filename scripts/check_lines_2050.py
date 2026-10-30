import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('core/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(2050, min(len(lines), 2090)):
    print(f'{i+1}: {lines[i]}', end='')
