import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('conduct/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('class SchoolClassViewSet(')
idx_end = text.find('class ', idx+1)
print("=== SchoolClassViewSet ===")
print(text[idx:idx+2500])
