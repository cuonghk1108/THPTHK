import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('core/models.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'class Notification.*?(?=\nclass |\Z)', text, re.DOTALL)
if matches:
    print(matches[0][:1500])
