import os, sys
sys.stdout.reconfigure(encoding='utf-8')
path = r'conduct/serializers.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()
idx1 = text.find('class SchoolClassSerializer')
idx2 = text.find('class StudentSerializer')
print(repr(text[idx1:idx2]))
