import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('static/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx2 = text.find('async function handleReviewActionSubmit(')
idx_end = text.find('\n}\n', idx2)
print(text[idx2:idx_end+10])
