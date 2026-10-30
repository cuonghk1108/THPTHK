import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('core/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(1920, min(len(lines), 1980)):
    print(f'{i+1}: {lines[i]}', end='')
