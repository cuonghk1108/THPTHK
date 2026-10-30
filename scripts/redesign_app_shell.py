"""
Script to upgrade App Header, Sidebar, and Competition Tab in templates/index.html.
Preserves all IDs and event bindings.
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
index_path = BASE / "templates" / "index.html"
content = index_path.read_text(encoding="utf-8")

# 1. UPGRADE APP HEADER
header_start_str = "<!-- 2. TOP HEADER (KHI ĐÃ ĐĂNG NHẬP) -->"
header_end_str = "<!-- 3. MAIN WRAPPER (SIDEBAR + CONTENT) -->"

h_start = content.find(header_start_str)
h_end = content.find(header_end_str)

if h_start == -1 or h_end == -1:
    print("ERROR: Could not find header boundary")
    sys.exit(1)

NEW_HEADER = """<!-- 2. TOP HEADER (KHI ĐÃ ĐĂNG NHẬP) -->
  <header class="app-header">
    <div class="app-header-inner">
      <!-- School Logo & Branding -->
      <a class="app-brand" href="/dashboard" aria-label="HK Student Hub Dashboard">
        <div class="app-brand-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
            <path d="M6 12v5c3 3 9 3 12 0v-5"/>
          </svg>
        </div>
        <div>
          <div class="app-brand-name">{{ school_name }}</div>
          <div class="app-brand-sub">HK Student Hub · Quản trị học đường</div>
        </div>
      </a>

      <!-- Academic Year & Server Live Clock -->
      <div class="app-header-meta">
        {% if current_year %}<span class="app-year-badge">Năm học: {{ current_year }}</span>{% endif %}
        <span id="current-datetime" class="app-datetime" aria-live="off"></span>
      </div>

      <!-- Action Items & User Controls -->
      <div class="app-header-actions">
        <!-- Notification Bell Dropdown -->
        <button type="button" onclick="toggleNotificationDropdown()" class="app-notif-btn" title="Thông báo hệ thống" aria-label="Xem thông báo" aria-haspopup="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          <span id="notif-badge" class="app-notif-badge hidden">0</span>
        </button>

        <div id="notif-dropdown" class="app-notif-dropdown hidden" role="region" aria-label="Danh sách thông báo">
          <div class="app-notif-header">
            <span>Thông báo mới</span>
            <button type="button" onclick="markAllNotificationsRead()" class="app-notif-mark-all">Đã đọc tất cả</button>
          </div>
          <div id="notif-list" class="app-notif-list" aria-live="polite">
            <div class="p-4 text-center text-slate-400 text-xs">Đang tải thông báo...</div>
          </div>
        </div>

        <!-- User Role & Display Badge -->
        <div id="user-badge" class="app-user-badge">
          <div id="user-avatar-text" class="app-user-avatar">HK</div>
          <img id="user-avatar-image" class="app-user-avatar-img hidden" alt="Ảnh đại diện">
          <div class="text-left hidden sm:block">
            <div id="user-display-name" class="app-user-name">Tài khoản</div>
            <div id="user-role-text" class="app-user-role"></div>
          </div>
        </div>

        <!-- Safe Logout Button -->
        <button type="button" onclick="handleLogout()" title="Đăng xuất an toàn" class="app-logout-btn">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          <span class="hidden md:inline">Đăng xuất</span>
        </button>

        <!-- Mobile Drawer Menu Toggle -->
        <button type="button" onclick="toggleMobileMenu()" class="app-mobile-menu-btn md:hidden" aria-label="Mở danh mục điều hướng">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg>
        </button>
      </div>
    </div>
  </header>

  """

content = content[:h_start] + NEW_HEADER + content[h_end:]
print("App header upgraded!")

# 2. UPGRADE TAB COMPETITION CONTENT
comp_start_str = '<!-- TAB 3: COMPETITION (THI ĐUA CHI ĐOÀN) -->'
comp_end_str = '<!-- TAB 4: ALERTS & GVCN INTERVENTIONS -->'

c_start = content.find(comp_start_str)
c_end = content.find(comp_end_str)

if c_start == -1 or c_end == -1:
    print("ERROR: Could not find competition tab boundary")
    sys.exit(1)

NEW_COMPETITION = """<!-- TAB 3: COMPETITION (THI ĐUA CHI ĐOÀN) -->
      <section id="tab-competition" class="tab-pane hidden space-y-6">
        
        <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-200/80">
          
          <!-- Header: Title & Actions -->
          <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
            <div>
              <div class="flex items-center gap-2">
                <h2 class="text-xl font-bold text-slate-900 tracking-tight">Bảng xếp hạng thi đua Chi đoàn</h2>
                <span id="period-lock-indicator" class="badge bg-slate-100 text-slate-600">Đang mở</span>
                <span id="period-type-badge" class="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-50 text-brand-700 border border-blue-200/60">Theo Tuần</span>
              </div>
              <p class="text-xs text-slate-500 mt-1" id="competition-period-title">
                Kỳ thi đua: Đang cập nhật...
              </p>
            </div>

            <!-- Action buttons -->
            <div class="flex flex-wrap items-center gap-2">
              <button onclick="recalculateScores()" id="btn-recalculate-score" class="px-3.5 py-2 bg-blue-50 hover:bg-blue-100 text-brand-700 font-semibold text-xs rounded-xl flex items-center space-x-1.5 transition">
                <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
                <span>Tính lại tự động</span>
              </button>
              
              <button onclick="toggleLockPeriod()" id="btn-lock-period" class="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl flex items-center space-x-1.5 transition">
                <i data-lucide="lock" class="w-3.5 h-3.5"></i>
                <span id="btn-lock-period-text">Chốt kết quả</span>
              </button>

              <button onclick="exportCompetitionExcel()" class="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-xl shadow-xs flex items-center space-x-1.5 transition">
                <i data-lucide="file-spreadsheet" class="w-3.5 h-3.5"></i>
                <span>Xuất Excel</span>
              </button>

              <button onclick="exportCompetitionPdf()" class="px-3.5 py-2 bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs rounded-xl shadow-xs flex items-center space-x-1.5 transition">
                <i data-lucide="file-text" class="w-3.5 h-3.5"></i>
                <span>Xuất PDF</span>
              </button>
            </div>
          </div>

          <!-- TIME NAVIGATION CONTROLS (QUAN TRỌNG: Academic Year, Type, Semester, Period) -->
          <div class="bg-slate-50/90 p-4 rounded-xl border border-slate-200/90 mb-5 flex flex-wrap items-center gap-3">
            <!-- 1. Năm học -->
            <label class="flex flex-col text-[11px] font-semibold text-slate-600 min-w-[150px]">
              <span class="mb-1">Năm học</span>
              <select id="comp-filter-academic-year" onchange="onAcademicYearFilterChange()" class="min-h-9 bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-xs font-normal text-slate-800 focus:outline-none focus:border-blue-500">
                <option value="">Chọn năm học</option>
              </select>
            </label>

            <!-- 2. Loại kỳ (Tuần / Tháng / Học kỳ) -->
            <div class="flex flex-col text-[11px] font-semibold text-slate-600">
              <span class="mb-1">Khung thi đua</span>
              <div class="inline-flex rounded-lg bg-slate-200/70 p-0.5 border border-slate-200">
                <button type="button" id="btn-comp-type-week" onclick="setCompetitionPeriodType('WEEK')" class="comp-type-btn px-3 py-1 text-xs font-semibold rounded-md bg-brand-900 text-white shadow-xs transition">Tuần</button>
                <button type="button" id="btn-comp-type-month" onclick="setCompetitionPeriodType('MONTH')" class="comp-type-btn px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-200 rounded-md transition">Tháng</button>
                <button type="button" id="btn-comp-type-semester" onclick="setCompetitionPeriodType('SEMESTER')" class="comp-type-btn px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-200 rounded-md transition">Học kỳ</button>
              </div>
            </div>

            <!-- 3. Học kỳ (Học kỳ I / Học kỳ II) -->
            <div id="comp-semester-wrapper" class="flex flex-col text-[11px] font-semibold text-slate-600 min-w-[160px]">
              <span class="mb-1">Học kỳ</span>
              <select id="comp-filter-semester" onchange="onCompetitionSemesterFilterChange()" class="min-h-9 bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-xs font-normal text-slate-800 focus:outline-none focus:border-blue-500">
                <option value="">Cả 2 học kỳ (35 tuần)</option>
                <option value="1">Học kỳ I (Tuần 1 - 18)</option>
                <option value="2">Học kỳ II (Tuần 19 - 35)</option>
              </select>
            </div>

            <!-- 4. Bộ chọn kỳ cụ thể -->
            <label class="flex flex-col text-[11px] font-semibold text-slate-600 flex-1 min-w-[220px]">
              <span class="mb-1">Chọn kỳ cụ thể</span>
              <select id="comp-filter-period" onchange="onPeriodFilterChange()" class="min-h-9 bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-xs font-normal text-slate-800 focus:outline-none focus:border-blue-500 font-medium">
                <option value="">Đang tải danh sách kỳ...</option>
              </select>
            </label>

            <!-- 5. Tìm kiếm chi đoàn -->
            <label class="flex flex-col text-[11px] font-semibold text-slate-600 min-w-[170px]">
              <span class="mb-1">Tìm chi đoàn</span>
              <input id="comp-search-input" oninput="debounceCompetitionSearch()" type="search" placeholder="Ví dụ: 10A1, 11A2..." class="min-h-9 bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-xs text-slate-800 focus:outline-none focus:border-blue-500">
            </label>
          </div>

          <!-- 6 KPI SUMMARY CARDS (đồng bộ với static/app.js) -->
          <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
            <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
              <span class="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">Tổng chi đoàn</span>
              <span id="comp-kpi-total-classes" class="text-base font-bold text-slate-900 block mt-1">--</span>
            </div>
            <div class="p-3 bg-amber-50/70 rounded-xl border border-amber-200/80">
              <span class="text-[10px] font-semibold text-amber-700 uppercase tracking-wider block">Đứng đầu (#1)</span>
              <span id="comp-kpi-top-class" class="text-xs font-bold text-amber-900 block mt-1 truncate">Chưa có</span>
              <span id="comp-kpi-top-score" class="text-[10px] text-amber-600 block">--</span>
            </div>
            <div class="p-3 bg-blue-50/70 rounded-xl border border-blue-200/80">
              <span class="text-[10px] font-semibold text-blue-700 uppercase tracking-wider block">Điểm cao nhất</span>
              <span id="comp-kpi-highest-score" class="text-base font-bold text-blue-900 block mt-1">--</span>
            </div>
            <div class="p-3 bg-emerald-50/70 rounded-xl border border-emerald-200/80">
              <span class="text-[10px] font-semibold text-emerald-700 uppercase tracking-wider block">Biến động hạng</span>
              <span id="comp-kpi-trend" class="text-xs font-bold text-emerald-900 block mt-1">--</span>
            </div>
            <div class="p-3 bg-rose-50/70 rounded-xl border border-rose-200/80">
              <span class="text-[10px] font-semibold text-rose-700 uppercase tracking-wider block">Lượt vi phạm</span>
              <span id="comp-kpi-violations" class="text-base font-bold text-rose-900 block mt-1">--</span>
            </div>
            <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
              <span id="comp-kpi-status" class="text-[10px] font-semibold text-slate-700 uppercase tracking-wider block truncate">Trạng thái</span>
              <span id="comp-kpi-updated-time" class="text-[10px] text-slate-500 block mt-1 truncate">Thời gian thực</span>
            </div>
          </div>

          <!-- Formula Explainer Banner -->
          <div class="p-3.5 bg-blue-50/60 rounded-xl border border-blue-100 text-xs text-brand-900 mb-5 flex items-start gap-3">
            <i data-lucide="info" class="w-4 h-4 text-brand-600 shrink-0 mt-0.5"></i>
            <div>
              <span class="font-bold">Công thức tính điểm thi đua chính thức:</span>
              <span> Điểm thi đua = <b>Điểm khởi đầu (100.0đ)</b> + <b>Tổng điểm cộng phong trào</b> − <b>Tổng điểm trừ (từ các vi phạm ĐÃ XÁC MINH)</b>. Giới hạn sàn: 0.0đ, trần: 150.0đ. Bản ghi vi phạm đang chờ xử lý sẽ không bị trừ điểm.</span>
            </div>
          </div>

          <!-- Grade Filter Tabs -->
          <div class="flex items-center space-x-2 border-b border-slate-200 pb-3 mb-4">
            <button onclick="filterCompetitionGrade('')" class="comp-grade-tab px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-brand-900 text-white">Toàn trường</button>
            <button onclick="filterCompetitionGrade(10)" class="comp-grade-tab px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100">Khối 10</button>
            <button onclick="filterCompetitionGrade(11)" class="comp-grade-tab px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100">Khối 11</button>
            <button onclick="filterCompetitionGrade(12)" class="comp-grade-tab px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100">Khối 12</button>
          </div>

          <!-- Competition Scores Table -->
          <div class="overflow-x-auto rounded-xl border border-slate-200/70">
            <table class="w-full text-left text-xs">
              <thead class="bg-slate-100/80 text-slate-700 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-200">
                <tr>
                  <th class="py-3 px-3 text-center w-16">Hạng</th>
                  <th class="py-3 px-3">Chi đoàn / Lớp</th>
                  <th class="py-3 px-3">Khối</th>
                  <th class="py-3 px-3">GVCN</th>
                  <th class="py-3 px-3 text-right">Điểm gốc</th>
                  <th class="py-3 px-3 text-right">Điểm cộng</th>
                  <th class="py-3 px-3 text-right text-rose-600">Điểm trừ</th>
                  <th class="py-3 px-3 text-right font-bold text-brand-900">Tổng điểm</th>
                  <th class="py-3 px-3 text-center">Số vi phạm</th>
                  <th class="py-3 px-3 text-center">Biến động</th>
                  <th class="py-3 px-3 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody id="competition-scores-tbody" class="divide-y divide-slate-100 bg-white">
                <tr><td colspan="11" class="text-center py-8 text-slate-400">Đang tải bảng điểm thi đua...</td></tr>
              </tbody>
            </table>
          </div>

        </div>

      </section>

      """

content = content[:c_start] + NEW_COMPETITION + content[c_end:]
print("Competition tab upgraded!")

index_path.write_text(content, encoding="utf-8")
print("Saved templates/index.html with upgraded Header and Competition Tab!")
