import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

content_norm = content.replace('\r\n', '\n')

old_block = """          <div>
            <label class="block font-semibold text-slate-700 mb-1">
              Chức vụ / Vai trò được Admin duyệt <span class="text-rose-500">*</span>
            </label>
            <select id="review-assigned-role" required class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 font-medium text-slate-900 focus:ring-2 focus:ring-brand-500 focus:bg-white transition">
              <option value="HOC_SINH">1. Học sinh</option>
              <option value="GVCN">2. Giáo viên chủ nhiệm (GVCN)</option>
              <option value="GVBM">3. Giáo viên bộ môn (GVBM)</option>
              <option value="SAO_DO">4. Đội Sao đỏ / Trực tuần</option>
              <option value="DOAN_TRUONG">5. Đoàn trường</option>
              <option value="BGH">6. Ban Giám hiệu (BGH)</option>
              <option value="CHUYEN_VIEN_TAM_LY">7. Chuyên viên tư vấn tâm lý</option>
              <option value="ADMIN">8. Quản trị viên hệ thống (Admin)</option>
              <option value="SUPER_ADMIN">9. Quản trị viên tối cao (Super Admin)</option>
            </select>
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">
              Phân công Lớp / Tổ chuyên môn (nếu có)
            </label>
            <input type="text" id="review-department" placeholder="VD: 10A1 hoặc Tổ Toán - Tin" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-medium text-slate-900 focus:ring-2 focus:ring-brand-500 focus:bg-white transition">
          </div>"""

new_block = """          <div>
            <label class="block font-semibold text-slate-700 mb-1">
              Chức vụ / Vai trò được Admin duyệt <span class="text-rose-500">*</span>
            </label>
            <select id="review-assigned-role" required onchange="onReviewRoleChange()" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 font-medium text-slate-900 focus:ring-2 focus:ring-brand-500 focus:bg-white transition">
              <option value="HOC_SINH">1. Học sinh</option>
              <option value="GVCN">2. Giáo viên chủ nhiệm (GVCN)</option>
              <option value="GVBM">3. Giáo viên bộ môn (GVBM)</option>
              <option value="SAO_DO">4. Đội Sao đỏ / Trực tuần</option>
              <option value="DOAN_TRUONG">5. Đoàn trường</option>
              <option value="BGH">6. Ban Giám hiệu (BGH)</option>
              <option value="CHUYEN_VIEN_TAM_LY">7. Chuyên viên tư vấn tâm lý</option>
              <option value="ADMIN">8. Quản trị viên hệ thống (Admin)</option>
              <option value="SUPER_ADMIN">9. Quản trị viên tối cao (Super Admin)</option>
            </select>
          </div>

          <input type="hidden" id="review-department">

          <!-- Dynamic Assignment Container based on Selected Role -->
          <div id="review-assignment-container" class="space-y-3">
            <!-- SECTION 1: HỌC SINH (Chọn 1 Khối và 1 Lớp duy nhất) -->
            <div id="review-section-student" class="p-3 bg-blue-50/70 rounded-xl border border-blue-200 space-y-2.5">
              <div class="flex items-center justify-between">
                <span class="font-bold text-blue-900 flex items-center gap-1.5 text-xs">
                  <i data-lucide="graduation-cap" class="w-4 h-4 text-blue-600"></i>
                  Phân công lớp cho học sinh <span class="text-rose-500">*</span>
                </span>
                <span class="text-[10px] font-semibold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">Chỉ chọn 1 lớp</span>
              </div>
              <div class="grid grid-cols-2 gap-2.5">
                <div>
                  <label class="block text-[11px] font-semibold text-slate-700 mb-1">Khối lớp:</label>
                  <select id="review-student-grade" onchange="onReviewStudentGradeChange(this.value)" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-slate-800 focus:ring-2 focus:ring-brand-500">
                    <option value="10">Khối 10 (22 lớp)</option>
                    <option value="11">Khối 11 (21 lớp)</option>
                    <option value="12">Khối 12 (21 lớp)</option>
                  </select>
                </div>
                <div>
                  <label class="block text-[11px] font-semibold text-slate-700 mb-1">Lớp học:</label>
                  <select id="review-student-class" onchange="onReviewStudentClassChange(this.value)" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs font-bold text-brand-700 focus:ring-2 focus:ring-brand-500">
                    <option value="">-- Chọn lớp --</option>
                  </select>
                </div>
              </div>
              <div id="review-student-selected-badge" class="text-[11px] text-blue-800 font-medium flex items-center gap-1">
                <i data-lucide="check" class="w-3.5 h-3.5 text-emerald-600"></i>
                <span>Lớp đã chọn: <b id="review-student-selected-text" class="text-brand-700 font-bold">Chưa chọn</b></span>
              </div>
            </div>

            <!-- SECTION 2: GIÁO VIÊN BỘ MÔN & CHỦ NHIỆM (Chọn Môn & Nhiều Lớp giảng dạy) -->
            <div id="review-section-teacher" class="p-3 bg-purple-50/70 rounded-xl border border-purple-200 space-y-3 hidden">
              <!-- Môn giảng dạy -->
              <div>
                <label class="block font-semibold text-slate-700 mb-1 flex items-center justify-between text-xs">
                  <span>Môn giảng dạy chính <span class="text-rose-500">*</span></span>
                  <span class="text-[10px] text-purple-700 font-normal">Tổ chuyên môn</span>
                </label>
                <select id="review-teacher-subject" class="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs font-semibold text-slate-800 focus:ring-2 focus:ring-brand-500">
                  <option value="Toán học">Toán học</option>
                  <option value="Ngữ văn">Ngữ văn</option>
                  <option value="Tiếng Anh">Tiếng Anh</option>
                  <option value="Vật lí">Vật lí</option>
                  <option value="Hóa học">Hóa học</option>
                  <option value="Sinh học">Sinh học</option>
                  <option value="Lịch sử">Lịch sử</option>
                  <option value="Địa lí">Địa lí</option>
                  <option value="GDCD / GDKT&PL">GDCD / GDKT&PL</option>
                  <option value="Tin học">Tin học</option>
                  <option value="Công nghệ">Công nghệ</option>
                  <option value="Thể dục / GDTC">Thể dục / GDTC</option>
                  <option value="GDQP-AN">GDQP-AN</option>
                  <option value="Âm nhạc">Âm nhạc</option>
                  <option value="Mỹ thuật">Mỹ thuật</option>
                  <option value="Hoạt động trải nghiệm">Hoạt động trải nghiệm</option>
                </select>
              </div>

              <!-- Lớp giảng dạy (Chọn nhiều) -->
              <div class="space-y-2">
                <div class="flex items-center justify-between">
                  <label class="block text-[11px] font-bold text-slate-800 flex items-center gap-1">
                    <i data-lucide="layers" class="w-3.5 h-3.5 text-purple-600"></i>
                    Phân công lớp giảng dạy (Chọn nhiều lớp):
                  </label>
                  <span id="review-teacher-selected-count" class="text-[10px] font-bold bg-purple-100 text-purple-800 px-2 py-0.5 rounded-full">
                    Đã chọn: 0 lớp
                  </span>
                </div>

                <!-- Tabs Khối 10, 11, 12 -->
                <div class="flex items-center justify-between bg-slate-100 p-1 rounded-lg">
                  <div class="flex space-x-1" id="review-teacher-grade-tabs">
                    <button type="button" onclick="switchReviewTeacherGradeTab(10)" id="review-tab-btn-10" class="px-2.5 py-1 text-[11px] font-bold rounded-md bg-white text-brand-700 shadow-sm transition">Khối 10</button>
                    <button type="button" onclick="switchReviewTeacherGradeTab(11)" id="review-tab-btn-11" class="px-2.5 py-1 text-[11px] font-medium rounded-md text-slate-600 hover:text-slate-900 transition">Khối 11</button>
                    <button type="button" onclick="switchReviewTeacherGradeTab(12)" id="review-tab-btn-12" class="px-2.5 py-1 text-[11px] font-medium rounded-md text-slate-600 hover:text-slate-900 transition">Khối 12</button>
                  </div>
                  <div class="flex items-center space-x-1.5 text-[10px]">
                    <button type="button" onclick="toggleReviewAllGradeClasses(true)" class="text-brand-600 hover:underline font-semibold">Chọn hết khối</button>
                    <span class="text-slate-300">•</span>
                    <button type="button" onclick="toggleReviewAllGradeClasses(false)" class="text-slate-500 hover:underline">Bỏ chọn khối</button>
                  </div>
                </div>

                <!-- Grid of Class Chips -->
                <div id="review-teacher-classes-grid" class="grid grid-cols-4 sm:grid-cols-6 gap-1.5 max-h-36 overflow-y-auto p-1.5 bg-white border border-slate-200 rounded-lg">
                  <!-- Populated dynamically -->
                </div>
              </div>
            </div>

            <!-- SECTION 3: GIÁO VIÊN CHỦ NHIỆM (GVCN - Chọn 1 lớp chủ nhiệm duy nhất) -->
            <div id="review-section-homeroom" class="p-3 bg-amber-50/80 rounded-xl border border-amber-300 space-y-2 hidden">
              <div class="flex items-center justify-between">
                <span class="font-bold text-amber-950 flex items-center gap-1.5 text-xs">
                  <i data-lucide="crown" class="w-4 h-4 text-amber-600"></i>
                  Lớp chủ nhiệm (Bắt buộc chọn 1 lớp) <span class="text-rose-500">*</span>
                </span>
                <span class="text-[10px] font-bold text-amber-800 bg-amber-200/80 px-2 py-0.5 rounded-full">GVCN duy nhất</span>
              </div>
              <div>
                <select id="review-homeroom-class" onchange="onReviewHomeroomClassChange(this.value)" class="w-full bg-white border border-amber-300 rounded-lg px-3 py-2 text-xs font-bold text-slate-900 focus:ring-2 focus:ring-amber-500">
                  <option value="">-- Chọn lớp chủ nhiệm (trong 64 lớp) --</option>
                </select>
              </div>
              <div id="review-homeroom-conflict-alert" class="hidden text-[11px] text-amber-900 bg-amber-100 p-2 rounded-lg border border-amber-200 flex items-start gap-1.5">
                <i data-lucide="alert-circle" class="w-3.5 h-3.5 text-amber-700 shrink-0 mt-0.5"></i>
                <span id="review-homeroom-conflict-msg">Lớp này hiện đã có GVCN. Khi lưu, quyền GVCN sẽ tự động chuyển sang giáo viên này.</span>
              </div>
            </div>

            <!-- SECTION 4: PHÒNG BAN / ĐƠN VỊ KHÁC (Admin, Đoàn trường, BGH, Sao đỏ...) -->
            <div id="review-section-other" class="space-y-1 hidden">
              <label class="block font-semibold text-slate-700 mb-1">
                Phòng ban / Đơn vị công tác (nếu có)
              </label>
              <input type="text" id="review-department-other" placeholder="VD: Văn phòng Đoàn trường, Ban Giám hiệu, Tổ Giám thị..." class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-medium text-slate-900 focus:ring-2 focus:ring-brand-500 focus:bg-white transition">
            </div>
          </div>"""

assert old_block in content_norm, "old_block not found in templates/index.html"
content_norm = content_norm.replace(old_block, new_block)

with open('templates/index.html', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content_norm)

print("templates/index.html patched successfully!")
