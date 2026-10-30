import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('static/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('return `\n      <button type="button" onclick="selectTeacherClass(${c.id})"')
if idx == -1:
    idx = text.find('onclick="selectTeacherClass(${c.id})"')
print(text[idx:idx+1500])
