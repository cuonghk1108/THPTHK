import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"

# ==============================================================================
# 1. UPDATE TEMPLATES/INDEX.HTML
# ==============================================================================
html_path = os.path.join(BASE_DIR, "templates", "index.html")
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# Normalize line endings
html = html.replace("\r\n", "\n")

# A. Add subtab button
btn_feedbacks_target = """            <button type="button" onclick="switchTeacherSubTab('feedbacks')" id="subtab-btn-feedbacks" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg text-slate-600 hover:text-slate-900 transition-all flex items-center gap-1.5">

              <i data-lucide="message-square" class="w-3.5 h-3.5"></i>

              <span>Lịch sử phản hồi</span>

              <span id="class-feedback-count-badge" class="px-1.5 py-0.2 rounded-full text-[10px] bg-blue-100 text-blue-700 font-bold">0</span>

            </button>"""

btn_teachers_addition = """            <button type="button" onclick="switchTeacherSubTab('teachers')" id="subtab-btn-teachers" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg text-slate-600 hover:text-slate-900 transition-all flex items-center gap-1.5">

              <i data-lucide="award" class="w-3.5 h-3.5"></i>

              <span>Đội ngũ giáo viên</span>

              <span id="class-teacher-count-badge" class="px-1.5 py-0.2 rounded-full text-[10px] bg-emerald-100 text-emerald-700 font-bold">0</span>

            </button>"""

if "id=\"subtab-btn-teachers\"" not in html:
    if btn_feedbacks_target in html:
        html = html.replace(btn_feedbacks_target, btn_feedbacks_target + "\n\n" + btn_teachers_addition)
        print("SUCCESS: Added subtab-btn-teachers to templates/index.html")
    else:
        print("ERROR: btn_feedbacks_target not found in templates/index.html")
else:
    print("INFO: subtab-btn-teachers already exists in templates/index.html")


# B. Add subtab pane for teachers
feedbacks_pane_end_target = """          <div id="teacher-feedbacks-empty-state" class="hidden bg-white rounded-2xl p-12 text-center border border-slate-200">

            <div class="w-14 h-14 rounded-2xl bg-blue-50 text-blue-500 mx-auto flex items-center justify-center mb-3">

              <i data-lucide="message-square-plus" class="w-7 h-7"></i>

            </div>

            <h3 class="text-sm font-bold text-slate-700">Chưa có phản hồi nào</h3>

            <p class="text-xs text-slate-500 mt-1 max-w-sm mx-auto">Chưa có phản hồi nào được ghi nhận cho lớp học này. Thầy/Cô có thể nhấn "Gửi phản hồi" trong danh sách học sinh để trao đổi.</p>

          </div>

        </div>"""

teachers_pane_html = """        <!-- SUB-TAB 3: CLASS TEACHING STAFF (GVCN & BỘ MÔN) -->
        <div id="subtab-pane-teachers" class="hidden space-y-4">
          <!-- Top Toolbar / Info Banner -->
          <div class="bg-white rounded-2xl p-4 shadow-sm border border-slate-200 flex flex-col md:flex-row items-center justify-between gap-3">
            <div>
              <h3 class="text-sm font-bold text-slate-900 flex items-center gap-2">
                <i data-lucide="award" class="w-4 h-4 text-blue-600"></i>
                <span id="teachers-pane-class-title">Đội ngũ giáo viên lớp</span>
              </h3>
              <p class="text-xs text-slate-500 mt-0.5">Quản lý và phân công Giáo viên Chủ nhiệm (GVCN) & Giáo viên Bộ môn (GVBM)</p>
            </div>
            <div class="flex items-center gap-2 flex-wrap">
              <button type="button" onclick="openAssignHomeroomModal()" class="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-xl shadow-sm flex items-center gap-1.5 transition">
                <i data-lucide="user-cog" class="w-4 h-4"></i>
                <span>Phân công GVCN</span>
              </button>
              <button type="button" onclick="openAssignSubjectTeacherModal()" class="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-sm flex items-center gap-1.5 transition">
                <i data-lucide="plus" class="w-4 h-4"></i>
                <span>+ Phân công GV Bộ môn</span>
              </button>
              <button type="button" onclick="loadClassTeachers()" class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl flex items-center gap-1.5 transition">
                <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
                <span>Làm mới</span>
              </button>
            </div>
          </div>

          <!-- Homeroom Teacher Profile Card -->
          <div class="bg-gradient-to-r from-blue-50/90 via-indigo-50/50 to-white rounded-2xl p-5 border border-blue-100 shadow-sm">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div class="flex items-center gap-4">
                <div class="w-14 h-14 rounded-2xl bg-blue-600 text-white flex items-center justify-center font-bold text-xl shadow-md flex-shrink-0">
                  <i data-lucide="shield-check" class="w-7 h-7"></i>
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 text-[10px] font-bold rounded-full bg-blue-600 text-white uppercase tracking-wider">Giáo viên chủ nhiệm</span>
                    <span id="class-gvcn-status-badge" class="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-100 text-emerald-700">Đang hoạt động</span>
                  </div>
                  <h4 id="class-gvcn-name" class="text-base font-bold text-slate-900 mt-1">Chưa phân công GVCN</h4>
                  <p id="class-gvcn-details" class="text-xs text-slate-600 mt-0.5">Môn chuyên môn: -- • Email: -- • SĐT: --</p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button type="button" onclick="openAssignHomeroomModal()" class="px-3.5 py-1.5 text-xs font-semibold rounded-xl bg-white border border-blue-200 hover:bg-blue-50 text-blue-700 transition flex items-center gap-1 shadow-2xs">
                  <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                  <span>Đổi GVCN</span>
                </button>
                <button type="button" id="btn-pane-revoke-gvcn" onclick="handleRevokeHomeroom()" class="px-3.5 py-1.5 text-xs font-semibold rounded-xl bg-rose-50 border border-rose-200 hover:bg-rose-100 text-rose-700 transition flex items-center gap-1">
                  <i data-lucide="user-x" class="w-3.5 h-3.5"></i>
                  <span>Thu hồi</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Subject Teachers Grid / Table -->
          <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div class="p-4 border-b border-slate-100 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <i data-lucide="book-open" class="w-4 h-4 text-indigo-600"></i>
                <h4 class="text-xs font-bold uppercase tracking-wider text-slate-700">Danh sách Giáo viên Bộ môn (GVBM)</h4>
              </div>
              <span id="subject-teachers-count-badge" class="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">0 môn đã phân công</span>
            </div>
            
            <div class="overflow-x-auto">
              <table class="w-full text-left border-collapse text-xs md:text-sm">
                <thead>
                  <tr class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
                    <th class="py-3 px-4 w-12 text-center">STT</th>
                    <th class="py-3 px-4 w-44">Môn học</th>
                    <th class="py-3 px-4">Giáo viên phụ trách</th>
                    <th class="py-3 px-4 w-48">Email</th>
                    <th class="py-3 px-4 w-36">Số điện thoại</th>
                    <th class="py-3 px-4 w-36 text-center">Ngày phân công</th>
                    <th class="py-3 px-4 w-28 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody id="class-subject-teachers-tbody" class="divide-y divide-slate-100">
                  <!-- Rendered dynamically -->
                </tbody>
              </table>
            </div>

            <!-- Empty subject teachers state -->
            <div id="class-subject-teachers-empty" class="hidden p-8 text-center">
              <div class="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-500 mx-auto flex items-center justify-center mb-2">
                <i data-lucide="user-plus" class="w-6 h-6"></i>
              </div>
              <p class="text-xs font-bold text-slate-700">Chưa có giáo viên bộ môn nào được phân công</p>
              <p class="text-[11px] text-slate-400 mt-1">Nhấn nút "+ Phân công GV Bộ môn" để gán giáo viên giảng dạy cho lớp này.</p>
            </div>
          </div>
        </div>"""

if "id=\"subtab-pane-teachers\"" not in html:
    if feedbacks_pane_end_target in html:
        html = html.replace(feedbacks_pane_end_target, feedbacks_pane_end_target + "\n\n" + teachers_pane_html)
        print("SUCCESS: Added subtab-pane-teachers to templates/index.html")
    else:
        print("ERROR: feedbacks_pane_end_target not found in templates/index.html")
else:
    print("INFO: subtab-pane-teachers already exists in templates/index.html")


# C. Add Class Selector in modal-assign-homeroom-teacher
hr_banner_target = """        <!-- Target Class & Current GVCN Info Banner -->

        <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5 text-xs">"""

hr_class_select_html = """        <!-- Target Class Selector -->
        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">
            Chọn Lớp cần phân công GVCN <span class="text-rose-500">*</span>
          </label>
          <select id="assign-homeroom-class-select" onchange="onAssignHomeroomClassSelectChange(this.value)" class="w-full px-3 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none font-medium">
            <option value="">-- Chọn lớp học --</option>
          </select>
        </div>

        <!-- Target Class & Current GVCN Info Banner -->
        <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5 text-xs">"""

if "id=\"assign-homeroom-class-select\"" not in html:
    if hr_banner_target in html:
        html = html.replace(hr_banner_target, hr_class_select_html)
        print("SUCCESS: Added assign-homeroom-class-select to modal-assign-homeroom-teacher")
    else:
        print("ERROR: hr_banner_target not found in templates/index.html")
else:
    print("INFO: assign-homeroom-class-select already exists in templates/index.html")


# D. Add modal-assign-subject-teacher
modal_hr_end_target = """  <!-- MODAL: GỬI PHẢN HỒI HỌC SINH -->"""

modal_subject_teacher_html = """  <!-- MODAL: PHÂN CÔNG GIÁO VIÊN BỘ MÔN (ADMIN / BAN GIÁM HIỆU) -->
  <div id="modal-assign-subject-teacher" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm hidden p-4 overflow-y-auto">
    <div class="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden my-8 flex flex-col">
      <!-- Header -->
      <div class="p-5 border-b border-slate-100 flex items-center justify-between bg-gradient-to-r from-indigo-50 to-blue-50">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold shadow-md">
            <i data-lucide="book-open" class="w-5 h-5"></i>
          </div>
          <div>
            <h3 class="text-base font-bold text-slate-900">Phân công Giáo viên Bộ môn</h3>
            <p class="text-xs text-slate-500">Gán giáo viên phụ trách môn học cho lớp</p>
          </div>
        </div>
        <button onclick="closeModal('modal-assign-subject-teacher')" class="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-white/80 transition-colors">
          <i data-lucide="x" class="w-5 h-5"></i>
        </button>
      </div>

      <!-- Body Form -->
      <form id="form-assign-subject-teacher" onsubmit="handleAssignSubjectTeacherSubmit(event)" class="p-6 space-y-4">
        <!-- Class Selector -->
        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">
            Lớp học <span class="text-rose-500">*</span>
          </label>
          <select id="assign-subject-class-select" class="w-full px-3 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none font-medium" required>
            <!-- options dynamically populated -->
          </select>
        </div>

        <!-- Subject Selection -->
        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">
            Môn học phân công <span class="text-rose-500">*</span>
          </label>
          <select id="assign-subject-code-select" onchange="onAssignSubjectChange(this.value)" class="w-full px-3 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none font-medium" required>
            <option value="">-- Chọn môn học --</option>
            <option value="TOAN">Toán học</option>
            <option value="VAN">Ngữ văn</option>
            <option value="ANH">Tiếng Anh</option>
            <option value="LY">Vật lý</option>
            <option value="HOA">Hóa học</option>
            <option value="SINH">Sinh học</option>
            <option value="SU">Lịch sử</option>
            <option value="DIA">Địa lý</option>
            <option value="GDCD">Giáo dục công dân / GDKT&PL</option>
            <option value="TIN">Tin học</option>
            <option value="CN">Công nghệ</option>
            <option value="TD">Giáo dục thể chất</option>
            <option value="QP">Giáo dục QP-AN</option>
            <option value="AM_NHAC">Âm nhạc</option>
            <option value="MY_THUAT">Mỹ thuật</option>
            <option value="HDTN">Hoạt động trải nghiệm, hướng nghiệp</option>
          </select>
        </div>

        <!-- Teacher Selection Dropdown -->
        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">
            Chọn Giáo viên phụ trách <span class="text-rose-500">*</span>
          </label>
          <select id="assign-subject-teacher-select" class="w-full px-3 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none font-medium" required>
            <option value="">-- Chọn môn học trước để lọc giáo viên phù hợp --</option>
          </select>
          <p class="text-[11px] text-slate-400 mt-1">Hệ thống ưu tiên hiển thị các giáo viên có chuyên môn dạy môn học này.</p>
        </div>

        <!-- Conflict Info if already assigned -->
        <div id="assign-subject-conflict-box" class="p-3 bg-amber-50 border border-amber-200 rounded-xl hidden text-xs text-amber-800">
          <div class="flex items-start gap-2">
            <i data-lucide="alert-triangle" class="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5"></i>
            <span id="assign-subject-conflict-msg" class="leading-relaxed font-medium">Môn này hiện đã có giáo viên phụ trách. Lưu phân công sẽ thay thế giáo viên hiện tại.</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="pt-3 flex items-center justify-end gap-2 border-t border-slate-100">
          <button type="button" onclick="closeModal('modal-assign-subject-teacher')" class="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors">
            Hủy
          </button>
          <button type="submit" id="btn-submit-assign-subject" class="px-5 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-sm transition-all flex items-center gap-1.5">
            <i data-lucide="check" class="w-3.5 h-3.5"></i>
            <span>Lưu phân công GVBM</span>
          </button>
        </div>
      </form>
    </div>
  </div>

"""

if "id=\"modal-assign-subject-teacher\"" not in html:
    if modal_hr_end_target in html:
        html = html.replace(modal_hr_end_target, modal_subject_teacher_html + modal_hr_end_target)
        print("SUCCESS: Added modal-assign-subject-teacher to templates/index.html")
    else:
        print("ERROR: modal_hr_end_target not found in templates/index.html")
else:
    print("INFO: modal-assign-subject-teacher already exists in templates/index.html")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print("Finished updating templates/index.html")
