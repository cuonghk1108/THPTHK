import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\alerts\models.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'class Meta:' in l:
        print(f"Meta at line {i+1}")
        for j in range(i, min(len(lines), i + 25)):
            print(f"{j+1}: {lines[j].rstrip()}")
