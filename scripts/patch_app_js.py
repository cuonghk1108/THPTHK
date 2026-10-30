import os, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_JS_PATH = os.path.join(BASE_DIR, 'static', 'app.js')

print("Patching static/app.js...")
with open(APP_JS_PATH, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Update getAllowedTabs to grant 'conduct' to Lớp trưởng
target_allowed = """  } else if (user.is_student || user.role === 'HOC_SINH') {

    ['teacher-classes', 'counseling'].forEach(tab => allowed.add(tab));

  }"""

repl_allowed = """  } else if (user.is_student || user.role === 'HOC_SINH') {

    ['teacher-classes', 'counseling'].forEach(tab => allowed.add(tab));
    if (user.is_class_monitor || user.student_profile?.is_class_monitor) {
      allowed.add('conduct');
    }

  }"""

if target_allowed in js:
    js = js.replace(target_allowed, repl_allowed, 1)
    print("SUCCESS: Patched getAllowedTabs for Lớp trưởng")
else:
    print("WARNING: target_allowed not found in app.js")

# 2. Update getActionButtonForViolation
target_action_btn = """function getActionButtonForViolation(v) {

  const canVerify = currentUser && (currentUser.role === 'ADMIN' || currentUser.role === 'SUPER_ADMIN' || currentUser.role === 'DOAN_TRUONG' || currentUser.is_doan_truong || currentUser.can_verify_violations);

  const canAppeal = currentUser && (

    (currentUser.role === 'HOC_SINH' && v.student_name && v.student_name.includes(currentUser.full_name)) ||

    (currentUser.role === 'GVCN' && v.class_name === '10A1')

  );"""

repl_action_btn = """function getActionButtonForViolation(v) {

  const canVerify = currentUser && (currentUser.role === 'ADMIN' || currentUser.role === 'SUPER_ADMIN' || currentUser.role === 'DOAN_TRUONG' || currentUser.is_doan_truong || currentUser.can_verify_violations);

  const isStudent = currentUser && (currentUser.is_student || currentUser.role === 'HOC_SINH');
  const studentClassId = Number(currentUser?.school_class_id || currentUser?.student_class_info?.id || currentUser?.student_profile?.school_class_id || 0);
  const violationClassId = Number(v.school_class || v.class_id || 0);

  const isOwnerStudent = isStudent && (
    (currentUser.student_profile && v.student === currentUser.student_profile.id) ||
    (currentUser.student_id && v.student === currentUser.student_id) ||
    (currentUser.student_code && v.student_code === currentUser.student_code) ||
    (v.student_name && currentUser.full_name && v.student_name.trim() === currentUser.full_name.trim())
  );

  const isClassMonitor = isStudent && Boolean(currentUser.is_class_monitor || currentUser.student_profile?.is_class_monitor) && (
    !violationClassId || !studentClassId || violationClassId === studentClassId
  );

  const isHomeroom = Boolean(currentUser && (currentUser.is_gvcn || currentUser.role === 'GVCN'));
  const isAdminOrDoan = Boolean(currentUser && (currentUser.is_admin || currentUser.is_doan_truong || currentUser.role === 'ADMIN' || currentUser.role === 'DOAN_TRUONG'));

  const canAppeal = isOwnerStudent || isClassMonitor || isHomeroom || isAdminOrDoan;"""

if target_action_btn in js:
    js = js.replace(target_action_btn, repl_action_btn, 1)
    print("SUCCESS: Patched getActionButtonForViolation with Lớp trưởng & RBAC check")
else:
    print("WARNING: target_action_btn not found in app.js")

# 3. Update selectTeacherClass to set header monitor info
target_select_class = """  if (desc) {

    desc.textContent = `Sĩ số: ${found.student_count} học sinh • GVCN: ${found.homeroom_teacher_name || 'Chưa phân công'} • Năm học: ${found.academic_year_name}`;

  }"""

repl_select_class = """  if (desc) {

    desc.textContent = `Sĩ số: ${found.student_count} học sinh • GVCN: ${found.homeroom_teacher_name || 'Chưa phân công'} • Năm học: ${found.academic_year_name}`;

  }

  updateClassMonitorHeader(found.monitor_name, found.can_assign_monitor);"""

if target_select_class in js:
    js = js.replace(target_select_class, repl_select_class, 1)
    print("SUCCESS: Patched selectTeacherClass for monitor header update")
else:
    print("WARNING: target_select_class not found in app.js")

# 4. Update fetchClassStudents to receive monitor info & update header
target_fetch_students = """    const data = await res.json();

    teacherStudentsList = data.students || [];

    filterTeacherStudentsList();"""

repl_fetch_students = """    const data = await res.json();

    teacherStudentsList = data.students || [];
    if (activeTeacherClass && activeTeacherClass.id === classId) {
      activeTeacherClass.monitor_id = data.monitor_id;
      activeTeacherClass.monitor_name = data.monitor_name;
      activeTeacherClass.can_assign_monitor = data.can_assign_monitor;
    }
    updateClassMonitorHeader(data.monitor_name, data.can_assign_monitor);

    filterTeacherStudentsList();"""

if target_fetch_students in js:
    js = js.replace(target_fetch_students, repl_fetch_students, 1)
    print("SUCCESS: Patched fetchClassStudents for monitor data update")
else:
    print("WARNING: target_fetch_students not found in app.js")

# 5. Update renderTeacherStudentsTable with monitor badge & assign button
target_render_students = """    const isSelf = isStudent && ((s.student_code && s.student_code.trim().toLowerCase() === myStudentCode) || (s.id && s.id === myStudentId) || (s.user_id && s.user_id === currentUser?.id));

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
        <button type="button" onclick="openSendFeedbackModal(${s.id}, ${activeTeacherClass.id}, '${escapeHtml(s.full_name)}', '${escapeHtml(activeTeacherClass.name)}')" title="Nhận xét đích danh học sinh này"
          class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-colors flex items-center gap-1">
          <i data-lucide="message-square-plus" class="w-3.5 h-3.5"></i>
          <span>Nhận xét</span>
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
      `;"""

repl_render_students = """    const isSelf = isStudent && ((s.student_code && s.student_code.trim().toLowerCase() === myStudentCode) || (s.id && s.id === myStudentId) || (s.user_id && s.user_id === currentUser?.id));
    const isMonitor = Boolean(s.is_class_monitor || (activeTeacherClass && activeTeacherClass.monitor_id === s.id));
    const monitorBadge = isMonitor
      ? `<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 ml-1.5 shadow-2xs" title="Lớp trưởng"><i data-lucide="crown" class="w-3 h-3 text-amber-600"></i> Lớp trưởng</span>`
      : '';

    let monitorActionBtn = '';
    if (!isStudent && activeTeacherClass && activeTeacherClass.can_assign_monitor) {
      if (isMonitor) {
        monitorActionBtn = `
          <button type="button" onclick="confirmRemoveMonitor(${s.id}, '${escapeHtml(s.full_name)}')" title="Hủy vai trò Lớp trưởng"
            class="px-2 py-1 text-xs font-semibold rounded-lg text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 transition-colors flex items-center gap-1">
            <i data-lucide="crown" class="w-3.5 h-3.5 text-amber-600"></i>
            <span>Hủy LT</span>
          </button>
        `;
      } else {
        monitorActionBtn = `
          <button type="button" onclick="confirmAssignMonitor(${s.id}, '${escapeHtml(s.full_name)}')" title="Phân công làm Lớp trưởng"
            class="px-2 py-1 text-xs font-semibold rounded-lg text-slate-600 hover:text-amber-700 hover:bg-amber-50 border border-slate-200 hover:border-amber-200 transition-colors flex items-center gap-1">
            <i data-lucide="crown" class="w-3.5 h-3.5 text-amber-500"></i>
            <span>Phân LT</span>
          </button>
        `;
      }
    }

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
        ${monitorActionBtn}
        <button type="button" onclick="openSendFeedbackModal(${s.id}, ${activeTeacherClass.id}, '${escapeHtml(s.full_name)}', '${escapeHtml(activeTeacherClass.name)}')" title="Nhận xét đích danh học sinh này"
          class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-colors flex items-center gap-1">
          <i data-lucide="message-square-plus" class="w-3.5 h-3.5"></i>
          <span>Nhận xét</span>
        </button>
        <button type="button" onclick="openViolationModalForStudent(${activeTeacherClass.id}, ${s.id}, '${escapeHtml(s.full_name)}')" title="Lập biên bản vi phạm kỷ luật"
          class="px-2 py-1 text-xs font-medium rounded-lg text-rose-600 hover:bg-rose-50 transition-colors">
          <i data-lucide="scale" class="w-3.5 h-3.5"></i>
        </button>
      `;
    }

    const nameCellHtml = (isStudent && !isSelf)
      ? `<div class="flex items-center flex-wrap gap-1"><span class="font-bold text-slate-900">${escapeHtml(s.full_name)}</span>${monitorBadge}</div>`
      : `
        <div class="flex items-center flex-wrap gap-1">
          <button type="button" onclick="openStudentProfileModal(${s.id})" class="font-bold text-slate-900 hover:text-blue-600 transition-colors text-left flex items-center gap-1.5 group">
            <span>${escapeHtml(s.full_name)}</span>
            <i data-lucide="external-link" class="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 text-blue-500 transition-opacity"></i>
          </button>
          ${monitorBadge}
        </div>
      `;"""

if target_render_students in js:
    js = js.replace(target_render_students, repl_render_students, 1)
    print("SUCCESS: Patched renderTeacherStudentsTable with monitor badge & action button")
else:
    print("WARNING: target_render_students not found in app.js")

# 6. Append Class Monitor helper functions to the end of static/app.js
monitor_helpers_js = """

// =============================================================================
// CLASS MONITOR (LỚP TRƯỞNG) MANAGEMENT FUNCTIONS
// =============================================================================

function updateClassMonitorHeader(monitorName, canAssign) {
  const badge = document.getElementById('active-class-monitor-badge');
  const nameEl = document.getElementById('active-class-monitor-name');
  const btnHeader = document.getElementById('btn-assign-monitor-header');

  if (badge && nameEl) {
    if (monitorName) {
      nameEl.textContent = monitorName;
      badge.classList.remove('hidden');
    } else {
      nameEl.textContent = 'Chưa có';
      if (canAssign) {
        badge.classList.remove('hidden');
      } else {
        badge.classList.add('hidden');
      }
    }
  }

  if (btnHeader) {
    btnHeader.classList.toggle('hidden', !canAssign);
  }
}

function openAssignMonitorModal() {
  if (!activeTeacherClass) {
    showToast('Vui lòng chọn một lớp học trước.', 'warning');
    return;
  }

  const modal = document.getElementById('modal-assign-class-monitor');
  if (!modal) return;

  const subtitle = document.getElementById('modal-assign-monitor-class-subtitle');
  if (subtitle) subtitle.textContent = `Lớp ${activeTeacherClass.name}`;

  const classIdInput = document.getElementById('assign-monitor-class-id');
  if (classIdInput) classIdInput.value = activeTeacherClass.id;

  const currentNameEl = document.getElementById('assign-monitor-current-name');
  const unassignBtn = document.getElementById('btn-unassign-monitor-modal');

  if (currentNameEl) {
    currentNameEl.textContent = activeTeacherClass.monitor_name || 'Chưa phân công';
  }
  if (unassignBtn) {
    unassignBtn.classList.toggle('hidden', !activeTeacherClass.monitor_id);
  }

  // Populate student select dropdown
  const studentSelect = document.getElementById('assign-monitor-select-student');
  if (studentSelect) {
    let optHtml = '<option value="">-- Chọn học sinh trong lớp --</option>';
    teacherStudentsList.forEach((s, idx) => {
      const isCur = Boolean(s.is_class_monitor || (activeTeacherClass.monitor_id === s.id));
      optHtml += `<option value="${s.id}" ${isCur ? 'selected' : ''}>${s.stt || (idx + 1)}. [${escapeHtml(s.student_code)}] ${escapeHtml(s.full_name)} ${isCur ? '⭐ (Hiện là LT)' : ''}</option>`;
    });
    studentSelect.innerHTML = optHtml;
  }

  modal.classList.remove('hidden');
  lucide.createIcons();
}

async function handleAssignMonitorSubmit(e) {
  e.preventDefault();
  const classId = document.getElementById('assign-monitor-class-id')?.value || activeTeacherClass?.id;
  const studentId = document.getElementById('assign-monitor-select-student')?.value;

  if (!classId) {
    showToast('Không xác định được lớp học.', 'error');
    return;
  }
  if (!studentId) {
    showToast('Vui lòng chọn một học sinh để phân công làm Lớp trưởng.', 'warning');
    return;
  }

  await executeAssignMonitor(Number(classId), Number(studentId));
}

function confirmAssignMonitor(studentId, studentName) {
  if (!activeTeacherClass) return;
  if (!confirm(`Bạn có chắc chắn muốn phân công học sinh "${studentName}" làm Lớp trưởng của lớp ${activeTeacherClass.name}?`)) {
    return;
  }
  executeAssignMonitor(activeTeacherClass.id, studentId);
}

function confirmRemoveMonitor(studentId, studentName) {
  if (!activeTeacherClass) return;
  if (!confirm(`Bạn có chắc chắn muốn hủy vai trò Lớp trưởng của học sinh "${studentName}"?`)) {
    return;
  }
  executeAssignMonitor(activeTeacherClass.id, null);
}

function confirmRemoveMonitorFromModal() {
  if (!activeTeacherClass) return;
  if (!confirm(`Bạn có chắc chắn muốn hủy vai trò Lớp trưởng của lớp ${activeTeacherClass.name}?`)) {
    return;
  }
  closeModal('modal-assign-class-monitor');
  executeAssignMonitor(activeTeacherClass.id, null);
}

async function executeAssignMonitor(classId, studentId) {
  const submitBtn = document.getElementById('btn-submit-assign-monitor');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i><span>Đang xử lý...</span>';
    lucide.createIcons();
  }

  try {
    const res = await fetch(`/api/conduct/teacher-classes/${classId}/assign-monitor/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify({ student_id: studentId })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || 'Không thể thực hiện phân công Lớp trưởng.');
    }

    showToast(data.message || 'Cập nhật Lớp trưởng thành công!', 'success');
    closeModal('modal-assign-class-monitor');

    // Update activeTeacherClass state
    if (activeTeacherClass && activeTeacherClass.id === classId) {
      activeTeacherClass.monitor_id = data.monitor_id;
      activeTeacherClass.monitor_name = data.monitor_name;
    }

    // Update teacherStudentsList locally
    teacherStudentsList.forEach(s => {
      s.is_class_monitor = Boolean(studentId && s.id === Number(studentId));
    });

    // Refresh UI
    updateClassMonitorHeader(data.monitor_name, true);
    filterTeacherStudentsList();
    lucide.createIcons();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i data-lucide="check" class="w-3.5 h-3.5"></i><span>Lưu phân công</span>';
      lucide.createIcons();
    }
  }
}
"""

if "function updateClassMonitorHeader" not in js:
    js += monitor_helpers_js
    print("SUCCESS: Appended class monitor functions to static/app.js")
else:
    print("NOTE: updateClassMonitorHeader already present in static/app.js")

with open(APP_JS_PATH, 'w', encoding='utf-8') as f:
    f.write(js)

print("Patching app.js finished.")
