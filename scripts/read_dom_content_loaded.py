import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "document.addEventListener('DOMContentLoaded'" in l:
        print(f"DOMContentLoaded at line {i+1}")
        for j in range(i, min(len(lines), i + 100)):
            print(f"{j+1}: {lines[j].rstrip()}")
        break
