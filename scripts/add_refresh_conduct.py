import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. Update templates/index.html
p_html = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\templates\index.html'
with open(p_html, 'r', encoding='utf-8') as f:
    html_text = f.read()

old_html_pattern = """            <div class="flex items-center gap-2">

              <button onclick="openRulesReferenceModal()" class="px-3.5 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs rounded-xl flex items-center space-x-1.5 transition">"""

new_html_pattern = """            <div class="flex items-center gap-2 flex-wrap">

              <button type="button" onclick="refreshConductData()" id="btn-refresh-conduct" class="px-3.5 py-2 bg-blue-50 hover:bg-blue-100 text-brand-700 font-semibold text-xs rounded-xl flex items-center space-x-1.5 transition shadow-2xs" title="Làm mới danh sách nề nếp">

                <i data-lucide="refresh-cw" class="w-4 h-4 text-brand-600"></i>

                <span>Làm mới</span>

              </button>

              <button onclick="openRulesReferenceModal()" class="px-3.5 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs rounded-xl flex items-center space-x-1.5 transition">"""

assert old_html_pattern in html_text, "old_html_pattern not found in templates/index.html"
html_text = html_text.replace(old_html_pattern, new_html_pattern, 1)

with open(p_html, 'w', encoding='utf-8') as f:
    f.write(html_text)

print("[OK] Updated templates/index.html with refresh button in Quản lý nề nếp")

# 2. Update static/app.js
p_js = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js'
with open(p_js, 'r', encoding='utf-8') as f:
    js_text = f.read()

old_js_pattern = """// 2. CONDUCT & VIOLATIONS MODULE

// ==========================================

async function loadConductViolations() {"""

new_js_pattern = """// 2. CONDUCT & VIOLATIONS MODULE

// ==========================================

async function refreshConductData(showNotification = true) {

  const btn = document.getElementById('btn-refresh-conduct');

  const icon = btn ? btn.querySelector('[data-lucide="refresh-cw"], svg') : null;

  if (btn) btn.disabled = true;

  if (icon) icon.classList.add('animate-spin');



  try {

    await loadConductViolations();

    if (showNotification && typeof showToast === 'function') {

      showToast('Đã làm mới danh sách nề nếp thành công.', 'success');

    }

  } catch (err) {

    if (showNotification && typeof showToast === 'function') {

      showToast('Có lỗi khi làm mới dữ liệu nề nếp.', 'error');

    }

  } finally {

    if (btn) btn.disabled = false;

    if (icon) icon.classList.remove('animate-spin');

    if (typeof lucide !== 'undefined' && lucide.createIcons) {

      lucide.createIcons();

    }

  }

}

window.refreshConductData = refreshConductData;



async function loadConductViolations() {"""

assert old_js_pattern in js_text, "old_js_pattern not found in static/app.js"
js_text = js_text.replace(old_js_pattern, new_js_pattern, 1)

with open(p_js, 'w', encoding='utf-8') as f:
    f.write(js_text)

print("[OK] Updated static/app.js with refreshConductData function")
