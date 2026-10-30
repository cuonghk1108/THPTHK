import os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

file_path = r'static/app.js'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update loadMetadata
load_meta_pat = r'(async function loadMetadata\(force = false\) \{.*?const \[classesRes, rulesRes\] = await Promise\.all\(\[classesPromise, rulesPromise\]\);).*?(?=\s*// Populate rules dropdown grouped by official categories)'

new_load_body = '''

    const classesData = await classesRes.json();
    classesCache = Array.isArray(classesData) ? classesData : (classesData.results || []);

    const rulesData = rulesRes ? await rulesRes.json() : [];
    rulesCache = Array.isArray(rulesData) ? rulesData : (rulesData.results || []);
    if (!Array.isArray(classesCache)) classesCache = [];
    if (!Array.isArray(rulesCache)) rulesCache = [];

    // Populate modal class dropdown & filter with natural sort
    if (typeof populateModalViolationClasses === 'function') {
      populateModalViolationClasses(document.getElementById('modal-violation-grade')?.value || '');
    }

    const filterClassSelect = document.getElementById('filter-conduct-class');
    if (filterClassSelect) {
      const sortedClasses = naturalSortClasses(classesCache);
      filterClassSelect.innerHTML = '<option value="">Tất cả các lớp</option>' +
        sortedClasses.map(c => `<option value="${c.id}">Lớp ${escapeHtml(c.name)} (Khối ${c.grade})</option>`).join('');
    }
    const studentApprovalClassSelect = document.getElementById('student-approval-class');
    if (studentApprovalClassSelect) {
      const sortedClasses = naturalSortClasses(classesCache);
      studentApprovalClassSelect.innerHTML = '<option value="">Tất cả lớp</option>' +
        sortedClasses.map(c => `<option value="${c.id}">Lớp ${escapeHtml(c.name)}</option>`).join('');
    }
'''

m1 = re.search(load_meta_pat, content, flags=re.DOTALL)
if not m1:
    print("ERROR: load_meta_pat not found!")
    sys.exit(1)

# Also update classesPromise to include ?all=true
part1 = m1.group(1).replace("fetch('/api/conduct/classes/')", "fetch('/api/conduct/classes/?all=true')")
content = content[:m1.start()] + part1 + new_load_body + content[m1.end():]
print("loadMetadata successfully patched.")

# 2. Add helper functions and update openQuickViolationModal
old_modal_funcs = r'function openQuickViolationModal\(\) \{.*?(?=function closeQuickViolationModal)'

new_modal_funcs = '''function naturalSortClasses(list) {
  if (!Array.isArray(list)) return [];
  return [...list].sort((a, b) => {
    const ga = Number(a.grade) || 0;
    const gb = Number(b.grade) || 0;
    if (ga !== gb) return ga - gb;
    const oa = Number(a.class_order) || 0;
    const ob = Number(b.class_order) || 0;
    if (oa !== ob) return oa - ob;
    return (a.name || '').localeCompare(b.name || '', undefined, { numeric: true, sensitivity: 'base' });
  });
}

function populateModalViolationClasses(filterGrade = '', selectedClassId = null) {
  const modalClassSelect = document.getElementById('modal-violation-class');
  const countBadge = document.getElementById('violation-class-count-badge');
  if (!modalClassSelect) return;

  const rawClasses = Array.isArray(classesCache) ? classesCache : [];
  const sortedAll = naturalSortClasses(rawClasses);

  let targetClasses = sortedAll;
  if (filterGrade !== '' && filterGrade !== null && filterGrade !== undefined) {
    targetClasses = sortedAll.filter(c => String(c.grade) === String(filterGrade));
  }

  if (countBadge) {
    countBadge.textContent = `${targetClasses.length} lớp`;
  }

  let html = '';
  if (filterGrade !== '' && filterGrade !== null && filterGrade !== undefined) {
    html += `<option value="">-- Chọn lớp học (${targetClasses.length} lớp) --</option>`;
    targetClasses.forEach(c => {
      const isSel = (selectedClassId && Number(selectedClassId) === Number(c.id));
      html += `<option value="${c.id}" ${isSel ? 'selected' : ''}>Lớp ${escapeHtml(c.name)} (Khối ${c.grade})</option>`;
    });
  } else {
    html += `<option value="">-- Chọn lớp trong toàn trường (${sortedAll.length} lớp) --</option>`;
    const grades = [10, 11, 12];
    grades.forEach(g => {
      const gClasses = sortedAll.filter(c => Number(c.grade) === g);
      if (gClasses.length > 0) {
        html += `<optgroup label="Khối ${g} (${gClasses.length} lớp)">`;
        gClasses.forEach(c => {
          const isSel = (selectedClassId && Number(selectedClassId) === Number(c.id));
          html += `<option value="${c.id}" ${isSel ? 'selected' : ''}>Lớp ${escapeHtml(c.name)}</option>`;
        });
        html += `</optgroup>`;
      }
    });
    const otherClasses = sortedAll.filter(c => ![10, 11, 12].includes(Number(c.grade)));
    if (otherClasses.length > 0) {
      html += `<optgroup label="Lớp khác (${otherClasses.length} lớp)">`;
      otherClasses.forEach(c => {
        const isSel = (selectedClassId && Number(selectedClassId) === Number(c.id));
        html += `<option value="${c.id}" ${isSel ? 'selected' : ''}>Lớp ${escapeHtml(c.name)}</option>`;
      });
      html += `</optgroup>`;
    }
  }

  modalClassSelect.innerHTML = html;

  if (selectedClassId && targetClasses.some(c => Number(c.id) === Number(selectedClassId))) {
    modalClassSelect.value = selectedClassId;
  }
}

function handleGradeChangeForViolation(grade) {
  const classSelect = document.getElementById('modal-violation-class');
  const prevClassId = classSelect ? classSelect.value : '';

  populateModalViolationClasses(grade, prevClassId);

  if (classSelect && classSelect.value !== prevClassId) {
    const studentSelect = document.getElementById('modal-violation-student');
    if (studentSelect) {
      studentSelect.innerHTML = '<option value="">-- Cả tập thể lớp --</option>';
    }
    const previewBox = document.getElementById('violation-preview-box');
    if (previewBox) previewBox.classList.add('hidden');
  }
}

function openQuickViolationModal() {
  if (currentUser && (currentUser.role === 'GVBM' || currentUser.is_gvbm) && !currentUser.is_admin && !currentUser.is_gvcn) {
    showToast('Giáo viên bộ môn chỉ có quyền gửi phản ánh nề nếp, không được ghi nhận vi phạm trừ điểm.', 'warning');
    openCreateReflectionModal();
    return;
  }
  const modal = document.getElementById('modal-quick-violation');
  activeViolationSubmissionKey = activeViolationSubmissionKey || createSubmissionKey();
  modal.classList.remove('hidden');
  document.getElementById('modal-violation-time').value = getLocalIsoString(new Date(Date.now() + serverTimeOffsetMs));

  const gradeSelect = document.getElementById('modal-violation-grade');
  if (gradeSelect) gradeSelect.value = '';

  if (!classesCache || classesCache.length === 0) {
    loadMetadata().then(() => {
      populateModalViolationClasses('');
    });
  } else {
    populateModalViolationClasses('');
  }

  const canDirect = canUserDeductDirectly();
  const submitButton = document.getElementById('modal-violation-submit-btn');
  const directNotice = document.getElementById('preview-direct-deduct-notice');
  const pendingNotice = document.getElementById('preview-pending-notice');
  if (submitButton) {
    if (canDirect) {
      submitButton.textContent = 'Xác nhận vi phạm và trừ điểm';
      submitButton.className = 'px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-sm transition';
      if (directNotice) directNotice.classList.remove('hidden');
      if (pendingNotice) pendingNotice.classList.add('hidden');
    } else {
      submitButton.textContent = 'Gửi bản ghi để xác minh';
      submitButton.className = 'px-5 py-2 bg-brand-600 hover:bg-brand-700 text-white font-bold rounded-xl shadow-sm transition';
      if (directNotice) directNotice.classList.add('hidden');
      if (pendingNotice) pendingNotice.classList.remove('hidden');
    }
  }

  const previewBox = document.getElementById('violation-preview-box');
  if (previewBox) previewBox.classList.add('hidden');

  lucide.createIcons();
}

'''

m2 = re.search(old_modal_funcs, content, flags=re.DOTALL)
if not m2:
    print("ERROR: old_modal_funcs not found!")
    sys.exit(1)

content = content[:m2.start()] + new_modal_funcs + content[m2.end():]
print("openQuickViolationModal successfully patched.")

# 3. Update openViolationModalForStudent to sync grade dropdown
old_open_for_student = r'function openViolationModalForStudent\(classId, studentId, studentName\) \{.*?openModal\(\'modal-quick-violation\'\);\s*\}'

new_open_for_student = '''function openViolationModalForStudent(classId, studentId, studentName) {
  if (!confirm(`Xác nhận chuyển sang lập biên bản vi phạm kỷ luật cho học sinh ${studentName}?`)) {
    return;
  }

  openQuickViolationModal();

  const classSelect = document.getElementById('modal-violation-class');
  const studentSelect = document.getElementById('modal-violation-student');
  const gradeSelect = document.getElementById('modal-violation-grade');

  const foundCls = (classesCache || []).find(c => Number(c.id) === Number(classId));
  const grade = foundCls ? String(foundCls.grade || '') : '';
  if (gradeSelect) gradeSelect.value = grade;
  populateModalViolationClasses(grade, classId);

  if (classSelect) {
    classSelect.value = classId;
    if (typeof handleClassChangeForStudents === 'function') {
      handleClassChangeForStudents(classId);
      setTimeout(() => {
        if (studentSelect) studentSelect.value = studentId;
      }, 300);
    } else if (studentSelect) {
      studentSelect.value = studentId;
    }
  }

  openModal('modal-quick-violation');
}'''

m3 = re.search(old_open_for_student, content, flags=re.DOTALL)
if not m3:
    print("ERROR: old_open_for_student not found!")
    sys.exit(1)

content = content[:m3.start()] + new_open_for_student + content[m3.end():]
print("openViolationModalForStudent successfully patched.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("ALL PATCHES APPLIED TO static/app.js!")
