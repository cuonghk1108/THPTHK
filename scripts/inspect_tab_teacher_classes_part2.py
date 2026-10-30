import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="tab-teacher-classes"')
print(text[idx+3500:idx+7500])
