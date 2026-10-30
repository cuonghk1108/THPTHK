import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\core\urls.py', 'r', encoding='utf-8') as f:
    urls = f.read()

print(urls)
