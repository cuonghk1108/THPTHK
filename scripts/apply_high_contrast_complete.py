"""
Complete High Contrast Color System Application Script for HK Student Hub.
Updates both templates/index.html and static/app.js.
"""
from pathlib import Path
import re

BASE_DIR = Path(r"C:\Users\Xuan Cuong\Desktop\hk-student-hub")
INDEX_PATH = BASE_DIR / "templates" / "index.html"
APP_JS_PATH = BASE_DIR / "static" / "app.js"

import sys
sys.path.append(str(BASE_DIR))
from scripts.apply_high_contrast import HIGH_CONTRAST_SHELL_CSS, HIGH_CONTRAST_DASHBOARD_CSS

NEW_APP_JS_CONTRAST = """// 1. DASHBOARD MODULE 2.0 (HIGH-CONTRAST & CRISP EDTECH)
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
// RENDER BỤC VINH DANH TOP 3 OLYMPIC (HIGH CONTRAST)
// ==========================================
function renderTopPodium(classes, gradeFilter = 'ALL', periodKey = 'week') {
  const container = document.getElementById('dashboard-podium-content');
  if (!container) return;

  if (!classes || !classes.length) {
    container.innerHTML = '<div class="py-8 text-center text-slate-700 font-bold text-xs">Chưa có dữ liệu xếp hạng trong kỳ này.</div>';
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
    container.innerHTML = '<div class="py-8 text-center text-slate-700 font-bold text-xs">Không có lớp nào phù hợp bộ lọc.</div>';
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
      <span class="text-xs font-black uppercase tracking-wider text-slate-900">Á Quân · Hạng 2</span>
      <h4 class="podium-class-title text-xl text-slate-950 font-black">${escapeHtml(c2.name)}</h4>
      <div class="podium-score-pill text-2xl text-[#07152b] font-black">${s2}đ</div>
      <div class="podium-sub-text text-slate-900 font-extrabold">Cộng +${b2} · Trừ -${p2}</div>
    </div>
    ` : '<div class="podium-pillar podium-silver opacity-40"><div class="podium-crown-badge">🥈</div><span class="text-xs text-slate-500 font-bold">Đang cập nhật</span></div>'}

    <!-- HẠNG 1 (QUÁN QUÂN - VÀNG) -->
    <div class="podium-pillar podium-gold" onclick="navigateTab('competition')">
      <div class="podium-crown-badge">👑 🥇</div>
      <span class="text-xs font-black uppercase tracking-wider text-amber-950">Dẫn Đầu Toàn Trường · Hạng 1</span>
      <h3 class="podium-class-title text-2xl text-black font-black">${escapeHtml(c1.name)}</h3>
      <div class="podium-score-pill text-3xl text-[#78350f] font-black">${s1}đ</div>
      <div class="podium-sub-text text-amber-950 font-extrabold">Cộng +${b1} · Trừ -${p1} điểm</div>
    </div>

    <!-- HẠNG 3 (QUÝ QUÂN - ĐỒNG) -->
    ${c3 ? `
    <div class="podium-pillar podium-bronze" onclick="navigateTab('competition')">
      <div class="podium-crown-badge">🥉</div>
      <span class="text-xs font-black uppercase tracking-wider text-orange-950">Quý Quân · Hạng 3</span>
      <h4 class="podium-class-title text-xl text-orange-950 font-black">${escapeHtml(c3.name)}</h4>
      <div class="podium-score-pill text-2xl text-[#9a3412] font-black">${s3}đ</div>
      <div class="podium-sub-text text-orange-950 font-extrabold">Cộng +${b3} · Trừ -${p3}</div>
    </div>
    ` : '<div class="podium-pillar podium-bronze opacity-40"><div class="podium-crown-badge">🥉</div><span class="text-xs text-slate-500 font-bold">Đang cập nhật</span></div>'}
  `;
}

// ==========================================
// RENDER BẢNG TỔNG SẮP CHI ĐOÀN (HIGH CONTRAST)
// ==========================================
function renderDashboardTable(classes, gradeFilter = 'ALL', periodKey = 'week', searchTerm = '') {
  const tbody = document.getElementById('dashboard-data-tbody');
  const countSpan = document.getElementById('dashboard-table-count');
  if (!tbody) return;

  if (!classes || !classes.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="py-6 text-center text-slate-700 font-bold text-xs">Không có dữ liệu.</td></tr>';
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
    tbody.innerHTML = '<tr><td colspan="8" class="py-6 text-center text-slate-700 font-bold text-xs">Không tìm thấy Chi đoàn nào phù hợp từ khóa.</td></tr>';
    return;
  }

  tbody.innerHTML = list.map((c, idx) => {
    const pData = c[periodKey] || {};
    const score = pData.total_score != null ? Number(pData.total_score).toFixed(2) : '100.00';
    const bonus = pData.bonus_points != null ? Number(pData.bonus_points).toFixed(1) : '0.0';
    const penalty = pData.penalty_points != null ? Number(pData.penalty_points).toFixed(1) : '0.0';
    const violations = pData.verified_violations_count != null ? pData.verified_violations_count : 0;
    const rankNum = idx + 1;

    let rankBadge = `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-slate-200 text-slate-900 font-black text-xs">${rankNum}</span>`;
    if (rankNum === 1) rankBadge = `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-amber-400 text-slate-950 font-black text-xs shadow border border-amber-600">🥇 1</span>`;
    else if (rankNum === 2) rankBadge = `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-slate-300 text-slate-950 font-black text-xs shadow border border-slate-500">🥈 2</span>`;
    else if (rankNum === 3) rankBadge = `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-orange-400 text-slate-950 font-black text-xs shadow border border-orange-600">🥉 3</span>`;
    else if (rankNum <= 10) rankBadge = `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-emerald-600 text-white font-black text-xs shadow-sm">${rankNum}</span>`;

    const scoreNum = Number(score);
    const progressWidth = Math.min(100, Math.max(0, (scoreNum / 100) * 100));
    let progressColor = 'bg-emerald-600';
    if (scoreNum < 85) progressColor = 'bg-rose-600';
    else if (scoreNum < 95) progressColor = 'bg-amber-500';

    return `
      <tr class="${idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/80'} border-b border-slate-200 hover:bg-blue-100/70 transition-colors font-medium">
        <td class="py-3 px-3.5 text-center">${rankBadge}</td>
        <td class="py-3 px-3.5 font-black text-slate-950 text-sm">${escapeHtml(c.name)}</td>
        <td class="py-3 px-3 text-center"><span class="text-xs font-bold px-2.5 py-0.5 rounded-full bg-slate-200 text-slate-900 border border-slate-300">Khối ${c.grade}</span></td>
        <td class="py-3 px-3 text-right font-black text-emerald-700 text-xs">+${bonus}</td>
        <td class="py-3 px-3 text-right font-black text-rose-700 text-xs">-${penalty}</td>
        <td class="py-3 px-3.5 text-right font-black text-base text-[#07152b]">${score}</td>
        <td class="py-3 px-4">
          <div class="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden flex border border-slate-300" title="${progressWidth}% chuẩn">
            <div class="${progressColor} h-2.5 rounded-full transition-all duration-300" style="width: ${progressWidth}%"></div>
          </div>
        </td>
        <td class="py-3 px-3 text-center">
          <span class="inline-flex items-center justify-center px-2.5 py-1 rounded text-xs font-black ${violations > 0 ? 'bg-rose-600 text-white shadow' : 'bg-slate-200 text-slate-800'}">${violations}</span>
        </td>
      </tr>
    `;
  }).join('');
}

// ==========================================
// RENDER BIỂU ĐỒ XU HƯỚNG CÁC TUẦN (HIGH CONTRAST)
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
  gradSchool.addColorStop(0, 'rgba(29, 78, 216, 0.35)');
  gradSchool.addColorStop(1, 'rgba(29, 78, 216, 0.0)');

  const datasets = [
    {
      label: 'Điểm TB toàn trường',
      data: avgScores,
      borderColor: '#1d4ed8',
      backgroundColor: gradSchool,
      borderWidth: 3.5,
      fill: true,
      tension: 0.35,
      pointRadius: 5,
      pointBackgroundColor: '#ffffff',
      pointBorderColor: '#1d4ed8',
      pointBorderWidth: 2.5,
      pointHoverRadius: 7,
    }
  ];

  if (customClassTrend && customClassTrend.length) {
    const classScores = customClassTrend.map(t => Number(t.total_score).toFixed(2));
    let gradClass = ctx.createLinearGradient(0, 0, 0, 260);
    gradClass.addColorStop(0, 'rgba(5, 150, 105, 0.35)');
    gradClass.addColorStop(1, 'rgba(5, 150, 105, 0.0)');

    datasets.push({
      label: `Lớp ${customClassName || 'chủ nhiệm'}`,
      data: classScores,
      borderColor: '#059669',
      backgroundColor: gradClass,
      borderWidth: 3.5,
      fill: true,
      tension: 0.35,
      pointRadius: 5,
      pointBackgroundColor: '#ffffff',
      pointBorderColor: '#059669',
      pointBorderWidth: 2.5,
      pointHoverRadius: 7,
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
          labels: { font: { size: 12.5, weight: '800', family: 'Inter, system-ui' }, color: '#07152b', boxWidth: 14, usePointStyle: true }
        },
        tooltip: {
          backgroundColor: '#07152b',
          titleFont: { size: 13, weight: '850' },
          bodyFont: { size: 12.5, weight: '700' },
          padding: 12,
          cornerRadius: 10,
          borderColor: '#3b82f6',
          borderWidth: 1.5,
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: ${ctx.raw} điểm`
          }
        }
      },
      scales: {
        y: {
          min: 80,
          max: 105,
          grid: { color: '#e2e8f0', lineWidth: 1.5 },
          ticks: { font: { size: 12, weight: '700' }, color: '#07152b', callback: v => v + 'đ' }
        },
        x: {
          grid: { display: false },
          ticks: { font: { size: 12, weight: '750' }, color: '#07152b' }
        }
      }
    }
  });
}

// ==========================================
// RENDER BIỂU ĐỒ CỘT SO SÁNH (HIGH CONTRAST)
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
    if (n >= 95) return '#1d4ed8'; // Royal Deep Blue
    if (n >= 90) return '#059669'; // Deep Emerald Green
    if (n >= 80) return '#d97706'; // Vivid Amber
    return '#dc2626'; // Ruby Red
  });

  _hkCharts.classComparison = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Điểm thi đua',
        data: scores,
        backgroundColor: backgroundColors,
        borderColor: '#07152b',
        borderWidth: 1.5,
        borderRadius: 8,
        borderSkipped: false,
        maxBarThickness: 36,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 500, easing: 'easeOutQuart' },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#07152b',
          titleFont: { size: 13, weight: '850' },
          bodyFont: { size: 12.5, weight: '700' },
          padding: 12,
          cornerRadius: 10,
          borderColor: '#3b82f6',
          borderWidth: 1.5,
          callbacks: {
            label: (ctx) => ` Điểm: ${ctx.raw}đ`
          }
        }
      },
      scales: {
        y: {
          min: 75,
          max: 105,
          grid: { color: '#e2e8f0', lineWidth: 1.5 },
          ticks: { font: { size: 12, weight: '700' }, color: '#07152b', callback: v => v + 'đ' }
        },
        x: {
          grid: { display: false },
          ticks: { font: { size: 12, weight: '800' }, color: '#07152b' }
        }
      }
    }
  });
}

// ==============================================================================
// HÀM TẢI VÀ DỰNG DASHBOARD CHÍNH CHO 6 VAI TRÒ (HIGH CONTRAST)
// ==============================================================================
async function loadDashboard() {
  const root = document.getElementById('role-dashboard-content');
  const errorBox = document.getElementById('role-dashboard-error');
  if (!root) return;

  destroyAllHkCharts();
  root.setAttribute('aria-busy', 'true');
  root.innerHTML = `
    <div class="space-y-4 animate-pulse">
      <div class="h-36 rounded-2xl bg-gradient-to-r from-blue-900/20 via-indigo-900/20 to-blue-800/20 border-2 border-slate-300"></div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="h-28 rounded-2xl bg-slate-200/80 border-2 border-slate-300"></div>
        <div class="h-28 rounded-2xl bg-slate-200/80 border-2 border-slate-300"></div>
        <div class="h-28 rounded-2xl bg-slate-200/80 border-2 border-slate-300"></div>
        <div class="h-28 rounded-2xl bg-slate-200/80 border-2 border-slate-300"></div>
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
    // 1. ADMIN & ĐOÀN TRƯỜNG COMMAND HUB (HIGH CONTRAST)
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
          <!-- 1. HIGH-CONTRAST HERO CARD -->
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
                  <i data-lucide="refresh-cw" class="w-4 h-4 text-blue-700"></i> Làm mới
                </button>
                <button type="button" onclick="openQuickViolationModal()" class="edtech-hero-btn edtech-hero-btn-primary">
                  <i data-lucide="plus-circle" class="w-4 h-4 text-black"></i> Ghi vi phạm
                </button>
              </div>
            </div>
          </div>

          <!-- 2. 4 HIGH-CONTRAST KPI METRIC CARDS -->
          <div class="edtech-kpi-grid">
            <div class="edtech-kpi-card" onclick="navigateTab('competition')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Điểm TB toàn trường</span>
                <div class="edtech-kpi-icon bg-blue-100 text-blue-800 border-2 border-blue-300">
                  <i data-lucide="award" class="w-6 h-6"></i>
                </div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-[#07152b]">${avgScore}</span>
                <span class="edtech-kpi-badge bg-emerald-100 text-emerald-950 border border-emerald-500 font-black">Chuẩn 100đ</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Thi đua ${currentWeekName}</span>
                <span class="text-blue-700 font-extrabold">Bảng vàng →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Báo cáo chờ duyệt</span>
                <div class="edtech-kpi-icon bg-amber-100 text-amber-800 border-2 border-amber-300">
                  <i data-lucide="clock" class="w-6 h-6"></i>
                </div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-amber-800">${pendingV}</span>
                <span class="edtech-kpi-badge ${pendingV > 0 ? 'bg-amber-400 text-black border border-amber-600 font-black' : 'bg-slate-200 text-slate-800 font-bold'}">
                  ${pendingV > 0 ? 'Cần xử lý' : 'Đã sạch'}
                </span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Biên bản cần thẩm tra</span>
                <span class="text-amber-800 font-extrabold">Xử lý ngay →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Vi phạm hôm nay</span>
                <div class="edtech-kpi-icon bg-rose-100 text-rose-800 border-2 border-rose-300">
                  <i data-lucide="alert-triangle" class="w-6 h-6"></i>
                </div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-rose-700">${todayV}</span>
                <span class="edtech-kpi-badge bg-rose-100 text-rose-950 border border-rose-400 font-black">Tuần: ${verifiedW}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Sao đỏ & GV ghi nhận</span>
                <span class="text-rose-700 font-extrabold">Xem nề nếp →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('student-approvals')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">${isDoan ? 'Biên bản Sao đỏ gửi' : 'Hồ sơ chờ phê duyệt'}</span>
                <div class="edtech-kpi-icon bg-emerald-100 text-emerald-800 border-2 border-emerald-300">
                  <i data-lucide="${isDoan ? 'shield' : 'user-check'}" class="w-6 h-6"></i>
                </div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-emerald-700">${isDoan ? rsPending : pendingAcc}</span>
                <span class="edtech-kpi-badge ${(isDoan ? rsPending : pendingAcc) > 0 ? 'bg-emerald-500 text-white border border-emerald-700 font-black' : 'bg-slate-200 text-slate-800 font-bold'}">
                  ${(isDoan ? rsPending : pendingAcc) > 0 ? 'Mới' : 'Hoàn tất'}
                </span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Kiểm duyệt tài khoản</span>
                <span class="text-emerald-700 font-extrabold">Phê duyệt →</span>
              </div>
            </div>
          </div>

          <!-- 3. HIGH-CONTRAST SEGMENTED CONTROLS -->
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
              <span class="text-xs font-black text-slate-800 mr-1">Kỳ thi đua:</span>
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
                  <h3 class="font-black text-[#07152b] text-lg flex items-center gap-2">
                    <i data-lucide="crown" class="w-5 h-5 text-amber-500"></i>
                    Bục Vinh Danh Top 3 Chi Đoàn Dẫn Đầu
                  </h3>
                  <p class="text-xs text-slate-700 font-semibold mt-0.5">Vinh danh thành tích nề nếp và phong trào thi đua xuất sắc nhất</p>
                </div>
                <div class="edtech-filter-pills">
                  <span class="text-xs font-black text-slate-800 mr-1">Khối lớp:</span>
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
                  <h4 class="font-black text-slate-900 text-sm">Bảng Điểm Thi Đua Toàn Diện</h4>
                  <span id="dashboard-table-count" class="text-xs font-black text-white bg-[#07152b] px-2.5 py-0.5 rounded-full shadow-sm">36 Chi đoàn</span>
                </div>
                <div class="relative">
                  <i data-lucide="search" class="w-4 h-4 text-slate-600 absolute left-3 top-2.5"></i>
                  <input type="text" placeholder="Tìm tên lớp (vd: 10A1)..." oninput="onDashboardSearch(this.value)" class="edtech-search-input">
                </div>
              </div>
              <div class="overflow-x-auto max-h-[400px]">
                <table class="w-full text-left text-xs border-collapse">
                  <thead class="edtech-table-head-dark sticky top-0 z-10 text-xs">
                    <tr>
                      <th class="py-3 px-3.5 text-center w-16">Hạng</th>
                      <th class="py-3 px-3.5">Chi đoàn</th>
                      <th class="py-3 px-3 text-center">Khối</th>
                      <th class="py-3 px-3 text-right">Điểm cộng (+)</th>
                      <th class="py-3 px-3 text-right">Điểm trừ (-)</th>
                      <th class="py-3 px-3.5 text-right">Tổng điểm</th>
                      <th class="py-3 px-4 w-40 text-center">Phong độ chuẩn</th>
                      <th class="py-3 px-3 text-center">Vi phạm</th>
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
              <div class="bg-white p-5 rounded-2xl border-2 border-slate-300 shadow-sm">
                <div class="flex items-center justify-between mb-3 border-b-2 border-slate-100 pb-2">
                  <h4 class="font-black text-slate-900 text-sm flex items-center gap-2">
                    <i data-lucide="alert-octagon" class="w-5 h-5 text-rose-600"></i>
                    Chi Đoàn Cần Đoàn Trường Lưu Ý
                  </h4>
                  <span class="text-xs text-slate-700 font-bold">Tuần hiện tại</span>
                </div>
                <div id="dashboard-attention-classes" class="space-y-2.5">
                  <div class="p-3 bg-amber-50 border-2 border-amber-300 rounded-xl text-xs text-amber-950 flex items-center justify-between">
                    <div>
                      <strong class="font-black text-amber-900">Chi đoàn có điểm dưới 90đ:</strong>
                      <p class="text-slate-800 font-medium mt-0.5">Cần gặp gỡ Ban cán sự và GVCN để cùng chấn chỉnh nề nếp trang phục, giờ giấc.</p>
                    </div>
                    <button onclick="navigateTab('conduct')" class="hk-btn hk-btn-primary text-xs py-1.5 px-3">Kiểm tra ngay</button>
                  </div>
                </div>
              </div>

              <div class="bg-white p-5 rounded-2xl border-2 border-slate-300 shadow-sm">
                <div class="flex items-center justify-between mb-3 border-b-2 border-slate-100 pb-2">
                  <h4 class="font-black text-slate-900 text-sm flex items-center gap-2">
                    <i data-lucide="check-circle" class="w-5 h-5 text-emerald-600"></i>
                    Cẩm Nang Thi Đua & Nề Nếp
                  </h4>
                  <span class="text-xs text-slate-700 font-bold">Quy chuẩn 2026</span>
                </div>
                <div class="space-y-2.5 text-xs text-slate-800 font-medium">
                  <div class="p-3 bg-slate-100 rounded-xl border-1.5 border-slate-300 flex items-center gap-2.5">
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-600 shrink-0"></span>
                    <span><strong class="font-black text-slate-950">Điểm chuẩn ban đầu:</strong> Mỗi Chi đoàn khởi điểm với 100 điểm trọn vẹn mỗi tuần.</span>
                  </div>
                  <div class="p-3 bg-slate-100 rounded-xl border-1.5 border-slate-300 flex items-center gap-2.5">
                    <span class="w-2.5 h-2.5 rounded-full bg-blue-600 shrink-0"></span>
                    <span><strong class="font-black text-slate-950">Trừ điểm trực tiếp:</strong> Đoàn trường và Admin có quyền trừ điểm trực tiếp không cần duyệt.</span>
                  </div>
                  <div class="p-3 bg-slate-100 rounded-xl border-1.5 border-slate-300 flex items-center gap-2.5">
                    <span class="w-2.5 h-2.5 rounded-full bg-amber-600 shrink-0"></span>
                    <span><strong class="font-black text-slate-950">Khiếu nại minh bạch:</strong> GVCN có 48 giờ để phản hồi hoặc khiếu nại biên bản vi phạm.</span>
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
                  <i data-lucide="refresh-cw" class="w-4 h-4 text-blue-700"></i> Làm mới
                </button>
              </div>
            </div>
          </div>

          <!-- SPOTLIGHT CARD LỚP CHỦ NHIỆM (HIGH CONTRAST) -->
          <div class="edtech-personal-card">
            <div class="flex items-center gap-4">
              <div class="w-16 h-16 rounded-2xl bg-emerald-700 text-white flex items-center justify-center font-black text-2xl shadow border-2 border-emerald-900">
                ${escapeHtml(hrClass.name || 'HK')}
              </div>
              <div>
                <span class="text-xs font-black text-emerald-900 uppercase tracking-wider">Tiêu điểm Chi đoàn chủ nhiệm</span>
                <h3 class="text-2xl font-black text-slate-950 mt-0.5">Chi đoàn ${escapeHtml(hrClass.name || '')}</h3>
                <p class="text-xs text-slate-700 font-bold">Xếp hạng: <strong class="text-emerald-800 text-sm">${rank}</strong> toàn trường · <strong class="text-emerald-800 text-sm">${rankGrade}</strong> Khối ${hrClass.grade || ''}</p>
              </div>
            </div>
            <div class="text-right">
              <span class="text-xs text-slate-700 font-bold">Điểm thi đua tuần:</span>
              <div class="text-3xl font-black text-[#07152b]">${score}đ</div>
              <span class="text-xs text-slate-800 font-bold">Cộng <strong class="text-emerald-700">+${bonus}</strong> · Trừ <strong class="text-rose-700">-${penalty}</strong></span>
            </div>
          </div>

          <div class="edtech-kpi-grid">
            <div class="edtech-kpi-card" onclick="navigateTab('students')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Sĩ số Chi đoàn</span>
                <div class="edtech-kpi-icon bg-blue-100 text-blue-900 border-2 border-blue-300"><i data-lucide="users" class="w-6 h-6"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-[#07152b]">${studentCount}</span>
                <span class="edtech-kpi-badge bg-blue-100 text-blue-950 font-black">Học sinh</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Danh sách học sinh</span>
                <span class="text-blue-700 font-black">Xem chi tiết →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Biên bản nề nếp</span>
                <div class="edtech-kpi-icon bg-amber-100 text-amber-900 border-2 border-amber-300"><i data-lucide="bell" class="w-6 h-6"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-amber-800">${pendingV}</span>
                <span class="edtech-kpi-badge ${pendingV > 0 ? 'bg-amber-400 text-black border border-amber-600 font-black' : 'bg-slate-200 text-slate-800 font-bold'}">${pendingV > 0 ? 'Cần nắm' : 'An toàn'}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Theo dõi học sinh</span>
                <span class="text-amber-800 font-black">Xem vi phạm →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('competition')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Hạng trong Khối ${hrClass.grade || ''}</span>
                <div class="edtech-kpi-icon bg-emerald-100 text-emerald-900 border-2 border-emerald-300"><i data-lucide="trophy" class="w-6 h-6"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-emerald-700">${rankGrade}</span>
                <span class="edtech-kpi-badge bg-emerald-100 text-emerald-950 font-black">Khối ${hrClass.grade || ''}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>So với các lớp cùng khối</span>
                <span class="text-emerald-700 font-black">Bảng thi đua →</span>
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
                  <i data-lucide="refresh-cw" class="w-4 h-4 text-blue-700"></i> Làm mới
                </button>
              </div>
            </div>
          </div>

          <div class="edtech-kpi-grid">
            <div class="edtech-kpi-card">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Lớp tham gia giảng dạy</span>
                <div class="edtech-kpi-icon bg-blue-100 text-blue-900 border-2 border-blue-300"><i data-lucide="book-open" class="w-6 h-6"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-[#07152b]">${teachCount}</span>
                <span class="edtech-kpi-badge bg-blue-100 text-blue-950 font-black">Lớp học</span>
              </div>
              <div class="edtech-kpi-footer"><span>Phân công chuyên môn</span></div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Biên bản nề nếp đã phản ánh</span>
                <div class="edtech-kpi-icon bg-emerald-100 text-emerald-900 border-2 border-emerald-300"><i data-lucide="check-square" class="w-6 h-6"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-emerald-700">${reportsSent}</span>
                <span class="edtech-kpi-badge bg-emerald-100 text-emerald-950 font-black">Ghi nhận</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Tuần hiện tại</span>
                <span class="text-emerald-700 font-black">Xem nề nếp →</span>
              </div>
            </div>
          </div>

          <div class="bg-white p-6 rounded-2xl border-2 border-slate-300 shadow-sm flex items-center justify-between flex-wrap gap-4">
            <div>
              <h4 class="font-black text-slate-950 text-base">Ghi nhận nề nếp tiết học</h4>
              <p class="text-xs text-slate-700 font-semibold mt-1 max-w-xl">Thầy/Cô có thể ghi nhận vi phạm tác phong hoặc tuyên dương cá nhân có tinh thần xây dựng bài học xuất sắc trong giờ dạy.</p>
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
                  <i data-lucide="refresh-cw" class="w-4 h-4 text-blue-700"></i> Làm mới
                </button>
              </div>
            </div>
          </div>

          <div class="edtech-kpi-grid">
            <div class="edtech-kpi-card">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Nhiệm vụ trực ban</span>
                <div class="edtech-kpi-icon bg-blue-100 text-blue-900 border-2 border-blue-300"><i data-lucide="shield-check" class="w-6 h-6"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-[#07152b]">Sao đỏ</span>
                <span class="edtech-kpi-badge bg-blue-100 text-blue-950 font-black">Đang trực</span>
              </div>
              <div class="edtech-kpi-footer"><span>Học kỳ I · 2026–2027</span></div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Biên bản đã gửi</span>
                <div class="edtech-kpi-icon bg-amber-100 text-amber-900 border-2 border-amber-300"><i data-lucide="send" class="w-6 h-6"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-amber-800">${sent}</span>
                <span class="edtech-kpi-badge bg-amber-400 text-black border border-amber-600 font-black">Chờ duyệt: ${pending}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Chờ Đoàn trường thẩm tra</span>
                <span class="text-amber-800 font-black">Xem danh sách →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Biên bản đã xác minh</span>
                <div class="edtech-kpi-icon bg-emerald-100 text-emerald-900 border-2 border-emerald-300"><i data-lucide="check-circle" class="w-6 h-6"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-emerald-700">${verified}</span>
                <span class="edtech-kpi-badge bg-emerald-100 text-emerald-950 font-black">Đã duyệt</span>
              </div>
              <div class="edtech-kpi-footer"><span>Được ghi nhận thi đua</span></div>
            </div>
          </div>

          <div class="bg-white p-6 rounded-2xl border-2 border-slate-300 shadow-sm flex items-center justify-between flex-wrap gap-4">
            <div>
              <h4 class="font-black text-slate-950 text-base">Gửi biên bản trực ban nề nếp</h4>
              <p class="text-xs text-slate-700 font-semibold mt-1 max-w-xl">Ghi nhận chính xác lỗi vi phạm, đúng học sinh và Chi đoàn để đảm bảo tính công bằng và minh bạch trong thi đua toàn trường.</p>
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
                  <i data-lucide="refresh-cw" class="w-4 h-4 text-blue-700"></i> Làm mới
                </button>
              </div>
            </div>
          </div>

          <div class="edtech-kpi-grid">
            <div class="edtech-kpi-card" onclick="navigateTab('profile')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Hồ sơ cá nhân</span>
                <div class="edtech-kpi-icon bg-blue-100 text-blue-900 border-2 border-blue-300"><i data-lucide="user" class="w-6 h-6"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-[#07152b]">${escapeHtml(clsName)}</span>
                <span class="edtech-kpi-badge bg-blue-100 text-blue-950 font-black">Mã: ${escapeHtml(code)}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Thông tin đoàn viên</span>
                <span class="text-blue-700 font-black">Xem hồ sơ →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('competition')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Điểm thi đua lớp tuần này</span>
                <div class="edtech-kpi-icon bg-emerald-100 text-emerald-900 border-2 border-emerald-300"><i data-lucide="award" class="w-6 h-6"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-emerald-700">${clsScore}</span>
                <span class="edtech-kpi-badge bg-emerald-100 text-emerald-950 font-black">Hạng: ${clsRank}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Toàn trường</span>
                <span class="text-emerald-700 font-black">Bảng vàng →</span>
              </div>
            </div>

            <div class="edtech-kpi-card">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Rèn luyện nề nếp cá nhân</span>
                <div class="edtech-kpi-icon bg-${myV > 0 ? 'rose' : 'emerald'}-100 text-${myV > 0 ? 'rose' : 'emerald'}-900 border-2 border-${myV > 0 ? 'rose' : 'emerald'}-300">
                  <i data-lucide="${myV > 0 ? 'alert-circle' : 'smile'}" class="w-6 h-6"></i>
                </div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-${myV > 0 ? 'rose-700' : 'emerald-700'}">${myV}</span>
                <span class="edtech-kpi-badge bg-${myV > 0 ? 'rose' : 'emerald'}-100 text-${myV > 0 ? 'rose' : 'emerald'}-950 border border-${myV > 0 ? 'rose' : 'emerald'}-400 font-black">
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
              <h3 class="font-black text-[#07152b] text-lg flex items-center gap-2">
                <i data-lucide="crown" class="w-5 h-5 text-amber-500"></i>
                Top 3 Chi Đoàn Dẫn Đầu Toàn Trường
              </h3>
              <span class="text-xs text-slate-800 font-black">${currentWeekName} · Năm học 2026–2027</span>
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
          <i data-lucide="alert-circle" class="w-4 h-4 text-rose-600"></i>
          <span class="font-bold text-rose-800">${escapeHtml(error.message || 'Không thể tải thông tin bảng điều khiển.')}</span>
        </div>
        <button type="button" class="hk-btn hk-btn-primary text-xs ml-3" onclick="loadDashboard()">Thử lại</button>
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
    # 1. Update templates/index.html CSS
    print("Reading templates/index.html...")
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        index_text = f.read()

    s1 = index_text.find("/* ===== PREMIUM EDTECH APP SHELL")
    s2 = index_text.find("/* ===== MODERN EDTECH DASHBOARD DESIGN SYSTEM 2.0")
    s3 = index_text.find("/* ===== MODERN SCHOOL PORTAL & EDTECH DESIGN SYSTEM ===== */")

    if s1 != -1 and s2 != -1 and s3 != -1:
        print(f"Applying High Contrast CSS ({s1} to {s3})...")
        index_text = index_text[:s1] + HIGH_CONTRAST_SHELL_CSS + "\n" + HIGH_CONTRAST_DASHBOARD_CSS + "\n    " + index_text[s3:]
        # Update cache buster
        index_text = index_text.replace("?v=20261025_06_revamp_all", "?v=20261025_07_high_contrast")
        with open(INDEX_PATH, 'w', encoding='utf-8') as f:
            f.write(index_text)
        print("Updated templates/index.html with High Contrast CSS!")
    else:
        print(f"CSS tokens not found in index.html: s1={s1}, s2={s2}, s3={s3}")

    # 2. Update static/app.js
    print("Reading static/app.js...")
    with open(APP_JS_PATH, 'r', encoding='utf-8') as f:
        app_text = f.read()

    app_start = app_text.find("// 1. DASHBOARD MODULE 2.0")
    app_end = app_text.find("// 2. CONDUCT & VIOLATIONS MODULE")
    if app_start != -1 and app_end != -1:
        print(f"Applying High Contrast to app.js ({app_start} to {app_end})...")
        app_text = app_text[:app_start] + NEW_APP_JS_CONTRAST + "\n\n" + app_text[app_end:]
        with open(APP_JS_PATH, 'w', encoding='utf-8') as f:
            f.write(app_text)
        print("Updated static/app.js with High Contrast Module!")
    else:
        print("Could not find app.js dashboard module bounds!")

if __name__ == '__main__':
    main()
