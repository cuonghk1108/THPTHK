import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\templates\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(2650, min(2850, len(lines))):
    print(f"{i+1}: {lines[i]}", end='')
