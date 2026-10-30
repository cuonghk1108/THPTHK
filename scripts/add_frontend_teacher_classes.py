# -*- coding: utf-8 -*-
import sys

JS_CODE = '''

// =====================================================================
// MODULE: QUẢN LÝ LỚP HỌC VÀ PHẢN HỒI HỌC SINH DÀNH CHO GIÁO VIÊN
// =====================================================================

let teacherAssignedClasses = [];
let activeTeacherClass = null;
let teacherStudentsList = [];
let teacherFeedbacksList = [];
let activeStudentProfileData = null;
let activeFeedbackDetailData = null;
let currentFeedbackScopeFilter = 'all';
let studentFilterDebounceTimer = null;

const FEEDBACK_TYPE_MAP = {
  ACADEMIC: { label: 'Kết quả học tập', badgeClass: 'bg-blue-50 text-blue-700 border border-blue-200' },
  ATTITUDE: { label: 'Thái độ học tập', badgeClass: 'bg-emerald-50 text-emerald-700 border border-emerald-200' },
  DISCIPLINE: { label: 'Nền nếp nội quy', badgeClass: 'bg-amber-50 text-amber-700 border border-amber-200' },
  ATTENDANCE: { label: 'Chuyên cần', badgeClass: 'bg-purple-50 text-purple-700 border border-purple-200' },
  PROGRESS: { label: 'Sự tiến bộ', badgeClass: 'bg-teal-50 text-teal-700 border border-teal-200' },
  IMPROVEMENT: { label: 'Điểm cần cải thiện', badgeClass: 'bg-rose-50 text-rose-700 border border-rose-200' },
  COOPERATION: { label: 'Đề xuất phối hợp', badgeClass: 'bg-indigo-50 text-indigo-700 border border-indigo-200' },
  OTHER: { label: 'Nội dung khác', badgeClass: 'bg-slate-100 text-slate-700 border border-slate-200' }
};

const FEEDBACK_STATUS_MAP = {
  SENT: { label: 'Đã gửi', badgeClass: 'bg-slate-100 text-slate-700 border border-slate-200' },
  SEEN: { label: 'Đã xem', badgeClass: 'bg-blue-50 text-blue-700 border border-blue-200' },
  PROCESSING: { label: 'Đang xử lý / Phối hợp', badgeClass: 'bg-amber-50 text-amber-700 border border-amber-200' },
  RESOLVED: { label: 'Đã giải quyết', badgeClass: 'bg-emerald-50 text-emerald-700 border border-emerald-200' }
};

async function loadTeacherClassesModule(force = false) {
  try {
    const roleBadgeText = document.getElementById('teacher-role-badge-text');
    if (roleBadgeText && currentUser) {
      if (isAdminUser(currentUser)) {
        roleBadgeText.textContent = 'Quản trị viên / Ban Giám hiệu';
      } else if (currentUser.role === 'GVCN' || currentUser.is_gvcn) {
        roleBadgeText.textContent = 'Giáo viên chủ nhiệm (GVCN)';
      } else if (currentUser.role === 'GVBM' || currentUser.is_gvbm) {
        roleBadgeText.textContent = 'Giáo viên bộ môn (GVBM)';
      } else {
        roleBadgeText.textContent = currentUser.role_display || 'Cán bộ giáo viên';
      }
    }

    const res = await fetch('/api/conduct/teacher-classes/', {
      headers: { 'Accept': 'application/json' }
    });
    if (!res.ok) throw new Error('Không thể tải danh sách lớp phân công.');

    teacherAssignedClasses = await res.json();
    const countBadge = document.getElementById('teacher-classes-count-badge');
    if (countBadge) countBadge.textContent = `${teacherAssignedClasses.length} lớp`;

    renderTeacherClassesBar();

    if (teacherAssignedClasses.length > 0) {
      const targetClass = (activeTeacherClass && teacherAssignedClasses.some(c => c.id === activeTeacherClass.id))
        ? activeTeacherClass
        : teacherAssignedClasses[0];
      selectTeacherClass(targetClass.id);
    } else {
      const container = document.getElementById('teacher-active-class-container');
      if (container) {
        container.innerHTML = `
          <div class="bg-white rounded-2xl p-12 text-center border border-slate-200">
            <div class="w-16 h-16 rounded-2xl bg-amber-50 text-amber-600 mx-auto flex items-center justify-center mb-4">
              <i data-lucide="alert-circle" class="w-8 h-8"></i>
            </div>
            <h3 class="text-base font-bold text-slate-800">Chưa có phân công lớp học</h3>
            <p class="text-xs text-slate-500 mt-1 max-w-md mx-auto leading-relaxed">
              Tài khoản hiện chưa được phân công làm giáo viên chủ nhiệm hoặc giáo viên bộ môn cho lớp nào trong năm học hiện tại. Vui lòng liên hệ Ban Giám hiệu hoặc Quản trị viên để kiểm tra lịch phân công.
            </p>
          </div>
        `;
        if (window.lucide) lucide.createIcons();
      }
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderTeacherClassesBar() {
  const bar = document.getElementById('teacher-assigned-classes-bar');
  if (!bar) return;

  if (teacherAssignedClasses.length === 0) {
    bar.innerHTML = '<span class="text-xs text-slate-400 italic">Chưa có lớp nào được phân công.</span>';
    return;
  }

  bar.innerHTML = teacherAssignedClasses.map(c => {
    const isSelected = activeTeacherClass && activeTeacherClass.id === c.id;
    const isGVCN = c.assignment_role === 'GVCN';
    const rolePill = isGVCN 
      ? '<span class="px-1.5 py-0.5 text-[10px] font-bold rounded bg-blue-100 text-blue-800">CN</span>'
      : `<span class="px-1.5 py-0.5 text-[10px] font-bold rounded bg-emerald-100 text-emerald-800">${escapeHtml(c.subjects.join(', ') || 'BM')}</span>`;

    return `
      <button type="button" onclick="selectTeacherClass(${c.id})" 
        class="group px-3.5 py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 border shadow-sm ${
          isSelected 
            ? 'bg-blue-600 text-white border-blue-600 ring-2 ring-blue-600/30' 
            : 'bg-white text-slate-700 border-slate-200 hover:border-blue-400 hover:bg-blue-50/50'
        }">
        <span class="w-6 h-6 rounded-lg ${isSelected ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-700'} flex items-center justify-center font-bold text-[11px]">
          ${escapeHtml(c.name.substring(0, 3))}
        </span>
        <span class="font-bold text-sm">${escapeHtml(c.name)}</span>
        ${rolePill}
        <span class="text-[11px] ${isSelected ? 'text-blue-100' : 'text-slate-400'}">(${c.student_count} HS)</span>
      </button>
    `;
  }).join('');
}

async function selectTeacherClass(classId) {
  const found = teacherAssignedClasses.find(c => c.id === classId);
  if (!found) return;
  activeTeacherClass = found;

  renderTeacherClassesBar();

  // Update header info
  const avatar = document.getElementById('active-class-avatar');
  const title = document.getElementById('active-class-title');
  const roleTag = document.getElementById('active-class-role-tag');
  const desc = document.getElementById('active-class-desc');

  if (avatar) avatar.textContent = found.name;
  if (title) title.textContent = `Lớp ${found.name}`;
  if (roleTag) {
    roleTag.textContent = found.assignment_role_display;
    roleTag.className = `px-2 py-0.5 text-[11px] font-semibold rounded ${
      found.assignment_role === 'GVCN' ? 'bg-blue-100 text-blue-800' : 'bg-emerald-100 text-emerald-800'
    }`;
  }
  if (desc) {
    desc.textContent = `Sĩ số: ${found.student_count} học sinh • GVCN: ${found.homeroom_teacher_name || 'Chưa phân công'} • Năm học: ${found.academic_year_name}`;
  }

  // Load students and feedbacks concurrently
  await Promise.all([
    fetchClassStudents(found.id),
    fetchClassFeedbacks(found.id)
  ]);
}

async function fetchClassStudents(classId) {
  try {
    const res = await fetch(`/api/conduct/teacher-classes/${classId}/students/`);
    if (!res.ok) throw new Error('Không thể tải danh sách học sinh của lớp này.');
    const data = await res.json();
    teacherStudentsList = data.students || [];
    filterTeacherStudentsList();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function fetchClassFeedbacks(classId) {
  try {
    const res = await fetch(`/api/conduct/feedbacks/?class_id=${classId}`);
    if (!res.ok) throw new Error('Không thể tải lịch sử phản hồi.');
    teacherFeedbacksList = await res.json();
    
    // Update count badge
    const badge = document.getElementById('class-feedback-count-badge');
    if (badge) badge.textContent = teacherFeedbacksList.length;

    renderTeacherFeedbacks();
  } catch (err) {
    console.error('Error fetching feedbacks:', err);
  }
}

function debounceTeacherStudentFilter() {
  clearTimeout(studentFilterDebounceTimer);
  studentFilterDebounceTimer = setTimeout(() => {
    filterTeacherStudentsList();
  }, 200);
}

function removeAccents(str) {
  if (!str) return '';
  return str.normalize('NFD')
    .replace(/[\\u0300-\\u036f]/g, '')
    .replace(/[đĐ]/g, m => m === 'đ' ? 'd' : 'D')
    .toLowerCase();
}

function filterTeacherStudentsList() {
  const searchInput = document.getElementById('teacher-student-search-input');
  const statusFilter = document.getElementById('teacher-student-status-filter');
  const query = (searchInput?.value || '').trim();
  const queryNorm = removeAccents(query);
  const statusVal = statusFilter?.value || '';

  const filtered = teacherStudentsList.filter(s => {
    if (statusVal && s.status !== statusVal) return false;
    if (query) {
      const codeMatch = s.student_code.toLowerCase().includes(query.toLowerCase());
      const nameMatch = s.full_name.toLowerCase().includes(query.toLowerCase()) || removeAccents(s.full_name).includes(queryNorm);
      if (!codeMatch && !nameMatch) return false;
    }
    return true;
  });

  const counter = document.getElementById('filtered-students-counter');
  if (counter) counter.textContent = `Hiển thị ${filtered.length} / ${teacherStudentsList.length} học sinh`;

  renderTeacherStudentsTable(filtered);
}

function renderTeacherStudentsTable(students) {
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
}

function switchTeacherSubTab(tabName) {
  const btnRoster = document.getElementById('subtab-btn-roster');
  const btnFeedbacks = document.getElementById('subtab-btn-feedbacks');
  const paneRoster = document.getElementById('subtab-pane-roster');
  const paneFeedbacks = document.getElementById('subtab-pane-feedbacks');

  if (tabName === 'roster') {
    if (btnRoster) {
      btnRoster.className = 'px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-white text-slate-900 shadow-sm transition-all flex items-center gap-1.5';
    }
    if (btnFeedbacks) {
      btnFeedbacks.className = 'px-3.5 py-1.5 text-xs font-semibold rounded-lg text-slate-600 hover:text-slate-900 transition-all flex items-center gap-1.5';
    }
    if (paneRoster) paneRoster.classList.remove('hidden');
    if (paneFeedbacks) paneFeedbacks.classList.add('hidden');
  } else {
    if (btnRoster) {
      btnRoster.className = 'px-3.5 py-1.5 text-xs font-semibold rounded-lg text-slate-600 hover:text-slate-900 transition-all flex items-center gap-1.5';
    }
    if (btnFeedbacks) {
      btnFeedbacks.className = 'px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-white text-slate-900 shadow-sm transition-all flex items-center gap-1.5';
    }
    if (paneRoster) paneRoster.classList.add('hidden');
    if (paneFeedbacks) paneFeedbacks.classList.remove('hidden');
    renderTeacherFeedbacks();
  }

  if (window.lucide) lucide.createIcons();
}

function filterFeedbacksScope(scope) {
  currentFeedbackScopeFilter = scope;
  ['all', 'my', 'attention'].forEach(id => {
    const btn = document.getElementById(`fb-filter-${id}`);
    if (btn) {
      const isTarget = (scope === 'all' && id === 'all') || (scope === 'my_sent' && id === 'my') || (scope === 'attention' && id === 'attention');
      btn.className = isTarget
        ? 'px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-50 text-blue-700 border border-blue-200 transition-colors'
        : 'px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors';
    }
  });
  renderTeacherFeedbacks();
}

function applyFeedbackFilters() {
  renderTeacherFeedbacks();
}

function renderTeacherFeedbacks() {
  const container = document.getElementById('teacher-feedbacks-container');
  const emptyState = document.getElementById('teacher-feedbacks-empty-state');
  const typeFilter = document.getElementById('teacher-feedback-type-filter');
  const selectedType = typeFilter?.value || '';

  if (!container) return;

  let filtered = [...teacherFeedbacksList];

  // Scope filter
  if (currentFeedbackScopeFilter === 'my_sent') {
    filtered = filtered.filter(f => f.teacher === currentUser.id || f.teacher_username === currentUser.username);
  } else if (currentFeedbackScopeFilter === 'attention') {
    filtered = filtered.filter(f => f.priority === 'ATTENTION' || f.priority === 'URGENT' || f.status === 'PROCESSING');
  }

  // Type filter
  if (selectedType) {
    filtered = filtered.filter(f => f.feedback_type === selectedType);
  }

  if (filtered.length === 0) {
    container.innerHTML = '';
    if (emptyState) emptyState.classList.remove('hidden');
    return;
  }

  if (emptyState) emptyState.classList.add('hidden');

  container.innerHTML = filtered.map(f => {
    const typeInfo = FEEDBACK_TYPE_MAP[f.feedback_type] || { label: f.feedback_type_display || 'Phản hồi', badgeClass: 'bg-slate-100 text-slate-700' };
    const statusInfo = FEEDBACK_STATUS_MAP[f.status] || { label: f.status_display || 'Đã gửi', badgeClass: 'bg-slate-100 text-slate-700' };
    const isAttention = f.priority === 'ATTENTION' || f.priority === 'URGENT';
    const dateStr = f.created_at ? new Date(f.created_at).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';

    return `
      <div class="bg-white rounded-2xl p-4 shadow-sm border border-slate-200 hover:border-blue-300 transition-all space-y-3 cursor-pointer" onclick="openFeedbackDetailModal(${f.id})">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
          <div class="flex items-center gap-2">
            <span class="font-mono text-xs font-bold text-slate-500">${escapeHtml(f.feedback_code)}</span>
            <span class="font-bold text-slate-900">${escapeHtml(f.student_name)}</span>
            <span class="text-xs text-slate-500">(${escapeHtml(f.class_name)})</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold ${statusInfo.badgeClass}">${statusInfo.label}</span>
            <span class="text-xs text-slate-400 font-medium">${dateStr}</span>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <span class="px-2 py-0.5 rounded-md text-[11px] font-semibold ${typeInfo.badgeClass}">${typeInfo.label}</span>
          ${isAttention ? '<span class="px-2 py-0.5 rounded-md text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1"><i data-lucide="alert-triangle" class="w-3 h-3"></i> Cần quan tâm</span>' : ''}
          ${f.subject ? `<span class="px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 text-slate-700">Môn ${escapeHtml(f.subject)}</span>` : ''}
          <span class="text-xs text-slate-500 ml-auto">Người gửi: <strong class="text-slate-800">${escapeHtml(f.teacher_name || f.teacher_username)}</strong> (${escapeHtml(f.teacher_role)})</span>
        </div>

        <p class="text-xs md:text-sm text-slate-700 leading-relaxed line-clamp-2">${escapeHtml(f.content)}</p>

        <div class="flex items-center justify-between pt-1 text-xs">
          <div class="flex items-center gap-1.5 text-blue-600 font-medium">
            <i data-lucide="message-square" class="w-3.5 h-3.5"></i>
            <span>${f.replies_count || (f.replies ? f.replies.length : 0)} trao đổi phối hợp</span>
          </div>
          <span class="text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1">
            <span>Chi tiết & Trả lời</span>
            <i data-lucide="chevron-right" class="w-3.5 h-3.5"></i>
          </span>
        </div>
      </div>
    `;
  }).join('');

  if (window.lucide) lucide.createIcons();
}

// ---------------------------------------------------------------------
// MODAL: GỬI PHẢN HỒI HỌC SINH
// ---------------------------------------------------------------------

function openSendFeedbackModal(studentId, classId, studentName, className) {
  const form = document.getElementById('form-send-student-feedback');
  if (form) form.reset();

  document.getElementById('fb-form-student-id').value = studentId;
  document.getElementById('fb-form-class-id').value = classId;
  document.getElementById('fb-form-student-name').textContent = studentName;
  document.getElementById('fb-form-class-name').textContent = className;

  // Auto fill subject for GVBM if applicable
  const subjectInput = document.getElementById('fb-form-subject');
  if (subjectInput && activeTeacherClass && activeTeacherClass.assignment_role === 'GVBM' && activeTeacherClass.subjects.length > 0) {
    subjectInput.value = activeTeacherClass.subjects[0];
  } else if (subjectInput) {
    subjectInput.value = '';
  }

  updateFbCharCount();
  const errorEl = document.getElementById('fb-form-content-error');
  if (errorEl) errorEl.classList.add('hidden');

  openModal('modal-send-student-feedback');
  if (window.lucide) lucide.createIcons();
}

function insertFeedbackStarter(text) {
  const textarea = document.getElementById('fb-form-content');
  if (!textarea) return;
  if (textarea.value.trim().length > 0) {
    textarea.value += ' ' + text;
  } else {
    textarea.value = text;
  }
  updateFbCharCount();
  textarea.focus();
}

function updateFbCharCount() {
  const textarea = document.getElementById('fb-form-content');
  const counter = document.getElementById('fb-char-counter');
  if (!textarea || !counter) return;
  const len = textarea.value.length;
  counter.textContent = `${len}/1000 ký tự`;
  if (len >= 950) {
    counter.className = 'text-[11px] text-rose-500 font-mono font-bold';
  } else {
    counter.className = 'text-[11px] text-slate-400 font-mono';
  }
}

async function handleSendFeedbackSubmit(event) {
  event.preventDefault();
  const submitBtn = document.getElementById('fb-submit-btn');
  const btnText = document.getElementById('fb-submit-btn-text');
  const errorEl = document.getElementById('fb-form-content-error');

  const studentId = document.getElementById('fb-form-student-id').value;
  const classId = document.getElementById('fb-form-class-id').value;
  const content = document.getElementById('fb-form-content').value.trim();
  const feedbackType = document.getElementById('fb-form-type').value;
  const priority = document.getElementById('fb-form-priority').value;
  const visibilityScope = document.getElementById('fb-form-scope').value;
  const subject = document.getElementById('fb-form-subject').value.trim();
  const strengths = document.getElementById('fb-form-strengths')?.value?.trim() || '';
  const weaknesses = document.getElementById('fb-form-weaknesses')?.value?.trim() || '';
  const cooperationProposal = document.getElementById('fb-form-cooperation')?.value?.trim() || '';

  if (!content) {
    if (errorEl) {
      errorEl.textContent = 'Vui lòng nhập nội dung phản hồi.';
      errorEl.classList.remove('hidden');
    }
    return;
  }

  try {
    if (submitBtn) submitBtn.disabled = true;
    if (btnText) btnText.textContent = 'Đang gửi...';

    const payload = {
      student_id: parseInt(studentId, 10),
      class_id: parseInt(classId, 10),
      content,
      feedback_type: feedbackType,
      priority,
      visibility_scope: visibilityScope,
      subject,
      strengths,
      weaknesses,
      cooperation_proposal: cooperationProposal
    };

    const res = await fetch('/api/conduct/feedbacks/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || 'Lỗi khi gửi phản hồi.');
    }

    showToast('Đã gửi phản hồi giáo dục thành công!', 'success');
    closeModal('modal-send-student-feedback');

    // Refresh class feedbacks and students list
    if (activeTeacherClass) {
      await Promise.all([
        fetchClassFeedbacks(activeTeacherClass.id),
        fetchClassStudents(activeTeacherClass.id)
      ]);
    }
  } catch (err) {
    if (errorEl) {
      errorEl.textContent = err.message;
      errorEl.classList.remove('hidden');
    }
    showToast(err.message, 'error');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
    if (btnText) btnText.textContent = 'Gửi phản hồi';
  }
}

// ---------------------------------------------------------------------
// MODAL: HỒ SƠ CHI TIẾT HỌC SINH (4 TABS)
// ---------------------------------------------------------------------

async function openStudentProfileModal(studentId) {
  try {
    const res = await fetch(`/api/conduct/students/${studentId}/profile-detail/`);
    if (!res.ok) throw new Error('Không thể tải hồ sơ chi tiết học sinh.');
    activeStudentProfileData = await res.json();

    const g = activeStudentProfileData.general;
    document.getElementById('student-modal-name').textContent = g.full_name;
    document.getElementById('student-modal-code').textContent = g.student_code;
    document.getElementById('student-modal-sub').textContent = `Lớp ${g.school_class_name} • Phòng: ${g.room_number || 'N/A'} • GVCN: ${g.homeroom_teacher_name}`;
    
    const avatar = document.getElementById('student-modal-avatar');
    if (avatar) {
      const parts = g.full_name.trim().split(' ');
      avatar.textContent = parts.length > 1 ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase() : g.full_name.substring(0, 2).toUpperCase();
    }

    // Tab 1: General Info Grid
    const generalGrid = document.getElementById('sp-general-info-grid');
    if (generalGrid) {
      generalGrid.innerHTML = `
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">
          <span class="text-slate-400 block text-[11px] font-semibold uppercase">Mã học sinh</span>
          <span class="font-bold text-slate-800 text-sm font-mono">${escapeHtml(g.student_code)}</span>
        </div>
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">
          <span class="text-slate-400 block text-[11px] font-semibold uppercase">Lớp học & Khối</span>
          <span class="font-bold text-slate-800 text-sm">Lớp ${escapeHtml(g.school_class_name)} (Khối ${g.grade})</span>
        </div>
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">
          <span class="text-slate-400 block text-[11px] font-semibold uppercase">Ngày sinh</span>
          <span class="font-bold text-slate-800 text-sm">${escapeHtml(g.date_of_birth || 'Chưa cập nhật')}</span>
        </div>
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">
          <span class="text-slate-400 block text-[11px] font-semibold uppercase">Giới tính</span>
          <span class="font-bold text-slate-800 text-sm">${escapeHtml(g.gender_display)}</span>
        </div>
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">
          <span class="text-slate-400 block text-[11px] font-semibold uppercase">Trạng thái học tập</span>
          <span class="font-bold text-emerald-700 text-sm">${escapeHtml(g.status_display)}</span>
        </div>
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">
          <span class="text-slate-400 block text-[11px] font-semibold uppercase">Đoàn viên / Sao đỏ</span>
          <span class="font-bold text-slate-800 text-sm">
            ${g.is_union_member ? 'Đoàn viên TNCS' : 'Chưa kết nạp'} • ${g.is_red_star ? 'Đội viên Sao đỏ' : 'Không thuộc Sao đỏ'}
          </span>
        </div>
      `;
    }

    // Tab 2: Feedbacks
    const feedbacks = activeStudentProfileData.feedbacks || [];
    const feedbackBadge = document.getElementById('sp-feedback-badge');
    if (feedbackBadge) feedbackBadge.textContent = feedbacks.length;
    const fbList = document.getElementById('sp-feedback-list');
    if (fbList) {
      if (feedbacks.length === 0) {
        fbList.innerHTML = '<p class="text-xs text-slate-400 italic text-center p-6">Chưa có phản hồi nào được ghi nhận cho học sinh này.</p>';
      } else {
        fbList.innerHTML = feedbacks.map(f => `
          <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1.5">
            <div class="flex items-center justify-between text-xs">
              <span class="font-bold text-slate-900">${escapeHtml(f.feedback_type_display)}</span>
              <span class="text-slate-400">${new Date(f.created_at).toLocaleDateString('vi-VN')}</span>
            </div>
            <p class="text-xs text-slate-700 leading-relaxed">${escapeHtml(f.content)}</p>
            <div class="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-200/50">
              <span>Người gửi: <strong>${escapeHtml(f.teacher_name)}</strong> (${escapeHtml(f.teacher_role)})</span>
              <span class="font-semibold text-blue-700">${f.status_display}</span>
            </div>
          </div>
        `).join('');
      }
    }

    // Tab 3: Violations (Read-only)
    const violations = activeStudentProfileData.violations || [];
    const violTable = document.getElementById('sp-violations-table-body');
    if (violTable) {
      if (violations.length === 0) {
        violTable.innerHTML = '<tr><td colspan="4" class="p-4 text-center text-slate-400 text-xs italic">Học sinh không có vi phạm nào được ghi nhận. Tinh thần nền nếp rất tốt!</td></tr>';
      } else {
        violTable.innerHTML = violations.map(v => `
          <tr class="hover:bg-slate-50">
            <td class="p-3 text-slate-600 font-medium">${escapeHtml(v.occurred_at)}</td>
            <td class="p-3">
              <span class="font-bold text-slate-800 block">${escapeHtml(v.rule_name)}</span>
              <span class="text-[11px] text-slate-400">${escapeHtml(v.location || 'Khuôn viên trường')}</span>
            </td>
            <td class="p-3 text-center font-bold text-rose-600">-${v.points_deducted}đ</td>
            <td class="p-3 text-center">
              <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">${escapeHtml(v.status_display)}</span>
            </td>
          </tr>
        `).join('');
      }
    }

    // Tab 4: Competition Summary
    const comp = activeStudentProfileData.competition || {};
    const compGrid = document.getElementById('sp-competition-summary');
    if (compGrid) {
      compGrid.innerHTML = `
        <div class="p-4 bg-blue-50 border border-blue-200 rounded-xl text-center">
          <span class="text-blue-600 text-xs font-bold uppercase block mb-1">Lớp học</span>
          <span class="text-xl font-bold text-blue-900">${escapeHtml(comp.class_name || '')}</span>
        </div>
        <div class="p-4 bg-amber-50 border border-amber-200 rounded-xl text-center">
          <span class="text-amber-600 text-xs font-bold uppercase block mb-1">Tổng vụ vi phạm</span>
          <span class="text-xl font-bold text-amber-900">${comp.total_violations_count || 0}</span>
        </div>
        <div class="p-4 bg-rose-50 border border-rose-200 rounded-xl text-center">
          <span class="text-rose-600 text-xs font-bold uppercase block mb-1">Điểm trừ nền nếp</span>
          <span class="text-xl font-bold text-rose-900">-${comp.total_points_deducted || 0}đ</span>
        </div>
      `;
    }

    switchStudentProfileTab('general');
    openModal('modal-student-detail-profile');
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function switchStudentProfileTab(tabName) {
  const tabs = ['general', 'feedback', 'violations', 'competition'];
  tabs.forEach(t => {
    const btn = document.getElementById(`sp-tab-${t}`);
    const pane = document.getElementById(`sp-pane-${t}`);
    if (t === tabName) {
      if (btn) btn.className = 'px-3.5 py-3 text-xs font-semibold text-blue-600 border-b-2 border-blue-600 flex items-center gap-1.5 whitespace-nowrap';
      if (pane) pane.classList.remove('hidden');
    } else {
      if (btn) btn.className = 'px-3.5 py-3 text-xs font-semibold text-slate-600 hover:text-slate-900 border-b-2 border-transparent flex items-center gap-1.5 whitespace-nowrap';
      if (pane) pane.classList.add('hidden');
    }
  });
}

function triggerFeedbackFromProfileModal() {
  if (!activeStudentProfileData || !activeStudentProfileData.general) return;
  const g = activeStudentProfileData.general;
  closeModal('modal-student-detail-profile');
  openSendFeedbackModal(g.id, g.school_class_id, g.full_name, g.school_class_name);
}

// ---------------------------------------------------------------------
// MODAL: CHI TIẾT PHẢN HỒI & TRAO ĐỔI PHỐI HỢP
// ---------------------------------------------------------------------

async function openFeedbackDetailModal(feedbackId) {
  try {
    // Automatically trigger mark-seen
    fetch(`/api/conduct/feedbacks/${feedbackId}/mark-seen/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') || '' }
    }).catch(console.error);

    const res = await fetch(`/api/conduct/feedbacks/${feedbackId}/`);
    if (!res.ok) throw new Error('Không thể tải chi tiết phản hồi.');
    activeFeedbackDetailData = await res.json();
    const f = activeFeedbackDetailData;

    document.getElementById('fd-modal-code').textContent = f.feedback_code;
    const statusInfo = FEEDBACK_STATUS_MAP[f.status] || { label: f.status_display, badgeClass: 'bg-slate-100 text-slate-700' };
    const statusBadge = document.getElementById('fd-modal-status-badge');
    if (statusBadge) {
      statusBadge.textContent = statusInfo.label;
      statusBadge.className = `px-2 py-0.5 text-[10px] font-bold rounded-full ${statusInfo.badgeClass}`;
    }

    document.getElementById('fd-modal-time').textContent = f.created_at ? new Date(f.created_at).toLocaleString('vi-VN') : '';
    document.getElementById('fd-modal-student').textContent = f.student_name;
    document.getElementById('fd-modal-class').textContent = `Lớp ${f.class_name}`;
    document.getElementById('fd-modal-author').textContent = `${f.teacher_name || f.teacher_username} (${f.teacher_role})`;
    document.getElementById('fd-modal-type-badge').textContent = f.feedback_type_display;
    document.getElementById('fd-modal-priority-badge').textContent = f.priority_display;
    document.getElementById('fd-modal-scope-badge').textContent = f.visibility_scope_display;
    document.getElementById('fd-modal-content').textContent = f.content;

    // Extra fields
    const extraContainer = document.getElementById('fd-modal-extra-container');
    if (extraContainer) {
      const hasExtra = f.strengths || f.weaknesses || f.cooperation_proposal;
      if (hasExtra) {
        extraContainer.classList.remove('hidden');
        extraContainer.innerHTML = `
          ${f.strengths ? `<div class="p-2.5 bg-emerald-50 text-emerald-900 rounded-lg text-xs"><strong>Điểm mạnh:</strong> ${escapeHtml(f.strengths)}</div>` : ''}
          ${f.weaknesses ? `<div class="p-2.5 bg-amber-50 text-amber-900 rounded-lg text-xs"><strong>Cần cải thiện:</strong> ${escapeHtml(f.weaknesses)}</div>` : ''}
          ${f.cooperation_proposal ? `<div class="p-2.5 bg-blue-50 text-blue-900 rounded-lg text-xs"><strong>Đề xuất phối hợp:</strong> ${escapeHtml(f.cooperation_proposal)}</div>` : ''}
        `;
      } else {
        extraContainer.classList.add('hidden');
      }
    }

    // Discussion Replies List
    renderFeedbackRepliesList(f.replies || []);

    // Status select
    const statusSelect = document.getElementById('fd-status-select');
    if (statusSelect) statusSelect.value = f.status;

    openModal('modal-feedback-detail-reply');
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderFeedbackRepliesList(replies) {
  const container = document.getElementById('fd-modal-replies-list');
  const countEl = document.getElementById('fd-modal-replies-count');
  if (countEl) countEl.textContent = replies.length;
  if (!container) return;

  if (replies.length === 0) {
    container.innerHTML = '<p class="text-xs text-slate-400 italic py-2">Chưa có trao đổi nào. Nhập tin nhắn phía dưới để gửi trao đổi cho đồng nghiệp.</p>';
    return;
  }

  container.innerHTML = replies.map(r => {
    const isMe = currentUser && (r.author === currentUser.id || r.author_username === currentUser.username);
    const timeStr = r.created_at ? new Date(r.created_at).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '';

    return `
      <div class="p-3 rounded-xl text-xs space-y-1 ${isMe ? 'bg-blue-50 border border-blue-200 ml-4' : 'bg-slate-50 border border-slate-200 mr-4'}">
        <div class="flex items-center justify-between font-semibold">
          <span class="${isMe ? 'text-blue-800' : 'text-slate-800'}">${escapeHtml(r.author_name || r.author_username)} (${escapeHtml(r.author_role)})</span>
          <span class="text-[11px] text-slate-400 font-normal">${timeStr}</span>
        </div>
        <p class="text-slate-700 leading-relaxed whitespace-pre-wrap">${escapeHtml(r.content)}</p>
      </div>
    `;
  }).join('');
}

async function handleSubmitFeedbackReply() {
  if (!activeFeedbackDetailData) return;
  const input = document.getElementById('fd-reply-input');
  const submitBtn = document.getElementById('fd-reply-submit-btn');
  const content = (input?.value || '').trim();

  if (!content) {
    showToast('Vui lòng nhập nội dung trao đổi.', 'warning');
    return;
  }

  try {
    if (submitBtn) submitBtn.disabled = true;
    const res = await fetch(`/api/conduct/feedbacks/${activeFeedbackDetailData.id}/reply/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify({ content })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Lỗi khi gửi trao đổi.');

    activeFeedbackDetailData = data;
    input.value = '';
    renderFeedbackRepliesList(data.replies || []);

    // Update status badge to processing
    const statusInfo = FEEDBACK_STATUS_MAP[data.status] || { label: data.status_display, badgeClass: 'bg-slate-100 text-slate-700' };
    const statusBadge = document.getElementById('fd-modal-status-badge');
    if (statusBadge) {
      statusBadge.textContent = statusInfo.label;
      statusBadge.className = `px-2 py-0.5 text-[10px] font-bold rounded-full ${statusInfo.badgeClass}`;
    }

    showToast('Đã gửi trao đổi thành công!', 'success');

    // Refresh class feedbacks
    if (activeTeacherClass) {
      fetchClassFeedbacks(activeTeacherClass.id);
    }
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

async function handleUpdateFeedbackStatus() {
  if (!activeFeedbackDetailData) return;
  const select = document.getElementById('fd-status-select');
  const statusVal = select?.value;

  try {
    const res = await fetch(`/api/conduct/feedbacks/${activeFeedbackDetailData.id}/update-status/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify({ status: statusVal })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Lỗi khi cập nhật trạng thái.');

    activeFeedbackDetailData = data;
    const statusInfo = FEEDBACK_STATUS_MAP[data.status] || { label: data.status_display, badgeClass: 'bg-slate-100 text-slate-700' };
    const statusBadge = document.getElementById('fd-modal-status-badge');
    if (statusBadge) {
      statusBadge.textContent = statusInfo.label;
      statusBadge.className = `px-2 py-0.5 text-[10px] font-bold rounded-full ${statusInfo.badgeClass}`;
    }

    showToast(`Đã chuyển trạng thái sang "${statusInfo.label}"`, 'success');

    if (activeTeacherClass) {
      fetchClassFeedbacks(activeTeacherClass.id);
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function openViolationModalForStudent(classId, studentId, studentName) {
  if (!confirm(`Xác nhận chuyển sang lập biên bản vi phạm kỷ luật cho học sinh ${studentName}?`)) {
    return;
  }

  // Open existing quick violation modal
  const classSelect = document.getElementById('modal-violation-class');
  const studentSelect = document.getElementById('modal-violation-student');

  if (classSelect) {
    classSelect.value = classId;
    if (typeof handleClassChangeForStudents === 'function') {
      handleClassChangeForStudents();
      setTimeout(() => {
        if (studentSelect) studentSelect.value = studentId;
      }, 300);
    } else if (studentSelect) {
      studentSelect.value = studentId;
    }
  }

  openModal('modal-quick-violation');
}
'''

target_path = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js'
with open(target_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update getAllowedTabs
old_tabs_logic = """  if (user.role === 'BGH' || user.is_bgh) {
    ['conduct', 'competition', 'alerts', 'reports'].forEach(tab => allowed.add(tab));
  } else if (user.is_gvcn || user.role === 'GVCN') {
    ['conduct', 'competition', 'alerts', 'reports', 'counseling'].forEach(tab => allowed.add(tab));
  } else if (user.role === 'GVBM' || user.is_gvbm) {
    ['conduct', 'counseling'].forEach(tab => allowed.add(tab));"""

new_tabs_logic = """  if (isAdminUser(user)) {
    allowed.add('teacher-classes');
  }
  if (user.role === 'BGH' || user.is_bgh) {
    ['conduct', 'competition', 'alerts', 'reports', 'teacher-classes'].forEach(tab => allowed.add(tab));
  } else if (user.is_gvcn || user.role === 'GVCN') {
    ['conduct', 'competition', 'alerts', 'reports', 'counseling', 'teacher-classes'].forEach(tab => allowed.add(tab));
  } else if (user.role === 'GVBM' || user.is_gvbm) {
    ['conduct', 'counseling', 'teacher-classes'].forEach(tab => allowed.add(tab));"""

if old_tabs_logic in content:
    content = content.replace(old_tabs_logic, new_tabs_logic)

# 2. Update NAV_LABELS
old_nav_labels = """const NAV_LABELS = {
  dashboard: ['Tổng quan', 'layout-dashboard'],"""

new_nav_labels = """const NAV_LABELS = {
  dashboard: ['Tổng quan', 'layout-dashboard'],
  'teacher-classes': ['Lớp & Học sinh', 'graduation-cap'],"""

if old_nav_labels in content and "'teacher-classes':" not in content:
    content = content.replace(old_nav_labels, new_nav_labels)

# 3. Update navTabs
old_nav_tabs = """  const navTabs = {
    dashboard: 'nav-btn-dashboard', conduct: 'nav-btn-conduct', competition: 'nav-btn-competition',"""

new_nav_tabs = """  const navTabs = {
    dashboard: 'nav-btn-dashboard', 'teacher-classes': 'nav-btn-teacher-classes', conduct: 'nav-btn-conduct', competition: 'nav-btn-competition',"""

if old_nav_tabs in content and "'teacher-classes': 'nav-btn-teacher-classes'" not in content:
    content = content.replace(old_nav_tabs, new_nav_tabs)

# 4. Update navigateTab
old_navigate = """  if (tabName === 'profile') renderProfile();
  else if (tabName === 'dashboard') { if (!_dashboardData.loaded) loadDashboard(); }"""

new_navigate = """  if (tabName === 'profile') renderProfile();
  else if (tabName === 'dashboard') { if (!_dashboardData.loaded) loadDashboard(); }
  else if (tabName === 'teacher-classes') loadTeacherClassesModule();"""

if old_navigate in content and "tabName === 'teacher-classes'" not in content:
    content = content.replace(old_navigate, new_navigate)

# 5. Append module functions
if 'function loadTeacherClassesModule(' not in content:
    content += "\n" + JS_CODE

with open(target_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: static/app.js updated with Teacher Classes and Feedback module.")
