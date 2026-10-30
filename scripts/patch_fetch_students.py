import os, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_JS_PATH = os.path.join(BASE_DIR, 'static', 'app.js')

with open(APP_JS_PATH, 'r', encoding='utf-8') as f:
    js = f.read()

target = """    const data = await res.json();

    teacherStudentsList = data.students || [];
    filterTeacherStudentsList();"""

repl = """    const data = await res.json();

    teacherStudentsList = data.students || [];
    if (activeTeacherClass && activeTeacherClass.id === classId) {
      activeTeacherClass.monitor_id = data.monitor_id;
      activeTeacherClass.monitor_name = data.monitor_name;
      activeTeacherClass.can_assign_monitor = data.can_assign_monitor;
    }
    updateClassMonitorHeader(data.monitor_name, data.can_assign_monitor);
    filterTeacherStudentsList();"""

if target in js:
    js = js.replace(target, repl, 1)
    with open(APP_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(js)
    print("SUCCESS: Updated fetchClassStudents in static/app.js")
else:
    print("FAILED: Target not found")
