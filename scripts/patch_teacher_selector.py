# -*- coding: utf-8 -*-
import sys
import os

html_path = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\templates\index.html'
js_path = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\public.js'

# ==========================================
# 1. UPDATE TEMPLATES/INDEX.HTML
# ==========================================
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read().replace('\r\n', '\n')

start_tag = '<!-- DYNAMIC TEACHER SUBJECTS & CLASSES SELECTION -->'
end_tag = '<!-- DYNAMIC DEPARTMENT -->'

start_idx = html_content.find(start_tag)
end_idx = html_content.find(end_tag)

if start_idx == -1 or end_idx == -1:
    print('ERROR: start_tag or end_tag not found in index.html!')
    sys.exit(1)

new_html_block = """<!-- DYNAMIC TEACHER SUBJECTS & CLASSES SELECTION -->
            <div id="register-teacher-details" class="auth-field space-y-3" hidden>
              <!-- 1. MULTI-SUBJECT SELECTION (NHÃ NHẶN, GỌN GÀNG, DỄ THƯƠNG) -->
              <div class="relative">
                <div class="flex items-center justify-between mb-1">
                  <label class="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                    <i data-lucide="sparkles" class="w-3.5 h-3.5 text-blue-500"></i>
                    <span>Môn giảng dạy</span> <span style="color:#ef4444;">*</span>
                  </label>
                  <span id="register-subject-count-badge" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                    0 môn đã chọn
                  </span>
                </div>

                <!-- Cute Trigger Box -->
                <button type="button" id="btn-toggle-subjects-dropdown" onclick="toggleTeacherSubjectsDropdown()" class="w-full min-h-[42px] px-3 py-1.5 bg-white border border-slate-300 hover:border-blue-400 focus:border-blue-500 rounded-xl text-xs flex items-center justify-between cursor-pointer transition text-left shadow-2xs group">
                  <div id="register-subjects-trigger-content" class="flex flex-wrap items-center gap-1 flex-1 py-0.5 overflow-hidden">
                    <span id="register-subjects-summary-text" class="text-slate-400 font-normal">✨ Bấm chọn môn giảng dạy (1 hoặc nhiều môn)...</span>
                  </div>
                  <div class="flex items-center gap-1.5 shrink-0 ml-1.5">
                    <span id="btn-clear-subjects-quick" onclick="event.stopPropagation(); clearTeacherSubjects();" class="hidden text-slate-400 hover:text-rose-600 p-0.5 rounded-full hover:bg-slate-100 transition text-sm leading-none font-bold" title="Xóa tất cả">&times;</span>
                    <i data-lucide="chevron-down" id="icon-subjects-chevron" class="w-4 h-4 text-slate-400 group-hover:text-blue-500 transition-transform"></i>
                  </div>
                </button>

                <!-- Floating Cute Popover Menu -->
                <div id="register-subjects-dropdown-container" class="hidden absolute left-0 right-0 top-full mt-1.5 z-40 bg-white/98 backdrop-blur-md border border-blue-100 rounded-2xl shadow-xl p-3 space-y-2.5 animate-in fade-in zoom-in-95 duration-150">
                  <div class="flex items-center justify-between gap-2 pb-1.5 border-b border-slate-100">
                    <div class="relative flex-1">
                      <i data-lucide="search" class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5"></i>
                      <input type="text" id="filter-subjects-input" oninput="filterTeacherSubjects(this.value)" placeholder="Tìm nhanh môn học..." class="w-full pl-8 pr-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-none focus:bg-white focus:border-blue-400 transition">
                    </div>
                    <button type="button" onclick="clearTeacherSubjects()" class="text-[11px] font-semibold text-slate-500 hover:text-rose-600 px-2 py-1 rounded-lg hover:bg-rose-50 transition">Xóa chọn</button>
                  </div>

                  <!-- Cute Chip Grid -->
                  <div id="subjects-checkboxes-grid" class="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto p-0.5">
                    <!-- Populated dynamically with cute rounded chips -->
                  </div>

                  <!-- Footer Bar -->
                  <div class="flex items-center justify-between pt-1 border-t border-slate-100 text-[11px]">
                    <span class="text-slate-500 font-medium" id="register-subjects-footer-count">Đã chọn: 0 môn</span>
                    <button type="button" onclick="toggleTeacherSubjectsDropdown(false)" class="px-3.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold shadow-2xs transition">Xong</button>
                  </div>
                </div>
              </div>

              <!-- 2. MULTI-CLASS SELECTION (NHÃ NHẶN, CHIA THEO KHỐI GỌN GÀNG) -->
              <div class="relative">
                <div class="flex items-center justify-between mb-1">
                  <label class="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                    <i data-lucide="layers" class="w-3.5 h-3.5 text-indigo-600"></i>
                    <span>Lớp giảng dạy</span> <span style="color:#ef4444;">*</span>
                  </label>
                  <span id="register-classes-count-badge" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                    0 lớp đã chọn
                  </span>
                </div>

                <!-- Cute Trigger Box -->
                <button type="button" id="btn-toggle-classes-dropdown" onclick="toggleTeacherClassesDropdown()" class="w-full min-h-[42px] px-3 py-1.5 bg-white border border-slate-300 hover:border-indigo-400 focus:border-indigo-500 rounded-xl text-xs flex items-center justify-between cursor-pointer transition text-left shadow-2xs group">
                  <div id="register-classes-trigger-content" class="flex flex-wrap items-center gap-1 flex-1 py-0.5 overflow-hidden">
                    <span id="register-classes-summary-text" class="text-slate-400 font-normal">🏫 Bấm chọn các lớp giảng dạy theo khối...</span>
                  </div>
                  <div class="flex items-center gap-1.5 shrink-0 ml-1.5">
                    <span id="btn-clear-classes-quick" onclick="event.stopPropagation(); clearTeacherClasses();" class="hidden text-slate-400 hover:text-rose-600 p-0.5 rounded-full hover:bg-slate-100 transition text-sm leading-none font-bold" title="Xóa tất cả">&times;</span>
                    <i data-lucide="chevron-down" id="icon-classes-chevron" class="w-4 h-4 text-slate-400 group-hover:text-indigo-500 transition-transform"></i>
                  </div>
                </button>

                <!-- Floating Cute Popover Menu -->
                <div id="register-classes-dropdown-container" class="hidden absolute left-0 right-0 top-full mt-1.5 z-40 bg-white/98 backdrop-blur-md border border-indigo-100 rounded-2xl shadow-xl p-3 space-y-2.5 animate-in fade-in zoom-in-95 duration-150">
                  <div class="flex items-center justify-between gap-2 pb-1.5 border-b border-slate-100">
                    <div class="relative flex-1">
                      <i data-lucide="search" class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5"></i>
                      <input type="text" id="filter-classes-input" oninput="filterTeacherClasses(this.value)" placeholder="Tìm nhanh lớp (VD: 10A1, 11A...)..." class="w-full pl-8 pr-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-none focus:bg-white focus:border-indigo-400 transition">
                    </div>
                    <button type="button" onclick="clearTeacherClasses()" class="text-[11px] font-semibold text-slate-500 hover:text-rose-600 px-2 py-1 rounded-lg hover:bg-rose-50 transition">Xóa chọn</button>
                  </div>

                  <!-- Segmented Grade Tabs -->
                  <div class="flex items-center justify-between gap-1.5 bg-slate-100/90 p-1 rounded-xl">
                    <div class="flex items-center gap-1">
                      <button type="button" onclick="switchRegisterGradeTab(10)" id="reg-grade-tab-10" class="px-2.5 py-1 rounded-lg text-xs font-bold bg-white text-indigo-700 shadow-xs transition flex items-center gap-1">
                        <span>Khối 10</span>
                        <span id="reg-grade-count-10" class="hidden text-[10px] px-1.5 py-0.2 rounded-full bg-indigo-100 text-indigo-800 font-extrabold">0</span>
                      </button>
                      <button type="button" onclick="switchRegisterGradeTab(11)" id="reg-grade-tab-11" class="px-2.5 py-1 rounded-lg text-xs font-bold text-slate-600 hover:text-slate-900 transition flex items-center gap-1">
                        <span>Khối 11</span>
                        <span id="reg-grade-count-11" class="hidden text-[10px] px-1.5 py-0.2 rounded-full bg-indigo-100 text-indigo-800 font-extrabold">0</span>
                      </button>
                      <button type="button" onclick="switchRegisterGradeTab(12)" id="reg-grade-tab-12" class="px-2.5 py-1 rounded-lg text-xs font-bold text-slate-600 hover:text-slate-900 transition flex items-center gap-1">
                        <span>Khối 12</span>
                        <span id="reg-grade-count-12" class="hidden text-[10px] px-1.5 py-0.2 rounded-full bg-indigo-100 text-indigo-800 font-extrabold">0</span>
                      </button>
                    </div>
                    <button type="button" onclick="toggleSelectCurrentGrade()" id="btn-toggle-select-current-grade" class="text-[11px] font-bold text-indigo-600 hover:text-indigo-800 px-2 py-0.5 rounded-lg hover:bg-white transition shrink-0">
                      + Chọn cả Khối 10
                    </button>
                  </div>

                  <!-- Grade Class Panels (only active grade panel shown) -->
                  <div class="max-h-48 overflow-y-auto p-1">
                    <!-- Khối 10 -->
                    <div id="teacher-classes-grid-10" class="grid grid-cols-4 sm:grid-cols-6 gap-1.5">
                      {% for item in school_classes %}{% if item.grade == 10 %}
                        <label class="class-choice-pill flex items-center justify-center p-1.5 bg-slate-50 hover:bg-blue-50 border border-slate-200 rounded-lg cursor-pointer text-xs font-semibold text-slate-700 transition select-none text-center">
                          <input type="checkbox" name="teacher_classes" value="{{ item.name }}" data-grade="10" onchange="syncTeacherClassSelection()" class="hidden">
                          <span>{{ item.name }}</span>
                        </label>
                      {% endif %}{% endfor %}
                    </div>

                    <!-- Khối 11 -->
                    <div id="teacher-classes-grid-11" class="hidden grid grid-cols-4 sm:grid-cols-6 gap-1.5">
                      {% for item in school_classes %}{% if item.grade == 11 %}
                        <label class="class-choice-pill flex items-center justify-center p-1.5 bg-slate-50 hover:bg-emerald-50 border border-slate-200 rounded-lg cursor-pointer text-xs font-semibold text-slate-700 transition select-none text-center">
                          <input type="checkbox" name="teacher_classes" value="{{ item.name }}" data-grade="11" onchange="syncTeacherClassSelection()" class="hidden">
                          <span>{{ item.name }}</span>
                        </label>
                      {% endif %}{% endfor %}
                    </div>

                    <!-- Khối 12 -->
                    <div id="teacher-classes-grid-12" class="hidden grid grid-cols-4 sm:grid-cols-6 gap-1.5">
                      {% for item in school_classes %}{% if item.grade == 12 %}
                        <label class="class-choice-pill flex items-center justify-center p-1.5 bg-slate-50 hover:bg-purple-50 border border-slate-200 rounded-lg cursor-pointer text-xs font-semibold text-slate-700 transition select-none text-center">
                          <input type="checkbox" name="teacher_classes" value="{{ item.name }}" data-grade="12" onchange="syncTeacherClassSelection()" class="hidden">
                          <span>{{ item.name }}</span>
                        </label>
                      {% endif %}{% endfor %}
                    </div>
                  </div>

                  <!-- Footer Bar -->
                  <div class="flex items-center justify-between pt-1 border-t border-slate-100 text-[11px]">
                    <span class="text-slate-500 font-medium" id="register-classes-footer-count">Đã chọn: 0 lớp</span>
                    <button type="button" onclick="toggleTeacherClassesDropdown(false)" class="px-3.5 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold shadow-2xs transition">Xong</button>
                  </div>
                </div>
              </div>
            </div>

            """

html_content = html_content[:start_idx] + new_html_block + html_content[end_idx:]

with open(html_path, 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(html_content)

print('Updated templates/index.html with refined teacher selectors!')

# ==========================================
# 2. UPDATE STATIC/PUBLIC.JS
# ==========================================
with open(js_path, 'r', encoding='utf-8') as f:
    js_content = f.read().replace('\r\n', '\n')

start_fn = 'function renderTeacherSubjectsGrid() {'
end_fn = 'const initRegistrationForm = () => {'

s_idx = js_content.find(start_fn)
e_idx = js_content.find(end_fn)

if s_idx == -1 or e_idx == -1:
    print('ERROR: start_fn or end_fn not found in public.js!')
    sys.exit(1)

new_js_block = """let currentRegGradeTab = 10;

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

"""

js_content = js_content[:s_idx] + new_js_block + js_content[e_idx:]

with open(js_path, 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(js_content)

print('Updated static/public.js with cute, refined popover controllers!')
