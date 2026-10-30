import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('conduct/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for j in range(10350, 10398):
    print(f"{j+1}: {lines[j]}", end='')
