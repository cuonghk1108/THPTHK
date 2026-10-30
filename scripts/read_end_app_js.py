from pathlib import Path

APP_JS_PATH = Path(r"C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js")
with open(APP_JS_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(len(lines) - 30, len(lines)):
    line = lines[i].encode('ascii', 'backslashreplace').decode('ascii')
    print(f"{i+1}: {line}", end='')
