import os
import sys

BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"
app_js_path = os.path.join(BASE_DIR, "static", "app.js")

with open(app_js_path, "r", encoding="utf-8") as f:
    code = f.read()

code_norm = code.replace("\r\n", "\n")

# ==============================================================================
# 1. getAllowedTabs
# ==============================================================================
old_tabs_stu = """  } else if (user.is_student || user.role === 'HOC_SINH') {
    ['conduct', 'competition', 'counseling'].forEach(tab => allowed.add(tab));
  }"""

new_tabs_stu = """  } else if (user.is_student || user.role === 'HOC_SINH') {
    ['teacher-classes', 'counseling'].forEach(tab => allowed.add(tab));
  }"""

if old_tabs_stu in code_norm:
    code_norm = code_norm.replace(old_tabs_stu, new_tabs_stu)
    print("SUCCESS 1: Updated getAllowedTabs for students (removed conduct & competition, added teacher-classes)")
else:
    print("WARNING 1: old_tabs_stu not found")

# ==============================================================================
# 2. renderMobileBottomNav
# ==============================================================================
old_mob_nav = """      : currentUser?.is_student || currentUser?.role === 'HOC_SINH'
        ? ['dashboard', 'conduct', 'competition', 'counseling']"""

new_mob_nav = """      : currentUser?.is_student || currentUser?.role === 'HOC_SINH'
        ? ['dashboard', 'teacher-classes', 'counseling', 'profile']"""

if old_mob_nav in code_norm:
    code_norm = code_norm.replace(old_mob_nav, new_mob_nav)
    print("SUCCESS 2: Updated renderMobileBottomNav for students")
else:
    print("WARNING 2: old_mob_nav not found")

# ==============================================================================
# 3. updateUserUI: Change nav label for students
# ==============================================================================
old_ui_toggle = """  Object.entries(navTabs).forEach(([tab, id]) => {
    const button = document.getElementById(id);
    if (button) button.classList.toggle('hidden', !allowed.has(tab));
  });"""

new_ui_toggle = """  Object.entries(navTabs).forEach(([tab, id]) => {
    const button = document.getElementById(id);
    if (button) button.classList.toggle('hidden', !allowed.has(tab));
  });

  const isStudentUser = currentUser && (currentUser.is_student || currentUser.role === 'HOC_SINH');
  const tcNavBtn = document.getElementById('nav-btn-teacher-classes');
  if (tcNavBtn) {
    const span = tcNavBtn.querySelector('span');
    if (span) {
      span.textContent = isStudentUser ? 'Lớp học của tôi' : 'Lớp học & Học sinh';
    }
  }
  if (NAV_LABELS && NAV_LABELS['teacher-classes']) {
    NAV_LABELS['teacher-classes'][0] = isStudentUser ? 'Lớp của tôi' : 'Lớp & Học sinh';
  }"""

if old_ui_toggle in code_norm:
    code_norm = code_norm.replace(old_ui_toggle, new_ui_toggle)
    print("SUCCESS 3: Added dynamic nav label for students in updateUserUI")
else:
    print("WARNING 3: old_ui_toggle not found")

# ==============================================================================
# 4. loadDashboard: Replace student dashboard HTML and remove podium
# ==============================================================================
old_dash_stu = """    // ==========================================
    // 5. HỌC SINH (STUDENT)
    // ==========================================
    else {
      const clsName = stats.class_name || (currentUser && currentUser.class_name) || 'Chưa xếp lớp';
      const code = stats.student_code || (currentUser && currentUser.student_code) || '-';
      const myV = stats.my_violations_count != null ? stats.my_violations_count : 0;
      const clsScore = stats.class_total_score != null ? Number(stats.class_total_score).toFixed(2) : '100.00';
      const clsRank = stats.class_rank != null ? '#' + stats.class_rank : '-';

      html = `
        <div class="edtech-dash-wrap">
          <div class="edtech-hero-card">
            <div class="edtech-hero-inner">
              <div class="edtech-greeting-box">
                <span class="edtech-role-pill" id="dash-role-badge">
                  <i data-lucide="graduation-cap" class="w-3.5 h-3.5 inline"></i> Học Sinh Trường THPT Hương Khê
                </span>
                <h2>${greeting}, <span id="dash-user-name">${escapeHtml(fullName)}</span>!</h2>
                <p id="dash-welcome-sub">Chi đoàn <strong>${escapeHtml(clsName)}</strong> · Mã HS: <strong>${escapeHtml(code)}</strong> · Niên khóa 2026–2027.</p>
              </div>
              <div class="edtech-hero-actions">
                <span class="edtech-live-pill">
                  <span class="edtech-live-dot"></span>
                  Đồng hành cùng học sinh
                </span>
                <button type="button" onclick="loadDashboard(true)" class="edtech-hero-btn">
                  <i data-lucide="refresh-cw" class="w-3.5 h-3.5 text-slate-500"></i> Làm mới
                </button>
              </div>
            </div>
          </div>

          <div class="edtech-kpi-grid">
            <div class="edtech-kpi-card" onclick="navigateTab('profile')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Hồ sơ cá nhân</span>
                <div class="edtech-kpi-icon bg-blue-50 text-blue-600"><i data-lucide="user" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-slate-800">${escapeHtml(clsName)}</span>
                <span class="edtech-kpi-badge bg-blue-50 text-blue-700 border border-blue-200/60 font-medium">Mã: ${escapeHtml(code)}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Thông tin đoàn viên</span>
                <span class="text-blue-600 font-medium">Xem hồ sơ →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('competition')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Điểm thi đua lớp (${weekLabel})</span>
                <div class="edtech-kpi-icon bg-emerald-50 text-emerald-600"><i data-lucide="award" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-emerald-700">${clsScore}</span>
                <span class="edtech-kpi-badge bg-emerald-50 text-emerald-700 border border-emerald-200/60 font-medium">Hạng: ${clsRank}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Toàn trường</span>
                <span class="text-emerald-700 font-medium">Bảng vàng →</span>
              </div>
            </div>

            <div class="edtech-kpi-card">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Rèn luyện nề nếp cá nhân</span>
                <div class="edtech-kpi-icon bg-${myV > 0 ? 'rose-50 text-rose-600' : 'emerald-50 text-emerald-600'}">
                  <i data-lucide="${myV > 0 ? 'alert-circle' : 'smile'}" class="w-5 h-5"></i>
                </div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-${myV > 0 ? 'rose-700' : 'emerald-700'}">${myV}</span>
                <span class="edtech-kpi-badge bg-${myV > 0 ? 'rose-50 text-rose-700 border border-rose-200/60' : 'emerald-50 text-emerald-700 border border-emerald-200/60'} font-medium">
                  ${myV === 0 ? 'Rất tốt' : 'Lưu ý'}
                </span>
              </div>
              <div class="edtech-kpi-footer">
                <span>${myV === 0 ? 'Tuyệt vời! Tiếp tục giữ vững nhé ✨' : 'Cần chú ý nội quy nhà trường'}</span>
              </div>
            </div>
          </div>

          <!-- PODIUM VINH DANH CHO HỌC SINH -->
          <div class="edtech-podium-card">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-semibold text-slate-800 text-base flex items-center gap-2">
                <i data-lucide="crown" class="w-5 h-5 text-amber-500"></i>
                Top 3 Chi Đoàn Dẫn Đầu Toàn Trường
              </h3>
              <span class="text-xs text-slate-500 font-medium">${currentWeekName} · Năm học 2026–2027</span>
            </div>
            <div id="dashboard-podium-content" class="edtech-podium-grid"></div>
          </div>
        </div>
      `;
    }"""

new_dash_stu = """    // ==========================================
    // 5. HỌC SINH (STUDENT)
    // ==========================================
    else {
      const clsName = stats.student_class || stats.class_name || (currentUser && currentUser.class_name) || (currentUser && currentUser.department_or_class) || 'Chưa xếp lớp';
      const code = stats.student_code || (currentUser && currentUser.student_code) || '-';
      const myV = stats.my_violations_count != null ? stats.my_violations_count : 0;
      const vVerified = stats.my_violations_verified != null ? stats.my_violations_verified : 0;
      const vPending = stats.my_violations_pending != null ? stats.my_violations_pending : 0;
      const hrTeacher = stats.homeroom_teacher || 'Chưa phân công';
      const roomNum = stats.room_number ? ` • Phòng ${stats.room_number}` : '';
      const myViolationsList = stats.my_violations_list || [];

      html = `
        <div class="edtech-dash-wrap">
          <div class="edtech-hero-card">
            <div class="edtech-hero-inner">
              <div class="edtech-greeting-box">
                <span class="edtech-role-pill" id="dash-role-badge">
                  <i data-lucide="graduation-cap" class="w-3.5 h-3.5 inline"></i> Học Sinh Trường THPT Hương Khê
                </span>
                <h2>${greeting}, <span id="dash-user-name">${escapeHtml(fullName)}</span>!</h2>
                <p id="dash-welcome-sub">Chi đoàn <strong>${escapeHtml(clsName)}</strong> · Mã HS: <strong>${escapeHtml(code)}</strong> · Niên khóa 2026–2027.</p>
              </div>
              <div class="edtech-hero-actions">
                <span class="edtech-live-pill">
                  <span class="edtech-live-dot"></span>
                  Đồng hành cùng học sinh
                </span>
                <button type="button" onclick="loadDashboard(true)" class="edtech-hero-btn">
                  <i data-lucide="refresh-cw" class="w-3.5 h-3.5 text-slate-500"></i> Làm mới
                </button>
              </div>
            </div>
          </div>

          <div class="edtech-kpi-grid">
            <div class="edtech-kpi-card cursor-pointer hover:shadow-md transition" onclick="navigateTab('teacher-classes')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Lớp học của tôi</span>
                <div class="edtech-kpi-icon bg-blue-50 text-blue-600"><i data-lucide="graduation-cap" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-slate-800">${escapeHtml(clsName)}</span>
                <span class="edtech-kpi-badge bg-blue-50 text-blue-700 border border-blue-200/60 font-medium">Mã: ${escapeHtml(code)}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>GVCN: ${escapeHtml(hrTeacher)}${roomNum}</span>
                <span class="text-blue-600 font-medium">Xem danh sách lớp →</span>
              </div>
            </div>

            <div class="edtech-kpi-card">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Rèn luyện nề nếp cá nhân</span>
                <div class="edtech-kpi-icon bg-${myV > 0 ? 'rose-50 text-rose-600' : 'emerald-50 text-emerald-600'}">
                  <i data-lucide="${myV > 0 ? 'alert-circle' : 'smile'}" class="w-5 h-5"></i>
                </div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-${myV > 0 ? 'rose-700' : 'emerald-700'}">${myV}</span>
                <span class="edtech-kpi-badge bg-${myV > 0 ? 'rose-50 text-rose-700 border border-rose-200/60' : 'emerald-50 text-emerald-700 border border-emerald-200/60'} font-medium">
                  ${myV === 0 ? 'Rất tốt' : 'Lưu ý'}
                </span>
              </div>
              <div class="edtech-kpi-footer">
                <span>${myV === 0 ? 'Tuyệt vời! Tiếp tục giữ vững nhé ✨' : `Đã duyệt: ${vVerified} • Chờ xử lý: ${vPending}`}</span>
              </div>
            </div>

            <div class="edtech-kpi-card cursor-pointer hover:shadow-md transition" onclick="navigateTab('counseling')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Góc sẻ chia & Tâm lý</span>
                <div class="edtech-kpi-icon bg-amber-50 text-amber-600"><i data-lucide="heart-handshake" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-amber-700">Tư vấn</span>
                <span class="edtech-kpi-badge bg-amber-50 text-amber-700 border border-amber-200/60 font-medium">Học đường</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Không gian lắng nghe học sinh</span>
                <span class="text-amber-700 font-medium">Gửi chia sẻ →</span>
              </div>
            </div>
          </div>

          <!-- BẢNG LỖI VI PHẠM NỀ NẾP CỦA HỌC SINH -->
          <div class="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-5 space-y-4">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100 flex-wrap gap-2">
              <div class="flex items-center gap-2.5">
                <div class="w-9 h-9 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold">
                  <i data-lucide="clipboard-check" class="w-5 h-5"></i>
                </div>
                <div>
                  <h3 class="font-bold text-slate-800 text-sm md:text-base">Lỗi vi phạm nề nếp của bạn</h3>
                  <p class="text-xs text-slate-500 font-normal mt-0.5">Hệ thống ghi nhận và đồng bộ trực tiếp phục vụ rèn luyện cá nhân</p>
                </div>
              </div>
              <span class="px-3 py-1 rounded-full text-xs font-semibold ${myV === 0 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'}">
                ${myV === 0 ? 'Không có vi phạm' : `${myV} bản ghi vi phạm`}
              </span>
            </div>

            ${myViolationsList.length === 0 ? `
              <div class="p-6 md:p-8 rounded-xl bg-gradient-to-r from-emerald-50/70 via-teal-50/40 to-white border border-emerald-200/70 text-center flex flex-col items-center justify-center space-y-2">
                <div class="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center">
                  <i data-lucide="award" class="w-6 h-6"></i>
                </div>
                <h4 class="font-bold text-emerald-900 text-sm md:text-base">Chúc mừng bạn! Không có lỗi vi phạm nề nếp nào được ghi nhận</h4>
                <p class="text-xs text-emerald-700 max-w-lg leading-relaxed">Bạn đang chấp hành rất nghiêm túc nội quy, kỷ luật của Nhà trường. Hãy tiếp tục giữ vững tinh thần gương mẫu và tinh hoa học sinh Hương Khê nhé!</p>
              </div>
            ` : `
              <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse text-xs md:text-sm">
                  <thead>
                    <tr class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
                      <th class="py-2.5 px-3 w-12 text-center">STT</th>
                      <th class="py-2.5 px-3 w-28">Thời gian</th>
                      <th class="py-2.5 px-3">Nội dung vi phạm / Quy chế</th>
                      <th class="py-2.5 px-3 w-36">Địa điểm</th>
                      <th class="py-2.5 px-3 w-24 text-center">Điểm trừ</th>
                      <th class="py-2.5 px-3 w-32 text-center">Trạng thái</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-100">
                    ${myViolationsList.map((v, i) => `
                      <tr class="hover:bg-slate-50/80 transition-colors">
                        <td class="py-3 px-3 text-center font-bold text-slate-400">${i + 1}</td>
                        <td class="py-3 px-3 font-mono text-slate-600 whitespace-nowrap">${escapeHtml(v.occurred_at || '')}</td>
                        <td class="py-3 px-3">
                          <span class="font-bold text-slate-800 block">${escapeHtml(v.rule_name || 'Vi phạm nội quy')}</span>
                          ${v.rule_code ? `<span class="text-[11px] text-slate-500 font-mono">Mã lỗi: ${escapeHtml(v.rule_code)}</span>` : ''}
                        </td>
                        <td class="py-3 px-3 text-slate-600">${escapeHtml(v.location || 'Khuôn viên trường')}</td>
                        <td class="py-3 px-3 text-center font-bold text-rose-600 whitespace-nowrap">-${v.points_deducted}đ</td>
                        <td class="py-3 px-3 text-center">
                          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${v.status === 'VERIFIED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'}">
                            ${escapeHtml(v.status_display || v.status)}
                          </span>
                        </td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              </div>
            `}
          </div>
        </div>
      `;
    }"""

if old_dash_stu in code_norm:
    code_norm = code_norm.replace(old_dash_stu, new_dash_stu)
    print("SUCCESS 4A: Replaced student dashboard HTML with KPI + Violations Table (removed podium and competition card)")
else:
    print("WARNING 4A: old_dash_stu not found")

# Remove renderTopPodium for students
old_podium_stu = """    } else if (isStudent) {
      renderTopPodium(snapshot.classes, 'ALL', 'week');
    }"""

new_podium_stu = """    } else if (isStudent) {
      // Học sinh không xem bảng xếp hạng thi đua và bục vinh danh
    }"""

if old_podium_stu in code_norm:
    code_norm = code_norm.replace(old_podium_stu, new_podium_stu)
    print("SUCCESS 4B: Removed renderTopPodium call for students")
else:
    print("WARNING 4B: old_podium_stu not found")

# ==============================================================================
# 5. loadTeacherClassesModule: Role badge for student
# ==============================================================================
old_tc_badge = """      } else if (currentUser.role === 'GVBM' || currentUser.is_gvbm) {
        roleBadgeText.textContent = 'Giáo viên bộ môn (GVBM)';
      } else {"""

new_tc_badge = """      } else if (currentUser.role === 'GVBM' || currentUser.is_gvbm) {
        roleBadgeText.textContent = 'Giáo viên bộ môn (GVBM)';
      } else if (currentUser.is_student || currentUser.role === 'HOC_SINH') {
        roleBadgeText.textContent = 'Học sinh (Lớp học của tôi)';
      } else {"""

if old_tc_badge in code_norm:
    code_norm = code_norm.replace(old_tc_badge, new_tc_badge)
    print("SUCCESS 5: Added student role badge text in loadTeacherClassesModule")
else:
    print("WARNING 5: old_tc_badge not found")

# ==============================================================================
# 6. renderTeacherStudentsTable: Role-aware student roster
# ==============================================================================
old_render_stu_table = """function renderTeacherStudentsTable(students) {
  const tbody = document.getElementById('teacher-students-table-body');
  const mobileList = document.getElementById('teacher-students-mobile-list');
  const emptyState = document.getElementById('teacher-students-empty-state');

  if (!tbody || !mobileList) return;

  if (students.length === 0) {
    tbody.innerHTML = '';
    mobileList.innerHTML = '';
    if (emptyState) emptyState.classList.remove('hidden');
    return;
  }

  if (emptyState) emptyState.classList.add('hidden');

  // Desktop Table
  tbody.innerHTML = students.map((s, idx) => {
    const isStudying = s.status === 'STUDYING';
    const statusBadge = isStudying
      ? '<span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">Đang học</span>'
      : `<span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">${escapeHtml(s.status_display)}</span>`;

    const feedbackCountBadge = s.feedback_count > 0
      ? `<span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-700">${s.feedback_count}</span>`
      : `<span class="text-slate-400 text-xs">0</span>`;

    return `
      <tr class="hover:bg-slate-50/80 transition-colors">
        <td class="py-3 px-4 text-center font-medium text-slate-500">${s.stt || (idx + 1)}</td>
        <td class="py-3 px-4 font-mono font-bold text-slate-700">${escapeHtml(s.student_code)}</td>
        <td class="py-3 px-4">
          <button type="button" onclick="openStudentProfileModal(${s.id})" class="font-bold text-slate-900 hover:text-blue-600 transition-colors text-left flex items-center gap-1.5 group">
            <span>${escapeHtml(s.full_name)}</span>
            <i data-lucide="external-link" class="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 text-blue-500 transition-opacity"></i>
          </button>
        </td>
        <td class="py-3 px-4 text-slate-600">${escapeHtml(s.gender_display || '')}</td>
        <td class="py-3 px-4 text-slate-600">${escapeHtml(s.date_of_birth || '')}</td>
        <td class="py-3 px-4 text-center">${statusBadge}</td>
        <td class="py-3 px-4 text-center">${feedbackCountBadge}</td>
        <td class="py-3 px-4 text-right">
          <div class="flex items-center justify-end gap-1.5">
            <button type="button" onclick="openStudentProfileModal(${s.id})" title="Xem hồ sơ chi tiết" 
              class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors flex items-center gap-1">
              <i data-lucide="user" class="w-3.5 h-3.5"></i>
              <span>Hồ sơ</span>
            </button>
            <button type="button" onclick="openSendFeedbackModal(${s.id}, ${activeTeacherClass.id}, '${escapeHtml(s.full_name)}', '${escapeHtml(activeTeacherClass.name)}')" title="Gửi phản hồi cho học sinh" 
              class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 transition-colors flex items-center gap-1">
              <i data-lucide="message-square-plus" class="w-3.5 h-3.5"></i>
              <span>Phản hồi</span>
            </button>
            <button type="button" onclick="openViolationModalForStudent(${activeTeacherClass.id}, ${s.id}, '${escapeHtml(s.full_name)}')" title="Lập biên bản vi phạm kỷ luật" 
              class="px-2 py-1 text-xs font-medium rounded-lg text-rose-600 hover:bg-rose-50 transition-colors">
              <i data-lucide="scale" class="w-3.5 h-3.5"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  // Mobile Cards
  mobileList.innerHTML = students.map((s, idx) => {
    return `
      <div class="p-3.5 bg-white rounded-xl border border-slate-200 space-y-2 mb-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-xs">${s.stt || (idx + 1)}</span>
            <button type="button" onclick="openStudentProfileModal(${s.id})" class="font-bold text-slate-900 text-sm hover:text-blue-600 text-left">
              ${escapeHtml(s.full_name)}
            </button>
          </div>
          <span class="font-mono text-xs font-bold text-slate-600">${escapeHtml(s.student_code)}</span>
        </div>
        <div class="flex items-center justify-between text-xs text-slate-500 pt-1 border-t border-slate-100">
          <span>${escapeHtml(s.gender_display || '')} • ${escapeHtml(s.date_of_birth || '')}</span>
          <span class="font-semibold text-blue-700">${s.feedback_count} phản hồi</span>
        </div>
        <div class="flex items-center justify-end gap-2 pt-2">
          <button type="button" onclick="openStudentProfileModal(${s.id})" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 text-slate-700">
            Hồ sơ
          </button>
          <button type="button" onclick="openSendFeedbackModal(${s.id}, ${activeTeacherClass.id}, '${escapeHtml(s.full_name)}', '${escapeHtml(activeTeacherClass.name)}')" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 text-white">
            Phản hồi
          </button>
        </div>
      </div>
    `;
  }).join('');

  if (window.lucide) lucide.createIcons();
}"""

new_render_stu_table = """function renderTeacherStudentsTable(students) {
  const tbody = document.getElementById('teacher-students-table-body');
  const mobileList = document.getElementById('teacher-students-mobile-list');
  const emptyState = document.getElementById('teacher-students-empty-state');

  if (!tbody || !mobileList) return;

  if (students.length === 0) {
    tbody.innerHTML = '';
    mobileList.innerHTML = '';
    if (emptyState) emptyState.classList.remove('hidden');
    return;
  }

  if (emptyState) emptyState.classList.add('hidden');

  const isStudent = currentUser && (currentUser.is_student || currentUser.role === 'HOC_SINH');
  const myStudentCode = (currentUser?.student_code || currentUser?.username || '').trim().toLowerCase();
  const myStudentId = currentUser?.student_profile?.id || currentUser?.student_id;

  // Desktop Table
  tbody.innerHTML = students.map((s, idx) => {
    const isStudying = s.status === 'STUDYING';
    const statusBadge = isStudying
      ? '<span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">Đang học</span>'
      : `<span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">${escapeHtml(s.status_display)}</span>`;

    const feedbackCountBadge = s.feedback_count > 0
      ? `<span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-700">${s.feedback_count}</span>`
      : `<span class="text-slate-400 text-xs">0</span>`;

    const isSelf = isStudent && ((s.student_code && s.student_code.trim().toLowerCase() === myStudentCode) || (s.id && s.id === myStudentId));

    let actionBtnsHtml = '';
    if (isStudent) {
      if (isSelf) {
        actionBtnsHtml = `
          <button type="button" onclick="openStudentProfileModal(${s.id})" title="Xem hồ sơ của tôi" 
            class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 transition-colors flex items-center gap-1">
            <i data-lucide="user" class="w-3.5 h-3.5"></i>
            <span>Hồ sơ của tôi</span>
          </button>
        `;
      } else {
        actionBtnsHtml = `<span class="text-xs text-slate-400 italic">Bạn cùng lớp</span>`;
      }
    } else {
      actionBtnsHtml = `
        <button type="button" onclick="openStudentProfileModal(${s.id})" title="Xem hồ sơ chi tiết" 
          class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors flex items-center gap-1">
          <i data-lucide="user" class="w-3.5 h-3.5"></i>
          <span>Hồ sơ</span>
        </button>
        <button type="button" onclick="openSendFeedbackModal(${s.id}, ${activeTeacherClass.id}, '${escapeHtml(s.full_name)}', '${escapeHtml(activeTeacherClass.name)}')" title="Gửi phản hồi cho học sinh" 
          class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 transition-colors flex items-center gap-1">
          <i data-lucide="message-square-plus" class="w-3.5 h-3.5"></i>
          <span>Phản hồi</span>
        </button>
        <button type="button" onclick="openViolationModalForStudent(${activeTeacherClass.id}, ${s.id}, '${escapeHtml(s.full_name)}')" title="Lập biên bản vi phạm kỷ luật" 
          class="px-2 py-1 text-xs font-medium rounded-lg text-rose-600 hover:bg-rose-50 transition-colors">
          <i data-lucide="scale" class="w-3.5 h-3.5"></i>
        </button>
      `;
    }

    const nameCellHtml = (isStudent && !isSelf)
      ? `<span class="font-bold text-slate-900">${escapeHtml(s.full_name)}</span>`
      : `
        <button type="button" onclick="openStudentProfileModal(${s.id})" class="font-bold text-slate-900 hover:text-blue-600 transition-colors text-left flex items-center gap-1.5 group">
          <span>${escapeHtml(s.full_name)}</span>
          <i data-lucide="external-link" class="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 text-blue-500 transition-opacity"></i>
        </button>
      `;

    return `
      <tr class="hover:bg-slate-50/80 transition-colors ${isSelf ? 'bg-blue-50/40' : ''}">
        <td class="py-3 px-4 text-center font-medium text-slate-500">${s.stt || (idx + 1)}</td>
        <td class="py-3 px-4 font-mono font-bold text-slate-700">${escapeHtml(s.student_code)}</td>
        <td class="py-3 px-4">
          ${nameCellHtml}
        </td>
        <td class="py-3 px-4 text-slate-600">${escapeHtml(s.gender_display || '')}</td>
        <td class="py-3 px-4 text-slate-600">${escapeHtml(s.date_of_birth || '')}</td>
        <td class="py-3 px-4 text-center">${statusBadge}</td>
        <td class="py-3 px-4 text-center">${feedbackCountBadge}</td>
        <td class="py-3 px-4 text-right">
          <div class="flex items-center justify-end gap-1.5">
            ${actionBtnsHtml}
          </div>
        </td>
      </tr>
    `;
  }).join('');

  // Mobile Cards
  mobileList.innerHTML = students.map((s, idx) => {
    const isSelf = isStudent && ((s.student_code && s.student_code.trim().toLowerCase() === myStudentCode) || (s.id && s.id === myStudentId));

    let mobileActionHtml = '';
    if (isStudent) {
      if (isSelf) {
        mobileActionHtml = `
          <button type="button" onclick="openStudentProfileModal(${s.id})" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 text-white">
            Hồ sơ của tôi
          </button>
        `;
      } else {
        mobileActionHtml = `<span class="text-xs text-slate-400 italic">Bạn cùng lớp</span>`;
      }
    } else {
      mobileActionHtml = `
        <button type="button" onclick="openStudentProfileModal(${s.id})" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 text-slate-700">
          Hồ sơ
        </button>
        <button type="button" onclick="openSendFeedbackModal(${s.id}, ${activeTeacherClass.id}, '${escapeHtml(s.full_name)}', '${escapeHtml(activeTeacherClass.name)}')" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 text-white">
          Phản hồi
        </button>
      `;
    }

    const mobileNameHtml = (isStudent && !isSelf)
      ? `<span class="font-bold text-slate-900 text-sm">${escapeHtml(s.full_name)}</span>`
      : `<button type="button" onclick="openStudentProfileModal(${s.id})" class="font-bold text-slate-900 text-sm hover:text-blue-600 text-left">${escapeHtml(s.full_name)}</button>`;

    return `
      <div class="p-3.5 bg-white rounded-xl border ${isSelf ? 'border-blue-300 ring-2 ring-blue-50 bg-blue-50/20' : 'border-slate-200'} space-y-2 mb-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-xs">${s.stt || (idx + 1)}</span>
            ${mobileNameHtml}
          </div>
          <span class="font-mono text-xs font-bold text-slate-600">${escapeHtml(s.student_code)}</span>
        </div>
        <div class="flex items-center justify-between text-xs text-slate-500 pt-1 border-t border-slate-100">
          <span>${escapeHtml(s.gender_display || '')} • ${escapeHtml(s.date_of_birth || '')}</span>
          <span class="font-semibold text-blue-700">${s.feedback_count} phản hồi</span>
        </div>
        <div class="flex items-center justify-end gap-2 pt-2">
          ${mobileActionHtml}
        </div>
      </div>
    `;
  }).join('');

  if (window.lucide) lucide.createIcons();
}"""

if old_render_stu_table in code_norm:
    code_norm = code_norm.replace(old_render_stu_table, new_render_stu_table)
    print("SUCCESS 6: Replaced renderTeacherStudentsTable with role-scoped roster view")
else:
    print("WARNING 6: old_render_stu_table not found")

# ==============================================================================
# 7. loadClassTeachers: Guard management actions for students
# ==============================================================================
old_load_teachers = """    // GVCN Card
    if (data.homeroom_teacher) {
      const ht = data.homeroom_teacher;
      if (gvcnName) gvcnName.textContent = ht.full_name || ht.username;
      if (gvcnDetails) {
        gvcnDetails.textContent = `Môn chuyên môn: ${ht.subject_display || ht.subject || 'Chưa phân môn'} • Email: ${ht.email || 'Chưa có'} • SĐT: ${ht.phone || 'Chưa có'}`;
      }
      if (gvcnStatus) {
        gvcnStatus.className = 'px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-100 text-emerald-700';
        gvcnStatus.textContent = 'Đang hoạt động';
      }
      if (revokeBtn) revokeBtn.classList.remove('hidden');

      if (activeTeacherClass && activeTeacherClass.id === targetId) {
        activeTeacherClass.homeroom_teacher_name = ht.full_name;
        activeTeacherClass.homeroom_teacher_id = ht.id;
      }
    } else {
      if (gvcnName) gvcnName.textContent = 'Chưa phân công GVCN';
      if (gvcnDetails) gvcnDetails.textContent = 'Lớp hiện chưa có giáo viên chủ nhiệm nhiệm kỳ này.';
      if (gvcnStatus) {
        gvcnStatus.className = 'px-2 py-0.5 text-[10px] font-bold rounded-full bg-amber-100 text-amber-700';
        gvcnStatus.textContent = 'Chưa phân công';
      }
      if (revokeBtn) revokeBtn.classList.add('hidden');

      if (activeTeacherClass && activeTeacherClass.id === targetId) {
        activeTeacherClass.homeroom_teacher_name = 'Chưa phân công';
        activeTeacherClass.homeroom_teacher_id = null;
      }
    }

    // Subject teachers table
    const subjectTeachers = data.subject_teachers || [];
    if (countBadge) countBadge.textContent = `${subjectTeachers.length} môn đã phân công`;
    if (tabBadge) tabBadge.textContent = `${(data.homeroom_teacher ? 1 : 0) + subjectTeachers.length}`;

    if (tbody) {
      if (subjectTeachers.length === 0) {
        tbody.innerHTML = '';
        if (emptyState) emptyState.classList.remove('hidden');
      } else {
        if (emptyState) emptyState.classList.add('hidden');
        tbody.innerHTML = subjectTeachers.map((st, idx) => {
          const formattedDate = st.assigned_at ? new Date(st.assigned_at).toLocaleDateString('vi-VN') : (st.start_date || '--');
          return `
            <tr class="hover:bg-slate-50/80 transition-colors">
              <td class="py-3 px-4 text-center font-bold text-slate-400">${idx + 1}</td>
              <td class="py-3 px-4">
                <span class="px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">
                  ${escapeHtml(st.subject_display || SUBJECT_MAP[st.subject] || st.subject)}
                </span>
              </td>
              <td class="py-3 px-4 font-semibold text-slate-800">
                ${escapeHtml(st.teacher_name || st.full_name || st.username)}
              </td>
              <td class="py-3 px-4 text-slate-500">${escapeHtml(st.email || st.teacher_email || '--')}</td>
              <td class="py-3 px-4 text-slate-500">${escapeHtml(st.phone || st.teacher_phone || '--')}</td>
              <td class="py-3 px-4 text-center text-slate-500">${formattedDate}</td>
              <td class="py-3 px-4 text-right">
                <button type="button" onclick="removeSubjectTeacher(${st.assignment_id})" class="px-2.5 py-1 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-lg transition" title="Thu hồi phân công môn ${escapeHtml(st.subject_display || st.subject)}">
                  Thu hồi
                </button>
              </td>
            </tr>
          `;
        }).join('');
      }
    }"""

new_load_teachers = """    const canManageTeachers = currentUser && (
      isAdminUser(currentUser) ||
      currentUser.role === 'BGH' || currentUser.is_bgh ||
      currentUser.role === 'DOAN_TRUONG' || currentUser.is_doan_truong
    );

    const btnAssignGvcn = document.getElementById('btn-pane-assign-gvcn');
    const btnAssignGvbm = document.getElementById('btn-pane-assign-gvbm');
    const btnChangeGvcn = document.getElementById('btn-pane-change-gvcn');
    const thActions = document.getElementById('th-subject-teachers-actions');
    if (btnAssignGvcn) btnAssignGvcn.classList.toggle('hidden', !canManageTeachers);
    if (btnAssignGvbm) btnAssignGvbm.classList.toggle('hidden', !canManageTeachers);
    if (btnChangeGvcn) btnChangeGvcn.classList.toggle('hidden', !canManageTeachers);
    if (thActions) thActions.textContent = canManageTeachers ? 'Thao tác' : 'Trạng thái';

    // GVCN Card
    if (data.homeroom_teacher) {
      const ht = data.homeroom_teacher;
      if (gvcnName) gvcnName.textContent = ht.full_name || ht.username;
      if (gvcnDetails) {
        gvcnDetails.textContent = `Môn chuyên môn: ${ht.subject_display || ht.subject || 'Chưa phân môn'} • Email: ${ht.email || 'Chưa có'} • SĐT: ${ht.phone || 'Chưa có'}`;
      }
      if (gvcnStatus) {
        gvcnStatus.className = 'px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-100 text-emerald-700';
        gvcnStatus.textContent = 'Đang hoạt động';
      }
      if (revokeBtn) revokeBtn.classList.toggle('hidden', !canManageTeachers);

      if (activeTeacherClass && activeTeacherClass.id === targetId) {
        activeTeacherClass.homeroom_teacher_name = ht.full_name;
        activeTeacherClass.homeroom_teacher_id = ht.id;
      }
    } else {
      if (gvcnName) gvcnName.textContent = 'Chưa phân công GVCN';
      if (gvcnDetails) gvcnDetails.textContent = 'Lớp hiện chưa có giáo viên chủ nhiệm nhiệm kỳ này.';
      if (gvcnStatus) {
        gvcnStatus.className = 'px-2 py-0.5 text-[10px] font-bold rounded-full bg-amber-100 text-amber-700';
        gvcnStatus.textContent = 'Chưa phân công';
      }
      if (revokeBtn) revokeBtn.classList.add('hidden');

      if (activeTeacherClass && activeTeacherClass.id === targetId) {
        activeTeacherClass.homeroom_teacher_name = 'Chưa phân công';
        activeTeacherClass.homeroom_teacher_id = null;
      }
    }

    // Subject teachers table
    const subjectTeachers = data.subject_teachers || [];
    if (countBadge) countBadge.textContent = `${subjectTeachers.length} môn đã phân công`;
    if (tabBadge) tabBadge.textContent = `${(data.homeroom_teacher ? 1 : 0) + subjectTeachers.length}`;

    if (tbody) {
      if (subjectTeachers.length === 0) {
        tbody.innerHTML = '';
        if (emptyState) emptyState.classList.remove('hidden');
      } else {
        if (emptyState) emptyState.classList.add('hidden');
        tbody.innerHTML = subjectTeachers.map((st, idx) => {
          const formattedDate = st.assigned_at ? new Date(st.assigned_at).toLocaleDateString('vi-VN') : (st.start_date || '--');
          const actionCell = canManageTeachers
            ? `<button type="button" onclick="removeSubjectTeacher(${st.assignment_id})" class="px-2.5 py-1 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-lg transition" title="Thu hồi phân công môn ${escapeHtml(st.subject_display || st.subject)}">Thu hồi</button>`
            : `<span class="text-xs text-slate-400 font-medium">Đang giảng dạy</span>`;
          return `
            <tr class="hover:bg-slate-50/80 transition-colors">
              <td class="py-3 px-4 text-center font-bold text-slate-400">${idx + 1}</td>
              <td class="py-3 px-4">
                <span class="px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">
                  ${escapeHtml(st.subject_display || SUBJECT_MAP[st.subject] || st.subject)}
                </span>
              </td>
              <td class="py-3 px-4 font-semibold text-slate-800">
                ${escapeHtml(st.teacher_name || st.full_name || st.username)}
              </td>
              <td class="py-3 px-4 text-slate-500">${escapeHtml(st.email || st.teacher_email || '--')}</td>
              <td class="py-3 px-4 text-slate-500">${escapeHtml(st.phone || st.teacher_phone || '--')}</td>
              <td class="py-3 px-4 text-center text-slate-500">${formattedDate}</td>
              <td class="py-3 px-4 text-right">
                ${actionCell}
              </td>
            </tr>
          `;
        }).join('');
      }
    }"""

if old_load_teachers in code_norm:
    code_norm = code_norm.replace(old_load_teachers, new_load_teachers)
    print("SUCCESS 7: Guarded teacher management actions for students in loadClassTeachers")
else:
    print("WARNING 7: old_load_teachers not found")

# ==============================================================================
# 8. openStudentProfileModal: Hide competition tab and quick feedback for students
# ==============================================================================
old_profile_modal = """    switchStudentProfileTab('general');

    openModal('modal-student-detail-profile');"""

new_profile_modal = """    const isStudentViewer = currentUser && (currentUser.is_student || currentUser.role === 'HOC_SINH');
    const compTab = document.getElementById('sp-tab-competition');
    if (compTab) compTab.classList.toggle('hidden', isStudentViewer);
    const compPane = document.getElementById('sp-pane-competition');
    if (compPane && isStudentViewer) compPane.classList.add('hidden');
    const quickFbBtn = document.getElementById('sp-quick-feedback-btn');
    if (quickFbBtn) quickFbBtn.classList.toggle('hidden', isStudentViewer);

    switchStudentProfileTab('general');

    openModal('modal-student-detail-profile');"""

if old_profile_modal in code_norm:
    code_norm = code_norm.replace(old_profile_modal, new_profile_modal)
    print("SUCCESS 8: Hid competition tab and quick feedback for students in openStudentProfileModal")
else:
    print("WARNING 8: old_profile_modal not found")

with open(app_js_path, "w", encoding="utf-8") as f:
    f.write(code_norm)

print("Finished applying updates to static/app.js!")
