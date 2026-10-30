import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('static/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx1 = text.find('async function openReviewModal(')
idx2 = text.find('async function handleReviewActionSubmit(')
idx3 = text.find('function closeReviewModal(')

print("openReviewModal at:", idx1)
print("closeReviewModal at:", idx3)
print("handleReviewActionSubmit at:", idx2)

print("\n--- openReviewModal start ---")
print(text[idx1:idx1+300])

print("\n--- handleReviewActionSubmit start ---")
print(text[idx2:idx2+300])
