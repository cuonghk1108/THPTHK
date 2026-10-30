import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('core/serializers.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.startswith('class UserSerializer('):
        print(f"UserSerializer at line {i+1}")
        for j in range(i, min(len(lines), i + 60)):
            print(f'{j+1}: {lines[j]}', end='')
        break
