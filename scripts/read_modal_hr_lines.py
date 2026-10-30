import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('templates/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'id="modal-assign-homeroom-teacher"' in line:
        for j in range(i, min(len(lines), i + 70)):
            print(f"{j+1}: {lines[j]}", end='')
        break
