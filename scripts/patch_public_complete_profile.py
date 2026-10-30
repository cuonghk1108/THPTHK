import os

BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"
public_js_path = os.path.join(BASE_DIR, "static", "public.js")

with open(public_js_path, "r", encoding="utf-8") as f:
    content = f.read()

# Verify existing initCompleteProfileForm
old_code_marker = "  const initCompleteProfileForm = () => {"
if old_code_marker not in content:
    print("ERROR: old_code_marker not found in static/public.js")
    exit(1)

# Let's inspect how DOMContentLoaded looks at the bottom
old_dom_listener = """document.addEventListener('DOMContentLoaded', () => {
    initPublicMenu();
    initPublicAccount();
    initPublicHomeSessionSync();
    initRegistrationForm();
    initLoginForm();
    initPendingConfirmation();
    initForgotForm();
    initResetForm();
  });
})();"""

new_dom_listener = """document.addEventListener('DOMContentLoaded', () => {
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
})();"""

# New complete profile code:
complete_profile_code = """
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
"""

# Replace from `  const initCompleteProfileForm = () => {` up to `  const initPendingApprovalActions = () => {`
idx_start = content.find(old_code_marker)
idx_pending = content.find("  const initPendingApprovalActions = () => {")

if idx_start == -1 or idx_pending == -1:
    print(f"ERROR finding slice: idx_start={idx_start}, idx_pending={idx_pending}")
    exit(1)

content_new = content[:idx_start] + complete_profile_code + "\n  " + content[idx_pending:]

# Now replace DOMContentLoaded
content_new_norm = content_new.replace("\r\n", "\n")
old_dom_listener_norm = old_dom_listener.replace("\r\n", "\n")
new_dom_listener_norm = new_dom_listener.replace("\r\n", "\n")

if old_dom_listener_norm in content_new_norm:
    content_new_norm = content_new_norm.replace(old_dom_listener_norm, new_dom_listener_norm)
    print("SUCCESS: Updated DOMContentLoaded with initCompleteProfileForm and initPendingApprovalActions")
else:
    print("WARNING: Could not find exact old_dom_listener_norm")

with open(public_js_path, "w", encoding="utf-8") as f:
    f.write(content_new_norm)

print("SUCCESS: static/public.js updated successfully")
