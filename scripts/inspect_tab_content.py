import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="tab-teacher-classes"')
idx_end = text.find('</section>', idx)
print(text[idx+7000:idx+15000])
