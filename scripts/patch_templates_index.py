import os

BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"
index_path = os.path.join(BASE_DIR, "templates", "index.html")

with open(index_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace assign buttons with IDs
old_btns = """            <div class="flex items-center gap-2 flex-wrap">
              <button type="button" onclick="openAssignHomeroomModal()" class="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-xl shadow-sm flex items-center gap-1.5 transition">
                <i data-lucide="user-cog" class="w-4 h-4"></i>
                <span>Phân công GVCN</span>
              </button>
              <button type="button" onclick="openAssignSubjectTeacherModal()" class="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-sm flex items-center gap-1.5 transition">
                <i data-lucide="plus" class="w-4 h-4"></i>
                <span>+ Phân công GV Bộ môn</span>
              </button>"""

new_btns = """            <div class="flex items-center gap-2 flex-wrap">
              <button type="button" id="btn-pane-assign-gvcn" onclick="openAssignHomeroomModal()" class="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-xl shadow-sm flex items-center gap-1.5 transition">
                <i data-lucide="user-cog" class="w-4 h-4"></i>
                <span>Phân công GVCN</span>
              </button>
              <button type="button" id="btn-pane-assign-gvbm" onclick="openAssignSubjectTeacherModal()" class="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-sm flex items-center gap-1.5 transition">
                <i data-lucide="plus" class="w-4 h-4"></i>
                <span>+ Phân công GV Bộ môn</span>
              </button>"""

old_change_gvcn = """              <div class="flex items-center gap-2">
                <button type="button" onclick="openAssignHomeroomModal()" class="px-3.5 py-1.5 text-xs font-semibold rounded-xl bg-white border border-blue-200 hover:bg-blue-50 text-blue-700 transition flex items-center gap-1 shadow-2xs">
                  <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                  <span>Đổi GVCN</span>
                </button>"""

new_change_gvcn = """              <div class="flex items-center gap-2">
                <button type="button" id="btn-pane-change-gvcn" onclick="openAssignHomeroomModal()" class="px-3.5 py-1.5 text-xs font-semibold rounded-xl bg-white border border-blue-200 hover:bg-blue-50 text-blue-700 transition flex items-center gap-1 shadow-2xs">
                  <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                  <span>Đổi GVCN</span>
                </button>"""

content_norm = content.replace("\r\n", "\n")

if old_btns in content_norm:
    content_norm = content_norm.replace(old_btns, new_btns)
    print("SUCCESS: Replaced top assign buttons in subtab-pane-teachers")
else:
    print("WARNING: old_btns not found")

if old_change_gvcn in content_norm:
    content_norm = content_norm.replace(old_change_gvcn, new_change_gvcn)
    print("SUCCESS: Replaced change GVCN button")
else:
    print("WARNING: old_change_gvcn not found")

# Also add ID to subject teachers action header
old_th_act = '<th class="py-3 px-4 w-28 text-right">Thao tác</th>'
new_th_act = '<th id="th-subject-teachers-actions" class="py-3 px-4 w-28 text-right">Thao tác</th>'
if old_th_act in content_norm:
    content_norm = content_norm.replace(old_th_act, new_th_act)
    print("SUCCESS: Added ID to th-subject-teachers-actions")
else:
    print("WARNING: old_th_act not found")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(content_norm.replace("\n", "\r\n"))

print("Finished updating templates/index.html")
