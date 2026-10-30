import sys
import re

sys.stdout.reconfigure(encoding='utf-8')
with open('static/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Look for school class endpoints and globals
endpoints = set(re.findall(r'/api/[a-zA-Z0-9_\-/]*(?:classes|school-classes)[a-zA-Z0-9_\-/]*', text))
print("Endpoints:", endpoints)

# Look for global arrays of classes
for m in re.finditer(r'(?:let|const|var)\s+([a-zA-Z0-9_]*class[a-zA-Z0-9_]*)\s*=', text, re.IGNORECASE):
    print("Class variable:", m.group(0))
