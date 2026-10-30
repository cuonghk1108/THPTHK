import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('conduct/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('def assign_homeroom(')
print(text[idx+2500:idx+5500])
