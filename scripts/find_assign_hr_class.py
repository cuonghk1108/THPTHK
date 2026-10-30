import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.py') and not f.startswith('.'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
            if 'def assign_homeroom' in c:
                print("Found in:", path)
                for line in c.splitlines():
                    if 'def assign_homeroom' in line or 'class ' in line:
                        print("  ", line)
