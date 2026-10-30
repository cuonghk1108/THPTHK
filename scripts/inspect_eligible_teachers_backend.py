import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('conduct/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('def eligible_teachers(')
print(text[idx:idx+1500])
