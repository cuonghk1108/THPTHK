import sys
import re

sys.stdout.reconfigure(encoding='utf-8')
with open('core/serializers.py', 'r', encoding='utf-8') as f:
    text = f.read()

match = re.search(r'class UserSerializer.*?(?=\nclass |\Z)', text, re.DOTALL)
if match:
    print(match.group(0)[1200:3000])
