import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\templates\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'id="tab-conduct"' in l or "id='tab-conduct'" in l:
        print(f'Line {i+1}: {l.strip()[:100]}')
        for j in range(i, min(len(lines), i + 70)):
            print(f'{j+1}: {lines[j].strip()[:140]}')
        break
