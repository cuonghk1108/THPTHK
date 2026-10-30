import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('static/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

funcs = ['loadEligibleTeachersForHomeroom', 'openAssignHomeroomModal', 'handleAssignHomeroomSubmit', 'renderTeacherClassesBar', 'selectTeacherClass']

for func in funcs:
    match = re.search(r'(?:async\s+)?function\s+' + func + r'\s*\(.*?\n\}', text, re.DOTALL)
    if match:
        print(f"=== {func} ===")
        print(match.group(0)[:1500])
        print("="*40)
    else:
        print(f"=== {func} NOT FOUND ===")
