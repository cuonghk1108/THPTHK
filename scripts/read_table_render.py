import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(5150, min(5280, len(lines))):
    print(f"{i+1}: {lines[i]}", end='')
