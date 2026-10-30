import os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

file_path = r'templates/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the single class div in quick-violation-form
target_html_pattern = r'<div>\s*<label class="block font-semibold text-slate-700 mb-1">1\. Lớp học vi phạm <span class="text-rose-500">\*</span></label>\s*<select id="modal-violation-class"[^>]*>.*?</select>\s*</div>'

replacement_html = '''<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">1a. Khối lớp</label>
            <select id="modal-violation-grade" onchange="handleGradeChangeForViolation(this.value)" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-brand-500">
              <option value="">-- Tất cả khối (64 lớp) --</option>
              <option value="10">Khối 10 (22 lớp)</option>
              <option value="11">Khối 11 (21 lớp)</option>
              <option value="12">Khối 12 (21 lớp)</option>
            </select>
          </div>
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="block font-semibold text-slate-700">1b. Lớp học vi phạm <span class="text-rose-500">*</span></label>
              <span id="violation-class-count-badge" class="text-[11px] text-brand-600 font-semibold"></span>
            </div>
            <select id="modal-violation-class" required onchange="handleClassChangeForStudents(this.value)" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-brand-500">
              <option value="">-- Chọn lớp học --</option>
            </select>
          </div>
        </div>'''

m = re.search(target_html_pattern, content, flags=re.DOTALL)
if not m:
    print("ERROR: target_html_pattern not found in templates/index.html!")
    sys.exit(1)

content = content[:m.start()] + replacement_html + content[m.end():]
print("Replaced class input with Grade + Class 2-dropdown grid in index.html.")

# Update script tag version
content = re.sub(r'app\.js\?v=20261029_gvbm_feedback', 'app.js?v=20261029_violation_grade_class', content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully patched templates/index.html!")
