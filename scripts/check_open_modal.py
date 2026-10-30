import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('static/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function openModal(')
print("openModal found at:", idx)

idx2 = text.find('function closeModal(')
print("closeModal found at:", idx2)
