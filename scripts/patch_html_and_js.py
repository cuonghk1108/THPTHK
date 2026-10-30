import os, sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, 'templates', 'index.html')
APP_JS_PATH = os.path.join(BASE_DIR, 'static', 'app.js')

print("Patching templates/index.html...")
with open(INDEX_PATH, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update active-class header in tab-teacher-classes
target_header = """              <div class="flex items-center flex-wrap gap-2">

                <p id="active-class-desc" class="text-xs text-slate-500 font-medium">Sĩ số: -- • GVCN: --</p>

                <button type="button" id="btn-admin-assign-homeroom-inline" onclick="openAssignHomeroomModal()" class="hidden px-2.5 py-1 text-xs font-bold rounded-lg bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition inline-flex items-center gap-1.5">

                  <i data-lucide="user-cog" class="w-3.5 h-3.5"></i>

                  <span>Phân công GVCN</span>

                </button>

              </div>"""

repl_header = """              <div class="flex items-center flex-wrap gap-2">

                <p id="active-class-desc" class="text-xs text-slate-500 font-medium">Sĩ số: -- • GVCN: --</p>

                <span id="active-class-monitor-badge" class="hidden px-2.5 py-0.5 text-xs font-semibold rounded-full bg-amber-50 text-amber-700 border border-amber-200 inline-flex items-center gap-1 shadow-sm">
                  <i data-lucide="crown" class="w-3.5 h-3.5 text-amber-500"></i>
                  <span>Lớp trưởng: <strong id="active-class-monitor-name" class="font-bold text-amber-800">--</strong></span>
                </span>

                <button type="button" id="btn-assign-monitor-header" onclick="openAssignMonitorModal()" class="hidden px-2.5 py-1 text-xs font-bold rounded-lg bg-amber-500 hover:bg-amber-600 text-white shadow-sm transition inline-flex items-center gap-1.5">
                  <i data-lucide="crown" class="w-3.5 h-3.5"></i>
                  <span>Phân Lớp trưởng</span>
                </button>

                <button type="button" id="btn-admin-assign-homeroom-inline" onclick="openAssignHomeroomModal()" class="hidden px-2.5 py-1 text-xs font-bold rounded-lg bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition inline-flex items-center gap-1.5">

                  <i data-lucide="user-cog" class="w-3.5 h-3.5"></i>

                  <span>Phân công GVCN</span>

                </button>

              </div>"""

if target_header in html:
    html = html.replace(target_header, repl_header, 1)
    print("SUCCESS: Patched active-class header in index.html")
else:
    print("WARNING: target_header not found in index.html")

# 2. Add modal-assign-class-monitor after modal-assign-homeroom-teacher
modal_homeroom_end = """      </form>



    </div>



  </div>"""

modal_assign_monitor_html = """      </form>



    </div>



  </div>



  <!-- MODAL: PHÂN CÔNG LỚP TRƯỞNG (ADMIN, ĐOÀN TRƯỜNG, GVCN CỦA LỚP) -->
  <div id="modal-assign-class-monitor" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm hidden p-4 overflow-y-auto">
    <div class="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-slate-200 overflow-hidden my-8 flex flex-col">
      <!-- Header -->
      <div class="px-6 py-4 bg-gradient-to-r from-amber-500 to-amber-600 flex items-center justify-between text-white">
        <div class="flex items-center gap-2.5">
          <div class="w-9 h-9 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center text-white">
            <i data-lucide="crown" class="w-5 h-5"></i>
          </div>
          <div>
            <h3 class="font-bold text-base text-white">Phân công Lớp trưởng</h3>
            <p id="modal-assign-monitor-class-subtitle" class="text-xs text-amber-100 font-medium">Lớp --</p>
          </div>
        </div>
        <button type="button" onclick="closeModal('modal-assign-class-monitor')" class="text-white/80 hover:text-white p-1.5 rounded-lg hover:bg-white/20 transition-colors">
          <i data-lucide="x" class="w-5 h-5"></i>
        </button>
      </div>

      <!-- Form Body -->
      <form id="form-assign-class-monitor" onsubmit="handleAssignMonitorSubmit(event)" class="p-6 space-y-4">
        <input type="hidden" id="assign-monitor-class-id" value="">
        
        <!-- Current monitor info -->
        <div id="assign-monitor-current-box" class="p-3.5 rounded-xl bg-amber-50/80 border border-amber-200 flex items-center justify-between text-xs">
          <div>
            <span class="text-amber-800 font-semibold block">Lớp trưởng hiện tại:</span>
            <span id="assign-monitor-current-name" class="font-bold text-slate-800 text-sm">Chưa có</span>
          </div>
          <button type="button" id="btn-unassign-monitor-modal" onclick="confirmRemoveMonitorFromModal()" class="hidden px-2.5 py-1 text-xs font-semibold text-rose-600 hover:text-rose-700 bg-white hover:bg-rose-50 border border-rose-200 rounded-lg transition-colors">
            Hủy vai trò
          </button>
        </div>

        <div>
          <label for="assign-monitor-select-student" class="block text-xs font-bold text-slate-700 mb-1.5">
            Chọn học sinh làm Lớp trưởng <span class="text-rose-500">*</span>
          </label>
          <div class="relative">
            <select id="assign-monitor-select-student" required class="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2.5 text-xs text-slate-800 focus:outline-none focus:border-amber-500 focus:bg-white transition-all cursor-pointer">
              <option value="">-- Chọn học sinh trong lớp --</option>
            </select>
          </div>
          <p class="text-[11px] text-slate-500 mt-1.5">
            Lớp trưởng có quyền đại diện tập thể lớp theo dõi nề nếp và gửi khiếu nại / giải trình các lỗi vi phạm của lớp đến Đoàn trường.
          </p>
        </div>

        <div class="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100">
          <button type="button" onclick="closeModal('modal-assign-class-monitor')" class="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors">
            Đóng
          </button>
          <button type="submit" id="btn-submit-assign-monitor" class="px-5 py-2 text-xs font-semibold bg-amber-500 hover:bg-amber-600 text-white rounded-xl shadow-sm transition-all flex items-center gap-1.5">
            <i data-lucide="check" class="w-3.5 h-3.5"></i>
            <span>Lưu phân công</span>
          </button>
        </div>
      </form>
    </div>
  </div>"""

if "id=\"modal-assign-class-monitor\"" not in html:
    # Find the position of modal-assign-homeroom-teacher closing
    homeroom_pos = html.find('id="modal-assign-homeroom-teacher"')
    if homeroom_pos != -1:
        # find closing </div> after </form>
        end_form_pos = html.find('</form>', homeroom_pos)
        end_div1 = html.find('</div>', end_form_pos)
        end_div2 = html.find('</div>', end_div1 + 6)
        insert_pos = end_div2 + 6
        html = html[:insert_pos] + "\n\n" + modal_assign_monitor_html[len(modal_homeroom_end):] + html[insert_pos:]
        print("SUCCESS: Added modal-assign-class-monitor into index.html")
    else:
        print("WARNING: modal-assign-homeroom-teacher not found in index.html")
else:
    print("NOTE: modal-assign-class-monitor already exists in index.html")

with open(INDEX_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print("Patching completed.")
