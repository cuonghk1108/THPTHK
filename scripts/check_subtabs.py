import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="tab-teacher-classes"')
idx_end = text.find('</section>', idx)
tab_html = text[idx:idx_end]

buttons = re.findall(r'<button[^>]*switchTeacherSubTab\([^>]*>.*?</button>', tab_html, re.DOTALL)
for b in buttons:
    print(b.strip())
    print('-'*30)
