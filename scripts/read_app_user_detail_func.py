import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('static/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for j in range(11910, 12065):
    print(f'{j+1:5d}: {lines[j]}', end='')
