import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('static/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('toggleConfirmReplaceCheckbox')
print("toggleConfirmReplaceCheckbox found at:", idx)
