import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('conduct/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for j in range(9893, len(lines)):
    line = lines[j]
    if line.startswith('class '):
        print(f"Next class at line {j+1}: {line.strip()}")
        break
    elif line.startswith('    @action') or line.startswith('    def '):
        print(f"Method at line {j+1}: {line.strip()}")
