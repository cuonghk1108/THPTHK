import sys
import os
import re

sys.stdout.reconfigure(encoding='utf-8')

root_dir = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub'

for app in ['competition', 'reports', 'conduct', 'core']:
    app_dir = os.path.join(root_dir, app)
    for r, d, files in os.walk(app_dir):
        for f in files:
            if f.endswith('.py') and not f.startswith('00'):
                p = os.path.join(r, f)
                with open(p, 'r', encoding='utf-8') as file:
                    for idx, line in enumerate(file):
                        if 'is_bgh' in line and 'is_doan_truong' not in line:
                            rel = os.path.relpath(p, root_dir)
                            print(f'{rel}:{idx+1}: {line.strip()[:120]}')
