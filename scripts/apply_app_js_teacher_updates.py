import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"
js_path = os.path.join(BASE_DIR, "static", "app.js")

with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

# Normalize line endings
js = js.replace("\r\n", "\n")

# ==============================================================================
# 1. ADD openModal and closeModal RIGHT AFTER showToast
# ==============================================================================
show_toast_end = """  setTimeout(() => {

    toast.classList.add('opacity-0', 'translate-y-2');

    setTimeout(() => toast.remove(), 300);

  }, 4000);

}"""

modal_helpers = """  setTimeout(() => {

    toast.classList.add('opacity-0', 'translate-y-2');

    setTimeout(() => toast.remove(), 300);

  }, 4000);

}

// ==============================================================================
// GLOBAL MODAL HELPERS (ROBUST OPEN / CLOSE)
// ==============================================================================
function openModal(modalId) {
  const modal = typeof modalId === 'string' ? document.getElementById(modalId) : modalId;
  if (!modal) return;
  modal.classList.remove('hidden');
  document.body.classList.add('overflow-hidden');
  if (window.lucide) {
    try { lucide.createIcons(); } catch(e) {}
  }
}

function closeModal(modalId) {
  const modal = typeof modalId === 'string' ? document.getElementById(modalId) : modalId;
  if (!modal) return;
  modal.classList.add('hidden');
  const anyOpenModal = document.querySelector('.fixed.inset-0:not(.hidden)');
  if (!anyOpenModal) {
    document.body.classList.remove('overflow-hidden');
  }
}

window.openModal = openModal;
window.closeModal = closeModal;"""

if "function openModal(" not in js:
    if show_toast_end in js:
        js = js.replace(show_toast_end, modal_helpers)
        print("SUCCESS: Added openModal and closeModal to static/app.js")
    else:
        print("ERROR: show_toast_end target not found in static/app.js")
else:
    print("INFO: openModal already exists in static/app.js")


# ==============================================================================
# 2. UPDATE selectTeacherClass TO ALSO LOAD TEACHERS
# ==============================================================================
target_promise_all = """  // Load students and feedbacks concurrently

  await Promise.all([

    fetchClassStudents(found.id),

    fetchClassFeedbacks(found.id)

  ]);"""

replacement_promise_all = """  // Load students, feedbacks, and teachers concurrently

  await Promise.all([

    fetchClassStudents(found.id),

    fetchClassFeedbacks(found.id),

    loadClassTeachers(found.id)

  ]);"""

if target_promise_all in js:
    js = js.replace(target_promise_all, replacement_promise_all)
    print("SUCCESS: Updated selectTeacherClass Promise.all to loadClassTeachers")
else:
    print("INFO: Promise.all in selectTeacherClass already updated or different")


# ==============================================================================
# 3. UPDATE switchTeacherSubTab TO SUPPORT 'teachers'
# ==============================================================================
old_switch_subtab = """function switchTeacherSubTab(tabName) {

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

}"""

new_switch_subtab = """function switchTeacherSubTab(tabName) {
  const btnRoster = document.getElementById('subtab-btn-roster');
  const btnFeedbacks = document.getElementById('subtab-btn-feedbacks');
  const btnTeachers = document.getElementById('subtab-btn-teachers');
  const paneRoster = document.getElementById('subtab-pane-roster');
  const paneFeedbacks = document.getElementById('subtab-pane-feedbacks');
  const paneTeachers = document.getElementById('subtab-pane-teachers');

  const activeBtnClass = 'px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-white text-slate-900 shadow-sm transition-all flex items-center gap-1.5';
  const inactiveBtnClass = 'px-3.5 py-1.5 text-xs font-semibold rounded-lg text-slate-600 hover:text-slate-900 transition-all flex items-center gap-1.5';

  if (tabName === 'roster') {
    if (btnRoster) btnRoster.className = activeBtnClass;
    if (btnFeedbacks) btnFeedbacks.className = inactiveBtnClass;
    if (btnTeachers) btnTeachers.className = inactiveBtnClass;
    if (paneRoster) paneRoster.classList.remove('hidden');
    if (paneFeedbacks) paneFeedbacks.classList.add('hidden');
    if (paneTeachers) paneTeachers.classList.add('hidden');
  } else if (tabName === 'feedbacks') {
    if (btnRoster) btnRoster.className = inactiveBtnClass;
    if (btnFeedbacks) btnFeedbacks.className = activeBtnClass;
    if (btnTeachers) btnTeachers.className = inactiveBtnClass;
    if (paneRoster) paneRoster.classList.add('hidden');
    if (paneFeedbacks) paneFeedbacks.classList.remove('hidden');
    if (paneTeachers) paneTeachers.classList.add('hidden');
    renderTeacherFeedbacks();
  } else if (tabName === 'teachers') {
    if (btnRoster) btnRoster.className = inactiveBtnClass;
    if (btnFeedbacks) btnFeedbacks.className = inactiveBtnClass;
    if (btnTeachers) btnTeachers.className = activeBtnClass;
    if (paneRoster) paneRoster.classList.add('hidden');
    if (paneFeedbacks) paneFeedbacks.classList.add('hidden');
    if (paneTeachers) paneTeachers.classList.remove('hidden');
    loadClassTeachers();
  }

  if (window.lucide) lucide.createIcons();
}"""

if old_switch_subtab in js:
    js = js.replace(old_switch_subtab, new_switch_subtab)
    print("SUCCESS: Updated switchTeacherSubTab to support 'teachers' subtab")
else:
    print("INFO: old_switch_subtab not found or already updated")


# ==============================================================================
# 4. UPDATE openAssignHomeroomModal & ADD onAssignHomeroomClassSelectChange
# ==============================================================================
old_open_assign_hr = """async function openAssignHomeroomModal(classId = null) {
  if (classId) {
    const target = (teacherAssignedClasses || []).find(c => c.id === classId);
    if (target) {
      activeTeacherClass = target;
      await selectTeacherClass(classId);
    }
  }

  if (!activeTeacherClass) return;

  const modal = document.getElementById('modal-assign-homeroom-teacher');

  if (!modal) return;



  document.getElementById('assign-homeroom-class-id').value = activeTeacherClass.id;

  document.getElementById('assign-homeroom-confirm-replace').value = 'false';

  document.getElementById('assign-homeroom-class-name').textContent = `Lớp ${activeTeacherClass.name} (Khối ${activeTeacherClass.grade})`;

  

  const currentGvcnText = activeTeacherClass.homeroom_teacher_name && activeTeacherClass.homeroom_teacher_name !== 'Chưa phân công'

    ? activeTeacherClass.homeroom_teacher_name

    : 'Chưa phân công GVCN';

  document.getElementById('assign-homeroom-current-gvcn').textContent = currentGvcnText;



  const conflictBox = document.getElementById('assign-homeroom-conflict-box');

  if (conflictBox) conflictBox.classList.add('hidden');

  const confirmCb = document.getElementById('assign-homeroom-confirm-checkbox');

  if (confirmCb) confirmCb.checked = false;



  const notesInput = document.getElementById('assign-homeroom-notes');

  if (notesInput) notesInput.value = '';



  await loadEligibleTeachersForHomeroom();



  openModal('modal-assign-homeroom-teacher');

  if (window.lucide) lucide.createIcons();

}"""

new_open_assign_hr = """async function openAssignHomeroomModal(classId = null) {
  if (classId) {
    const target = (teacherAssignedClasses || []).find(c => c.id === classId);
    if (target) {
      activeTeacherClass = target;
      await selectTeacherClass(classId);
    }
  }

  if (!activeTeacherClass && teacherAssignedClasses && teacherAssignedClasses.length > 0) {
    activeTeacherClass = teacherAssignedClasses[0];
    await selectTeacherClass(activeTeacherClass.id);
  }

  if (!activeTeacherClass) {
    showToast('Vui lòng chọn một lớp học trước khi phân công.', 'warning');
    return;
  }

  const modal = document.getElementById('modal-assign-homeroom-teacher');
  if (!modal) return;

  const classSelect = document.getElementById('assign-homeroom-class-select');
  if (classSelect && teacherAssignedClasses && teacherAssignedClasses.length > 0) {
    classSelect.innerHTML = teacherAssignedClasses.map(c => 
      `<option value="${c.id}" ${c.id === activeTeacherClass.id ? 'selected' : ''}>Lớp ${escapeHtml(c.name)} (Khối ${c.grade})</option>`
    ).join('');
  }

  document.getElementById('assign-homeroom-class-id').value = activeTeacherClass.id;
  document.getElementById('assign-homeroom-confirm-replace').value = 'false';
  document.getElementById('assign-homeroom-class-name').textContent = `Lớp ${activeTeacherClass.name} (Khối ${activeTeacherClass.grade})`;

  const currentGvcnText = activeTeacherClass.homeroom_teacher_name && activeTeacherClass.homeroom_teacher_name !== 'Chưa phân công'
    ? activeTeacherClass.homeroom_teacher_name
    : 'Chưa phân công GVCN';
  document.getElementById('assign-homeroom-current-gvcn').textContent = currentGvcnText;

  const conflictBox = document.getElementById('assign-homeroom-conflict-box');
  if (conflictBox) conflictBox.classList.add('hidden');
  const confirmCb = document.getElementById('assign-homeroom-confirm-checkbox');
  if (confirmCb) confirmCb.checked = false;

  const notesInput = document.getElementById('assign-homeroom-notes');
  if (notesInput) notesInput.value = '';

  await loadEligibleTeachersForHomeroom();

  openModal('modal-assign-homeroom-teacher');
  if (window.lucide) lucide.createIcons();
}

async function onAssignHomeroomClassSelectChange(newClassId) {
  if (!newClassId) return;
  const numId = Number(newClassId);
  const target = (teacherAssignedClasses || []).find(c => c.id === numId);
  if (target) {
    activeTeacherClass = target;
    await selectTeacherClass(numId);
  }
  document.getElementById('assign-homeroom-class-id').value = activeTeacherClass.id;
  document.getElementById('assign-homeroom-class-name').textContent = `Lớp ${activeTeacherClass.name} (Khối ${activeTeacherClass.grade})`;
  const currentGvcnText = activeTeacherClass.homeroom_teacher_name && activeTeacherClass.homeroom_teacher_name !== 'Chưa phân công'
    ? activeTeacherClass.homeroom_teacher_name
    : 'Chưa phân công GVCN';
  document.getElementById('assign-homeroom-current-gvcn').textContent = currentGvcnText;
  const conflictBox = document.getElementById('assign-homeroom-conflict-box');
  if (conflictBox) conflictBox.classList.add('hidden');
  const confirmCb = document.getElementById('assign-homeroom-confirm-checkbox');
  if (confirmCb) confirmCb.checked = false;
  await loadEligibleTeachersForHomeroom();
}"""

if old_open_assign_hr in js:
    js = js.replace(old_open_assign_hr, new_open_assign_hr)
    print("SUCCESS: Updated openAssignHomeroomModal and added onAssignHomeroomClassSelectChange")
else:
    print("INFO: old_open_assign_hr not found or already updated")


# ==============================================================================
# 5. SYNC loadClassTeachers IN handleAssignHomeroomSubmit AND handleRevokeHomeroom
# ==============================================================================
target_hr_submit_sync = """    renderTeacherClassesBar();

  } catch (err) {"""

replacement_hr_submit_sync = """    renderTeacherClassesBar();
    await loadClassTeachers(activeTeacherClass.id);

  } catch (err) {"""

if target_hr_submit_sync in js:
    js = js.replace(target_hr_submit_sync, replacement_hr_submit_sync)
    print("SUCCESS: Added loadClassTeachers sync to handleAssignHomeroomSubmit")

target_hr_revoke_sync = """    renderTeacherClassesBar();

  } catch (err) {"""

if target_hr_revoke_sync in js:
    js = js.replace(target_hr_revoke_sync, replacement_hr_submit_sync)
    print("SUCCESS: Added loadClassTeachers sync to handleRevokeHomeroom")


# ==============================================================================
# 6. ADD loadClassTeachers, openAssignSubjectTeacherModal, etc.
# ==============================================================================
class_teachers_module_code = """
// ==============================================================================
// ĐỘI NGŨ GIÁO VIÊN (GVCN & BỘ MÔN) QUẢN TRỊ TRỰC TIẾP
// ==============================================================================
const SUBJECT_MAP = {
  'TOAN': 'Toán học',
  'VAN': 'Ngữ văn',
  'ANH': 'Tiếng Anh',
  'LY': 'Vật lý',
  'HOA': 'Hóa học',
  'SINH': 'Sinh học',
  'SU': 'Lịch sử',
  'DIA': 'Địa lý',
  'GDCD': 'GDCD/GDKT&PL',
  'TIN': 'Tin học',
  'CN': 'Công nghệ',
  'TD': 'Giáo dục thể chất',
  'QP': 'Giáo dục QP-AN',
  'AM_NHAC': 'Âm nhạc',
  'MY_THUAT': 'Mỹ thuật',
  'HDTN': 'Hoạt động trải nghiệm'
};

let currentClassTeachersData = null;
let eligibleTeachersCache = [];

async function loadClassTeachers(classId = null) {
  const targetId = classId || (activeTeacherClass ? activeTeacherClass.id : null);
  if (!targetId) return;

  const paneTitle = document.getElementById('teachers-pane-class-title');
  const gvcnName = document.getElementById('class-gvcn-name');
  const gvcnDetails = document.getElementById('class-gvcn-details');
  const gvcnStatus = document.getElementById('class-gvcn-status-badge');
  const revokeBtn = document.getElementById('btn-pane-revoke-gvcn');
  const tbody = document.getElementById('class-subject-teachers-tbody');
  const emptyState = document.getElementById('class-subject-teachers-empty');
  const countBadge = document.getElementById('subject-teachers-count-badge');
  const tabBadge = document.getElementById('class-teacher-count-badge');

  try {
    const res = await fetch(`/api/conduct/teacher-classes/${targetId}/assigned-teachers/`);
    if (!res.ok) throw new Error('Không thể tải danh sách giáo viên phụ trách.');
    const data = await res.json();
    currentClassTeachersData = data;

    if (paneTitle && data.class_name) {
      paneTitle.textContent = `Đội ngũ giáo viên - Lớp ${data.class_name} (Khối ${data.grade})`;
    }

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
    }

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error('Error loading class teachers:', err);
    if (gvcnName) gvcnName.textContent = 'Lỗi tải dữ liệu';
  }
}

async function openAssignSubjectTeacherModal() {
  if (!activeTeacherClass && teacherAssignedClasses && teacherAssignedClasses.length > 0) {
    activeTeacherClass = teacherAssignedClasses[0];
    await selectTeacherClass(activeTeacherClass.id);
  }

  if (!activeTeacherClass) {
    showToast('Vui lòng chọn một lớp học trước khi phân công.', 'warning');
    return;
  }

  const modal = document.getElementById('modal-assign-subject-teacher');
  if (!modal) return;

  // Populate class dropdown
  const classSelect = document.getElementById('assign-subject-class-select');
  if (classSelect && teacherAssignedClasses && teacherAssignedClasses.length > 0) {
    classSelect.innerHTML = teacherAssignedClasses.map(c => 
      `<option value="${c.id}" ${c.id === activeTeacherClass.id ? 'selected' : ''}>Lớp ${escapeHtml(c.name)} (Khối ${c.grade})</option>`
    ).join('');
  }

  // Reset subject & teacher selects
  const subjectSelect = document.getElementById('assign-subject-code-select');
  if (subjectSelect) subjectSelect.value = '';

  const teacherSelect = document.getElementById('assign-subject-teacher-select');
  if (teacherSelect) teacherSelect.innerHTML = '<option value="">-- Chọn môn học trước để lọc giáo viên phù hợp --</option>';

  const conflictBox = document.getElementById('assign-subject-conflict-box');
  if (conflictBox) conflictBox.classList.add('hidden');

  // Load eligible teachers
  try {
    const res = await fetch('/api/conduct/teacher-classes/eligible-teachers/');
    if (res.ok) {
      eligibleTeachersCache = await res.json();
    }
  } catch(e) {
    console.error('Failed to load eligible teachers:', e);
  }

  openModal('modal-assign-subject-teacher');
  if (window.lucide) lucide.createIcons();
}

function onAssignSubjectChange(subjectCode) {
  const teacherSelect = document.getElementById('assign-subject-teacher-select');
  const conflictBox = document.getElementById('assign-subject-conflict-box');
  const conflictMsg = document.getElementById('assign-subject-conflict-msg');
  if (!teacherSelect) return;

  if (!subjectCode) {
    teacherSelect.innerHTML = '<option value="">-- Chọn môn học trước để lọc giáo viên phù hợp --</option>';
    if (conflictBox) conflictBox.classList.add('hidden');
    return;
  }

  // Check if subject is already assigned in this class
  if (currentClassTeachersData && currentClassTeachersData.subject_teachers) {
    const existing = currentClassTeachersData.subject_teachers.find(st => st.subject === subjectCode);
    if (existing) {
      if (conflictBox) conflictBox.classList.remove('hidden');
      if (conflictMsg) conflictMsg.textContent = `Môn này hiện đã được phân công cho Thầy/Cô ${existing.teacher_name || existing.full_name}. Lưu phân công mới sẽ thay thế giáo viên này.`;
    } else {
      if (conflictBox) conflictBox.classList.add('hidden');
    }
  }

  if (eligibleTeachersCache.length === 0) {
    teacherSelect.innerHTML = '<option value="">-- Không có giáo viên nào --</option>';
    return;
  }

  // Partition matching teachers vs others
  const matching = [];
  const others = [];

  eligibleTeachersCache.forEach(t => {
    const tSubject = (t.subject || '').toUpperCase();
    if (tSubject === subjectCode.toUpperCase() || tSubject.includes(subjectCode.toUpperCase())) {
      matching.push(t);
    } else {
      others.push(t);
    }
  });

  let optionsHtml = '<option value="">-- Chọn Giáo viên phụ trách --</option>';
  if (matching.length > 0) {
    optionsHtml += `<optgroup label="Giáo viên chuyên môn ${SUBJECT_MAP[subjectCode] || subjectCode}">`;
    matching.forEach(t => {
      optionsHtml += `<option value="${t.id}">${escapeHtml(t.full_name || t.username)} [Đúng chuyên môn]</option>`;
    });
    optionsHtml += `</optgroup>`;
  }

  if (others.length > 0) {
    optionsHtml += `<optgroup label="Tất cả giáo viên khác">`;
    others.forEach(t => {
      const subjectNote = t.subject ? ` (Môn ${t.subject})` : '';
      optionsHtml += `<option value="${t.id}">${escapeHtml(t.full_name || t.username)}${subjectNote}</option>`;
    });
    optionsHtml += `</optgroup>`;
  }

  teacherSelect.innerHTML = optionsHtml;
}

async function handleAssignSubjectTeacherSubmit(event) {
  event.preventDefault();

  const classSelect = document.getElementById('assign-subject-class-select');
  const classId = classSelect ? classSelect.value : (activeTeacherClass ? activeTeacherClass.id : null);
  const subjectCode = document.getElementById('assign-subject-code-select')?.value;
  const teacherId = document.getElementById('assign-subject-teacher-select')?.value;
  const submitBtn = document.getElementById('btn-submit-assign-subject');

  if (!classId) {
    showToast('Vui lòng chọn lớp học.', 'warning');
    return;
  }
  if (!subjectCode) {
    showToast('Vui lòng chọn môn học.', 'warning');
    return;
  }
  if (!teacherId) {
    showToast('Vui lòng chọn giáo viên phụ trách.', 'warning');
    return;
  }

  try {
    if (submitBtn) submitBtn.disabled = true;

    const res = await fetch(`/api/conduct/teacher-classes/${classId}/assign-subject-teacher/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify({
        teacher_id: parseInt(teacherId, 10),
        subject: subjectCode
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Lỗi khi phân công giáo viên bộ môn.');

    showToast(data.message || 'Phân công Giáo viên Bộ môn thành công!', 'success');
    closeModal('modal-assign-subject-teacher');
    await loadClassTeachers(Number(classId));
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

async function removeSubjectTeacher(assignmentId) {
  if (!activeTeacherClass) return;
  if (!confirm('Bạn có chắc chắn muốn thu hồi phân công giáo viên môn này?')) return;

  try {
    const res = await fetch(`/api/conduct/teacher-classes/${activeTeacherClass.id}/remove-subject-teacher/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify({
        assignment_id: assignmentId
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Lỗi khi thu hồi phân công.');

    showToast(data.message || 'Đã thu hồi phân công giáo viên bộ môn.', 'success');
    await loadClassTeachers(activeTeacherClass.id);
  } catch (err) {
    showToast(err.message, 'error');
  }
}
"""

if "function loadClassTeachers(" not in js:
    # Append class_teachers_module_code before window exports
    window_export_target = "window.closeReviewModal = closeReviewModal;"
    if window_export_target in js:
        js = js.replace(window_export_target, class_teachers_module_code + "\n\n" + window_export_target)
        print("SUCCESS: Added loadClassTeachers and subject assignment module to static/app.js")
    else:
        js += "\n\n" + class_teachers_module_code
        print("SUCCESS: Appended loadClassTeachers module to static/app.js")
else:
    print("INFO: loadClassTeachers already exists in static/app.js")


# ==============================================================================
# 7. ADD WINDOW EXPORTS
# ==============================================================================
exports_additions = """
window.openModal = openModal;
window.closeModal = closeModal;
window.openAssignHomeroomModal = openAssignHomeroomModal;
window.onAssignHomeroomClassSelectChange = onAssignHomeroomClassSelectChange;
window.handleAssignHomeroomSubmit = handleAssignHomeroomSubmit;
window.handleRevokeHomeroom = handleRevokeHomeroom;
window.revokeHomeroomTeacher = handleRevokeHomeroom;
window.switchTeacherSubTab = switchTeacherSubTab;
window.loadClassTeachers = loadClassTeachers;
window.openAssignSubjectTeacherModal = openAssignSubjectTeacherModal;
window.onAssignSubjectChange = onAssignSubjectChange;
window.handleAssignSubjectTeacherSubmit = handleAssignSubjectTeacherSubmit;
window.removeSubjectTeacher = removeSubjectTeacher;
"""

if "window.loadClassTeachers = loadClassTeachers;" not in js:
    js += "\n" + exports_additions
    print("SUCCESS: Exported new teacher assignment functions to window")
else:
    print("INFO: Window exports already present")

with open(js_path, "w", encoding="utf-8") as f:
    f.write(js)
print("Finished updating static/app.js")
