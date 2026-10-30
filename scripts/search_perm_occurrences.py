import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

for root_dir in [r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\competition', r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\reports']:
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            if f.endswith('.py'):
                p = os.path.join(root, f)
                with open(p, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                for i, line in enumerate(lines):
                    if any(k in line for k in ['is_admin or', 'is_bgh', 'is_doan_truong', 'get_competition_class_scope', 'may_view_unpublished', 'is_published']):
                        rel = os.path.relpath(p, r'C:\Users\Xuan Cuong\Desktop\hk-student-hub')
                        print(f'{rel}:{i+1}: {line.strip()[:120]}')
