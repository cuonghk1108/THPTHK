import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('conduct/urls.py', 'r', encoding='utf-8') as f:
    print(f.read())
