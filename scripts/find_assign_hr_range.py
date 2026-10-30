import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('conduct/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'def assign_homeroom(self, request, pk=None):' in line:
        print(f"assign_homeroom starts at line {i+1}")
        # Find the end of assign_homeroom
        for j in range(i+1, min(len(lines), i + 200)):
            if lines[j].startswith('    @action') or lines[j].startswith('    def ') or lines[j].startswith('class '):
                print(f"assign_homeroom ends before line {j+1}: {lines[j].strip()}")
                break
        break
