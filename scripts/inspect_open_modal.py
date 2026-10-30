import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('static/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx1 = text.find('async function openReviewModal(')
idx2 = text.find('function closeReviewModal(')
print(text[idx1:idx2])
