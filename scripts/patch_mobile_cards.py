import os, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_JS_PATH = os.path.join(BASE_DIR, 'static', 'app.js')

with open(APP_JS_PATH, 'r', encoding='utf-8') as f:
    js = f.read()

target = """  // Mobile Cards
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
          Nhận xét
        </button>
      `;
    }

    const mobileNameHtml = (isStudent && !isSelf)
      ? `<span class="font-bold text-slate-900 text-sm">${escapeHtml(s.full_name)}</span>`
      : `<button type="button" onclick="openStudentProfileModal(${s.id})" class="font-bold text-slate-900 text-sm hover:text-blue-600 text-left">${escapeHtml(s.full_name)}</button>`;"""

repl = """  // Mobile Cards
  mobileList.innerHTML = students.map((s, idx) => {
    const isSelf = isStudent && ((s.student_code && s.student_code.trim().toLowerCase() === myStudentCode) || (s.id && s.id === myStudentId));
    const isMonitor = Boolean(s.is_class_monitor || (activeTeacherClass && activeTeacherClass.monitor_id === s.id));
    const mobileMonitorBadge = isMonitor
      ? `<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 ml-1" title="Lớp trưởng"><i data-lucide="crown" class="w-3 h-3 text-amber-600"></i> LT</span>`
      : '';

    let mobileMonitorBtn = '';
    if (!isStudent && activeTeacherClass && activeTeacherClass.can_assign_monitor) {
      if (isMonitor) {
        mobileMonitorBtn = `
          <button type="button" onclick="confirmRemoveMonitor(${s.id}, '${escapeHtml(s.full_name)}')" class="px-2.5 py-1.5 text-xs font-semibold rounded-lg text-amber-700 bg-amber-50 border border-amber-200">
            Hủy LT
          </button>
        `;
      } else {
        mobileMonitorBtn = `
          <button type="button" onclick="confirmAssignMonitor(${s.id}, '${escapeHtml(s.full_name)}')" class="px-2.5 py-1.5 text-xs font-semibold rounded-lg text-slate-600 bg-slate-50 border border-slate-200">
            Phân LT
          </button>
        `;
      }
    }

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
        ${mobileMonitorBtn}
        <button type="button" onclick="openSendFeedbackModal(${s.id}, ${activeTeacherClass.id}, '${escapeHtml(s.full_name)}', '${escapeHtml(activeTeacherClass.name)}')" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 text-white">
          Nhận xét
        </button>
      `;
    }

    const mobileNameHtml = (isStudent && !isSelf)
      ? `<div class="flex items-center flex-wrap gap-1"><span class="font-bold text-slate-900 text-sm">${escapeHtml(s.full_name)}</span>${mobileMonitorBadge}</div>`
      : `<div class="flex items-center flex-wrap gap-1"><button type="button" onclick="openStudentProfileModal(${s.id})" class="font-bold text-slate-900 text-sm hover:text-blue-600 text-left">${escapeHtml(s.full_name)}</button>${mobileMonitorBadge}</div>`;"""

if target in js:
    js = js.replace(target, repl, 1)
    with open(APP_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(js)
    print("SUCCESS: Updated mobile cards in static/app.js")
else:
    print("FAILED: Target not found")
