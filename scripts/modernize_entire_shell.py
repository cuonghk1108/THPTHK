"""
Script to modernize the entire HK Student Hub Workspace (App Header, Sidebar, Design System, navigateTab).
Applies changes directly to Desktop files.
"""
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Xuan Cuong\Desktop\hk-student-hub")
INDEX_PATH = BASE_DIR / "templates" / "index.html"
APP_JS_PATH = BASE_DIR / "static" / "app.js"

# 1. NEW APP SHELL CSS
NEW_SHELL_CSS = """    /* ===== PREMIUM EDTECH APP SHELL (HEADER, SIDEBAR & WORKSPACE 2.0) ===== */
    .app-header {
      position: sticky;
      top: 0;
      z-index: 40;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border-bottom: 1px solid #e2e8f0;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }
    .app-header-inner {
      max-width: 1360px;
      margin: 0 auto;
      padding: 0 24px;
      height: 64px;
      display: flex;
      align-items: center;
      gap: 20px;
    }
    .app-brand {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;
      text-decoration: none;
      transition: opacity 0.15s ease;
    }
    .app-brand:hover {
      opacity: 0.92;
    }
    .app-brand-icon {
      width: 38px;
      height: 38px;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, #173b70 0%, #2563eb 100%);
      border-radius: 12px;
      color: #ffffff;
      box-shadow: 0 3px 8px rgba(37, 99, 235, 0.28);
    }
    .app-brand-name {
      font-size: 14.5px;
      font-weight: 850;
      color: #0f172a;
      letter-spacing: -0.02em;
      line-height: 1.2;
    }
    .app-brand-sub {
      font-size: 11px;
      color: #2563eb;
      font-weight: 650;
      margin-top: 1px;
    }
    .app-header-meta {
      flex: 1;
      display: flex;
      align-items: center;
      gap: 14px;
      justify-content: center;
    }
    .app-year-badge {
      font-size: 11.5px;
      font-weight: 700;
      color: #1e40af;
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      border-radius: 9999px;
      padding: 4px 14px;
      letter-spacing: 0.01em;
    }
    .app-datetime {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 12px;
      font-weight: 600;
      color: #64748b;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      padding: 4px 10px;
      border-radius: 8px;
    }
    .app-header-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
      position: relative;
    }
    .app-notif-btn {
      position: relative;
      width: 38px;
      height: 38px;
      display: grid;
      place-items: center;
      color: #475569;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.18s ease;
    }
    .app-notif-btn:hover {
      background: #eff6ff;
      color: #2563eb;
      border-color: #bfdbfe;
      transform: translateY(-1px);
    }
    .app-notif-badge {
      position: absolute;
      top: -2px;
      right: -2px;
      min-width: 18px;
      height: 18px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0 5px;
      background: #e11d48;
      color: #ffffff;
      font-size: 10px;
      font-weight: 800;
      border-radius: 9999px;
      line-height: 1;
      border: 2px solid #ffffff;
      box-shadow: 0 2px 5px rgba(225, 29, 72, 0.4);
    }
    .app-notif-dropdown {
      position: absolute;
      top: calc(100% + 10px);
      right: 0;
      z-index: 50;
      width: 350px;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      box-shadow: 0 16px 40px -10px rgba(15, 23, 42, 0.16);
      overflow: hidden;
      animation: edtechFadeIn 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .app-notif-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 16px;
      border-bottom: 1px solid #f1f5f9;
      font-size: 13.5px;
      font-weight: 800;
      color: #0f172a;
    }
    .app-notif-mark-all {
      font-size: 11.5px;
      color: #2563eb;
      background: transparent;
      border: 0;
      cursor: pointer;
      font-weight: 700;
    }
    .app-notif-mark-all:hover {
      text-decoration: underline;
    }
    .app-notif-list {
      max-height: 360px;
      overflow-y: auto;
    }
    .app-user-badge {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 4px 14px 4px 5px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 9999px;
      transition: all 0.18s ease;
      cursor: pointer;
    }
    .app-user-badge:hover {
      background: #f1f5f9;
      border-color: #cbd5e1;
    }
    .app-user-avatar {
      width: 30px;
      height: 30px;
      flex-shrink: 0;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, #173b70 0%, #2563eb 100%);
      color: #ffffff;
      border-radius: 50%;
      font-size: 11px;
      font-weight: 800;
      box-shadow: 0 2px 6px rgba(37, 99, 235, 0.25);
    }
    .app-user-avatar-img {
      width: 30px;
      height: 30px;
      border-radius: 50%;
      object-fit: cover;
    }
    .app-user-name {
      font-size: 12.5px;
      font-weight: 750;
      color: #0f172a;
      max-width: 140px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .app-user-role {
      font-size: 10.5px;
      color: #64748b;
      font-weight: 600;
    }
    .app-logout-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 7px 12px;
      background: #fff1f2;
      border: 1px solid #fecdd3;
      color: #e11d48 !important;
      border-radius: 10px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.18s ease;
    }
    .app-logout-btn:hover {
      background: #ffe4e6;
      border-color: #fda4af;
      transform: translateY(-1px);
    }
    .app-mobile-menu-btn {
      width: 38px;
      height: 38px;
      display: none;
      place-items: center;
      background: #f8fafc;
      color: #334155;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      cursor: pointer;
    }

    /* SIDEBAR NAVIGATION (MODERN EDTECH 2.0) */
    .app-sidebar nav {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 20px;
      padding: 14px 10px;
      box-shadow: 0 1px 4px rgba(15, 23, 42, 0.03);
    }
    .nav-group-heading {
      padding: 12px 12px 4px;
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 0.07em;
      text-transform: uppercase;
      color: #94a3b8;
    }
    .nav-item {
      display: flex !important;
      align-items: center;
      gap: 10px;
      width: 100%;
      padding: 9px 12px;
      margin-bottom: 2px;
      font-size: 13px;
      font-weight: 600;
      color: #475569;
      background: transparent;
      border: 1px solid transparent;
      border-radius: 12px;
      text-align: left;
      cursor: pointer;
      transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .nav-item:hover {
      background: #f8fafc;
      color: #0f172a;
      border-color: #f1f5f9;
      transform: translateX(3px);
    }
    .nav-item.is-active,
    .nav-item.active {
      background: linear-gradient(135deg, #173b70 0%, #2563eb 100%) !important;
      color: #ffffff !important;
      font-weight: 750;
      border-color: transparent;
      box-shadow: 0 4px 14px rgba(37, 99, 235, 0.28);
      transform: translateX(3px);
    }
    .nav-item.is-active i,
    .nav-item.is-active svg,
    .nav-item.active i,
    .nav-item.active svg {
      color: #ffffff !important;
    }
    .nav-item i, .nav-item svg {
      width: 17px;
      height: 17px;
      flex-shrink: 0;
      transition: transform 0.18s ease;
    }
    .nav-item:hover i, .nav-item:hover svg {
      transform: scale(1.1);
    }

    /* QUICK ACTION WIDGET */
    #quick-action-widget {
      border-radius: 18px;
      background: linear-gradient(135deg, #0f2b59 0%, #1d4ed8 100%);
      padding: 16px;
      color: #ffffff;
      box-shadow: 0 8px 24px -4px rgba(15, 43, 89, 0.25);
      border: 1px solid rgba(255, 255, 255, 0.15);
    }

    /* WORKSPACE HEADERS & CARDS ACROSS ALL TABS */
    .workspace-page-head {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      padding: 20px 24px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }
    .workspace-page-head h1 {
      margin: 4px 0 2px;
      font-size: 20px;
      font-weight: 850;
      color: #0f172a;
      letter-spacing: -0.02em;
    }
    .workspace-page-head p {
      margin: 0;
      font-size: 13px;
      color: #64748b;
      line-height: 1.4;
    }
    .workspace-kicker {
      font-size: 10.5px;
      font-weight: 800;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: #2563eb;
      margin-bottom: 2px;
    }
    .workspace-refresh {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 14px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      font-size: 12px;
      font-weight: 700;
      color: #334155;
      cursor: pointer;
      transition: all 0.18s ease;
    }
    .workspace-refresh:hover {
      background: #eff6ff;
      border-color: #bfdbfe;
      color: #2563eb;
      transform: translateY(-1px);
    }
    .tab-pane { animation: edtechFadeIn 0.22s cubic-bezier(0.16, 1, 0.3, 1); }
    @media (max-width:768px) {
      .app-header-inner { padding: 0 16px; height: 56px; gap: 12px; }
      .app-header-meta { display: none; }
      .app-brand-name { max-width: 140px; font-size: 12.5px; }
      .app-brand-sub { display: none; }
      .app-notif-dropdown { width: min(320px, calc(100vw - 24px)); right: -8px; }
      .app-mobile-menu-btn { display: grid; }
    }
"""

# 2. NEW APP SHELL HTML (HEADER + SIDEBAR)
NEW_SHELL_HTML = """  <!-- ========================================== -->
  <!-- 2. TOP HEADER (MODERN EDTECH 2.0) -->
  <header class="app-header">
    <div class="app-header-inner">
      <!-- School Logo & Branding -->
      <a class="app-brand" href="/dashboard" aria-label="HK Student Hub Dashboard">
        <div class="app-brand-icon">
          <i data-lucide="graduation-cap" class="w-5 h-5 text-white"></i>
        </div>
        <div>
          <div class="app-brand-name">{{ school_name }}</div>
          <div class="app-brand-sub">HK Student Hub · Quản trị nề nếp số</div>
        </div>
      </a>

      <!-- Academic Year & Server Live Clock -->
      <div class="app-header-meta">
        {% if current_year %}
        <span class="app-year-badge">
          <i data-lucide="calendar" class="w-3.5 h-3.5 inline mr-1 text-blue-600"></i>
          Năm học: {{ current_year }}
        </span>
        {% endif %}
        <span id="current-datetime" class="app-datetime" aria-live="off"></span>
      </div>

      <!-- Action Items & User Controls -->
      <div class="app-header-actions">
        <!-- Notification Bell Dropdown -->
        <button type="button" onclick="toggleNotificationDropdown()" class="app-notif-btn" title="Thông báo hệ thống" aria-label="Xem thông báo" aria-haspopup="true">
          <i data-lucide="bell" class="w-4 h-4"></i>
          <span id="notif-badge" class="app-notif-badge hidden">0</span>
        </button>

        <div id="notif-dropdown" class="app-notif-dropdown hidden" role="region" aria-label="Danh sách thông báo">
          <div class="app-notif-header">
            <span class="flex items-center gap-2">
              <i data-lucide="bell" class="w-4 h-4 text-blue-600"></i>
              Thông báo mới
            </span>
            <button type="button" onclick="markAllNotificationsRead()" class="app-notif-mark-all">Đã đọc tất cả</button>
          </div>
          <div id="notif-list" class="app-notif-list" aria-live="polite">
            <div class="p-4 text-center text-slate-400 text-xs">Đang tải thông báo...</div>
          </div>
        </div>

        <!-- User Role & Display Capsule -->
        <div id="user-badge" class="app-user-badge cursor-pointer" onclick="navigateTab('profile')" title="Xem hồ sơ cá nhân">
          <div id="user-avatar-text" class="app-user-avatar">HK</div>
          <img id="user-avatar-image" class="app-user-avatar-img hidden" alt="Ảnh đại diện">
          <div class="text-left hidden sm:block">
            <div id="user-display-name" class="app-user-name">Tài khoản</div>
            <div id="user-role-text" class="app-user-role"></div>
          </div>
        </div>

        <!-- Safe Logout Button -->
        <button type="button" onclick="handleLogout()" title="Đăng xuất an toàn" class="app-logout-btn">
          <i data-lucide="log-out" class="w-3.5 h-3.5"></i>
          <span class="hidden md:inline">Đăng xuất</span>
        </button>

        <!-- Mobile Drawer Menu Toggle -->
        <button type="button" onclick="toggleMobileMenu()" class="app-mobile-menu-btn md:hidden" aria-label="Mở danh mục điều hướng">
          <i data-lucide="menu" class="w-5 h-5"></i>
        </button>
      </div>
    </div>
  </header>

  <!-- 3. MAIN WRAPPER (SIDEBAR + CONTENT) -->
  <div class="app-shell flex-1 flex max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 gap-6">

    <!-- DESKTOP SIDEBAR NAVIGATION -->
    <aside class="app-sidebar w-64 shrink-0 hidden md:block">
      <nav class="sticky top-24 space-y-1 bg-white p-3.5 rounded-2xl shadow-sm border border-slate-200/90">
        
        <!-- NHÓM 1: TỔNG QUAN -->
        <div class="nav-group-heading" data-nav-group="main"><span>Tổng quan & Nề nếp</span></div>

        <button onclick="navigateTab('dashboard')" id="nav-btn-dashboard" class="nav-item is-active w-full">
          <i data-lucide="layout-dashboard"></i>
          <span>Tổng quan chung</span>
        </button>

        <button onclick="navigateTab('conduct')" id="nav-btn-conduct" class="nav-item hidden w-full">
          <i data-lucide="clipboard-list"></i>
          <span>Quản lý nề nếp</span>
        </button>

        <button onclick="navigateTab('competition')" id="nav-btn-competition" class="nav-item hidden w-full">
          <i data-lucide="award"></i>
          <span>Thi đua Chi đoàn</span>
        </button>

        <button onclick="navigateTab('sao-do-duty')" id="nav-btn-sao-do-duty" class="nav-item hidden w-full">
          <i data-lucide="star"></i>
          <span>Nhiệm vụ Sao đỏ</span>
        </button>

        <!-- NHÓM 2: QUẢN TRỊ ĐOÀN TRƯỜNG -->
        <div class="nav-group-heading hidden" data-nav-group="management"><span>Quản trị Đoàn trường</span></div>

        <button onclick="navigateTab('student-approvals')" id="nav-btn-student-approvals" class="nav-item hidden w-full justify-between">
          <div class="flex items-center gap-2.5">
            <i data-lucide="user-check"></i>
            <span>Duyệt học sinh</span>
          </div>
          <span id="sidebar-student-approval-badge" class="hidden px-1.5 py-0.5 text-[10px] font-bold bg-amber-100 text-amber-800 rounded-full">0</span>
        </button>

        <button onclick="navigateTab('doan-truong')" id="nav-btn-doan-truong" class="nav-item hidden w-full">
          <i data-lucide="shield-check"></i>
          <span>BCH Đoàn trường</span>
        </button>

        <button onclick="navigateTab('red-star')" id="nav-btn-red-star" class="nav-item hidden w-full">
          <i data-lucide="badge-check"></i>
          <span>Phân công Sao đỏ</span>
        </button>

        <button onclick="navigateTab('users')" id="nav-btn-users" class="nav-item hidden w-full">
          <i data-lucide="shield-alert"></i>
          <span>Duyệt quyền & Vai trò</span>
        </button>

        <!-- NHÓM 3: ĐỒNG HÀNH & HỖ TRỢ -->
        <div class="nav-group-heading hidden" data-nav-group="support"><span>Đồng hành & Hỗ trợ</span></div>

        <button onclick="navigateTab('alerts')" id="nav-btn-alerts" class="nav-item hidden w-full justify-between">
          <div class="flex items-center gap-2.5">
            <i data-lucide="bell-ring"></i>
            <span>Cảnh báo & GVCN</span>
          </div>
          <span id="sidebar-alert-badge" class="hidden px-1.5 py-0.5 text-[10px] font-bold bg-amber-100 text-amber-800 rounded-full">0</span>
        </button>

        <button onclick="navigateTab('counseling')" id="nav-btn-counseling" class="nav-item hidden w-full">
          <i data-lucide="heart-handshake"></i>
          <span>Góc sẻ chia & Tư vấn</span>
        </button>

        <!-- NHÓM 4: BÁO CÁO & CÀI ĐẶT -->
        <div class="nav-group-heading hidden" data-nav-group="admin"><span>Báo cáo & Hệ thống</span></div>

        <button onclick="navigateTab('reports')" id="nav-btn-reports" class="nav-item hidden w-full">
          <i data-lucide="file-spreadsheet"></i>
          <span>Báo cáo & Xuất file</span>
        </button>

        <button onclick="navigateTab('settings')" id="nav-btn-settings" class="nav-item hidden w-full">
          <i data-lucide="settings"></i>
          <span>Cấu hình & Nhật ký</span>
        </button>

        <div class="nav-group-heading" data-nav-group="account"><span>Tài khoản</span></div>

        <button onclick="navigateTab('profile')" id="nav-btn-profile" class="nav-item w-full">
          <i data-lucide="user-circle"></i>
          <span>Hồ sơ cá nhân</span>
        </button>

      </nav>

      <!-- Quick Action Launcher Widget -->
      <div id="quick-action-widget" class="hidden mt-4 p-4 rounded-2xl bg-gradient-to-br from-[#0f2b59] to-[#1d4ed8] text-white shadow-md border border-white/10">
        <div class="flex items-center space-x-2 mb-1.5 font-bold text-xs tracking-wide">
          <i data-lucide="zap" class="w-3.5 h-3.5 text-amber-300"></i>
          <span>Ghi nhận nhanh</span>
        </div>
        <p class="text-[11px] text-blue-100/90 mb-3 leading-relaxed">
          Đoàn trường, GV & Sao đỏ ghi nhận nề nếp tại lớp học hoặc cổng trường.
        </p>
        <button onclick="openQuickViolationModal()" class="w-full py-2 bg-amber-400 hover:bg-amber-300 text-slate-900 font-extrabold rounded-xl text-xs flex items-center justify-center space-x-1.5 shadow-sm transition">
          <i data-lucide="plus-circle" class="w-3.5 h-3.5"></i>
          <span>Ghi nhận vi phạm</span>
        </button>
      </div>

    </aside>
"""

def main():
    print("Reading templates/index.html...")
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        index_text = f.read()

    # 1. Replace Shell CSS
    s_css = index_text.find("/* ===== PREMIUM DESIGN SYSTEM v2 ===== */")
    e_css = index_text.find("/* ===== MODERN EDTECH DASHBOARD DESIGN SYSTEM 2.0 (FRIENDLY & ULTRA-SMOOTH) ===== */")
    if s_css != -1 and e_css != -1:
        print(f"Replacing Shell CSS ({s_css} to {e_css})...")
        index_text = index_text[:s_css] + NEW_SHELL_CSS + "\n    " + index_text[e_css:]
    else:
        print("ERROR: Shell CSS tokens not found!")

    # 2. Replace Header & Sidebar HTML
    s_html = index_text.find("<!-- ========================================== -->\n  <!-- 2. TOP HEADER")
    if s_html == -1:
        s_html = index_text.find("<!-- 2. TOP HEADER")
    e_html = index_text.find("<!-- CONTENT AREA -->")
    if s_html != -1 and e_html != -1:
        print(f"Replacing Shell HTML ({s_html} to {e_html})...")
        index_text = index_text[:s_html] + NEW_SHELL_HTML + "\n\n    " + index_text[e_html:]
    else:
        print("ERROR: Shell HTML tokens not found!")

    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(index_text)
    print("Saved upgraded templates/index.html!")

    # 3. Update navigateTab in static/app.js
    print("Reading static/app.js...")
    with open(APP_JS_PATH, 'r', encoding='utf-8') as f:
        app_text = f.read()

    old_nav_code = """  // Update nav buttons
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.remove('bg-brand-50', 'text-brand-900', 'border-brand-100');
    el.classList.add('text-slate-600');
  });
  const activeBtn = document.getElementById(`nav-btn-${tabName}`);
  if (activeBtn) {
    activeBtn.classList.add('bg-brand-50', 'text-brand-900', 'border-brand-100');
    activeBtn.classList.remove('text-slate-600');
  }"""

    new_nav_code = """  // Update nav buttons with modern EdTech active gradient styles
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.remove('is-active', 'active', 'bg-brand-50', 'text-brand-900', 'border-brand-100');
  });
  const activeBtn = document.getElementById(`nav-btn-${tabName}`);
  if (activeBtn) {
    activeBtn.classList.add('is-active', 'active');
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });"""

    if old_nav_code in app_text:
        print("Updating navigateTab in static/app.js...")
        app_text = app_text.replace(old_nav_code, new_nav_code)
        with open(APP_JS_PATH, 'w', encoding='utf-8') as f:
            f.write(app_text)
        print("Saved upgraded static/app.js!")
    else:
        print("Note: navigateTab active styling pattern already updated or not matched exactly.")

if __name__ == '__main__':
    main()
