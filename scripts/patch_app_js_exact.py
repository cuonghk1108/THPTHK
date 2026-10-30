import os
import sys

BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"
app_js_path = os.path.join(BASE_DIR, "static", "app.js")

with open(app_js_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# ------------------------------------------------------------------------------
# 1. getAllowedTabs: Replace line 2399
# ------------------------------------------------------------------------------
found_1 = False
for i, l in enumerate(lines):
    if "['conduct', 'competition', 'counseling'].forEach(tab => allowed.add(tab));" in l:
        lines[i] = "    ['teacher-classes', 'counseling'].forEach(tab => allowed.add(tab));\n"
        found_1 = True
        print(f"SUCCESS 1: Updated getAllowedTabs at line {i+1}")
        break
assert found_1, "Failed to find target 1"

# ------------------------------------------------------------------------------
# 2. renderMobileBottomNav: Replace line 2471
# ------------------------------------------------------------------------------
found_2 = False
for i, l in enumerate(lines):
    if "? ['dashboard', 'conduct', 'competition', 'counseling']" in l:
        lines[i] = "        ? ['dashboard', 'teacher-classes', 'counseling', 'profile']\n"
        found_2 = True
        print(f"SUCCESS 2: Updated renderMobileBottomNav at line {i+1}")
        break
assert found_2, "Failed to find target 2"

# ------------------------------------------------------------------------------
# 3. updateUserUI: Add student nav label logic after nav group toggle
# ------------------------------------------------------------------------------
found_3 = False
for i in range(2540, 2580):
    if lines[i].strip() == "Object.entries(navTabs).forEach(([tab, id]) => {" :
        # find matching end of this forEach
        for j in range(i, i+15):
            if lines[j].strip() == "});":
                nav_label_patch = [
                    "\n",
                    "  const isStudentUser = currentUser && (currentUser.is_student || currentUser.role === 'HOC_SINH');\n",
                    "  const tcNavBtn = document.getElementById('nav-btn-teacher-classes');\n",
                    "  if (tcNavBtn) {\n",
                    "    const span = tcNavBtn.querySelector('span');\n",
                    "    if (span) {\n",
                    "      span.textContent = isStudentUser ? 'Lớp học của tôi' : 'Lớp học & Học sinh';\n",
                    "    }\n",
                    "  }\n",
                    "  if (NAV_LABELS && NAV_LABELS['teacher-classes']) {\n",
                    "    NAV_LABELS['teacher-classes'][0] = isStudentUser ? 'Lớp của tôi' : 'Lớp & Học sinh';\n",
                    "  }\n",
                    "\n"
                ]
                lines = lines[:j+1] + nav_label_patch + lines[j+1:]
                found_3 = True
                print(f"SUCCESS 3: Added student nav label in updateUserUI at line {j+1}")
                break
        break
assert found_3, "Failed to find target 3"

# ------------------------------------------------------------------------------
# 4A. loadDashboard: Replace student dashboard block
# ------------------------------------------------------------------------------
start_4a = None
end_4a = None
for i, l in enumerate(lines):
    if "5. HỌC SINH (STUDENT)" in l:
        start_4a = i
    if start_4a and "Render HTML vào DOM" in l:
        # look backward for the closing bracket of the else
        for j in range(i-1, max(0, i-20), -1):
            if lines[j].strip() == "}":
                end_4a = j + 1
                break
        break

assert start_4a is not None and end_4a is not None, f"Failed 4A: start={start_4a}, end={end_4a}"

new_student_dash_code = [
    "    // ==========================================\n",
    "    // 5. HỌC SINH (STUDENT)\n",
    "    // ==========================================\n",
    "    else {\n",
    "      const clsName = stats.student_class || stats.class_name || (currentUser && currentUser.class_name) || (currentUser && currentUser.department_or_class) || 'Chưa xếp lớp';\n",
    "      const code = stats.student_code || (currentUser && currentUser.student_code) || '-';\n",
    "      const myV = stats.my_violations_count != null ? stats.my_violations_count : 0;\n",
    "      const vVerified = stats.my_violations_verified != null ? stats.my_violations_verified : 0;\n",
    "      const vPending = stats.my_violations_pending != null ? stats.my_violations_pending : 0;\n",
    "      const hrTeacher = stats.homeroom_teacher || 'Chưa phân công';\n",
    "      const roomNum = stats.room_number ? ` • Phòng ${stats.room_number}` : '';\n",
    "      const myViolationsList = stats.my_violations_list || [];\n",
    "\n",
    "      html = `\n",
    "        <div class=\"edtech-dash-wrap\">\n",
    "          <div class=\"edtech-hero-card\">\n",
    "            <div class=\"edtech-hero-inner\">\n",
    "              <div class=\"edtech-greeting-box\">\n",
    "                <span class=\"edtech-role-pill\" id=\"dash-role-badge\">\n",
    "                  <i data-lucide=\"graduation-cap\" class=\"w-3.5 h-3.5 inline\"></i> Học Sinh Trường THPT Hương Khê\n",
    "                </span>\n",
    "                <h2>${greeting}, <span id=\"dash-user-name\">${escapeHtml(fullName)}</span>!</h2>\n",
    "                <p id=\"dash-welcome-sub\">Chi đoàn <strong>${escapeHtml(clsName)}</strong> · Mã HS: <strong>${escapeHtml(code)}</strong> · Niên khóa 2026–2027.</p>\n",
    "              </div>\n",
    "              <div class=\"edtech-hero-actions\">\n",
    "                <span class=\"edtech-live-pill\">\n",
    "                  <span class=\"edtech-live-dot\"></span>\n",
    "                  Đồng hành cùng học sinh\n",
    "                </span>\n",
    "                <button type=\"button\" onclick=\"loadDashboard(true)\" class=\"edtech-hero-btn\">\n",
    "                  <i data-lucide=\"refresh-cw\" class=\"w-3.5 h-3.5 text-slate-500\"></i> Làm mới\n",
    "                </button>\n",
    "              </div>\n",
    "            </div>\n",
    "          </div>\n",
    "\n",
    "          <div class=\"edtech-kpi-grid\">\n",
    "            <div class=\"edtech-kpi-card cursor-pointer hover:shadow-md transition\" onclick=\"navigateTab('teacher-classes')\">\n",
    "              <div class=\"edtech-kpi-header\">\n",
    "                <span class=\"edtech-kpi-title\">Lớp học của tôi</span>\n",
    "                <div class=\"edtech-kpi-icon bg-blue-50 text-blue-600\"><i data-lucide=\"graduation-cap\" class=\"w-5 h-5\"></i></div>\n",
    "              </div>\n",
    "              <div class=\"edtech-kpi-val-row\">\n",
    "                <span class=\"edtech-kpi-val text-slate-800\">${escapeHtml(clsName)}</span>\n",
    "                <span class=\"edtech-kpi-badge bg-blue-50 text-blue-700 border border-blue-200/60 font-medium\">Mã: ${escapeHtml(code)}</span>\n",
    "              </div>\n",
    "              <div class=\"edtech-kpi-footer\">\n",
    "                <span>GVCN: ${escapeHtml(hrTeacher)}${roomNum}</span>\n",
    "                <span class=\"text-blue-600 font-medium\">Xem danh sách lớp →</span>\n",
    "              </div>\n",
    "            </div>\n",
    "\n",
    "            <div class=\"edtech-kpi-card\">\n",
    "              <div class=\"edtech-kpi-header\">\n",
    "                <span class=\"edtech-kpi-title\">Rèn luyện nề nếp cá nhân</span>\n",
    "                <div class=\"edtech-kpi-icon bg-${myV > 0 ? 'rose-50 text-rose-600' : 'emerald-50 text-emerald-600'}\">\n",
    "                  <i data-lucide=\"${myV > 0 ? 'alert-circle' : 'smile'}\" class=\"w-5 h-5\"></i>\n",
    "                </div>\n",
    "              </div>\n",
    "              <div class=\"edtech-kpi-val-row\">\n",
    "                <span class=\"edtech-kpi-val text-${myV > 0 ? 'rose-700' : 'emerald-700'}\">${myV}</span>\n",
    "                <span class=\"edtech-kpi-badge bg-${myV > 0 ? 'rose-50 text-rose-700 border border-rose-200/60' : 'emerald-50 text-emerald-700 border border-emerald-200/60'} font-medium\">\n",
    "                  ${myV === 0 ? 'Rất tốt' : 'Lưu ý'}\n",
    "                </span>\n",
    "              </div>\n",
    "              <div class=\"edtech-kpi-footer\">\n",
    "                <span>${myV === 0 ? 'Tuyệt vời! Tiếp tục giữ vững nhé ✨' : `Đã duyệt: ${vVerified} • Chờ xử lý: ${vPending}`}</span>\n",
    "              </div>\n",
    "            </div>\n",
    "\n",
    "            <div class=\"edtech-kpi-card cursor-pointer hover:shadow-md transition\" onclick=\"navigateTab('counseling')\">\n",
    "              <div class=\"edtech-kpi-header\">\n",
    "                <span class=\"edtech-kpi-title\">Góc sẻ chia & Tâm lý</span>\n",
    "                <div class=\"edtech-kpi-icon bg-amber-50 text-amber-600\"><i data-lucide=\"heart-handshake\" class=\"w-5 h-5\"></i></div>\n",
    "              </div>\n",
    "              <div class=\"edtech-kpi-val-row\">\n",
    "                <span class=\"edtech-kpi-val text-amber-700\">Tư vấn</span>\n",
    "                <span class=\"edtech-kpi-badge bg-amber-50 text-amber-700 border border-amber-200/60 font-medium\">Học đường</span>\n",
    "              </div>\n",
    "              <div class=\"edtech-kpi-footer\">\n",
    "                <span>Không gian lắng nghe học sinh</span>\n",
    "                <span class=\"text-amber-700 font-medium\">Gửi chia sẻ →</span>\n",
    "              </div>\n",
    "            </div>\n",
    "          </div>\n",
    "\n",
    "          <!-- BẢNG LỖI VI PHẠM NỀ NẾP CỦA HỌC SINH -->\n",
    "          <div class=\"bg-white rounded-2xl border border-slate-200/80 shadow-sm p-5 space-y-4\">\n",
    "            <div class=\"flex items-center justify-between pb-3 border-b border-slate-100 flex-wrap gap-2\">\n",
    "              <div class=\"flex items-center gap-2.5\">\n",
    "                <div class=\"w-9 h-9 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold\">\n",
    "                  <i data-lucide=\"clipboard-check\" class=\"w-5 h-5\"></i>\n",
    "                </div>\n",
    "                <div>\n",
    "                  <h3 class=\"font-bold text-slate-800 text-sm md:text-base\">Lỗi vi phạm nề nếp của bạn</h3>\n",
    "                  <p class=\"text-xs text-slate-500 font-normal mt-0.5\">Hệ thống ghi nhận và đồng bộ trực tiếp phục vụ rèn luyện cá nhân</p>\n",
    "                </div>\n",
    "              </div>\n",
    "              <span class=\"px-3 py-1 rounded-full text-xs font-semibold ${myV === 0 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'}\">\n",
    "                ${myV === 0 ? 'Không có vi phạm' : `${myV} bản ghi vi phạm`}\n",
    "              </span>\n",
    "            </div>\n",
    "\n",
    "            ${myViolationsList.length === 0 ? `\n",
    "              <div class=\"p-6 md:p-8 rounded-xl bg-gradient-to-r from-emerald-50/70 via-teal-50/40 to-white border border-emerald-200/70 text-center flex flex-col items-center justify-center space-y-2\">\n",
    "                <div class=\"w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center\">\n",
    "                  <i data-lucide=\"award\" class=\"w-6 h-6\"></i>\n",
    "                </div>\n",
    "                <h4 class=\"font-bold text-emerald-900 text-sm md:text-base\">Chúc mừng bạn! Không có lỗi vi phạm nề nếp nào được ghi nhận</h4>\n",
    "                <p class=\"text-xs text-emerald-700 max-w-lg leading-relaxed\">Bạn đang chấp hành rất nghiêm túc nội quy, kỷ luật của Nhà trường. Hãy tiếp tục giữ vững tinh thần gương mẫu và tinh hoa học sinh Hương Khê nhé!</p>\n",
    "              </div>\n",
    "            ` : `\n",
    "              <div class=\"overflow-x-auto\">\n",
    "                <table class=\"w-full text-left border-collapse text-xs md:text-sm\">\n",
    "                  <thead>\n",
    "                    <tr class=\"bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]\">\n",
    "                      <th class=\"py-2.5 px-3 w-12 text-center\">STT</th>\n",
    "                      <th class=\"py-2.5 px-3 w-28\">Thời gian</th>\n",
    "                      <th class=\"py-2.5 px-3\">Nội dung vi phạm / Quy chế</th>\n",
    "                      <th class=\"py-2.5 px-3 w-36\">Địa điểm</th>\n",
    "                      <th class=\"py-2.5 px-3 w-24 text-center\">Điểm trừ</th>\n",
    "                      <th class=\"py-2.5 px-3 w-32 text-center\">Trạng thái</th>\n",
    "                    </tr>\n",
    "                  </thead>\n",
    "                  <tbody class=\"divide-y divide-slate-100\">\n",
    "                    ${myViolationsList.map((v, i) => `\n",
    "                      <tr class=\"hover:bg-slate-50/80 transition-colors\">\n",
    "                        <td class=\"py-3 px-3 text-center font-bold text-slate-400\">${i + 1}</td>\n",
    "                        <td class=\"py-3 px-3 font-mono text-slate-600 whitespace-nowrap\">${escapeHtml(v.occurred_at || '')}</td>\n",
    "                        <td class=\"py-3 px-3\">\n",
    "                          <span class=\"font-bold text-slate-800 block\">${escapeHtml(v.rule_name || 'Vi phạm nội quy')}</span>\n",
    "                          ${v.rule_code ? `<span class=\"text-[11px] text-slate-500 font-mono\">Mã lỗi: ${escapeHtml(v.rule_code)}</span>` : ''}\n",
    "                        </td>\n",
    "                        <td class=\"py-3 px-3 text-slate-600\">${escapeHtml(v.location || 'Khuôn viên trường')}</td>\n",
    "                        <td class=\"py-3 px-3 text-center font-bold text-rose-600 whitespace-nowrap\">-${v.points_deducted}đ</td>\n",
    "                        <td class=\"py-3 px-3 text-center\">\n",
    "                          <span class=\"px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${v.status === 'VERIFIED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'}\">\n",
    "                            ${escapeHtml(v.status_display || v.status)}\n",
    "                          </span>\n",
    "                        </td>\n",
    "                      </tr>\n",
    "                    `).join('')}\n",
    "                  </tbody>\n",
    "                </table>\n",
    "              </div>\n",
    "            `}\n",
    "          </div>\n",
    "        </div>\n",
    "      `;\n",
    "    }\n",
]

lines = lines[:start_4a] + new_student_dash_code + lines[end_4a:]
print("SUCCESS 4A: Replaced student dashboard HTML")

# ------------------------------------------------------------------------------
# 4B. Remove renderTopPodium for students
# ------------------------------------------------------------------------------
found_4b = False
for i, l in enumerate(lines):
    if "renderTopPodium(snapshot.classes, 'ALL', 'week');" in l:
        lines[i] = "      // Học sinh không xem bảng xếp hạng thi đua và bục vinh danh\n"
        found_4b = True
        print(f"SUCCESS 4B: Removed renderTopPodium at line {i+1}")
        break
assert found_4b, "Failed to find target 4B"

# ------------------------------------------------------------------------------
# 5. loadTeacherClassesModule: Role badge for student
# ------------------------------------------------------------------------------
found_5 = False
for i, l in enumerate(lines):
    if "roleBadgeText.textContent = 'Giáo viên bộ môn (GVBM)';" in l:
        # insert student role badge right after
        # find the next } else {
        for j in range(i, i+10):
            if lines[j].strip() == "} else {":
                stu_role_badge = [
                    "      } else if (currentUser.is_student || currentUser.role === 'HOC_SINH') {\n",
                    "        roleBadgeText.textContent = 'Học sinh (Lớp học của tôi)';\n",
                ]
                lines = lines[:j] + stu_role_badge + lines[j+1:]
                found_5 = True
                print(f"SUCCESS 5: Added student role badge at line {j+1}")
                break
        break
assert found_5, "Failed to find target 5"

# ------------------------------------------------------------------------------
# 6. renderTeacherStudentsTable: Replace full function
# ------------------------------------------------------------------------------
start_6 = None
end_6 = None
for i, l in enumerate(lines):
    if "function renderTeacherStudentsTable(students) {" in l:
        start_6 = i
    if start_6 and "function switchTeacherSubTab(" in l:
        end_6 = i
        break

assert start_6 is not None and end_6 is not None, f"Failed 6: start={start_6}, end={end_6}"

new_render_stu_table_code = [
    "function renderTeacherStudentsTable(students) {\n",
    "  const tbody = document.getElementById('teacher-students-table-body');\n",
    "  const mobileList = document.getElementById('teacher-students-mobile-list');\n",
    "  const emptyState = document.getElementById('teacher-students-empty-state');\n",
    "\n",
    "  if (!tbody || !mobileList) return;\n",
    "\n",
    "  if (students.length === 0) {\n",
    "    tbody.innerHTML = '';\n",
    "    mobileList.innerHTML = '';\n",
    "    if (emptyState) emptyState.classList.remove('hidden');\n",
    "    return;\n",
    "  }\n",
    "\n",
    "  if (emptyState) emptyState.classList.add('hidden');\n",
    "\n",
    "  const isStudent = currentUser && (currentUser.is_student || currentUser.role === 'HOC_SINH');\n",
    "  const myStudentCode = (currentUser?.student_code || currentUser?.username || '').trim().toLowerCase();\n",
    "  const myStudentId = currentUser?.student_profile?.id || currentUser?.student_id;\n",
    "\n",
    "  // Desktop Table\n",
    "  tbody.innerHTML = students.map((s, idx) => {\n",
    "    const isStudying = s.status === 'STUDYING';\n",
    "    const statusBadge = isStudying\n",
    "      ? '<span class=\"px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200\">Đang học</span>'\n",
    "      : `<span class=\"px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200\">${escapeHtml(s.status_display)}</span>`;\n",
    "\n",
    "    const feedbackCountBadge = s.feedback_count > 0\n",
    "      ? `<span class=\"px-2 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-700\">${s.feedback_count}</span>`\n",
    "      : `<span class=\"text-slate-400 text-xs\">0</span>`;\n",
    "\n",
    "    const isSelf = isStudent && ((s.student_code && s.student_code.trim().toLowerCase() === myStudentCode) || (s.id && s.id === myStudentId));\n",
    "\n",
    "    let actionBtnsHtml = '';\n",
    "    if (isStudent) {\n",
    "      if (isSelf) {\n",
    "        actionBtnsHtml = `\n",
    "          <button type=\"button\" onclick=\"openStudentProfileModal(${s.id})\" title=\"Xem hồ sơ của tôi\"\n",
    "            class=\"px-2.5 py-1 text-xs font-semibold rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 transition-colors flex items-center gap-1\">\n",
    "            <i data-lucide=\"user\" class=\"w-3.5 h-3.5\"></i>\n",
    "            <span>Hồ sơ của tôi</span>\n",
    "          </button>\n",
    "        `;\n",
    "      } else {\n",
    "        actionBtnsHtml = `<span class=\"text-xs text-slate-400 italic\">Bạn cùng lớp</span>`;\n",
    "      }\n",
    "    } else {\n",
    "      actionBtnsHtml = `\n",
    "        <button type=\"button\" onclick=\"openStudentProfileModal(${s.id})\" title=\"Xem hồ sơ chi tiết\"\n",
    "          class=\"px-2.5 py-1 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors flex items-center gap-1\">\n",
    "          <i data-lucide=\"user\" class=\"w-3.5 h-3.5\"></i>\n",
    "          <span>Hồ sơ</span>\n",
    "        </button>\n",
    "        <button type=\"button\" onclick=\"openSendFeedbackModal(${s.id}, ${activeTeacherClass.id}, '${escapeHtml(s.full_name)}', '${escapeHtml(activeTeacherClass.name)}')\" title=\"Gửi phản hồi cho học sinh\"\n",
    "          class=\"px-2.5 py-1 text-xs font-semibold rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 transition-colors flex items-center gap-1\">\n",
    "          <i data-lucide=\"message-square-plus\" class=\"w-3.5 h-3.5\"></i>\n",
    "          <span>Phản hồi</span>\n",
    "        </button>\n",
    "        <button type=\"button\" onclick=\"openViolationModalForStudent(${activeTeacherClass.id}, ${s.id}, '${escapeHtml(s.full_name)}')\" title=\"Lập biên bản vi phạm kỷ luật\"\n",
    "          class=\"px-2 py-1 text-xs font-medium rounded-lg text-rose-600 hover:bg-rose-50 transition-colors\">\n",
    "          <i data-lucide=\"scale\" class=\"w-3.5 h-3.5\"></i>\n",
    "        </button>\n",
    "      `;\n",
    "    }\n",
    "\n",
    "    const nameCellHtml = (isStudent && !isSelf)\n",
    "      ? `<span class=\"font-bold text-slate-900\">${escapeHtml(s.full_name)}</span>`\n",
    "      : `\n",
    "        <button type=\"button\" onclick=\"openStudentProfileModal(${s.id})\" class=\"font-bold text-slate-900 hover:text-blue-600 transition-colors text-left flex items-center gap-1.5 group\">\n",
    "          <span>${escapeHtml(s.full_name)}</span>\n",
    "          <i data-lucide=\"external-link\" class=\"w-3.5 h-3.5 opacity-0 group-hover:opacity-100 text-blue-500 transition-opacity\"></i>\n",
    "        </button>\n",
    "      `;\n",
    "\n",
    "    return `\n",
    "      <tr class=\"hover:bg-slate-50/80 transition-colors ${isSelf ? 'bg-blue-50/40' : ''}\">\n",
    "        <td class=\"py-3 px-4 text-center font-medium text-slate-500\">${s.stt || (idx + 1)}</td>\n",
    "        <td class=\"py-3 px-4 font-mono font-bold text-slate-700\">${escapeHtml(s.student_code)}</td>\n",
    "        <td class=\"py-3 px-4\">\n",
    "          ${nameCellHtml}\n",
    "        </td>\n",
    "        <td class=\"py-3 px-4 text-slate-600\">${escapeHtml(s.gender_display || '')}</td>\n",
    "        <td class=\"py-3 px-4 text-slate-600\">${escapeHtml(s.date_of_birth || '')}</td>\n",
    "        <td class=\"py-3 px-4 text-center\">${statusBadge}</td>\n",
    "        <td class=\"py-3 px-4 text-center\">${feedbackCountBadge}</td>\n",
    "        <td class=\"py-3 px-4 text-right\">\n",
    "          <div class=\"flex items-center justify-end gap-1.5\">\n",
    "            ${actionBtnsHtml}\n",
    "          </div>\n",
    "        </td>\n",
    "      </tr>\n",
    "    `;\n",
    "  }).join('');\n",
    "\n",
    "  // Mobile Cards\n",
    "  mobileList.innerHTML = students.map((s, idx) => {\n",
    "    const isSelf = isStudent && ((s.student_code && s.student_code.trim().toLowerCase() === myStudentCode) || (s.id && s.id === myStudentId));\n",
    "\n",
    "    let mobileActionHtml = '';\n",
    "    if (isStudent) {\n",
    "      if (isSelf) {\n",
    "        mobileActionHtml = `\n",
    "          <button type=\"button\" onclick=\"openStudentProfileModal(${s.id})\" class=\"px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 text-white\">\n",
    "            Hồ sơ của tôi\n",
    "          </button>\n",
    "        `;\n",
    "      } else {\n",
    "        mobileActionHtml = `<span class=\"text-xs text-slate-400 italic\">Bạn cùng lớp</span>`;\n",
    "      }\n",
    "    } else {\n",
    "      mobileActionHtml = `\n",
    "        <button type=\"button\" onclick=\"openStudentProfileModal(${s.id})\" class=\"px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 text-slate-700\">\n",
    "          Hồ sơ\n",
    "        </button>\n",
    "        <button type=\"button\" onclick=\"openSendFeedbackModal(${s.id}, ${activeTeacherClass.id}, '${escapeHtml(s.full_name)}', '${escapeHtml(activeTeacherClass.name)}')\" class=\"px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 text-white\">\n",
    "          Phản hồi\n",
    "        </button>\n",
    "      `;\n",
    "    }\n",
    "\n",
    "    const mobileNameHtml = (isStudent && !isSelf)\n",
    "      ? `<span class=\"font-bold text-slate-900 text-sm\">${escapeHtml(s.full_name)}</span>`\n",
    "      : `<button type=\"button\" onclick=\"openStudentProfileModal(${s.id})\" class=\"font-bold text-slate-900 text-sm hover:text-blue-600 text-left\">${escapeHtml(s.full_name)}</button>`;\n",
    "\n",
    "    return `\n",
    "      <div class=\"p-3.5 bg-white rounded-xl border ${isSelf ? 'border-blue-300 ring-2 ring-blue-50 bg-blue-50/20' : 'border-slate-200'} space-y-2 mb-2\">\n",
    "        <div class=\"flex items-center justify-between\">\n",
    "          <div class=\"flex items-center gap-2\">\n",
    "            <span class=\"w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-xs\">${s.stt || (idx + 1)}</span>\n",
    "            ${mobileNameHtml}\n",
    "          </div>\n",
    "          <span class=\"font-mono text-xs font-bold text-slate-600\">${escapeHtml(s.student_code)}</span>\n",
    "        </div>\n",
    "        <div class=\"flex items-center justify-between text-xs text-slate-500 pt-1 border-t border-slate-100\">\n",
    "          <span>${escapeHtml(s.gender_display || '')} • ${escapeHtml(s.date_of_birth || '')}</span>\n",
    "          <span class=\"font-semibold text-blue-700\">${s.feedback_count} phản hồi</span>\n",
    "        </div>\n",
    "        <div class=\"flex items-center justify-end gap-2 pt-2\">\n",
    "          ${mobileActionHtml}\n",
    "        </div>\n",
    "      </div>\n",
    "    `;\n",
    "  }).join('');\n",
    "\n",
    "  if (window.lucide) lucide.createIcons();\n",
    "}\n\n"
]

lines = lines[:start_6] + new_render_stu_table_code + lines[end_6:]
print("SUCCESS 6: Replaced renderTeacherStudentsTable")

with open(app_js_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("ALL APP.JS EXACT PATCHES APPLIED SUCCESSFULLY!")
