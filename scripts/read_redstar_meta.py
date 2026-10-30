import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\conduct\models.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'class RedStarReport' in l:
        print(f"RedStarReport at {i+1}")
        for j in range(i, min(len(lines), i + 80)):
            if 'class Meta:' in lines[j]:
                print(f"Meta at {j+1}")
                for k in range(j, min(len(lines), j + 15)):
                    print(f"{k+1}: {lines[k].rstrip()}")
                break
        break
