import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"

# ==============================================================================
# 1. UPDATE templates/index.html
# ==============================================================================
html_path = os.path.join(BASE_DIR, "templates", "index.html")
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

html_norm = html.replace("\r\n", "\n")

old_teacher_section = """              <!-- BƯỚC 2B: THÔNG TIN GIÁO VIÊN -->

              <div id="section-teacher-fields" hidden>

                <div class="auth-row">

                  <div class="auth-field">

                    <label for="complete-teacher-name">Họ và tên giáo viên <span style="color:#ef4444;">*</span></label>

                    <input id="complete-teacher-name" name="teacher_full_name" value="{{ auth_user.full_name }}">

                  </div>

                  <div class="auth-field">

                    <label for="complete-teacher-phone">Số điện thoại liên lạc <span style="color:#ef4444;">*</span></label>

                    <input id="complete-teacher-phone" name="teacher_phone" type="tel" placeholder="09xxxxxxxx">

                  </div>

                </div>



                <div class="auth-row">

                  <div class="auth-field">

                    <label for="complete-teacher-subject">Tổ chuyên môn / Bộ môn <span style="color:#ef4444;">*</span></label>

                    <select id="complete-teacher-subject" name="subject">

                      <option value="">-- Chọn tổ chuyên môn --</option>

                      <option value="Toán học">Tổ Toán học</option>

                      <option value="Ngữ văn">Tổ Ngữ văn</option>

                      <option value="Ngoại ngữ (Tiếng Anh)">Tổ Ngoại ngữ (Tiếng Anh)</option>

                      <option value="Vật lý">Tổ Vật lý</option>

                      <option value="Hóa học">Tổ Hóa học</option>

                      <option value="Sinh học">Tổ Sinh học</option>

                      <option value="Lịch sử">Tổ Lịch sử</option>

                      <option value="Địa lý">Tổ Địa lý</option>

                      <option value="Giáo dục công dân / KT&PL">Tổ GDCD / GDKT&PL</option>

                      <option value="Tin học">Tổ Tin học</option>

                      <option value="Thể dục - GDQP">Tổ Thể dục - GDQP</option>

                    </select>

                  </div>

                  <div class="auth-field">

                    <label for="complete-teacher-type">Loại phân công <span style="color:#ef4444;">*</span></label>

                    <select id="complete-teacher-type" name="teacher_type">

                      <option value="gvbm">Giáo viên bộ môn (GVBM)</option>

                      <option value="gvcn">Giáo viên chủ nhiệm (GVCN)</option>

                    </select>

                  </div>

                </div>



                <div class="auth-field" id="wrap-homeroom-class" hidden>

                  <label for="complete-teacher-homeroom">Lớp chủ nhiệm được phân công</label>

                  <select id="complete-teacher-homeroom" name="homeroom_class">

                    <option value="">-- Chọn lớp chủ nhiệm --</option>

                    {% for item in school_classes %}

                      <option value="{{ item.name }}">{{ item.name }}</option>

                    {% endfor %}

                  </select>

                </div>



                <div class="auth-field">

                  <label for="complete-teacher-code">Mã cán bộ / giáo viên (nếu có)</label>

                  <input id="complete-teacher-code" name="teacher_code" placeholder="Ví dụ: CB-GV08">

                </div>

              </div>"""

new_teacher_section = """              <!-- BƯỚC 2B: THÔNG TIN GIÁO VIÊN -->
              <div id="section-teacher-fields" hidden class="space-y-4">
                <div class="auth-row">
                  <div class="auth-field">
                    <label for="complete-teacher-name">Họ và tên giáo viên <span style="color:#ef4444;">*</span></label>
                    <input id="complete-teacher-name" name="teacher_full_name" value="{{ auth_user.full_name }}" placeholder="Họ và tên đầy đủ">
                  </div>
                  <div class="auth-field">
                    <label for="complete-teacher-phone">Số điện thoại liên lạc <span style="color:#ef4444;">*</span></label>
                    <input id="complete-teacher-phone" name="teacher_phone" type="tel" placeholder="09xxxxxxxx">
                  </div>
                </div>

                <!-- DYNAMIC TEACHER SUBJECTS & CLASSES SELECTION -->
                <div id="complete-teacher-details" class="auth-field space-y-3">
                  <!-- 1. MULTI-SUBJECT SELECTION -->
                  <div class="relative">
                    <div class="flex items-center justify-between mb-1">
                      <label class="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                        <i data-lucide="sparkles" class="w-3.5 h-3.5 text-blue-500"></i>
                        <span>Môn giảng dạy</span> <span style="color:#ef4444;">*</span>
                      </label>
                      <span id="complete-subject-count-badge" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                        0 môn đã chọn
                      </span>
                    </div>

                    <!-- Trigger Box -->
                    <button type="button" id="btn-toggle-complete-subjects-dropdown" onclick="toggleCompleteTeacherSubjectsDropdown()" class="w-full min-h-[42px] px-3 py-1.5 bg-white border border-slate-300 hover:border-blue-400 focus:border-blue-500 rounded-xl text-xs flex items-center justify-between cursor-pointer transition text-left shadow-2xs group">
                      <div id="complete-subjects-trigger-content" class="flex flex-wrap items-center gap-1 flex-1 py-0.5 overflow-hidden">
                        <span id="complete-subjects-summary-text" class="text-slate-400 font-normal">✨ Bấm chọn môn giảng dạy (1 hoặc nhiều môn)...</span>
                      </div>
                      <div class="flex items-center gap-1.5 shrink-0 ml-1.5">
                        <span id="btn-clear-complete-subjects-quick" onclick="event.stopPropagation(); clearCompleteTeacherSubjects();" class="hidden text-slate-400 hover:text-rose-600 p-0.5 rounded-full hover:bg-slate-100 transition text-sm leading-none font-bold" title="Xóa tất cả">&times;</span>
                        <i data-lucide="chevron-down" id="icon-complete-subjects-chevron" class="w-4 h-4 text-slate-400 group-hover:text-blue-500 transition-transform"></i>
                      </div>
                    </button>

                    <!-- Floating Popover Menu -->
                    <div id="complete-subjects-dropdown-container" class="hidden absolute left-0 right-0 top-full mt-1.5 z-40 bg-white/98 backdrop-blur-md border border-blue-100 rounded-2xl shadow-xl p-3 space-y-2.5 animate-in fade-in zoom-in-95 duration-150">
                      <div class="flex items-center justify-between gap-2 pb-1.5 border-b border-slate-100">
                        <div class="relative flex-1">
                          <i data-lucide="search" class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5"></i>
                          <input type="text" id="filter-complete-subjects-input" oninput="filterCompleteTeacherSubjects(this.value)" placeholder="Tìm nhanh môn học..." class="w-full pl-8 pr-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-none focus:bg-white focus:border-blue-400 transition">
                        </div>
                        <button type="button" onclick="clearCompleteTeacherSubjects()" class="text-[11px] font-semibold text-slate-500 hover:text-rose-600 px-2 py-1 rounded-lg hover:bg-rose-50 transition">Xóa chọn</button>
                      </div>

                      <!-- Chip Grid -->
                      <div id="complete-subjects-checkboxes-grid" class="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto p-0.5">
                        <!-- Populated dynamically -->
                      </div>

                      <!-- Footer Bar -->
                      <div class="flex items-center justify-between pt-1 border-t border-slate-100 text-[11px]">
                        <span class="text-slate-500 font-medium" id="complete-subjects-footer-count">Đã chọn: 0 môn</span>
                        <button type="button" onclick="toggleCompleteTeacherSubjectsDropdown(false)" class="px-3.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold shadow-2xs transition">Xong</button>
                      </div>
                    </div>
                  </div>

                  <!-- 2. MULTI-CLASS SELECTION -->
                  <div class="relative">
                    <div class="flex items-center justify-between mb-1">
                      <label class="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                        <i data-lucide="layers" class="w-3.5 h-3.5 text-indigo-600"></i>
                        <span>Lớp giảng dạy</span> <span style="color:#ef4444;">*</span>
                      </label>
                      <span id="complete-classes-count-badge" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                        0 lớp đã chọn
                      </span>
                    </div>

                    <!-- Trigger Box -->
                    <button type="button" id="btn-toggle-complete-classes-dropdown" onclick="toggleCompleteTeacherClassesDropdown()" class="w-full min-h-[42px] px-3 py-1.5 bg-white border border-slate-300 hover:border-indigo-400 focus:border-indigo-500 rounded-xl text-xs flex items-center justify-between cursor-pointer transition text-left shadow-2xs group">
                      <div id="complete-classes-trigger-content" class="flex flex-wrap items-center gap-1 flex-1 py-0.5 overflow-hidden">
                        <span id="complete-classes-summary-text" class="text-slate-400 font-normal">🏫 Bấm chọn các lớp giảng dạy theo khối...</span>
                      </div>
                      <div class="flex items-center gap-1.5 shrink-0 ml-1.5">
                        <span id="btn-clear-complete-classes-quick" onclick="event.stopPropagation(); clearCompleteTeacherClasses();" class="hidden text-slate-400 hover:text-rose-600 p-0.5 rounded-full hover:bg-slate-100 transition text-sm leading-none font-bold" title="Xóa tất cả">&times;</span>
                        <i data-lucide="chevron-down" id="icon-complete-classes-chevron" class="w-4 h-4 text-slate-400 group-hover:text-indigo-500 transition-transform"></i>
                      </div>
                    </button>

                    <!-- Floating Popover Menu -->
                    <div id="complete-classes-dropdown-container" class="hidden absolute left-0 right-0 top-full mt-1.5 z-40 bg-white/98 backdrop-blur-md border border-indigo-100 rounded-2xl shadow-xl p-3 space-y-2.5 animate-in fade-in zoom-in-95 duration-150">
                      <div class="flex items-center justify-between gap-2 pb-1.5 border-b border-slate-100">
                        <div class="relative flex-1">
                          <i data-lucide="search" class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5"></i>
                          <input type="text" id="filter-complete-classes-input" oninput="filterCompleteTeacherClasses(this.value)" placeholder="Tìm nhanh lớp (VD: 10A1, 11A...)..." class="w-full pl-8 pr-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-none focus:bg-white focus:border-indigo-400 transition">
                        </div>
                        <button type="button" onclick="clearCompleteTeacherClasses()" class="text-[11px] font-semibold text-slate-500 hover:text-rose-600 px-2 py-1 rounded-lg hover:bg-rose-50 transition">Xóa chọn</button>
                      </div>

                      <!-- Segmented Grade Tabs -->
                      <div class="flex items-center justify-between gap-1.5 bg-slate-100/90 p-1 rounded-xl">
                        <div class="flex items-center gap-1">
                          <button type="button" onclick="switchCompleteGradeTab(10)" id="comp-grade-tab-10" class="px-2.5 py-1 rounded-lg text-xs font-bold bg-white text-indigo-700 shadow-xs transition flex items-center gap-1">
                            <span>Khối 10</span>
                            <span id="comp-grade-count-10" class="hidden text-[10px] px-1.5 py-0.2 rounded-full bg-indigo-100 text-indigo-800 font-extrabold">0</span>
                          </button>
                          <button type="button" onclick="switchCompleteGradeTab(11)" id="comp-grade-tab-11" class="px-2.5 py-1 rounded-lg text-xs font-bold text-slate-600 hover:text-slate-900 transition flex items-center gap-1">
                            <span>Khối 11</span>
                            <span id="comp-grade-count-11" class="hidden text-[10px] px-1.5 py-0.2 rounded-full bg-indigo-100 text-indigo-800 font-extrabold">0</span>
                          </button>
                          <button type="button" onclick="switchCompleteGradeTab(12)" id="comp-grade-tab-12" class="px-2.5 py-1 rounded-lg text-xs font-bold text-slate-600 hover:text-slate-900 transition flex items-center gap-1">
                            <span>Khối 12</span>
                            <span id="comp-grade-count-12" class="hidden text-[10px] px-1.5 py-0.2 rounded-full bg-indigo-100 text-indigo-800 font-extrabold">0</span>
                          </button>
                        </div>
                        <button type="button" onclick="toggleSelectCompleteCurrentGrade()" id="btn-toggle-select-complete-current-grade" class="text-[11px] font-bold text-indigo-600 hover:text-indigo-800 px-2 py-0.5 rounded-lg hover:bg-white transition shrink-0">
                          + Chọn cả Khối 10
                        </button>
                      </div>

                      <!-- Grade Class Panels -->
                      <div class="max-h-48 overflow-y-auto p-1">
                        <!-- Khối 10 -->
                        <div id="complete-teacher-classes-grid-10" class="grid grid-cols-4 sm:grid-cols-6 gap-1.5">
                          {% for item in school_classes %}{% if item.grade == 10 %}
                            <label class="class-choice-pill flex items-center justify-center p-1.5 bg-slate-50 hover:bg-blue-50 border border-slate-200 rounded-lg cursor-pointer text-xs font-semibold text-slate-700 transition select-none text-center">
                              <input type="checkbox" name="complete_teacher_classes" value="{{ item.name }}" data-grade="10" onchange="syncCompleteTeacherClassSelection()" class="hidden">
                              <span>{{ item.name }}</span>
                            </label>
                          {% endif %}{% endfor %}
                        </div>

                        <!-- Khối 11 -->
                        <div id="complete-teacher-classes-grid-11" class="hidden grid grid-cols-4 sm:grid-cols-6 gap-1.5">
                          {% for item in school_classes %}{% if item.grade == 11 %}
                            <label class="class-choice-pill flex items-center justify-center p-1.5 bg-slate-50 hover:bg-emerald-50 border border-slate-200 rounded-lg cursor-pointer text-xs font-semibold text-slate-700 transition select-none text-center">
                              <input type="checkbox" name="complete_teacher_classes" value="{{ item.name }}" data-grade="11" onchange="syncCompleteTeacherClassSelection()" class="hidden">
                              <span>{{ item.name }}</span>
                            </label>
                          {% endif %}{% endfor %}
                        </div>

                        <!-- Khối 12 -->
                        <div id="complete-teacher-classes-grid-12" class="hidden grid grid-cols-4 sm:grid-cols-6 gap-1.5">
                          {% for item in school_classes %}{% if item.grade == 12 %}
                            <label class="class-choice-pill flex items-center justify-center p-1.5 bg-slate-50 hover:bg-purple-50 border border-slate-200 rounded-lg cursor-pointer text-xs font-semibold text-slate-700 transition select-none text-center">
                              <input type="checkbox" name="complete_teacher_classes" value="{{ item.name }}" data-grade="12" onchange="syncCompleteTeacherClassSelection()" class="hidden">
                              <span>{{ item.name }}</span>
                            </label>
                          {% endif %}{% endfor %}
                        </div>
                      </div>

                      <!-- Footer Bar -->
                      <div class="flex items-center justify-between pt-1 border-t border-slate-100 text-[11px]">
                        <span class="text-slate-500 font-medium" id="complete-classes-footer-count">Đã chọn: 0 lớp</span>
                        <button type="button" onclick="toggleCompleteTeacherClassesDropdown(false)" class="px-3.5 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold shadow-2xs transition">Xong</button>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="auth-field">
                  <label for="complete-teacher-code">Mã cán bộ / giáo viên (nếu có)</label>
                  <input id="complete-teacher-code" name="teacher_code" placeholder="Ví dụ: CB-GV08">
                </div>
              </div>"""

old_logout_link = """                <a href="/login" class="hk-button hk-button-secondary" style="flex:1; justify-content:center;">Đăng xuất</a>"""
new_logout_link = """                <button type="button" id="btn-complete-logout" onclick="handleCompleteProfileLogout()" class="hk-button hk-button-secondary" style="flex:1; justify-content:center;">Đăng xuất</button>"""

if old_teacher_section in html_norm:
    html_norm = html_norm.replace(old_teacher_section, new_teacher_section)
    print("SUCCESS: Replaced teacher fields in complete-profile with modern multi-select UI")
else:
    print("WARNING: old_teacher_section not found in templates/index.html")

if old_logout_link in html_norm:
    html_norm = html_norm.replace(old_logout_link, new_logout_link)
    print("SUCCESS: Replaced logout link with safe POST logout button")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_norm)
print("Finished updating templates/index.html")
