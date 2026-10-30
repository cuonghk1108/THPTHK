import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('static/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

for m in re.finditer(r'(?:openModal|closeModal)\s*\(', text):
    idx = m.start()
    print("Call at", idx, ":", text[idx:idx+60].strip())
