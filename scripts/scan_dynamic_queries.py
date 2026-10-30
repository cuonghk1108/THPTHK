import os
import re

BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"

patterns = [
    r'\.order_by\s*\(\s*(?:request|params|sort|order)',
    r'\.filter\s*\(\s*\*\*(?:request|params|filters|kwargs)',
    r'connection\.cursor',
    r'execute\s*\(',
]

for root, dirs, files in os.walk(BASE_DIR):
    if any(skip in root for skip in ['.venv', 'staticfiles', '.git']):
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            for idx, line in enumerate(lines):
                for p in patterns:
                    if re.search(p, line):
                        rel = os.path.relpath(path, BASE_DIR)
                        print(f"{rel}:{idx+1} -> {line.strip()}")
