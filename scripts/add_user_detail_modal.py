import sys

with open('templates/index.html', 'rb') as f:
    text = f.read().decode('utf-8').replace('\r\n', '\n')

modal_html = '''  <!-- Modal: Xem chi tiết tài khoản & Lịch sử xét duyệt (User Detail Modal) -->
  <div id="modal-user-detail" class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm hidden flex items-center justify-center p-4">
    <div class="bg-white w-full max-w-xl rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col text-xs max-h-[90vh]">
      <!-- Header -->
      <div class="px-5 py-3.5 bg-slate-900 text-white flex items-center justify-between">
        <div class="flex items-center space-x-2.5">
          <div class="w-8 h-8 rounded-xl bg-purple-600/30 border border-purple-400/40 flex items-center justify-center text-purple-300 font-bold text-sm">
            <i data-lucide="user" class="w-4 h-4"></i>
          </div>
          <div>
            <h3 class="font-bold text-sm" id="detail-user-fullname">Hồ sơ người dùng</h3>
            <p class="text-[11px] text-slate-400 font-mono">@<span id="detail-user-username">username</span></p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span id="detail-user-status-badge"></span>
          <button type="button" onclick="closeUserDetailModal()" class="w-7 h-7 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white flex items-center justify-center text-lg leading-none transition">&times;</button>
        </div>
      </div>

      <!-- Body Scrollable -->
      <div class="p-5 space-y-4 overflow-y-auto">
        <!-- Grid Info -->
        <div class="grid grid-cols-2 gap-3 p-3.5 bg-slate-50 rounded-xl border border-slate-200">
          <div><span class="text-slate-500 block text-[10px] uppercase font-semibold">Email</span><span id="detail-user-email" class="font-medium text-slate-800 break-all">—</span></div>
          <div><span class="text-slate-500 block text-[10px] uppercase font-semibold">Số điện thoại</span><span id="detail-user-phone" class="font-medium text-slate-800">—</span></div>
          <div><span class="text-slate-500 block text-[10px] uppercase font-semibold">Vai trò hiện tại</span><span id="detail-user-role" class="font-bold text-purple-800">—</span></div>
          <div><span class="text-slate-500 block text-[10px] uppercase font-semibold">Vai trò yêu cầu ban đầu</span><span id="detail-user-req-role" class="font-medium text-slate-700">—</span></div>
          <div><span class="text-slate-500 block text-[10px] uppercase font-semibold">Lớp / Bộ môn / Đơn vị</span><span id="detail-user-dept" class="font-medium text-slate-800">—</span></div>
          <div><span class="text-slate-500 block text-[10px] uppercase font-semibold">Ngày đăng ký</span><span id="detail-user-date" class="font-medium text-slate-700">—</span></div>
        </div>

        <!-- Verification Info -->
        <div class="p-3 bg-amber-50/70 rounded-xl border border-amber-200">
          <span class="text-[10px] font-bold text-amber-900 uppercase block mb-1 flex items-center gap-1.5"><i data-lucide="badge-check" class="w-3.5 h-3.5 text-amber-600"></i> Thông tin xác minh / Ghi chú đăng ký</span>
          <p id="detail-user-verification" class="text-slate-700 text-xs leading-relaxed">—</p>
        </div>

        <!-- Approval Meta Box -->
        <div id="detail-approval-meta-box" class="p-3 bg-emerald-50/70 rounded-xl border border-emerald-200 hidden">
          <span class="text-[10px] font-bold text-emerald-900 uppercase block mb-0.5">Thông tin phê duyệt</span>
          <p id="detail-user-approved-meta" class="text-emerald-800 text-xs font-medium">—</p>
        </div>

        <!-- Rejection Meta Box -->
        <div id="detail-rejection-meta-box" class="p-3 bg-rose-50/70 rounded-xl border border-rose-200 hidden">
          <span class="text-[10px] font-bold text-rose-900 uppercase block mb-0.5">Lý do từ chối</span>
          <p id="detail-user-rejection-reason" class="text-rose-800 text-xs font-medium">—</p>
        </div>

        <!-- Internal Notes Box -->
        <div id="detail-internal-notes-box" class="p-3 bg-purple-50/70 rounded-xl border border-purple-200 hidden">
          <span class="text-[10px] font-bold text-purple-900 uppercase block mb-0.5">Ghi chú nội bộ Admin</span>
          <p id="detail-user-internal-notes" class="text-purple-900 text-xs font-medium">—</p>
        </div>

        <!-- History logs -->
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <span class="font-bold text-slate-800 flex items-center gap-1.5"><i data-lucide="history" class="w-3.5 h-3.5 text-slate-500"></i> Lịch sử xét duyệt & thay đổi</span>
            <span id="detail-history-count" class="badge bg-slate-100 text-slate-600 border border-slate-200 font-mono text-[10px]">0 sự kiện</span>
          </div>
          <div id="detail-user-history-list" class="space-y-1.5 max-h-40 overflow-y-auto"></div>
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="p-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
        <div id="detail-modal-admin-actions">
          <button type="button" id="btn-delete-user-detail" class="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl font-semibold transition flex items-center gap-1 shadow-sm">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i> Xóa tài khoản
          </button>
        </div>
        <div class="flex items-center gap-2">
          <button type="button" id="btn-approve-user-detail" class="px-3.5 py-1.5 bg-purple-700 hover:bg-purple-800 text-white rounded-xl font-semibold transition flex items-center gap-1 shadow-sm">
            <i data-lucide="user-check" class="w-3.5 h-3.5"></i> Duyệt / Đổi quyền
          </button>
          <button type="button" onclick="closeUserDetailModal()" class="px-3.5 py-1.5 bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 rounded-xl font-medium transition">Đóng</button>
        </div>
      </div>
    </div>
  </div>\n\n'''

target = '  <div id="modal-approve-role"'
assert target in text, 'target not found in templates/index.html'

if 'id="modal-user-detail"' not in text:
    text = text.replace(target, modal_html + target, 1)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Successfully added modal-user-detail into templates/index.html!')
