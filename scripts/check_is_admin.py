import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('core/models.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('def is_admin(')
if idx != -1:
    print(text[idx-50:idx+300])

idx2 = text.find('is_admin =')
if idx2 != -1:
    print(text[idx2-50:idx2+300])
