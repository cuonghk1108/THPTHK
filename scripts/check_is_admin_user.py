import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('static/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

for m in re.finditer(r'function isAdminUser\(', text):
    idx = m.start()
    print("Match at", idx)
    print(text[idx:idx+300])
