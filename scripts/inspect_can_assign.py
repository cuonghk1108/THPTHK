import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('static/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find("const adminBtn = document.getElementById('btn-admin-assign-homeroom');")
print(text[max(0, idx-500):min(len(text), idx+500)])
