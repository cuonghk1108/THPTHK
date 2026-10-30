with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\templates\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update tab-conduct header buttons
target1 = """            <div class="flex items-center gap-2">
              <button onclick="openQuickViolationModal()" class="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs rounded-xl shadow-sm flex items-center space-x-1.5 transition">
                <i data-lucide="plus" class="w-4 h-4"></i>
                <span>Ghi nhận vi phạm mới</span>
              </button>
              <button onclick="exportViolationsExcel()" class="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl flex items-center space-x-1.5 transition">
                <i data-lucide="download" class="w-4 h-4 text-emerald-600"></i>
                <span>Xuất Excel</span>
              </button>
            </div>"""

replacement1 = """            <div class="flex items-center gap-2">
              <button onclick="openRulesReferenceModal()" class="px-3.5 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs rounded-xl flex items-center space-x-1.5 transition">
                <i data-lucide="book-open" class="w-4 h-4 text-indigo-600"></i>
                <span>Quy tắc trừ điểm</span>
              </button>
              <button onclick="openQuickViolationModal()" class="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs rounded-xl shadow-sm flex items-center space-x-1.5 transition">
                <i data-lucide="plus" class="w-4 h-4"></i>
                <span>Ghi nhận vi phạm mới</span>
              </button>
              <button onclick="exportViolationsExcel()" class="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl flex items-center space-x-1.5 transition">
                <i data-lucide="download" class="w-4 h-4 text-emerald-600"></i>
                <span>Xuất Excel</span>
              </button>
            </div>"""

# 2. Update tab-competition header buttons
target2 = """            <div class="flex flex-wrap items-center gap-2">
              <button onclick="recalculateScores()" id="btn-recalculate-score" class="px-3.5 py-2 bg-blue-50 hover:bg-blue-100 text-brand-700 font-semibold text-xs rounded-xl flex items-center space-x-1.5 transition">
                <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
                <span>Tính lại tự động</span>
              </button>"""

replacement2 = """            <div class="flex flex-wrap items-center gap-2">
              <button onclick="openRulesReferenceModal()" class="px-3.5 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs rounded-xl flex items-center space-x-1.5 transition">
                <i data-lucide="book-open" class="w-3.5 h-3.5 text-indigo-600"></i>
                <span>Quy tắc trừ điểm</span>
              </button>
              <button onclick="recalculateScores()" id="btn-recalculate-score" class="px-3.5 py-2 bg-blue-50 hover:bg-blue-100 text-brand-700 font-semibold text-xs rounded-xl flex items-center space-x-1.5 transition">
                <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
                <span>Tính lại tự động</span>
              </button>"""

# 3. Update modal-quick-violation rule select & preview box
target3 = """        <div>
          <label class="block font-semibold text-slate-700 mb-1">3. Lỗi vi phạm nội quy <span class="text-rose-500">*</span></label>
          <select id="modal-violation-rule" required class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-brand-500">
            <option value="">-- Chọn lỗi vi phạm --</option>
          </select>
        </div>"""

replacement3 = """        <div>
          <div class="flex items-center justify-between mb-1">
            <label class="block font-semibold text-slate-700">3. Lỗi vi phạm nội quy <span class="text-rose-500">*</span></label>
            <button type="button" onclick="openRulesReferenceModal()" class="text-brand-600 hover:text-brand-700 text-[11px] font-semibold flex items-center gap-1">
              <i data-lucide="book-open" class="w-3.5 h-3.5"></i>
              <span>Tra cứu quy tắc (-đ)</span>
            </button>
          </div>
          <select id="modal-violation-rule" required onchange="updateViolationPointsPreview()" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-brand-500">
            <option value="">-- Chọn lỗi vi phạm --</option>
          </select>
        </div>

        <!-- Live preview of points deduction -->
        <div id="violation-preview-box" class="hidden p-3 bg-rose-50/80 border border-rose-200/80 rounded-xl space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="font-semibold text-rose-900 flex items-center gap-1.5">
              <i data-lucide="alert-circle" class="w-4 h-4 text-rose-600"></i>
              <span>Xem trước điểm thi đua áp dụng</span>
            </span>
            <span id="preview-rule-badge" class="px-2 py-0.5 rounded-full font-mono font-bold text-xs bg-rose-600 text-white">-5.00đ</span>
          </div>
          <div class="text-[11px] text-rose-800 flex items-center justify-between">
            <span>Điểm hiện tại của lớp: <b id="preview-current-score" class="font-mono">100.00</b></span>
            <span>Sau khi trừ: <b id="preview-projected-score" class="font-mono text-rose-700">95.00</b></span>
          </div>
        </div>"""

# 4. Add modal-conduct-rules-lookup right before mobile navigation
target4 = """  <!-- ========================================== -->
  <!-- MOBILE BOTTOM NAVIGATION (CHO ĐIỆN THOẠI) -->
  <!-- ========================================== -->"""

replacement4 = """  <!-- ========================================== -->
  <!-- MODAL: TRA CỨU QUY TẮC TRỪ ĐIỂM CHÍNH THỨC -->
  <!-- ========================================== -->
  <div id="modal-conduct-rules-lookup" class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm hidden flex items-center justify-center p-3 sm:p-4">
    <div class="bg-white w-full max-w-4xl max-h-[90vh] rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col text-xs">
      <!-- Modal Header -->
      <div class="px-5 py-3.5 bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white flex items-center justify-between shrink-0">
        <div class="flex items-center space-x-2.5">
          <div class="w-8 h-8 rounded-xl bg-white/10 flex items-center justify-center text-yellow-300">
            <i data-lucide="book-open" class="w-4 h-4"></i>
          </div>
          <div>
            <h3 class="font-bold text-sm text-white">Quy tắc trừ điểm thi đua & nền nếp</h3>
            <p class="text-[11px] text-blue-200 font-normal">Hệ thống 46 quy định nền nếp chính thức · Trường THPT Hương Khê</p>
          </div>
        </div>
        <button type="button" onclick="closeRulesReferenceModal()" class="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 text-blue-200 hover:text-white flex items-center justify-center transition" aria-label="Đóng">&times;</button>
      </div>

      <!-- Search & Category Filters -->
      <div class="p-3.5 bg-slate-50 border-b border-slate-200 space-y-2.5 shrink-0">
        <div class="flex flex-col sm:flex-row items-center gap-2.5">
          <div class="relative flex-1 w-full">
            <i data-lucide="search" class="w-4 h-4 text-slate-400 absolute left-3 top-2.5"></i>
            <input type="text" id="rules-filter-search" oninput="filterRulesReferenceTable()" placeholder="Tìm kiếm theo mã (TT01, SH01, GT01, KL01...), tên vi phạm hoặc điểm trừ..." class="w-full bg-white border border-slate-300 rounded-xl pl-9 pr-4 py-2 text-xs focus:ring-2 focus:ring-brand-500 focus:outline-none">
          </div>
          <div class="flex items-center gap-2 text-xs shrink-0 text-slate-500">
            <span id="rules-filter-count-badge" class="font-semibold text-brand-700 bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-200">Hiển thị: 46 / 46 quy định</span>
          </div>
        </div>

        <!-- Category Pills -->
        <div class="flex items-center gap-1.5 overflow-x-auto pb-1" id="rules-category-chips">
          <!-- Dynamically populated or rendered -->
        </div>
      </div>

      <!-- Rules Table Content -->
      <div class="overflow-y-auto flex-1 p-3.5">
        <div class="overflow-x-auto rounded-xl border border-slate-200 shadow-xs">
          <table class="w-full text-left text-xs border-collapse">
            <thead class="bg-slate-100 text-slate-700 font-bold uppercase text-[10px] tracking-wider sticky top-0 z-10 border-b border-slate-200">
              <tr>
                <th class="py-2.5 px-3 w-12 text-center">STT</th>
                <th class="py-2.5 px-3 w-20">Mã quy định</th>
                <th class="py-2.5 px-3">Hành vi vi phạm nội quy</th>
                <th class="py-2.5 px-3 w-44">Nhóm nội quy</th>
                <th class="py-2.5 px-3 w-24 text-center">Điểm trừ</th>
                <th class="py-2.5 px-3 w-28 text-center">Mức độ</th>
                <th class="py-2.5 px-3 w-24 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody id="rules-reference-tbody" class="divide-y divide-slate-100 bg-white">
              <!-- Populated by JavaScript -->
            </tbody>
          </table>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="px-5 py-3 bg-slate-50 border-t border-slate-200 flex flex-wrap items-center justify-between gap-2 shrink-0">
        <div class="flex items-center gap-2.5 text-[11px] text-slate-500">
          <span class="inline-flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> -3đ (Nhẹ)</span>
          <span class="inline-flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span> -5đ (Trung bình)</span>
          <span class="inline-flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-orange-500"></span> -10đ (Nghiêm trọng)</span>
          <span class="inline-flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-rose-600"></span> -15đ, -20đ (Rất nghiêm trọng)</span>
        </div>
        <button type="button" onclick="closeRulesReferenceModal()" class="px-4 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold rounded-xl transition">Đóng</button>
      </div>
    </div>
  </div>

  <!-- ========================================== -->
  <!-- MOBILE BOTTOM NAVIGATION (CHO ĐIỆN THOẠI) -->
  <!-- ========================================== -->"""

content_norm = content.replace('\r\n', '\n')
target1_norm = target1.replace('\r\n', '\n')
replacement1_norm = replacement1.replace('\r\n', '\n')
target2_norm = target2.replace('\r\n', '\n')
replacement2_norm = replacement2.replace('\r\n', '\n')
target3_norm = target3.replace('\r\n', '\n')
replacement3_norm = replacement3.replace('\r\n', '\n')
target4_norm = target4.replace('\r\n', '\n')
replacement4_norm = replacement4.replace('\r\n', '\n')

assert target1_norm in content_norm, "Target 1 not found"
content_norm = content_norm.replace(target1_norm, replacement1_norm, 1)

assert target2_norm in content_norm, "Target 2 not found"
content_norm = content_norm.replace(target2_norm, replacement2_norm, 1)

assert target3_norm in content_norm, "Target 3 not found"
content_norm = content_norm.replace(target3_norm, replacement3_norm, 1)

assert target4_norm in content_norm, "Target 4 not found"
content_norm = content_norm.replace(target4_norm, replacement4_norm, 1)

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\templates\index.html', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content_norm.replace('\n', '\r\n'))

print("Updated templates/index.html successfully!")
