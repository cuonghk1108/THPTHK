# -*- coding: utf-8 -*-
import sys
import os

path = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\templates\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('\r\n', '\n')

# 1. Update tab-profile in templates/index.html
old_profile_tab = """          <div class="workspace-profile-actions"><button id="profile-edit-button" type="button" class="hk-button hk-button-secondary" onclick="setProfileEditing(true)">Chỉnh sửa thông tin</button><div id="profile-edit-actions" class="hidden gap-2"><button type="button" class="hk-button hk-button-secondary" onclick="cancelProfileEditing()">Hủy</button><button id="profile-save-button" type="submit" class="hk-button hk-button-primary">Lưu thay đổi</button></div></div>

        </form>

      </section>"""

new_profile_tab = """          <div class="workspace-profile-actions flex flex-wrap items-center gap-2">
            <button id="profile-edit-button" type="button" class="hk-button hk-button-secondary" onclick="setProfileEditing(true)">Chỉnh sửa thông tin</button>
            <button id="profile-pwd-button" type="button" class="hk-button hk-button-secondary flex items-center gap-1.5" onclick="openPasswordChange()"><i data-lucide="key" class="w-4 h-4 text-amber-500"></i><span>Đổi mật khẩu</span></button>
            <div id="profile-edit-actions" class="hidden gap-2">
              <button type="button" class="hk-button hk-button-secondary" onclick="cancelProfileEditing()">Hủy</button>
              <button id="profile-save-button" type="submit" class="hk-button hk-button-primary">Lưu thay đổi</button>
            </div>
          </div>

        </form>

        <!-- KHỐI QUẢN LÝ LỚP HỌC: HỌC SINH XIN ĐỔI LỚP (CẦN ADMIN DUYỆT) / GIÁO VIÊN CẬP NHẬT LỚP DẠY (TỰ CẬP NHẬT) -->
        <div id="profile-class-section" class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4 hidden">
          <!-- Phân hệ lớp dành cho Học sinh -->
          <div id="profile-student-class-box" class="hidden space-y-4">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-2">
              <div>
                <h3 class="text-base font-bold text-slate-900 flex items-center gap-2">
                  <i data-lucide="graduation-cap" class="w-5 h-5 text-blue-600"></i> Lớp học & Đổi lớp
                </h3>
                <p class="text-xs text-slate-500">Đối với học sinh, khi xin chuyển lớp cần được Quản trị viên nhà trường phê duyệt.</p>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs font-semibold text-slate-500">Lớp hiện tại:</span>
                <span id="profile-student-current-class-badge" class="px-3 py-1 bg-blue-100 text-blue-800 font-extrabold rounded-xl border border-blue-200 text-sm">--</span>
              </div>
            </div>

            <!-- Banner thông báo đang có yêu cầu đổi lớp chờ duyệt -->
            <div id="profile-student-pending-banner" class="p-4 bg-amber-50 border border-amber-300 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 hidden">
              <div>
                <div class="flex items-center gap-1.5 text-amber-900 font-bold text-xs uppercase tracking-wide">
                  <i data-lucide="clock" class="w-4 h-4 text-amber-600"></i> Yêu cầu chuyển lớp đang chờ Quản trị viên duyệt
                </div>
                <p class="text-xs text-amber-800 mt-1" id="profile-student-pending-text">Đang chờ Quản trị viên duyệt yêu cầu chuyển lớp.</p>
              </div>
              <button type="button" onclick="cancelStudentClassChangeRequest()" class="px-3 py-1.5 bg-white border border-rose-300 text-rose-700 hover:bg-rose-50 rounded-xl text-xs font-bold transition shadow-sm">
                Hủy yêu cầu
              </button>
            </div>

            <!-- Form gửi yêu cầu đổi lớp -->
            <div id="profile-student-change-form" class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
              <h4 class="text-xs font-bold uppercase tracking-wider text-slate-700">Gửi yêu cầu xin chuyển lớp mới</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs font-semibold text-slate-700 mb-1">Chọn lớp muốn chuyển đến <span class="text-rose-500">*</span></label>
                  <select id="profile-student-target-class" class="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs font-bold text-slate-800 focus:outline-none focus:border-blue-600 shadow-sm cursor-pointer">
                    <option value="">-- Chọn lớp học --</option>
                  </select>
                </div>
                <div>
                  <label class="block text-xs font-semibold text-slate-700 mb-1">Lý do xin chuyển lớp (tùy chọn)</label>
                  <input type="text" id="profile-student-change-reason" placeholder="Ví dụ: Đổi ban học tập, thay đổi nguyện vọng..." class="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-blue-600 shadow-sm">
                </div>
              </div>
              <div class="flex justify-end pt-1">
                <button type="button" onclick="submitStudentClassChangeRequest()" id="btn-submit-student-class-change" class="hk-button hk-button-primary flex items-center gap-1.5 text-xs font-bold">
                  <i data-lucide="send" class="w-3.5 h-3.5"></i> Gửi yêu cầu đổi lớp (Cần Admin duyệt)
                </button>
              </div>
            </div>
          </div>

          <!-- Phân hệ lớp dành cho Giáo viên bộ môn / Giáo viên chủ nhiệm (TỰ CẬP NHẬT) -->
          <div id="profile-teacher-class-box" class="hidden space-y-4">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-2">
              <div>
                <h3 class="text-base font-bold text-slate-900 flex items-center gap-2">
                  <i data-lucide="book-open" class="w-5 h-5 text-emerald-600"></i> Phân công giảng dạy các lớp
                </h3>
                <p class="text-xs text-slate-500">Giáo viên có thể tự do chọn hoặc cập nhật các lớp mình giảng dạy ở tất cả các khối (Không cần Admin can thiệp).</p>
              </div>
              <span id="profile-teacher-classes-count-badge" class="px-3 py-1 bg-emerald-100 text-emerald-800 font-extrabold rounded-xl border border-emerald-200 text-xs">0 lớp đã chọn</span>
            </div>

            <!-- Môn giảng dạy -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Môn giảng dạy</label>
                <input type="text" id="profile-teacher-subject" placeholder="Ví dụ: Toán, Ngữ Văn, Tiếng Anh..." class="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs font-semibold text-slate-800 focus:outline-none focus:border-emerald-600 shadow-sm">
              </div>
            </div>

            <!-- Grade selector & class checkboxes -->
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-2 uppercase tracking-wider">Danh sách các lớp giảng dạy (Chọn nhiều lớp thuộc các khối)</label>
              <!-- Grade Filter Tabs -->
              <div class="flex items-center gap-2 mb-3">
                <button type="button" onclick="filterProfileTeacherGrade('ALL')" id="profile-grade-btn-ALL" class="px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-900 text-white transition shadow-sm">Tất cả khối</button>
                <button type="button" onclick="filterProfileTeacherGrade(10)" id="profile-grade-btn-10" class="px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-700 hover:bg-slate-200 transition">Khối 10</button>
                <button type="button" onclick="filterProfileTeacherGrade(11)" id="profile-grade-btn-11" class="px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-700 hover:bg-slate-200 transition">Khối 11</button>
                <button type="button" onclick="filterProfileTeacherGrade(12)" id="profile-grade-btn-12" class="px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-700 hover:bg-slate-200 transition">Khối 12</button>
              </div>

              <!-- Interactive class grid -->
              <div id="profile-teacher-classes-grid" class="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2 max-h-60 overflow-y-auto p-3 bg-slate-50 rounded-xl border border-slate-200">
                <!-- Class checkboxes injected here -->
              </div>
            </div>

            <div class="flex justify-end pt-2">
              <button type="button" onclick="submitTeacherClassesUpdate()" id="btn-submit-teacher-classes" class="hk-button hk-button-primary flex items-center gap-1.5 text-xs font-bold bg-emerald-600 hover:bg-emerald-700">
                <i data-lucide="check-circle" class="w-3.5 h-3.5"></i> Lưu danh sách lớp giảng dạy (Hiệu lực ngay)
              </button>
            </div>
          </div>
        </div>

      </section>"""

if old_profile_tab in content:
    content = content.replace(old_profile_tab, new_profile_tab)
    print('Patched tab-profile in templates/index.html')
else:
    print('old_profile_tab not found!')

# 2. Update modal-user-detail with pending class change box
old_user_detail_box = """        <!-- Verification Info -->
        <div class="p-3 bg-amber-50/70 rounded-xl border border-amber-200">
          <span class="text-[10px] font-bold text-amber-900 uppercase block mb-1 flex items-center gap-1.5"><i data-lucide="badge-check" class="w-3.5 h-3.5 text-amber-600"></i> Thông tin xác minh / Ghi chú đăng ký</span>
          <p id="detail-user-verification" class="text-slate-700 text-xs leading-relaxed">—</p>
        </div>"""

new_user_detail_box = """        <!-- Verification Info -->
        <div class="p-3 bg-amber-50/70 rounded-xl border border-amber-200">
          <span class="text-[10px] font-bold text-amber-900 uppercase block mb-1 flex items-center gap-1.5"><i data-lucide="badge-check" class="w-3.5 h-3.5 text-amber-600"></i> Thông tin xác minh / Ghi chú đăng ký</span>
          <p id="detail-user-verification" class="text-slate-700 text-xs leading-relaxed">—</p>
        </div>

        <!-- Pending Class Change Box in Admin Review Modal -->
        <div id="detail-pending-class-box" class="p-3.5 bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl border border-amber-300 hidden space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-amber-900 uppercase flex items-center gap-1.5">
              <i data-lucide="arrow-right-left" class="w-3.5 h-3.5 text-amber-600"></i> Yêu cầu chuyển lớp đang chờ duyệt
            </span>
            <span class="badge bg-amber-200 text-amber-900 border border-amber-400 font-bold text-[10px]">CẦN DUYỆT</span>
          </div>
          <p class="text-xs text-slate-800">
            Học sinh đề nghị chuyển từ lớp <strong id="detail-class-change-from" class="text-slate-900 font-bold">—</strong> sang lớp <strong id="detail-class-change-to" class="text-blue-700 font-extrabold text-sm">—</strong>
          </p>
          <p id="detail-class-change-reason-box" class="text-[11px] text-slate-600 italic">
            Lý do: <span id="detail-class-change-reason">—</span>
          </p>
          <div class="flex items-center gap-2 pt-1">
            <button type="button" id="btn-approve-class-change" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-sm transition flex items-center gap-1 text-xs">
              <i data-lucide="check" class="w-3.5 h-3.5"></i> Duyệt chuyển lớp
            </button>
            <button type="button" id="btn-reject-class-change" class="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl font-bold shadow-sm transition flex items-center gap-1 text-xs">
              <i data-lucide="x" class="w-3.5 h-3.5"></i> Từ chối
            </button>
          </div>
        </div>"""

if old_user_detail_box in content:
    content = content.replace(old_user_detail_box, new_user_detail_box)
    print('Patched modal-user-detail in templates/index.html')
else:
    print('old_user_detail_box not found!')

with open(path, 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content)

print('Updated templates/index.html successfully!')
