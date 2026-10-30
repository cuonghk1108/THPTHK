"""
Script to apply the ultra-smooth, friendly EdTech Dashboard 2.0 to HK Student Hub.
Updates templates/index.html and static/app.js on Desktop.
"""
import os
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Xuan Cuong\Desktop\hk-student-hub")
INDEX_PATH = BASE_DIR / "templates" / "index.html"
APP_JS_PATH = BASE_DIR / "static" / "app.js"

# ==============================================================================
# 1. NEW CSS FOR DASHBOARD (templates/index.html)
# ==============================================================================
NEW_CSS = """    /* ===== MODERN EDTECH DASHBOARD DESIGN SYSTEM 2.0 (FRIENDLY & ULTRA-SMOOTH) ===== */
    @keyframes edtechFadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes edtechPulse {
      0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6); }
      70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
      100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    @keyframes goldShine {
      0% { transform: translateX(-100%); }
      100% { transform: translateX(200%); }
    }

    .edtech-dash-wrap {
      animation: edtechFadeIn 0.28s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    /* 1. HERO GREETING CARD */
    .edtech-hero-card {
      background: linear-gradient(135deg, #0f2b59 0%, #1e4287 48%, #2563eb 100%);
      background-image: radial-gradient(circle at 92% 18%, rgba(255, 255, 255, 0.18) 0%, transparent 55%),
                        radial-gradient(circle at 8% 85%, rgba(96, 165, 250, 0.22) 0%, transparent 45%);
      border-radius: 20px;
      padding: 24px 28px;
      color: #ffffff;
      position: relative;
      overflow: hidden;
      box-shadow: 0 12px 32px -8px rgba(15, 43, 89, 0.25);
      margin-bottom: 20px;
      border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .edtech-hero-card::after {
      content: "";
      position: absolute;
      top: -60px;
      right: -60px;
      width: 240px;
      height: 240px;
      background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
      border-radius: 50%;
      pointer-events: none;
    }
    .edtech-hero-inner {
      position: relative;
      z-index: 2;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    .edtech-greeting-box h2 {
      margin: 8px 0 5px;
      font-size: clamp(20px, 2.3vw, 26px);
      font-weight: 850;
      color: #ffffff;
      letter-spacing: -0.025em;
      line-height: 1.25;
    }
    .edtech-greeting-box p {
      margin: 0;
      font-size: 13.5px;
      color: rgba(241, 245, 249, 0.92);
      line-height: 1.5;
      font-weight: 450;
    }
    .edtech-role-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(255, 255, 255, 0.18);
      border: 1px solid rgba(255, 255, 255, 0.3);
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 750;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: #ffffff;
      backdrop-filter: blur(10px);
    }
    .edtech-hero-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .edtech-live-pill {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      background: rgba(16, 185, 129, 0.22);
      border: 1px solid rgba(16, 185, 129, 0.45);
      color: #a7f3d0;
      padding: 6px 12px;
      border-radius: 10px;
      font-size: 12px;
      font-weight: 650;
      backdrop-filter: blur(8px);
    }
    .edtech-live-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #10b981;
      animation: edtechPulse 2s infinite;
    }
    .edtech-hero-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(255, 255, 255, 0.16);
      border: 1px solid rgba(255, 255, 255, 0.28);
      color: #ffffff !important;
      padding: 7px 14px;
      border-radius: 10px;
      font-size: 12.5px;
      font-weight: 650;
      cursor: pointer;
      transition: all 0.18s ease;
      backdrop-filter: blur(8px);
    }
    .edtech-hero-btn:hover {
      background: rgba(255, 255, 255, 0.28);
      transform: translateY(-1px);
    }

    /* 2. SMART KPI METRIC CARDS */
    .edtech-kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 22px;
    }
    .edtech-kpi-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      padding: 18px 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
      position: relative;
      overflow: hidden;
      cursor: pointer;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }
    .edtech-kpi-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 12px 26px -6px rgba(15, 23, 42, 0.08);
      border-color: #cbd5e1;
    }
    .edtech-kpi-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 12px;
    }
    .edtech-kpi-title {
      font-size: 12.5px;
      font-weight: 650;
      color: #64748b;
      line-height: 1.3;
    }
    .edtech-kpi-icon {
      width: 40px;
      height: 40px;
      border-radius: 12px;
      display: grid;
      place-items: center;
      flex-shrink: 0;
      transition: transform 0.2s ease;
    }
    .edtech-kpi-card:hover .edtech-kpi-icon {
      transform: scale(1.06);
    }
    .edtech-kpi-val-row {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 8px;
    }
    .edtech-kpi-val {
      font-size: 28px;
      font-weight: 850;
      line-height: 1.1;
      font-variant-numeric: tabular-nums;
      letter-spacing: -0.025em;
    }
    .edtech-kpi-badge {
      font-size: 11px;
      font-weight: 750;
      padding: 3px 8px;
      border-radius: 6px;
      display: inline-flex;
      align-items: center;
      gap: 3px;
    }
    .edtech-kpi-footer {
      font-size: 11.5px;
      color: #64748b;
      margin-top: 10px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-top: 8px;
      border-top: 1px dashed #f1f5f9;
    }

    /* 3. SEGMENTED TAB CONTROLS */
    .edtech-tabs-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }
    .edtech-segmented-nav {
      background: #f1f5f9;
      padding: 4px;
      border-radius: 14px;
      display: inline-flex;
      gap: 4px;
      border: 1px solid #e2e8f0;
    }
    .edtech-seg-btn {
      padding: 8px 16px;
      font-size: 13px;
      font-weight: 650;
      border-radius: 10px;
      transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
      border: none;
      background: transparent;
      color: #64748b;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 7px;
    }
    .edtech-seg-btn:hover {
      color: #1e293b;
    }
    .edtech-seg-btn.active {
      background: #ffffff;
      color: #173b70;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
      font-weight: 750;
    }

    /* 4. OLYMPIC PODIUM 3D */
    .edtech-podium-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 20px;
      padding: 24px;
      margin-bottom: 22px;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }
    .edtech-podium-grid {
      display: grid;
      grid-template-columns: 1fr 1.08fr 1fr;
      gap: 16px;
      align-items: flex-end;
      margin-top: 16px;
    }
    @media (max-width: 768px) {
      .edtech-podium-grid {
        grid-template-columns: 1fr;
        align-items: stretch;
      }
    }
    .podium-pillar {
      border-radius: 18px;
      padding: 20px 18px;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      position: relative;
      overflow: hidden;
      transition: all 0.22s ease;
      cursor: pointer;
    }
    .podium-pillar:hover {
      transform: translateY(-4px);
    }
    .podium-gold {
      background: linear-gradient(180deg, #fffdf2 0%, #fef3c7 60%, #fde68a 100%);
      border: 2px solid #fbbf24;
      box-shadow: 0 10px 28px -6px rgba(245, 158, 11, 0.22);
      min-height: 250px;
      order: 2;
    }
    .podium-silver {
      background: linear-gradient(180deg, #ffffff 0%, #f8fafc 60%, #e2e8f0 100%);
      border: 1.5px solid #cbd5e1;
      box-shadow: 0 6px 18px -4px rgba(148, 163, 184, 0.16);
      min-height: 220px;
      order: 1;
    }
    .podium-bronze {
      background: linear-gradient(180deg, #fffaf5 0%, #ffedd5 60%, #fed7aa 100%);
      border: 1.5px solid #fdba74;
      box-shadow: 0 6px 18px -4px rgba(251, 146, 60, 0.16);
      min-height: 205px;
      order: 3;
    }
    @media (max-width: 768px) {
      .podium-gold { order: 1; min-height: auto; }
      .podium-silver { order: 2; min-height: auto; }
      .podium-bronze { order: 3; min-height: auto; }
    }
    .podium-crown-badge {
      width: 48px;
      height: 48px;
      border-radius: 14px;
      display: grid;
      place-items: center;
      font-size: 22px;
      margin-bottom: 10px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
      background: #ffffff;
    }
    .podium-class-title {
      font-size: 18px;
      font-weight: 850;
      color: #0f172a;
      letter-spacing: -0.01em;
    }
    .podium-score-pill {
      font-size: 22px;
      font-weight: 900;
      color: #173b70;
      margin: 6px 0 4px;
      font-variant-numeric: tabular-nums;
    }
    .podium-sub-text {
      font-size: 11.5px;
      color: #64748b;
      font-weight: 550;
    }

    /* 5. INTERACTIVE LEADERBOARD TABLE */
    .edtech-table-container {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }
    .edtech-table-toolbar {
      padding: 14px 18px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      background: #ffffff;
      border-bottom: 1px solid #f1f5f9;
    }
    .edtech-search-input {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 7px 12px 7px 32px;
      font-size: 12.5px;
      color: #1e293b;
      width: 220px;
      transition: all 0.16s ease;
    }
    .edtech-search-input:focus {
      background: #ffffff;
      border-color: #2563eb;
      outline: none;
      box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
    }
    .edtech-filter-pills {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }
    .edtech-filter-pill {
      font-size: 12px;
      font-weight: 650;
      padding: 5px 12px;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
      background: #f8fafc;
      color: #475569;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .edtech-filter-pill:hover {
      background: #eff6ff;
      color: #2563eb;
    }
    .edtech-filter-pill.active {
      background: #2457a7;
      color: #ffffff !important;
      border-color: #2457a7;
      box-shadow: 0 2px 6px rgba(36, 87, 167, 0.2);
    }

    /* 6. CHARTS SECTION */
    .edtech-chart-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(440px, 1fr));
      gap: 18px;
      margin-bottom: 22px;
    }
    @media (max-width: 640px) {
      .edtech-chart-grid { grid-template-columns: 1fr; }
    }
    .edtech-chart-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      padding: 20px 22px;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }
    .edtech-chart-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid #f1f5f9;
    }
    .edtech-chart-title {
      font-size: 14.5px;
      font-weight: 800;
      color: #173b70;
      margin: 0;
    }
    .edtech-chart-desc {
      font-size: 12px;
      color: #64748b;
      margin: 2px 0 0;
    }
    .edtech-chart-canvas-wrap {
      position: relative;
      width: 100%;
      height: 290px;
    }

    /* 7. HOMEROOM / STUDENT PERSONAL CARD */
    .edtech-personal-card {
      background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
      border: 1px solid #bbf7d0;
      border-radius: 18px;
      padding: 20px 24px;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      box-shadow: 0 2px 8px rgba(16, 185, 129, 0.06);
    }
"""

# ==============================================================================
# 2. NEW TAB CONTAINER FOR DASHBOARD (templates/index.html)
# ==============================================================================
NEW_TAB_HTML = """      <!-- TAB 1: DASHBOARD (MODERN EDTECH REDESIGN 2.0) -->
      <section id="tab-dashboard" class="tab-pane space-y-5">
        <div id="role-dashboard-content" class="role-dashboard-content min-w-0" aria-live="polite" aria-busy="true">
          <div class="space-y-4 animate-pulse">
            <div class="h-36 rounded-2xl bg-gradient-to-r from-blue-900/10 via-indigo-900/10 to-blue-800/10 border border-slate-200/60"></div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="h-28 rounded-2xl bg-slate-100/80 border border-slate-200/60"></div>
              <div class="h-28 rounded-2xl bg-slate-100/80 border border-slate-200/60"></div>
              <div class="h-28 rounded-2xl bg-slate-100/80 border border-slate-200/60"></div>
              <div class="h-28 rounded-2xl bg-slate-100/80 border border-slate-200/60"></div>
            </div>
          </div>
        </div>
        <div id="role-dashboard-error" class="workspace-error" role="alert" hidden>
          <div class="flex items-center gap-2">
            <i data-lucide="alert-circle" class="w-4 h-4 text-rose-500"></i>
            <span>Không thể tải dữ liệu bảng điều khiển.</span>
          </div>
          <button type="button" class="hk-btn hk-btn-secondary text-xs ml-3" onclick="loadDashboard()">Thử lại</button>
        </div>
      </section>"""

# ==============================================================================
# 3. NEW JAVASCRIPT LOGIC (static/app.js)
# ==============================================================================
NEW_APP_JS_MODULE = """// 1. DASHBOARD MODULE 2.0 – MODERN EDTECH & ULTRA-SMOOTH SCHOOL HUB
// =====================================================================
const _hkCharts = {
  weeklyTrend: null,
  classComparison: null,
};

let _dashboardData = {
  stats: null,
  snapshot: null,
  selectedGrade: 'ALL',
  selectedPeriod: 'week', // 'week' | 'semester'
  selectedTab: 'leaderboard', // 'leaderboard' | 'analytics' | 'activity'
  searchTerm: '',
};

function destroyAllHkCharts() {
  ['weeklyTrend', 'classComparison'].forEach(key => {
    if (_hkCharts[key]) {
      try {
        _hkCharts[key].destroy();
      } catch (e) {
        console.warn('Lỗi giải phóng biểu đồ ' + key, e);
      }
      _hkCharts[key] = null;
    }
  });
}

// Chuyển đổi qua lại giữa các tab con trên Dashboard
function switchDashboardTab(tabKey) {
  _dashboardData.selectedTab = tabKey;
  
  // Cập nhật nút điều hướng
  document.querySelectorAll('[data-dash-tab]').forEach(btn => {
    if (btn.getAttribute('data-dash-tab') === tabKey) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Cập nhật hiển thị pane
  const panes = ['leaderboard', 'analytics', 'activity'];
  panes.forEach(pane => {
    const el = document.getElementById(`dash-pane-${pane}`);
    if (el) {
      if (pane === tabKey) {
        el.classList.remove('hidden');
        el.classList.add('edtech-dash-wrap');
      } else {
        el.classList.add('hidden');
      }
    }
  });

  // Nếu chuyển sang tab analytics, kích hoạt vẽ lại biểu đồ mượt mà
  if (tabKey === 'analytics' && _dashboardData.snapshot) {
    setTimeout(() => {
      renderWeeklyTrendChart('chart-weekly-trend', _dashboardData.snapshot.weekly_trend);
      renderClassComparisonChart('chart-class-comparison', _dashboardData.snapshot.classes, _dashboardData.selectedGrade, _dashboardData.selectedPeriod);
    }, 50);
  }

  if (window.lucide) lucide.createIcons();
}

// Cập nhật bộ lọc Khối và Kỳ thi đua tức thời (không reload trang)
function onDashboardFilterChange(filterType, filterValue) {
  if (filterType === 'grade') {
    _dashboardData.selectedGrade = filterValue;
    document.querySelectorAll('[data-grade-filter]').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-grade-filter') === filterValue);
    });
  } else if (filterType === 'period') {
    _dashboardData.selectedPeriod = filterValue;
    document.querySelectorAll('[data-period-filter]').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-period-filter') === filterValue);
    });
  }

  if (!_dashboardData.snapshot || !_dashboardData.snapshot.classes) return;

  renderTopPodium(_dashboardData.snapshot.classes, _dashboardData.selectedGrade, _dashboardData.selectedPeriod);
  renderDashboardTable(_dashboardData.snapshot.classes, _dashboardData.selectedGrade, _dashboardData.selectedPeriod, _dashboardData.searchTerm);
  
  if (_dashboardData.selectedTab === 'analytics') {
    renderClassComparisonChart('chart-class-comparison', _dashboardData.snapshot.classes, _dashboardData.selectedGrade, _dashboardData.selectedPeriod);
  }
}

// Tìm kiếm Chi đoàn tức thì khi gõ phím
function onDashboardSearch(keyword) {
  _dashboardData.searchTerm = (keyword || '').toLowerCase().trim();
  if (_dashboardData.snapshot && _dashboardData.snapshot.classes) {
    renderDashboardTable(_dashboardData.snapshot.classes, _dashboardData.selectedGrade, _dashboardData.selectedPeriod, _dashboardData.searchTerm);
  }
}

// Lấy lời chào ấm áp, thân thiện theo khung giờ trong ngày
function getEdtechGreeting() {
  const h = new Date().getHours();
  if (h >= 5 && h < 11) return 'Chào buổi sáng ☀️';
  if (h >= 11 && h < 13) return 'Chúc buổi trưa an lành 🌿';
  if (h >= 13 && h < 18) return 'Chào buổi chiều năng lượng 🌤️';
  return 'Chúc buổi tối vui vẻ 🌙';
}

// ==========================================
// RENDER BỤC VINH DANH TOP 3 OLYMPIC
// ==========================================
function renderTopPodium(classes, gradeFilter = 'ALL', periodKey = 'week') {
  const container = document.getElementById('dashboard-podium-content');
  if (!container) return;

  if (!classes || !classes.length) {
    container.innerHTML = '<div class="py-8 text-center text-slate-400 text-xs">Chưa có dữ liệu xếp hạng trong kỳ này.</div>';
    return;
  }

  // Lọc theo khối
  let filtered = [...classes];
  if (gradeFilter !== 'ALL') {
    filtered = filtered.filter(c => String(c.grade) === String(gradeFilter));
  }

  // Sắp xếp giảm dần theo điểm
  filtered.sort((a, b) => {
    const sA = (a[periodKey] && a[periodKey].total_score != null) ? a[periodKey].total_score : 100;
    const sB = (b[periodKey] && b[periodKey].total_score != null) ? b[periodKey].total_score : 100;
    return sB - sA;
  });

  const c1 = filtered[0];
  const c2 = filtered[1];
  const c3 = filtered[2];

  if (!c1) {
    container.innerHTML = '<div class="py-8 text-center text-slate-400 text-xs">Không có lớp nào phù hợp bộ lọc.</div>';
    return;
  }

  const s1 = (c1[periodKey] && c1[periodKey].total_score != null) ? Number(c1[periodKey].total_score).toFixed(2) : '100.00';
  const s2 = c2 && (c2[periodKey] && c2[periodKey].total_score != null) ? Number(c2[periodKey].total_score).toFixed(2) : '-';
  const s3 = c3 && (c3[periodKey] && c3[periodKey].total_score != null) ? Number(c3[periodKey].total_score).toFixed(2) : '-';

  const b1 = (c1[periodKey] && c1[periodKey].bonus_points) ? Number(c1[periodKey].bonus_points).toFixed(1) : '0';
  const p1 = (c1[periodKey] && c1[periodKey].penalty_points) ? Number(c1[periodKey].penalty_points).toFixed(1) : '0';

  const b2 = c2 && (c2[periodKey] && c2[periodKey].bonus_points) ? Number(c2[periodKey].bonus_points).toFixed(1) : '0';
  const p2 = c2 && (c2[periodKey] && c2[periodKey].penalty_points) ? Number(c2[periodKey].penalty_points).toFixed(1) : '0';

  const b3 = c3 && (c3[periodKey] && c3[periodKey].bonus_points) ? Number(c3[periodKey].bonus_points).toFixed(1) : '0';
  const p3 = c3 && (c3[periodKey] && c3[periodKey].penalty_points) ? Number(c3[periodKey].penalty_points).toFixed(1) : '0';

  container.innerHTML = `
    <!-- HẠNG 2 (Á QUÂN - BẠC) -->
    ${c2 ? `
    <div class="podium-pillar podium-silver" onclick="navigateTab('competition')">
      <div class="podium-crown-badge">🥈</div>
      <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500">Á Quân · Hạng 2</span>
      <h4 class="podium-class-title">${escapeHtml(c2.name)}</h4>
      <div class="podium-score-pill">${s2}đ</div>
      <div class="podium-sub-text">Cộng +${b2} · Trừ -${p2}</div>
    </div>
    ` : '<div class="podium-pillar podium-silver opacity-40"><div class="podium-crown-badge">🥈</div><span class="text-xs text-slate-400">Đang cập nhật</span></div>'}

    <!-- HẠNG 1 (QUÁN QUÂN - VÀNG) -->
    <div class="podium-pillar podium-gold" onclick="navigateTab('competition')">
      <div class="podium-crown-badge">👑 🥇</div>
      <span class="text-[11px] font-extrabold uppercase tracking-wider text-amber-700">Dẫn Đầu Toàn Trường · Hạng 1</span>
      <h3 class="podium-class-title text-xl text-amber-950 font-black">${escapeHtml(c1.name)}</h3>
      <div class="podium-score-pill text-2xl text-amber-900">${s1}đ</div>
      <div class="podium-sub-text text-amber-800">Cộng +${b1} · Trừ -${p1} điểm</div>
    </div>

    <!-- HẠNG 3 (QUÝ QUÂN - ĐỒNG) -->
    ${c3 ? `
    <div class="podium-pillar podium-bronze" onclick="navigateTab('competition')">
      <div class="podium-crown-badge">🥉</div>
      <span class="text-[11px] font-bold uppercase tracking-wider text-orange-600">Quý Quân · Hạng 3</span>
      <h4 class="podium-class-title">${escapeHtml(c3.name)}</h4>
      <div class="podium-score-pill">${s3}đ</div>
      <div class="podium-sub-text">Cộng +${b3} · Trừ -${p3}</div>
    </div>
    ` : '<div class="podium-pillar podium-bronze opacity-40"><div class="podium-crown-badge">🥉</div><span class="text-xs text-slate-400">Đang cập nhật</span></div>'}
  `;
}

// ==========================================
// RENDER BẢNG TỔNG SẮP CHI ĐOÀN CHI TIẾT
// ==========================================
function renderDashboardTable(classes, gradeFilter = 'ALL', periodKey = 'week', searchTerm = '') {
  const tbody = document.getElementById('dashboard-data-tbody');
  const countSpan = document.getElementById('dashboard-table-count');
  if (!tbody) return;

  if (!classes || !classes.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="py-6 text-center text-slate-400 text-xs">Không có dữ liệu.</td></tr>';
    if (countSpan) countSpan.textContent = '0 lớp';
    return;
  }

  let list = [...classes];
  if (gradeFilter !== 'ALL') {
    list = list.filter(c => String(c.grade) === String(gradeFilter));
  }
  if (searchTerm) {
    list = list.filter(c => c.name && c.name.toLowerCase().includes(searchTerm));
  }

  list.sort((a, b) => {
    const sA = (a[periodKey] && a[periodKey].total_score != null) ? a[periodKey].total_score : 100;
    const sB = (b[periodKey] && b[periodKey].total_score != null) ? b[periodKey].total_score : 100;
    return sB - sA;
  });

  if (countSpan) countSpan.textContent = `${list.length} Chi đoàn`;

  if (!list.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="py-6 text-center text-slate-400 text-xs">Không tìm thấy Chi đoàn nào phù hợp từ khóa.</td></tr>';
    return;
  }

  tbody.innerHTML = list.map((c, idx) => {
    const pData = c[periodKey] || {};
    const score = pData.total_score != null ? Number(pData.total_score).toFixed(2) : '100.00';
    const bonus = pData.bonus_points != null ? Number(pData.bonus_points).toFixed(1) : '0.0';
    const penalty = pData.penalty_points != null ? Number(pData.penalty_points).toFixed(1) : '0.0';
    const violations = pData.verified_violations_count != null ? pData.verified_violations_count : 0;
    const rankNum = idx + 1;

    let rankBadge = `<span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-slate-100 text-slate-700 font-bold text-xs">${rankNum}</span>`;
    if (rankNum === 1) rankBadge = `<span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-amber-100 text-amber-800 font-bold text-xs shadow-sm">🥇 1</span>`;
    else if (rankNum === 2) rankBadge = `<span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-slate-200 text-slate-800 font-bold text-xs shadow-sm">🥈 2</span>`;
    else if (rankNum === 3) rankBadge = `<span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-orange-100 text-orange-800 font-bold text-xs shadow-sm">🥉 3</span>`;
    else if (rankNum <= 10) rankBadge = `<span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-emerald-50 text-emerald-700 font-bold text-xs">${rankNum}</span>`;

    const scoreNum = Number(score);
    const progressWidth = Math.min(100, Math.max(0, (scoreNum / 100) * 100));
    let progressColor = 'bg-emerald-500';
    if (scoreNum < 85) progressColor = 'bg-rose-500';
    else if (scoreNum < 95) progressColor = 'bg-amber-500';

    return `
      <tr class="border-b border-slate-100 hover:bg-slate-50/80 transition-colors">
        <td class="py-3 px-3.5 text-center font-medium">${rankBadge}</td>
        <td class="py-3 px-3.5 font-bold text-slate-900">${escapeHtml(c.name)}</td>
        <td class="py-3 px-3 text-center"><span class="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">Khối ${c.grade}</span></td>
        <td class="py-3 px-3 text-right font-medium text-emerald-600">+${bonus}</td>
        <td class="py-3 px-3 text-right font-medium text-rose-600">-${penalty}</td>
        <td class="py-3 px-3.5 text-right font-black text-sm text-[#173B70]">${score}</td>
        <td class="py-3 px-4">
          <div class="w-full bg-slate-100 rounded-full h-2 overflow-hidden flex" title="${progressWidth}% chuẩn">
            <div class="${progressColor} h-2 rounded-full transition-all duration-300" style="width: ${progressWidth}%"></div>
          </div>
        </td>
        <td class="py-3 px-3 text-center">
          <span class="inline-flex items-center justify-center px-2 py-0.5 rounded text-[11px] font-semibold ${violations > 0 ? 'bg-rose-50 text-rose-700' : 'bg-slate-100 text-slate-600'}">${violations}</span>
        </td>
      </tr>
    `;
  }).join('');
}

// ==========================================
// RENDER BIỂU ĐỒ XU HƯỚNG CÁC TUẦN (CHART.JS)
// ==========================================
function renderWeeklyTrendChart(canvasId, weeklyTrendData, customClassTrend = null, customClassName = '') {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  if (_hkCharts.weeklyTrend) {
    try { _hkCharts.weeklyTrend.destroy(); } catch (e) {}
    _hkCharts.weeklyTrend = null;
  }

  let labels = [];
  let avgScores = [];

  if (weeklyTrendData && weeklyTrendData.length) {
    weeklyTrendData.forEach(item => {
      labels.push(item.period_name || `Tuần ${item.period_id}`);
      avgScores.push(item.average_score != null ? Number(item.average_score).toFixed(2) : 100.0);
    });
  } else {
    labels = ['Tuần 1', 'Tuần 2', 'Tuần 3', 'Tuần 4', 'Tuần 5'];
    avgScores = [98.5, 97.2, 98.9, 96.8, 98.0];
  }

  const ctx = canvas.getContext('2d');
  let gradSchool = ctx.createLinearGradient(0, 0, 0, 260);
  gradSchool.addColorStop(0, 'rgba(37, 99, 235, 0.22)');
  gradSchool.addColorStop(1, 'rgba(37, 99, 235, 0.0)');

  const datasets = [
    {
      label: 'Điểm TB toàn trường',
      data: avgScores,
      borderColor: '#2563eb',
      backgroundColor: gradSchool,
      borderWidth: 2.5,
      fill: true,
      tension: 0.38,
      pointRadius: 4,
      pointBackgroundColor: '#ffffff',
      pointBorderColor: '#2563eb',
      pointBorderWidth: 2,
      pointHoverRadius: 6,
    }
  ];

  if (customClassTrend && customClassTrend.length) {
    const classScores = customClassTrend.map(t => Number(t.total_score).toFixed(2));
    let gradClass = ctx.createLinearGradient(0, 0, 0, 260);
    gradClass.addColorStop(0, 'rgba(16, 185, 129, 0.22)');
    gradClass.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    datasets.push({
      label: `Lớp ${customClassName || 'chủ nhiệm'}`,
      data: classScores,
      borderColor: '#059669',
      backgroundColor: gradClass,
      borderWidth: 2.5,
      fill: true,
      tension: 0.38,
      pointRadius: 4,
      pointBackgroundColor: '#ffffff',
      pointBorderColor: '#059669',
      pointBorderWidth: 2,
      pointHoverRadius: 6,
    });
  }

  _hkCharts.weeklyTrend = new Chart(canvas, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 550, easing: 'easeOutQuart' },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: { font: { size: 12, weight: '600', family: 'Inter, system-ui' }, boxWidth: 12, usePointStyle: true }
        },
        tooltip: {
          backgroundColor: '#0f172a',
          titleFont: { size: 12, weight: '700' },
          bodyFont: { size: 12 },
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: ${ctx.raw} điểm`
          }
        }
      },
      scales: {
        y: {
          min: 80,
          max: 105,
          grid: { color: '#f1f5f9' },
          ticks: { font: { size: 11 }, callback: v => v + 'đ' }
        },
        x: {
          grid: { display: false },
          ticks: { font: { size: 11 } }
        }
      }
    }
  });
}

// ==========================================
// RENDER BIỂU ĐỒ CỘT SO SÁNH CÁC LỚP
// ==========================================
function renderClassComparisonChart(canvasId, classes, gradeFilter = 'ALL', periodKey = 'week') {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  if (_hkCharts.classComparison) {
    try { _hkCharts.classComparison.destroy(); } catch (e) {}
    _hkCharts.classComparison = null;
  }

  if (!classes || !classes.length) return;

  let list = [...classes];
  if (gradeFilter !== 'ALL') {
    list = list.filter(c => String(c.grade) === String(gradeFilter));
  }
  list.sort((a, b) => {
    const sA = (a[periodKey] && a[periodKey].total_score != null) ? a[periodKey].total_score : 100;
    const sB = (b[periodKey] && b[periodKey].total_score != null) ? b[periodKey].total_score : 100;
    return sB - sA;
  });

  const topClasses = list.slice(0, 14);
  const labels = topClasses.map(c => c.name);
  const scores = topClasses.map(c => (c[periodKey] && c[periodKey].total_score != null) ? Number(c[periodKey].total_score).toFixed(2) : 100);

  const backgroundColors = scores.map(s => {
    const n = Number(s);
    if (n >= 95) return '#2563eb';
    if (n >= 90) return '#0d9488';
    if (n >= 80) return '#f59e0b';
    return '#f43f5e';
  });

  _hkCharts.classComparison = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Điểm thi đua',
        data: scores,
        backgroundColor: backgroundColors,
        borderRadius: 8,
        borderSkipped: false,
        maxBarThickness: 34,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 500, easing: 'easeOutQuart' },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0f172a',
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: (ctx) => ` Điểm: ${ctx.raw}đ`
          }
        }
      },
      scales: {
        y: {
          min: 75,
          max: 105,
          grid: { color: '#f1f5f9' },
          ticks: { font: { size: 11 }, callback: v => v + 'đ' }
        },
        x: {
          grid: { display: false },
          ticks: { font: { size: 11, weight: '600' } }
        }
      }
    }
  });
}

// ==============================================================================
// HÀM TẢI VÀ DỰNG DASHBOARD CHÍNH CHO 6 VAI TRÒ
// ==============================================================================
async function loadDashboard() {
  const root = document.getElementById('role-dashboard-content');
  const errorBox = document.getElementById('role-dashboard-error');
  if (!root) return;

  destroyAllHkCharts();
  root.setAttribute('aria-busy', 'true');
  root.innerHTML = `
    <div class="space-y-4 animate-pulse">
      <div class="h-36 rounded-2xl bg-gradient-to-r from-blue-900/10 via-indigo-900/10 to-blue-800/10 border border-slate-200/60"></div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="h-28 rounded-2xl bg-slate-100/80 border border-slate-200/60"></div>
        <div class="h-28 rounded-2xl bg-slate-100/80 border border-slate-200/60"></div>
        <div class="h-28 rounded-2xl bg-slate-100/80 border border-slate-200/60"></div>
        <div class="h-28 rounded-2xl bg-slate-100/80 border border-slate-200/60"></div>
      </div>
    </div>
  `;
  if (errorBox) errorBox.hidden = true;

  try {
    const [statsRes, dashRes] = await Promise.all([
      apiRequest('/api/core/system/stats/'),
      apiRequest('/api/competition/periods/dashboard/'),
    ]);

    const stats = (statsRes && statsRes.data) ? statsRes.data : statsRes || {};
    const snapshot = (dashRes && dashRes.data) ? dashRes.data : dashRes || {};
    _dashboardData.stats = stats;
    _dashboardData.snapshot = snapshot;

    const role = stats.user_role || (currentUser && currentUser.role) || 'STUDENT';
    const isAdmin = role === 'ADMIN' || (currentUser && (currentUser.is_superuser || currentUser.is_staff));
    const isDoanTruong = role === 'DOAN_TRUONG' || role === 'BCH_DOAN' || (currentUser && currentUser.is_doan_truong);
    const isGVCN = role === 'GVCN' || (currentUser && currentUser.is_gvcn);
    const isGVBM = role === 'GVBM';
    const isSaoDo = role === 'SAO_DO';
    const isStudent = role === 'STUDENT' || (!isAdmin && !isDoanTruong && !isGVCN && !isGVBM && !isSaoDo);

    const greeting = getEdtechGreeting();
    const fullName = (currentUser && currentUser.full_name) || (stats.user && stats.user.full_name) || 'Bạn';
    const now = new Date();
    const timeStr = now.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    const currentWeekName = stats.current_week || 'Tuần 1';

    let html = '';

    // ==========================================
    // 1. ADMIN & ĐOÀN TRƯỜNG COMMAND HUB
    // ==========================================
    if (isAdmin || isDoanTruong) {
      const isDoan = isDoanTruong && !isAdmin;
      const b = stats.violations_breakdown || {};
      const pendingV = stats.violations_pending != null ? stats.violations_pending : (b.pending || 0);
      const todayV = stats.violations_today != null ? stats.violations_today : 0;
      const verifiedW = stats.violations_verified_week != null ? stats.violations_verified_week : (b.verified || 0);
      const pendingAcc = stats.pending_accounts != null ? stats.pending_accounts : 0;
      const avgScore = stats.average_score != null ? Number(stats.average_score).toFixed(1) : '100.0';
      const rsPending = (stats.red_star_stats && stats.red_star_stats.pending) || 0;

      html = `
        <div class="edtech-dash-wrap">
          <!-- 1. SMART HERO CARD -->
          <div class="edtech-hero-card">
            <div class="edtech-hero-inner">
              <div class="edtech-greeting-box">
                <span class="edtech-role-pill" id="dash-role-badge">
                  <i data-lucide="${isDoan ? 'award' : 'shield'}" class="w-3.5 h-3.5 inline"></i>
                  ${isDoan ? 'Ban Chấp Hành Đoàn Trường' : 'Quản Trị Viên Hệ Thống'}
                </span>
                <h2>${greeting}, <span id="dash-user-name">${escapeHtml(fullName)}</span>!</h2>
                <p id="dash-welcome-sub">Theo dõi nề nếp số <strong>${stats.total_classes || 36} Chi đoàn</strong> · Năm học 2026–2027 (${currentWeekName}).</p>
              </div>
              <div class="edtech-hero-actions">
                <span class="edtech-live-pill">
                  <span class="edtech-live-dot"></span>
                  Trực tiếp (${timeStr})
                </span>
                <button type="button" onclick="loadDashboard()" class="edtech-hero-btn">
                  <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i> Làm mới
                </button>
                <button type="button" onclick="openQuickViolationModal()" class="edtech-hero-btn bg-white/25 hover:bg-white/35">
                  <i data-lucide="plus-circle" class="w-3.5 h-3.5"></i> Ghi vi phạm
                </button>
              </div>
            </div>
          </div>

          <!-- 2. 4 SMART KPI METRIC CARDS -->
          <div class="edtech-kpi-grid">
            <div class="edtech-kpi-card" onclick="navigateTab('competition')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Điểm TB toàn trường</span>
                <div class="edtech-kpi-icon bg-blue-50 text-blue-600 border border-blue-100">
                  <i data-lucide="award" class="w-5 h-5"></i>
                </div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-[#173B70]">${avgScore}</span>
                <span class="edtech-kpi-badge bg-emerald-50 text-emerald-700">Chuẩn 100đ</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Thi đua ${currentWeekName}</span>
                <span class="text-blue-600 font-semibold">Bảng vàng →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Báo cáo chờ duyệt</span>
                <div class="edtech-kpi-icon bg-amber-50 text-amber-600 border border-amber-100">
                  <i data-lucide="clock" class="w-5 h-5"></i>
                </div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-amber-600">${pendingV}</span>
                <span class="edtech-kpi-badge ${pendingV > 0 ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600'}">
                  ${pendingV > 0 ? 'Cần xử lý' : 'Đã sạch'}
                </span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Biên bản cần thẩm tra</span>
                <span class="text-amber-600 font-semibold">Xử lý ngay →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Vi phạm hôm nay</span>
                <div class="edtech-kpi-icon bg-rose-50 text-rose-600 border border-rose-100">
                  <i data-lucide="alert-triangle" class="w-5 h-5"></i>
                </div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-rose-600">${todayV}</span>
                <span class="edtech-kpi-badge bg-rose-50 text-rose-700">Tuần: ${verifiedW}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Ghi nhận từ Sao đỏ & GV</span>
                <span class="text-rose-600 font-semibold">Xem nề nếp →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('student-approvals')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">${isDoan ? 'Biên bản Sao đỏ gửi' : 'Hồ sơ chờ phê duyệt'}</span>
                <div class="edtech-kpi-icon bg-emerald-50 text-emerald-600 border border-emerald-100">
                  <i data-lucide="${isDoan ? 'shield' : 'user-check'}" class="w-5 h-5"></i>
                </div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-emerald-600">${isDoan ? rsPending : pendingAcc}</span>
                <span class="edtech-kpi-badge ${(isDoan ? rsPending : pendingAcc) > 0 ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}">
                  ${(isDoan ? rsPending : pendingAcc) > 0 ? 'Mới' : 'Hoàn tất'}
                </span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Kiểm duyệt tài khoản</span>
                <span class="text-emerald-700 font-semibold">Phê duyệt →</span>
              </div>
            </div>
          </div>

          <!-- 3. SEGMENTED TABS CONTROLS (ULTRA SMOOTH) -->
          <div class="edtech-tabs-bar">
            <div class="edtech-segmented-nav">
              <button type="button" data-dash-tab="leaderboard" onclick="switchDashboardTab('leaderboard')" class="edtech-seg-btn active">
                <i data-lucide="trophy" class="w-4 h-4"></i>
                <span>Bảng Vàng & Thi Đua</span>
              </button>
              <button type="button" data-dash-tab="analytics" onclick="switchDashboardTab('analytics')" class="edtech-seg-btn">
                <i data-lucide="bar-chart-2" class="w-4 h-4"></i>
                <span>Biểu Đồ Phân Tích</span>
              </button>
              <button type="button" data-dash-tab="activity" onclick="switchDashboardTab('activity')" class="edtech-seg-btn">
                <i data-lucide="bell" class="w-4 h-4"></i>
                <span>Cảnh Báo & Hoạt Động</span>
              </button>
            </div>

            <div class="edtech-filter-pills">
              <span class="text-xs font-bold text-slate-500 mr-1">Kỳ:</span>
              <button type="button" data-period-filter="week" onclick="onDashboardFilterChange('period', 'week')" class="edtech-filter-pill active">Tuần này</button>
              <button type="button" data-period-filter="semester" onclick="onDashboardFilterChange('period', 'semester')" class="edtech-filter-pill">Học kỳ I</button>
            </div>
          </div>

          <!-- TAB PANE 1: BẢNG VÀNG & THI ĐUA -->
          <div id="dash-pane-leaderboard" class="space-y-5">
            <!-- PODIUM VINH DANH -->
            <div class="edtech-podium-card">
              <div class="flex items-center justify-between flex-wrap gap-2 mb-2">
                <div>
                  <h3 class="font-extrabold text-[#173B70] text-base flex items-center gap-2">
                    <i data-lucide="crown" class="w-4 h-4 text-amber-500"></i>
                    Bục Vinh Danh Top 3 Chi Đoàn Dẫn Đầu
                  </h3>
                  <p class="text-xs text-slate-500 mt-0.5">Vinh danh thành tích nề nếp và phong trào thi đua xuất sắc nhất</p>
                </div>
                <div class="edtech-filter-pills">
                  <span class="text-xs font-semibold text-slate-500 mr-1">Khối:</span>
                  <button type="button" data-grade-filter="ALL" onclick="onDashboardFilterChange('grade', 'ALL')" class="edtech-filter-pill active">Tất cả</button>
                  <button type="button" data-grade-filter="10" onclick="onDashboardFilterChange('grade', '10')" class="edtech-filter-pill">Khối 10</button>
                  <button type="button" data-grade-filter="11" onclick="onDashboardFilterChange('grade', '11')" class="edtech-filter-pill">Khối 11</button>
                  <button type="button" data-grade-filter="12" onclick="onDashboardFilterChange('grade', '12')" class="edtech-filter-pill">Khối 12</button>
                </div>
              </div>
              <div id="dashboard-podium-content" class="edtech-podium-grid"></div>
            </div>

            <!-- BẢNG TỔNG SẮP CHI ĐOÀN -->
            <div class="edtech-table-container">
              <div class="edtech-table-toolbar">
                <div class="flex items-center gap-3">
                  <h4 class="font-bold text-slate-800 text-sm">Bảng Điểm Thi Đua Chi Tiết</h4>
                  <span id="dashboard-table-count" class="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">36 Chi đoàn</span>
                </div>
                <div class="relative">
                  <i data-lucide="search" class="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5"></i>
                  <input type="text" placeholder="Tìm tên lớp (vd: 10A1)..." oninput="onDashboardSearch(this.value)" class="edtech-search-input">
                </div>
              </div>
              <div class="overflow-x-auto max-h-[380px]">
                <table class="w-full text-left text-xs border-collapse">
                  <thead class="bg-slate-50 sticky top-0 border-b border-slate-200 text-slate-600 font-semibold z-10">
                    <tr>
                      <th class="py-2.5 px-3.5 text-center w-12">Hạng</th>
                      <th class="py-2.5 px-3.5">Chi đoàn</th>
                      <th class="py-2.5 px-3 text-center">Khối</th>
                      <th class="py-2.5 px-3 text-right">Điểm cộng</th>
                      <th class="py-2.5 px-3 text-right">Điểm trừ</th>
                      <th class="py-2.5 px-3.5 text-right">Tổng điểm</th>
                      <th class="py-2.5 px-4 w-36">Phong độ chuẩn</th>
                      <th class="py-2.5 px-3 text-center">Vi phạm</th>
                    </tr>
                  </thead>
                  <tbody id="dashboard-data-tbody"></tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- TAB PANE 2: BIỂU ĐỒ PHÂN TÍCH -->
          <div id="dash-pane-analytics" class="hidden space-y-5">
            <div class="edtech-chart-grid">
              <div class="edtech-chart-card">
                <div class="edtech-chart-header">
                  <div>
                    <h3 class="edtech-chart-title">1. Biến Động Điểm Toàn Trường Qua Các Tuần</h3>
                    <p class="edtech-chart-desc">Đường spline so sánh điểm TB các tuần với chuẩn 100 điểm</p>
                  </div>
                </div>
                <div class="edtech-chart-canvas-wrap">
                  <canvas id="chart-weekly-trend"></canvas>
                </div>
              </div>

              <div class="edtech-chart-card">
                <div class="edtech-chart-header">
                  <div>
                    <h3 class="edtech-chart-title">2. So Sánh Điểm Thi Đua Các Lớp</h3>
                    <p class="edtech-chart-desc">Phân bố điểm nề nếp theo các lớp trong khối đang chọn</p>
                  </div>
                </div>
                <div class="edtech-chart-canvas-wrap">
                  <canvas id="chart-class-comparison"></canvas>
                </div>
              </div>
            </div>
          </div>

          <!-- TAB PANE 3: CẢNH BÁO & HOẠT ĐỘNG -->
          <div id="dash-pane-activity" class="hidden space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-sm">
                <div class="flex items-center justify-between mb-3">
                  <h4 class="font-bold text-slate-800 text-sm flex items-center gap-2">
                    <i data-lucide="alert-octagon" class="w-4 h-4 text-rose-500"></i>
                    Chi Đoàn Cần Đoàn Trường Lưu Ý
                  </h4>
                  <span class="text-xs text-slate-500">Tuần hiện tại</span>
                </div>
                <div id="dashboard-attention-classes" class="space-y-2.5">
                  <div class="p-3 bg-amber-50/70 border border-amber-200/60 rounded-xl text-xs text-amber-800 flex items-center justify-between">
                    <div>
                      <strong>Chi đoàn có điểm dưới 90đ:</strong>
                      <p class="text-slate-600 mt-0.5">Cần gặp gỡ Ban cán sự và GVCN để cùng chấn chỉnh nề nếp trang phục, giờ giấc.</p>
                    </div>
                    <button onclick="navigateTab('conduct')" class="hk-btn hk-btn-secondary text-[11px] py-1 px-2.5">Kiểm tra</button>
                  </div>
                </div>
              </div>

              <div class="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-sm">
                <div class="flex items-center justify-between mb-3">
                  <h4 class="font-bold text-slate-800 text-sm flex items-center gap-2">
                    <i data-lucide="check-circle" class="w-4 h-4 text-emerald-500"></i>
                    Cẩm Nang Thi Đua & Nề Nếp
                  </h4>
                  <span class="text-xs text-slate-500">Quy chuẩn 2026</span>
                </div>
                <div class="space-y-2 text-xs text-slate-600">
                  <div class="p-2.5 bg-slate-50 rounded-xl border border-slate-100 flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                    <span><strong>Điểm chuẩn ban đầu:</strong> Mỗi Chi đoàn khởi điểm với 100 điểm trọn vẹn mỗi tuần.</span>
                  </div>
                  <div class="p-2.5 bg-slate-50 rounded-xl border border-slate-100 flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-blue-500"></span>
                    <span><strong>Trừ điểm trực tiếp:</strong> Đoàn trường và Admin có quyền trừ điểm trực tiếp không cần duyệt.</span>
                  </div>
                  <div class="p-2.5 bg-slate-50 rounded-xl border border-slate-100 flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-amber-500"></span>
                    <span><strong>Khiếu nại minh bạch:</strong> GVCN có 48 giờ để phản hồi hoặc khiếu nại biên bản.</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    // ==========================================
    // 2. GIÁO VIÊN CHỦ NHIỆM (GVCN) HUB
    // ==========================================
    else if (isGVCN) {
      const clsInfo = stats.class_score_info || {};
      const hrClass = stats.homeroom_class || {};
      const score = clsInfo.total_score != null ? Number(clsInfo.total_score).toFixed(2) : '100.00';
      const rank = clsInfo.rank != null ? '#' + clsInfo.rank : '-';
      const rankGrade = clsInfo.rank_in_grade != null ? '#' + clsInfo.rank_in_grade : '-';
      const bonus = clsInfo.bonus_points != null ? Number(clsInfo.bonus_points).toFixed(1) : '0.0';
      const penalty = clsInfo.penalty_points != null ? Number(clsInfo.penalty_points).toFixed(1) : '0.0';
      const pendingV = clsInfo.pending_violations != null ? clsInfo.pending_violations : 0;
      const studentCount = hrClass.student_count || 0;

      html = `
        <div class="edtech-dash-wrap">
          <div class="edtech-hero-card">
            <div class="edtech-hero-inner">
              <div class="edtech-greeting-box">
                <span class="edtech-role-pill" id="dash-role-badge">
                  <i data-lucide="book-open" class="w-3.5 h-3.5 inline"></i> Giáo Viên Chủ Nhiệm
                </span>
                <h2>${greeting}, Thầy/Cô <span id="dash-user-name">${escapeHtml(fullName)}</span>!</h2>
                <p id="dash-welcome-sub">Chủ nhiệm <strong>Chi đoàn ${escapeHtml(hrClass.name || 'Chưa gán')}</strong> · Sĩ số: <strong>${studentCount} học sinh</strong> · Niên khóa 2026–2027.</p>
              </div>
              <div class="edtech-hero-actions">
                <span class="edtech-live-pill">
                  <span class="edtech-live-dot"></span>
                  Trực tiếp (${timeStr})
                </span>
                <button type="button" onclick="loadDashboard()" class="edtech-hero-btn">
                  <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i> Làm mới
                </button>
              </div>
            </div>
          </div>

          <!-- SPOTLIGHT CARD LỚP CHỦ NHIỆM -->
          <div class="edtech-personal-card">
            <div class="flex items-center gap-4">
              <div class="w-14 h-14 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-black text-2xl shadow-sm">
                ${escapeHtml(hrClass.name || 'HK')}
              </div>
              <div>
                <span class="text-xs font-bold text-emerald-800 uppercase tracking-wider">Tiêu điểm Chi đoàn chủ nhiệm</span>
                <h3 class="text-xl font-extrabold text-slate-900 mt-0.5">Chi đoàn ${escapeHtml(hrClass.name || '')}</h3>
                <p class="text-xs text-slate-500">Xếp hạng: <strong class="text-emerald-700">${rank}</strong> toàn trường · <strong class="text-emerald-700">${rankGrade}</strong> Khối ${hrClass.grade || ''}</p>
              </div>
            </div>
            <div class="text-right">
              <span class="text-xs text-slate-500 font-medium">Điểm thi đua tuần:</span>
              <div class="text-3xl font-black text-[#173B70]">${score}đ</div>
              <span class="text-xs text-slate-500">Cộng +${bonus} · Trừ -${penalty}</span>
            </div>
          </div>

          <div class="edtech-kpi-grid">
            <div class="edtech-kpi-card" onclick="navigateTab('students')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Sĩ số Chi đoàn</span>
                <div class="edtech-kpi-icon bg-blue-50 text-blue-600 border border-blue-100"><i data-lucide="users" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-[#173B70]">${studentCount}</span>
                <span class="edtech-kpi-badge bg-blue-50 text-blue-700">Học sinh</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Danh sách lớp</span>
                <span class="text-blue-600 font-semibold">Xem chi tiết →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Biên bản nề nếp</span>
                <div class="edtech-kpi-icon bg-amber-50 text-amber-600 border border-amber-100"><i data-lucide="bell" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-amber-600">${pendingV}</span>
                <span class="edtech-kpi-badge ${pendingV > 0 ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600'}">${pendingV > 0 ? 'Cần nắm' : 'An toàn'}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Theo dõi học sinh</span>
                <span class="text-amber-600 font-semibold">Xem vi phạm →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('competition')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Hạng trong khối ${hrClass.grade || ''}</span>
                <div class="edtech-kpi-icon bg-emerald-50 text-emerald-600 border border-emerald-100"><i data-lucide="trophy" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-emerald-600">${rankGrade}</span>
                <span class="edtech-kpi-badge bg-emerald-50 text-emerald-700">Khối ${hrClass.grade || ''}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>So với các lớp cùng khối</span>
                <span class="text-emerald-700 font-semibold">Bảng thi đua →</span>
              </div>
            </div>
          </div>

          <div class="edtech-chart-card">
            <div class="edtech-chart-header">
              <div>
                <h3 class="edtech-chart-title">Biến Động Điểm Thi Đua Lớp ${escapeHtml(hrClass.name || '')}</h3>
                <p class="edtech-chart-desc">So sánh điểm lớp chủ nhiệm với điểm trung bình toàn trường qua các tuần</p>
              </div>
            </div>
            <div class="edtech-chart-canvas-wrap">
              <canvas id="chart-weekly-trend"></canvas>
            </div>
          </div>
        </div>
      `;
    }

    // ==========================================
    // 3. GIÁO VIÊN BỘ MÔN (GVBM)
    // ==========================================
    else if (isGVBM) {
      const teachCount = stats.teaching_classes_count || 0;
      const reportsSent = stats.reports_sent || 0;

      html = `
        <div class="edtech-dash-wrap">
          <div class="edtech-hero-card">
            <div class="edtech-hero-inner">
              <div class="edtech-greeting-box">
                <span class="edtech-role-pill" id="dash-role-badge">
                  <i data-lucide="bookmark" class="w-3.5 h-3.5 inline"></i> Giáo Viên Bộ Môn
                </span>
                <h2>${greeting}, Thầy/Cô <span id="dash-user-name">${escapeHtml(fullName)}</span>!</h2>
                <p id="dash-welcome-sub">Phân công giảng dạy <strong>${teachCount} lớp</strong> · Năm học 2026–2027.</p>
              </div>
              <div class="edtech-hero-actions">
                <span class="edtech-live-pill">
                  <span class="edtech-live-dot"></span>
                  Trực tiếp (${timeStr})
                </span>
                <button type="button" onclick="loadDashboard()" class="edtech-hero-btn">
                  <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i> Làm mới
                </button>
              </div>
            </div>
          </div>

          <div class="edtech-kpi-grid">
            <div class="edtech-kpi-card">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Lớp tham gia giảng dạy</span>
                <div class="edtech-kpi-icon bg-blue-50 text-blue-600 border border-blue-100"><i data-lucide="book-open" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-[#173B70]">${teachCount}</span>
                <span class="edtech-kpi-badge bg-blue-50 text-blue-700">Lớp học</span>
              </div>
              <div class="edtech-kpi-footer"><span>Phân công chuyên môn</span></div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Biên bản nề nếp đã phản ánh</span>
                <div class="edtech-kpi-icon bg-emerald-50 text-emerald-600 border border-emerald-100"><i data-lucide="check-square" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-emerald-600">${reportsSent}</span>
                <span class="edtech-kpi-badge bg-emerald-50 text-emerald-700">Ghi nhận</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Tuần hiện tại</span>
                <span class="text-emerald-700 font-semibold">Xem nề nếp →</span>
              </div>
            </div>
          </div>

          <div class="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-sm flex items-center justify-between flex-wrap gap-4">
            <div>
              <h4 class="font-extrabold text-slate-800 text-sm">Ghi nhận nề nếp tiết học</h4>
              <p class="text-xs text-slate-500 mt-1 max-w-xl">Thầy/Cô có thể ghi nhận vi phạm tác phong hoặc tuyên dương cá nhân có tinh thần xây dựng bài học xuất sắc trong giờ dạy.</p>
            </div>
            <button onclick="navigateTab('conduct')" class="hk-btn hk-btn-primary">
              <i data-lucide="edit-3" class="w-4 h-4"></i> Ghi nhận nề nếp
            </button>
          </div>
        </div>
      `;
    }

    // ==========================================
    // 4. SAO ĐỎ (ĐỘI TRỰC BAN HỌC SINH)
    // ==========================================
    else if (isSaoDo) {
      const rs = stats.red_star_stats || {};
      const sent = rs.sent != null ? rs.sent : 0;
      const verified = rs.verified != null ? rs.verified : 0;
      const pending = rs.pending != null ? rs.pending : 0;

      html = `
        <div class="edtech-dash-wrap">
          <div class="edtech-hero-card">
            <div class="edtech-hero-inner">
              <div class="edtech-greeting-box">
                <span class="edtech-role-pill" id="dash-role-badge">
                  <i data-lucide="star" class="w-3.5 h-3.5 inline"></i> Đội Trực Ban Sao Đỏ
                </span>
                <h2>${greeting}, <span id="dash-user-name">${escapeHtml(fullName)}</span>!</h2>
                <p id="dash-welcome-sub">Nhiệm vụ trực ban nề nếp & giám sát công bằng thi đua các Chi đoàn · Học kỳ I.</p>
              </div>
              <div class="edtech-hero-actions">
                <span class="edtech-live-pill">
                  <span class="edtech-live-dot"></span>
                  Trực ban (${timeStr})
                </span>
                <button type="button" onclick="loadDashboard()" class="edtech-hero-btn">
                  <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i> Làm mới
                </button>
              </div>
            </div>
          </div>

          <div class="edtech-kpi-grid">
            <div class="edtech-kpi-card">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Nhiệm vụ trực ban</span>
                <div class="edtech-kpi-icon bg-blue-50 text-blue-600 border border-blue-100"><i data-lucide="shield-check" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-[#173B70]">Sao đỏ</span>
                <span class="edtech-kpi-badge bg-blue-50 text-blue-700">Đang trực</span>
              </div>
              <div class="edtech-kpi-footer"><span>Học kỳ I · 2026–2027</span></div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Biên bản đã gửi</span>
                <div class="edtech-kpi-icon bg-amber-50 text-amber-600 border border-amber-100"><i data-lucide="send" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-amber-600">${sent}</span>
                <span class="edtech-kpi-badge bg-amber-50 text-amber-700">Chờ duyệt: ${pending}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Chờ Đoàn trường thẩm tra</span>
                <span class="text-amber-600 font-semibold">Xem danh sách →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Biên bản đã xác minh</span>
                <div class="edtech-kpi-icon bg-emerald-50 text-emerald-600 border border-emerald-100"><i data-lucide="check-circle" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-emerald-600">${verified}</span>
                <span class="edtech-kpi-badge bg-emerald-50 text-emerald-700">Đã duyệt</span>
              </div>
              <div class="edtech-kpi-footer"><span>Được ghi nhận thi đua</span></div>
            </div>
          </div>

          <div class="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-sm flex items-center justify-between flex-wrap gap-4">
            <div>
              <h4 class="font-extrabold text-slate-800 text-sm">Gửi biên bản trực ban nề nếp</h4>
              <p class="text-xs text-slate-500 mt-1 max-w-xl">Ghi nhận chính xác lỗi vi phạm, đúng học sinh và Chi đoàn để đảm bảo tính công bằng và minh bạch trong thi đua toàn trường.</p>
            </div>
            <button onclick="navigateTab('conduct')" class="hk-btn hk-btn-primary">
              <i data-lucide="plus" class="w-4 h-4"></i> Gửi biên bản trực
            </button>
          </div>
        </div>
      `;
    }

    // ==========================================
    // 5. HỌC SINH (STUDENT)
    // ==========================================
    else {
      const clsName = stats.class_name || (currentUser && currentUser.class_name) || 'Chưa xếp lớp';
      const code = stats.student_code || (currentUser && currentUser.student_code) || '-';
      const myV = stats.my_violations_count != null ? stats.my_violations_count : 0;
      const clsScore = stats.class_total_score != null ? Number(stats.class_total_score).toFixed(2) : '100.00';
      const clsRank = stats.class_rank != null ? '#' + stats.class_rank : '-';

      html = `
        <div class="edtech-dash-wrap">
          <div class="edtech-hero-card">
            <div class="edtech-hero-inner">
              <div class="edtech-greeting-box">
                <span class="edtech-role-pill" id="dash-role-badge">
                  <i data-lucide="graduation-cap" class="w-3.5 h-3.5 inline"></i> Học Sinh Trường THPT Hương Khê
                </span>
                <h2>${greeting}, <span id="dash-user-name">${escapeHtml(fullName)}</span>!</h2>
                <p id="dash-welcome-sub">Chi đoàn <strong>${escapeHtml(clsName)}</strong> · Mã HS: <strong>${escapeHtml(code)}</strong> · Niên khóa 2026–2027.</p>
              </div>
              <div class="edtech-hero-actions">
                <span class="edtech-live-pill">
                  <span class="edtech-live-dot"></span>
                  Đồng hành cùng học sinh
                </span>
                <button type="button" onclick="loadDashboard()" class="edtech-hero-btn">
                  <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i> Làm mới
                </button>
              </div>
            </div>
          </div>

          <div class="edtech-kpi-grid">
            <div class="edtech-kpi-card" onclick="navigateTab('profile')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Hồ sơ cá nhân</span>
                <div class="edtech-kpi-icon bg-blue-50 text-blue-600 border border-blue-100"><i data-lucide="user" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-[#173B70]">${escapeHtml(clsName)}</span>
                <span class="edtech-kpi-badge bg-blue-50 text-blue-700">Mã: ${escapeHtml(code)}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Thông tin đoàn viên</span>
                <span class="text-blue-600 font-semibold">Xem hồ sơ →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('competition')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Điểm thi đua lớp tuần này</span>
                <div class="edtech-kpi-icon bg-emerald-50 text-emerald-600 border border-emerald-100"><i data-lucide="award" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-emerald-600">${clsScore}</span>
                <span class="edtech-kpi-badge bg-emerald-50 text-emerald-700">Hạng: ${clsRank}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Toàn trường</span>
                <span class="text-emerald-700 font-semibold">Bảng vàng →</span>
              </div>
            </div>

            <div class="edtech-kpi-card">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Rèn luyện nề nếp cá nhân</span>
                <div class="edtech-kpi-icon bg-${myV > 0 ? 'rose' : 'teal'}-50 text-${myV > 0 ? 'rose' : 'teal'}-600 border border-${myV > 0 ? 'rose' : 'teal'}-100">
                  <i data-lucide="${myV > 0 ? 'alert-circle' : 'smile'}" class="w-5 h-5"></i>
                </div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-${myV > 0 ? 'rose-600' : 'teal-600'}">${myV}</span>
                <span class="edtech-kpi-badge bg-${myV > 0 ? 'rose' : 'teal'}-50 text-${myV > 0 ? 'rose' : 'teal'}-700">
                  ${myV === 0 ? 'Rất tốt' : 'Lưu ý'}
                </span>
              </div>
              <div class="edtech-kpi-footer">
                <span>${myV === 0 ? 'Tuyệt vời! Tiếp tục giữ vững nhé ✨' : 'Cần chú ý nội quy nhà trường'}</span>
              </div>
            </div>
          </div>

          <!-- PODIUM VINH DANH CHO HỌC SINH -->
          <div class="edtech-podium-card">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-extrabold text-[#173B70] text-base flex items-center gap-2">
                <i data-lucide="crown" class="w-4 h-4 text-amber-500"></i>
                Top 3 Chi Đoàn Dẫn Đầu Toàn Trường
              </h3>
              <span class="text-xs text-slate-500">${currentWeekName} · Năm học 2026–2027</span>
            </div>
            <div id="dashboard-podium-content" class="edtech-podium-grid"></div>
          </div>
        </div>
      `;
    }

    // Render HTML vào DOM
    root.innerHTML = html;
    root.setAttribute('aria-busy', 'false');

    // Khởi tạo Lucide Icons
    if (window.lucide) {
      lucide.createIcons();
    }

    // Khởi tạo các biểu đồ và bảng số liệu
    if (isAdmin || isDoanTruong) {
      renderTopPodium(snapshot.classes, _dashboardData.selectedGrade, _dashboardData.selectedPeriod);
      renderDashboardTable(snapshot.classes, _dashboardData.selectedGrade, _dashboardData.selectedPeriod, _dashboardData.searchTerm);
    } else if (isGVCN) {
      const hrClass = stats.homeroom_class || {};
      let myClassTrend = null;
      if (snapshot && snapshot.classes) {
        const found = snapshot.classes.find(c => c.id === hrClass.id || c.name === hrClass.name);
        if (found && found.trend) myClassTrend = found.trend;
      }
      renderWeeklyTrendChart('chart-weekly-trend', snapshot.weekly_trend, myClassTrend, hrClass.name || '');
    } else if (isStudent) {
      renderTopPodium(snapshot.classes, 'ALL', 'week');
    }

  } catch (error) {
    console.error('Lỗi tải Dashboard:', error);
    root.setAttribute('aria-busy', 'false');
    root.innerHTML = '';
    if (errorBox) {
      errorBox.innerHTML = `
        <div class="flex items-center gap-2">
          <i data-lucide="alert-circle" class="w-4 h-4 text-rose-500"></i>
          <span>${escapeHtml(error.message || 'Không thể tải thông tin bảng điều khiển.')}</span>
        </div>
        <button type="button" class="hk-btn hk-btn-secondary text-xs ml-3" onclick="loadDashboard()">Thử lại</button>
      `;
      errorBox.hidden = false;
      if (window.lucide) lucide.createIcons();
    }
  }
}

// Đăng ký toàn cục các hàm tương tác của Dashboard
window.switchDashboardTab = switchDashboardTab;
window.onDashboardFilterChange = onDashboardFilterChange;
window.onDashboardSearch = onDashboardSearch;
"""

def main():
    print("Reading templates/index.html...")
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        index_text = f.read()

    # 1. Replace CSS
    css_start_token = "/* ===== MODERN EDTECH DASHBOARD DESIGN SYSTEM ===== */"
    css_end_token = "/* ===== MODERN SCHOOL PORTAL & EDTECH DESIGN SYSTEM ===== */"
    idx_css_s = index_text.find(css_start_token)
    idx_css_e = index_text.find(css_end_token)
    if idx_css_s != -1 and idx_css_e != -1:
        print(f"Replacing CSS ({idx_css_s} to {idx_css_e})...")
        index_text = index_text[:idx_css_s] + NEW_CSS + "\n    " + index_text[idx_css_e:]
    else:
        print("WARNING: Could not find CSS tokens in index.html!")

    # 2. Replace Tab 1
    tab_start_token = "<!-- TAB 1: DASHBOARD -->"
    tab_end_token = '<section id="tab-student-approvals"'
    idx_tab_s = index_text.find(tab_start_token)
    idx_tab_e = index_text.find(tab_end_token)
    if idx_tab_s != -1 and idx_tab_e != -1:
        print(f"Replacing TAB 1 ({idx_tab_s} to {idx_tab_e})...")
        index_text = index_text[:idx_tab_s] + NEW_TAB_HTML + "\n\n      " + index_text[idx_tab_e:]
    else:
        print("WARNING: Could not find TAB 1 tokens in index.html!")

    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(index_text)
    print("Saved upgraded templates/index.html!")

    # 3. Replace static/app.js
    print("Reading static/app.js...")
    with open(APP_JS_PATH, 'r', encoding='utf-8') as f:
        app_text = f.read()

    app_start_token = "// 1. DASHBOARD MODULE – MODERN EDTECH & CLEAN ACADEMIC SAAS"
    app_end_token = "// 2. CONDUCT & VIOLATIONS MODULE"
    idx_app_s = app_text.find(app_start_token)
    idx_app_e = app_text.find(app_end_token)
    if idx_app_s != -1 and idx_app_e != -1:
        print(f"Replacing app.js dashboard module ({idx_app_s} to {idx_app_e})...")
        app_text = app_text[:idx_app_s] + NEW_APP_JS_MODULE + "\n\n" + app_text[idx_app_e:]
        with open(APP_JS_PATH, 'w', encoding='utf-8') as f:
            f.write(app_text)
        print("Saved upgraded static/app.js!")
    else:
        print("WARNING: Could not find app.js dashboard tokens!")

if __name__ == '__main__':
    main()
