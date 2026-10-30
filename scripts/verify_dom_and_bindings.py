import os
import re

BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"

with open(os.path.join(BASE_DIR, "templates", "index.html"), "r", encoding="utf-8") as f:
    html = f.read()

with open(os.path.join(BASE_DIR, "static", "app.js"), "r", encoding="utf-8") as f:
    js = f.read()

required_html_ids = [
    "subtab-btn-roster",
    "subtab-btn-feedbacks",
    "subtab-btn-teachers",
    "subtab-pane-roster",
    "subtab-pane-feedbacks",
    "subtab-pane-teachers",
    "modal-assign-homeroom-teacher",
    "assign-homeroom-class-select",
    "assign-homeroom-teacher-select",
    "assign-homeroom-notes",
    "assign-homeroom-conflict-box",
    "assign-homeroom-confirm-checkbox",
    "btn-submit-assign-homeroom",
    "btn-revoke-homeroom",
    "modal-assign-subject-teacher",
    "assign-subject-class-select",
    "assign-subject-code-select",
    "assign-subject-teacher-select",
    "assign-subject-conflict-box",
    "btn-submit-assign-subject",
    "class-gvcn-name",
    "class-gvcn-details",
    "class-gvcn-status-badge",
    "btn-pane-revoke-gvcn",
    "class-subject-teachers-tbody",
    "class-subject-teachers-empty",
    "subject-teachers-count-badge",
    "class-teacher-count-badge"
]

missing_ids = [elem_id for elem_id in required_html_ids if f'id="{elem_id}"' not in html]
if missing_ids:
    print(f"FAILED: Missing HTML IDs: {missing_ids}")
else:
    print("PASS: All required HTML IDs are present in templates/index.html")

required_js_exports = [
    "openModal",
    "closeModal",
    "openAssignHomeroomModal",
    "onAssignHomeroomClassSelectChange",
    "handleAssignHomeroomSubmit",
    "handleRevokeHomeroom",
    "revokeHomeroomTeacher",
    "switchTeacherSubTab",
    "loadClassTeachers",
    "openAssignSubjectTeacherModal",
    "onAssignSubjectChange",
    "handleAssignSubjectTeacherSubmit",
    "removeSubjectTeacher"
]

missing_exports = [exp for exp in required_js_exports if f"window.{exp} =" not in js and f"window.{exp}=" not in js]
if missing_exports:
    print(f"FAILED: Missing JS window exports: {missing_exports}")
else:
    print("PASS: All required JS functions are exported to window in static/app.js")
