import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('conduct/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines in conduct/views.py: {len(lines)}")
for j in range(9950, min(len(lines), 10070)):
    print(f"{j+1}: {lines[j]}", end='')
