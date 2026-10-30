import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('core/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('Notification.objects.create(')
while idx != -1:
    print(text[idx:idx+400])
    print('='*40)
    idx = text.find('Notification.objects.create(', idx+1)
