(() => {
  const cookie = (name) => {
    const prefix = `${name}=`;
    const item = document.cookie.split(';').map(part => part.trim()).find(part => part.startsWith(prefix));
    return item ? decodeURIComponent(item.slice(prefix.length)) : '';
  };

  const csrfToken = () => cookie('csrftoken') || document.querySelector('[name="csrfmiddlewaretoken"]')?.value || '';

  const parseResponse = async (response) => {
    try { return await response.json(); } catch { return {}; }
  };

  const request = async (url, payload, form) => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken(),
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify(payload),
      });
      return { response, data: await parseResponse(response) };
    } finally {
      window.clearTimeout(timeout);
    }
  };

  const setMessage = (id, message, visible = true) => {
    const node = document.getElementById(id);
    if (!node) return;
    node.textContent = message;
    node.hidden = !visible;
  };

  const errorText = (data) => {
    if (typeof data?.error === 'string') return data.error;
    const details = data?.details || data;
    if (details && typeof details === 'object') {
      for (const value of Object.values(details)) {
        if (Array.isArray(value) && value.length) return String(value[0]);
        if (typeof value === 'string') return value;
      }
    }
    return 'Không thể hoàn tất yêu cầu. Vui lòng thử lại.';
  };

  const withLoading = async (button, idleText, action) => {
    if (!button || button.disabled) return;
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
    button.textContent = 'Đang xử lý…';
    try { await action(); }
    finally {
      button.disabled = false;
      button.removeAttribute('aria-busy');
      button.textContent = idleText;
    }
  };

  const initPublicMenu = () => {
    const toggle = document.getElementById('public-menu-toggle');
    const nav = document.getElementById('public-nav');
    if (!toggle || !nav) return;
    const close = () => {
      nav.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
    };
    toggle.addEventListener('click', () => {
      const open = !nav.classList.contains('is-open');
      nav.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
    });
    nav.querySelectorAll('a').forEach(link => link.addEventListener('click', close));
    document.addEventListener('keydown', event => { if (event.key === 'Escape') close(); });
  };

  const initPublicAccount = () => {
    const account = document.getElementById('public-user-account');
    if (!account) return;

    const toggle = document.getElementById('public-account-toggle');
    const menu = document.getElementById('public-account-menu');
    const logoutButton = document.getElementById('public-account-logout');
    const error = document.getElementById('public-account-error');
    const closeMenu = () => {
      menu.hidden = true;
      toggle.setAttribute('aria-expanded', 'false');
    };

    toggle?.addEventListener('click', () => {
      const open = menu.hidden;
      menu.hidden = !open;
      toggle.setAttribute('aria-expanded', String(open));
    });
    document.addEventListener('click', event => {
      if (!account.contains(event.target)) closeMenu();
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape') closeMenu();
    });
    menu?.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));

    logoutButton?.addEventListener('click', async () => {
      if (logoutButton.disabled) return;
      if (error) {
        error.textContent = '';
        error.hidden = true;
      }
      logoutButton.disabled = true;
      logoutButton.setAttribute('aria-busy', 'true');
      logoutButton.textContent = 'Đang đăng xuất…';
      try {
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 12000);
        let response;
        try {
          response = await fetch('/api/core/auth/logout/', {
            method: 'POST',
            credentials: 'same-origin',
            signal: controller.signal,
            headers: {
              'X-CSRFToken': csrfToken(),
              'X-Requested-With': 'XMLHttpRequest',
            },
          });
        } finally {
          window.clearTimeout(timeout);
        }
        if (!response.ok) {
          const data = await parseResponse(response);
          throw new Error(errorText(data));
        }
        window.location.replace('/');
      } catch (logoutError) {
        if (error) {
          error.textContent = logoutError.name === 'AbortError'
            ? 'Kết nối đang chậm. Phiên đăng nhập vẫn được giữ nguyên; vui lòng thử lại.'
            : (logoutError.message || 'Không thể đăng xuất. Vui lòng thử lại.');
          error.hidden = false;
        }
      } finally {
        logoutButton.disabled = false;
        logoutButton.removeAttribute('aria-busy');
        logoutButton.textContent = 'Đăng xuất';
      }
    });

    const image = document.getElementById('public-account-avatar-image');
    const fallback = document.getElementById('public-account-avatar-fallback');
    if (image && fallback && image.getAttribute('src')) {
      const updateAvatarFallback = () => {
        const loaded = image.complete && image.naturalWidth > 0;
        image.hidden = !loaded;
        fallback.hidden = loaded;
      };
      image.addEventListener('load', updateAvatarFallback);
      image.addEventListener('error', updateAvatarFallback);
      if (image.complete) updateAvatarFallback();
    }
  };

  const applyPublicHomeSession = (user) => {
    const guestActions = document.getElementById('public-guest-actions');
    const account = document.getElementById('public-user-account');
    const menu = document.getElementById('public-account-menu');
    const toggle = document.getElementById('public-account-toggle');
    const error = document.getElementById('public-account-error');
    if (!guestActions || !account) return;

    const signedIn = Boolean(user && user.id);
    guestActions.hidden = signedIn;
    account.hidden = !signedIn;
    if (menu) menu.hidden = true;
    toggle?.setAttribute('aria-expanded', 'false');
    if (error) {
      error.textContent = '';
      error.hidden = true;
    }

    const nameNode = document.getElementById('public-account-toggle-name');
    const detailName = document.getElementById('public-account-detail-name');
    const classNode = document.getElementById('public-account-class');
    const roleNode = document.getElementById('public-account-role');
    const statusNode = document.getElementById('public-account-status');
    const image = document.getElementById('public-account-avatar-image');
    const fallback = document.getElementById('public-account-avatar-fallback');
    if (!signedIn) {
      [nameNode, detailName, classNode, roleNode, statusNode].forEach(node => { if (node) node.textContent = ''; });
      if (classNode) classNode.hidden = true;
      if (image) {
        image.hidden = true;
        image.removeAttribute('src');
      }
      if (fallback) {
        fallback.textContent = 'HK';
        fallback.hidden = false;
      }
      return;
    }

    const displayName = user.full_name || user.username || 'Người dùng';
    const className = user.meta?.class_name || user.department_or_class || '';
    if (nameNode) nameNode.textContent = displayName;
    if (detailName) detailName.textContent = displayName;
    if (classNode) {
      classNode.textContent = className ? `Lớp/đơn vị: ${className}` : '';
      classNode.hidden = !className;
    }
    if (roleNode) roleNode.textContent = user.role_display || 'Vai trò chưa cập nhật';
    if (statusNode) statusNode.textContent = user.account_status_display || 'Trạng thái chưa cập nhật';
    if (fallback) {
      fallback.textContent = displayName.split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0]).join('').toUpperCase() || 'HK';
      fallback.hidden = false;
    }
    if (image) {
      image.hidden = true;
      image.removeAttribute('src');
      if (user.avatar) {
        image.onload = () => { image.hidden = false; if (fallback) fallback.hidden = true; };
        image.onerror = () => { image.hidden = true; if (fallback) fallback.hidden = false; };
        image.src = user.avatar;
      }
    }
  };

  const initPublicHomeSessionSync = () => {
    if (!document.querySelector('.public-page')) return;

    let refreshInProgress = false;
    const refresh = async () => {
      if (refreshInProgress) return;
      refreshInProgress = true;
      const loading = document.getElementById('public-session-loading');
      const guestActions = document.getElementById('public-guest-actions');
      const account = document.getElementById('public-user-account');
      if (loading) {
        loading.textContent = 'Đang kiểm tra phiên…';
        loading.hidden = false;
      }
      if (guestActions) guestActions.hidden = true;
      if (account) account.hidden = true;
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 10000);
      try {
        const response = await fetch('/api/core/auth/me/', {
          credentials: 'same-origin',
          cache: 'no-store',
          signal: controller.signal,
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        const data = await parseResponse(response);
        if (!response.ok) throw new Error('Session lookup failed');
        applyPublicHomeSession(data.authenticated ? data.user : null);
      } catch {
        // Fail closed so a bfcache page cannot leave an expired identity visible.
        applyPublicHomeSession(null);
        if (loading) {
          loading.textContent = 'Không thể kiểm tra phiên. Vui lòng tải lại trang.';
          loading.hidden = false;
        }
      } finally {
        window.clearTimeout(timeout);
        if (loading && loading.textContent === 'Đang kiểm tra phiên…') loading.hidden = true;
        refreshInProgress = false;
      }
    };

    window.addEventListener('pageshow', event => {
      if (event.persisted) refresh();
    });
    let wasHidden = document.hidden;
    document.addEventListener('visibilitychange', () => {
      if (wasHidden && !document.hidden) refresh();
      wasHidden = document.hidden;
    });
  };

  
/* --- TEACHER MULTI-SUBJECT & MULTI-CLASS SELECTION HELPERS --- */
const HIGH_SCHOOL_SUBJECTS = [
  'Toán học',
  'Ngữ văn',
  'Tiếng Anh',
  'Vật lý',
  'Hóa học',
  'Sinh học',
  'Lịch sử',
  'Địa lý',
  'GDKT & PL',
  'Tin học',
  'Công nghệ',
  'Giáo dục thể chất',
  'GD Quốc phòng & An ninh',
  'HĐTN - Hướng nghiệp',
  'Âm nhạc',
  'Mỹ thuật'
];

let currentRegGradeTab = 10;

function renderTeacherSubjectsGrid() {
  const grid = document.getElementById('subjects-checkboxes-grid');
  if (!grid || grid.children.length > 0) return;
  grid.innerHTML = HIGH_SCHOOL_SUBJECTS.map(s => `
    <label class="subject-choice-pill flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 rounded-xl cursor-pointer text-xs font-semibold text-slate-700 transition select-none">
      <input type="checkbox" name="teacher_subjects" value="${s}" onchange="syncTeacherSubjectSelection()" class="hidden">
      <span class="chip-check text-blue-600 font-bold hidden">✓</span>
      <span>${s}</span>
    </label>
  `).join('');
}

function syncTeacherSubjectSelection() {
  const checked = Array.from(document.querySelectorAll('input[name="teacher_subjects"]:checked')).map(el => el.value);
  const countBadge = document.getElementById('register-subject-count-badge');
  const triggerContent = document.getElementById('register-subjects-trigger-content');
  const clearBtn = document.getElementById('btn-clear-subjects-quick');
  const footerCount = document.getElementById('register-subjects-footer-count');

  if (countBadge) countBadge.textContent = `${checked.length} môn đã chọn`;
  if (footerCount) footerCount.textContent = `Đã chọn: ${checked.length} môn`;
  if (clearBtn) clearBtn.classList.toggle('hidden', checked.length === 0);

  // Update styles of chips in dropdown
  document.querySelectorAll('#subjects-checkboxes-grid label').forEach(lbl => {
    const cb = lbl.querySelector('input');
    const checkIcon = lbl.querySelector('.chip-check');
    if (!cb) return;
    if (cb.checked) {
      lbl.className = 'subject-choice-pill flex items-center gap-1.5 px-2.5 py-1.5 bg-blue-50 text-blue-800 border border-blue-300 rounded-xl cursor-pointer text-xs font-bold shadow-2xs scale-102 transition select-none';
      if (checkIcon) checkIcon.classList.remove('hidden');
    } else {
      lbl.className = 'subject-choice-pill flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 rounded-xl cursor-pointer text-xs font-semibold text-slate-700 transition select-none';
      if (checkIcon) checkIcon.classList.add('hidden');
    }
  });

  // Render cute mini pills inside trigger box
  if (triggerContent) {
    if (checked.length === 0) {
      triggerContent.innerHTML = '<span id="register-subjects-summary-text" class="text-slate-400 font-normal">✨ Bấm chọn môn giảng dạy (1 hoặc nhiều môn)...</span>';
    } else {
      triggerContent.innerHTML = checked.map(s => `
        <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-800 border border-blue-200 shadow-2xs">
          <span>${s}</span>
          <span onclick="event.stopPropagation(); removeTeacherSubject('${s}')" class="text-blue-500 hover:text-rose-600 font-bold text-xs cursor-pointer leading-none">&times;</span>
        </span>
      `).join('');
    }
  }
}

function syncTeacherClassSelection() {
  const checked = Array.from(document.querySelectorAll('input[name="teacher_classes"]:checked')).map(el => el.value);
  const countBadge = document.getElementById('register-classes-count-badge');
  const triggerContent = document.getElementById('register-classes-trigger-content');
  const clearBtn = document.getElementById('btn-clear-classes-quick');
  const footerCount = document.getElementById('register-classes-footer-count');

  if (countBadge) countBadge.textContent = `${checked.length} lớp đã chọn`;
  if (footerCount) footerCount.textContent = `Đã chọn: ${checked.length} lớp`;
  if (clearBtn) clearBtn.classList.toggle('hidden', checked.length === 0);

  // Update grade badges on tabs
  [10, 11, 12].forEach(g => {
    const gradeCheckedCount = document.querySelectorAll(`input[name="teacher_classes"][data-grade="${g}"]:checked`).length;
    const badge = document.getElementById(`reg-grade-count-${g}`);
    if (badge) {
      if (gradeCheckedCount > 0) {
        badge.textContent = gradeCheckedCount;
        badge.classList.remove('hidden');
      } else {
        badge.classList.add('hidden');
      }
    }
  });

  // Update styles of chips in dropdown
  document.querySelectorAll('input[name="teacher_classes"]').forEach(cb => {
    const lbl = cb.closest('label');
    if (!lbl) return;
    const grade = cb.getAttribute('data-grade');
    if (cb.checked) {
      let activeClass = 'bg-indigo-50 text-indigo-800 border-indigo-300 font-bold';
      if (grade === '10') activeClass = 'bg-blue-50 text-blue-800 border-blue-300 font-bold';
      else if (grade === '11') activeClass = 'bg-emerald-50 text-emerald-800 border-emerald-300 font-bold';
      else if (grade === '12') activeClass = 'bg-purple-50 text-purple-800 border-purple-300 font-bold';
      lbl.className = `class-choice-pill flex items-center justify-center p-1.5 ${activeClass} border rounded-lg cursor-pointer text-xs shadow-2xs scale-102 transition select-none text-center`;
    } else {
      lbl.className = 'class-choice-pill flex items-center justify-center p-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg cursor-pointer text-xs font-semibold text-slate-700 transition select-none text-center';
    }
  });

  // Update toggle select button text for current active grade
  updateToggleSelectCurrentGradeBtn();

  // Render cute mini pills inside trigger box (compact summary if many selected)
  if (triggerContent) {
    if (checked.length === 0) {
      triggerContent.innerHTML = '<span id="register-classes-summary-text" class="text-slate-400 font-normal">🏫 Bấm chọn các lớp giảng dạy theo khối...</span>';
    } else if (checked.length <= 4) {
      triggerContent.innerHTML = checked.map(c => `
        <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-800 border border-indigo-200 shadow-2xs">
          <span>${c}</span>
          <span onclick="event.stopPropagation(); removeTeacherClass('${c}')" class="text-indigo-500 hover:text-rose-600 font-bold text-xs cursor-pointer leading-none">&times;</span>
        </span>
      `).join('');
    } else {
      const topPills = checked.slice(0, 3).map(c => `
        <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-800 border border-indigo-200 shadow-2xs">
          <span>${c}</span>
          <span onclick="event.stopPropagation(); removeTeacherClass('${c}')" class="text-indigo-500 hover:text-rose-600 font-bold text-xs cursor-pointer leading-none">&times;</span>
        </span>
      `).join('');
      const moreCount = checked.length - 3;
      triggerContent.innerHTML = `${topPills} <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-slate-100 text-slate-700 border border-slate-200">+${moreCount} lớp khác</span>`;
    }
  }
}

function switchRegisterGradeTab(grade) {
  currentRegGradeTab = grade;
  [10, 11, 12].forEach(g => {
    const tabBtn = document.getElementById(`reg-grade-tab-${g}`);
    const panel = document.getElementById(`teacher-classes-grid-${g}`);
    const isCurrent = (g === grade);
    if (tabBtn) {
      if (isCurrent) {
        tabBtn.className = 'px-2.5 py-1 rounded-lg text-xs font-bold bg-white text-indigo-700 shadow-xs transition flex items-center gap-1';
      } else {
        tabBtn.className = 'px-2.5 py-1 rounded-lg text-xs font-bold text-slate-600 hover:text-slate-900 transition flex items-center gap-1';
      }
    }
    if (panel) {
      panel.classList.toggle('hidden', !isCurrent);
    }
  });
  updateToggleSelectCurrentGradeBtn();
}

function updateToggleSelectCurrentGradeBtn() {
  const btn = document.getElementById('btn-toggle-select-current-grade');
  if (!btn) return;
  const grade = currentRegGradeTab;
  const cbs = Array.from(document.querySelectorAll(`input[name="teacher_classes"][data-grade="${grade}"]`));
  const allChecked = cbs.length > 0 && cbs.every(cb => cb.checked);
  btn.textContent = allChecked ? `✓ Bỏ chọn Khối ${grade}` : `+ Chọn cả Khối ${grade}`;
}

function toggleSelectCurrentGrade() {
  const grade = currentRegGradeTab;
  const cbs = Array.from(document.querySelectorAll(`input[name="teacher_classes"][data-grade="${grade}"]`));
  const allChecked = cbs.length > 0 && cbs.every(cb => cb.checked);
  cbs.forEach(cb => { cb.checked = !allChecked; });
  syncTeacherClassSelection();
}

function toggleTeacherSubjectsDropdown(forceState) {
  const container = document.getElementById('register-subjects-dropdown-container');
  const icon = document.getElementById('icon-subjects-chevron');
  if (!container) return;

  const isOpen = typeof forceState === 'boolean' ? !forceState : !container.classList.contains('hidden');
  if (isOpen) {
    container.classList.add('hidden');
    if (icon) icon.classList.remove('rotate-180');
  } else {
    // Close classes dropdown first so only one is open
    toggleTeacherClassesDropdown(false);
    container.classList.remove('hidden');
    if (icon) icon.classList.add('rotate-180');
    renderTeacherSubjectsGrid();
    const searchInput = document.getElementById('filter-subjects-input');
    if (searchInput) searchInput.focus();
  }
}

function toggleTeacherClassesDropdown(forceState) {
  const container = document.getElementById('register-classes-dropdown-container');
  const icon = document.getElementById('icon-classes-chevron');
  if (!container) return;

  const isOpen = typeof forceState === 'boolean' ? !forceState : !container.classList.contains('hidden');
  if (isOpen) {
    container.classList.add('hidden');
    if (icon) icon.classList.remove('rotate-180');
  } else {
    // Close subjects dropdown first
    toggleTeacherSubjectsDropdown(false);
    container.classList.remove('hidden');
    if (icon) icon.classList.add('rotate-180');
    populateTeacherClassGridsIfEmpty();
    switchRegisterGradeTab(currentRegGradeTab);
    const searchInput = document.getElementById('filter-classes-input');
    if (searchInput) searchInput.focus();
  }
}

// Click outside to dismiss floating popovers
document.addEventListener('click', (e) => {
  const teacherDetails = document.getElementById('register-teacher-details');
  if (!teacherDetails) return;
  if (!teacherDetails.contains(e.target)) {
    toggleTeacherSubjectsDropdown(false);
    toggleTeacherClassesDropdown(false);
  }
});

function filterTeacherSubjects(q) {
  const term = (q || '').toLowerCase().trim();
  document.querySelectorAll('#subjects-checkboxes-grid label').forEach(lbl => {
    const text = lbl.textContent.toLowerCase();
    lbl.style.display = (!term || text.includes(term)) ? 'flex' : 'none';
  });
}

function filterTeacherClasses(q) {
  const term = (q || '').toLowerCase().trim();
  document.querySelectorAll('input[name="teacher_classes"]').forEach(cb => {
    const lbl = cb.closest('label');
    if (!lbl) return;
    const text = cb.value.toLowerCase();
    lbl.style.display = (!term || text.includes(term)) ? 'flex' : 'none';
  });
}

function clearTeacherSubjects() {
  document.querySelectorAll('input[name="teacher_subjects"]').forEach(cb => { cb.checked = false; });
  syncTeacherSubjectSelection();
}

function clearTeacherClasses() {
  document.querySelectorAll('input[name="teacher_classes"]').forEach(cb => { cb.checked = false; });
  syncTeacherClassSelection();
}

function removeTeacherSubject(val) {
  const cb = document.querySelector(`input[name="teacher_subjects"][value="${val}"]`);
  if (cb) { cb.checked = false; syncTeacherSubjectSelection(); }
}

function removeTeacherClass(val) {
  const cb = document.querySelector(`input[name="teacher_classes"][value="${val}"]`);
  if (cb) { cb.checked = false; syncTeacherClassSelection(); }
}

function getSelectedTeacherSubjects() {
  return Array.from(document.querySelectorAll('input[name="teacher_subjects"]:checked')).map(el => el.value);
}

function getSelectedTeacherClasses() {
  return Array.from(document.querySelectorAll('input[name="teacher_classes"]:checked')).map(el => el.value);
}

function populateTeacherClassGridsIfEmpty() {
  const classes = window.HK_SCHOOL_CLASSES || [];
  if (!classes || classes.length === 0) return;
  [10, 11, 12].forEach(grade => {
    const grid = document.getElementById(`teacher-classes-grid-${grade}`);
    if (grid && grid.children.length === 0) {
      const gradeClasses = classes.filter(c => c.grade === grade);
      grid.innerHTML = gradeClasses.map(item => `
        <label class="class-choice-pill flex items-center justify-center p-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg cursor-pointer text-xs font-semibold text-slate-700 transition select-none text-center">
          <input type="checkbox" name="teacher_classes" value="${item.name}" data-grade="${item.grade}" onchange="syncTeacherClassSelection()" class="hidden">
          <span>${item.name}</span>
        </label>
      `).join('');
    }
  });
}

// Expose functions globally for inline events
window.toggleTeacherSubjectsDropdown = toggleTeacherSubjectsDropdown;
window.toggleTeacherClassesDropdown = toggleTeacherClassesDropdown;
window.switchRegisterGradeTab = switchRegisterGradeTab;
window.toggleSelectCurrentGrade = toggleSelectCurrentGrade;
window.filterTeacherSubjects = filterTeacherSubjects;
window.filterTeacherClasses = filterTeacherClasses;
window.clearTeacherSubjects = clearTeacherSubjects;
window.clearTeacherClasses = clearTeacherClasses;
window.removeTeacherSubject = removeTeacherSubject;
window.removeTeacherClass = removeTeacherClass;
window.syncTeacherSubjectSelection = syncTeacherSubjectSelection;
window.syncTeacherClassSelection = syncTeacherClassSelection;

const initRegistrationForm = () => {
    const form = document.getElementById('public-register-form');
    if (!form) return;
    const role = document.getElementById('register-requested-role');
    const studentFields = document.getElementById('register-student-details');
    const teacherDetails = document.getElementById('register-teacher-details') || document.getElementById('register-subject-field');
    const departmentField = document.getElementById('register-department-field');
    const grade = document.getElementById('register-grade');
    const classSelect = document.getElementById('register-class');
    const department = document.getElementById('register-department');

    const syncRole = () => {
      const isStudent = role.value === 'HOC_SINH';
      const isTeacher = role.value === 'GVBM';
      if (studentFields) studentFields.hidden = !isStudent;
      if (teacherDetails) teacherDetails.hidden = !isTeacher;
      if (departmentField) departmentField.hidden = isStudent || isTeacher;
      if (grade) grade.required = isStudent;
      if (classSelect) classSelect.required = isStudent;
      if (department) department.required = !isStudent && !isTeacher;
      if (isTeacher) {
        renderTeacherSubjectsGrid();
        populateTeacherClassGridsIfEmpty();
        if (window.lucide) lucide.createIcons();
      }
    };
    const syncClasses = () => {
      const selectedGrade = grade.value;
      Array.from(classSelect.options).forEach(option => {
        if (!option.value) return;
        option.hidden = Boolean(selectedGrade && option.dataset.grade !== selectedGrade);
        if (option.hidden && option.selected) classSelect.value = '';
      });
    };
    role.addEventListener('change', syncRole);
    grade.addEventListener('change', syncClasses);
    syncRole();
    syncClasses();

    form.addEventListener('submit', event => {
      event.preventDefault();
      const errorId = 'public-register-error';
      setMessage(errorId, '', false);
      if (!form.reportValidity()) return;

      const values = new FormData(form);
      const requestedRole = values.get('requested_role');
      const payload = {
        full_name: String(values.get('full_name') || '').trim(),
        username: String(values.get('username') || '').trim(),
        email: String(values.get('email') || '').trim(),
        phone: String(values.get('phone') || '').trim(),
        requested_role: requestedRole,
        password: String(values.get('password') || ''),
        confirm_password: String(values.get('confirm_password') || ''),
        terms_accepted: document.getElementById('register-terms').checked,
      };
      if (requestedRole === 'HOC_SINH') {
        payload.grade_level = Number(values.get('grade_level'));
        payload.class_id = Number(values.get('class_id'));
      } else if (requestedRole === 'GVBM') {
        const subjects = getSelectedTeacherSubjects();
        const classes = getSelectedTeacherClasses();
        if (subjects.length === 0) {
          setMessage(errorId, 'Vui lòng chọn ít nhất một môn giảng dạy trong danh sách xổ xuống.', false);
          toggleTeacherSubjectsDropdown();
          return;
        }
        payload.subjects = subjects;
        payload.subject = subjects.join(', ');
        payload.teaching_classes = classes;
      } else {
        payload.department_or_class = String(values.get('department_or_class') || '').trim();
      }

      withLoading(document.getElementById('public-register-submit'), 'Gửi yêu cầu đăng ký', async () => {
        try {
          const { response, data } = await request('/api/core/auth/register/', payload, form);
          if (!response.ok) throw new Error(errorText(data));
          sessionStorage.setItem('hk-registration-confirmation', data.full_name || payload.full_name);
          window.location.assign('/registration-pending');
        } catch (error) {
          setMessage(errorId, error.name === 'AbortError' ? 'Kết nối đang chậm. Vui lòng thử lại.' : error.message);
        }
      });
    });
  };

  const initLoginForm = () => {
    const form = document.getElementById('public-login-form');
    if (!form) return;
    document.querySelectorAll('[data-password-toggle]').forEach(button => {
      const input = document.getElementById(button.dataset.passwordToggle);
      if (!input) return;
      button.addEventListener('click', () => {
        const showPassword = input.type === 'password';
        input.type = showPassword ? 'text' : 'password';
        button.textContent = showPassword ? 'Ẩn' : 'Hiện';
        button.setAttribute('aria-label', `${showPassword ? 'Ẩn' : 'Hiện'} mật khẩu`);
        button.setAttribute('aria-pressed', String(showPassword));
      });
    });
    form.addEventListener('submit', event => {
      event.preventDefault();
      setMessage('public-login-error', '', false);
      if (!form.reportValidity()) return;
      const values = new FormData(form);
      const payload = {
        username: String(values.get('username') || '').trim(),
        password: String(values.get('password') || ''),
      };
      withLoading(document.getElementById('public-login-submit'), 'Đăng nhập hệ thống', async () => {
        try {
          const { response, data } = await request('/api/core/auth/login/', payload, form);
          if (!response.ok) {
            if (data?.account_status === 'PENDING') {
              sessionStorage.setItem('hk-registration-confirmation', data.full_name || payload.username);
              window.location.assign('/registration-pending');
              return;
            }
            throw new Error(errorText(data));
          }
          window.location.assign(destinationAfterLogin(data.user));
        } catch (error) {
          setMessage('public-login-error', error.name === 'AbortError' ? 'Kết nối đang chậm. Vui lòng thử lại.' : error.message);
        }
      });
    });
  };

  const destinationAfterLogin = (user) => {
    const requested = new URLSearchParams(window.location.search).get('next');
    if (!requested || !requested.startsWith('/') || requested.startsWith('//') || requested.includes('\\')) return '/dashboard';
    try {
      const destination = new URL(requested, window.location.origin);
      const path = destination.pathname.replace(/\/$/, '') || '/';
      if (destination.origin !== window.location.origin || !['/dashboard', '/profile', '/admin/users'].includes(path)) return '/dashboard';
      const isAdmin = Boolean(user?.is_admin || user?.is_super_admin || user?.is_superuser || ['ADMIN', 'SUPER_ADMIN'].includes(user?.role));
      if (path === '/admin/users' && !isAdmin) return '/dashboard';
      return `${path}${destination.search}${destination.hash}`;
    } catch {
      return '/dashboard';
    }
  };

  const initPendingConfirmation = () => {
    const savedName = sessionStorage.getItem('hk-registration-confirmation');
    if (!savedName) return;
    sessionStorage.removeItem('hk-registration-confirmation');
    const generic = document.getElementById('pending-generic');
    const confirmed = document.getElementById('pending-confirmed');
    const name = document.getElementById('pending-confirmed-name');
    if (name) name.textContent = `Cảm ơn ${savedName}.`;
    if (generic) generic.hidden = true;
    if (confirmed) confirmed.hidden = false;
  };

  const initForgotForm = () => {
    const form = document.getElementById('public-forgot-form');
    if (!form) return;
    form.addEventListener('submit', event => {
      event.preventDefault();
      setMessage('public-forgot-error', '', false);
      setMessage('public-forgot-message', '', false);
      if (!form.reportValidity()) return;
      const email = String(new FormData(form).get('email') || '').trim();
      withLoading(document.getElementById('public-forgot-submit'), 'Gửi hướng dẫn khôi phục', async () => {
        try {
          const { response, data } = await request('/api/core/auth/forgot-password/', { email }, form);
          if (!response.ok) {
            let errMsg = errorText(data);
            if (data && data.debug_reset_url) {
              errMsg += `<br><a href="${data.debug_reset_url}" style="color:#2563EB; font-weight:700; text-decoration:underline; margin-top:8px; display:inline-block;">👉 Nhấn vào đây để đặt lại mật khẩu ngay (Chế độ phát triển)</a>`;
              const errEl = document.getElementById('public-forgot-error');
              if (errEl) {
                errEl.innerHTML = errMsg;
                errEl.hidden = false;
                return;
              }
            }
            throw new Error(errMsg);
          }
          setMessage('public-forgot-message', data.message || 'Nếu thông tin tài khoản hợp lệ, hướng dẫn sẽ được gửi đến hộp thư của bạn.');
        } catch (error) {
          setMessage('public-forgot-error', error.name === 'AbortError' ? 'Kết nối đang chậm. Vui lòng thử lại.' : error.message);
        }
      });
    });
  };

  const initResetForm = () => {
    const form = document.getElementById('public-reset-form');
    if (!form) return;
    const query = new URLSearchParams(window.location.search);
    const uid = query.get('uid') || '';
    const token = query.get('token') || '';
    const submit = document.getElementById('public-reset-submit');
    if (!uid || !token) {
      submit.disabled = true;
      setMessage('public-reset-error', 'Liên kết đặt lại mật khẩu không đầy đủ. Hãy yêu cầu email hướng dẫn mới.');
    }
    form.addEventListener('submit', event => {
      event.preventDefault();
      setMessage('public-reset-error', '', false);
      setMessage('public-reset-success', '', false);
      if (!uid || !token || !form.reportValidity()) return;
      const values = new FormData(form);
      const payload = {
        uid,
        token,
        new_password: String(values.get('new_password') || ''),
        confirm_password: String(values.get('confirm_password') || ''),
      };
      withLoading(submit, 'Cập nhật mật khẩu', async () => {
        try {
          const { response, data } = await request('/api/core/auth/reset-password/', payload, form);
          if (!response.ok) throw new Error(errorText(data));
          form.reset();
          setMessage('public-reset-success', data.message || 'Mật khẩu đã được cập nhật. Vui lòng đăng nhập.');
          submit.hidden = true;
        } catch (error) {
          setMessage('public-reset-error', error.name === 'AbortError' ? 'Kết nối đang chậm. Vui lòng thử lại.' : error.message);
        }
      });
    });
  };

  

  /* ==============================================================================
   * COMPLETE PROFILE - TEACHER MULTI-SUBJECT & MULTI-CLASS SELECTION HELPERS
   * ============================================================================== */
  let currentCompGradeTab = 10;

  function renderCompleteTeacherSubjectsGrid() {
    const grid = document.getElementById('complete-subjects-checkboxes-grid');
    if (!grid || grid.children.length > 0) return;
    const subjects = typeof HIGH_SCHOOL_SUBJECTS !== 'undefined' ? HIGH_SCHOOL_SUBJECTS : [
      'Toán học', 'Ngữ văn', 'Tiếng Anh', 'Vật lý', 'Hóa học', 'Sinh học',
      'Lịch sử', 'Địa lý', 'GDKT & PL', 'Tin học', 'Công nghệ',
      'Giáo dục thể chất', 'GD Quốc phòng & An ninh', 'HĐTN - Hướng nghiệp',
      'Âm nhạc', 'Mỹ thuật'
    ];
    grid.innerHTML = subjects.map(s => `
      <label class="subject-choice-pill flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 rounded-xl cursor-pointer text-xs font-semibold text-slate-700 transition select-none">
        <input type="checkbox" name="complete_teacher_subjects" value="${s}" onchange="syncCompleteTeacherSubjectSelection()" class="hidden">
        <span class="chip-check text-blue-600 font-bold hidden">✓</span>
        <span>${s}</span>
      </label>
    `).join('');
  }

  function syncCompleteTeacherSubjectSelection() {
    const checked = Array.from(document.querySelectorAll('input[name="complete_teacher_subjects"]:checked')).map(el => el.value);
    const countBadge = document.getElementById('complete-subject-count-badge');
    const triggerContent = document.getElementById('complete-subjects-trigger-content');
    const clearBtn = document.getElementById('btn-clear-complete-subjects-quick');
    const footerCount = document.getElementById('complete-subjects-footer-count');

    if (countBadge) countBadge.textContent = `${checked.length} môn đã chọn`;
    if (footerCount) footerCount.textContent = `Đã chọn: ${checked.length} môn`;
    if (clearBtn) clearBtn.classList.toggle('hidden', checked.length === 0);

    document.querySelectorAll('#complete-subjects-checkboxes-grid label').forEach(lbl => {
      const cb = lbl.querySelector('input');
      const checkIcon = lbl.querySelector('.chip-check');
      if (!cb) return;
      if (cb.checked) {
        lbl.className = 'subject-choice-pill flex items-center gap-1.5 px-2.5 py-1.5 bg-blue-50 text-blue-800 border border-blue-300 rounded-xl cursor-pointer text-xs font-bold shadow-2xs scale-102 transition select-none';
        if (checkIcon) checkIcon.classList.remove('hidden');
      } else {
        lbl.className = 'subject-choice-pill flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 rounded-xl cursor-pointer text-xs font-semibold text-slate-700 transition select-none';
        if (checkIcon) checkIcon.classList.add('hidden');
      }
    });

    if (triggerContent) {
      if (checked.length === 0) {
        triggerContent.innerHTML = '<span id="complete-subjects-summary-text" class="text-slate-400 font-normal">✨ Bấm chọn môn giảng dạy (1 hoặc nhiều môn)...</span>';
      } else {
        triggerContent.innerHTML = checked.map(s => `
          <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-800 border border-blue-200 shadow-2xs">
            <span>${s}</span>
            <span onclick="event.stopPropagation(); removeCompleteTeacherSubject('${s}')" class="text-blue-500 hover:text-rose-600 font-bold text-xs cursor-pointer leading-none">&times;</span>
          </span>
        `).join('');
      }
    }
  }

  function toggleCompleteTeacherSubjectsDropdown(forceState) {
    const container = document.getElementById('complete-subjects-dropdown-container');
    const icon = document.getElementById('icon-complete-subjects-chevron');
    if (!container) return;

    const isOpen = typeof forceState === 'boolean' ? !forceState : !container.classList.contains('hidden');
    if (isOpen) {
      container.classList.add('hidden');
      if (icon) icon.classList.remove('rotate-180');
    } else {
      toggleCompleteTeacherClassesDropdown(false);
      container.classList.remove('hidden');
      if (icon) icon.classList.add('rotate-180');
      renderCompleteTeacherSubjectsGrid();
      const searchInput = document.getElementById('filter-complete-subjects-input');
      if (searchInput) searchInput.focus();
    }
  }

  function toggleCompleteTeacherClassesDropdown(forceState) {
    const container = document.getElementById('complete-classes-dropdown-container');
    const icon = document.getElementById('icon-complete-classes-chevron');
    if (!container) return;

    const isOpen = typeof forceState === 'boolean' ? !forceState : !container.classList.contains('hidden');
    if (isOpen) {
      container.classList.add('hidden');
      if (icon) icon.classList.remove('rotate-180');
    } else {
      toggleCompleteTeacherSubjectsDropdown(false);
      container.classList.remove('hidden');
      if (icon) icon.classList.add('rotate-180');
      switchCompleteGradeTab(currentCompGradeTab);
      const searchInput = document.getElementById('filter-complete-classes-input');
      if (searchInput) searchInput.focus();
    }
  }

  function filterCompleteTeacherSubjects(q) {
    const term = (q || '').toLowerCase().trim();
    document.querySelectorAll('#complete-subjects-checkboxes-grid label').forEach(lbl => {
      const text = lbl.textContent.toLowerCase();
      lbl.style.display = (!term || text.includes(term)) ? 'flex' : 'none';
    });
  }

  function filterCompleteTeacherClasses(q) {
    const term = (q || '').toLowerCase().trim();
    document.querySelectorAll('input[name="complete_teacher_classes"]').forEach(cb => {
      const lbl = cb.closest('label');
      if (!lbl) return;
      const text = cb.value.toLowerCase();
      lbl.style.display = (!term || text.includes(term)) ? 'flex' : 'none';
    });
  }

  function clearCompleteTeacherSubjects() {
    document.querySelectorAll('input[name="complete_teacher_subjects"]').forEach(cb => { cb.checked = false; });
    syncCompleteTeacherSubjectSelection();
  }

  function clearCompleteTeacherClasses() {
    document.querySelectorAll('input[name="complete_teacher_classes"]').forEach(cb => { cb.checked = false; });
    syncCompleteTeacherClassSelection();
  }

  function removeCompleteTeacherSubject(val) {
    const cb = document.querySelector(`input[name="complete_teacher_subjects"][value="${val}"]`);
    if (cb) { cb.checked = false; syncCompleteTeacherSubjectSelection(); }
  }

  function removeCompleteTeacherClass(val) {
    const cb = document.querySelector(`input[name="complete_teacher_classes"][value="${val}"]`);
    if (cb) { cb.checked = false; syncCompleteTeacherClassSelection(); }
  }

  function getSelectedCompleteTeacherSubjects() {
    return Array.from(document.querySelectorAll('input[name="complete_teacher_subjects"]:checked')).map(el => el.value);
  }

  function getSelectedCompleteTeacherClasses() {
    return Array.from(document.querySelectorAll('input[name="complete_teacher_classes"]:checked')).map(el => el.value);
  }

  function updateToggleSelectCompleteCurrentGradeBtn() {
    const btn = document.getElementById('btn-toggle-select-complete-current-grade');
    if (!btn) return;
    const grade = currentCompGradeTab;
    const cbs = Array.from(document.querySelectorAll(`input[name="complete_teacher_classes"][data-grade="${grade}"]`));
    const allChecked = cbs.length > 0 && cbs.every(cb => cb.checked);
    btn.textContent = allChecked ? `✓ Bỏ chọn Khối ${grade}` : `+ Chọn cả Khối ${grade}`;
  }

  function toggleSelectCompleteCurrentGrade() {
    const grade = currentCompGradeTab;
    const cbs = Array.from(document.querySelectorAll(`input[name="complete_teacher_classes"][data-grade="${grade}"]`));
    const allChecked = cbs.length > 0 && cbs.every(cb => cb.checked);
    cbs.forEach(cb => { cb.checked = !allChecked; });
    syncCompleteTeacherClassSelection();
  }

  function switchCompleteGradeTab(grade) {
    currentCompGradeTab = grade;
    [10, 11, 12].forEach(g => {
      const tabBtn = document.getElementById(`comp-grade-tab-${g}`);
      const panel = document.getElementById(`complete-teacher-classes-grid-${g}`);
      const isCurrent = (g === grade);
      if (tabBtn) {
        if (isCurrent) {
          tabBtn.className = 'px-2.5 py-1 rounded-lg text-xs font-bold bg-white text-indigo-700 shadow-xs transition flex items-center gap-1';
        } else {
          tabBtn.className = 'px-2.5 py-1 rounded-lg text-xs font-bold text-slate-600 hover:text-slate-900 transition flex items-center gap-1';
        }
      }
      if (panel) {
        panel.classList.toggle('hidden', !isCurrent);
      }
    });
    updateToggleSelectCompleteCurrentGradeBtn();
  }

  function syncCompleteTeacherClassSelection() {
    const checked = Array.from(document.querySelectorAll('input[name="complete_teacher_classes"]:checked')).map(el => el.value);
    const countBadge = document.getElementById('complete-classes-count-badge');
    const triggerContent = document.getElementById('complete-classes-trigger-content');
    const clearBtn = document.getElementById('btn-clear-complete-classes-quick');
    const footerCount = document.getElementById('complete-classes-footer-count');

    if (countBadge) countBadge.textContent = `${checked.length} lớp đã chọn`;
    if (footerCount) footerCount.textContent = `Đã chọn: ${checked.length} lớp`;
    if (clearBtn) clearBtn.classList.toggle('hidden', checked.length === 0);

    // Update grade badges on tabs
    [10, 11, 12].forEach(g => {
      const gradeCheckedCount = document.querySelectorAll(`input[name="complete_teacher_classes"][data-grade="${g}"]:checked`).length;
      const badge = document.getElementById(`comp-grade-count-${g}`);
      if (badge) {
        if (gradeCheckedCount > 0) {
          badge.textContent = gradeCheckedCount;
          badge.classList.remove('hidden');
        } else {
          badge.classList.add('hidden');
        }
      }
    });

    // Update styles of chips in dropdown
    document.querySelectorAll('input[name="complete_teacher_classes"]').forEach(cb => {
      const lbl = cb.closest('label');
      if (!lbl) return;
      const grade = cb.getAttribute('data-grade');
      if (cb.checked) {
        let activeClass = 'bg-indigo-50 text-indigo-800 border-indigo-300 font-bold';
        if (grade === '10') activeClass = 'bg-blue-50 text-blue-800 border-blue-300 font-bold';
        else if (grade === '11') activeClass = 'bg-emerald-50 text-emerald-800 border-emerald-300 font-bold';
        else if (grade === '12') activeClass = 'bg-purple-50 text-purple-800 border-purple-300 font-bold';
        lbl.className = `class-choice-pill flex items-center justify-center p-1.5 ${activeClass} border rounded-lg cursor-pointer text-xs shadow-2xs scale-102 transition select-none text-center`;
      } else {
        lbl.className = 'class-choice-pill flex items-center justify-center p-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg cursor-pointer text-xs font-semibold text-slate-700 transition select-none text-center';
      }
    });

    updateToggleSelectCompleteCurrentGradeBtn();

    // Render cute mini pills inside trigger box
    if (triggerContent) {
      if (checked.length === 0) {
        triggerContent.innerHTML = '<span id="complete-classes-summary-text" class="text-slate-400 font-normal">🏫 Bấm chọn các lớp giảng dạy theo khối...</span>';
      } else if (checked.length <= 4) {
        triggerContent.innerHTML = checked.map(c => `
          <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-800 border border-indigo-200 shadow-2xs">
            <span>${c}</span>
            <span onclick="event.stopPropagation(); removeCompleteTeacherClass('${c}')" class="text-indigo-500 hover:text-rose-600 font-bold text-xs cursor-pointer leading-none">&times;</span>
          </span>
        `).join('');
      } else {
        const topPills = checked.slice(0, 3).map(c => `
          <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-800 border border-indigo-200 shadow-2xs">
            <span>${c}</span>
            <span onclick="event.stopPropagation(); removeCompleteTeacherClass('${c}')" class="text-indigo-500 hover:text-rose-600 font-bold text-xs cursor-pointer leading-none">&times;</span>
          </span>
        `).join('');
        const moreCount = checked.length - 3;
        triggerContent.innerHTML = `${topPills} <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-slate-100 text-slate-700 border border-slate-200">+${moreCount} lớp khác</span>`;
      }
    }
  }

  // Dismiss floating popovers on click outside
  document.addEventListener('click', (e) => {
    const details = document.getElementById('complete-teacher-details');
    if (!details) return;
    if (!details.contains(e.target)) {
      toggleCompleteTeacherSubjectsDropdown(false);
      toggleCompleteTeacherClassesDropdown(false);
    }
  });

  async function handleCompleteProfileLogout() {
    const btn = document.getElementById('btn-complete-logout');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Đang đăng xuất…';
    }
    try {
      await fetch('/api/core/auth/logout/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'X-CSRFToken': csrfToken(),
          'X-Requested-With': 'XMLHttpRequest',
        },
      });
    } catch (e) {
      // ignore network errors
    } finally {
      window.location.href = '/login';
    }
  }

  // Expose to window for inline onclick handlers
  window.toggleCompleteTeacherSubjectsDropdown = toggleCompleteTeacherSubjectsDropdown;
  window.toggleCompleteTeacherClassesDropdown = toggleCompleteTeacherClassesDropdown;
  window.switchCompleteGradeTab = switchCompleteGradeTab;
  window.toggleSelectCompleteCurrentGrade = toggleSelectCompleteCurrentGrade;
  window.filterCompleteTeacherSubjects = filterCompleteTeacherSubjects;
  window.filterCompleteTeacherClasses = filterCompleteTeacherClasses;
  window.clearCompleteTeacherSubjects = clearCompleteTeacherSubjects;
  window.clearCompleteTeacherClasses = clearCompleteTeacherClasses;
  window.removeCompleteTeacherSubject = removeCompleteTeacherSubject;
  window.removeCompleteTeacherClass = removeCompleteTeacherClass;
  window.syncCompleteTeacherSubjectSelection = syncCompleteTeacherSubjectSelection;
  window.syncCompleteTeacherClassSelection = syncCompleteTeacherClassSelection;
  window.handleCompleteProfileLogout = handleCompleteProfileLogout;

  const initCompleteProfileForm = () => {
    const form = document.getElementById('public-complete-profile-form');
    if (!form) return;

    const studentCard = document.getElementById('card-role-student');
    const teacherCard = document.getElementById('card-role-teacher');
    const studentSection = document.getElementById('section-student-fields');
    const teacherSection = document.getElementById('section-teacher-fields');
    const gradeSelect = document.getElementById('complete-student-grade');
    const classSelect = document.getElementById('complete-student-class');
    const submitBtn = document.getElementById('btn-submit-profile');

    const updateRoleView = (isStudent) => {
      studentCard?.classList.toggle('selected', isStudent);
      teacherCard?.classList.toggle('selected', !isStudent);
      if (studentSection) studentSection.hidden = !isStudent;
      if (teacherSection) teacherSection.hidden = isStudent;
      if (!isStudent) {
        renderCompleteTeacherSubjectsGrid();
      }
      if (window.lucide) {
        lucide.createIcons();
      }
    };

    studentCard?.addEventListener('click', () => {
      const radio = studentCard.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
      updateRoleView(true);
    });

    teacherCard?.addEventListener('click', () => {
      const radio = teacherCard.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
      updateRoleView(false);
    });

    // Student grade filtering
    gradeSelect?.addEventListener('change', () => {
      const grade = gradeSelect.value;
      if (!classSelect) return;
      Array.from(classSelect.options).forEach(opt => {
        if (!opt.value) { opt.hidden = false; return; }
        opt.hidden = Boolean(grade && opt.dataset.grade !== grade);
      });
      const currentOpt = classSelect.selectedOptions[0];
      if (currentOpt && currentOpt.hidden) classSelect.value = '';
    });

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      setMessage('complete-profile-error', '', false);

      const isStudent = form.querySelector('input[name="role_type"]:checked')?.value === 'student';
      const payload = {
        role_type: isStudent ? 'student' : 'teacher',
      };

      if (isStudent) {
        const name = document.getElementById('complete-student-name')?.value.trim();
        const gradeVal = gradeSelect?.value;
        const className = classSelect?.value;
        if (!name) {
          setMessage('complete-profile-error', 'Vui lòng nhập họ và tên học sinh.');
          return;
        }
        if (!gradeVal || !className) {
          setMessage('complete-profile-error', 'Vui lòng chọn khối và lớp học chính thức.');
          return;
        }
        payload.full_name = name;
        payload.grade = parseInt(gradeVal, 10);
        payload.class_name = className;
        payload.dob = document.getElementById('complete-student-dob')?.value || null;
        payload.gender = document.getElementById('complete-student-gender')?.value || 'Nam';
        payload.phone = document.getElementById('complete-student-phone')?.value.trim() || '';
        payload.student_code = document.getElementById('complete-student-code')?.value.trim() || '';
      } else {
        const name = document.getElementById('complete-teacher-name')?.value.trim();
        const phone = document.getElementById('complete-teacher-phone')?.value.trim();
        const subjects = getSelectedCompleteTeacherSubjects();
        const classes = getSelectedCompleteTeacherClasses();

        if (!name) {
          setMessage('complete-profile-error', 'Vui lòng nhập họ và tên giáo viên.');
          return;
        }
        if (!phone) {
          setMessage('complete-profile-error', 'Vui lòng nhập số điện thoại liên lạc của giáo viên.');
          return;
        }
        if (subjects.length === 0) {
          setMessage('complete-profile-error', 'Vui lòng chọn ít nhất một môn giảng dạy trong danh sách xổ xuống.');
          toggleCompleteTeacherSubjectsDropdown(true);
          return;
        }
        payload.full_name = name;
        payload.phone = phone;
        payload.subjects = subjects;
        payload.subject = subjects.join(', ');
        payload.teaching_classes = classes;
        payload.teacher_type = 'gvbm';
        payload.teacher_code = document.getElementById('complete-teacher-code')?.value.trim() || '';
      }

      withLoading(submitBtn, 'Gửi hồ sơ đăng ký Quản trị viên xét duyệt', async () => {
        try {
          const { response, data } = await request('/api/core/auth/complete-profile/', payload, form);
          if (!response.ok) throw new Error(errorText(data));
          window.location.href = data.redirect_url || '/pending-approval';
        } catch (err) {
          setMessage('complete-profile-error', err.name === 'AbortError' ? 'Kết nối đang chậm. Vui lòng thử lại.' : err.message);
        }
      });
    });
  };

    const initPendingApprovalActions = () => {
    const logoutBtn = document.getElementById('btn-pending-logout');
    if (!logoutBtn) return;
    logoutBtn.addEventListener('click', async () => {
      logoutBtn.disabled = true;
      logoutBtn.textContent = 'Đang đăng xuất…';
      try {
        await fetch('/api/core/auth/logout/', {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'X-CSRFToken': csrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
          },
        });
      } catch (e) {
        // ignore network error on logout
      } finally {
        window.location.href = '/login';
      }
    });
  };

document.addEventListener('DOMContentLoaded', () => {
    initPublicMenu();
    initPublicAccount();
    initPublicHomeSessionSync();
    initRegistrationForm();
    initLoginForm();
    initPendingConfirmation();
    initForgotForm();
    initResetForm();
    initCompleteProfileForm();
    initPendingApprovalActions();
  });
})();
