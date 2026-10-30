import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('core/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('def approve_role(self, request, pk=None):')
if idx != -1:
    print(text[idx:idx+1500])
