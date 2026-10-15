/**
 * HK Student Hub – Frontend Application Logic
 * Trường THPT Hương Khê – Hà Tĩnh
 * Bảo mật RBAC & Xác thực đăng nhập nghiêm ngặt
 */

// Global State
let currentUser = null;
let currentPeriod = null;
let classesCache = [];
let rulesCache = [];
let allUsersCache = [];
let activeTab = 'dashboard';
let trendChartInstance = null;

// CSRF Token Helper
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Toast Notifications
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  const colors = {
    success: 'bg-emerald-600 text-white',
    error: 'bg-rose-600 text-white',
    warning: 'bg-amber-500 text-white',
    info: 'bg-brand-600 text-white'
  };

  toast.className = `${colors[type] || colors.info} px-4 py-3 rounded-xl shadow-lg text-xs font-medium flex items-center space-x-2 pointer-events-auto transform transition duration-300 ease-out translate-y-2 opacity-0`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  }, 10);

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// App Initialization
document.addEventListener('DOMContentLoaded', async () => {
  await checkAuthStatus();
  lucide.createIcons();
});

// ==========================================
// AUTHENTICATION & LOGIN WORKFLOW
// ==========================================

async function checkAuthStatus() {
  try {
    const res = await fetch('/api/core/auth/me/');
    const data = await res.json();
    
    if (data.authenticated && data.user) {
      currentUser = data.user;
      hideLoginScreen();
      updateUserUI();
      await loadMetadata();
      await loadDashboard();
    } else {
      currentUser = null;
      showLoginScreen();
    }
  } catch (err) {
    console.error('Lỗi kiểm tra xác thực:', err);
    showLoginScreen();
  }
}

function showLoginScreen() {
  const overlay = document.getElementById('login-overlay');
  if (overlay) overlay.classList.remove('hidden');
}

function hideLoginScreen() {
  const overlay = document.getElementById('login-overlay');
  if (overlay) overlay.classList.add('hidden');
}

function fillTestAccount(username, password) {
  document.getElementById('login-username').value = username;
  document.getElementById('login-password').value = password;
  document.getElementById('btn-login-submit').focus();
}

async function handleLoginSubmit(e) {
  e.preventDefault();
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;
  const errorBox = document.getElementById('login-error-alert');

  errorBox.classList.add('hidden');
  errorBox.textContent = '';

  try {
    const res = await fetch('/api/core/auth/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();

    if (res.ok) {
      currentUser = data.user;
      hideLoginScreen();
      updateUserUI();
      showToast(data.message, 'success');
      await loadMetadata();
      await loadDashboard();
      navigateTab('dashboard');
    } else {
      errorBox.textContent = data.error || 'Đăng nhập thất bại. Vui lòng thử lại.';
      errorBox.classList.remove('hidden');
    }
  } catch (err) {
    errorBox.textContent = 'Không thể kết nối đến máy chủ. Vui lòng thử lại sau.';
    errorBox.classList.remove('hidden');
  }
}

async function handleLogout() {
  if (!confirm('Bạn có chắc chắn muốn đăng xuất khỏi hệ thống?')) return;
  try {
    await fetch('/api/core/auth/logout/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken')
      }
    });
    currentUser = null;
    showToast('Đã đăng xuất an toàn', 'info');
    showLoginScreen();
    // Reset form
    document.getElementById('login-password').value = '';
  } catch (err) {
    showToast('Lỗi khi đăng xuất', 'error');
  }
}

function updateUserUI() {
  if (!currentUser) return;
  
  // Set display name & role in header
  document.getElementById('user-display-name').textContent = currentUser.full_name || currentUser.username;
  document.getElementById('user-role-text').textContent = currentUser.role_display;
  document.getElementById('dash-user-name').textContent = currentUser.full_name || currentUser.username;
  document.getElementById('dash-role-badge').textContent = currentUser.role_display;
  
  // Avatar initials
  const initials = (currentUser.full_name || currentUser.username).split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  document.getElementById('user-avatar-text').textContent = initials;

  // Admin Only Menu: Quản lý Phân quyền
  const adminNav = document.getElementById('nav-btn-users');
  if (adminNav) {
    if (currentUser.role === 'ADMIN') {
      adminNav.classList.remove('hidden');
    } else {
      adminNav.classList.add('hidden');
    }
  }

  // Quick Action Widget: Show for Sao đỏ, GV, Đoàn trường, Admin
  const quickWidget = document.getElementById('quick-action-widget');
  if (quickWidget) {
    if (currentUser.role === 'HOC_SINH') {
      quickWidget.classList.add('hidden');
    } else {
      quickWidget.classList.remove('hidden');
    }
  }

  // Personalized role notice on dashboard
  const banner = document.getElementById('role-personalized-banner');
  if (currentUser.role === 'GVCN') {
    banner.className = 'p-4 bg-blue-50 border border-blue-200 rounded-2xl flex items-center justify-between';
    banner.innerHTML = `
      <div class="flex items-center space-x-3">
        <div class="p-2 bg-brand-600 text-white rounded-xl"><i data-lucide="users" class="w-5 h-5"></i></div>
        <div>
          <h4 class="font-bold text-xs text-brand-900">Không gian quản lý lớp chủ nhiệm: 10A1</h4>
          <p class="text-[11px] text-slate-500">Bạn đang theo dõi nền nếp, tiếp nhận cảnh báo sớm và ghi nhận biện pháp hỗ trợ học sinh của lớp mình.</p>
        </div>
      </div>
      <button onclick="navigateTab('conduct')" class="px-3 py-1.5 bg-brand-600 text-white rounded-lg text-xs font-semibold">Xem lớp mình</button>
    `;
  } else if (currentUser.role === 'HOC_SINH') {
    banner.className = 'p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center justify-between';
    banner.innerHTML = `
      <div class="flex items-center space-x-3">
        <div class="p-2 bg-emerald-600 text-white rounded-xl"><i data-lucide="user-check" class="w-5 h-5"></i></div>
        <div>
          <h4 class="font-bold text-xs text-emerald-900">Cổng thông tin học sinh: ${currentUser.full_name || currentUser.username}</h4>
          <p class="text-[11px] text-slate-500">Tra cứu vi phạm nền nếp cá nhân, gửi giải trình khiếu nại hoặc tâm sự tại Góc sẻ chia.</p>
        </div>
      </div>
      <button onclick="navigateTab('counseling')" class="px-3 py-1.5 bg-rose-600 text-white rounded-lg text-xs font-semibold">Vào Góc sẻ chia</button>
    `;
  } else if (currentUser.role === 'CHUYEN_VIEN_TAM_LY') {
    banner.className = 'p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-center justify-between';
    banner.innerHTML = `
      <div class="flex items-center space-x-3">
        <div class="p-2 bg-rose-600 text-white rounded-xl"><i data-lucide="shield-check" class="w-5 h-5"></i></div>
        <div>
          <h4 class="font-bold text-xs text-rose-900">Chuyên viên tư vấn tâm lý học đường</h4>
          <p class="text-[11px] text-slate-500">Bạn được phân quyền chuyên biệt tiếp nhận tâm sự học sinh, hẹn lịch trao đổi và lưu ghi chép chuyên môn.</p>
        </div>
      </div>
      <button onclick="navigateTab('counseling')" class="px-3 py-1.5 bg-rose-600 text-white rounded-lg text-xs font-semibold">Mở Hộp thư tư vấn</button>
    `;
  } else {
    banner.className = 'hidden';
  }

  lucide.createIcons();
}

// Navigation
function navigateTab(tabName) {
  // If not authenticated, cannot navigate
  if (!currentUser) {
    showLoginScreen();
    return;
  }

  // Guard: Users tab is strictly for ADMIN
  if (tabName === 'users' && currentUser.role !== 'ADMIN') {
    showToast('Chỉ Quản trị viên hệ thống (Admin) mới có quyền truy cập trang phân quyền', 'error');
    return;
  }

  activeTab = tabName;
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
  const targetPane = document.getElementById(`tab-${tabName}`);
  if (targetPane) targetPane.classList.remove('hidden');

  // Update nav buttons
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.remove('bg-brand-50', 'text-brand-900', 'border-brand-100');
    el.classList.add('text-slate-600');
  });
  const activeBtn = document.getElementById(`nav-btn-${tabName}`);
  if (activeBtn) {
    activeBtn.classList.add('bg-brand-50', 'text-brand-900', 'border-brand-100');
    activeBtn.classList.remove('text-slate-600');
  }

  // Load relevant tab data
  if (tabName === 'dashboard') loadDashboard();
  else if (tabName === 'conduct') loadConductViolations();
  else if (tabName === 'competition') loadCompetitionScores();
  else if (tabName === 'alerts') loadEarlyAlerts();
  else if (tabName === 'counseling') loadCounselorInbox();
  else if (tabName === 'reports') loadReportsHistory();
  else if (tabName === 'users') loadUsersManagement();
  else if (tabName === 'settings') loadAuditLogs();

  lucide.createIcons();
}

// Load metadata (classes, rules)
async function loadMetadata() {
  try {
    const [classesRes, rulesRes] = await Promise.all([
      fetch('/api/conduct/classes/'),
      fetch('/api/conduct/rules/')
    ]);

    const classesData = await classesRes.json();
    classesCache = classesData.results || classesData;

    const rulesData = await rulesRes.json();
    rulesCache = rulesData.results || rulesData;

    // Populate modal class dropdown & filter
    const modalClassSelect = document.getElementById('modal-violation-class');
    const filterClassSelect = document.getElementById('filter-conduct-class');
    
    if (modalClassSelect) {
      modalClassSelect.innerHTML = '<option value="">-- Chọn lớp học --</option>' +
        classesCache.map(c => `<option value="${c.id}">Lớp ${c.name} (Khối ${c.grade})</option>`).join('');
    }
    if (filterClassSelect) {
      filterClassSelect.innerHTML = '<option value="">Tất cả các lớp</option>' +
        classesCache.map(c => `<option value="${c.id}">Lớp ${c.name}</option>`).join('');
    }

    // Populate rules dropdown
    const modalRuleSelect = document.getElementById('modal-violation-rule');
    if (modalRuleSelect) {
      modalRuleSelect.innerHTML = '<option value="">-- Chọn lỗi vi phạm --</option>' +
        rulesCache.map(r => `<option value="${r.id}">[${r.code}] ${r.name} (-${r.default_points_deducted}đ)</option>`).join('');
    }
  } catch (err) {
    console.error('Lỗi tải danh mục lớp và nội quy:', err);
  }
}

// ==========================================
// 1. DASHBOARD MODULE
// ==========================================
async function loadDashboard() {
  try {
    const res = await fetch('/api/core/system/stats/');
    const stats = await res.json();

    document.getElementById('stat-violations-today').textContent = stats.violations_today || 0;
    document.getElementById('stat-violations-pending').textContent = stats.violations_pending || 0;
    document.getElementById('stat-violations-week').textContent = stats.violations_verified_week || 0;
    document.getElementById('stat-alerts-active').textContent = stats.alerts_active || 0;
    
    // Sidebar alert counter badge
    const alertBadge = document.getElementById('sidebar-alert-badge');
    if (stats.alerts_active > 0) {
      alertBadge.textContent = stats.alerts_active;
      alertBadge.classList.remove('hidden');
    } else {
      alertBadge.classList.add('hidden');
    }

    // Set 5th card counts
    const classCnt = document.getElementById('stat-classes-count');
    const stuCnt = document.getElementById('stat-students-count');
    if (classCnt) classCnt.textContent = stats.total_classes || 9;
    if (stuCnt) stuCnt.textContent = stats.total_students || 362;

    renderTrendChart();
    renderCategoryDoughnutChart();
    loadDashboardLeaderboard();
    loadDashboardRecentViolations();
  } catch (err) {
    console.error('Lỗi tải thống kê dashboard:', err);
  }
}

let categoryChartInstance = null;
function renderCategoryDoughnutChart() {
  const ctx = document.getElementById('categoryDoughnutChart');
  if (!ctx) return;

  if (categoryChartInstance) {
    categoryChartInstance.destroy();
  }

  categoryChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Chuyên cần', 'Tác phong', 'Kỷ luật', 'Vệ sinh', 'ATGT'],
      datasets: [{
        data: [42, 28, 16, 9, 5],
        backgroundColor: ['#3b82f6', '#8b5cf6', '#f59e0b', '#10b981', '#ef4444'],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              return ` ${context.label}: ${context.raw}%`;
            }
          }
        }
      }
    }
  });
}

function renderTrendChart() {
  const ctx = document.getElementById('violationsTrendChart');
  if (!ctx) return;

  if (trendChartInstance) {
    trendChartInstance.destroy();
  }

  trendChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm (Hôm nay)', 'Thứ Sáu', 'Thứ Bảy'],
      datasets: [
        {
          label: 'Vi phạm đã xác minh',
          data: [3, 2, 4, 1, 0, 0],
          backgroundColor: '#3b82f6',
          borderRadius: 8
        },
        {
          label: 'Chờ xác minh',
          data: [0, 1, 1, 2, 0, 0],
          backgroundColor: '#f59e0b',
          borderRadius: 8
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } }
      },
      scales: {
        y: { beginAtZero: true, ticks: { stepSize: 1, font: { size: 10 } } },
        x: { ticks: { font: { size: 11 } } }
      }
    }
  });
}

async function loadDashboardLeaderboard() {
  const container = document.getElementById('dash-top-classes-list');
  try {
    const res = await fetch('/api/competition/periods/1/scores/');
    const data = await res.json();
    const scores = (data.scores || []).slice(0, 5);

    if (scores.length === 0) {
      container.innerHTML = '<div class="text-center py-4 text-xs text-slate-400">Chưa có dữ liệu xếp hạng</div>';
      return;
    }

    container.innerHTML = scores.map(s => {
      let rankBadge = `<span class="w-5 h-5 rounded-full bg-slate-100 text-slate-700 font-bold text-xs flex items-center justify-center">${s.rank}</span>`;
      if (s.rank === 1) rankBadge = `<span class="w-5 h-5 rounded-full bg-amber-400 text-brand-900 font-bold text-xs flex items-center justify-center shadow-sm">1</span>`;
      else if (s.rank === 2) rankBadge = `<span class="w-5 h-5 rounded-full bg-slate-300 text-slate-900 font-bold text-xs flex items-center justify-center">2</span>`;
      else if (s.rank === 3) rankBadge = `<span class="w-5 h-5 rounded-full bg-amber-700 text-white font-bold text-xs flex items-center justify-center">3</span>`;

      return `
        <div class="flex items-center justify-between p-2 rounded-xl bg-slate-50 border border-slate-100">
          <div class="flex items-center space-x-2.5">
            ${rankBadge}
            <div>
              <div class="font-bold text-xs text-slate-800">Lớp ${s.class_name}</div>
              <div class="text-[10px] text-slate-400">Khối ${s.grade} • ${s.verified_violations_count} vi phạm</div>
            </div>
          </div>
          <div class="text-right">
            <span class="font-bold text-xs text-brand-700">${parseFloat(s.total_score).toFixed(1)}đ</span>
            ${s.bonus_points > 0 ? `<div class="text-[10px] text-emerald-600">+${parseFloat(s.bonus_points).toFixed(1)}đ cộng</div>` : ''}
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    container.innerHTML = '<div class="text-center py-4 text-xs text-slate-400">Chưa mở kỳ thi đua</div>';
  }
}

async function loadDashboardRecentViolations() {
  const tbody = document.getElementById('dash-recent-violations-body');
  try {
    const res = await fetch('/api/conduct/violations/?limit=5');
    const data = await res.json();
    const items = data.results || data;

    if (items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center py-6 text-slate-400">Chưa có vi phạm nào được ghi nhận.</td></tr>';
      return;
    }

    tbody.innerHTML = items.slice(0, 5).map(v => `
      <tr class="hover:bg-slate-50/80 transition">
        <td class="py-2.5 px-3 font-mono font-semibold text-slate-700">${v.record_code}</td>
        <td class="py-2.5 px-3 text-slate-500">${new Date(v.occurred_at).toLocaleDateString('vi-VN')}</td>
        <td class="py-2.5 px-3 font-medium text-slate-800">${v.class_name}</td>
        <td class="py-2.5 px-3 text-slate-700">${v.student_name}</td>
        <td class="py-2.5 px-3 font-medium text-slate-900">${v.rule_name}</td>
        <td class="py-2.5 px-3 text-rose-600 font-semibold">${v.points_deducted > 0 ? `-${v.points_deducted}đ` : '0đ'}</td>
        <td class="py-2.5 px-3">${getStatusBadge(v.status, v.status_display)}</td>
        <td class="py-2.5 px-3 text-right">
          ${getActionButtonForViolation(v)}
        </td>
      </tr>
    `).join('');
    lucide.createIcons();
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-center py-6 text-rose-500">Lỗi tải dữ liệu.</td></tr>';
  }
}

// ==========================================
// 2. CONDUCT & VIOLATIONS MODULE
// ==========================================
async function loadConductViolations() {
  const tbody = document.getElementById('conduct-violations-tbody');
  const classId = document.getElementById('filter-conduct-class')?.value || '';
  const statusVal = document.getElementById('filter-conduct-status')?.value || '';
  const dateFrom = document.getElementById('filter-conduct-from')?.value || '';
  const dateTo = document.getElementById('filter-conduct-to')?.value || '';

  let url = `/api/conduct/violations/?class_id=${classId}&status=${statusVal}&date_from=${dateFrom}&date_to=${dateTo}`;

  try {
    tbody.innerHTML = '<tr><td colspan="10" class="text-center py-8 text-slate-400">Đang tải dữ liệu...</td></tr>';
    const res = await fetch(url);
    const data = await res.json();
    const items = data.results || data;

    document.getElementById('conduct-count-summary').textContent = `Hiển thị: ${items.length} bản ghi`;

    if (items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="10" class="text-center py-10 text-slate-400">Không tìm thấy bản ghi vi phạm phù hợp.</td></tr>';
      return;
    }

    tbody.innerHTML = items.map(v => `
      <tr class="hover:bg-slate-50 transition border-b border-slate-100">
        <td class="py-3 px-3 font-mono font-semibold text-slate-800">${v.record_code}</td>
        <td class="py-3 px-3 text-slate-500">
          <div>${new Date(v.occurred_at).toLocaleDateString('vi-VN')}</div>
          <div class="text-[10px] text-slate-400">${new Date(v.occurred_at).toLocaleTimeString('vi-VN', {hour: '2-digit', minute:'2-digit'})}</div>
        </td>
        <td class="py-3 px-3 font-bold text-slate-800">Lớp ${v.class_name}</td>
        <td class="py-3 px-3 text-slate-700">
          <div class="font-medium">${v.student_name}</div>
          <div class="text-[10px] text-slate-400">Người báo: ${v.reporter_name}</div>
        </td>
        <td class="py-3 px-3">
          <div class="font-medium text-slate-900">${v.rule_name}</div>
          <div class="text-[10px] text-slate-500">${v.rule_category}</div>
        </td>
        <td class="py-3 px-3 text-slate-500">${v.location}</td>
        <td class="py-3 px-3 text-rose-600 font-bold">
          ${v.points_deducted > 0 ? `-${v.points_deducted}đ` : '<span class="text-slate-400 font-normal">Chưa trừ</span>'}
        </td>
        <td class="py-3 px-3">${getStatusBadge(v.status, v.status_display)}</td>
        <td class="py-3 px-3 text-center">
          ${v.evidence_image_url ? `
            <a href="${v.evidence_image_url}" target="_blank" class="p-1.5 bg-blue-50 text-brand-700 hover:bg-blue-100 rounded-lg inline-flex" title="Xem ảnh minh chứng">
              <i data-lucide="image" class="w-4 h-4"></i>
            </a>
          ` : '<span class="text-slate-300 text-[10px]">Không có</span>'}
        </td>
        <td class="py-3 px-3 text-right">
          ${getActionButtonForViolation(v)}
        </td>
      </tr>
    `).join('');
    lucide.createIcons();
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="10" class="text-center py-8 text-rose-500">Lỗi tải danh sách vi phạm.</td></tr>';
  }
}

function getStatusBadge(status, label) {
  const map = {
    PENDING: 'bg-amber-100 text-amber-800 border border-amber-200',
    VERIFIED: 'bg-emerald-100 text-emerald-800 border border-emerald-200',
    REJECTED: 'bg-slate-100 text-slate-600 border border-slate-200',
    ADJUSTED: 'bg-purple-100 text-purple-800 border border-purple-200',
    APPEALING: 'bg-rose-100 text-rose-800 border border-rose-200 font-bold animate-pulse',
  };
  return `<span class="badge ${map[status] || 'bg-slate-100 text-slate-700'}">${label}</span>`;
}

function getActionButtonForViolation(v) {
  const canVerify = currentUser && (currentUser.role === 'ADMIN' || currentUser.role === 'DOAN_TRUONG' || currentUser.can_verify_violations);
  const canAppeal = currentUser && (
    (currentUser.role === 'HOC_SINH' && v.student_name && v.student_name.includes(currentUser.full_name)) ||
    (currentUser.role === 'GVCN' && v.class_name === '10A1')
  );

  let btns = `<button onclick="openViolationDetailModal(${v.id})" class="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-[11px] font-medium transition mr-1">Chi tiết</button>`;

  if (canVerify && v.status === 'PENDING') {
    btns += `<button onclick="openVerifyModal(${v.id}, '${v.record_code}', '${v.student_name} (${v.class_name})', '${v.rule_name}', '${v.description || ''}')" class="px-2.5 py-1 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-[11px] font-semibold transition">Xác minh</button>`;
  } else if (canVerify && v.status === 'APPEALING') {
    btns += `<button onclick="openVerifyModal(${v.id}, '${v.record_code}', '${v.student_name}', '${v.rule_name}', 'Khiếu nại: ${v.appeal_reason || ''}')" class="px-2.5 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-[11px] font-semibold transition">Duyệt khiếu nại</button>`;
  }

  if (canAppeal && v.status === 'VERIFIED') {
    btns += `<button onclick="openAppealModal(${v.id})" class="px-2.5 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-[11px] font-semibold transition">Khiếu nại</button>`;
  }

  return btns;
}

async function openViolationDetailModal(id) {
  try {
    const res = await fetch(`/api/conduct/violations/${id}/`);
    if (!res.ok) {
      showToast('Không thể tải chi tiết bản ghi', 'error');
      return;
    }
    const v = await res.json();
    
    document.getElementById('detail-code').textContent = v.record_code || `VP-${v.id}`;
    document.getElementById('detail-time').textContent = new Date(v.occurred_at).toLocaleString('vi-VN');
    document.getElementById('detail-status-badge').innerHTML = getStatusBadge(v.status, v.status_display);
    document.getElementById('detail-class').textContent = 'Lớp ' + (v.class_name || 'N/A');
    document.getElementById('detail-student').textContent = (v.student_name || 'Tập thể lớp') + (v.reporter_name ? ` (Báo bởi: ${v.reporter_name})` : '');
    document.getElementById('detail-rule').textContent = (v.rule_name || 'N/A') + (v.rule_category ? ` - ${v.rule_category}` : '');
    document.getElementById('detail-points').textContent = v.points_deducted > 0 ? `-${v.points_deducted}đ` : 'Chưa áp dụng trừ điểm';
    document.getElementById('detail-desc').textContent = (v.location ? `[Vị trí: ${v.location}] ` : '') + (v.description || 'Không có mô tả chi tiết.');

    // Evidence image
    const evidenceContainer = document.getElementById('detail-evidence-container');
    const evidenceImg = document.getElementById('detail-evidence-img');
    if (v.evidence_image_url) {
      evidenceImg.src = v.evidence_image_url;
      evidenceContainer.classList.remove('hidden');
    } else {
      evidenceContainer.classList.add('hidden');
      evidenceImg.src = '';
    }

    // Verification Box
    const verBox = document.getElementById('detail-verification-box');
    if (v.verifier_name || v.verified_at || v.verification_notes) {
      verBox.classList.remove('hidden');
      document.getElementById('detail-verification-notes').textContent = v.verification_notes || '(Không có ghi chú thêm)';
      document.getElementById('detail-verification-meta').textContent = `Xác minh bởi: ${v.verifier_name || 'Đoàn trường'} vào lúc ${v.verified_at ? new Date(v.verified_at).toLocaleString('vi-VN') : 'N/A'}`;
    } else {
      verBox.classList.add('hidden');
    }

    // Appeal Box
    const appealBox = document.getElementById('detail-appeal-box');
    if (v.appeal_reason || v.status === 'APPEALING') {
      appealBox.classList.remove('hidden');
      document.getElementById('detail-appeal-reason').textContent = v.appeal_reason || 'Đang chờ nội dung giải trình...';
      document.getElementById('detail-appeal-meta').textContent = `Thời gian khiếu nại: ${v.appeal_submitted_at ? new Date(v.appeal_submitted_at).toLocaleString('vi-VN') : 'Đang xử lý'}`;
    } else {
      appealBox.classList.add('hidden');
    }

    // Timeline / Reviews
    const timelineList = document.getElementById('detail-timeline-list');
    if (v.reviews && v.reviews.length > 0) {
      timelineList.innerHTML = v.reviews.map(h => `
        <div class="p-2.5 bg-slate-50 rounded-lg border border-slate-100 flex items-start justify-between">
          <div>
            <div class="font-bold text-slate-700">${h.performer_name || 'Hệ thống'} <span class="font-normal text-slate-500">chuyển trạng thái:</span> <span class="text-brand-700 font-semibold">${h.previous_status} &rarr; ${h.new_status}</span></div>
            <div class="text-slate-600 mt-0.5">${h.reason || 'Không có ghi chú thêm'} (Điểm: -${h.points_applied || 0}đ)</div>
          </div>
          <span class="text-[10px] text-slate-400 whitespace-nowrap ml-2">${new Date(h.created_at).toLocaleString('vi-VN')}</span>
        </div>
      `).join('');
    } else {
      timelineList.innerHTML = '<div class="text-slate-400 italic text-[11px] p-2 bg-slate-50 rounded-lg border border-slate-100">Bản ghi ban đầu do Sao đỏ/người trực ghi nhận, chưa có điều chỉnh bổ sung.</div>';
    }

    document.getElementById('modal-violation-detail').classList.remove('hidden');
    lucide.createIcons();
  } catch (err) {
    showToast('Lỗi hiển thị chi tiết bản ghi', 'error');
  }
}

function closeViolationDetailModal() {
  document.getElementById('modal-violation-detail').classList.add('hidden');
}

function openQuickViolationModal() {
  const modal = document.getElementById('modal-quick-violation');
  modal.classList.remove('hidden');
  document.getElementById('modal-violation-time').value = new Date().toISOString().slice(0, 16);
  lucide.createIcons();
}

function closeQuickViolationModal() {
  document.getElementById('modal-quick-violation').classList.add('hidden');
}

async function handleClassChangeForStudents(classId) {
  const select = document.getElementById('modal-violation-student');
  select.innerHTML = '<option value="">-- Cả tập thể lớp --</option>';
  if (!classId) return;

  try {
    const res = await fetch(`/api/conduct/students/?class_id=${classId}`);
    const data = await res.json();
    const students = data.results || data;
    students.forEach(s => {
      select.innerHTML += `<option value="${s.id}">${s.full_name} (${s.student_code})</option>`;
    });
  } catch (err) {
    console.error('Lỗi tải danh sách học sinh:', err);
  }
}

async function handleQuickViolationSubmit(e) {
  e.preventDefault();
  const form = document.getElementById('quick-violation-form');
  const formData = new FormData();

  formData.append('school_class', document.getElementById('modal-violation-class').value);
  formData.append('student', document.getElementById('modal-violation-student').value || '');
  formData.append('rule', document.getElementById('modal-violation-rule').value);
  formData.append('location', document.getElementById('modal-violation-location').value);
  formData.append('description', document.getElementById('modal-violation-desc').value);
  formData.append('occurred_at', document.getElementById('modal-violation-time').value);

  const fileInput = document.getElementById('modal-violation-file');
  if (fileInput.files.length > 0) {
    formData.append('evidence_image', fileInput.files[0]);
  }

  try {
    const res = await fetch('/api/conduct/violations/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: formData
    });
    const data = await res.json();

    if (res.ok) {
      showToast(`Đã gửi bản ghi ${data.record_code} thành công (Chờ xác minh)`, 'success');
      closeQuickViolationModal();
      form.reset();
      loadConductViolations();
      loadDashboard();
    } else {
      showToast(data.error || 'Lỗi gửi bản ghi', 'error');
    }
  } catch (err) {
    showToast('Lỗi kết nối máy chủ', 'error');
  }
}

function openVerifyModal(id, code, target, rule, desc) {
  document.getElementById('verify-violation-id').value = id;
  document.getElementById('verify-modal-code').textContent = code;
  document.getElementById('verify-modal-target').textContent = target;
  document.getElementById('verify-modal-rule').textContent = rule;
  document.getElementById('verify-modal-desc').textContent = desc || 'Không có mô tả thêm.';
  document.getElementById('modal-verify-violation').classList.remove('hidden');
}

function closeVerifyModal() {
  document.getElementById('modal-verify-violation').classList.add('hidden');
}

function handleVerifyStatusChange(status) {
  const pointsWrapper = document.getElementById('verify-points-wrapper');
  if (status === 'REJECTED') {
    pointsWrapper.classList.add('hidden');
  } else {
    pointsWrapper.classList.remove('hidden');
  }
}

async function handleVerifySubmit(e) {
  e.preventDefault();
  const id = document.getElementById('verify-violation-id').value;
  const status = document.getElementById('verify-status-select').value;
  const adjusted_points = status === 'REJECTED' ? 0 : parseFloat(document.getElementById('verify-points-input').value || 2.0);
  const verification_notes = document.getElementById('verify-notes-input').value;

  try {
    const res = await fetch(`/api/conduct/violations/${id}/verify/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({ status, adjusted_points, verification_notes })
    });
    const data = await res.json();

    if (res.ok) {
      showToast(data.message, 'success');
      closeVerifyModal();
      loadConductViolations();
      loadDashboard();
      if (activeTab === 'competition') loadCompetitionScores();
    } else {
      showToast(data.error || 'Lỗi thẩm định', 'error');
    }
  } catch (err) {
    showToast('Lỗi kết nối máy chủ', 'error');
  }
}

function openAppealModal(id) {
  document.getElementById('appeal-violation-id').value = id;
  document.getElementById('modal-appeal-violation').classList.remove('hidden');
}

function closeAppealModal() {
  document.getElementById('modal-appeal-violation').classList.add('hidden');
}

async function handleAppealSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('appeal-violation-id').value;
  const reason = document.getElementById('appeal-reason-input').value;

  try {
    const res = await fetch(`/api/conduct/violations/${id}/appeal/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({ reason })
    });
    const data = await res.json();

    if (res.ok) {
      showToast(data.message, 'success');
      closeAppealModal();
      loadConductViolations();
    } else {
      showToast(data.error || 'Lỗi gửi khiếu nại', 'error');
    }
  } catch (err) {
    showToast('Lỗi kết nối máy chủ', 'error');
  }
}

// ==========================================
// 3. COMPETITION MODULE
// ==========================================
let selectedCompetitionGrade = '';

function filterCompetitionGrade(grade) {
  selectedCompetitionGrade = grade;
  document.querySelectorAll('.comp-grade-tab').forEach(btn => {
    btn.classList.remove('bg-brand-900', 'text-white');
    btn.classList.add('text-slate-600');
  });
  event.target.classList.add('bg-brand-900', 'text-white');
  event.target.classList.remove('text-slate-600');
  loadCompetitionScores();
}

async function loadCompetitionScores() {
  const tbody = document.getElementById('competition-scores-tbody');
  try {
    tbody.innerHTML = '<tr><td colspan="11" class="text-center py-8 text-slate-400">Đang cập nhật bảng điểm...</td></tr>';
    
    let url = `/api/competition/periods/1/scores/`;
    if (selectedCompetitionGrade) url += `?grade=${selectedCompetitionGrade}`;

    const res = await fetch(url);
    const data = await res.json();
    currentPeriod = data.period;

    const lockIndicator = document.getElementById('period-lock-indicator');
    const lockBtnText = document.getElementById('btn-lock-period-text');
    if (currentPeriod.is_locked) {
      lockIndicator.className = 'badge bg-rose-100 text-rose-800 border border-rose-200';
      lockIndicator.textContent = 'Đã chốt sổ';
      lockBtnText.textContent = 'Mở lại kỳ';
    } else {
      lockIndicator.className = 'badge bg-emerald-100 text-emerald-800 border border-emerald-200';
      lockIndicator.textContent = 'Đang mở';
      lockBtnText.textContent = 'Chốt kết quả';
    }

    const scores = data.scores || [];
    if (scores.length === 0) {
      tbody.innerHTML = '<tr><td colspan="11" class="text-center py-8 text-slate-400">Không có dữ liệu lớp trong khối này.</td></tr>';
      return;
    }

    tbody.innerHTML = scores.map(s => {
      let trendDisplay = '<span class="text-slate-400 font-mono">0</span>';
      if (s.rank_change > 0) trendDisplay = `<span class="text-emerald-600 font-bold font-mono">+${s.rank_change} ▲</span>`;
      else if (s.rank_change < 0) trendDisplay = `<span class="text-rose-600 font-bold font-mono">${s.rank_change} ▼</span>`;

      let rankColor = 'text-slate-700 font-bold';
      if (s.rank === 1) rankColor = 'text-amber-500 font-extrabold text-sm';
      else if (s.rank === 2) rankColor = 'text-slate-400 font-extrabold text-sm';
      else if (s.rank === 3) rankColor = 'text-amber-700 font-extrabold text-sm';

      return `
        <tr class="hover:bg-slate-50 transition border-b border-slate-100">
          <td class="py-3 px-3 text-center ${rankColor}">#${s.rank}</td>
          <td class="py-3 px-3 font-bold text-slate-900">Chi đoàn ${s.class_name}</td>
          <td class="py-3 px-3 text-slate-500">Khối ${s.grade}</td>
          <td class="py-3 px-3 text-slate-600">${s.homeroom_teacher_name || 'Chưa phân công'}</td>
          <td class="py-3 px-3 text-right font-mono text-slate-600">${parseFloat(s.base_points).toFixed(1)}</td>
          <td class="py-3 px-3 text-right font-mono text-emerald-600 font-semibold">${parseFloat(s.bonus_points) > 0 ? `+${parseFloat(s.bonus_points).toFixed(1)}` : '0.0'}</td>
          <td class="py-3 px-3 text-right font-mono text-rose-600 font-semibold">${parseFloat(s.penalty_points) > 0 ? `-${parseFloat(s.penalty_points).toFixed(1)}` : '0.0'}</td>
          <td class="py-3 px-3 text-right font-mono font-extrabold text-brand-900 text-sm">${parseFloat(s.total_score).toFixed(1)}đ</td>
          <td class="py-3 px-3 text-center font-mono text-slate-700">${s.verified_violations_count}</td>
          <td class="py-3 px-3 text-center">${trendDisplay}</td>
          <td class="py-3 px-3 text-right">
            ${currentUser && (currentUser.role === 'ADMIN' || currentUser.role === 'DOAN_TRUONG') && !currentPeriod.is_locked ? `
              <button onclick="openBonusModal(${s.id}, '${s.class_name}')" class="px-2 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-lg text-[11px] font-semibold transition">+ Cộng điểm</button>
            ` : '<span class="text-slate-300 text-[10px]">--</span>'}
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="11" class="text-center py-8 text-rose-500">Lỗi tải dữ liệu thi đua.</td></tr>';
  }
}

async function recalculateScores() {
  try {
    const res = await fetch('/api/competition/periods/1/recalculate/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      }
    });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message, 'success');
      loadCompetitionScores();
    } else {
      showToast(data.error || 'Lỗi tính điểm', 'error');
    }
  } catch (err) {
    showToast('Lỗi kết nối máy chủ', 'error');
  }
}

async function toggleLockPeriod() {
  if (!currentPeriod) return;
  const action = currentPeriod.is_locked ? 'unlock' : 'lock';
  try {
    const res = await fetch(`/api/competition/periods/${currentPeriod.id}/${action}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      }
    });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message, 'success');
      loadCompetitionScores();
    } else {
      showToast(data.error || 'Lỗi thao tác', 'error');
    }
  } catch (err) {
    showToast('Lỗi kết nối máy chủ', 'error');
  }
}

function openBonusModal(scoreId, className) {
  document.getElementById('bonus-score-id').value = scoreId;
  document.getElementById('bonus-class-name').textContent = className;
  document.getElementById('modal-bonus-points').classList.remove('hidden');
}

function closeBonusModal() {
  document.getElementById('modal-bonus-points').classList.add('hidden');
}

async function handleBonusSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('bonus-score-id').value;
  const bonus = parseFloat(document.getElementById('bonus-points-val').value || 0);
  const note = document.getElementById('bonus-notes-val').value;

  try {
    const res = await fetch(`/api/competition/scores/${id}/add-bonus/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({ bonus_points: bonus, note })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message, 'success');
      closeBonusModal();
      loadCompetitionScores();
    } else {
      showToast(data.error || 'Lỗi cộng điểm', 'error');
    }
  } catch (err) {
    showToast('Lỗi kết nối', 'error');
  }
}

function exportCompetitionExcel() {
  window.open('/api/reports/competition/excel/1/', '_blank');
  showToast('Đang tạo và tải tệp Excel thi đua...', 'info');
}

function exportCompetitionPdf() {
  window.open('/api/reports/competition/pdf/1/', '_blank');
  showToast('Đang tạo và tải tệp PDF thi đua...', 'info');
}

function exportViolationsExcel() {
  window.open('/api/reports/violations/excel/', '_blank');
  showToast('Đang tạo và tải danh sách vi phạm...', 'info');
}

// ==========================================
// 4. ALERTS & GVCN INTERVENTIONS
// ==========================================
async function loadEarlyAlerts() {
  const container = document.getElementById('alerts-cards-container');
  try {
    container.innerHTML = '<div class="text-center py-8 text-slate-400 text-xs">Đang tải cảnh báo...</div>';
    const res = await fetch('/api/alerts/alerts/');
    const data = await res.json();
    const alerts = data.results || data;

    if (alerts.length === 0) {
      container.innerHTML = `
        <div class="text-center py-12 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
          <i data-lucide="check-circle-2" class="w-10 h-10 text-emerald-500 mx-auto mb-2"></i>
          <h4 class="font-bold text-slate-800 text-sm">Không có cảnh báo vi phạm nền nếp nào đang mở</h4>
          <p class="text-xs text-slate-400 mt-1">Nền nếp các lớp hiện tại được duy trì tốt và không có học sinh vượt ngưỡng vi phạm lặp lại.</p>
        </div>
      `;
      lucide.createIcons();
      return;
    }

    container.innerHTML = alerts.map(a => {
      const isResolved = a.status === 'RESOLVED';
      const severityMap = {
        LOW: 'bg-blue-100 text-brand-800',
        MEDIUM: 'bg-amber-100 text-amber-800',
        HIGH: 'bg-purple-100 text-purple-800',
        URGENT: 'bg-rose-100 text-rose-800'
      };

      return `
        <div class="p-5 rounded-2xl border ${isResolved ? 'bg-slate-50/60 border-slate-200 opacity-80' : 'bg-white border-purple-200 shadow-sm'} transition">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
            <div class="flex items-center space-x-2">
              <span class="badge ${severityMap[a.severity] || 'bg-slate-100 text-slate-700'}">${a.severity_display}</span>
              <span class="badge ${isResolved ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">${a.status_display}</span>
              <span class="text-xs text-slate-400">• Lớp ${a.class_name}</span>
            </div>
            <span class="text-[11px] text-slate-400 font-mono">${new Date(a.created_at).toLocaleString('vi-VN')}</span>
          </div>

          <h3 class="font-bold text-sm text-slate-900 mb-2">${a.alert_title}</h3>
          
          <div class="p-3 bg-slate-50 rounded-xl text-xs text-slate-700 mb-3 whitespace-pre-line border border-slate-100 font-mono">
${a.details}
          </div>

          ${a.interventions && a.interventions.length > 0 ? `
            <div class="space-y-2 mb-3">
              <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Nhật ký hỗ trợ đã ghi nhận:</div>
              ${a.interventions.map(i => `
                <div class="p-2.5 bg-emerald-50/60 rounded-lg border border-emerald-100 text-xs">
                  <div class="font-semibold text-emerald-900">Biện pháp: ${i.action_taken}</div>
                  ${i.outcome ? `<div class="text-emerald-700 text-[11px] mt-0.5">Kết quả: ${i.outcome}</div>` : ''}
                  <div class="text-[10px] text-slate-400 mt-1">Bởi: ${i.teacher_name} lúc ${new Date(i.created_at).toLocaleString('vi-VN')}</div>
                </div>
              `).join('')}
            </div>
          ` : ''}

          <div class="flex items-center justify-between pt-2 border-t border-slate-100">
            <span class="text-xs text-slate-400 italic">Dữ liệu nguồn được trích xuất từ các vi phạm đã xác minh</span>
            ${!isResolved && currentUser && (currentUser.role === 'GVCN' || currentUser.role === 'ADMIN') ? `
              <button onclick="openInterventionModal(${a.id}, '${a.alert_title}', '${a.details.replace(/\n/g, ' ')}')" class="px-3.5 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-semibold shadow-sm transition">
                Ghi nhận can thiệp & Hỗ trợ
              </button>
            ` : ''}
          </div>
        </div>
      `;
    }).join('');
    lucide.createIcons();
  } catch (err) {
    container.innerHTML = '<div class="text-center py-8 text-rose-500 text-xs">Lỗi tải cảnh báo.</div>';
  }
}

function openInterventionModal(id, title, details) {
  document.getElementById('intervention-alert-id').value = id;
  document.getElementById('intervention-alert-title').textContent = title;
  document.getElementById('intervention-alert-details').textContent = details;
  document.getElementById('modal-gvcn-intervention').classList.remove('hidden');
}

function closeInterventionModal() {
  document.getElementById('modal-gvcn-intervention').classList.add('hidden');
}

async function handleInterventionSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('intervention-alert-id').value;
  const action_taken = document.getElementById('intervention-action-input').value;
  const outcome = document.getElementById('intervention-outcome-input').value;
  const status = document.getElementById('intervention-status-select').value;

  try {
    const res = await fetch(`/api/alerts/alerts/${id}/intervene/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({ action_taken, outcome, status })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message, 'success');
      closeInterventionModal();
      loadEarlyAlerts();
    } else {
      showToast(data.error || 'Lỗi lưu can thiệp', 'error');
    }
  } catch (err) {
    showToast('Lỗi kết nối máy chủ', 'error');
  }
}

// ==========================================
// 5. COUNSELING MODULE ("GÓC SẺ CHIA")
// ==========================================
function toggleAnonymityField(checked) {
  const wrapper = document.getElementById('alias-field-wrapper');
  if (checked) wrapper.classList.remove('hidden');
  else wrapper.classList.add('hidden');
}

async function handleCounselingSubmit(e) {
  e.preventDefault();
  const form = document.getElementById('counseling-submit-form');
  const payload = {
    topic: document.getElementById('counseling-topic').value,
    content: document.getElementById('counseling-content').value,
    preferred_channel: document.getElementById('counseling-channel').value,
    contact_info: document.getElementById('counseling-contact').value,
    preferred_schedule: document.getElementById('counseling-schedule').value,
    is_anonymous: document.getElementById('counseling-is-anonymous').checked,
    alias_name: document.getElementById('counseling-alias').value
  };

  try {
    const res = await fetch('/api/counseling/submit/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (res.ok) {
      form.reset();
      showToast('Đã gửi đề nghị hỗ trợ tâm lý thành công!', 'success');
      
      alert(`ĐỀ NGHỊ CỦA BẠN ĐÃ ĐƯỢC TIẾP NHẬN BẢO MẬT!\n\nMã tra cứu bí mật của bạn là: ${data.tracking_code}\n\nHãy lưu lại mã này để tra cứu lịch hẹn hoặc phản hồi từ chuyên viên tư vấn mà không cần tiết lộ danh tính.\n\n${data.emergency_guidance ? `\nLƯU Ý AN TOÀN:\n${data.emergency_guidance}` : ''}`);
      
      document.getElementById('track-code-input').value = data.tracking_code;
      checkCounselingTracking();
    } else {
      showToast(data.error || 'Lỗi gửi đề nghị', 'error');
    }
  } catch (err) {
    showToast('Lỗi kết nối máy chủ', 'error');
  }
}

async function checkCounselingTracking() {
  const code = document.getElementById('track-code-input').value.trim();
  const box = document.getElementById('track-result-box');
  if (!code) {
    showToast('Vui lòng nhập mã hồ sơ bảo mật', 'warning');
    return;
  }

  try {
    const res = await fetch(`/api/counseling/track/${code}/`);
    const data = await res.json();

    if (res.ok) {
      box.classList.remove('hidden');
      box.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="font-bold text-slate-800">Mã: ${data.tracking_code}</span>
          <span class="badge bg-blue-100 text-brand-800">${data.status_display}</span>
        </div>
        <div>Chủ đề: <b>${data.topic_display}</b></div>
        <div>Người tiếp nhận: <span class="text-slate-600">${data.counselor_name}</span></div>
        ${data.scheduled_meeting ? `
          <div class="p-2 bg-emerald-50 text-emerald-800 rounded-lg font-semibold mt-1">
            Lịch hẹn trao đổi: ${new Date(data.scheduled_meeting).toLocaleString('vi-VN')}
          </div>
        ` : '<div class="text-[11px] text-slate-400">Chuyên viên đang sắp xếp lịch hẹn phù hợp...</div>'}
      `;
    } else {
      box.classList.remove('hidden');
      box.innerHTML = `<span class="text-rose-600 font-medium">${data.error || 'Không tìm thấy hồ sơ'}</span>`;
    }
  } catch (err) {
    showToast('Lỗi tra cứu', 'error');
  }
}

async function loadCounselorInbox() {
  const list = document.getElementById('counselor-requests-list');
  const desc = document.getElementById('counselor-status-desc');

  try {
    const res = await fetch('/api/counseling/requests/');
    if (res.status === 403) {
      desc.textContent = 'Quyền riêng tư được bảo vệ: Bạn không thuộc bộ phận tư vấn tâm lý nên nội dung này bị ẩn an toàn.';
      list.innerHTML = `
        <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl text-center text-xs text-slate-500">
          <i data-lucide="lock" class="w-6 h-6 text-slate-400 mx-auto mb-1"></i>
          <div>Dữ liệu tư vấn tâm lý được cách ly độc lập.</div>
          <div class="text-[10px] text-slate-400 mt-1">Chỉ tài khoản được Admin cấp quyền tư vấn mới có thể xem nội dung này.</div>
        </div>
      `;
      lucide.createIcons();
      return;
    }

    const data = await res.json();
    const items = data.results || data;

    desc.textContent = `Hiện có ${items.length} hồ sơ tư vấn cần đồng hành và hỗ trợ.`;

    if (items.length === 0) {
      list.innerHTML = '<div class="text-center py-6 text-xs text-slate-400">Chưa có đề nghị tư vấn nào.</div>';
      return;
    }

    list.innerHTML = items.map(req => `
      <div class="p-3 rounded-xl border ${req.is_urgent_safety ? 'bg-rose-50 border-rose-300' : 'bg-slate-50 border-slate-200'} text-xs space-y-1.5">
        <div class="flex items-center justify-between">
          <span class="font-mono font-bold text-slate-800">${req.tracking_code}</span>
          <span class="badge ${req.is_urgent_safety ? 'bg-rose-600 text-white' : 'bg-slate-200 text-slate-800'}">${req.status_display}</span>
        </div>
        <div class="font-semibold text-slate-900">${req.alias_name ? `Bí danh: ${req.alias_name}` : req.student_name}</div>
        <div class="text-slate-500">Chủ đề: <b>${req.topic_display}</b></div>
        <div class="text-slate-700 bg-white p-2 rounded-lg border border-slate-200/60 leading-relaxed font-sans">${req.content}</div>
        ${req.contact_info ? `<div class="text-[11px] text-slate-500">Liên hệ: ${req.contact_info}</div>` : ''}
        ${req.preferred_schedule ? `<div class="text-[11px] text-slate-500">Khung giờ: ${req.preferred_schedule}</div>` : ''}
        
        <div class="pt-2 flex items-center justify-between">
          <span class="text-[10px] text-slate-400">${new Date(req.created_at).toLocaleString('vi-VN')}</span>
          <button onclick="promptCounselorAction(${req.id})" class="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-[11px] font-semibold transition">Xử lý hồ sơ</button>
        </div>
      </div>
    `).join('');
    lucide.createIcons();
  } catch (err) {
    console.error(err);
  }
}

async function promptCounselorAction(reqId) {
  const newStatus = prompt("Chọn trạng thái cập nhật (RECEIVED, IN_PROGRESS, SCHEDULED, COMPLETED):", "SCHEDULED");
  if (!newStatus) return;

  let scheduled = null;
  if (newStatus === "SCHEDULED") {
    scheduled = prompt("Nhập thời gian hẹn trao đổi (YYYY-MM-DD HH:MM):", "2026-10-16 10:00");
  }

  try {
    const res = await fetch(`/api/counseling/requests/${reqId}/update-status/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({ status: newStatus, scheduled_meeting: scheduled })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message, 'success');
      loadCounselorInbox();
    } else {
      showToast(data.error || 'Lỗi cập nhật', 'error');
    }
  } catch (err) {
    showToast('Lỗi kết nối', 'error');
  }
}

// ==========================================
// 6. ADMIN USER MANAGEMENT & ROLE APPROVAL
// ==========================================
async function loadUsersManagement() {
  const tbody = document.getElementById('user-management-tbody');
  if (!currentUser || currentUser.role !== 'ADMIN') {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-rose-500">Chỉ có Quản trị viên hệ thống (Admin) mới có quyền truy cập.</td></tr>';
    return;
  }

  try {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-slate-400">Đang tải danh sách tài khoản...</td></tr>';
    const res = await fetch('/api/core/users/');
    if (res.status === 403) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-rose-500">Bị từ chối: Chỉ có Admin mới được duyệt chức vụ của quyền.</td></tr>';
      return;
    }

    const data = await res.json();
    allUsersCache = data.results || data;
    renderUsersTable(allUsersCache);
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-rose-500">Lỗi tải dữ liệu người dùng.</td></tr>';
  }
}

function renderUsersTable(users) {
  const tbody = document.getElementById('user-management-tbody');
  if (users.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-slate-400">Không tìm thấy người dùng nào.</td></tr>';
    return;
  }

  const roleColors = {
    ADMIN: 'bg-purple-100 text-purple-800 border-purple-200',
    BGH: 'bg-blue-100 text-brand-800 border-blue-200',
    DOAN_TRUONG: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    SAO_DO: 'bg-amber-100 text-amber-800 border-amber-200',
    GVCN: 'bg-sky-100 text-sky-800 border-sky-200',
    GVBM: 'bg-slate-100 text-slate-700 border-slate-200',
    HOC_SINH: 'bg-slate-100 text-slate-800 border-slate-200',
    CHUYEN_VIEN_TAM_LY: 'bg-rose-100 text-rose-800 border-rose-200',
  };

  tbody.innerHTML = users.map(u => `
    <tr class="hover:bg-slate-50 transition border-b border-slate-100">
      <td class="py-3 px-3">
        <div class="font-bold text-slate-900">${u.full_name || u.username}</div>
        <div class="text-[10px] text-slate-400">${u.email || 'Chưa cập nhật email'}</div>
      </td>
      <td class="py-3 px-3 font-mono font-medium text-slate-700">${u.username}</td>
      <td class="py-3 px-3">
        <span class="badge border ${roleColors[u.role] || 'bg-slate-100 text-slate-700'}">${u.role_display}</span>
      </td>
      <td class="py-3 px-3 text-center">
        ${u.can_verify_violations ? '<span class="badge bg-emerald-50 text-emerald-700 border border-emerald-200">Có quyền</span>' : '<span class="text-slate-300 text-[10px]">--</span>'}
      </td>
      <td class="py-3 px-3 text-center">
        ${u.can_view_counseling ? '<span class="badge bg-rose-50 text-rose-700 border border-rose-200">Được cấp</span>' : '<span class="text-slate-300 text-[10px]">--</span>'}
      </td>
      <td class="py-3 px-3 text-center">
        ${u.is_active ? '<span class="badge bg-emerald-100 text-emerald-800">Hoạt động</span>' : '<span class="badge bg-rose-100 text-rose-800">Đã khóa</span>'}
      </td>
      <td class="py-3 px-3 text-right">
        <button onclick="openApproveRoleModal(${u.id})" class="px-2.5 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-[11px] font-semibold transition shadow-sm">
          Duyệt chức vụ & Quyền
        </button>
      </td>
    </tr>
  `).join('');
  lucide.createIcons();
}

function filterUsersList(keyword) {
  const q = keyword.toLowerCase().trim();
  if (!q) {
    renderUsersTable(allUsersCache);
    return;
  }
  const filtered = allUsersCache.filter(u => 
    (u.full_name && u.full_name.toLowerCase().includes(q)) ||
    (u.username && u.username.toLowerCase().includes(q)) ||
    (u.role_display && u.role_display.toLowerCase().includes(q))
  );
  renderUsersTable(filtered);
}

function openApproveRoleModal(userId) {
  const u = allUsersCache.find(x => x.id === userId);
  if (!u) return;

  document.getElementById('approve-user-id').value = u.id;
  document.getElementById('approve-modal-fullname').textContent = u.full_name || u.username;
  document.getElementById('approve-modal-username').textContent = u.username;
  document.getElementById('approve-modal-current-role').textContent = u.role_display;

  document.getElementById('approve-role-select').value = u.role;
  document.getElementById('approve-can-verify').checked = Boolean(u.can_verify_violations);
  document.getElementById('approve-can-counseling').checked = Boolean(u.can_view_counseling);
  document.getElementById('approve-is-active').checked = Boolean(u.is_active);

  document.getElementById('modal-approve-role').classList.remove('hidden');
}

function closeApproveRoleModal() {
  document.getElementById('modal-approve-role').classList.add('hidden');
}

async function handleApproveRoleSubmit(e) {
  e.preventDefault();
  const userId = document.getElementById('approve-user-id').value;
  const newRole = document.getElementById('approve-role-select').value;
  const canVerify = document.getElementById('approve-can-verify').checked;
  const canCounseling = document.getElementById('approve-can-counseling').checked;
  const isActive = document.getElementById('approve-is-active').checked;

  try {
    const res = await fetch(`/api/core/users/${userId}/approve-role/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({
        role: newRole,
        can_verify_violations: canVerify,
        can_view_counseling: canCounseling,
        is_active: isActive
      })
    });
    const data = await res.json();

    if (res.ok) {
      showToast(data.message, 'success');
      closeApproveRoleModal();
      loadUsersManagement();
    } else {
      showToast(data.error || 'Lỗi phê duyệt chức vụ', 'error');
    }
  } catch (err) {
    showToast('Lỗi kết nối máy chủ', 'error');
  }
}

// ==========================================
// 7. REPORTS & AUDIT LOGS
// ==========================================
async function loadReportsHistory() {
  const tbody = document.getElementById('reports-history-tbody');
  try {
    const res = await fetch('/api/reports/history/');
    const data = await res.json();
    const items = data.results || data;

    if (items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-slate-400">Chưa có lượt xuất báo cáo nào.</td></tr>';
      return;
    }

    tbody.innerHTML = items.map(h => `
      <tr class="hover:bg-slate-50 transition border-b border-slate-100">
        <td class="py-2.5 px-3 font-semibold text-slate-800">${h.title}</td>
        <td class="py-2.5 px-3 text-slate-600">${h.report_type}</td>
        <td class="py-2.5 px-3"><span class="badge ${h.file_format === 'PDF' ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'}">${h.file_format}</span></td>
        <td class="py-2.5 px-3 text-slate-600">${h.exported_by}</td>
        <td class="py-2.5 px-3 text-slate-400 font-mono">${h.created_at}</td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-rose-500">Lỗi tải lịch sử.</td></tr>';
  }
}

async function loadAuditLogs() {
  const tbody = document.getElementById('settings-audit-tbody');
  try {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center py-6 text-slate-400">Đang tải nhật ký...</td></tr>';
    const res = await fetch('/api/core/audit-logs/');
    const data = await res.json();
    const items = data.results || data;

    if (items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center py-6 text-slate-400">Chưa có nhật ký hoạt động.</td></tr>';
      return;
    }

    tbody.innerHTML = items.map(l => `
      <tr class="hover:bg-slate-50 transition border-b border-slate-100">
        <td class="py-2.5 px-3 text-slate-400 font-mono text-[11px]">${new Date(l.created_at).toLocaleString('vi-VN')}</td>
        <td class="py-2.5 px-3 font-semibold text-slate-800">${l.user_full_name || l.username}</td>
        <td class="py-2.5 px-3"><span class="badge bg-blue-50 text-brand-700 border border-blue-200">${l.action}</span></td>
        <td class="py-2.5 px-3 text-slate-600 font-medium">${l.resource_type}</td>
        <td class="py-2.5 px-3 font-mono text-slate-500">${l.resource_id || '--'}</td>
        <td class="py-2.5 px-3 text-slate-700">${l.details}</td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center py-6 text-rose-500">Lỗi tải nhật ký thao tác.</td></tr>';
  }
}

async function triggerSeedMockData() {
  if (!confirm('Nạp lại dữ liệu thử nghiệm chuẩn cho Trường THPT Hương Khê?')) return;
  try {
    showToast('Vui lòng chạy lệnh: python manage.py seed_hk_data trên terminal để bảo đảm tính toàn vẹn', 'info');
  } catch (err) {
    showToast('Lỗi kết nối', 'error');
  }
}

function confirmResetMockData() {
  alert('Để bảo đảm an toàn hệ thống, lệnh xóa sạch toàn bộ dữ liệu mẫu có thể được kích hoạt từ dòng lệnh: python manage.py seed_hk_data --clean');
}

function toggleMobileMenu() {
  const sidebar = document.querySelector('aside');
  if (sidebar.classList.contains('hidden')) {
    sidebar.classList.remove('hidden');
    sidebar.classList.add('fixed', 'inset-0', 'z-50', 'bg-slate-900/60', 'p-4');
  } else {
    sidebar.classList.add('hidden');
    sidebar.classList.remove('fixed', 'inset-0', 'z-50', 'bg-slate-900/60', 'p-4');
  }
}
