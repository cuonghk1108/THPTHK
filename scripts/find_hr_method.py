import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('conduct/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

current_class = None
for i, line in enumerate(lines):
    if line.startswith('class '):
        current_class = line.strip()
    if 'def assign_homeroom' in line or 'def eligible_teachers' in line:
        print(f"Line {i+1}: {line.strip()} in {current_class}")
