import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('conduct/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for j in range(10200, min(len(lines), 10320)):
    if lines[j].strip().startswith('class ') or lines[j].strip().startswith('@action') or lines[j].strip().startswith('return Response'):
        print(f"{j+1}: {lines[j]}", end='')
