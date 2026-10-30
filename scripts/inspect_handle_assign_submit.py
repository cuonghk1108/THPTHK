import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('static/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('async function handleAssignHomeroomSubmit(')
if idx == -1:
    idx = text.find('function handleAssignHomeroomSubmit(')
print(text[idx:idx+2500])
