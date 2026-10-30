import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('core/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(2010, min(len(lines), 2050)):
    print(f'{i+1}: {lines[i]}', end='')
