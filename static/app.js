/**

 * HK Student Hub – Frontend Application Logic

 * Trường THPT Hương Khê – Hà Tĩnh

 * Bảo mật RBAC & Xác thực đăng nhập nghiêm ngặt

 */



// Global State



// ==============================================================================

// SẮP XẾP LỚP HỌC TỰ NHIÊN HỆ THỐNG: A1 -> A2 -> ... -> A22 (TỪ NHỎ ĐẾN LỚN)

// ==============================================================================

function parseClassSortKey(val) {

  const str = (typeof val === 'string' ? val : (val?.name || val?.class_name || val?.school_class_name || '')).trim().toUpperCase();

  const m = str.match(/^(\d+)?([A-ZĐ_]+)?(\d+)?$/);

  if (m) {

    return {

      grade: m[1] ? parseInt(m[1], 10) : 0,

      prefix: m[2] || '',

      num: m[3] ? parseInt(m[3], 10) : 0

    };

  }

  return { grade: 0, prefix: str, num: 0 };

}



function naturalClassSort(a, b) {

  const kA = parseClassSortKey(a);

  const kB = parseClassSortKey(b);

  if (kA.grade !== kB.grade) return kA.grade - kB.grade;

  if (kA.prefix !== kB.prefix) return kA.prefix.localeCompare(kB.prefix, 'vi');

  if (kA.num !== kB.num) return kA.num - kB.num;

  const nameA = typeof a === 'string' ? a : (a?.name || a?.class_name || '');

  const nameB = typeof b === 'string' ? b : (b?.name || b?.class_name || '');

  return nameA.localeCompare(nameB, 'vi');

}

window.naturalClassSort = naturalClassSort;



let currentUser = null;

let currentPeriod = null;

let classesCache = [];

let rulesCache = [];

let allUsersCache = [];

let activeTab = 'dashboard';

let trendChartInstance = null;

let activeViolationSubmissionKey = null;

let lastViolationFingerprint = '';

let profileAvatarPreviewUrl = null;



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

  toast.textContent = message;

  container.appendChild(toast);



  setTimeout(() => {

    toast.classList.remove('translate-y-2', 'opacity-0');

  }, 10);



  setTimeout(() => {

    toast.classList.add('opacity-0', 'translate-y-2');

    setTimeout(() => toast.remove(), 300);

  }, 4000);

}

// ==============================================================================
// GLOBAL MODAL HELPERS (ROBUST OPEN / CLOSE)
// ==============================================================================
function openModal(modalId) {
  const modal = typeof modalId === 'string' ? document.getElementById(modalId) : modalId;
  if (!modal) return;
  modal.classList.remove('hidden');
  document.body.classList.add('overflow-hidden');
  if (window.lucide) {
    try { lucide.createIcons(); } catch(e) {}
  }
}

function closeModal(modalId) {
  const modal = typeof modalId === 'string' ? document.getElementById(modalId) : modalId;
  if (!modal) return;
  modal.classList.add('hidden');
  const anyOpenModal = document.querySelector('.fixed.inset-0:not(.hidden)');
  if (!anyOpenModal) {
    document.body.classList.remove('overflow-hidden');
  }
}

window.openModal = openModal;
window.closeModal = closeModal;



function escapeHtml(value) {

  return String(value ?? '').replace(/[&<>"']/g, char => ({

    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'

  }[char]));

}



// ==========================================

// REAL-TIME SYSTEM TIME & SYNCHRONIZATION

// ==========================================

let serverTimeOffsetMs = 0;



function getLocalIsoString(date = new Date()) {

  const pad = (n) => String(n).padStart(2, '0');

  const year = date.getFullYear();

  const month = pad(date.getMonth() + 1);

  const day = pad(date.getDate());

  const hours = pad(date.getHours());

  const minutes = pad(date.getMinutes());

  return `${year}-${month}-${day}T${hours}:${minutes}`;

}



function setRealTimeForViolation() {

  const input = document.getElementById('modal-violation-time');

  if (input) {

    const now = new Date(Date.now() + serverTimeOffsetMs);

    input.value = getLocalIsoString(now);

    showToast('Đã đồng bộ thời gian thực hiện tại.', 'info');

  }

}



async function syncServerTime() {

  try {

    const start = Date.now();

    const res = await fetch('/api/core/system/time/');

    if (res.ok) {

      const data = await res.json();

      const latency = (Date.now() - start) / 2;

      const serverMs = data.timestamp_ms + latency;

      serverTimeOffsetMs = serverMs - Date.now();

      updateClockDisplay();

    }

  } catch (err) {

    console.warn('Không thể đồng bộ thời gian máy chủ:', err);

  }

}



function updateClockDisplay() {

  const clockTime = document.getElementById('live-clock-time');

  const clockDate = document.getElementById('live-clock-date');

  const currentDateTime = document.getElementById('current-datetime');

  if (!clockTime && !clockDate && !currentDateTime) return;



  const now = new Date(Date.now() + serverTimeOffsetMs);

  const pad = (n) => String(n).padStart(2, '0');

  const hours = pad(now.getHours());

  const minutes = pad(now.getMinutes());

  const seconds = pad(now.getSeconds());



  if (clockTime) clockTime.textContent = `${hours}:${minutes}:${seconds}`;



  if (clockDate) {

    const days = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];

    const dayStr = days[now.getDay()];

    clockDate.textContent = `${dayStr}, ${pad(now.getDate())}/${pad(now.getMonth() + 1)}/${now.getFullYear()}`;

  }



  if (currentDateTime) {

    const fullDays = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];

    const fullDayStr = fullDays[now.getDay()];

    currentDateTime.textContent = `${fullDayStr}, ${pad(now.getDate())}/${pad(now.getMonth() + 1)}/${now.getFullYear()} - ${hours}:${minutes}:${seconds}`;

  }

}



function initRealTimeClock() {

  updateClockDisplay();

  setInterval(updateClockDisplay, 1000);

  syncServerTime();

  setInterval(syncServerTime, 5 * 60 * 1000);

}



// App Initialization

document.addEventListener('DOMContentLoaded', async () => {

  if (!document.querySelector('.app-shell')) return;

  initRealTimeClock();

  const currentPath = window.location.pathname;

  await checkAuthStatus();

  if (!currentUser) {

    redirectToLoginForCurrentRoute();

    return;

  }

  if (currentPath.startsWith('/admin/users')) {
    navigateTab('users', false);
  } else if (currentPath.startsWith('/profile')) {
    navigateTab('profile', false);
  } else if (currentPath.startsWith('/teacher-classes')) {
    navigateTab('teacher-classes', false);
  } else if (currentPath.startsWith('/competition')) {
    navigateTab('competition', false);
  } else if (currentPath.startsWith('/conduct')) {
    navigateTab('conduct', false);
  } else if (currentPath.startsWith('/counseling')) {
    navigateTab('counseling', false);
  } else {
    navigateTab('dashboard', false);
  }

  lucide.createIcons();



  // Polling thông minh có kiểm tra tab hiển thị (Page Visibility API) để tiết kiệm tài nguyên

  let notifPollingTimer = null;

  function startSmartNotificationPolling() {

    if (notifPollingTimer) clearInterval(notifPollingTimer);

    notifPollingTimer = setInterval(() => {

      // Chỉ gửi request khi tab đang mở và người dùng đang hoạt động

      if (currentUser && !document.hidden) {

        verifyCurrentSession();

        loadNotifications();

      }

    }, 45000); // 45s interval

  }

  startSmartNotificationPolling();



  document.addEventListener('visibilitychange', () => {

    if (!document.hidden && currentUser) {

      loadNotifications();

    }

  });

});



window.addEventListener('popstate', () => {

  if (!document.querySelector('.app-shell')) return;

  const path = window.location.pathname;

  if (!currentUser) {

    redirectToLoginForCurrentRoute();

    return;

  }

  navigateTab(path.startsWith('/admin/users') ? 'users' : (path.startsWith('/profile') ? 'profile' : 'dashboard'), false);

});



window.addEventListener('pageshow', event => {

  if (event.persisted && document.querySelector('.app-shell')) window.location.reload();

});



function redirectToLoginForCurrentRoute() {

  const next = `${window.location.pathname}${window.location.search}`;

  const query = new URLSearchParams({ next });

  window.location.replace(`/login?${query.toString()}`);

}



// ==========================================

// AUTHENTICATION & LOGIN WORKFLOW

// ==========================================



async function checkAuthStatus() {

  try {

    const res = await fetch('/api/core/auth/me/', { credentials: 'same-origin', cache: 'no-store' });

    const data = await res.json();

    

    if (data.authenticated && data.user) {

      await activateAuthenticatedUser(data.user);

    } else {

      currentUser = null;

    }

  } catch (err) {

    console.error('Lỗi kiểm tra xác thực:', err);

    currentUser = null;

  }

}



async function verifyCurrentSession() {

  if (!currentUser || document.hidden) return;

  try {

    const response = await fetch('/api/core/auth/me/', {

      credentials: 'same-origin',

      cache: 'no-store',

      headers: { 'X-Requested-With': 'XMLHttpRequest' },

    });

    const data = await response.json().catch(() => ({}));

    if ((response.ok && (!data.authenticated || !data.user)) || [401, 403].includes(response.status)) {

      currentUser = null;

      redirectToLoginForCurrentRoute();

      return;

    }

    if (!response.ok || !data.user) return;

    const oldAccess = JSON.stringify({

      role: currentUser.role,

      permissions: currentUser.permissions || [],

      is_admin: currentUser.is_admin,

      is_super_admin: currentUser.is_super_admin,

      is_superuser: currentUser.is_superuser,

      is_doan_truong: currentUser.is_doan_truong,

      is_active_red_star: currentUser.is_active_red_star,

      is_gvcn: currentUser.is_gvcn,

      is_gvbm: currentUser.is_gvbm,

      is_student: currentUser.is_student,

    });

    currentUser = data.user;

    const newAccess = JSON.stringify({

      role: currentUser.role,

      permissions: currentUser.permissions || [],

      is_admin: currentUser.is_admin,

      is_super_admin: currentUser.is_super_admin,

      is_superuser: currentUser.is_superuser,

      is_doan_truong: currentUser.is_doan_truong,

      is_active_red_star: currentUser.is_active_red_star,

      is_gvcn: currentUser.is_gvcn,

      is_gvbm: currentUser.is_gvbm,

      is_student: currentUser.is_student,

    });

    if (oldAccess !== newAccess) {

      updateUserUI();

      if (!getAllowedTabs().has(activeTab)) navigateTab('dashboard', false);

    }

  } catch {

    // A temporary network failure should not end a valid session.

  }

}



async function activateAuthenticatedUser(user) {

  currentUser = user;

  hideLoginScreen();

  showAuthenticatedApp();

  updateUserUI();

  renderProfile();

  await loadNotifications();



  if (user.must_change_password) {

    openPasswordChange();

    return false;

  }



  document.getElementById('password-change-overlay').classList.add('hidden');

  const needsClassMetadata = isAdminUser() || user.is_bgh || user.is_gvcn || user.is_active_red_star ||

    (user.is_doan_truong && userHasPermission('red_star.assign'));

  if (needsClassMetadata) await loadMetadata();

  return true;

}



function showLoginScreen() {

  window.location.assign('/login');

}



function hideLoginScreen() {

  document.getElementById('auth-page')?.classList.add('hidden');

  document.getElementById('public-home')?.classList.add('hidden');

  document.getElementById('privacy-policy-page')?.classList.add('hidden');

  document.getElementById('terms-of-service-page')?.classList.add('hidden');

  cleanupLegalInteractions();

}



function showAuthenticatedApp() {

  document.getElementById('public-home')?.classList.add('hidden');

  document.getElementById('auth-page')?.classList.add('hidden');

  document.getElementById('privacy-policy-page')?.classList.add('hidden');

  document.getElementById('terms-of-service-page')?.classList.add('hidden');

  cleanupLegalInteractions();

  document.getElementById('authenticated-header')?.classList.remove('hidden');

  document.getElementById('authenticated-main')?.classList.remove('hidden');

  document.getElementById('authenticated-mobile-nav')?.classList.remove('hidden');

}



function showPublicRoute(path = window.location.pathname) {

  const normalizedPath = path.replace(/\/$/, '') || '/';

  const isPrivacy = normalizedPath === '/privacy-policy';

  const isTerms = normalizedPath === '/terms-of-service';

  const isLegal = isPrivacy || isTerms;

  const isHome = normalizedPath === '/' && !currentUser;

  const isAuthRoute = ['/login', '/register', '/registration-pending', '/forgot-password', '/reset-password'].includes(normalizedPath);



  document.getElementById('public-home')?.classList.toggle('hidden', !isHome);

  document.getElementById('auth-page')?.classList.toggle('hidden', !isAuthRoute);

  document.getElementById('privacy-policy-page')?.classList.toggle('hidden', !isPrivacy);

  document.getElementById('terms-of-service-page')?.classList.toggle('hidden', !isTerms);



  if (isLegal || !currentUser) {

    document.getElementById('authenticated-header')?.classList.add('hidden');

    document.getElementById('authenticated-main')?.classList.add('hidden');

    document.getElementById('authenticated-mobile-nav')?.classList.add('hidden');

  }



  document.getElementById('login-box')?.classList.toggle('hidden', normalizedPath !== '/login');

  document.getElementById('register-box')?.classList.toggle('hidden', normalizedPath !== '/register');

  document.getElementById('forgot-password-box')?.classList.toggle('hidden', normalizedPath !== '/forgot-password');

  document.getElementById('reset-password-box')?.classList.toggle('hidden', normalizedPath !== '/reset-password');

  const pendingBox = document.getElementById('registration-pending-box');

  pendingBox?.classList.toggle('hidden', normalizedPath !== '/registration-pending');

  if (normalizedPath === '/registration-pending') {

    renderPendingConfirmation(history.state?.registration || null);

  }

  if (normalizedPath === '/reset-password') {

    setupResetPasswordView();

  }



  if (isPrivacy) {

    initLegalPageInteractions('privacy');

  } else if (isTerms) {

    initLegalPageInteractions('terms');

  } else {

    cleanupLegalInteractions();

  }



  if (window.location.hash) {

    const targetEl = document.querySelector(window.location.hash);

    if (targetEl) {

      setTimeout(() => targetEl.scrollIntoView({ behavior: 'smooth' }), 50);

    } else {

      window.scrollTo(0, 0);

    }

  } else {

    window.scrollTo(0, 0);

  }

  lucide.createIcons();

}



// Global cache & listeners for legal documents

const legalDocOriginalHtml = {};

let activeLegalObserver = null;

let legalScrollHandler = null;



function cleanupLegalInteractions() {

  if (activeLegalObserver) {

    activeLegalObserver.disconnect();

    activeLegalObserver = null;

  }

  if (legalScrollHandler) {

    window.removeEventListener('scroll', legalScrollHandler);

    legalScrollHandler = null;

  }

}



function initLegalPageInteractions(prefix) {

  cleanupLegalInteractions();



  const container = document.getElementById(`${prefix}-sections-container`);

  if (!container) return;



  if (!legalDocOriginalHtml[prefix]) {

    legalDocOriginalHtml[prefix] = container.innerHTML;

  }



  const progressBar = document.getElementById(`${prefix}-reading-progress`);

  const backToTopBtn = document.getElementById(`btn-back-to-top-${prefix}`);



  legalScrollHandler = () => {

    const docEl = document.documentElement;

    const body = document.body;

    const scrollTop = window.scrollY || docEl.scrollTop || body.scrollTop || 0;

    const scrollHeight = (docEl.scrollHeight || body.scrollHeight) - window.innerHeight;

    const progress = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;

    if (progressBar) {

      progressBar.style.width = Math.min(100, Math.max(0, progress)) + '%';

    }

    if (backToTopBtn) {

      backToTopBtn.classList.toggle('hidden', scrollTop < 350);

    }

  };

  window.addEventListener('scroll', legalScrollHandler, { passive: true });

  legalScrollHandler();



  // ScrollSpy with IntersectionObserver

  const sections = container.querySelectorAll(`article[id^="${prefix}-section-"]`);

  const tocLinks = document.querySelectorAll(`#${prefix}-desktop-toc .legal-nav-link`);



  if ('IntersectionObserver' in window && sections.length > 0) {

    activeLegalObserver = new IntersectionObserver((entries) => {

      entries.forEach(entry => {

        if (entry.isIntersecting) {

          const id = entry.target.id;

          tocLinks.forEach(link => {

            const href = link.getAttribute('href');

            if (href === `#${id}`) {

              link.classList.add('active');

            } else {

              link.classList.remove('active');

            }

          });

        }

      });

    }, {

      rootMargin: '-10% 0px -70% 0px',

      threshold: [0, 0.2, 0.5]

    });



    sections.forEach(sec => activeLegalObserver.observe(sec));

  }

}



function searchInLegalDoc(prefix, query) {

  const container = document.getElementById(`${prefix}-sections-container`);

  const badge = document.getElementById(`${prefix}-search-badge`);

  const countEl = document.getElementById(`${prefix}-search-count`);

  const clearBtn = document.getElementById(`${prefix}-search-clear`);

  if (!container) return;



  if (!legalDocOriginalHtml[prefix]) {

    legalDocOriginalHtml[prefix] = container.innerHTML;

  }



  const trimmed = (query || '').trim();

  if (trimmed.length < 2) {

    container.innerHTML = legalDocOriginalHtml[prefix];

    badge?.classList.add('hidden');

    badge?.classList.remove('flex');

    clearBtn?.classList.add('hidden');

    lucide.createIcons();

    return;

  }



  clearBtn?.classList.remove('hidden');



  container.innerHTML = legalDocOriginalHtml[prefix];



  const safeQuery = trimmed.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

  const regex = new RegExp(`(${safeQuery})`, 'gi');



  let matchCount = 0;

  function highlightTextNodes(node) {

    if (node.nodeType === Node.TEXT_NODE) {

      if (node.nodeValue && regex.test(node.nodeValue)) {

        const matches = node.nodeValue.match(regex);

        matchCount += matches ? matches.length : 0;

        const span = document.createElement('span');

        span.innerHTML = escapeHtml(node.nodeValue).replace(regex, '<mark class="legal-mark">$1</mark>');

        node.parentNode.replaceChild(span, node);

      }

    } else if (node.nodeType === Node.ELEMENT_NODE && !['SCRIPT', 'STYLE', 'BUTTON', 'MARK'].includes(node.tagName)) {

      Array.from(node.childNodes).forEach(child => highlightTextNodes(child));

    }

  }



  highlightTextNodes(container);



  if (badge && countEl) {

    countEl.textContent = `${matchCount} kết quả tìm thấy`;

    badge.classList.remove('hidden');

    badge.classList.add('flex');

  }



  if (matchCount > 0) {

    const firstMark = container.querySelector('mark.legal-mark');

    firstMark?.scrollIntoView({ behavior: 'smooth', block: 'center' });

  }



  lucide.createIcons();

}



function clearLegalSearch(prefix) {

  const input = document.getElementById(`${prefix}-search-input`);

  if (input) input.value = '';

  const container = document.getElementById(`${prefix}-sections-container`);

  if (container && legalDocOriginalHtml[prefix]) {

    container.innerHTML = legalDocOriginalHtml[prefix];

  }

  const badge = document.getElementById(`${prefix}-search-badge`);

  badge?.classList.add('hidden');

  badge?.classList.remove('flex');

  const clearBtn = document.getElementById(`${prefix}-search-clear`);

  clearBtn?.classList.add('hidden');

  lucide.createIcons();

}



function copySectionLink(sectionId) {

  const fullUrl = `${window.location.origin}${window.location.pathname}#${sectionId}`;

  if (navigator.clipboard && navigator.clipboard.writeText) {

    navigator.clipboard.writeText(fullUrl).then(() => {

      showToast('Đã sao chép liên kết mục vào bộ nhớ tạm!', 'success');

    }).catch(() => {

      fallbackCopyText(fullUrl);

    });

  } else {

    fallbackCopyText(fullUrl);

  }

}



function fallbackCopyText(text) {

  const textarea = document.createElement('textarea');

  textarea.value = text;

  textarea.style.position = 'fixed';

  textarea.style.opacity = '0';

  document.body.appendChild(textarea);

  textarea.select();

  try {

    document.execCommand('copy');

    showToast('Đã sao chép liên kết mục vào bộ nhớ tạm!', 'success');

  } catch (err) {

    showToast('Không thể sao chép, vui lòng sao chép thủ công.', 'error');

  }

  document.body.removeChild(textarea);

}



function toggleMobileLegalToc(prefix) {

  const content = document.getElementById(`${prefix}-mobile-toc-content`);

  const chevron = document.getElementById(`${prefix}-mobile-toc-chevron`);

  if (content) {

    content.classList.toggle('hidden');

  }

  if (chevron) {

    chevron.classList.toggle('rotate-180');

  }

}



function setupResetPasswordView() {

  const params = new URLSearchParams(window.location.search);

  const uid = params.get('uid');

  const token = params.get('token');

  const alertEl = document.getElementById('reset-password-alert');

  if (alertEl) {

    alertEl.className = 'hidden rounded-xl p-4 text-sm leading-6';

    alertEl.textContent = '';

  }

  if (!uid || !token) {

    document.getElementById('reset-token-invalid')?.classList.remove('hidden');

    document.getElementById('reset-password-form')?.classList.add('hidden');

  } else {

    document.getElementById('reset-token-invalid')?.classList.add('hidden');

    document.getElementById('reset-password-form')?.classList.remove('hidden');

  }

}



async function handleForgotPasswordSubmit(event) {

  event.preventDefault();

  const emailInput = document.getElementById('forgot-email');

  const alertEl = document.getElementById('forgot-password-alert');

  const btn = document.getElementById('btn-forgot-submit');

  const email = emailInput?.value.trim() || '';



  if (!email) {

    emailInput?.focus();

    return;

  }



  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!emailPattern.test(email)) {

    if (alertEl) {

      alertEl.className = 'rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm leading-6 text-rose-800';

      alertEl.textContent = 'Vui lòng nhập địa chỉ email hợp lệ.';

      alertEl.classList.remove('hidden');

    }

    return;

  }



  btn.disabled = true;

  const originalHtml = btn.innerHTML;

  btn.innerHTML = `<span class="inline-block animate-spin mr-2">◌</span><span>Đang xử lý yêu cầu...</span>`;



  try {

    const res = await fetch('/api/core/auth/forgot-password/', {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken') || '',

      },

      body: JSON.stringify({ email }),

    });

    const data = await res.json();

    if (res.ok) {

      alertEl.className = 'rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm leading-6 text-emerald-800';

      alertEl.textContent = data.message || 'Nếu địa chỉ email hợp lệ và đủ điều kiện khôi phục, bạn sẽ nhận được email hướng dẫn đặt lại mật khẩu. Vui lòng kiểm tra hộp thư đến (và thư rác/spam).';

      alertEl.classList.remove('hidden');

      if (emailInput) emailInput.value = '';

    } else {

      alertEl.className = 'rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm leading-6 text-rose-800';

      alertEl.textContent = data.detail || data.error || (data.email ? data.email[0] : 'Không thể xử lý yêu cầu. Vui lòng thử lại sau.');

      alertEl.classList.remove('hidden');

    }

  } catch (err) {

    alertEl.className = 'rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm leading-6 text-rose-800';

    alertEl.textContent = 'Lỗi kết nối máy chủ. Vui lòng kiểm tra mạng và thử lại.';

    alertEl.classList.remove('hidden');

  } finally {

    btn.disabled = false;

    btn.innerHTML = originalHtml;

    lucide.createIcons();

  }

}



async function handleResetPasswordSubmit(event) {

  event.preventDefault();

  const newPassInput = document.getElementById('reset-new-password');

  const confirmPassInput = document.getElementById('reset-confirm-password');

  const alertEl = document.getElementById('reset-password-alert');

  const btn = document.getElementById('btn-reset-submit');



  const newPassword = newPassInput?.value || '';

  const confirmPassword = confirmPassInput?.value || '';



  const params = new URLSearchParams(window.location.search);

  const uid = params.get('uid') || '';

  const token = params.get('token') || '';



  if (!uid || !token) {

    document.getElementById('reset-token-invalid')?.classList.remove('hidden');

    document.getElementById('reset-password-form')?.classList.add('hidden');

    return;

  }



  if (newPassword.length < 8) {

    alertEl.className = 'rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm leading-6 text-rose-800';

    alertEl.textContent = 'Mật khẩu mới phải có độ dài tối thiểu 8 ký tự.';

    alertEl.classList.remove('hidden');

    return;

  }



  if (newPassword !== confirmPassword) {

    alertEl.className = 'rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm leading-6 text-rose-800';

    alertEl.textContent = 'Mật khẩu xác nhận không trùng khớp.';

    alertEl.classList.remove('hidden');

    return;

  }



  btn.disabled = true;

  const originalHtml = btn.innerHTML;

  btn.innerHTML = `<span class="inline-block animate-spin mr-2">◌</span><span>Đang cập nhật...</span>`;



  try {

    const res = await fetch('/api/core/auth/reset-password/', {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken') || '',

      },

      body: JSON.stringify({

        uid,

        token,

        new_password: newPassword,

        confirm_password: confirmPassword,

      }),

    });

    const data = await res.json();

    if (res.ok) {

      alertEl.className = 'rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm leading-6 text-emerald-800';

      alertEl.innerHTML = `<strong>Thành công:</strong> ${data.message || 'Mật khẩu đã được đặt lại thành công.'} Đang chuyển hướng đến trang đăng nhập sau 2 giây...`;

      alertEl.classList.remove('hidden');

      if (newPassInput) newPassInput.value = '';

      if (confirmPassInput) confirmPassInput.value = '';

      setTimeout(() => {

        history.pushState({}, '', '/login');

        showPublicRoute('/login');

      }, 2000);

    } else {

      alertEl.className = 'rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm leading-6 text-rose-800';

      const msg = data.non_field_errors?.[0] || data.detail || data.error || (data.new_password ? data.new_password[0] : 'Không thể đặt lại mật khẩu.');

      alertEl.textContent = msg;

      alertEl.classList.remove('hidden');

      if (res.status === 400 && (msg.includes('hết hạn') || msg.includes('không hợp lệ'))) {

        document.getElementById('reset-token-invalid')?.classList.remove('hidden');

        document.getElementById('reset-password-form')?.classList.add('hidden');

      }

    }

  } catch (err) {

    alertEl.className = 'rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm leading-6 text-rose-800';

    alertEl.textContent = 'Lỗi kết nối máy chủ. Vui lòng thử lại sau.';

    alertEl.classList.remove('hidden');

  } finally {

    btn.disabled = false;

    btn.innerHTML = originalHtml;

    lucide.createIcons();

  }

}



function renderPendingConfirmation(registration) {

  const statusEl = document.getElementById('pending-account-status');

  const statusText = document.getElementById('pending-status-text');

  const userEl = document.getElementById('pending-user');

  const directNote = document.getElementById('pending-direct-note');

  const message = document.getElementById('pending-message');

  if (registration?.account_status === 'PENDING') {

    document.getElementById('pending-kicker').textContent = 'HỒ SƠ ĐÃ ĐƯỢC TIẾP NHẬN';

    document.getElementById('pending-title').textContent = 'Đăng ký thành công – Vui lòng chờ phê duyệt';

    statusEl?.classList.remove('hidden');

    statusText.textContent = 'Đang chờ duyệt';

    userEl.textContent = registration.full_name ? `Hồ sơ đăng ký: ${registration.full_name}` : '';

    directNote?.classList.add('hidden');

    message.textContent = 'Yêu cầu tạo tài khoản đã được máy chủ tiếp nhận. Bạn có thể sử dụng hệ thống sau khi tài khoản được phê duyệt và cấp quyền phù hợp.';

  } else {

    document.getElementById('pending-kicker').textContent = 'QUY TRÌNH ĐĂNG KÝ';

    document.getElementById('pending-title').textContent = 'Tài khoản cần được phê duyệt';

    statusEl?.classList.add('hidden');

    userEl.textContent = '';

    directNote?.classList.remove('hidden');

    message.textContent = 'Tài khoản mới cần được nhà trường phê duyệt trước khi có thể đăng nhập và sử dụng hệ thống. Trạng thái cá nhân chỉ được xác nhận sau khi máy chủ tiếp nhận biểu mẫu đăng ký.';

  }

  lucide.createIcons();

}



function togglePublicMenu() {

  const menu = document.getElementById('public-mobile-menu');

  const button = document.getElementById('public-menu-toggle');

  const isOpening = menu?.classList.contains('hidden');

  menu?.classList.toggle('hidden', !isOpening);

  button?.setAttribute('aria-expanded', String(Boolean(isOpening)));

  button?.setAttribute('aria-label', isOpening ? 'Đóng menu' : 'Mở menu');

}



function closePublicMenu() {

  document.getElementById('public-mobile-menu')?.classList.add('hidden');

  document.getElementById('public-menu-toggle')?.setAttribute('aria-expanded', 'false');

}



function togglePasswordVisibility(inputId, button) {

  const input = document.getElementById(inputId);

  if (!input || !button) return;

  const show = input.type === 'password';

  input.type = show ? 'text' : 'password';

  const label = show ? 'Ẩn' : 'Hiện';

  button.setAttribute('aria-label', show ? 'Ẩn mật khẩu' : 'Hiện mật khẩu');

  button.innerHTML = `<i data-lucide="${show ? 'eye-off' : 'eye'}" class="h-4 w-4"></i><span class="${inputId === 'login-password' ? 'hidden sm:inline' : 'sr-only'}">${label}</span>`;

  lucide.createIcons();

}



function switchToRegisterView() {

  history.pushState({}, '', '/register');

  clearRegistrationErrors();

  showPublicRoute('/register');

}



function switchToLoginView() {

  history.pushState({}, '', '/login');

  showPublicRoute('/login');

}



function clearRegistrationErrors() {

  const alert = document.getElementById('register-error-alert');

  if (alert) {

    alert.classList.add('hidden');

    alert.textContent = '';

  }

  document.querySelectorAll('[data-error-for]').forEach(node => { node.textContent = ''; });

  document.querySelectorAll('#register-form [aria-invalid="true"]').forEach(input => {

    input.removeAttribute('aria-invalid');

    input.removeAttribute('aria-describedby');

  });

}



let currentRegisterRole = 'HOC_SINH';



function setRegisterRole(role) {

  currentRegisterRole = role;

  const roleInput = document.getElementById('reg-requested-role');

  if (roleInput) roleInput.value = role;



  const radioStudent = document.getElementById('radio-role-student');

  const radioTeacher = document.getElementById('radio-role-teacher');

  const labelStudent = document.getElementById('label-role-student');

  const labelTeacher = document.getElementById('label-role-teacher');

  const studentSection = document.getElementById('reg-student-section');

  const teacherSection = document.getElementById('reg-teacher-section');

  const phoneReq = document.getElementById('reg-phone-required-mark');

  const phoneInput = document.getElementById('reg-phone');



  if (role === 'HOC_SINH') {

    if (radioStudent) radioStudent.checked = true;

    if (labelStudent) {

      labelStudent.className = 'flex items-center gap-3 rounded-xl border-2 border-[#2563EB] bg-blue-50/70 p-3.5 cursor-pointer shadow-sm transition';

      labelStudent.querySelector('i, svg')?.classList.add('text-[#2563EB]');

      labelStudent.querySelector('i, svg')?.classList.remove('text-slate-500');

    }

    if (labelTeacher) {

      labelTeacher.className = 'flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-3.5 cursor-pointer transition hover:bg-slate-50 hover:border-slate-300';

      labelTeacher.querySelector('i, svg')?.classList.remove('text-[#2563EB]');

      labelTeacher.querySelector('i, svg')?.classList.add('text-slate-500');

    }

    if (studentSection) studentSection.classList.remove('hidden');

    if (teacherSection) teacherSection.classList.add('hidden');

    if (phoneReq) phoneReq.textContent = '(không bắt buộc)';

    if (phoneInput) phoneInput.required = false;

  } else {

    if (radioTeacher) radioTeacher.checked = true;

    if (labelTeacher) {

      labelTeacher.className = 'flex items-center gap-3 rounded-xl border-2 border-[#2563EB] bg-blue-50/70 p-3.5 cursor-pointer shadow-sm transition';

      labelTeacher.querySelector('i, svg')?.classList.add('text-[#2563EB]');

      labelTeacher.querySelector('i, svg')?.classList.remove('text-slate-500');

    }

    if (labelStudent) {

      labelStudent.className = 'flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-3.5 cursor-pointer transition hover:bg-slate-50 hover:border-slate-300';

      labelStudent.querySelector('i, svg')?.classList.remove('text-[#2563EB]');

      labelStudent.querySelector('i, svg')?.classList.add('text-slate-500');

    }

    if (studentSection) studentSection.classList.add('hidden');

    if (teacherSection) teacherSection.classList.remove('hidden');

    if (phoneReq) {

      phoneReq.innerHTML = '<span class="text-rose-600 font-bold">*</span>';

    }

    if (phoneInput) phoneInput.required = true;

  }

  if (typeof lucide !== 'undefined' && lucide.createIcons) lucide.createIcons();

}



function onRegisterClassChange() {

  const classSelect = document.getElementById('reg-class');

  const gradeSelect = document.getElementById('reg-grade');

  if (!classSelect || !gradeSelect) return;

  const opt = classSelect.selectedOptions[0];

  const grade = opt?.getAttribute('data-grade');

  if (grade && gradeSelect.value !== grade) {

    gradeSelect.value = grade;

  }

}



async function onRegisterGradeChange() {

  const grade = document.getElementById('reg-grade')?.value;

  const classSelect = document.getElementById('reg-class');

  if (!classSelect) return;



  // Filter optgroups if present in DOM

  const optgroups = classSelect.querySelectorAll('optgroup');

  if (optgroups && optgroups.length > 0) {

    optgroups.forEach(group => {

      const label = group.getAttribute('label') || '';

      if (!grade || label.includes(`Khối ${grade}`)) {

        group.style.display = '';

      } else {

        group.style.display = 'none';

      }

    });

    const curOpt = classSelect.selectedOptions[0];

    if (grade && curOpt && curOpt.getAttribute('data-grade') && curOpt.getAttribute('data-grade') !== grade) {

      classSelect.value = '';

    }

    return;

  }



  // Fallback to fetch if optgroups were not pre-rendered

  classSelect.innerHTML = '<option value="">-- Đang tải danh sách lớp... --</option>';

  try {

    const res = await fetch(`/api/conduct/classes/?grade=${grade || ''}`);

    if (!res.ok) throw new Error('Không thể tải danh sách lớp');

    const data = await res.json();

    const classes = data.results || data;



    classSelect.innerHTML = '<option value="">-- Chọn lớp học chính thức --</option>';

    classes.forEach(cls => {

      const opt = document.createElement('option');

      opt.value = cls.id;

      opt.setAttribute('data-grade', cls.grade);

      opt.textContent = `Lớp ${cls.name}`;

      classSelect.appendChild(opt);

    });

  } catch (err) {

    classSelect.innerHTML = '<option value="">Lỗi tải lớp, vui lòng thử lại</option>';

  }

}



function setRegistrationFieldError(field, message) {

  const inputIds = {

    full_name: 'reg-fullname', username: 'reg-username', email: 'reg-email', phone: 'reg-phone',

    password: 'reg-password', confirm_password: 'reg-confirm-password', requested_role: 'reg-requested-role',

    grade_level: 'reg-grade', class_id: 'reg-class', subject: 'reg-subject',

    department_or_class: 'reg-class', terms_accepted: 'reg-terms'

  };

  const input = document.getElementById(inputIds[field]);

  const errorNode = document.querySelector(`[data-error-for="${field}"]`);

  if (input) {

    input.setAttribute('aria-invalid', 'true');

    if (errorNode) {

      errorNode.id ||= `registration-error-${field}`;

      input.setAttribute('aria-describedby', errorNode.id);

    }

  }

  if (errorNode) errorNode.textContent = message;

}



function renderRegistrationErrors(details) {

  let rendered = false;

  Object.entries(details || {}).forEach(([field, value]) => {

    let message = value;

    while (Array.isArray(message)) message = message[0];

    if (typeof message === 'string') {

      setRegistrationFieldError(field, message);

      rendered = true;

    }

  });

  return rendered;

}



async function handleRegisterSubmit(e) {

  e.preventDefault();

  const form = document.getElementById('register-form');

  const errorBox = document.getElementById('register-error-alert');

  const submitBtn = document.getElementById('btn-register-submit');

  const originalButton = '<i data-lucide="send" class="h-4 w-4"></i><span>Gửi yêu cầu đăng ký</span>';

  clearRegistrationErrors();

  if (!form.reportValidity()) return;



  const pwd = document.getElementById('reg-password').value;

  const confirmPwd = document.getElementById('reg-confirm-password').value;

  if (pwd !== confirmPwd) {

    setRegistrationFieldError('confirm_password', 'Mật khẩu nhập lại chưa khớp.');

    document.getElementById('reg-confirm-password').focus();

    return;

  }



  const role = currentRegisterRole;

  const payload = {

    full_name: document.getElementById('reg-fullname').value.trim(),

    username: document.getElementById('reg-username').value.trim(),

    email: document.getElementById('reg-email').value.trim(),

    phone: document.getElementById('reg-phone').value.trim(),

    password: pwd,

    confirm_password: confirmPwd,

    requested_role: role,

    terms_accepted: document.getElementById('reg-terms').checked,

    verification_info: document.getElementById('reg-verification-info')?.value.trim() || ''

  };



  if (role === 'HOC_SINH') {

    const grade = document.getElementById('reg-grade')?.value;

    const classId = document.getElementById('reg-class')?.value;

    if (!grade) {

      setRegistrationFieldError('grade_level', 'Vui lòng chọn khối học.');

      return;

    }

    if (!classId) {

      setRegistrationFieldError('class_id', 'Vui lòng chọn lớp học chính thức.');

      return;

    }

    payload.grade_level = parseInt(grade, 10);

    payload.class_id = parseInt(classId, 10);

    const classOpt = document.getElementById('reg-class')?.selectedOptions[0];

    payload.department_or_class = classOpt ? classOpt.text.replace('Lớp ', '') : '';

  } else if (role === 'GVBM') {

    const subject = document.getElementById('reg-subject')?.value;

    if (!subject) {

      setRegistrationFieldError('subject', 'Vui lòng chọn môn giảng dạy chính.');

      return;

    }

    if (!payload.phone) {

      setRegistrationFieldError('phone', 'Vui lòng cung cấp số điện thoại liên hệ của giáo viên.');

      return;

    }

    payload.subject = subject;

    payload.department_or_class = subject;

  }



  submitBtn.disabled = true;

  submitBtn.innerHTML = '<span class="animate-pulse">Đang gửi yêu cầu đăng ký…</span>';

  try {

    const res = await fetch('/api/core/auth/register/', {

      method: 'POST',

      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },

      signal: AbortSignal.timeout(15000),

      body: JSON.stringify(payload)

    });

    const data = await res.json();

    if (!res.ok) {

      const hasFieldErrors = renderRegistrationErrors(data.details);

      errorBox.textContent = hasFieldErrors ? 'Vui lòng kiểm tra lại các thông tin được đánh dấu.' : (data.error || 'Đăng ký tài khoản không thành công. Vui lòng thử lại.');

      errorBox.classList.remove('hidden');

      errorBox.focus?.();

      return;

    }

    history.pushState({ registration: { account_status: data.account_status, username: data.username, full_name: data.full_name } }, '', '/registration-pending');

    showPublicRoute('/registration-pending');

    document.getElementById('registration-pending-box')?.focus?.();

  } catch (err) {

    errorBox.textContent = 'Không thể kết nối đến máy chủ. Vui lòng kiểm tra kết nối và thử lại.';

    errorBox.classList.remove('hidden');

  } finally {

    submitBtn.disabled = false;

    submitBtn.innerHTML = originalButton;

    lucide.createIcons();

  }

}



async function handleLoginSubmit(e) {

  e.preventDefault();

  const form = document.getElementById('login-form');

  const username = document.getElementById('login-username').value.trim();

  const password = document.getElementById('login-password').value;

  const errorBox = document.getElementById('login-error-alert');

  const submitBtn = document.getElementById('btn-login-submit');

  if (!form.reportValidity()) return;

  errorBox.classList.add('hidden');

  errorBox.textContent = '';

  submitBtn.disabled = true;

  submitBtn.innerHTML = '<span class="animate-pulse">Đang xác thực…</span>';

  try {

    const res = await fetch('/api/core/auth/login/', {

      method: 'POST',

      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },

      signal: AbortSignal.timeout(15000),

      body: JSON.stringify({ username, password })

    });

    const data = await res.json();

    if (res.ok) {

      showToast(data.message, 'success');

      if (await activateAuthenticatedUser(data.user)) {

        history.replaceState({}, '', '/');

        navigateTab('dashboard');

      }

    } else {

      const statusLabels = {

        PENDING: 'Đang chờ duyệt', APPROVED: 'Đã phê duyệt', REJECTED: 'Chưa được chấp thuận',

        SUSPENDED: 'Tạm khóa', DISABLED: 'Đã vô hiệu hóa'

      };

      const statusLabel = statusLabels[data.account_status];

      errorBox.textContent = `${statusLabel ? `Trạng thái tài khoản: ${statusLabel}. ` : ''}${data.error || 'Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin.'}`;

      errorBox.classList.remove('hidden');

      errorBox.focus();

    }

  } catch (err) {

    errorBox.textContent = 'Không thể kết nối đến máy chủ. Vui lòng kiểm tra kết nối và thử lại.';

    errorBox.classList.remove('hidden');

  } finally {

    submitBtn.disabled = false;

    submitBtn.innerHTML = '<i data-lucide="log-in" class="h-4 w-4"></i><span>Đăng nhập</span>';

    lucide.createIcons();

  }

}



async function handlePasswordChangeSubmit(e) {

  e.preventDefault();

  const returnTab = activeTab;

  const errorBox = document.getElementById('password-change-error');

  errorBox.classList.add('hidden');

  errorBox.textContent = '';



  try {

    const res = await fetch('/api/core/auth/change-password/', {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken')

      },

      body: JSON.stringify({

        current_password: document.getElementById('current-password').value,

        new_password: document.getElementById('new-password').value,

        confirm_password: document.getElementById('confirm-password').value

      })

    });

    const data = await res.json();

    if (!res.ok) {

      errorBox.textContent = data.error || 'Không thể đổi mật khẩu.';

      errorBox.classList.remove('hidden');

      return;

    }



    document.getElementById('password-change-form').reset();

    currentUser = data.user;

    document.getElementById('password-change-overlay').classList.add('hidden');

    updateUserUI();

    showToast(data.message, 'success');

    renderProfile();

    if (returnTab !== 'profile') {

      await loadMetadata();

      await loadDashboard();

      navigateTab('dashboard');

    }

  } catch (err) {

    errorBox.textContent = 'Không thể kết nối đến máy chủ. Vui lòng thử lại.';

    errorBox.classList.remove('hidden');

  }

}



async function handleLogout() {

  if (!confirm('Bạn có chắc chắn muốn đăng xuất khỏi hệ thống?')) return;

  try {

    const response = await fetch('/api/core/auth/logout/', {

      method: 'POST',

      headers: {

        'X-CSRFToken': getCookie('csrftoken')

      }

    });

    if (!response.ok) throw new Error(`Logout failed with status ${response.status}`);

    currentUser = null;

    window.location.replace('/');

  } catch (err) {

    showToast('Lỗi khi đăng xuất', 'error');

  }

}



function isAdminUser(user = currentUser) {

  return Boolean(user && (user.is_admin || user.is_super_admin || user.is_superuser || user.role === 'ADMIN' || user.role === 'SUPER_ADMIN'));

}



function userHasPermission(permission, user = currentUser) {

  if (!user) return false;

  if (user.is_admin || user.is_super_admin || user.role === 'ADMIN' || user.role === 'SUPER_ADMIN') return true;

  if (user.is_doan_truong || user.role === 'DOAN_TRUONG') {

    if (permission === 'admin.all' || permission === 'settings.manage' || permission === 'audit_logs.delete') return false;

    return true; // Đoàn trường có toàn quyền nghiệp vụ tương đương admin

  }

  return Boolean(Array.isArray(user.permissions) && user.permissions.includes(permission));

}



function getAllowedTabs(user = currentUser) {

  const allowed = new Set(['dashboard', 'profile']);

  if (!user) return allowed;

  if (isAdminUser(user)) {

    ['teacher-classes', 'conduct', 'competition', 'alerts', 'counseling', 'reports', 'student-approvals', 'doan-truong', 'red-star', 'users', 'settings'].forEach(tab => allowed.add(tab));

    return allowed;

  }

  if (user.is_doan_truong || user.role === 'DOAN_TRUONG') {

    // Đoàn trường có toàn quyền nghiệp vụ bao gồm theo dõi lớp học, nề nếp và thi đua

    ['teacher-classes', 'conduct', 'competition', 'alerts', 'counseling', 'reports', 'student-approvals', 'doan-truong', 'red-star', 'sao-do-duty', 'users'].forEach(tab => allowed.add(tab));

    return allowed;

  }

  if (isAdminUser(user)) {

    allowed.add('teacher-classes');

  }

  if (user.role === 'BGH' || user.is_bgh) {

    ['conduct', 'competition', 'alerts', 'reports', 'teacher-classes'].forEach(tab => allowed.add(tab));

  } else if (user.is_gvcn || user.role === 'GVCN') {

    ['conduct', 'competition', 'alerts', 'reports', 'counseling', 'teacher-classes'].forEach(tab => allowed.add(tab));

  } else if (user.role === 'GVBM' || user.is_gvbm) {

    ['conduct', 'counseling', 'teacher-classes'].forEach(tab => allowed.add(tab));

  } else if (user.is_student || user.role === 'HOC_SINH') {

    ['teacher-classes', 'counseling'].forEach(tab => allowed.add(tab));
    if (user.is_class_monitor || user.student_profile?.is_class_monitor) {
      allowed.add('conduct');
    }

  } else if (user.role === 'CHUYEN_VIEN_TAM_LY' || user.has_counseling_access) {

    allowed.add('counseling');

  }

  if (user.is_active_red_star && !user.is_doan_truong && user.role !== 'DOAN_TRUONG') {

    allowed.add('sao-do-duty');

    allowed.add('conduct');

  }

  return allowed;

}



const NAV_LABELS = {

  dashboard: ['Tổng quan', 'layout-dashboard'],

  'teacher-classes': ['Lớp & Học sinh', 'graduation-cap'],

  conduct: ['Nền nếp', 'clipboard-list'],

  competition: ['Thi đua', 'award'],

  alerts: ['Cảnh báo', 'bell-ring'],

  counseling: ['Góc sẻ chia', 'heart-handshake'],

  reports: ['Báo cáo', 'file-spreadsheet'],

  'student-approvals': ['Duyệt học sinh', 'user-check'],

  'doan-truong': ['Quản lý Đoàn trường', 'shield-check'],

  'red-star': ['Phân công Sao đỏ', 'star'],

  'sao-do-duty': ['Nhiệm vụ Sao đỏ', 'star'],

  users: ['Người dùng', 'users-round'],

  settings: ['Cấu hình', 'settings'],

  profile: ['Hồ sơ', 'user-round'],

};



function renderMobileBottomNav(allowedTabs) {

  const container = document.getElementById('mobile-bottom-nav-items');

  if (!container) return;

  const priorities = (currentUser?.role === 'DOAN_TRUONG' || currentUser?.is_doan_truong)

    ? ['dashboard', 'conduct', 'competition', 'student-approvals', 'red-star', 'profile']

    : currentUser?.is_active_red_star

      ? ['dashboard', 'sao-do-duty', 'conduct', 'profile']

      : currentUser?.is_student || currentUser?.role === 'HOC_SINH'

        ? ['dashboard', 'teacher-classes', 'counseling', 'profile']

        : currentUser?.is_gvcn || currentUser?.role === 'GVCN'

          ? ['dashboard', 'alerts', 'conduct', 'competition']

          : ['dashboard', 'conduct', 'competition', 'student-approvals'];

  const visible = priorities.filter(tab => allowedTabs.has(tab));

  const tabs = visible.slice(0, 4);

  const hasMore = Array.from(allowedTabs).some(tab => !tabs.includes(tab));

  container.innerHTML = tabs.map(tab => {

    const [label, icon] = NAV_LABELS[tab];

    return `<button type="button" data-mobile-tab="${tab}" onclick="navigateTab('${tab}')" class="mobile-nav-button" aria-label="${label}"><i data-lucide="${icon}" class="w-5 h-5"></i><span>${label}</span></button>`;

  }).join('') + (hasMore ? '<button type="button" onclick="toggleMobileMenu()" class="mobile-nav-button" aria-label="Mở thêm mục"><i data-lucide="menu" class="w-5 h-5"></i><span>Thêm</span></button>' : '');

  lucide.createIcons();

}



function updateUserUI() {

  if (!currentUser) return;

  const isAdmin = isAdminUser();

  const allowed = getAllowedTabs();

  const displayName = currentUser.full_name || currentUser.username || 'Người dùng';

  const headerName = document.getElementById('user-display-name');

  const roleText = document.getElementById('user-role-text');

  const dashName = document.getElementById('dash-user-name');

  const dashRole = document.getElementById('dash-role-badge');

  if (headerName) headerName.textContent = displayName;

  if (roleText) roleText.textContent = currentUser.role_display || '';

  if (dashName) dashName.textContent = displayName;

  if (dashRole) dashRole.textContent = currentUser.role_display || 'Tổng quan';



  const initials = displayName.split(/\s+/).map(part => part[0]).join('').substring(0, 2).toUpperCase() || 'HK';

  const avatarFallback = document.getElementById('user-avatar-text');

  if (avatarFallback) avatarFallback.textContent = initials;

  setAvatarImage(document.getElementById('user-avatar-image'), avatarFallback, currentUser.avatar);



  const navTabs = {

    dashboard: 'nav-btn-dashboard', 'teacher-classes': 'nav-btn-teacher-classes', conduct: 'nav-btn-conduct', competition: 'nav-btn-competition',

    alerts: 'nav-btn-alerts', counseling: 'nav-btn-counseling', reports: 'nav-btn-reports',

    'student-approvals': 'nav-btn-student-approvals', 'doan-truong': 'nav-btn-doan-truong',

    'red-star': 'nav-btn-red-star', 'sao-do-duty': 'nav-btn-sao-do-duty',

    users: 'nav-btn-users', settings: 'nav-btn-settings', profile: 'nav-btn-profile',

  };

  Object.entries(navTabs).forEach(([tab, id]) => {

    const button = document.getElementById(id);

    if (button) button.classList.toggle('hidden', !allowed.has(tab));

  });

  const isStudentUser = currentUser && (currentUser.is_student || currentUser.role === 'HOC_SINH');
  const tcNavBtn = document.getElementById('nav-btn-teacher-classes');
  if (tcNavBtn) {
    const span = tcNavBtn.querySelector('span');
    if (span) {
      span.textContent = isStudentUser ? 'Lớp học của tôi' : 'Lớp học & Học sinh';
    }
  }
  if (NAV_LABELS && NAV_LABELS['teacher-classes']) {
    NAV_LABELS['teacher-classes'][0] = isStudentUser ? 'Lớp của tôi' : 'Lớp & Học sinh';
  }




  // Hiển thị/ẩn tiêu đề nhóm sidebar theo quyền

  const navGroups = {

    main: ['teacher-classes', 'conduct', 'competition'],

    overview: ['teacher-classes', 'conduct', 'competition', 'sao-do-duty'],

    management: ['student-approvals', 'doan-truong', 'red-star', 'users'],

    support: ['alerts', 'counseling'],

    admin: ['reports', 'settings'],

    account: ['profile'],

  };

  Object.entries(navGroups).forEach(([grp, tabs]) => {

    const heading = document.querySelector(`[data-nav-group="${grp}"]`);

    if (heading) {

      const hasVisible = tabs.some(t => allowed.has(t));

      heading.classList.toggle('hidden', !hasVisible);

    }

  });



  // Cập nhật thông tin trong Mobile Drawer

  const mAvatar = document.getElementById('mobile-drawer-avatar');

  const mName = document.getElementById('mobile-drawer-name');

  const mRole = document.getElementById('mobile-drawer-role');

  const mNavList = document.getElementById('mobile-drawer-nav-list');

  if (mAvatar) mAvatar.textContent = initials;

  if (mName) mName.textContent = displayName;

  if (mRole) mRole.textContent = currentUser.role_display || 'Thành viên';

  if (mNavList) {

    mNavList.innerHTML = Array.from(allowed).map(tab => {

      const info = NAV_LABELS[tab];

      if (!info) return '';

      const [label, icon] = info;

      const isAct = activeTab === tab;

      return `<button type="button" data-mobile-drawer-tab="${tab}" onclick="navigateTab('${tab}')" class="mobile-drawer-nav-item ${isAct ? 'is-active' : ''}"><i data-lucide="${icon}" class="w-4 h-4 text-slate-500"></i><span>${label}</span></button>`;

    }).join('');

  }



  const quickWidget = document.getElementById('quick-action-widget');

  const canQuickReport = (isAdmin || currentUser.is_bgh || currentUser.is_doan_truong || currentUser.role === 'DOAN_TRUONG' || currentUser.is_gvcn || currentUser.is_active_red_star);

  if (quickWidget) quickWidget.classList.toggle('hidden', !canQuickReport);

  document.getElementById('red-star-assignment-panel')?.classList.toggle('hidden', !(isAdmin || userHasPermission('red_star.assign')));

  document.getElementById('sao-do-report-panel')?.classList.toggle('hidden', !currentUser.is_active_red_star);

  renderMobileBottomNav(allowed);

  if (window.lucide) lucide.createIcons();

}



function setAvatarImage(image, fallback, avatarUrl) {

  if (!image || !fallback) return;

  if (!avatarUrl) {

    image.classList.add('hidden');

    fallback.classList.remove('hidden');

    image.removeAttribute('src');

    return;

  }

  image.onload = () => {

    image.classList.remove('hidden');

    fallback.classList.add('hidden');

  };

  image.onerror = () => {

    image.classList.add('hidden');

    fallback.classList.remove('hidden');

  };

  image.src = avatarUrl;

}



function renderProfile() {

  if (!currentUser) return;

  const name = currentUser.full_name || '';

  const initials = (name || currentUser.username || '?').split(/\s+/).map(part => part[0]).join('').substring(0, 2).toUpperCase();

  const fullNameInput = document.getElementById('profile-full-name');

  if (!fullNameInput) return;

  fullNameInput.value = name;

  document.getElementById('profile-username').value = currentUser.username || '';

  document.getElementById('profile-role').value = currentUser.role_display || currentUser.role || '';

  document.getElementById('profile-email').value = currentUser.email || '';

  document.getElementById('profile-phone').value = currentUser.phone || '';

  document.getElementById('profile-department').value =

    currentUser.meta?.class_name || currentUser.department_or_class || 'Chưa cập nhật';

  const joined = currentUser.date_joined ? new Date(currentUser.date_joined) : null;

  document.getElementById('profile-date-joined').value =

    joined && !Number.isNaN(joined.getTime()) ? joined.toLocaleDateString('vi-VN') : '—';

  document.getElementById('profile-avatar-name').textContent = name || currentUser.username;

  const fallback = document.getElementById('profile-avatar-fallback');

  if (fallback) fallback.textContent = initials;

  setAvatarImage(

    document.getElementById('profile-avatar-image'),

    fallback,

    currentUser.avatar

  );

  renderProfileClassSection();

}



function setProfileEditing(editing) {

  ['profile-full-name', 'profile-phone', 'profile-email'].forEach(id => {

    const el = document.getElementById(id);
    if (el) el.disabled = !editing;

  });

  document.getElementById('profile-edit-button').classList.toggle('hidden', editing);

  const actions = document.getElementById('profile-edit-actions');

  actions.classList.toggle('hidden', !editing);

  actions.classList.toggle('flex', editing);

  document.getElementById('profile-avatar-choose').classList.toggle('hidden', !editing);

  document.getElementById('profile-avatar-help').textContent = editing

    ? 'Ảnh mới chỉ được lưu khi bạn nhấn “Lưu thay đổi”.'

    : 'Ảnh hiện tại được dùng trong header và hồ sơ của bạn.';

  if (editing) document.getElementById('profile-full-name').focus();

}



function clearProfileAvatarPreview() {

  if (profileAvatarPreviewUrl) URL.revokeObjectURL(profileAvatarPreviewUrl);

  profileAvatarPreviewUrl = null;

  document.getElementById('profile-avatar-input').value = '';

}



function previewProfileAvatar(event) {

  const file = event.target.files?.[0];

  if (!file) return;

  if (file.size > 5 * 1024 * 1024) {

    showToast('Ảnh đại diện không được vượt quá 5 MB.', 'error');

    clearProfileAvatarPreview();

    renderProfile();

    return;

  }

  const extension = file.name.split('.').pop()?.toLowerCase();

  if (!['jpg', 'jpeg', 'png', 'webp'].includes(extension)) {

    showToast('Chỉ chấp nhận ảnh JPG, PNG hoặc WebP.', 'error');

    clearProfileAvatarPreview();

    renderProfile();

    return;

  }

  if (profileAvatarPreviewUrl) URL.revokeObjectURL(profileAvatarPreviewUrl);

  profileAvatarPreviewUrl = URL.createObjectURL(file);

  setAvatarImage(

    document.getElementById('profile-avatar-image'),

    document.getElementById('profile-avatar-fallback'),

    profileAvatarPreviewUrl

  );

}



function cancelProfileEditing() {

  clearProfileAvatarPreview();

  renderProfile();

  setProfileEditing(false);

}



async function saveProfileChanges(event) {

  event.preventDefault();

  const form = document.getElementById('profile-form');

  if (!form.reportValidity()) return;

  const fullName = document.getElementById('profile-full-name').value.trim();

  if (!fullName) {

    showToast('Họ và tên không được để trống.', 'error');

    return;

  }



  const saveButton = document.getElementById('profile-save-button');

  saveButton.disabled = true;

  try {

    const response = await fetch('/api/core/auth/profile/', {

      method: 'PATCH',

      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },

      body: JSON.stringify({

        full_name: fullName,

        phone: document.getElementById('profile-phone').value.trim(),

        email: document.getElementById('profile-email').value.trim()

      })

    });

    const data = await response.json();

    if (!response.ok) throw new Error(data.error || 'Không thể lưu hồ sơ.');

    currentUser = { ...currentUser, ...data };

    updateUserUI();

    renderProfile();



    const avatarFile = document.getElementById('profile-avatar-input').files?.[0];

    if (avatarFile) {

      const avatarForm = new FormData();

      avatarForm.append('avatar', avatarFile);

      const avatarResponse = await fetch('/api/core/auth/profile/avatar/', {

        method: 'POST',

        headers: { 'X-CSRFToken': getCookie('csrftoken') },

        body: avatarForm

      });

      const avatarData = await avatarResponse.json();

      if (!avatarResponse.ok) {

        throw new Error(`Thông tin đã lưu nhưng ảnh đại diện chưa được lưu: ${avatarData.error || 'Vui lòng thử lại.'}`);

      }

      currentUser = { ...currentUser, ...avatarData };

      clearProfileAvatarPreview();

      updateUserUI();

      renderProfile();

    }

    setProfileEditing(false);

    showToast('Đã lưu hồ sơ cá nhân.', 'success');

  } catch (error) {

    showToast(error.message || 'Không thể lưu hồ sơ. Vui lòng thử lại.', 'error');

  } finally {

    saveButton.disabled = false;

  }

}




// ==========================================
// PROFILE CLASS MANAGEMENT (STUDENT & TEACHER)
// ==========================================

let currentProfileTeacherGrade = 'ALL';

function filterProfileTeacherGrade(grade) {
  currentProfileTeacherGrade = grade;
  ['ALL', '10', '11', '12'].forEach(g => {
    const btn = document.getElementById(`profile-grade-btn-${g}`);
    if (btn) {
      if (String(g) === String(grade)) {
        btn.className = 'px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-900 text-white transition shadow-sm';
      } else {
        btn.className = 'px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-700 hover:bg-slate-200 transition';
      }
    }
  });
  renderProfileTeacherClasses(grade);
}

function renderProfileTeacherClasses(filterGrade = 'ALL') {
  const container = document.getElementById('profile-teacher-classes-grid');
  if (!container) return;

  const classes = (classesCache && classesCache.length > 0) ? classesCache : [];
  if (classes.length === 0) {
    container.innerHTML = '<div class="col-span-full py-4 text-center text-slate-400 text-xs font-medium">Đang tải danh sách lớp...</div>';
    fetch('/api/conduct/classes/').then(r => r.json()).then(data => {
      classesCache = data.results || data;
      renderProfileTeacherClasses(filterGrade);
    }).catch(() => {});
    return;
  }

  // Get active assigned classes
  const assignedList = currentUser?.teaching_classes || (currentUser?.meta?.teaching_classes || []).map(c => c.name || c) || [];
  const assignedSet = new Set(assignedList);

  // Preserve existing UI selections if user toggled
  const existingChecked = new Set();
  document.querySelectorAll('.profile-teacher-class-cb:checked').forEach(cb => existingChecked.add(cb.value));

  // Sort classes 10A1 -> 12A22
  const sortedClasses = [...classes].sort((a, b) => {
    if (a.grade !== b.grade) return a.grade - b.grade;
    return a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' });
  });

  const filtered = sortedClasses.filter(c => {
    if (filterGrade === 'ALL') return true;
    return String(c.grade) === String(filterGrade);
  });

  container.innerHTML = filtered.map(c => {
    const isChecked = existingChecked.size > 0 ? existingChecked.has(c.name) : assignedSet.has(c.name);
    return `
      <label class="flex items-center gap-2 p-2 bg-white rounded-lg border border-slate-200 hover:border-emerald-500 cursor-pointer text-xs font-semibold select-none shadow-2xs">
        <input type="checkbox" value="${escapeHtml(c.name)}" class="profile-teacher-class-cb rounded text-emerald-600 focus:ring-emerald-500" ${isChecked ? 'checked' : ''} onchange="updateProfileTeacherClassesCount()">
        <span>${escapeHtml(c.name)}</span>
      </label>
    `;
  }).join('');

  updateProfileTeacherClassesCount();
}

function updateProfileTeacherClassesCount() {
  const count = document.querySelectorAll('.profile-teacher-class-cb:checked').length;
  const badge = document.getElementById('profile-teacher-classes-count-badge');
  if (badge) badge.textContent = `${count} lớp đã chọn`;
}

function populateStudentTargetClassSelect(currentClassName) {
  const select = document.getElementById('profile-student-target-class');
  if (!select) return;

  const classes = (classesCache && classesCache.length > 0) ? classesCache : [];
  if (classes.length === 0) {
    fetch('/api/conduct/classes/').then(r => r.json()).then(data => {
      classesCache = data.results || data;
      populateStudentTargetClassSelect(currentClassName);
    }).catch(() => {});
    return;
  }

  const sorted = [...classes].sort((a, b) => {
    if (a.grade !== b.grade) return a.grade - b.grade;
    return a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' });
  });

  select.innerHTML = '<option value="">-- Chọn lớp học --</option>' +
    sorted
      .filter(c => c.name !== currentClassName)
      .map(c => `<option value="${escapeHtml(c.name)}">Lớp ${escapeHtml(c.name)} (Khối ${c.grade})</option>`)
      .join('');
}

async function renderProfileClassSection() {
  const section = document.getElementById('profile-class-section');
  if (!section || !currentUser) return;

  const isStudent = currentUser.role === 'HOC_SINH' || currentUser.is_student;
  const isTeacher = currentUser.role === 'GVBM' || currentUser.role === 'GVCN' || currentUser.is_gvbm || currentUser.is_gvcn;

  if (!isStudent && !isTeacher) {
    section.classList.add('hidden');
    return;
  }

  section.classList.remove('hidden');

  if (isStudent) {
    const studentBox = document.getElementById('profile-student-class-box');
    const teacherBox = document.getElementById('profile-teacher-class-box');
    if (studentBox) studentBox.classList.remove('hidden');
    if (teacherBox) teacherBox.classList.add('hidden');

    const currentClass = currentUser.meta?.class_name || currentUser.student_class_name || currentUser.department_or_class || 'Chưa phân lớp';
    const badge = document.getElementById('profile-student-current-class-badge');
    if (badge) badge.textContent = currentClass;

    // Check pending class change
    let pending = currentUser.pending_class_change || currentUser.meta?.pending_class_change;
    if (!pending && currentUser.verification_info && currentUser.verification_info.startsWith('{')) {
      try {
        const v = JSON.parse(currentUser.verification_info);
        pending = v.pending_class_change;
      } catch(e) {}
    }

    const pendingBanner = document.getElementById('profile-student-pending-banner');
    const changeForm = document.getElementById('profile-student-change-form');

    if (pending) {
      if (pendingBanner) {
        document.getElementById('profile-student-pending-text').innerHTML =
          `Đang xin chuyển từ lớp <b>${escapeHtml(pending.previous_class || currentClass)}</b> sang lớp <b class="text-blue-700">${escapeHtml(pending.target_class_name)}</b>.<br><span class="italic text-[11px] text-amber-700">Lý do: ${escapeHtml(pending.reason || 'Nguyện vọng học tập')}</span>`;
        pendingBanner.classList.remove('hidden');
      }
      if (changeForm) changeForm.classList.add('hidden');
    } else {
      if (pendingBanner) pendingBanner.classList.add('hidden');
      if (changeForm) {
        changeForm.classList.remove('hidden');
        populateStudentTargetClassSelect(currentClass);
      }
    }
  } else if (isTeacher) {
    const studentBox = document.getElementById('profile-student-class-box');
    const teacherBox = document.getElementById('profile-teacher-class-box');
    if (studentBox) studentBox.classList.add('hidden');
    if (teacherBox) teacherBox.classList.remove('hidden');

    const subjInput = document.getElementById('profile-teacher-subject');
    if (subjInput) {
      subjInput.value = currentUser.teacher_subject || currentUser.meta?.teaching_classes?.[0]?.subject || currentUser.subject || '';
    }

    filterProfileTeacherGrade('ALL');
  }
}

async function submitStudentClassChangeRequest() {
  const targetClass = document.getElementById('profile-student-target-class')?.value;
  if (!targetClass) {
    showToast('Vui lòng chọn lớp bạn muốn chuyển đến.', 'error');
    return;
  }

  const reason = (document.getElementById('profile-student-change-reason')?.value || '').trim();
  const btn = document.getElementById('btn-submit-student-class-change');
  if (btn) btn.disabled = true;

  try {
    const res = await fetch('/api/core/auth/profile/', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({
        target_class_name: targetClass,
        class_change_reason: reason
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Không thể gửi yêu cầu đổi lớp.');

    showToast(data.message || 'Yêu cầu đổi lớp đã được gửi tới Quản trị viên để xét duyệt!', 'success');
    currentUser = { ...currentUser, ...data };
    updateUserUI();
    renderProfile();
  } catch (err) {
    showToast(err.message || 'Lỗi khi gửi yêu cầu đổi lớp.', 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function cancelStudentClassChangeRequest() {
  if (!confirm('Bạn có chắc chắn muốn hủy yêu cầu đổi lớp này?')) return;

  try {
    const res = await fetch('/api/core/auth/profile/', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({
        cancel_class_change: true
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Không thể hủy yêu cầu.');

    showToast('Đã hủy yêu cầu chuyển lớp thành công.', 'info');
    currentUser = { ...currentUser, ...data };
    updateUserUI();
    renderProfile();
  } catch (err) {
    showToast(err.message || 'Lỗi khi hủy yêu cầu đổi lớp.', 'error');
  }
}

async function submitTeacherClassesUpdate() {
  const checkboxes = document.querySelectorAll('.profile-teacher-class-cb:checked');
  const selectedClasses = Array.from(checkboxes).map(cb => cb.value);
  const subject = (document.getElementById('profile-teacher-subject')?.value || '').trim();

  const btn = document.getElementById('btn-submit-teacher-classes');
  if (btn) btn.disabled = true;

  try {
    const res = await fetch('/api/core/auth/profile/', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({
        teaching_classes: selectedClasses,
        subject: subject
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Không thể cập nhật danh sách lớp.');

    showToast(data.message || 'Đã cập nhật danh sách phân công lớp giảng dạy thành công!', 'success');
    currentUser = { ...currentUser, ...data };
    updateUserUI();
    renderProfile();

    if (typeof loadTeacherClassesModule === 'function') {
      loadTeacherClassesModule(true);
    }
  } catch (err) {
    showToast(err.message || 'Lỗi khi lưu phân công lớp.', 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function handleReviewClassChange(userId, action) {
  let reason = '';
  if (action === 'reject') {
    reason = prompt('Nhập lý do từ chối yêu cầu đổi lớp (nếu có):') || '';
    if (reason === null) return;
  } else {
    if (!confirm('Bạn có chắc chắn muốn phê duyệt chuyển lớp cho học sinh này không?')) return;
  }

  try {
    const res = await fetch(`/api/core/users/${userId}/review-class-change/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({ action, reason }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Thao tác không thành công.');

    showToast(data.message || 'Đã xử lý yêu cầu đổi lớp thành công.', 'success');

    if (data.user && Array.isArray(allUsersCache)) {
      const idx = allUsersCache.findIndex(x => String(x.id) === String(userId));
      if (idx !== -1) allUsersCache[idx] = data.user;
    }

    closeUserDetailModal();

    if (typeof loadUsers === 'function') loadUsers();
    if (typeof loadStudentApprovals === 'function') loadStudentApprovals();
  } catch (err) {
    showToast(err.message || 'Lỗi khi xử lý yêu cầu đổi lớp.', 'error');
  }
}

function openPasswordChange() {

  const overlay = document.getElementById('password-change-overlay');

  const required = Boolean(currentUser?.must_change_password);

  document.getElementById('password-change-title').textContent =

    required ? 'Đổi mật khẩu bắt buộc' : 'Đổi mật khẩu';

  document.getElementById('password-change-description').textContent =

    required ? 'Hãy đặt mật khẩu mới trước khi sử dụng hệ thống.' : 'Nhập mật khẩu hiện tại và chọn mật khẩu mới an toàn.';

  document.getElementById('password-change-close').classList.toggle('hidden', required);

  overlay.classList.remove('hidden');

  document.getElementById('current-password').focus();

}



function closePasswordChange() {

  if (currentUser?.must_change_password) return;

  document.getElementById('password-change-overlay').classList.add('hidden');

  document.getElementById('password-change-form').reset();

  document.getElementById('password-change-error').classList.add('hidden');

}



// ==========================================

// NOTIFICATIONS SYSTEM

// ==========================================

let notificationsCache = [];



async function loadNotifications() {

  if (!currentUser) return;

  try {

    const resCount = await fetch('/api/core/notifications/unread-count/');

    if (resCount.ok) {

      const data = await resCount.json();

      const badge = document.getElementById('notif-badge');

      if (badge) {

        if (data.unread_count > 0) {

          badge.textContent = data.unread_count > 99 ? '99+' : data.unread_count;

          badge.classList.remove('hidden');

        } else {

          badge.classList.add('hidden');

        }

      }

    }

  } catch (err) {

    console.error('Lỗi tải số thông báo:', err);

  }

}



async function toggleNotificationDropdown() {

  const dropdown = document.getElementById('notif-dropdown');

  if (!dropdown) return;

  const isHidden = dropdown.classList.contains('hidden');

  if (isHidden) {

    dropdown.classList.remove('hidden');

    await fetchAndRenderNotifications();

  } else {

    dropdown.classList.add('hidden');

  }

}



async function fetchAndRenderNotifications() {

  const container = document.getElementById('notif-list');

  if (!container) return;

  try {

    container.innerHTML = '<div class="p-4 text-center text-slate-400">Đang tải thông báo...</div>';

    const res = await fetch('/api/core/notifications/');

    if (!res.ok) throw new Error('Không thể tải thông báo');

    const data = await res.json();

    notificationsCache = data.results || data;



    if (notificationsCache.length === 0) {

      container.innerHTML = '<div class="p-4 text-center text-slate-400">Không có thông báo mới.</div>';

      return;

    }



    container.innerHTML = notificationsCache.map(n => {

      const isUnread = !n.read_at;

      return `

        <div onclick="handleNotificationClick(${n.id}, '${n.link || ''}')" class="p-3 transition cursor-pointer hover:bg-slate-50 flex items-start space-x-2.5 ${isUnread ? 'bg-blue-50/70 font-medium' : ''}">

          <div class="mt-1 w-2 h-2 rounded-full ${isUnread ? 'bg-rose-500' : 'bg-slate-300'} shrink-0"></div>

          <div class="flex-1 min-w-0">

            <div class="flex items-center justify-between gap-1">

              <span class="text-xs font-bold text-slate-800 truncate">${escapeHtml(n.title)}</span>

              <span class="text-[10px] text-slate-400 whitespace-nowrap">${new Date(n.created_at).toLocaleDateString('vi-VN')}</span>

            </div>

            <p class="text-[11px] text-slate-600 mt-0.5 line-clamp-2 leading-relaxed">${escapeHtml(n.message)}</p>

          </div>

        </div>

      `;

    }).join('');

    lucide.createIcons();

  } catch (err) {

    container.innerHTML = '<div class="p-4 text-center text-rose-500">Lỗi khi tải thông báo.</div>';

  }

}



async function handleNotificationClick(notifId, link) {

  try {

    await fetch(`/api/core/notifications/${notifId}/mark-read/`, {

      method: 'POST',

      headers: { 'X-CSRFToken': getCookie('csrftoken') }

    });

    await loadNotifications();

    const dropdown = document.getElementById('notif-dropdown');

    if (dropdown) dropdown.classList.add('hidden');

    if (link && link.startsWith('/admin/users')) {

      if (currentUser && (currentUser.is_admin || currentUser.is_super_admin || currentUser.role === 'ADMIN' || currentUser.role === 'SUPER_ADMIN')) {

        navigateTab('users');

      }

    }

  } catch (e) {

    console.error('Lỗi đánh dấu thông báo:', e);

  }

}



async function markAllNotificationsRead() {

  try {

    const res = await fetch('/api/core/notifications/mark-all-read/', {

      method: 'POST',

      headers: { 'X-CSRFToken': getCookie('csrftoken') }

    });

    const data = await res.json();

    showToast(data.message || 'Đã đánh dấu đã đọc tất cả thông báo.', 'success');

    await loadNotifications();

    await fetchAndRenderNotifications();

  } catch (err) {

    showToast('Lỗi khi đánh dấu thông báo.', 'error');

  }

}



// Navigation

function navigateTab(tabName, pushHistory = true) {

  // If not authenticated, cannot navigate

  if (!currentUser) {

    showLoginScreen();

    return;

  }



  const allowedTabs = getAllowedTabs();

  if (!allowedTabs.has(tabName)) {

    showToast('Tài khoản của bạn chưa được cấp quyền truy cập mục này.', 'error');

    return;

  }

  if (!document.getElementById(`tab-${tabName}`)) {

    showToast('Mục này hiện chưa được cấu hình.', 'warning');

    return;

  }



  activeTab = tabName;

  if (pushHistory && window.history && window.history.pushState) {
    const routeMap = {
      users: '/admin/users',
      profile: '/profile',
      'teacher-classes': '/teacher-classes',
      competition: '/competition',
      conduct: '/conduct',
      counseling: '/counseling',
      dashboard: '/dashboard'
    };
    history.pushState(null, '', routeMap[tabName] || '/dashboard');
  }



  document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));

  const targetPane = document.getElementById(`tab-${tabName}`);

  if (targetPane) targetPane.classList.remove('hidden');



  // Update nav buttons with modern EdTech active gradient styles

  document.querySelectorAll('.nav-item').forEach(el => {

    el.classList.remove('is-active', 'active', 'bg-brand-50', 'text-brand-900', 'border-brand-100');

  });

  const activeBtn = document.getElementById(`nav-btn-${tabName}`);

  if (activeBtn) {

    activeBtn.classList.add('is-active', 'active');

  }

  window.scrollTo({ top: 0, behavior: 'smooth' });

  document.querySelectorAll('[data-mobile-tab]').forEach(button => {

    button.classList.toggle('is-active', button.dataset.mobileTab === tabName);

  });

  if (typeof closeMobileDrawer === 'function') {

    closeMobileDrawer();

  }

  document.querySelectorAll('[data-mobile-drawer-tab]').forEach(btn => {

    btn.classList.toggle('is-active', btn.dataset.mobileDrawerTab === tabName);

  });



  // Load relevant tab data

  if (tabName === 'profile') renderProfile();

  else if (tabName === 'dashboard') { if (!_dashboardData.loaded) loadDashboard(); }

  else if (tabName === 'teacher-classes') loadTeacherClassesModule();

  else if (tabName === 'student-approvals') loadStudentApprovals();

  else if (tabName === 'red-star') loadRedStarAssignments();

  else if (tabName === 'sao-do-duty') loadSaoDoDuty();

  else if (tabName === 'doan-truong') loadDoanTruongManagement();

  else if (tabName === 'conduct') loadConductViolations();

  else if (tabName === 'competition') loadCompetitionScores();

  else if (tabName === 'alerts') loadEarlyAlerts();

  else if (tabName === 'counseling') loadCounselorInbox();

  else if (tabName === 'reports') loadReportsHistory();

  else if (tabName === 'users') loadUsersManagement();

  else if (tabName === 'teachers') loadTeachersManagement();

  else if (tabName === 'reflections') loadReflectionsData();

  else if (tabName === 'settings') {

    loadAuditLogs();

    loadEmailSettings();

  }



  lucide.createIcons();

}



// In-memory client cache cho metadata để tránh refetch lặp lại

let metadataCacheTimestamp = 0;

const METADATA_CLIENT_TTL_MS = 180000; // 3 phút



// Load metadata (classes, rules)

async function loadMetadata(force = false) {

  const now = Date.now();

  if (!force && classesCache.length > 0 && rulesCache.length > 0 && (now - metadataCacheTimestamp < METADATA_CLIENT_TTL_MS)) {

    return;

  }

  metadataCacheTimestamp = now;

  try {

    const classesPromise = fetch('/api/conduct/classes/?all=true');

    const rulesPromise = fetch('/api/conduct/rules/');

    const [classesRes, rulesRes] = await Promise.all([classesPromise, rulesPromise]);

    const classesData = await classesRes.json();
    classesCache = Array.isArray(classesData) ? classesData : (classesData.results || []);

    const rulesData = rulesRes ? await rulesRes.json() : [];
    rulesCache = Array.isArray(rulesData) ? rulesData : (rulesData.results || []);
    if (!Array.isArray(classesCache)) classesCache = [];
    if (!Array.isArray(rulesCache)) rulesCache = [];

    // Populate modal class dropdown & filter with natural sort
    if (typeof populateModalViolationClasses === 'function') {
      populateModalViolationClasses(document.getElementById('modal-violation-grade')?.value || '');
    }

    const filterClassSelect = document.getElementById('filter-conduct-class');
    if (filterClassSelect) {
      const sortedClasses = naturalSortClasses(classesCache);
      filterClassSelect.innerHTML = '<option value="">Tất cả các lớp</option>' +
        sortedClasses.map(c => `<option value="${c.id}">Lớp ${escapeHtml(c.name)} (Khối ${c.grade})</option>`).join('');
    }
    const studentApprovalClassSelect = document.getElementById('student-approval-class');
    if (studentApprovalClassSelect) {
      const sortedClasses = naturalSortClasses(classesCache);
      studentApprovalClassSelect.innerHTML = '<option value="">Tất cả lớp</option>' +
        sortedClasses.map(c => `<option value="${c.id}">Lớp ${escapeHtml(c.name)}</option>`).join('');
    }




    // Populate rules dropdown grouped by official categories

    const modalRuleSelect = document.getElementById('modal-violation-rule');

    if (modalRuleSelect) {

      modalRuleSelect.innerHTML = renderRuleOptionsGrouped(rulesCache, '-- Chọn lỗi vi phạm --', true);

    }

    populateRedStarClassSelects();

    populateSaoDoReportSelects();

  } catch (err) {

    console.error('Lỗi tải danh mục lớp và nội quy:', err);

  }

}



async function apiRequest(url, options = {}) {

  const headers = { ...(options.headers || {}) };

  if (options.body && !(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';

  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes((options.method || 'GET').toUpperCase())) headers['X-CSRFToken'] = getCookie('csrftoken');

  const response = await fetch(url, { credentials: 'same-origin', ...options, headers });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) throw new Error(data.error || data.detail || 'Không thể hoàn tất yêu cầu.');

  return data;

}



const fetchApi = apiRequest;

window.fetchApi = apiRequest;



function apiList(data) {

  if (Array.isArray(data)) return data;

  if (Array.isArray(data?.results)) return data.results;

  return [];

}



function displayDate(value) {

  if (!value) return '—';

  const date = new Date(value);

  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString('vi-VN');

}



async function loadStudentApprovals() {

  const list = document.getElementById('student-approval-list');

  const error = document.getElementById('student-approval-error');

  const summary = document.getElementById('student-approval-summary');

  if (!list) return;

  bindStudentApprovalFilters();

  if (!isAdminUser() && !['student_accounts.view', 'student_accounts.approve', 'student_accounts.reject'].some(permission => userHasPermission(permission))) {

    if (error) { error.textContent = 'Bạn chưa được cấp quyền xem yêu cầu đăng ký học sinh.'; error.hidden = false; }

    list.innerHTML = '';

    return;

  }

  if (error) error.hidden = true;

  list.setAttribute('aria-busy', 'true');

  list.innerHTML = '<div class="workspace-loading">Đang tải yêu cầu…</div>';



  const statusFilter = document.getElementById('student-approval-status')?.value || 'PENDING';

  const gradeFilter = document.getElementById('student-approval-grade')?.value || '';

  const classFilter = document.getElementById('student-approval-class')?.value || '';

  const search = document.getElementById('student-approval-search')?.value.trim() || '';



  const query = new URLSearchParams();

  if (statusFilter && statusFilter !== 'ALL') query.set('status', statusFilter);

  if (gradeFilter) query.set('grade', gradeFilter);

  if (classFilter) query.set('school_class', classFilter);

  if (search) query.set('search', search);



  try {

    const [data, stats] = await Promise.all([

      apiRequest(`/api/core/student-approvals/?${query.toString()}`),

      apiRequest('/api/core/student-approvals/stats/').catch(() => null),

    ]);

    const accounts = apiList(data);



    if (stats) {

      const pEl = document.getElementById('stat-student-pending');

      if (pEl) pEl.textContent = stats.pending ?? 0;

      const aEl = document.getElementById('stat-student-approved');

      if (aEl) aEl.textContent = stats.approved ?? 0;

      const rEl = document.getElementById('stat-student-rejected');

      if (rEl) rEl.textContent = stats.rejected ?? 0;

      const tEl = document.getElementById('stat-student-total');

      if (tEl) tEl.textContent = stats.total ?? 0;

    }



    if (summary) summary.textContent = stats ? `${stats.pending} yêu cầu đang chờ · ${accounts.length} mục trong kết quả lọc` : `${accounts.length} mục trong kết quả lọc`;

    const badge = document.getElementById('sidebar-student-approval-badge');

    if (badge && stats?.pending > 0) { badge.textContent = stats.pending > 99 ? '99+' : stats.pending; badge.classList.remove('hidden'); }

    else if (badge) badge.classList.add('hidden');



    const selectAllCheckbox = document.getElementById('student-approval-select-all');

    if (selectAllCheckbox) selectAllCheckbox.checked = false;



    if (!accounts.length) {

      list.innerHTML = '<div class="workspace-empty">Không có yêu cầu nào phù hợp với bộ lọc.</div>';

      updateBulkActionButtons();

      return;

    }



    const canApprove = isAdminUser() || userHasPermission('student_accounts.approve');

    const canReject = isAdminUser() || userHasPermission('student_accounts.reject');



    list.innerHTML = accounts.map(account => {

      const statusCode = String(account.account_status || '').toLowerCase();

      const statusClass = statusCode === 'approved' ? 'approved' : statusCode === 'rejected' ? 'rejected' : statusCode === 'pending' ? 'pending' : '';

      const checkboxHtml = `<input type="checkbox" class="student-approval-checkbox rounded border-slate-300 text-brand-600 focus:ring-brand-500 mr-2" value="${Number(account.id)}" onchange="updateBulkActionButtons()">`;



      const actions = account.account_status !== 'APPROVED' && (canApprove || (canReject && account.account_status === 'PENDING'))

        ? `<div class="workspace-record-actions">${canApprove ? `<button type="button" class="hk-button hk-button-primary" onclick="approveStudentAccount(${Number(account.id)})">Duyệt</button>` : ''}${canReject && account.account_status === 'PENDING' ? `<button type="button" class="hk-button hk-button-secondary text-rose-600 border-rose-200" onclick="openRejectStudentModal(${Number(account.id)}, '${escapeHtml(account.full_name || account.username)}')">Từ chối</button>` : ''}</div>` : '';



      let extra = '';

      if (account.rejection_reason) {

        extra += `<br><span class="text-rose-600 font-medium">Lý do từ chối: ${escapeHtml(account.rejection_reason)}</span>`;

        if (account.rejected_by_name) extra += ` <span class="text-slate-400">(${escapeHtml(account.rejected_by_name)})</span>`;

      }

      if (account.approved_by_name) {

        extra += `<br><span class="text-emerald-700">Người duyệt: ${escapeHtml(account.approved_by_name)}</span>`;

      }



      return `<article class="workspace-record flex items-start gap-3"><div class="pt-1">${checkboxHtml}</div><div class="workspace-record-main flex-1"><h2 class="workspace-record-title">${escapeHtml(account.full_name || account.username)}</h2><p class="workspace-record-meta">${escapeHtml(account.email || 'Chưa có email')} · ${escapeHtml(account.school_class_name || account.department_or_class || 'Chưa có lớp')} · Khối ${escapeHtml(account.grade_level || '—')} · Mã ${escapeHtml(account.student_code || '—')}<br>Gửi ngày ${escapeHtml(displayDate(account.date_joined))}${extra}</p></div><div class="workspace-record-actions"><span class="workspace-status ${statusClass}">${escapeHtml(account.account_status_display || account.account_status || '')}</span>${actions}</div></article>`;

    }).join('');



    updateBulkActionButtons();

  } catch (err) {

    list.innerHTML = '';

    if (error) { error.textContent = err.message || 'Không thể tải danh sách đăng ký.'; error.hidden = false; }

  } finally {

    list.setAttribute('aria-busy', 'false');

  }

}



function toggleSelectAllStudents(master) {

  const checkboxes = document.querySelectorAll('.student-approval-checkbox');

  checkboxes.forEach(cb => { cb.checked = master.checked; });

  updateBulkActionButtons();

}



function updateBulkActionButtons() {

  const checked = document.querySelectorAll('.student-approval-checkbox:checked');

  const count = checked.length;

  const bulkApproveBtn = document.getElementById('student-approval-bulk-approve');

  const bulkRejectBtn = document.getElementById('student-approval-bulk-reject');

  if (bulkApproveBtn) {

    bulkApproveBtn.disabled = count === 0;

    bulkApproveBtn.innerHTML = `<i data-lucide="check" class="w-3.5 h-3.5"></i><span>Duyệt đã chọn (${count})</span>`;

  }

  if (bulkRejectBtn) {

    bulkRejectBtn.disabled = count === 0;

    bulkRejectBtn.innerHTML = `<i data-lucide="x" class="w-3.5 h-3.5"></i><span>Từ chối đã chọn (${count})</span>`;

  }

  if (window.lucide && lucide.createIcons) lucide.createIcons();

}



async function bulkApproveStudents() {

  const checked = Array.from(document.querySelectorAll('.student-approval-checkbox:checked')).map(cb => Number(cb.value));

  if (!checked.length) return showToast('Vui lòng chọn ít nhất một học sinh.', 'warning');

  if (!isAdminUser() && !userHasPermission('student_accounts.approve')) return showToast('Bạn chưa được cấp quyền duyệt tài khoản.', 'error');

  if (!window.confirm(`Xác nhận duyệt ${checked.length} tài khoản học sinh đã chọn?`)) return;

  try {

    const data = await apiRequest('/api/core/student-approvals/bulk-approve/', {

      method: 'POST',

      body: JSON.stringify({ user_ids: checked })

    });

    showToast(data.message || 'Đã duyệt các tài khoản thành công.', 'success');

    await loadStudentApprovals();

  } catch (err) {

    showToast(err.message, 'error');

  }

}



function openRejectStudentModal(id, studentName) {

  document.getElementById('reject-student-id').value = id;

  document.getElementById('reject-student-is-bulk').value = 'false';

  document.getElementById('reject-student-reason').value = '';

  document.getElementById('reject-student-target-info').textContent = `Từ chối tài khoản học sinh: ${studentName || id}`;

  document.getElementById('modal-reject-student').classList.remove('hidden');

}



function openBulkRejectModal() {

  const checked = Array.from(document.querySelectorAll('.student-approval-checkbox:checked')).map(cb => Number(cb.value));

  if (!checked.length) return showToast('Vui lòng chọn ít nhất một học sinh.', 'warning');

  document.getElementById('reject-student-id').value = '';

  document.getElementById('reject-student-is-bulk').value = 'true';

  document.getElementById('reject-student-reason').value = '';

  document.getElementById('reject-student-target-info').textContent = `Từ chối ${checked.length} tài khoản học sinh đã chọn.`;

  document.getElementById('modal-reject-student').classList.remove('hidden');

}



function closeRejectStudentModal() {

  document.getElementById('modal-reject-student').classList.add('hidden');

}



async function handleRejectStudentSubmit(event) {

  event.preventDefault();

  const reason = document.getElementById('reject-student-reason').value.trim();

  if (!reason) return showToast('Bắt buộc phải nhập lý do từ chối.', 'warning');

  const isBulk = document.getElementById('reject-student-is-bulk').value === 'true';

  const submitBtn = document.getElementById('reject-student-submit-btn');

  submitBtn.disabled = true;

  try {

    if (isBulk) {

      const checked = Array.from(document.querySelectorAll('.student-approval-checkbox:checked')).map(cb => Number(cb.value));

      const res = await apiRequest('/api/core/student-approvals/bulk-reject/', {

        method: 'POST',

        body: JSON.stringify({ user_ids: checked, reason })

      });

      showToast(res.message || 'Đã từ chối các tài khoản đã chọn.', 'success');

    } else {

      const userId = Number(document.getElementById('reject-student-id').value);

      const res = await apiRequest(`/api/core/student-approvals/${userId}/reject/`, {

        method: 'POST',

        body: JSON.stringify({ reason })

      });

      showToast(res.message || 'Đã từ chối tài khoản học sinh.', 'success');

    }

    closeRejectStudentModal();

    await loadStudentApprovals();

  } catch (err) {

    showToast(err.message, 'error');

  } finally {

    submitBtn.disabled = false;

  }

}



async function approveStudentAccount(userId) {

  if (!isAdminUser() && !userHasPermission('student_accounts.approve')) return showToast('Bạn chưa được cấp quyền duyệt tài khoản.', 'error');

  if (!window.confirm('Duyệt tài khoản học sinh này?')) return;

  try {

    const data = await apiRequest(`/api/core/student-approvals/${userId}/approve/`, { method: 'POST', body: JSON.stringify({}) });

    showToast(data.message || 'Đã duyệt tài khoản.', 'success');

    await loadStudentApprovals();

  } catch (err) { showToast(err.message, 'error'); }

}



async function rejectStudentAccount(userId) {

  openRejectStudentModal(userId, `ID #${userId}`);

}



function bindStudentApprovalFilters() {

  const search = document.getElementById('student-approval-search');

  const status = document.getElementById('student-approval-status');

  const grade = document.getElementById('student-approval-grade');

  const sclass = document.getElementById('student-approval-class');

  if (search && !search.dataset.bound) {

    search.dataset.bound = 'true';

    search.addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); loadStudentApprovals(); } });

  }

  if (status && !status.dataset.bound) { status.dataset.bound = 'true'; status.addEventListener('change', loadStudentApprovals); }

  if (grade && !grade.dataset.bound) { grade.dataset.bound = 'true'; grade.addEventListener('change', loadStudentApprovals); }

  if (sclass && !sclass.dataset.bound) { sclass.dataset.bound = 'true'; sclass.addEventListener('change', loadStudentApprovals); }

}



function populateRedStarClassSelects() {

  const classSelect = document.getElementById('assignment-class');

  if (classSelect) {

    classSelect.innerHTML = '<option value="">Chọn lớp</option>' + classesCache.map(item => `<option value="${Number(item.id)}">${escapeHtml(item.name)} · Khối ${escapeHtml(item.grade)}</option>`).join('');

  }

  const classesContainer = document.getElementById('assignment-classes');

  if (classesContainer) {

    classesContainer.innerHTML = classesCache.map(item => `<label><input type="checkbox" value="${Number(item.id)}"> ${escapeHtml(item.name)} · Khối ${escapeHtml(item.grade)}</label>`).join('');

    if (!classesCache.length) classesContainer.innerHTML = '<p class="workspace-empty">Chưa có lớp đang hoạt động.</p>';

  }

}



function initRedStarAssignmentForm() {

  const form = document.getElementById('red-star-assignment-form');

  if (!form || form.dataset.bound) return;

  form.dataset.bound = 'true';

  const scope = document.getElementById('assignment-scope-type');

  const classField = document.getElementById('assignment-class-field');

  const classesField = document.getElementById('assignment-classes-field');

  const gradeField = document.getElementById('assignment-grade-field');

  const areaField = document.getElementById('assignment-area-field');

  const syncScope = () => {

    const value = scope.value;

    classField.hidden = value !== 'CLASS';

    classesField.hidden = value !== 'MULTI_CLASS';

    gradeField.hidden = value !== 'GRADE';

    areaField.hidden = value !== 'AREA';

    document.getElementById('assignment-class').required = value === 'CLASS';

    document.getElementById('assignment-grade').required = value === 'GRADE';

    document.getElementById('assignment-area').required = value === 'AREA';

  };

  scope.addEventListener('change', syncScope);

  syncScope();

  const start = document.getElementById('assignment-start-date');

  if (start && !start.value) start.value = new Date().toLocaleDateString('en-CA');

  const search = document.getElementById('red-star-candidate-search');

  if (search && !search.dataset.bound) {

    search.dataset.bound = 'true';

    let searchTimer = null;

    search.addEventListener('input', () => {

      clearTimeout(searchTimer);

      searchTimer = setTimeout(loadRedStarCandidates, 250);

    });

  }

  form.addEventListener('submit', async event => {

    event.preventDefault();

    if (!form.reportValidity()) return;

    if (!isAdminUser() && !userHasPermission('red_star.assign')) return showToast('Bạn chưa được cấp quyền phân công Sao đỏ.', 'error');

    const type = scope.value;

    const selectedClasses = Array.from(document.querySelectorAll('#assignment-classes input:checked')).map(input => Number(input.value));

    if (type === 'MULTI_CLASS' && !selectedClasses.length) return showToast('Hãy chọn ít nhất một lớp phụ trách.', 'warning');

    const payload = {

      student_id: Number(document.getElementById('red-star-candidate').value),

      scope_type: type,

      start_date: start.value,

      end_date: document.getElementById('assignment-end-date').value || null,

      notes: document.getElementById('assignment-notes').value.trim(),

    };

    if (type === 'CLASS') payload.assigned_class = Number(document.getElementById('assignment-class').value);

    if (type === 'MULTI_CLASS') payload.assigned_class_ids = selectedClasses;

    if (type === 'GRADE') payload.assigned_grade = Number(document.getElementById('assignment-grade').value);

    if (type === 'AREA') payload.area_name = document.getElementById('assignment-area').value.trim();

    const button = document.getElementById('red-star-assignment-submit');

    button.disabled = true;

    try {

      const result = await apiRequest('/api/conduct/red-star/', { method: 'POST', body: JSON.stringify(payload) });

      showToast(result.message || 'Đã lưu phân công.', 'success');

      const message = document.getElementById('red-star-assignment-message');

      message.textContent = result.message || 'Phân công đã được lưu.';

      message.hidden = false;

      form.reset();

      const candidateSearch = document.getElementById('red-star-candidate-search');

      if (candidateSearch) candidateSearch.value = '';

      start.value = new Date().toLocaleDateString('en-CA');

      syncScope();

      await loadRedStarAssignments();

    } catch (err) { showToast(err.message, 'error'); }

    finally { button.disabled = false; }

  });

}



async function loadRedStarCandidates() {

  const select = document.getElementById('red-star-candidate');

  if (!select) return;

  select.innerHTML = '<option value="">Đang tải học sinh…</option>';

  try {

    const query = new URLSearchParams({ red_star_candidates: 'true' });

    const search = document.getElementById('red-star-candidate-search')?.value.trim();

    if (search) query.set('search', search);

    const students = apiList(await apiRequest(`/api/conduct/students/?${query.toString()}`));

    select.innerHTML = '<option value="">Chọn học sinh đã duyệt</option>' + students.map(student => `<option value="${Number(student.id)}">${escapeHtml(student.full_name)} · ${escapeHtml(student.class_name || 'Chưa có lớp')} · ${escapeHtml(student.student_code || '')}</option>`).join('');

    if (!students.length) select.innerHTML = '<option value="">Chưa có học sinh đủ điều kiện</option>';

  } catch (err) { select.innerHTML = '<option value="">Không tải được danh sách học sinh</option>'; }

}



async function loadRedStarAssignments() {

  const list = document.getElementById('red-star-assignment-list');

  const error = document.getElementById('red-star-assignment-error');

  if (!list) return;

  const canView = isAdminUser() || userHasPermission('red_star.view') || userHasPermission('red_star.revoke');

  const canAssign = isAdminUser() || userHasPermission('red_star.assign');

  const canRevoke = isAdminUser() || userHasPermission('red_star.revoke');

  const panel = document.getElementById('red-star-assignment-panel');

  if (panel) panel.hidden = !canAssign;

  initRedStarAssignmentForm();

  populateRedStarClassSelects();

  if (!canView && !canAssign) {

    if (error) { error.textContent = 'Bạn chưa được cấp quyền quản lý phân công Sao đỏ.'; error.hidden = false; }

    list.innerHTML = '';

    return;

  }

  list.setAttribute('aria-busy', 'true');

  if (error) error.hidden = true;

  list.innerHTML = '<div class="workspace-loading">Đang tải phân công…</div>';

  const candidatesPromise = canAssign ? loadRedStarCandidates() : Promise.resolve();

  try {

    const records = canView ? apiList(await apiRequest('/api/conduct/red-star/')) : [];

    await candidatesPromise;

    if (!canView) {

      list.innerHTML = '<div class="workspace-empty">Bạn có quyền phân công hoặc thu hồi Sao đỏ. Quyền xem danh sách chưa được cấp.</div>';

      return;

    }

    if (!records.length) {

      list.innerHTML = '<div class="workspace-empty">Chưa có phân công nào phù hợp.</div>';

      return;

    }

    list.innerHTML = records.map(record => {

      const status = String(record.status || '').toLowerCase();

      let actionButtons = '';

      if (record.status === 'ACTIVE') {

        if (canRevoke) {

          actionButtons += `<button type="button" class="hk-button hk-button-secondary text-amber-700 bg-amber-50 mr-1" onclick="suspendRedStarAssignment(${Number(record.id)})">Tạm ngưng</button>`;

          actionButtons += `<button type="button" class="hk-button hk-button-secondary text-rose-700 bg-rose-50" onclick="revokeRedStarAssignment(${Number(record.id)})">Thu hồi</button>`;

        }

      } else if (record.status === 'SUSPENDED') {

        if (canAssign) {

          actionButtons += `<button type="button" class="hk-button hk-button-primary bg-emerald-600 mr-1" onclick="reactivateRedStarAssignment(${Number(record.id)})">Kích hoạt lại</button>`;

        }

        if (canRevoke) {

          actionButtons += `<button type="button" class="hk-button hk-button-secondary text-rose-700 bg-rose-50" onclick="revokeRedStarAssignment(${Number(record.id)})">Thu hồi</button>`;

        }

      }

      return `<article class="workspace-record"><div class="workspace-record-main"><h2 class="workspace-record-title">${escapeHtml(record.student_name || record.student_username || 'Học sinh')}</h2><p class="workspace-record-meta">${escapeHtml(record.student_code || 'Chưa có mã')} · Lớp ${escapeHtml(record.home_class_name || 'Chưa liên kết')}<br>${escapeHtml(record.scope_display || 'Chưa có phạm vi')} · Từ ${escapeHtml(displayDate(record.start_date))}${record.end_date ? ` đến ${escapeHtml(displayDate(record.end_date))}` : ''}${record.assigned_by_name ? ` · Phân công bởi ${escapeHtml(record.assigned_by_name)}` : ''}</p></div><div class="workspace-record-actions"><span class="workspace-status ${status === 'active' ? 'active' : status === 'suspended' ? 'pending' : status === 'revoked' ? 'revoked' : ''}">${escapeHtml(record.status_display || record.status || '')}</span>${actionButtons}</div></article>`;

    }).join('');

  } catch (err) {

    await candidatesPromise;

    list.innerHTML = canAssign ? '<div class="workspace-empty">Không tải được danh sách phân công. Bạn vẫn có thể gửi phân công mới nếu được cấp quyền.</div>' : '';

    if (error) { error.textContent = err.message || 'Không thể tải phân công Sao đỏ.'; error.hidden = false; }

  } finally {

    list.setAttribute('aria-busy', 'false');

  }

}



async function suspendRedStarAssignment(assignmentId) {

  if (!isAdminUser() && !userHasPermission('red_star.revoke')) return showToast('Bạn chưa được cấp quyền tạm ngưng phân công.', 'error');

  if (!window.confirm('Tạm ngưng phân công Sao đỏ này?')) return;

  try {

    const result = await apiRequest(`/api/conduct/red-star/${assignmentId}/suspend/`, { method: 'POST', body: JSON.stringify({}) });

    showToast(result.message || 'Đã tạm ngưng phân công.', 'success');

    await loadRedStarAssignments();

  } catch (err) { showToast(err.message, 'error'); }

}



async function reactivateRedStarAssignment(assignmentId) {

  if (!isAdminUser() && !userHasPermission('red_star.assign')) return showToast('Bạn chưa được cấp quyền kích hoạt lại phân công.', 'error');

  if (!window.confirm('Kích hoạt lại phân công Sao đỏ này?')) return;

  try {

    const result = await apiRequest(`/api/conduct/red-star/${assignmentId}/reactivate/`, { method: 'POST', body: JSON.stringify({}) });

    showToast(result.message || 'Đã kích hoạt lại phân công.', 'success');

    await loadRedStarAssignments();

  } catch (err) { showToast(err.message, 'error'); }

}



async function revokeRedStarAssignment(assignmentId) {

  if (!isAdminUser() && !userHasPermission('red_star.revoke')) return showToast('Bạn chưa được cấp quyền thu hồi phân công.', 'error');

  if (!window.confirm('Thu hồi phân công Sao đỏ này?')) return;

  const reason = window.prompt('Lý do thu hồi (không bắt buộc):') || '';

  try {

    const result = await apiRequest(`/api/conduct/red-star/${assignmentId}/revoke/`, { method: 'POST', body: JSON.stringify({ reason: reason.trim() }) });

    showToast(result.message || 'Đã thu hồi phân công.', 'success');

    await loadRedStarAssignments();

  } catch (err) { showToast(err.message, 'error'); }

}



const DOAN_REVOKE_ROLE_OPTIONS = [

  ['HOC_SINH', 'Học sinh'],

  ['GVCN', 'Giáo viên chủ nhiệm'],

  ['GVBM', 'Giáo viên bộ môn'],

  ['CHUYEN_VIEN_TAM_LY', 'Chuyên viên tư vấn tâm lý'],

];



function initDoanMemberForm() {

  const form = document.getElementById('doan-member-form');

  if (!form || form.dataset.bound) return;

  form.dataset.bound = 'true';

  form.addEventListener('submit', async event => {

    event.preventDefault();

    if (!isAdminUser()) return showToast('Chỉ Admin mới được quản lý quyền Đoàn trường.', 'error');

    const username = document.getElementById('doan-member-username').value.trim();

    const permissions = Array.from(document.querySelectorAll('#doan-permission-options input:checked')).map(input => input.value);

    const button = document.getElementById('doan-member-submit');

    button.disabled = true;

    try {

      const result = await apiRequest('/api/core/doan-truong/', {

        method: 'POST',

        body: JSON.stringify({ username, permissions }),

      });

      const message = document.getElementById('doan-member-message');

      message.textContent = result.message || 'Đã bổ nhiệm cán bộ Đoàn trường.';

      message.hidden = false;

      form.reset();

      showToast(message.textContent, 'success');

      await loadDoanTruongManagement();

    } catch (err) { showToast(err.message, 'error'); }

    finally { button.disabled = false; }

  });

}



async function loadDoanTruongManagement() {

  const list = document.getElementById('doan-members-list');

  const error = document.getElementById('doan-management-error');

  if (!list) return;

  const isDoanOrAdmin = isAdminUser() || currentUser.is_doan_truong || currentUser.role === 'DOAN_TRUONG';

  if (!isDoanOrAdmin) {

    list.innerHTML = '';

    if (error) { error.textContent = 'Chỉ Quản trị viên hệ thống hoặc Đoàn trường mới có quyền truy cập.'; error.hidden = false; }

    return;

  }

  const formCard = document.getElementById('doan-member-form');

  if (formCard) {

    formCard.closest('section')?.classList.toggle('hidden', !isAdminUser());

  }

  initDoanMemberForm();

  list.setAttribute('aria-busy', 'true');

  list.innerHTML = '<div class="workspace-loading">Đang tải danh sách cán bộ…</div>';

  if (error) error.hidden = true;

  try {

    const [membersData, permissionsData] = await Promise.all([

      apiRequest('/api/core/doan-truong/'),

      apiRequest('/api/core/doan-truong/available-permissions/'),

    ]);

    const members = apiList(membersData);

    const permissionCatalog = apiList(permissionsData.permissions);

    if (!members.length) {

      list.innerHTML = '<div class="workspace-empty">Chưa có cán bộ Đoàn trường được bổ nhiệm.</div>';

      return;

    }

    list.innerHTML = members.map(member => {

      const memberPermissions = Array.isArray(member.permissions) ? member.permissions : [];

      const roleOptions = DOAN_REVOKE_ROLE_OPTIONS.map(([value, label]) => `<option value="${value}">${label}</option>`).join('');

      const checkboxes = permissionCatalog.map(permission => `<label><input type="checkbox" data-permission="${escapeHtml(permission.code)}" ${memberPermissions.includes(permission.code) ? 'checked' : ''}> ${escapeHtml(permission.name)}</label>`).join('');

      return `<article class="workspace-record doan-member-card" data-member-id="${Number(member.id)}"><div class="workspace-record-main"><h2 class="workspace-record-title">${escapeHtml(member.full_name || member.username)}</h2><p class="workspace-record-meta">@${escapeHtml(member.username)} · ${escapeHtml(member.email || 'Chưa có email')} · ${escapeHtml(member.role_display || '')}</p><div class="workspace-permission-grid">${checkboxes}</div></div><div class="workspace-record-actions"><button type="button" class="hk-button hk-button-primary" onclick="saveDoanMemberPermissions(${Number(member.id)})">Lưu quyền</button><label class="workspace-field"><span>Vai trò khi thu hồi</span><select data-revoke-role>${roleOptions}</select></label><button type="button" class="hk-button hk-button-secondary" onclick="revokeDoanMember(${Number(member.id)})">Thu hồi vai trò</button></div></article>`;

    }).join('');

  } catch (err) {

    list.innerHTML = '';

    if (error) { error.textContent = err.message || 'Không thể tải danh sách cán bộ Đoàn trường.'; error.hidden = false; }

  } finally { list.setAttribute('aria-busy', 'false'); }

}



async function saveDoanMemberPermissions(memberId) {

  if (!isAdminUser()) return showToast('Chỉ Admin mới được cập nhật quyền.', 'error');

  const card = document.querySelector(`.doan-member-card[data-member-id="${Number(memberId)}"]`);

  if (!card) return;

  const permissions = Array.from(card.querySelectorAll('[data-permission]:checked')).map(input => input.dataset.permission);

  try {

    const result = await apiRequest(`/api/core/doan-truong/${Number(memberId)}/permissions/`, {

      method: 'POST', body: JSON.stringify({ permissions }),

    });

    showToast(result.message || 'Đã cập nhật quyền.', 'success');

    await loadDoanTruongManagement();

  } catch (err) { showToast(err.message, 'error'); }

}



async function revokeDoanMember(memberId) {

  if (!isAdminUser()) return showToast('Chỉ Admin mới được thu hồi vai trò.', 'error');

  const card = document.querySelector(`.doan-member-card[data-member-id="${Number(memberId)}"]`);

  const targetRole = card?.querySelector('[data-revoke-role]')?.value || 'HOC_SINH';

  if (!window.confirm('Thu hồi vai trò Đoàn trường và chuyển tài khoản về vai trò đã chọn?')) return;

  try {

    const result = await apiRequest(`/api/core/doan-truong/${Number(memberId)}/revoke/`, {

      method: 'POST', body: JSON.stringify({ target_role: targetRole }),

    });

    showToast(result.message || 'Đã thu hồi vai trò.', 'success');

    await loadDoanTruongManagement();

  } catch (err) { showToast(err.message, 'error'); }

}



function populateSaoDoReportSelects() {

  const classSelect = document.getElementById('sao-do-report-class');

  const ruleSelect = document.getElementById('sao-do-report-rule');

  if (classSelect) {

    classSelect.innerHTML = '<option value="">Chọn lớp</option>' + classesCache.map(item => `<option value="${Number(item.id)}">${escapeHtml(item.name)} · Khối ${escapeHtml(item.grade)}</option>`).join('');

    if (!classSelect.dataset.bound) {

      classSelect.dataset.bound = 'true';

      classSelect.addEventListener('change', loadSaoDoReportStudents);

    }

  }

  if (ruleSelect) {

    ruleSelect.innerHTML = renderRuleOptionsGrouped(rulesCache, 'Chọn nội quy nếu phù hợp', true);

  }

  const form = document.getElementById('sao-do-report-form');

  if (form && !form.dataset.bound) {

    form.dataset.bound = 'true';

    form.addEventListener('submit', submitSaoDoReport);

  }

  const timeInput = document.getElementById('sao-do-report-time');

  if (timeInput && !timeInput.value) timeInput.value = getLocalIsoString();

}



async function loadSaoDoReportStudents() {

  const classId = document.getElementById('sao-do-report-class')?.value;

  const select = document.getElementById('sao-do-report-student');

  if (!select) return;

  if (!classId) { select.innerHTML = '<option value="">Chọn lớp trước</option>'; return; }

  select.innerHTML = '<option value="">Đang tải học sinh…</option>';

  try {

    const query = new URLSearchParams({ class_id: classId });

    const students = apiList(await apiRequest(`/api/conduct/students/?${query.toString()}`));

    select.innerHTML = '<option value="">Không chọn học sinh</option>' + students.map(student => `<option value="${Number(student.id)}">${escapeHtml(student.full_name)} · ${escapeHtml(student.student_code || '')}</option>`).join('');

  } catch (err) {

    select.innerHTML = '<option value="">Không tải được danh sách học sinh</option>';

  }

}



async function submitSaoDoReport(event) {

  event.preventDefault();

  const form = event.currentTarget;

  if (!currentUser?.is_active_red_star) return showToast('Nhiệm vụ Sao đỏ đang hoạt động mới được gửi báo cáo.', 'error');

  if (!form.reportValidity()) return;

  const formData = new FormData();

  formData.append('school_class', document.getElementById('sao-do-report-class').value);

  const studentId = document.getElementById('sao-do-report-student').value;

  const ruleId = document.getElementById('sao-do-report-rule').value;

  if (studentId) formData.append('student', studentId);

  if (ruleId) formData.append('rule', ruleId);

  formData.append('incident_time', document.getElementById('sao-do-report-time').value);

  formData.append('location', document.getElementById('sao-do-report-location').value.trim());

  formData.append('description', document.getElementById('sao-do-report-description').value.trim());

  if (ruleId) {

    const rule = rulesCache.find(item => String(item.id) === String(ruleId));

    if (rule) formData.append('incident_type', rule.name);

  }

  const file = document.getElementById('sao-do-report-evidence').files?.[0];

  if (file) formData.append('evidence_image', file);

  const button = document.getElementById('sao-do-report-submit');

  button.disabled = true;

  try {

    const result = await apiRequest('/api/conduct/red-star-reports/', { method: 'POST', body: formData });

    const message = document.getElementById('sao-do-report-message');

    message.textContent = result.message || 'Báo cáo đã được gửi.';

    message.hidden = false;

    showToast(result.message || 'Đã gửi báo cáo.', 'success');

    form.reset();

    document.getElementById('sao-do-report-class').value = '';

    document.getElementById('sao-do-report-student').innerHTML = '<option value="">Chọn lớp trước</option>';

    document.getElementById('sao-do-report-time').value = getLocalIsoString();

    await loadSaoDoDuty();

  } catch (err) {

    showToast(err.message, 'error');

  } finally { button.disabled = false; }

}



async function loadSaoDoDuty() {

  const list = document.getElementById('sao-do-duty-list');

  const reportList = document.getElementById('my-red-star-report-list');

  const error = document.getElementById('sao-do-duty-error');

  if (!list || !currentUser) return;

  if (!currentUser.is_active_red_star) {

    if (error) { error.textContent = 'Tài khoản chưa có nhiệm vụ Sao đỏ đang hoạt động.'; error.hidden = false; }

    list.innerHTML = '<div class="workspace-empty">Chưa có nhiệm vụ đang hoạt động.</div>';

    document.getElementById('sao-do-report-panel')?.classList.add('hidden');

    return;

  }

  if (error) error.hidden = true;

  list.setAttribute('aria-busy', 'true');

  list.innerHTML = '<div class="workspace-loading">Đang tải nhiệm vụ…</div>';

  document.getElementById('sao-do-report-panel')?.classList.remove('hidden');

  try {

    const [dutyData, reportsData] = await Promise.all([

      apiRequest('/api/conduct/red-star/my-duty/'),

      apiRequest('/api/conduct/red-star-reports/'),

    ]);

    const assignments = apiList(dutyData.active_assignments);

    list.innerHTML = assignments.length ? assignments.map(item => `<article class="workspace-record"><div class="workspace-record-main"><h2 class="workspace-record-title">${escapeHtml(item.scope_display || 'Nhiệm vụ Sao đỏ')}</h2><p class="workspace-record-meta">Bắt đầu ${escapeHtml(displayDate(item.start_date))}${item.end_date ? ` · Kết thúc ${escapeHtml(displayDate(item.end_date))}` : ''}${item.area_name ? ` · ${escapeHtml(item.area_name)}` : ''}${item.notes ? `<br>${escapeHtml(item.notes)}` : ''}</p></div><span class="workspace-status active">${escapeHtml(item.status_display || 'Đang hoạt động')}</span></article>`).join('') : '<div class="workspace-empty">Không có nhiệm vụ đang hoạt động.</div>';

    const reports = apiList(reportsData);

    if (reportList) reportList.innerHTML = reports.length ? reports.slice(0, 10).map(report => {

      const state = String(report.status || '').toLowerCase();

      const stateClass = state === 'pending' ? 'pending' : state === 'verified' || state === 'resolved' ? 'approved' : state === 'rejected' ? 'rejected' : '';

      return `<article class="workspace-record"><div class="workspace-record-main"><h3 class="workspace-record-title">${escapeHtml(report.report_code || report.incident_type || 'Báo cáo nền nếp')}</h3><p class="workspace-record-meta">${escapeHtml(report.class_name || '—')} · ${escapeHtml(report.student_name_snapshot || 'Chưa xác định học sinh')} · ${escapeHtml(displayDate(report.incident_time))}${report.review_note ? `<br>Ý kiến xử lý: ${escapeHtml(report.review_note)}` : ''}</p></div><span class="workspace-status ${stateClass}">${escapeHtml(report.status_display || report.status || '')}</span></article>`;

    }).join('') : '<div class="workspace-empty">Bạn chưa gửi báo cáo nào.</div>';

    populateSaoDoReportSelects();

  } catch (err) {

    list.innerHTML = '';

    if (error) { error.textContent = err.message || 'Không tải được nhiệm vụ Sao đỏ.'; error.hidden = false; }

  } finally { list.setAttribute('aria-busy', 'false'); }

}



// ==========================================

// 1. DASHBOARD MODULE 2.0 (HIGH-CONTRAST & CRISP EDTECH)

// =====================================================================

const _hkCharts = {

  weeklyTrend: null,

  classComparison: null,

};



let _dashboardData = {

  stats: null,

  snapshot: null,

  weeksList: [],          // Danh sách 35 tuần (Tuần 1 đến 35)

  semestersList: [],      // Danh sách Học kỳ (Kỳ 1 và Kỳ 2)

  timeframeMode: 'week',  // 'week' | 'semester'

  selectedWeekNum: 7,     // 1 .. 35

  selectedSemNum: 1,      // 1 | 2

  selectedPeriodId: null,

  classesWithScores: [],  // Danh sách các lớp kèm điểm kỳ đang chọn

  selectedGrade: 'ALL',

  selectedTab: 'leaderboard', // 'leaderboard' | 'analytics' | 'activity'

  searchTerm: '',

  loaded: false,

  refreshing: false,

  scoresCache: {},        // Cache điểm thi đua theo kỳ { [periodId]: [...] }

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

let _dashSearchTimer = null;
function onDashboardSearch(keyword) {
  clearTimeout(_dashSearchTimer);
  _dashSearchTimer = setTimeout(() => {
    _dashboardData.searchTerm = (keyword || '').toLowerCase().trim();
    if (_dashboardData.snapshot && _dashboardData.snapshot.classes) {
      renderDashboardTable(_dashboardData.snapshot.classes, _dashboardData.selectedGrade, _dashboardData.selectedPeriod, _dashboardData.searchTerm);
    }
  }, 180);
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



  // Cập nhật nhãn phân định rõ Tuần vs Học kỳ

  const weekP = _dashboardData.snapshot?.periods?.WEEK;

  const semP = _dashboardData.snapshot?.periods?.SEMESTER;

  const weekNum = weekP?.week_number || _dashboardData.stats?.current_week_number || 7;

  const semNum = weekP?.semester_number || semP?.semester_number || _dashboardData.stats?.current_semester_number || 1;

  const semRoman = semNum === 1 ? 'I' : 'II';

  const isWeek = periodKey === 'week';



  const titleEl = document.getElementById('dashboard-podium-title');

  if (titleEl) {

    titleEl.innerHTML = `

      <i data-lucide="crown" class="w-5 h-5 text-amber-500"></i>

      Bục Vinh Danh Top 3 Chi Đoàn · ${isWeek ? `Theo Tuần (Tuần ${weekNum})` : `Theo Học Kỳ (Học kỳ ${semRoman})`}

    `;

  }

  const subEl = document.getElementById('dashboard-podium-sub');

  if (subEl) {

    subEl.textContent = isWeek

      ? `Vinh danh 3 Chi đoàn dẫn đầu điểm thi đua nề nếp trong Tuần ${weekNum} (Học kỳ ${semRoman})`

      : `Vinh danh 3 Chi đoàn dẫn đầu điểm thi đua tích lũy toàn diện cả Học kỳ ${semRoman}`;

  }



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

    const pA = a[periodKey] || a.current_view || a.week || {};

    const pB = b[periodKey] || b.current_view || b.week || {};

    const sA = pA.total_score != null ? pA.total_score : 100;

    const sB = pB.total_score != null ? pB.total_score : 100;

    return sB - sA;

  });



  const c1 = filtered[0];

  const c2 = filtered[1];

  const c3 = filtered[2];



  if (!c1) {

    container.innerHTML = '<div class="py-8 text-center text-slate-700 font-bold text-xs">Không có lớp nào phù hợp bộ lọc.</div>';

    return;

  }



  const d1 = c1[periodKey] || c1.current_view || c1.week || {};

  const d2 = c2 ? (c2[periodKey] || c2.current_view || c2.week || {}) : null;

  const d3 = c3 ? (c3[periodKey] || c3.current_view || c3.week || {}) : null;



  const s1 = d1.total_score != null ? Number(d1.total_score).toFixed(2) : '100.00';

  const s2 = d2 && d2.total_score != null ? Number(d2.total_score).toFixed(2) : '-';

  const s3 = d3 && d3.total_score != null ? Number(d3.total_score).toFixed(2) : '-';



  const b1 = d1.bonus_points != null ? Number(d1.bonus_points).toFixed(1) : '0';

  const p1 = d1.penalty_points != null ? Number(d1.penalty_points).toFixed(1) : '0';



  const b2 = d2 && d2.bonus_points != null ? Number(d2.bonus_points).toFixed(1) : '0';

  const p2 = d2 && d2.penalty_points != null ? Number(d2.penalty_points).toFixed(1) : '0';



  const b3 = d3 && d3.bonus_points != null ? Number(d3.bonus_points).toFixed(1) : '0';

  const p3 = d3 && d3.penalty_points != null ? Number(d3.penalty_points).toFixed(1) : '0';



  container.innerHTML = `
    <!-- HẠNG 2 (Á QUÂN - BẠC) -->
    ${c2 ? `
    <div class="podium-pillar podium-silver" onclick="navigateTab('competition')">
      <div class="podium-crown-badge">🥈</div>
      <span class="text-xs font-semibold uppercase tracking-wider text-slate-500">Á Quân · Hạng 2</span>
      <h4 class="podium-class-title text-lg text-slate-800 font-bold">${escapeHtml(c2.name)}</h4>
      <div class="podium-score-pill text-xl text-slate-800 font-bold">${s2}đ</div>
      <div class="podium-sub-text text-slate-500 font-medium">Cộng +${b2} · Trừ -${p2}</div>
    </div>
    ` : '<div class="podium-pillar podium-silver opacity-40"><div class="podium-crown-badge">🥈</div><span class="text-xs text-slate-400 font-medium">Đang cập nhật</span></div>'}

    <!-- HẠNG 1 (QUÁN QUÂN - VÀNG) -->
    <div class="podium-pillar podium-gold" onclick="navigateTab('competition')">
      <div class="podium-crown-badge">👑 🥇</div>
      <span class="text-xs font-semibold uppercase tracking-wider text-amber-700">Dẫn Đầu Toàn Trường · Hạng 1</span>
      <h3 class="podium-class-title text-xl text-amber-950 font-bold">${escapeHtml(c1.name)}</h3>
      <div class="podium-score-pill text-2xl text-amber-900 font-bold">${s1}đ</div>
      <div class="podium-sub-text text-amber-800/90 font-medium">Cộng +${b1} · Trừ -${p1} điểm</div>
    </div>

    <!-- HẠNG 3 (QUÝ QUÂN - ĐỒNG) -->
    ${c3 ? `
    <div class="podium-pillar podium-bronze" onclick="navigateTab('competition')">
      <div class="podium-crown-badge">🥉</div>
      <span class="text-xs font-semibold uppercase tracking-wider text-amber-800/80">Quý Quân · Hạng 3</span>
      <h4 class="podium-class-title text-lg text-amber-950 font-bold">${escapeHtml(c3.name)}</h4>
      <div class="podium-score-pill text-xl text-amber-900 font-bold">${s3}đ</div>
      <div class="podium-sub-text text-amber-800/80 font-medium">Cộng +${b3} · Trừ -${p3}</div>
    </div>
    ` : '<div class="podium-pillar podium-bronze opacity-40"><div class="podium-crown-badge">🥉</div><span class="text-xs text-slate-400 font-medium">Đang cập nhật</span></div>'}
  `;
}



// ==========================================

// RENDER BẢNG TỔNG SẮP CHI ĐOÀN (HIGH CONTRAST)

// ==========================================

function renderDashboardTable(classes, gradeFilter = 'ALL', periodKey = 'week', searchTerm = '') {

  const tbody = document.getElementById('dashboard-data-tbody');

  const countSpan = document.getElementById('dashboard-table-count');

  if (!tbody) return;



  // Cập nhật nhãn bảng phân định rõ Tuần vs Học kỳ

  const weekP = _dashboardData.snapshot?.periods?.WEEK;

  const semP = _dashboardData.snapshot?.periods?.SEMESTER;

  const weekNum = weekP?.week_number || _dashboardData.stats?.current_week_number || 7;

  const semNum = weekP?.semester_number || semP?.semester_number || _dashboardData.stats?.current_semester_number || 1;

  const semRoman = semNum === 1 ? 'I' : 'II';

  const isWeek = periodKey === 'week';



  const titleEl = document.getElementById('dashboard-table-title');

  if (titleEl) {

    titleEl.textContent = isWeek

      ? `Bảng Điểm Thi Đua Chi Đoàn · Tuần ${weekNum} (Học kỳ ${semRoman})`

      : `Bảng Điểm Thi Đua Tổng Hợp · Cả Học kỳ ${semRoman}`;

  }

  const thViolations = document.getElementById('dashboard-th-violations');

  if (thViolations) {

    thViolations.textContent = isWeek ? `Vi phạm (Tuần ${weekNum})` : `Vi phạm (Học kỳ ${semRoman})`;

  }



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

    const pA = a[periodKey] || a.current_view || a.week || {};

    const pB = b[periodKey] || b.current_view || b.week || {};

    const sA = pA.total_score != null ? pA.total_score : 100;

    const sB = pB.total_score != null ? pB.total_score : 100;

    if (sB !== sA) return sB - sA;

    return naturalClassSort(a, b);

  });



  if (countSpan) countSpan.textContent = `${list.length} Chi đoàn`;



  if (!list.length) {

    tbody.innerHTML = '<tr><td colspan="8" class="py-6 text-center text-slate-700 font-bold text-xs">Không tìm thấy Chi đoàn nào phù hợp từ khóa.</td></tr>';

    return;

  }



  tbody.innerHTML = list.map((c, idx) => {

    const pData = c[periodKey] || c.current_view || c.week || {};

    const score = pData.total_score != null ? Number(pData.total_score).toFixed(2) : '100.00';

    const bonus = pData.bonus_points != null ? Number(pData.bonus_points).toFixed(1) : '0.0';

    const penalty = pData.penalty_points != null ? Number(pData.penalty_points).toFixed(1) : '0.0';

    const violations = pData.verified_violations_count != null ? pData.verified_violations_count : 0;

    const rankNum = idx + 1;



    let rankBadge = `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-slate-50 text-slate-500 font-medium text-xs border border-slate-200/60">${rankNum}</span>`;
    if (rankNum === 1) rankBadge = `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-amber-50 text-amber-700 font-bold text-xs border border-amber-200">🥇 1</span>`;
    else if (rankNum === 2) rankBadge = `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-slate-100 text-slate-700 font-bold text-xs border border-slate-200">🥈 2</span>`;
    else if (rankNum === 3) rankBadge = `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-orange-50 text-orange-700 font-bold text-xs border border-orange-200">🥉 3</span>`;
    else if (rankNum <= 10) rankBadge = `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-blue-50 text-blue-700 font-semibold text-xs border border-blue-200/60">${rankNum}</span>`;

    const scoreNum = Number(score);
    const progressWidth = Math.min(100, Math.max(0, (scoreNum / 100) * 100));
    let progressColor = 'bg-emerald-500';
    if (scoreNum < 85) progressColor = 'bg-rose-500';
    else if (scoreNum < 95) progressColor = 'bg-amber-500';

    return `
      <tr class="${idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'} border-b border-slate-100 hover:bg-slate-50/80 transition-colors">
        <td class="py-3 px-3.5 text-center">${rankBadge}</td>
        <td class="py-3 px-3.5 font-semibold text-slate-800 text-sm">${escapeHtml(c.name)}</td>
        <td class="py-3 px-3 text-center"><span class="text-xs font-medium px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200/60">Khối ${c.grade}</span></td>
        <td class="py-3 px-3 text-right font-medium text-emerald-600 text-xs">+${bonus}</td>
        <td class="py-3 px-3 text-right font-medium text-rose-600 text-xs">-${penalty}</td>
        <td class="py-3 px-3.5 text-right font-bold text-base text-slate-900">${score}</td>
        <td class="py-3 px-4">
          <div class="w-full bg-slate-100 rounded-full h-2 overflow-hidden flex border border-slate-200/60" title="${progressWidth}% chuẩn">
            <div class="${progressColor} h-2 rounded-full transition-all duration-300" style="width: ${progressWidth}%"></div>
          </div>
        </td>
        <td class="py-3 px-3 text-center">
          <span class="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-xs font-medium ${violations > 0 ? 'bg-rose-50 text-rose-700 border border-rose-200/60' : 'bg-slate-50 text-slate-500'}">${violations}</span>
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



  const weekP = _dashboardData.snapshot?.periods?.WEEK;

  const semP = _dashboardData.snapshot?.periods?.SEMESTER;

  const weekNum = weekP?.week_number || _dashboardData.stats?.current_week_number || 7;

  const semNum = weekP?.semester_number || semP?.semester_number || _dashboardData.stats?.current_semester_number || 1;

  const semRoman = semNum === 1 ? 'I' : 'II';

  const isWeek = periodKey === 'week';



  const titleEl = document.getElementById('chart-class-comparison-title');

  if (titleEl) {

    titleEl.textContent = `2. So Sánh Điểm Thi Đua Các Lớp · ${isWeek ? `Tuần ${weekNum}` : `Học kỳ ${semRoman}`}`;

  }

  const descEl = document.getElementById('chart-class-comparison-desc');

  if (descEl) {

    descEl.textContent = isWeek

      ? `Phân bố điểm nề nếp theo các lớp trong khối đang chọn cho Tuần ${weekNum} (Học kỳ ${semRoman})`

      : `Phân bố điểm nề nếp tổng hợp tích lũy cả Học kỳ ${semRoman}`;

  }



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

    const pA = a[periodKey] || a.current_view || a.week || {};

    const pB = b[periodKey] || b.current_view || b.week || {};

    const sA = pA.total_score != null ? pA.total_score : 100;

    const sB = pB.total_score != null ? pB.total_score : 100;

    if (sB !== sA) return sB - sA;

    return naturalClassSort(a, b);

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



// ==============================================================================

// ĐIỀU CHỈNH KHUNG THỜI GIAN DASHBOARD: TUẦN (1 ĐẾN 35) & KỲ (KỲ 1 VÀ KỲ 2)

// ==============================================================================

async function initDashboardTimeframeSelectors(defaultWeekNum = 7, defaultSemNum = 1) {

  try {

    const [weeksRes, semsRes] = await Promise.all([

      apiRequest('/api/competition/periods/?period_type=WEEK'),

      apiRequest('/api/competition/periods/?period_type=SEMESTER')

    ]);



    _dashboardData.weeksList = weeksRes || [];

    _dashboardData.semestersList = semsRes || [];

  } catch (e) {

    console.warn('Không thể tải trước danh sách tuần/kỳ:', e);

  }



  // 1. Điền bộ chọn Tuần (Tuần 1 đến Tuần 35) ngay lập tức

  const weekSelect = document.getElementById('dash-week-select');

  if (weekSelect) {

    const hk1Options = [];

    const hk2Options = [];

    for (let w = 1; w <= 18; w++) {

      const isCur = w === defaultWeekNum ? ' ★ (Hiện tại)' : '';

      hk1Options.push(`<option value="${w}" ${w === defaultWeekNum ? 'selected' : ''}>Tuần ${w}${isCur}</option>`);

    }

    for (let w = 19; w <= 35; w++) {

      const isCur = w === defaultWeekNum ? ' ★ (Hiện tại)' : '';

      const sem2W = w - 18;

      hk2Options.push(`<option value="${w}" ${w === defaultWeekNum ? 'selected' : ''}>Tuần ${w} (Tuần ${sem2W} - HK II)${isCur}</option>`);

    }



    weekSelect.innerHTML = `

      <optgroup label="Học kỳ I (18 tuần: Tuần 1 – Tuần 18)">

        ${hk1Options.join('')}

      </optgroup>

      <optgroup label="Học kỳ II (17 tuần: Tuần 19 – Tuần 35)">

        ${hk2Options.join('')}

      </optgroup>

    `;

    weekSelect.value = String(defaultWeekNum);

  }



  // 2. Điền bộ chọn Kỳ (Kỳ 1 và Kỳ 2)

  const semSelect = document.getElementById('dash-sem-select');

  if (semSelect) {

    semSelect.innerHTML = `

      <option value="1" ${defaultSemNum === 1 ? 'selected' : ''}>Kỳ 1 (Học kỳ I · Tuần 1 đến 18)</option>

      <option value="2" ${defaultSemNum === 2 ? 'selected' : ''}>Kỳ 2 (Học kỳ II · Tuần 19 đến 35)</option>

    `;

  }

}



function setDashboardTimeframe(mode) {

  _dashboardData.timeframeMode = mode;

  const btnWeek = document.getElementById('dash-btn-tf-week');

  const btnSem = document.getElementById('dash-btn-tf-semester');

  const wrapWeek = document.getElementById('dash-week-selector-wrap');

  const wrapSem = document.getElementById('dash-sem-selector-wrap');

  const selectWeek = document.getElementById('dash-week-select');

  const selectSem = document.getElementById('dash-sem-select');



  if (mode === 'week') {

    if (btnWeek) { btnWeek.classList.add('active'); btnWeek.style.background = '#07152b'; btnWeek.style.color = '#ffffff'; }

    if (btnSem) { btnSem.classList.remove('active'); btnSem.style.background = 'transparent'; btnSem.style.color = '#1e293b'; }

    if (wrapWeek) wrapWeek.classList.remove('hidden');

    if (wrapSem) wrapSem.classList.add('hidden');

    const wVal = selectWeek ? selectWeek.value : (_dashboardData.selectedWeekNum || 7);

    onDashboardWeekSelect(wVal);

  } else {

    if (btnSem) { btnSem.classList.add('active'); btnSem.style.background = '#07152b'; btnSem.style.color = '#ffffff'; }

    if (btnWeek) { btnWeek.classList.remove('active'); btnWeek.style.background = 'transparent'; btnWeek.style.color = '#1e293b'; }

    if (wrapSem) wrapSem.classList.remove('hidden');

    if (wrapWeek) wrapWeek.classList.add('hidden');

    const sVal = selectSem ? selectSem.value : (_dashboardData.selectedSemNum || 1);

    onDashboardSemesterSelect(sVal);

  }

}



async function onDashboardWeekSelect(weekNumber) {

  weekNumber = parseInt(weekNumber, 10);

  _dashboardData.selectedWeekNum = weekNumber;

  _dashboardData.timeframeMode = 'week';



  const semNum = weekNumber <= 18 ? 1 : 2;

  const semRoman = semNum === 1 ? 'I' : 'II';



  updateDashboardTitles('week', weekNumber, semRoman);



  if (!_dashboardData.weeksList || _dashboardData.weeksList.length === 0) {

    try {

      _dashboardData.weeksList = await apiRequest('/api/competition/periods/?period_type=WEEK');

    } catch (e) {

      console.warn('Lỗi tải weeksList:', e);

    }

  }



  const weekP = (_dashboardData.weeksList || []).find(w => w.week_number === weekNumber);

  const pId = weekP ? weekP.id : null;

  const currentWeekP = _dashboardData.snapshot?.periods?.WEEK;



  // Nếu là tuần hiện tại và đã có snapshot.classes

  if (currentWeekP && pId === currentWeekP.id && _dashboardData.snapshot?.classes) {

    _dashboardData.classesWithScores = _dashboardData.snapshot.classes.map(c => ({

      ...c,

      current_view: c.week || { total_score: 100, bonus_points: 0, penalty_points: 0, verified_violations_count: 0 }

    }));

    refreshDashboardRender();

    return;

  }



  // Nếu có trong cache

  if (pId && _dashboardData.scoresCache[pId]) {

    _dashboardData.classesWithScores = _dashboardData.scoresCache[pId];

    refreshDashboardRender();

    return;

  }



  // Tải từ API

  if (pId) {

    try {

      const res = await apiRequest(`/api/competition/periods/${pId}/scores/`);

      if (res && res.scores) {

        _dashboardData.classesWithScores = res.scores.map(s => ({

          id: s.school_class,

          name: s.class_name,

          grade: s.grade,

          current_view: {

            total_score: parseFloat(s.total_score) || 100,

            bonus_points: parseFloat(s.bonus_points) || 0,

            penalty_points: parseFloat(s.penalty_points) || 0,

            verified_violations_count: s.verified_violations_count || 0,

            rank: s.rank,

            rank_in_grade: s.rank_in_grade

          }

        }));

        _dashboardData.scoresCache[pId] = _dashboardData.classesWithScores;

        refreshDashboardRender();

      }

    } catch (err) {

      console.error(`Lỗi tải điểm Tuần ${weekNumber}:`, err);

    }

  }

}



async function onDashboardSemesterSelect(semNumber) {

  semNumber = parseInt(semNumber, 10);

  _dashboardData.selectedSemNum = semNumber;

  _dashboardData.timeframeMode = 'semester';



  const semRoman = semNumber === 1 ? 'I' : 'II';

  updateDashboardTitles('semester', semNumber, semRoman);



  if (!_dashboardData.semestersList || _dashboardData.semestersList.length === 0) {

    try {

      _dashboardData.semestersList = await apiRequest('/api/competition/periods/?period_type=SEMESTER');

    } catch (e) {

      console.warn('Lỗi tải semestersList:', e);

    }

  }



  const semP = (_dashboardData.semestersList || []).find(s => s.semester_number === semNumber || (s.name && s.name.includes(semRoman)));

  const pId = semP ? semP.id : null;

  const currentSemP = _dashboardData.snapshot?.periods?.SEMESTER;



  // Nếu là Kỳ 1 hiện tại và snapshot có semester

  if (semNumber === 1 && currentSemP && pId === currentSemP.id && _dashboardData.snapshot?.classes && _dashboardData.snapshot.classes[0]?.semester) {

    _dashboardData.classesWithScores = _dashboardData.snapshot.classes.map(c => ({

      ...c,

      current_view: c.semester || { total_score: 100, bonus_points: 0, penalty_points: 0, verified_violations_count: 0 }

    }));

    refreshDashboardRender();

    return;

  }



  // Nếu có trong cache

  if (pId && _dashboardData.scoresCache[pId]) {

    _dashboardData.classesWithScores = _dashboardData.scoresCache[pId];

    refreshDashboardRender();

    return;

  }



  // Tải từ API

  if (pId) {

    try {

      const res = await apiRequest(`/api/competition/periods/${pId}/scores/`);

      if (res && res.scores) {

        _dashboardData.classesWithScores = res.scores.map(s => ({

          id: s.school_class,

          name: s.class_name,

          grade: s.grade,

          current_view: {

            total_score: parseFloat(s.total_score) || 100,

            bonus_points: parseFloat(s.bonus_points) || 0,

            penalty_points: parseFloat(s.penalty_points) || 0,

            verified_violations_count: s.verified_violations_count || 0,

            rank: s.rank,

            rank_in_grade: s.rank_in_grade

          }

        }));

        _dashboardData.scoresCache[pId] = _dashboardData.classesWithScores;

        refreshDashboardRender();

      }

    } catch (err) {

      console.error(`Lỗi tải điểm Kỳ ${semNumber}:`, err);

    }

  }

}



function refreshDashboardRender() {

  if (!_dashboardData.classesWithScores || !_dashboardData.classesWithScores.length) return;

  renderTopPodium(_dashboardData.classesWithScores, _dashboardData.selectedGrade, 'current_view');

  renderDashboardTable(_dashboardData.classesWithScores, _dashboardData.selectedGrade, 'current_view', _dashboardData.searchTerm);

  if (_dashboardData.selectedTab === 'analytics') {

    renderClassComparisonChart('chart-class-comparison', _dashboardData.classesWithScores, _dashboardData.selectedGrade, 'current_view');

  }

}



function updateDashboardTitles(mode, num, semRoman) {

  const isWeek = mode === 'week';

  const titleEl = document.getElementById('dashboard-podium-title');

  if (titleEl) {

    titleEl.innerHTML = `

      <i data-lucide="crown" class="w-5 h-5 text-amber-500"></i>

      Bục Vinh Danh Top 3 Chi Đoàn · ${isWeek ? `Tuần ${num} ${num <= 18 ? '(Học kỳ I)' : `(Tuần ${num - 18} - HK II)`}` : `Kỳ ${num} (Học kỳ ${semRoman})`}

    `;

  }

  const subEl = document.getElementById('dashboard-podium-sub');

  if (subEl) {

    subEl.textContent = isWeek

      ? `Vinh danh 3 Chi đoàn dẫn đầu điểm thi đua nề nếp trong Tuần ${num} (${num <= 18 ? 'Học kỳ I' : 'Học kỳ II'})`

      : `Vinh danh 3 Chi đoàn dẫn đầu tổng điểm thi đua tích lũy cả Kỳ ${num} (Học kỳ ${semRoman})`;

  }



  const tableTitleEl = document.getElementById('dashboard-table-title');

  if (tableTitleEl) {

    tableTitleEl.textContent = isWeek

      ? `Bảng Điểm Thi Đua Chi Đoàn · Tuần ${num} ${num <= 18 ? '(Học kỳ I)' : `(Tuần ${num - 18} - HK II)`}`

      : `Bảng Điểm Thi Đua Tổng Hợp · Kỳ ${num} (Học kỳ ${semRoman})`;

  }

  const thViolations = document.getElementById('dashboard-th-violations');

  if (thViolations) {

    thViolations.textContent = isWeek ? `Vi phạm (Tuần ${num})` : `Vi phạm (Kỳ ${num})`;

  }



  const chartTitleEl = document.getElementById('chart-class-comparison-title');

  if (chartTitleEl) {

    chartTitleEl.textContent = `2. So Sánh Điểm Thi Đua Các Lớp · ${isWeek ? `Tuần ${num}` : `Kỳ ${num} (HK ${semRoman})`}`;

  }

  const chartDescEl = document.getElementById('chart-class-comparison-desc');

  if (chartDescEl) {

    chartDescEl.textContent = isWeek

      ? `Phân bố điểm nề nếp theo các lớp trong khối đang chọn cho Tuần ${num} (${num <= 18 ? 'Học kỳ I' : 'Học kỳ II'})`

      : `Phân bố điểm nề nếp tổng hợp tích lũy cả Kỳ ${num} (Học kỳ ${semRoman})`;

  }



  if (window.lucide) lucide.createIcons();

}

window.setDashboardTimeframe = setDashboardTimeframe;

window.onDashboardWeekSelect = onDashboardWeekSelect;

window.onDashboardSemesterSelect = onDashboardSemesterSelect;



async function loadDashboard(force = false) {

  // Chỉ tải lại khi load trang hoặc khi bấm nút 'Làm mới' rõ ràng (ko tự động reset)

  if (_dashboardData.loaded && !force) {

    return;

  }

  const root = document.getElementById('role-dashboard-content');

  const errorBox = document.getElementById('role-dashboard-error');

  if (!root) return;



  destroyAllHkCharts();

  root.setAttribute('aria-busy', 'true');

  root.innerHTML = `

    <div class="space-y-4 animate-pulse">

      <div class="h-36 rounded-2xl bg-gradient-to-r from-blue-50 via-indigo-50 to-slate-50 border border-slate-200 animate-pulse"></div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="h-28 rounded-2xl bg-slate-100/70 border border-slate-200/70 animate-pulse"></div>
        <div class="h-28 rounded-2xl bg-slate-100/70 border border-slate-200/70 animate-pulse"></div>
        <div class="h-28 rounded-2xl bg-slate-100/70 border border-slate-200/70 animate-pulse"></div>
        <div class="h-28 rounded-2xl bg-slate-100/70 border border-slate-200/70 animate-pulse"></div>
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



    // Phân định rõ ràng Khung Tuần và Học Kỳ

    const weekPeriod = (snapshot.periods && (snapshot.periods.WEEK || snapshot.periods['WEEK'])) || null;

    const semesterPeriod = (snapshot.periods && (snapshot.periods.SEMESTER || snapshot.periods['SEMESTER'])) || null;



    const weekNum = weekPeriod?.week_number || stats.current_week_number || 7;

    const semNum = weekPeriod?.semester_number || semesterPeriod?.semester_number || stats.current_semester_number || 1;

    const semRoman = semNum === 1 ? 'I' : 'II';



    const weekLabel = `Tuần ${weekNum}`;

    const semesterLabel = `Học kỳ ${semRoman}`;

    const currentWeekName = weekPeriod?.display_week_label || `${weekLabel} (${semesterLabel})`;



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

                <p id="dash-welcome-sub">Theo dõi nề nếp số <strong>${stats.total_classes || 36} Chi đoàn</strong> · Năm học 2026–2027 · Khung thời gian: <strong>${weekLabel} (${semesterLabel})</strong>.</p>

              </div>

              <div class="edtech-hero-actions">

                <span class="edtech-live-pill">

                  <span class="edtech-live-dot"></span>

                  Trực tiếp (${timeStr})

                </span>

                <button type="button" onclick="loadDashboard(true)" class="edtech-hero-btn">

                  <i data-lucide="refresh-cw" class="w-3.5 h-3.5 text-slate-500"></i> Làm mới

                </button>

                <button type="button" onclick="openQuickViolationModal()" class="edtech-hero-btn edtech-hero-btn-primary">

                  <i data-lucide="plus-circle" class="w-3.5 h-3.5 text-white"></i> Ghi vi phạm

                </button>

              </div>

            </div>

          </div>



          <!-- 2. 4 HIGH-CONTRAST KPI METRIC CARDS -->

          <div class="edtech-kpi-grid">

            <div class="edtech-kpi-card" onclick="navigateTab('competition')">

              <div class="edtech-kpi-header">

                <span class="edtech-kpi-title">Điểm TB toàn trường (${weekLabel})</span>

                <div class="edtech-kpi-icon bg-blue-50 text-blue-600">

                  <i data-lucide="award" class="w-6 h-6"></i>

                </div>

              </div>

              <div class="edtech-kpi-val-row">

                <span class="edtech-kpi-val text-slate-900">${avgScore}</span>

                <span class="edtech-kpi-badge bg-blue-50 text-blue-700 border border-blue-200/60 font-medium">Chuẩn 100đ</span>

              </div>

              <div class="edtech-kpi-footer">

                <span>Thi đua ${weekLabel} (${semesterLabel})</span>

                <span class="text-brand-600 font-medium">Bảng vàng →</span>

              </div>

            </div>



            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">

              <div class="edtech-kpi-header">

                <span class="edtech-kpi-title">Báo cáo chờ duyệt</span>

                <div class="edtech-kpi-icon bg-amber-50 text-amber-600">

                  <i data-lucide="clock" class="w-6 h-6"></i>

                </div>

              </div>

              <div class="edtech-kpi-val-row">

                <span class="edtech-kpi-val text-amber-600">${pendingV}</span>

                <span class="edtech-kpi-badge ${pendingV > 0 ? 'bg-amber-50 text-amber-700 border border-amber-200/80 font-medium' : 'bg-slate-100 text-slate-600 font-medium'}">

                  ${pendingV > 0 ? 'Cần xử lý' : 'Đã sạch'}

                </span>

              </div>

              <div class="edtech-kpi-footer">

                <span>Biên bản cần thẩm tra</span>

                <span class="text-amber-700 font-medium">Xử lý ngay →</span>

              </div>

            </div>



            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">

              <div class="edtech-kpi-header">

                <span class="edtech-kpi-title">Vi phạm hôm nay</span>

                <div class="edtech-kpi-icon bg-rose-50 text-rose-600">

                  <i data-lucide="alert-triangle" class="w-6 h-6"></i>

                </div>

              </div>

              <div class="edtech-kpi-val-row">

                <span class="edtech-kpi-val text-rose-600">${todayV}</span>

                <span class="edtech-kpi-badge bg-rose-50 text-rose-700 border border-rose-200/80 font-medium">Tuần: ${verifiedW}</span>

              </div>

              <div class="edtech-kpi-footer">

                <span>Sao đỏ & GV ghi nhận</span>

                <span class="text-rose-600 font-medium">Xem nề nếp →</span>

              </div>

            </div>



            <div class="edtech-kpi-card" onclick="navigateTab('student-approvals')">

              <div class="edtech-kpi-header">

                <span class="edtech-kpi-title">${isDoan ? 'Biên bản Sao đỏ gửi' : 'Hồ sơ chờ phê duyệt'}</span>

                <div class="edtech-kpi-icon bg-emerald-50 text-emerald-600">

                  <i data-lucide="${isDoan ? 'shield' : 'user-check'}" class="w-6 h-6"></i>

                </div>

              </div>

              <div class="edtech-kpi-val-row">

                <span class="edtech-kpi-val text-emerald-600">${isDoan ? rsPending : pendingAcc}</span>

                <span class="edtech-kpi-badge ${(isDoan ? rsPending : pendingAcc) > 0 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/80 font-medium' : 'bg-slate-100 text-slate-600 font-medium'}">

                  ${(isDoan ? rsPending : pendingAcc) > 0 ? 'Mới' : 'Hoàn tất'}

                </span>

              </div>

              <div class="edtech-kpi-footer">

                <span>Kiểm duyệt tài khoản</span>

                <span class="text-emerald-700 font-medium">Phê duyệt →</span>

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



            <!-- BỘ CHỌN KHUNG THỜI GIAN THI ĐUA: TUẦN (1-35) HOẶC KỲ (KỲ 1 & 2) -->

            <div class="flex items-center gap-2 flex-wrap">

              <div class="edtech-segmented-nav inline-flex border border-slate-200/80 p-0.5 rounded-xl bg-slate-100/90">

                <button type="button" id="dash-btn-tf-week" onclick="setDashboardTimeframe('week')" class="edtech-seg-btn active">

                  <i data-lucide="calendar" class="w-3.5 h-3.5 inline mr-1"></i> Theo Tuần

                </button>

                <button type="button" id="dash-btn-tf-semester" onclick="setDashboardTimeframe('semester')" class="edtech-seg-btn">

                  <i data-lucide="award" class="w-3.5 h-3.5 inline mr-1"></i> Theo Kỳ

                </button>

              </div>



              <!-- Dropdown Chọn Tuần (1 đến 35) -->

              <div id="dash-week-selector-wrap" class="flex items-center gap-1.5">

                <span class="text-xs font-medium text-slate-500">Tuần:</span>

                <select id="dash-week-select" onchange="onDashboardWeekSelect(this.value)" class="bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs font-semibold text-slate-800 focus:ring-1 focus:ring-brand-500 focus:outline-none shadow-xs cursor-pointer min-w-[200px]">

                  <!-- Rendered dynamically (Tuần 1 đến 35) -->

                </select>

              </div>



              <!-- Dropdown Chọn Kỳ (Kỳ 1 và Kỳ 2) -->

              <div id="dash-sem-selector-wrap" class="hidden flex items-center gap-1.5">

                <span class="text-xs font-medium text-slate-500">Kỳ:</span>

                <select id="dash-sem-select" onchange="onDashboardSemesterSelect(this.value)" class="bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs font-semibold text-slate-800 focus:ring-1 focus:ring-brand-500 focus:outline-none shadow-xs cursor-pointer min-w-[190px]">

                  <option value="1">Kỳ 1 (Học kỳ I · 18 tuần)</option>

                  <option value="2">Kỳ 2 (Học kỳ II · 17 tuần)</option>

                </select>

              </div>

            </div>

          </div>



          <!-- TAB PANE 1: BẢNG VÀNG & THI ĐUA -->

          <div id="dash-pane-leaderboard" class="space-y-5">

            <!-- PODIUM VINH DANH -->

            <div class="edtech-podium-card">

              <div class="flex items-center justify-between flex-wrap gap-2 mb-2">

                <div>

                  <h3 class="font-bold text-slate-900 text-base flex items-center gap-2" id="dashboard-podium-title">

                    <i data-lucide="crown" class="w-5 h-5 text-amber-500"></i>

                    Bục Vinh Danh Top 3 Chi Đoàn · Theo Tuần (${weekLabel})

                  </h3>

                  <p class="text-xs text-slate-500 font-normal mt-0.5" id="dashboard-podium-sub">Vinh danh 3 Chi đoàn dẫn đầu điểm thi đua nề nếp trong ${weekLabel} (${semesterLabel})</p>

                </div>

                <div class="edtech-filter-pills">

                  <span class="text-xs font-medium text-slate-500 mr-1">Khối lớp:</span>

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

                  <h4 class="font-bold text-slate-900 text-sm" id="dashboard-table-title">Bảng Điểm Thi Đua Chi Đoàn · ${weekLabel} (${semesterLabel})</h4>

                  <span id="dashboard-table-count" class="text-xs font-medium text-slate-600 bg-slate-100 px-2.5 py-0.5 rounded-full border border-slate-200/70">36 Chi đoàn</span>

                </div>

                <div class="relative">

                  <i data-lucide="search" class="w-4 h-4 text-slate-400 absolute left-3 top-2.5"></i>

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

                      <th class="py-3 px-3 text-center" id="dashboard-th-violations">Vi phạm (${weekLabel})</th>

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

                    <h3 class="edtech-chart-title" id="chart-class-comparison-title">2. So Sánh Điểm Thi Đua Các Lớp · ${weekLabel}</h3>

                    <p class="edtech-chart-desc" id="chart-class-comparison-desc">Phân bố điểm nề nếp theo các lớp trong khối đang chọn cho ${weekLabel} (${semesterLabel})</p>

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

              <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">

                <div class="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">

                  <h4 class="font-bold text-slate-900 text-sm flex items-center gap-2">

                    <i data-lucide="alert-octagon" class="w-5 h-5 text-rose-600"></i>

                    Chi Đoàn Cần Đoàn Trường Lưu Ý

                  </h4>

                  <span class="text-xs text-slate-500">Tuần hiện tại</span>

                </div>

                <div id="dashboard-attention-classes" class="space-y-2.5">

                  <div class="p-3.5 bg-amber-50/70 border border-amber-200/80 rounded-xl text-xs text-amber-900 flex items-center justify-between">

                    <div>

                      <strong class="font-semibold text-amber-900">Chi đoàn có điểm dưới 90đ:</strong>

                      <p class="text-slate-600 mt-0.5">Cần gặp gỡ Ban cán sự và GVCN để cùng chấn chỉnh nề nếp trang phục, giờ giấc.</p>

                    </div>

                    <button onclick="navigateTab('conduct')" class="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-medium transition">Kiểm tra ngay</button>

                  </div>

                </div>

              </div>



              <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">

                <div class="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">

                  <h4 class="font-bold text-slate-900 text-sm flex items-center gap-2">

                    <i data-lucide="check-circle" class="w-5 h-5 text-emerald-600"></i>

                    Cẩm Nang Thi Đua & Nề Nếp

                  </h4>

                  <span class="text-xs text-slate-500">Quy chuẩn 2026</span>

                </div>

                <div class="space-y-2.5 text-xs text-slate-800 font-medium">

                  <div class="p-3 bg-slate-50/80 rounded-xl border border-slate-100 flex items-center gap-2.5 text-slate-700">

                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-600 shrink-0"></span>

                    <span><strong class="font-semibold text-slate-900">Điểm chuẩn ban đầu:</strong> Mỗi Chi đoàn khởi điểm với 100 điểm trọn vẹn mỗi tuần.</span>

                  </div>

                  <div class="p-3 bg-slate-50/80 rounded-xl border border-slate-100 flex items-center gap-2.5 text-slate-700">

                    <span class="w-2.5 h-2.5 rounded-full bg-blue-600 shrink-0"></span>

                    <span><strong class="font-semibold text-slate-900">Trừ điểm trực tiếp:</strong> Đoàn trường và Admin có quyền trừ điểm trực tiếp không cần duyệt.</span>

                  </div>

                  <div class="p-3 bg-slate-50/80 rounded-xl border border-slate-100 flex items-center gap-2.5 text-slate-700">

                    <span class="w-2.5 h-2.5 rounded-full bg-amber-600 shrink-0"></span>

                    <span><strong class="font-semibold text-slate-900">Khiếu nại minh bạch:</strong> GVCN có 48 giờ để phản hồi hoặc khiếu nại biên bản vi phạm.</span>

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

                <button type="button" onclick="loadDashboard(true)" class="edtech-hero-btn">

                  <i data-lucide="refresh-cw" class="w-3.5 h-3.5 text-slate-500"></i> Làm mới

                </button>

              </div>

            </div>

          </div>



          <!-- SPOTLIGHT CARD LỚP CHỦ NHIỆM (HIGH CONTRAST) -->

          <div class="edtech-personal-card">

            <div class="flex items-center gap-4">

              <div class="w-14 h-14 rounded-2xl bg-emerald-600 text-white flex items-center justify-center font-bold text-xl shadow-xs">

                ${escapeHtml(hrClass.name || 'HK')}

              </div>

              <div>

                <span class="text-[11px] font-semibold text-emerald-800 uppercase tracking-wider">Tiêu điểm Chi đoàn chủ nhiệm</span>

                <h3 class="text-xl font-bold text-slate-900 mt-0.5">Chi đoàn ${escapeHtml(hrClass.name || '')}</h3>

                <p class="text-xs text-slate-600">Xếp hạng: <strong class="text-emerald-700 font-semibold">${rank}</strong> toàn trường · <strong class="text-emerald-700 font-semibold">${rankGrade}</strong> Khối ${hrClass.grade || ''}</p>

              </div>

            </div>

            <div class="text-right">

              <span class="text-xs text-slate-500 font-medium">Điểm thi đua ${weekLabel}:</span>

              <div class="text-2xl font-bold font-mono text-slate-900">${score}đ</div>

              <span class="text-xs text-slate-600">Cộng <strong class="text-emerald-600">+${bonus}</strong> · Trừ <strong class="text-rose-600">-${penalty}</strong></span>

            </div>

          </div>



          <div class="edtech-kpi-grid">

            <div class="edtech-kpi-card" onclick="navigateTab('students')">

              <div class="edtech-kpi-header">

                <span class="edtech-kpi-title">Sĩ số Chi đoàn</span>

                <div class="edtech-kpi-icon bg-blue-50 text-blue-600"><i data-lucide="users" class="w-5 h-5"></i></div>

              </div>

              <div class="edtech-kpi-val-row">

                <span class="edtech-kpi-val text-slate-900">${studentCount}</span>

                <span class="edtech-kpi-badge bg-blue-50 text-blue-700 border border-blue-200/60 font-medium">Học sinh</span>

              </div>

              <div class="edtech-kpi-footer">

                <span>Danh sách học sinh</span>

                <span class="text-brand-600 font-medium">Xem chi tiết →</span>

              </div>

            </div>



            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">

              <div class="edtech-kpi-header">

                <span class="edtech-kpi-title">Biên bản nề nếp</span>

                <div class="edtech-kpi-icon bg-amber-50 text-amber-600"><i data-lucide="bell" class="w-5 h-5"></i></div>

              </div>

              <div class="edtech-kpi-val-row">

                <span class="edtech-kpi-val text-amber-600">${pendingV}</span>

                <span class="edtech-kpi-badge ${pendingV > 0 ? 'bg-amber-50 text-amber-700 border border-amber-200/80 font-medium' : 'bg-slate-100 text-slate-600 font-medium'}">${pendingV > 0 ? 'Cần nắm' : 'An toàn'}</span>

              </div>

              <div class="edtech-kpi-footer">

                <span>Theo dõi học sinh</span>

                <span class="text-amber-700 font-medium">Xem vi phạm →</span>

              </div>

            </div>



            <div class="edtech-kpi-card" onclick="navigateTab('competition')">

              <div class="edtech-kpi-header">

                <span class="edtech-kpi-title">Hạng trong Khối ${hrClass.grade || ''}</span>

                <div class="edtech-kpi-icon bg-emerald-50 text-emerald-600"><i data-lucide="trophy" class="w-5 h-5"></i></div>

              </div>

              <div class="edtech-kpi-val-row">

                <span class="edtech-kpi-val text-emerald-700">${rankGrade}</span>

                <span class="edtech-kpi-badge bg-emerald-50 text-emerald-700 border border-emerald-200/60 font-medium">Khối ${hrClass.grade || ''}</span>

              </div>

              <div class="edtech-kpi-footer">

                <span>So với các lớp cùng khối</span>

                <span class="text-emerald-700 font-medium">Bảng thi đua →</span>

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

                <button type="button" onclick="loadDashboard(true)" class="edtech-hero-btn">

                  <i data-lucide="refresh-cw" class="w-3.5 h-3.5 text-slate-500"></i> Làm mới

                </button>

              </div>

            </div>

          </div>



          <div class="edtech-kpi-grid">

            <div class="edtech-kpi-card">

              <div class="edtech-kpi-header">

                <span class="edtech-kpi-title">Lớp tham gia giảng dạy</span>

                <div class="edtech-kpi-icon bg-blue-50 text-blue-600"><i data-lucide="book-open" class="w-5 h-5"></i></div>

              </div>

              <div class="edtech-kpi-val-row">

                <span class="edtech-kpi-val text-slate-900">${teachCount}</span>

                <span class="edtech-kpi-badge bg-blue-50 text-blue-700 border border-blue-200/60 font-medium">Lớp học</span>

              </div>

              <div class="edtech-kpi-footer"><span>Phân công chuyên môn</span></div>

            </div>



            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Biên bản nề nếp đã phản ánh</span>
                <div class="edtech-kpi-icon bg-emerald-50 text-emerald-600"><i data-lucide="check-square" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-emerald-700">${reportsSent}</span>
                <span class="edtech-kpi-badge bg-emerald-50 text-emerald-700 border border-emerald-200/60 font-medium">Ghi nhận</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Tuần hiện tại</span>
                <span class="text-emerald-700 font-medium">Xem nề nếp →</span>
              </div>
            </div>
          </div>

          <div class="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between flex-wrap gap-4">
            <div>
              <h4 class="font-semibold text-slate-900 text-base">Ghi nhận nề nếp tiết học</h4>
              <p class="text-xs text-slate-500 font-normal mt-1 max-w-xl">Thầy/Cô có thể ghi nhận vi phạm tác phong hoặc tuyên dương cá nhân có tinh thần xây dựng bài học xuất sắc trong giờ dạy.</p>
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

                <button type="button" onclick="loadDashboard(true)" class="edtech-hero-btn">

                  <i data-lucide="refresh-cw" class="w-3.5 h-3.5 text-slate-500"></i> Làm mới

                </button>

              </div>

            </div>

          </div>



          <div class="edtech-kpi-grid">

            <div class="edtech-kpi-card">

              <div class="edtech-kpi-header">

                <span class="edtech-kpi-title">Nhiệm vụ trực ban</span>

                <div class="edtech-kpi-icon bg-blue-50 text-blue-600"><i data-lucide="shield-check" class="w-5 h-5"></i></div>

              </div>

              <div class="edtech-kpi-val-row">

                <span class="edtech-kpi-val text-slate-900">Sao đỏ</span>

                <span class="edtech-kpi-badge bg-blue-50 text-blue-700 border border-blue-200/60 font-medium">Đang trực</span>

              </div>

              <div class="edtech-kpi-footer"><span>Học kỳ I · 2026–2027</span></div>

            </div>



            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Biên bản đã gửi</span>
                <div class="edtech-kpi-icon bg-amber-50 text-amber-600"><i data-lucide="send" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-amber-700">${sent}</span>
                <span class="edtech-kpi-badge bg-amber-50 text-amber-700 border border-amber-200/60 font-medium">Chờ duyệt: ${pending}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Chờ Đoàn trường thẩm tra</span>
                <span class="text-amber-700 font-medium">Xem danh sách →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Biên bản đã xác minh</span>
                <div class="edtech-kpi-icon bg-emerald-50 text-emerald-600"><i data-lucide="check-circle" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-emerald-700">${verified}</span>
                <span class="edtech-kpi-badge bg-emerald-50 text-emerald-700 border border-emerald-200/60 font-medium">Đã duyệt</span>
              </div>
              <div class="edtech-kpi-footer"><span>Được ghi nhận thi đua</span></div>
            </div>
          </div>

          <div class="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between flex-wrap gap-4">
            <div>
              <h4 class="font-semibold text-slate-900 text-base">Gửi biên bản trực ban nề nếp</h4>
              <p class="text-xs text-slate-500 font-normal mt-1 max-w-xl">Ghi nhận chính xác lỗi vi phạm, đúng học sinh và Chi đoàn để đảm bảo tính công bằng và minh bạch trong thi đua toàn trường.</p>
            </div>
            <button onclick="navigateTab('conduct')" class="hk-btn hk-btn-primary">

              <i data-lucide="plus" class="w-4 h-4"></i> Gửi biên bản trực

            </button>

          </div>

        </div>

      `;

    }



    // ==========================================

    // ==========================================
    // 5. HỌC SINH (STUDENT)
    // ==========================================
    else {
      const clsName = stats.student_class || stats.class_name || (currentUser && currentUser.class_name) || (currentUser && currentUser.department_or_class) || 'Chưa xếp lớp';
      const code = stats.student_code || (currentUser && currentUser.student_code) || '-';
      const myV = stats.my_violations_count != null ? stats.my_violations_count : 0;
      const vVerified = stats.my_violations_verified != null ? stats.my_violations_verified : 0;
      const vPending = stats.my_violations_pending != null ? stats.my_violations_pending : 0;
      const hrTeacher = stats.homeroom_teacher || 'Chưa phân công';
      const roomNum = stats.room_number ? ` • Phòng ${stats.room_number}` : '';
      const myViolationsList = stats.my_violations_list || [];

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
                <button type="button" onclick="loadDashboard(true)" class="edtech-hero-btn">
                  <i data-lucide="refresh-cw" class="w-3.5 h-3.5 text-slate-500"></i> Làm mới
                </button>
              </div>
            </div>
          </div>

          <div class="edtech-kpi-grid">
            <div class="edtech-kpi-card cursor-pointer hover:shadow-md transition" onclick="navigateTab('teacher-classes')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Lớp học của tôi</span>
                <div class="edtech-kpi-icon bg-blue-50 text-blue-600"><i data-lucide="graduation-cap" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-slate-800">${escapeHtml(clsName)}</span>
                <span class="edtech-kpi-badge bg-blue-50 text-blue-700 border border-blue-200/60 font-medium">Mã: ${escapeHtml(code)}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>GVCN: ${escapeHtml(hrTeacher)}${roomNum}</span>
                <span class="text-blue-600 font-medium">Xem danh sách lớp →</span>
              </div>
            </div>

            <div class="edtech-kpi-card">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Rèn luyện nề nếp cá nhân</span>
                <div class="edtech-kpi-icon bg-${myV > 0 ? 'rose-50 text-rose-600' : 'emerald-50 text-emerald-600'}">
                  <i data-lucide="${myV > 0 ? 'alert-circle' : 'smile'}" class="w-5 h-5"></i>
                </div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-${myV > 0 ? 'rose-700' : 'emerald-700'}">${myV}</span>
                <span class="edtech-kpi-badge bg-${myV > 0 ? 'rose-50 text-rose-700 border border-rose-200/60' : 'emerald-50 text-emerald-700 border border-emerald-200/60'} font-medium">
                  ${myV === 0 ? 'Rất tốt' : 'Lưu ý'}
                </span>
              </div>
              <div class="edtech-kpi-footer">
                <span>${myV === 0 ? 'Tuyệt vời! Tiếp tục giữ vững nhé ✨' : `Đã duyệt: ${vVerified} • Chờ xử lý: ${vPending}`}</span>
              </div>
            </div>

            <div class="edtech-kpi-card cursor-pointer hover:shadow-md transition" onclick="navigateTab('counseling')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Góc sẻ chia & Tâm lý</span>
                <div class="edtech-kpi-icon bg-amber-50 text-amber-600"><i data-lucide="heart-handshake" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-amber-700">Tư vấn</span>
                <span class="edtech-kpi-badge bg-amber-50 text-amber-700 border border-amber-200/60 font-medium">Học đường</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Không gian lắng nghe học sinh</span>
                <span class="text-amber-700 font-medium">Gửi chia sẻ →</span>
              </div>
            </div>
          </div>

          <!-- BẢNG LỖI VI PHẠM NỀ NẾP CỦA HỌC SINH -->
          <div class="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-5 space-y-4">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100 flex-wrap gap-2">
              <div class="flex items-center gap-2.5">
                <div class="w-9 h-9 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold">
                  <i data-lucide="clipboard-check" class="w-5 h-5"></i>
                </div>
                <div>
                  <h3 class="font-bold text-slate-800 text-sm md:text-base">Lỗi vi phạm nề nếp của bạn</h3>
                  <p class="text-xs text-slate-500 font-normal mt-0.5">Hệ thống ghi nhận và đồng bộ trực tiếp phục vụ rèn luyện cá nhân</p>
                </div>
              </div>
              <span class="px-3 py-1 rounded-full text-xs font-semibold ${myV === 0 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'}">
                ${myV === 0 ? 'Không có vi phạm' : `${myV} bản ghi vi phạm`}
              </span>
            </div>

            ${myViolationsList.length === 0 ? `
              <div class="p-6 md:p-8 rounded-xl bg-gradient-to-r from-emerald-50/70 via-teal-50/40 to-white border border-emerald-200/70 text-center flex flex-col items-center justify-center space-y-2">
                <div class="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center">
                  <i data-lucide="award" class="w-6 h-6"></i>
                </div>
                <h4 class="font-bold text-emerald-900 text-sm md:text-base">Chúc mừng bạn! Không có lỗi vi phạm nề nếp nào được ghi nhận</h4>
                <p class="text-xs text-emerald-700 max-w-lg leading-relaxed">Bạn đang chấp hành rất nghiêm túc nội quy, kỷ luật của Nhà trường. Hãy tiếp tục giữ vững tinh thần gương mẫu và tinh hoa học sinh Hương Khê nhé!</p>
              </div>
            ` : `
              <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse text-xs md:text-sm">
                  <thead>
                    <tr class="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
                      <th class="py-2.5 px-3 w-12 text-center">STT</th>
                      <th class="py-2.5 px-3 w-28">Thời gian</th>
                      <th class="py-2.5 px-3">Nội dung vi phạm / Quy chế</th>
                      <th class="py-2.5 px-3 w-36">Địa điểm</th>
                      <th class="py-2.5 px-3 w-24 text-center">Điểm trừ</th>
                      <th class="py-2.5 px-3 w-32 text-center">Trạng thái</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-100">
                    ${myViolationsList.map((v, i) => `
                      <tr class="hover:bg-slate-50/80 transition-colors">
                        <td class="py-3 px-3 text-center font-bold text-slate-400">${i + 1}</td>
                        <td class="py-3 px-3 font-mono text-slate-600 whitespace-nowrap">${escapeHtml(v.occurred_at || '')}</td>
                        <td class="py-3 px-3">
                          <span class="font-bold text-slate-800 block">${escapeHtml(v.rule_name || 'Vi phạm nội quy')}</span>
                          ${v.rule_code ? `<span class="text-[11px] text-slate-500 font-mono">Mã lỗi: ${escapeHtml(v.rule_code)}</span>` : ''}
                        </td>
                        <td class="py-3 px-3 text-slate-600">${escapeHtml(v.location || 'Khuôn viên trường')}</td>
                        <td class="py-3 px-3 text-center font-bold text-rose-600 whitespace-nowrap">-${v.points_deducted}đ</td>
                        <td class="py-3 px-3 text-center">
                          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${v.status === 'VERIFIED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'}">
                            ${escapeHtml(v.status_display || v.status)}
                          </span>
                        </td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              </div>
            `}
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



    // Lưu trữ lớp với điểm hiện tại

    _dashboardData.classesWithScores = snapshot.classes.map(c => ({

      ...c,

      current_view: c.week || { total_score: 100, bonus_points: 0, penalty_points: 0, verified_violations_count: 0 }

    }));



    // Tải song song danh sách tuần và kỳ để điền vào bộ chọn

    initDashboardTimeframeSelectors(weekNum, semNum);



    // Khởi tạo các biểu đồ và bảng số liệu

    if (isAdmin || isDoanTruong) {

      renderTopPodium(_dashboardData.classesWithScores, _dashboardData.selectedGrade, 'current_view');

      renderDashboardTable(_dashboardData.classesWithScores, _dashboardData.selectedGrade, 'current_view', _dashboardData.searchTerm);

    } else if (isGVCN) {

      const hrClass = stats.homeroom_class || {};

      let myClassTrend = null;

      if (snapshot && snapshot.classes) {

        const found = snapshot.classes.find(c => c.id === hrClass.id || c.name === hrClass.name);

        if (found && found.trend) myClassTrend = found.trend;

      }

      renderWeeklyTrendChart('chart-weekly-trend', snapshot.weekly_trend, myClassTrend, hrClass.name || '');

    } else if (isStudent) {

      // Học sinh không xem bảng xếp hạng thi đua và bục vinh danh

    }



    _dashboardData.loaded = true;



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

        <button type="button" class="hk-btn hk-btn-primary text-xs ml-3" onclick="loadDashboard(true)">Thử lại</button>

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





// 2. CONDUCT & VIOLATIONS MODULE

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



async function loadConductViolations() {

  const tbody = document.getElementById('conduct-violations-tbody');

  const classId = document.getElementById('filter-conduct-class')?.value || '';

  const statusVal = document.getElementById('filter-conduct-status')?.value || '';

  const reporterRole = document.getElementById('filter-conduct-reporter-role')?.value || '';

  const dateFrom = document.getElementById('filter-conduct-from')?.value || '';

  const dateTo = document.getElementById('filter-conduct-to')?.value || '';



  let url = `/api/conduct/violations/?class_id=${classId}&status=${statusVal}&date_from=${dateFrom}&date_to=${dateTo}${reporterRole ? `&reporter_role=${reporterRole}` : ''}`;



  try {

    tbody.innerHTML = '<tr><td colspan="10" class="text-center py-8 text-slate-400">Đang tải dữ liệu...</td></tr>';

    const res = await fetch(url, { cache: 'no-store' });

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

  const canVerify = currentUser && (currentUser.role === 'ADMIN' || currentUser.role === 'SUPER_ADMIN' || currentUser.role === 'DOAN_TRUONG' || currentUser.is_doan_truong || currentUser.can_verify_violations);

  const isStudent = currentUser && (currentUser.is_student || currentUser.role === 'HOC_SINH');
  const studentClassId = Number(currentUser?.school_class_id || currentUser?.student_class_info?.id || currentUser?.student_profile?.school_class_id || 0);
  const violationClassId = Number(v.school_class || v.class_id || 0);

  const isOwnerStudent = isStudent && (
    (currentUser.student_profile && v.student === currentUser.student_profile.id) ||
    (currentUser.student_id && v.student === currentUser.student_id) ||
    (currentUser.student_code && v.student_code === currentUser.student_code) ||
    (v.student_name && currentUser.full_name && v.student_name.trim() === currentUser.full_name.trim())
  );

  const isClassMonitor = isStudent && Boolean(currentUser.is_class_monitor || currentUser.student_profile?.is_class_monitor) && (
    !violationClassId || !studentClassId || violationClassId === studentClassId
  );

  const isHomeroom = Boolean(currentUser && (currentUser.is_gvcn || currentUser.role === 'GVCN'));
  const isAdminOrDoan = Boolean(currentUser && (currentUser.is_admin || currentUser.is_doan_truong || currentUser.role === 'ADMIN' || currentUser.role === 'DOAN_TRUONG'));

  const canAppeal = isOwnerStudent || isClassMonitor || isHomeroom || isAdminOrDoan;



  let btns = `<button onclick="openViolationDetailModal(${v.id})" class="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-[11px] font-medium transition mr-1">Chi tiết</button>`;



  if (canVerify && v.status === 'PENDING') {

    btns += `<button onclick="openVerifyModal(${v.id}, '${v.record_code}', '${(v.student_name || 'Tập thể').replace(/'/g, "\\'")} (${v.class_name})', '${(v.rule_name || '').replace(/'/g, "\\'")}', '${(v.description || '').replace(/'/g, "\\'")}')" class="px-2.5 py-1 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-[11px] font-semibold transition">Xác minh</button>`;

  } else if (canVerify && v.status === 'APPEALING') {

    btns += `<button onclick="openVerifyModal(${v.id}, '${v.record_code}', '${(v.student_name || 'Tập thể').replace(/'/g, "\\'")}', '${(v.rule_name || '').replace(/'/g, "\\'")}', 'Khiếu nại: ${(v.appeal_reason || '').replace(/'/g, "\\'")}')" class="px-2.5 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-[11px] font-semibold transition">Duyệt khiếu nại</button>`;

  }



  if (canVerify && (v.status === 'VERIFIED' || v.status === 'ADJUSTED')) {

    const studentLabel = (v.student_name || 'Tập thể').replace(/'/g, "\\'");

    btns += `<button onclick="openAdjustUndoModal(${v.id}, '${v.record_code}', '${studentLabel} (${v.class_name})', ${v.points_deducted})" class="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 rounded-lg text-[11px] font-semibold transition ml-1">Hoàn tác / Sửa</button>`;

  }



  if (canAppeal && v.status === 'VERIFIED') {

    btns += `<button onclick="openAppealModal(${v.id})" class="px-2.5 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-[11px] font-semibold transition">Khiếu nại</button>`;

  }



  return btns;

}



let currentDetailViolationId = null;



async function openViolationDetailModal(id) {

  currentDetailViolationId = id;

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



function canUserDeductDirectly() {

  if (!currentUser) return false;

  return Boolean(

    currentUser.is_admin ||

    currentUser.is_super_admin ||

    currentUser.role === 'ADMIN' ||

    currentUser.role === 'SUPER_ADMIN' ||

    currentUser.role === 'DOAN_TRUONG' ||

    currentUser.role === 'BCH_DOAN' ||

    currentUser.is_doan_truong ||

    currentUser.can_verify_violations

  );

}



function naturalSortClasses(list) {
  if (!Array.isArray(list)) return [];
  return [...list].sort((a, b) => {
    const ga = Number(a.grade) || 0;
    const gb = Number(b.grade) || 0;
    if (ga !== gb) return ga - gb;
    const oa = Number(a.class_order) || 0;
    const ob = Number(b.class_order) || 0;
    if (oa !== ob) return oa - ob;
    return (a.name || '').localeCompare(b.name || '', undefined, { numeric: true, sensitivity: 'base' });
  });
}

function populateModalViolationClasses(filterGrade = '', selectedClassId = null) {
  const modalClassSelect = document.getElementById('modal-violation-class');
  const countBadge = document.getElementById('violation-class-count-badge');
  if (!modalClassSelect) return;

  const rawClasses = Array.isArray(classesCache) ? classesCache : [];
  const sortedAll = naturalSortClasses(rawClasses);

  let targetClasses = sortedAll;
  if (filterGrade !== '' && filterGrade !== null && filterGrade !== undefined) {
    targetClasses = sortedAll.filter(c => String(c.grade) === String(filterGrade));
  }

  if (countBadge) {
    countBadge.textContent = `${targetClasses.length} lớp`;
  }

  let html = '';
  if (filterGrade !== '' && filterGrade !== null && filterGrade !== undefined) {
    html += `<option value="">-- Chọn lớp học (${targetClasses.length} lớp) --</option>`;
    targetClasses.forEach(c => {
      const isSel = (selectedClassId && Number(selectedClassId) === Number(c.id));
      html += `<option value="${c.id}" ${isSel ? 'selected' : ''}>Lớp ${escapeHtml(c.name)} (Khối ${c.grade})</option>`;
    });
  } else {
    html += `<option value="">-- Chọn lớp trong toàn trường (${sortedAll.length} lớp) --</option>`;
    const grades = [10, 11, 12];
    grades.forEach(g => {
      const gClasses = sortedAll.filter(c => Number(c.grade) === g);
      if (gClasses.length > 0) {
        html += `<optgroup label="Khối ${g} (${gClasses.length} lớp)">`;
        gClasses.forEach(c => {
          const isSel = (selectedClassId && Number(selectedClassId) === Number(c.id));
          html += `<option value="${c.id}" ${isSel ? 'selected' : ''}>Lớp ${escapeHtml(c.name)}</option>`;
        });
        html += `</optgroup>`;
      }
    });
    const otherClasses = sortedAll.filter(c => ![10, 11, 12].includes(Number(c.grade)));
    if (otherClasses.length > 0) {
      html += `<optgroup label="Lớp khác (${otherClasses.length} lớp)">`;
      otherClasses.forEach(c => {
        const isSel = (selectedClassId && Number(selectedClassId) === Number(c.id));
        html += `<option value="${c.id}" ${isSel ? 'selected' : ''}>Lớp ${escapeHtml(c.name)}</option>`;
      });
      html += `</optgroup>`;
    }
  }

  modalClassSelect.innerHTML = html;

  if (selectedClassId && targetClasses.some(c => Number(c.id) === Number(selectedClassId))) {
    modalClassSelect.value = selectedClassId;
  }
}

function handleGradeChangeForViolation(grade) {
  const classSelect = document.getElementById('modal-violation-class');
  const prevClassId = classSelect ? classSelect.value : '';

  populateModalViolationClasses(grade, prevClassId);

  if (classSelect && classSelect.value !== prevClassId) {
    const studentSelect = document.getElementById('modal-violation-student');
    if (studentSelect) {
      studentSelect.innerHTML = '<option value="">-- Cả tập thể lớp --</option>';
    }
    const previewBox = document.getElementById('violation-preview-box');
    if (previewBox) previewBox.classList.add('hidden');
  }
}

function openQuickViolationModal() {
  if (currentUser && (currentUser.role === 'GVBM' || currentUser.is_gvbm) && !currentUser.is_admin && !currentUser.is_gvcn) {
    showToast('Giáo viên bộ môn chỉ có quyền gửi phản ánh nề nếp, không được ghi nhận vi phạm trừ điểm.', 'warning');
    openCreateReflectionModal();
    return;
  }
  const modal = document.getElementById('modal-quick-violation');
  activeViolationSubmissionKey = activeViolationSubmissionKey || createSubmissionKey();
  modal.classList.remove('hidden');
  document.getElementById('modal-violation-time').value = getLocalIsoString(new Date(Date.now() + serverTimeOffsetMs));

  const gradeSelect = document.getElementById('modal-violation-grade');
  if (gradeSelect) gradeSelect.value = '';

  if (!classesCache || classesCache.length === 0) {
    loadMetadata().then(() => {
      populateModalViolationClasses('');
    });
  } else {
    populateModalViolationClasses('');
  }

  const canDirect = canUserDeductDirectly();
  const submitButton = document.getElementById('modal-violation-submit-btn');
  const directNotice = document.getElementById('preview-direct-deduct-notice');
  const pendingNotice = document.getElementById('preview-pending-notice');
  if (submitButton) {
    if (canDirect) {
      submitButton.textContent = 'Xác nhận vi phạm và trừ điểm';
      submitButton.className = 'px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-sm transition';
      if (directNotice) directNotice.classList.remove('hidden');
      if (pendingNotice) pendingNotice.classList.add('hidden');
    } else {
      submitButton.textContent = 'Gửi bản ghi để xác minh';
      submitButton.className = 'px-5 py-2 bg-brand-600 hover:bg-brand-700 text-white font-bold rounded-xl shadow-sm transition';
      if (directNotice) directNotice.classList.add('hidden');
      if (pendingNotice) pendingNotice.classList.remove('hidden');
    }
  }

  const previewBox = document.getElementById('violation-preview-box');
  if (previewBox) previewBox.classList.add('hidden');

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

  updateViolationPointsPreview();

}



async function updateViolationPointsPreview() {

  const classId = document.getElementById('modal-violation-class')?.value;

  const ruleId = document.getElementById('modal-violation-rule')?.value;

  const previewBox = document.getElementById('violation-preview-box');

  if (!classId || !ruleId) {

    if (previewBox) previewBox.classList.add('hidden');

    return;

  }



  try {

    const res = await fetch(`/api/conduct/violations/preview-deduction/?class_id=${classId}&rule_id=${ruleId}`);

    if (!res.ok) return;

    const data = await res.json();

    const badge = document.getElementById('preview-rule-badge');

    const curr = document.getElementById('preview-current-score');

    const proj = document.getElementById('preview-projected-score');

    if (badge) badge.textContent = `-${Number(data.points_to_deduct).toFixed(2)}đ`;

    if (curr) curr.textContent = Number(data.current_score).toFixed(2);

    if (proj) proj.textContent = Number(data.projected_score).toFixed(2);

    if (previewBox) previewBox.classList.remove('hidden');

    lucide.createIcons();

  } catch (e) {

    console.error('Lỗi tải xem trước điểm trừ:', e);

  }

}



async function handleQuickViolationSubmit(e) {

  e.preventDefault();

  const form = document.getElementById('quick-violation-form');

  const classSelect = document.getElementById('modal-violation-class');

  const studentSelect = document.getElementById('modal-violation-student');

  const ruleSelect = document.getElementById('modal-violation-rule');



  const classId = classSelect.value;

  const ruleId = ruleSelect.value;

  if (!classId || !ruleId) {

    showToast('Vui lòng chọn lớp học và lỗi vi phạm.', 'warning');

    return;

  }



  const canDirect = canUserDeductDirectly();

  if (canDirect) {

    const className = classSelect.options[classSelect.selectedIndex]?.text || '';

    const ruleName = ruleSelect.options[ruleSelect.selectedIndex]?.text || '';

    const studentName = studentSelect.value ? (studentSelect.options[studentSelect.selectedIndex]?.text || '') : 'Toàn thể lớp';

    const confirmMsg = `Xác nhận ghi nhận vi phạm và TRỪ TRỰC TIẾP điểm thi đua?\n\n- Lớp: ${className}\n- Đối tượng: ${studentName}\n- Vi phạm: ${ruleName}\n\nĐiểm thi đua sẽ được trừ ngay lập tức không cần Admin duyệt.`;

    if (!window.confirm(confirmMsg)) {

      return;

    }

  }



  const occurredAtVal = document.getElementById('modal-violation-time').value;

  if (occurredAtVal) {

    const selectedTime = new Date(occurredAtVal).getTime();

    const currentTime = Date.now() + serverTimeOffsetMs;

    if (selectedTime > currentTime + 5 * 60 * 1000) {

      showToast('Thời gian vi phạm không thể ở tương lai. Vui lòng ghi nhận thời gian thực.', 'error');

      return;

    }

  }



  const formData = new FormData();

  formData.append('school_class', classId);

  formData.append('student', studentSelect.value || '');

  formData.append('rule', ruleId);

  formData.append('location', document.getElementById('modal-violation-location').value);

  formData.append('description', document.getElementById('modal-violation-desc').value);

  formData.append('occurred_at', document.getElementById('modal-violation-time').value);

  if (canDirect) {

    formData.append('direct_deduct', 'true');

  }



  const fileInput = document.getElementById('modal-violation-file');

  if (fileInput.files.length > 0) {

    formData.append('evidence_image', fileInput.files[0]);

  }



  const fingerprint = JSON.stringify([

    ...Array.from(formData.entries()).filter(([key]) => key !== 'evidence_image'),

    fileInput.files[0] ? [fileInput.files[0].name, fileInput.files[0].size, fileInput.files[0].lastModified] : null

  ]);

  if (!activeViolationSubmissionKey || (lastViolationFingerprint && fingerprint !== lastViolationFingerprint)) {

    activeViolationSubmissionKey = createSubmissionKey();

  }

  lastViolationFingerprint = fingerprint;

  formData.append('submission_key', activeViolationSubmissionKey);



  const submitButton = document.getElementById('modal-violation-submit-btn') || form.querySelector('button[type="submit"]');

  const origBtnText = submitButton.textContent;

  submitButton.disabled = true;

  submitButton.textContent = 'Đang xử lý...';



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

      const emailStatus = data.email_status;

      let emailNote = data.email_message || '';

      if (!emailNote) {

        if (emailStatus === 'SENT') {

          emailNote = 'Đã gửi email thành công.';

        } else if (emailStatus === 'FAILED') {

          emailNote = 'Vi phạm đã được ghi nhận, nhưng email thông báo chưa gửi được. Hệ thống sẽ thử gửi lại.';

        } else if (emailStatus === 'SKIPPED') {

          emailNote = 'Chưa có tài khoản Đoàn trường hợp lệ để gửi email thông báo.';

        } else {

          emailNote = 'Đang chờ gửi email.';

        }

      }



      if (data.status === 'VERIFIED') {

        const scoreInfo = (data.score_before !== null && data.score_after !== null && data.score_before !== undefined)

          ? ` (Điểm thi đua: ${data.score_before} ➔ ${data.score_after})`

          : '';

        showToast(`Đã ghi nhận vi phạm ${data.record_code} và trừ trực tiếp ${data.points_deducted}đ thành công!${scoreInfo} · ${emailNote}`, 'success');

      } else {

        showToast(`Đã gửi bản ghi ${data.record_code} thành công (Chờ xác minh). · ${emailNote}`, 'success');

      }



      closeQuickViolationModal();

      form.reset();

      activeViolationSubmissionKey = null;

      lastViolationFingerprint = '';

      loadConductViolations();

      loadDashboard();

      if (typeof loadCompetitionScores === 'function') {

        loadCompetitionScores();

      }

    } else {

      showToast(data.error || 'Không thể ghi nhận vi phạm. Vui lòng kiểm tra dữ liệu và thử lại.', 'error');

    }

  } catch (err) {

    showToast('Lỗi kết nối máy chủ', 'error');

  } finally {

    submitButton.disabled = false;

    submitButton.textContent = origBtnText;

  }

}



function openAdjustUndoModal(id, code, target, points) {

  document.getElementById('adjust-undo-id').value = id;

  document.getElementById('adjust-undo-code').textContent = code;

  document.getElementById('adjust-undo-target').textContent = target;

  document.getElementById('adjust-undo-points').textContent = `-${points}đ`;

  document.getElementById('adjust-undo-action').value = 'undo';

  document.getElementById('adjust-undo-points-wrapper').classList.add('hidden');

  document.getElementById('adjust-undo-reason').value = '';

  document.getElementById('modal-adjust-undo-violation').classList.remove('hidden');

  lucide.createIcons();

}



function closeAdjustUndoModal() {

  document.getElementById('modal-adjust-undo-violation').classList.add('hidden');

}



function handleAdjustUndoActionChange(action) {

  const wrapper = document.getElementById('adjust-undo-points-wrapper');

  const submitBtn = document.getElementById('adjust-undo-submit-btn');

  if (action === 'adjust') {

    wrapper.classList.remove('hidden');

    submitBtn.textContent = 'Lưu điều chỉnh điểm';

  } else {

    wrapper.classList.add('hidden');

    submitBtn.textContent = 'Xác nhận hoàn tác';

  }

}



async function handleAdjustUndoSubmit(e) {

  e.preventDefault();

  const id = document.getElementById('adjust-undo-id').value;

  const action = document.getElementById('adjust-undo-action').value;

  const reason = document.getElementById('adjust-undo-reason').value.trim();

  const newPoints = document.getElementById('adjust-undo-new-points').value;



  if (!reason) {

    showToast('Vui lòng nhập lý do điều chỉnh hoặc hoàn tác.', 'warning');

    return;

  }



  const payload = { action, reason };

  if (action === 'adjust') {

    if (newPoints === '' || isNaN(newPoints) || Number(newPoints) < 0) {

      showToast('Mức điểm trừ mới không hợp lệ.', 'warning');

      return;

    }

    payload.adjusted_points = parseFloat(newPoints);

  }



  const submitBtn = document.getElementById('adjust-undo-submit-btn');

  submitBtn.disabled = true;

  submitBtn.textContent = 'Đang xử lý...';



  try {

    const res = await fetch(`/api/conduct/violations/${id}/adjust-or-undo/`, {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken')

      },

      body: JSON.stringify(payload)

    });

    const data = await res.json();

    if (res.ok) {

      showToast(data.message || 'Thao tác thành công', 'success');

      closeAdjustUndoModal();

      loadConductViolations();

      loadDashboard();

      if (typeof loadCompetitionScores === 'function') {

        loadCompetitionScores();

      }

    } else {

      showToast(data.error || 'Lỗi xử lý yêu cầu', 'error');

    }

  } catch (err) {

    showToast('Lỗi kết nối máy chủ', 'error');

  } finally {

    submitBtn.disabled = false;

    submitBtn.textContent = 'Xác nhận xử lý';

  }

}



function createSubmissionKey() {

  if (window.crypto && typeof window.crypto.randomUUID === 'function') return window.crypto.randomUUID();

  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, char => {

    const random = Math.random() * 16 | 0;

    return (char === 'x' ? random : (random & 0x3 | 0x8)).toString(16);

  });

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

// ==========================================

// 3. THI ĐUA CHI ĐOÀN (THEO TUẦN, THÁNG, HỌC KỲ)

// ==========================================

let selectedCompetitionPeriodType = 'WEEK'; // 'WEEK' | 'MONTH' | 'SEMESTER'

let selectedAcademicYearId = '';

let selectedPeriodId = '';

let selectedCompetitionGrade = '';

let competitionSearchQuery = '';

let competitionSearchTimer = null;

let competitionMeta = null;

let periodsCache = [];

let selectedCompetitionSemesterNumber = '';



async function initCompetitionModule() {

  try {

    // 1. Tải metadata danh mục (Năm học, Học kỳ, Tiêu chí biểu điểm)

    const res = await fetch('/api/competition/periods/filters-meta/');

    if (res.ok) {

      competitionMeta = await res.json();

      populateCompetitionFiltersMeta();

    }

    // 2. Tải danh sách kỳ thi đua và bảng xếp hạng

    await loadCompetitionPeriodsList();

  } catch (err) {

    console.error('Lỗi khởi tạo module thi đua:', err);

  }

}



function populateCompetitionFiltersMeta() {

  if (!competitionMeta) return;



  // Điền danh sách năm học

  const yearSelect = document.getElementById('comp-filter-academic-year');

  const modalYearSelect = document.getElementById('new-period-academic-year');

  if (yearSelect && competitionMeta.academic_years) {

    yearSelect.innerHTML = competitionMeta.academic_years.map(y => `

      <option value="${y.id}" ${y.is_current ? 'selected' : ''}>Năm học: ${y.name}</option>

    `).join('');

    selectedAcademicYearId = yearSelect.value;

  }

  if (modalYearSelect && competitionMeta.academic_years) {

    modalYearSelect.innerHTML = competitionMeta.academic_years.map(y => `

      <option value="${y.id}" ${y.is_current ? 'selected' : ''}>${y.name}</option>

    `).join('');

  }



  // Điền danh sách học kỳ trong modal tạo kỳ

  const modalSemSelect = document.getElementById('new-period-semester');

  if (modalSemSelect && competitionMeta.semesters) {

    modalSemSelect.innerHTML = '<option value="">(Không bắt buộc)</option>' + competitionMeta.semesters.map(s => `

      <option value="${s.id}">Học kỳ: ${s.name}</option>

    `).join('');

  }

}



async function loadCompetitionPeriodsList(preferredPeriodId = null) {

  const periodSelect = document.getElementById('comp-filter-period');

  const semWrapper = document.getElementById('comp-semester-wrapper');

  if (!periodSelect) return;



  // Ẩn vĩnh viễn bộ lọc học kỳ phụ vì Khung Tuần chọn trực tiếp Tuần 1 đến 35, Khung Kỳ chọn Kỳ 1 và Kỳ 2

  if (semWrapper) {

    semWrapper.style.display = 'none';

    semWrapper.classList.add('hidden');

  }



  try {

    periodSelect.innerHTML = '<option value="">Đang tải danh sách kỳ...</option>';

    let url = `/api/competition/periods/?period_type=${selectedCompetitionPeriodType}`;

    if (selectedAcademicYearId) url += `&academic_year=${selectedAcademicYearId}`;

    // Luôn tải toàn bộ 35 tuần khi xem theo Khung Tuần, không giới hạn học kỳ



    const res = await fetch(url);

    if (!res.ok) throw new Error('Không thể tải danh sách kỳ');

    periodsCache = await res.json();



    if (periodsCache.length === 0) {

      periodSelect.innerHTML = '<option value="">Chưa có kỳ nào</option>';

      selectedPeriodId = '';

      currentPeriod = null;

      renderEmptyCompetitionTable('Chưa có kỳ thi đua nào được cấu hình cho loại này.');

      return;

    }



    // Ưu tiên kỳ hiện tại theo trạng thái lịch do máy chủ xác định

    let defaultPeriod = periodsCache.find(p => p.id === preferredPeriodId);

    if (!defaultPeriod) {

      defaultPeriod = periodsCache.find(p => p.result_status === 'TEMPORARY' && !p.calendar_requires_review);

    }

    if (!defaultPeriod) {

      defaultPeriod = periodsCache.find(p => !p.calendar_requires_review && p.result_status === 'WAITING_LOCK')

        || periodsCache.find(p => !p.calendar_requires_review && p.result_status === 'NOT_STARTED')

        || periodsCache.find(p => !p.calendar_requires_review)

        || periodsCache[0];

    }

    selectedPeriodId = defaultPeriod ? defaultPeriod.id : periodsCache[0].id;



    // Phân nhóm hiển thị trực quan cho Khung Tuần (Tuần 1 đến Tuần 35)

    if (selectedCompetitionPeriodType === 'WEEK') {

      const sortedWeeks = [...periodsCache].sort((a, b) => (a.week_number || 0) - (b.week_number || 0));

      const hk1Weeks = sortedWeeks.filter(p => (p.week_number && p.week_number <= 18) || p.semester_number === 1);

      const hk2Weeks = sortedWeeks.filter(p => (p.week_number && p.week_number > 18) || p.semester_number === 2);



      let optHtml = '';

      if (hk1Weeks.length > 0) {

        optHtml += `<optgroup label="Học kỳ I (18 tuần: Tuần 1 đến Tuần 18)">`;

        optHtml += hk1Weeks.map(p => {

          const wNum = p.week_number || '';

          const isCur = p.result_status === 'TEMPORARY' ? ' · Tạm tính' : '';

          const lockStatus = (p.is_locked || p.result_status === 'LOCKED') ? ' 🔒 (Đã chốt)' : (p.result_status === 'WAITING_LOCK' ? ' · Chờ chốt' : '');

          const review = p.calendar_requires_review ? ' ⚠️' : '';

          return `<option value="${p.id}" ${p.id === selectedPeriodId ? 'selected' : ''}>Tuần ${wNum} (Học kỳ I)${isCur}${lockStatus}${review}</option>`;

        }).join('');

        optHtml += `</optgroup>`;

      }

      if (hk2Weeks.length > 0) {

        optHtml += `<optgroup label="Học kỳ II (17 tuần: Tuần 19 đến Tuần 35)">`;

        optHtml += hk2Weeks.map(p => {

          const wNum = p.week_number || '';

          const sem2W = wNum > 18 ? ` (Tuần ${wNum - 18} - HK II)` : ' (Học kỳ II)';

          const isCur = p.result_status === 'TEMPORARY' ? ' · Tạm tính' : '';

          const lockStatus = (p.is_locked || p.result_status === 'LOCKED') ? ' 🔒 (Đã chốt)' : (p.result_status === 'WAITING_LOCK' ? ' · Chờ chốt' : '');

          const review = p.calendar_requires_review ? ' ⚠️' : '';

          return `<option value="${p.id}" ${p.id === selectedPeriodId ? 'selected' : ''}>Tuần ${wNum}${sem2W}${isCur}${lockStatus}${review}</option>`;

        }).join('');

        optHtml += `</optgroup>`;

      }

      const otherWeeks = sortedWeeks.filter(p => !hk1Weeks.includes(p) && !hk2Weeks.includes(p));

      if (otherWeeks.length > 0) {

        optHtml += `<optgroup label="Các tuần khác">`;

        optHtml += otherWeeks.map(p => `<option value="${p.id}" ${p.id === selectedPeriodId ? 'selected' : ''}>${p.display_week_label || p.name}</option>`).join('');

        optHtml += `</optgroup>`;

      }

      periodSelect.innerHTML = optHtml;

      if (!selectedPeriodId && periodSelect.value) {

        selectedPeriodId = periodSelect.value;

      }

    } else if (selectedCompetitionPeriodType === 'SEMESTER') {

      const seenSems = new Set();

      const uniqueSems = [];

      for (const p of periodsCache) {

        const num = p.semester_number || (p.name && p.name.includes('I') && !p.name.includes('II') ? 1 : (p.name && p.name.includes('II') ? 2 : 1));

        if (!seenSems.has(num)) {

          seenSems.add(num);

          uniqueSems.push({ ...p, semester_number: num });

        }

      }

      uniqueSems.sort((a, b) => (a.semester_number || 1) - (b.semester_number || 1));

      periodSelect.innerHTML = uniqueSems.map(p => {

        const num = p.semester_number;

        const semTitle = num === 1 ? 'Kỳ 1 (Học kỳ I · Tuần 1 đến 18)' : 'Kỳ 2 (Học kỳ II · Tuần 19 đến 35)';

        const isCur = p.result_status === 'TEMPORARY' ? ' · Tạm tính' : '';

        const lockStatus = (p.is_locked || p.result_status === 'LOCKED') ? ' 🔒 (Đã chốt)' : (p.result_status === 'WAITING_LOCK' ? ' · Chờ chốt' : '');

        return `<option value="${p.id}" ${p.id === selectedPeriodId ? 'selected' : ''}>${semTitle}${isCur}${lockStatus}</option>`;

      }).join('');

      if (!selectedPeriodId && periodSelect.value) {

        selectedPeriodId = periodSelect.value;

      }

    } else {

      periodSelect.innerHTML = periodsCache.map(p => {

        const isCur = p.result_status === 'TEMPORARY' ? ' · Tạm tính' : '';

        const lockStatus = (p.is_locked || p.result_status === 'LOCKED') ? ' 🔒 (Đã chốt)' : (p.result_status === 'WAITING_LOCK' ? ' · Chờ chốt' : '');

        const review = p.calendar_requires_review ? ' ⚠️ (Cần rà soát lịch cũ)' : '';

        return `<option value="${p.id}" ${p.id === selectedPeriodId ? 'selected' : ''}>${p.name}${isCur}${lockStatus}${review}</option>`;

      }).join('');

      if (!selectedPeriodId && periodSelect.value) {

        selectedPeriodId = periodSelect.value;

      }

    }



    await loadCompetitionScores();

  } catch (err) {

    console.error('Lỗi tải kỳ thi đua:', err);

    periodSelect.innerHTML = '<option value="">Lỗi tải kỳ</option>';

  }

}



function onCompetitionSemesterFilterChange() {

  const sel = document.getElementById('comp-filter-semester');

  if (sel) {

    selectedCompetitionSemesterNumber = sel.value;

  }

  loadCompetitionPeriodsList();

}



async function initStandard35WeeksSchedule() {

  if (!confirm(`Bạn có chắc chắn muốn khởi tạo các kỳ còn thiếu trong khung 35 tuần học (18 tuần Học kỳ I + 17 tuần Học kỳ II)?

- Hệ thống tạo bảng điểm cho các lớp đang hoạt động của năm học đã chọn.

- Lịch sử vi phạm và các kỳ đã chốt sổ vẫn được bảo toàn nguyên vẹn.`)) {

    return;

  }



  try {

    showToast('Đang chuẩn hóa 35 tuần học cho THPT Hương Khê...', 'info');

    const res = await fetch('/api/competition/periods/init-standard-schedule/', {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken')

      },

      body: JSON.stringify({ academic_year: selectedAcademicYearId })

    });

    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Lỗi chuẩn hóa lịch trình');

    

    showToast(data.message || 'Chuẩn hóa thành công 35 tuần học!', 'success');

    await loadCompetitionPeriodsList();

    if (typeof loadManagePeriodsTable === 'function') {

      loadManagePeriodsTable();

    }

  } catch (err) {

    console.error('Lỗi khởi tạo chuẩn 35 tuần:', err);

    showToast(err.message || 'Không thể chuẩn hóa khung tuần học', 'error');

  }

}



function setCompetitionPeriodType(type) {

  selectedCompetitionPeriodType = type;

  selectedCompetitionSemesterNumber = '';



  // Cập nhật giao diện nút loại kỳ

  document.querySelectorAll('.comp-type-btn').forEach(btn => {

    btn.classList.remove('bg-brand-900', 'text-white', 'shadow-xs', 'shadow-sm');

    btn.classList.add('text-slate-600', 'hover:bg-slate-200');

  });



  const activeBtn = document.getElementById(`btn-comp-type-${type.toLowerCase()}`);

  if (activeBtn) {

    activeBtn.classList.add('bg-brand-900', 'text-white', 'shadow-xs');

    activeBtn.classList.remove('text-slate-600', 'hover:bg-slate-200');

  }



  const badge = document.getElementById('period-type-badge');

  if (badge) {

    if (type === 'WEEK') badge.textContent = 'Theo Tuần (Tuần 1 - 35)';

    else if (type === 'MONTH') badge.textContent = 'Theo Tháng';

    else if (type === 'SEMESTER') badge.textContent = 'Theo Kỳ (Kỳ 1 & Kỳ 2)';

  }



  // Luôn ẩn dropdown lọc tuần theo Học kỳ để người dùng chọn trực tiếp Tuần 1 đến 35

  const semWrapper = document.getElementById('comp-semester-wrapper');

  if (semWrapper) {

    semWrapper.style.display = 'none';

    semWrapper.classList.add('hidden');

  }

  const periodLabel = document.getElementById('comp-period-select-label');

  if (periodLabel) {

    if (type === 'WEEK') periodLabel.textContent = 'Chọn tuần thi đua (Tuần 1 - 35)';

    else if (type === 'MONTH') periodLabel.textContent = 'Chọn tháng thi đua';

    else if (type === 'SEMESTER') periodLabel.textContent = 'Chọn kỳ thi đua (Kỳ 1 & Kỳ 2)';

  }



  loadCompetitionPeriodsList();

}



function onAcademicYearFilterChange() {

  const sel = document.getElementById('comp-filter-academic-year');

  if (sel) selectedAcademicYearId = sel.value;

  loadCompetitionPeriodsList();

}



function onPeriodFilterChange() {

  const sel = document.getElementById('comp-filter-period');

  if (sel) selectedPeriodId = sel.value;

  loadCompetitionScores();

}



function filterCompetitionGrade(grade) {

  selectedCompetitionGrade = grade;

  document.querySelectorAll('.comp-grade-tab').forEach(btn => {

    btn.classList.remove('bg-brand-900', 'text-white');

    btn.classList.add('text-slate-600');

  });

  if (event && event.target) {

    event.target.classList.add('bg-brand-900', 'text-white');

    event.target.classList.remove('text-slate-600');

  }

  loadCompetitionScores();

}



function debounceCompetitionSearch() {

  clearTimeout(competitionSearchTimer);

  competitionSearchTimer = setTimeout(() => {

    const input = document.getElementById('comp-search-input');

    competitionSearchQuery = input ? input.value.trim() : '';

    loadCompetitionScores();

  }, 250);

}



let _compScoresReqSeq = 0;
async function loadCompetitionScores() {
  const currentReqSeq = ++_compScoresReqSeq;

  if (!selectedPeriodId) {

    // Nếu chưa khởi tạo metadata, gọi init

    if (!competitionMeta) {

      await initCompetitionModule();

      return;

    }

    return;

  }



  const tbody = document.getElementById('competition-scores-tbody');

  try {

    tbody.innerHTML = '<tr><td colspan="11" class="text-center py-8 text-slate-400">Đang cập nhật bảng xếp hạng thi đua...</td></tr>';

    

    let url = `/api/competition/periods/${selectedPeriodId}/scores/`;

    const params = new URLSearchParams();

    if (selectedCompetitionGrade) params.append('grade', selectedCompetitionGrade);

    if (competitionSearchQuery) params.append('search', competitionSearchQuery);

    if (params.toString()) url += `?${params.toString()}`;



    const res = await fetch(url, { cache: 'no-store' });

    if (!res.ok) throw new Error('Không thể tải điểm thi đua');

    const data = await res.json();
    if (currentReqSeq !== _compScoresReqSeq) return;

    currentPeriod = data.period;



    // 1. Cập nhật tiêu đề và trạng thái kỳ

    const titleEl = document.getElementById('competition-period-title');

    if (titleEl) {

      const typeStr = currentPeriod.period_type_display || 'Thi đua';

      titleEl.innerHTML = `Kỳ thi đua: <b>${currentPeriod.name}</b> (${typeStr}) — Áp dụng: <b>${formatVNDate(currentPeriod.start_date)}</b> đến <b>${formatVNDate(currentPeriod.end_date)}</b>`;

    }



    const lockIndicator = document.getElementById('period-lock-indicator');

    const lockBtnText = document.getElementById('btn-lock-period-text');

    const resultState = data.period_status || currentPeriod.calendar_progress || {};

    const resultStateLabel = `${resultState.display || (currentPeriod.is_locked ? 'Đã chốt' : 'Tạm tính')}${resultState.requires_review ? ' · Cần rà soát' : ''}`;

    if (currentPeriod.is_locked) {

      lockIndicator.className = 'px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-100 text-rose-800 border border-rose-200';

      lockIndicator.textContent = 'Đã chốt sổ';

      if (lockBtnText) lockBtnText.textContent = 'Mở lại kỳ';

    } else if (resultState.code === 'WAITING_LOCK') {

      lockIndicator.className = 'px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200';

      lockIndicator.textContent = 'Chờ chốt';

      if (lockBtnText) lockBtnText.textContent = 'Chốt kết quả';

    } else if (resultState.code === 'NOT_STARTED') {

      lockIndicator.className = 'px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-100 text-slate-700 border border-slate-200';

      lockIndicator.textContent = 'Chưa diễn ra';

      if (lockBtnText) lockBtnText.textContent = 'Chưa đến kỳ';

    } else {

      lockIndicator.className = 'px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200';

      lockIndicator.textContent = resultStateLabel;

      if (lockBtnText) lockBtnText.textContent = 'Chốt kết quả';

    }



    // 2. Cập nhật 6 thẻ KPI tổng quan

    const sum = data.summary || {};

    const elTot = document.getElementById('comp-kpi-total-classes'); if (elTot) elTot.textContent = sum.total_classes !== undefined ? `${sum.total_classes} Chi đoàn` : '--';

    

    const topClassEl = document.getElementById('comp-kpi-top-class');

    const topScoreEl = document.getElementById('comp-kpi-top-score');

    if (sum.top_class) {

      topClassEl.textContent = `Lớp ${sum.top_class.class_name}`;

      topScoreEl.textContent = `Điểm: ${parseFloat(sum.top_class.total_score).toFixed(1)}đ (Hạng #1)`;

    } else {

      topClassEl.textContent = 'Chưa có';

      topScoreEl.textContent = '--';

    }



    const elHigh = document.getElementById('comp-kpi-highest-score'); if (elHigh) elHigh.textContent = sum.highest_score !== null ? `${parseFloat(sum.highest_score).toFixed(1)}đ` : '--';

    

    const trendEl = document.getElementById('comp-kpi-trend');

    if (sum.improved_classes_count !== undefined) {

      trendEl.innerHTML = `<span class="text-emerald-700 font-bold">${sum.improved_classes_count} tăng</span> / <span class="text-rose-600 font-bold">${sum.worsened_classes_count} giảm</span>`;

    } else {

      trendEl.textContent = '--';

    }



    const elVio = document.getElementById('comp-kpi-violations'); if (elVio) elVio.textContent = sum.total_violations_in_period !== undefined ? `${sum.total_violations_in_period} lượt` : '0 lượt';

    

    const statusEl = document.getElementById('comp-kpi-status');

    const updateTimeEl = document.getElementById('comp-kpi-updated-time');

    if (sum.is_locked) {

      statusEl.innerHTML = '<span class="text-rose-700 font-bold">Đã chốt sổ 🔒</span>';

      updateTimeEl.textContent = sum.locked_at ? `Chốt lúc: ${sum.locked_at}` : 'Đã chốt kết quả';

    } else {

      statusEl.textContent = `Trạng thái: ${resultStateLabel}`;

      updateTimeEl.textContent = sum.last_updated ? `Cập nhật: ${sum.last_updated}` : 'Dữ liệu thời gian thực';

    }



    // 3. Renders bảng điểm

    const scores = data.scores || [];

    if (scores.length === 0) {

      const emptyMessage = resultState.code === 'NOT_STARTED'

        ? 'Kỳ thi đua chưa diễn ra; chưa có kết quả để xếp hạng.'

        : (currentPeriod.period_type !== 'WEEK' && resultState.included_weeks === 0

          ? 'Chưa có tuần nào được chốt trong kỳ này.'

          : 'Chưa có kết quả phù hợp với phạm vi và bộ lọc hiện tại.');

      tbody.innerHTML = `<tr><td colspan="11" class="text-center py-8 text-slate-400">${escapeHtml(emptyMessage)}</td></tr>`;

      return;

    }



    tbody.innerHTML = scores.map(s => {

      // Huy hiệu thứ hạng top 1, 2, 3

      let rankDisplay = `<span class="font-bold text-slate-700">#${s.rank}</span>`;

      if (s.rank === 1) {

        rankDisplay = `

          <div class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-amber-100 text-amber-800 font-black text-xs shadow-xs border border-amber-300">

            🥇 1

          </div>

        `;

      } else if (s.rank === 2) {

        rankDisplay = `

          <div class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-slate-100 text-slate-700 font-black text-xs shadow-xs border border-slate-300">

            🥈 2

          </div>

        `;

      } else if (s.rank === 3) {

        rankDisplay = `

          <div class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-amber-50 text-amber-900 font-black text-xs shadow-xs border border-amber-200">

            🥉 3

          </div>

        `;

      }



      // Biến động thứ hạng so với kỳ trước tương ứng

      let trendDisplay = '';

      if (!s.has_comparison) {

        trendDisplay = '<span class="text-slate-400 italic text-[11px]">Chưa có dữ liệu so sánh</span>';

      } else if (s.rank_change > 0) {

        trendDisplay = `<span class="inline-flex items-center text-emerald-700 font-bold font-mono bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200/60">+${s.rank_change} ▲</span>`;

      } else if (s.rank_change < 0) {

        trendDisplay = `<span class="inline-flex items-center text-rose-700 font-bold font-mono bg-rose-50 px-2 py-0.5 rounded-md border border-rose-200/60">${s.rank_change} ▼</span>`;

      } else {

        trendDisplay = '<span class="text-slate-500 font-mono text-[11px] font-semibold bg-slate-100 px-2 py-0.5 rounded-md">0 (Giữ nguyên)</span>';

      }



      return `

        <tr class="hover:bg-slate-50 transition border-b border-slate-100">

          <td class="py-3 px-3 text-center">${rankDisplay}</td>

          <td class="py-3 px-3">

            <button onclick="openClassCompetitionDetailModal(${s.school_class})" class="font-bold text-slate-900 hover:text-brand-700 hover:underline flex items-center space-x-1 text-left">

              <span>Chi đoàn ${s.class_name}</span>

              <i data-lucide="chevron-right" class="w-3.5 h-3.5 text-slate-400"></i>

            </button>

          </td>

          <td class="py-3 px-3 text-slate-500">Khối ${s.grade}</td>

          <td class="py-3 px-3 text-slate-600">${s.homeroom_teacher_name || 'Chưa phân công'}</td>

          <td class="py-3 px-3 text-right font-mono text-slate-600">${parseFloat(s.base_points).toFixed(1)}</td>

          <td class="py-3 px-3 text-right font-mono text-emerald-600 font-semibold">${parseFloat(s.bonus_points) > 0 ? `+${parseFloat(s.bonus_points).toFixed(1)}` : '0.0'}</td>

          <td class="py-3 px-3 text-right font-mono text-rose-600 font-semibold">${parseFloat(s.penalty_points) > 0 ? `-${parseFloat(s.penalty_points).toFixed(1)}` : '0.0'}</td>

          <td class="py-3 px-3 text-right font-mono font-black text-brand-900 text-sm">${parseFloat(s.total_score).toFixed(1)}đ</td>

          <td class="py-3 px-3 text-center font-mono text-slate-700">${s.verified_violations_count}</td>

          <td class="py-3 px-3 text-center">${trendDisplay}</td>

          <td class="py-3 px-3 text-right space-x-1 whitespace-nowrap">

            <button onclick="openClassCompetitionDetailModal(${s.school_class})" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-[11px] font-semibold transition">Chi tiết</button>

            ${currentUser && currentUser.role === 'ADMIN' && !currentPeriod.is_locked ? `

              <button onclick="openBonusModal(${s.id}, '${s.class_name}')" class="px-2 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-lg text-[11px] font-semibold transition">+ Cộng điểm</button>

            ` : ''}

          </td>

        </tr>

      `;

    }).join('');



    lucide.createIcons();

  } catch (err) {

    tbody.innerHTML = '<tr><td colspan="11" class="text-center py-8 text-rose-500">Lỗi tải dữ liệu bảng xếp hạng thi đua.</td></tr>';

  }

}



function renderEmptyCompetitionTable(msg) {

  const tbody = document.getElementById('competition-scores-tbody');

  if (tbody) {

    tbody.innerHTML = `<tr><td colspan="11" class="text-center py-8 text-slate-400">${msg}</td></tr>`;

  }

  const titleEl = document.getElementById('competition-period-title');

  if (titleEl) titleEl.textContent = msg;

}



function formatVNDate(dateStr) {

  if (!dateStr) return '';

  const parts = dateStr.split('-');

  if (parts.length === 3) return `${parts[2]}/${parts[1]}/${parts[0]}`;

  return dateStr;

}



function printCompetitionRanking() {

  const printContent = document.getElementById('tab-competition');

  if (!printContent) return;

  window.print();

}



// ==========================================

// MODAL: CHI TIẾT THI ĐUA LỚP

// ==========================================

let currentDetailClassId = null;



async function openClassCompetitionDetailModal(classId) {

  if (!selectedPeriodId) return;

  currentDetailClassId = classId;



  try {

    const res = await fetch(`/api/competition/periods/${selectedPeriodId}/classes/${classId}/detail/`);

    if (!res.ok) {

      const err = await res.json();

      showToast(err.error || 'Bạn không có quyền xem chi tiết lớp này', 'error');

      return;

    }

    const data = await res.json();



    // Điền tiêu đề & thông tin lớp

    document.getElementById('modal-class-detail-title').textContent = `Hồ sơ thi đua Chi đoàn ${data.school_class.name}`;

    document.getElementById('modal-class-detail-subtitle').textContent = `Kỳ tổng kết: ${data.period.name} (${data.period.period_type_display})`;

    document.getElementById('modal-class-detail-gvcn').textContent = data.school_class.homeroom_teacher || 'Chưa phân công';

    document.getElementById('modal-class-detail-rank-grade').textContent = data.score.rank_in_grade

      ? `#${data.score.rank_in_grade} (Khối ${data.school_class.grade})`

      : `Chưa xếp hạng (Khối ${data.school_class.grade})`;



    let trendStr = '<span class="text-slate-400 font-normal">Chưa có dữ liệu so sánh</span>';

    if (data.score.rank_change !== null) {

      if (data.score.rank_change > 0) trendStr = `<span class="text-emerald-600 font-bold">+${data.score.rank_change} bậc ▲ (Tiến bộ)</span>`;

      else if (data.score.rank_change < 0) trendStr = `<span class="text-rose-600 font-bold">${data.score.rank_change} bậc ▼</span>`;

      else trendStr = '<span class="text-slate-600 font-bold">0 (Ổn định)</span>';

    }

    document.getElementById('modal-class-detail-trend').innerHTML = trendStr;



    // Điền 4 thẻ KPI

    document.getElementById('modal-class-kpi-base').textContent = data.score.base_points === null ? '—' : `${Number(data.score.base_points).toFixed(1)}đ`;

    document.getElementById('modal-class-kpi-bonus').textContent = `+${Number(data.score.bonus_points || 0).toFixed(1)}đ`;

    document.getElementById('modal-class-kpi-penalty').textContent = `-${Number(data.score.penalty_points || 0).toFixed(1)}đ`;

    document.getElementById('modal-class-kpi-violations-count').textContent = `${data.score.verified_violations_count} vi phạm`;

    document.getElementById('modal-class-kpi-total').textContent = data.score.total_score === null ? 'Chưa có kết quả' : `${Number(data.score.total_score).toFixed(1)}đ`;

    document.getElementById('modal-class-kpi-rank').textContent = data.score.rank ? `Hạng #${data.score.rank} Toàn trường` : 'Chưa xếp hạng';



    // 1. Tab sự kiện điểm trong kỳ

    const eventsContainer = document.getElementById('modal-class-events-list');

    const events = data.events || [];

    if (events.length === 0 && data.score.bonus_points === 0) {

      eventsContainer.innerHTML = '<div class="p-4 bg-emerald-50/60 rounded-xl border border-emerald-100 text-emerald-800 text-center text-xs font-semibold">🌟 Tuyệt vời! Chi đoàn giữ nền nếp chuẩn mực, không có vi phạm nào trong kỳ.</div>';

    } else {

      let eventsHtml = '';

      if (data.score.bonus_points > 0) {

        eventsHtml += `

          <div class="p-3 bg-emerald-50/70 rounded-xl border border-emerald-100 flex items-start justify-between">

            <div>

              <div class="font-bold text-emerald-900 flex items-center gap-1.5">

                <i data-lucide="plus-circle" class="w-4 h-4 text-emerald-600"></i>

                <span>Cộng điểm phong trào Đoàn trường</span>

              </div>

              <p class="text-slate-600 mt-1 whitespace-pre-line text-[11px]">${escapeHtml(data.score.bonus_notes || 'Khoản điểm cộng cũ; cần rà soát chi tiết.').replace(/\n/g, '<br>')}</p>

            </div>

            <span class="font-mono font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-md text-xs">+${data.score.bonus_points.toFixed(1)}đ</span>

          </div>

        `;

      }



      eventsHtml += events.map(ev => {

        if (ev.event_type === 'SCORE_ADJUSTMENT') {

          const amount = Number(ev.amount || 0);

          const positive = amount >= 0;

          const palette = positive

            ? { panel: 'bg-emerald-50/70 border-emerald-100', title: 'text-emerald-900', badge: 'text-emerald-700 border-emerald-200/50', amount: 'text-emerald-700' }

            : { panel: 'bg-rose-50/70 border-rose-100', title: 'text-rose-900', badge: 'text-rose-700 border-rose-200/50', amount: 'text-rose-700' };

          return `

            <div class="p-3 ${palette.panel} rounded-xl border flex items-start justify-between">

              <div>

                <div class="flex items-center gap-2">

                  <span class="font-bold ${palette.title}">Điều chỉnh điểm thi đua</span>

                  <span class="px-1.5 py-0.5 bg-white ${palette.badge} rounded font-mono text-[10px] font-semibold border">${escapeHtml(ev.record_code)}</span>

                </div>

                <p class="text-slate-700 mt-1 text-[11px] whitespace-pre-line">${escapeHtml(ev.reason)}</p>

                <div class="text-[10px] text-slate-500 mt-0.5">${escapeHtml(ev.time)} · Ghi nhận: ${escapeHtml(ev.created_by_name)} · Duyệt: ${escapeHtml(ev.approved_by_name)}</div>

              </div>

              <span class="font-mono font-bold ${palette.amount} bg-white px-2 py-0.5 rounded-md text-xs whitespace-nowrap ml-2">${positive ? '+' : '−'}${Math.abs(amount).toFixed(1)}đ</span>

            </div>

          `;

        }

        return `

          <div class="p-3 bg-white rounded-xl border border-slate-200 flex items-start justify-between">

            <div>

              <div class="flex items-center gap-2">

                <span class="font-bold text-slate-800">${escapeHtml(ev.rule_name)}</span>

                <span class="px-1.5 py-0.5 bg-rose-50 text-rose-700 rounded font-mono text-[10px] font-semibold border border-rose-200/50">${escapeHtml(ev.record_code)}</span>

              </div>

              <div class="text-slate-600 mt-1 text-[11px]">

                <span>Đối tượng: <b>${escapeHtml(ev.student_name)}</b></span>

                ${ev.location ? ` • <span>Vị trí: ${escapeHtml(ev.location)}</span>` : ''}

                • <span>Thời gian: ${escapeHtml(ev.time)}</span>

              </div>

              <div class="text-[10px] text-slate-400 mt-0.5">Người ghi nhận: ${escapeHtml(ev.reporter_name)} • Trạng thái: <b class="text-emerald-700">${escapeHtml(ev.status)}</b></div>

            </div>

            <span class="font-mono font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded-md text-xs whitespace-nowrap ml-2">-${Number(ev.points_deducted || 0).toFixed(1)}đ</span>

          </div>

        `;

      }).join('');

      eventsContainer.innerHTML = eventsHtml;

    }



    // 2. Tab lịch sử tiến trình qua các kỳ

    const historyTbody = document.getElementById('modal-class-history-tbody');

    const hist = data.history || [];

    if (hist.length === 0) {

      historyTbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-slate-400">Chưa có lịch sử các kỳ trước.</td></tr>';

    } else {

      historyTbody.innerHTML = hist.map(h => {

        let trend = '<span class="text-slate-400">--</span>';

        if (h.rank_change !== null) {

          if (h.rank_change > 0) trend = `<span class="text-emerald-600 font-bold">+${h.rank_change} ▲</span>`;

          else if (h.rank_change < 0) trend = `<span class="text-rose-600 font-bold">${h.rank_change} ▼</span>`;

          else trend = '<span class="text-slate-500 font-bold">0</span>';

        }

        return `

          <tr class="${h.is_current ? 'bg-blue-50/70 font-semibold' : 'hover:bg-slate-50'}">

            <td class="py-2.5 px-3 font-medium text-slate-900">${h.period_name} ${h.is_current ? '<span class="text-[10px] bg-brand-100 text-brand-800 px-1.5 py-0.5 rounded font-bold ml-1">Đang xem</span>' : ''}</td>

            <td class="py-2.5 px-3 text-right font-mono font-bold text-brand-900">${h.total_score.toFixed(1)}đ</td>

            <td class="py-2.5 px-3 text-center font-bold text-slate-700">#${h.rank}</td>

            <td class="py-2.5 px-3 text-center text-slate-600">#${h.rank_in_grade}</td>

            <td class="py-2.5 px-3 text-center font-mono">${trend}</td>

            <td class="py-2.5 px-3 text-center">

              ${h.is_locked ? '<span class="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-[10px] font-bold">Chốt sổ</span>' : '<span class="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded text-[10px] font-bold">Đang mở</span>'}

            </td>

          </tr>

        `;

      }).join('');

    }



    switchClassDetailTab('events');

    document.getElementById('modal-class-competition-detail').classList.remove('hidden');

    lucide.createIcons();

  } catch (err) {

    showToast('Lỗi hiển thị chi tiết thi đua của lớp', 'error');

  }

}



function switchClassDetailTab(tab) {

  const btnEvents = document.getElementById('btn-tab-class-events');

  const btnHistory = document.getElementById('btn-tab-class-history');

  const paneEvents = document.getElementById('class-detail-pane-events');

  const paneHistory = document.getElementById('class-detail-pane-history');



  if (tab === 'events') {

    btnEvents.className = 'px-3.5 py-1.5 text-xs font-bold border-b-2 border-brand-900 text-brand-900';

    btnHistory.className = 'px-3.5 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-800';

    paneEvents.classList.remove('hidden');

    paneHistory.classList.add('hidden');

  } else {

    btnHistory.className = 'px-3.5 py-1.5 text-xs font-bold border-b-2 border-brand-900 text-brand-900';

    btnEvents.className = 'px-3.5 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-800';

    paneHistory.classList.remove('hidden');

    paneEvents.classList.add('hidden');

  }

}



function closeClassCompetitionDetailModal() {

  document.getElementById('modal-class-competition-detail').classList.add('hidden');

}



// ==========================================

// MODAL: QUẢN LÝ KỲ THI ĐUA (ADMIN / ĐOÀN TRƯỜNG)

// ==========================================

async function openManagePeriodsModal() {

  const modal = document.getElementById('modal-manage-periods');

  modal.classList.remove('hidden');



  populateCompetitionFiltersMeta();

  await loadManagePeriodsTable();

  lucide.createIcons();

}



function closeManagePeriodsModal() {

  document.getElementById('modal-manage-periods').classList.add('hidden');

}



function onNewPeriodTypeChange() {

  const type = document.getElementById('new-period-type').value;

  const numContainer = document.getElementById('new-period-number-container');

  const numLabel = document.getElementById('new-period-number-label');

  const nameInput = document.getElementById('new-period-name');



  if (type === 'WEEK') {

    numContainer.classList.remove('hidden');

    numLabel.textContent = 'Số thứ tự tuần';

    nameInput.placeholder = 'VD: Tuần 9 - Học kỳ I (2026-2027)';

  } else if (type === 'MONTH') {

    numContainer.classList.remove('hidden');

    numLabel.textContent = 'Số tháng (1-12)';

    nameInput.placeholder = 'VD: Thi đua Tháng 11/2026';

  } else {

    numContainer.classList.add('hidden');

    nameInput.placeholder = 'VD: Thi đua Học kỳ II (2026-2027)';

  }

}



async function loadManagePeriodsTable() {

  const tbody = document.getElementById('manage-periods-tbody');

  try {

    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-slate-400">Đang tải danh sách kỳ...</td></tr>';

    const res = await fetch('/api/competition/periods/');

    if (!res.ok) throw new Error('Lỗi tải danh sách');

    const periods = await res.json();



    if (periods.length === 0) {

      tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-slate-400">Chưa có kỳ nào.</td></tr>';

      return;

    }



    tbody.innerHTML = periods.map(p => {

      let typeBadge = '<span class="px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-semibold text-[10px]">Tuần</span>';

      if (p.period_type === 'MONTH') typeBadge = '<span class="px-2 py-0.5 rounded bg-amber-50 text-amber-700 font-semibold text-[10px]">Tháng</span>';

      else if (p.period_type === 'SEMESTER') typeBadge = '<span class="px-2 py-0.5 rounded bg-purple-50 text-purple-700 font-semibold text-[10px]">Học kỳ</span>';



      return `

        <tr class="hover:bg-slate-50 border-b border-slate-100">

          <td class="py-2.5 px-3">${typeBadge}</td>

          <td class="py-2.5 px-3 font-semibold text-slate-900">${p.name}</td>

          <td class="py-2.5 px-3 text-slate-500 font-mono text-[11px]">${formatVNDate(p.start_date)} &rarr; ${formatVNDate(p.end_date)}</td>

          <td class="py-2.5 px-3 text-center">

            ${p.is_locked ? '<span class="px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 font-bold text-[10px]">🔒 Đã chốt</span>' : '<span class="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold text-[10px]">🟢 Đang mở</span>'}

          </td>

          <td class="py-2.5 px-3 text-right space-x-1 whitespace-nowrap">

            <button onclick="quickSelectPeriod(${p.id}, '${p.period_type}')" class="px-2 py-1 bg-brand-50 hover:bg-brand-100 text-brand-700 rounded font-semibold text-[11px]">Xem</button>

            <button onclick="toggleLockSpecificPeriod(${p.id}, ${p.is_locked})" class="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded font-semibold text-[11px]">${p.is_locked ? 'Mở lại' : 'Chốt kỳ'}</button>

            ${!p.is_locked && currentUser && currentUser.role === 'ADMIN' ? `

              <button onclick="deleteCompetitionPeriod(${p.id}, '${p.name}')" class="px-2 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded font-semibold text-[11px]">Xóa</button>

            ` : ''}

          </td>

        </tr>

      `;

    }).join('');

  } catch (err) {

    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-rose-500">Lỗi tải danh sách kỳ thi đua.</td></tr>';

  }

}



async function quickSelectPeriod(periodId, periodType) {

  closeManagePeriodsModal();

  selectedCompetitionPeriodType = periodType;

  selectedCompetitionSemesterNumber = '';



  document.querySelectorAll('.comp-type-btn').forEach(btn => {

    btn.classList.remove('bg-brand-900', 'text-white', 'shadow-xs', 'shadow-sm');

    btn.classList.add('text-slate-600', 'hover:bg-slate-200');

  });

  const activeBtn = document.getElementById(`btn-comp-type-${periodType.toLowerCase()}`);

  if (activeBtn) {

    activeBtn.classList.add('bg-brand-900', 'text-white', 'shadow-xs');

    activeBtn.classList.remove('text-slate-600', 'hover:bg-slate-200');

  }



  const periodLabel = document.getElementById('comp-period-select-label');

  if (periodLabel) {

    if (periodType === 'WEEK') periodLabel.textContent = 'Chọn tuần thi đua (Tuần 1 - 35)';

    else if (periodType === 'MONTH') periodLabel.textContent = 'Chọn tháng thi đua';

    else if (periodType === 'SEMESTER') periodLabel.textContent = 'Chọn kỳ thi đua (Kỳ 1 & Kỳ 2)';

  }



  await loadCompetitionPeriodsList(periodId);

}



async function handleCreatePeriodSubmit(e) {

  e.preventDefault();

  const periodType = document.getElementById('new-period-type').value;

  const academicYear = document.getElementById('new-period-academic-year').value;

  const semester = document.getElementById('new-period-semester').value || null;

  const name = document.getElementById('new-period-name').value.trim();

  const numVal = parseInt(document.getElementById('new-period-number').value || 0, 10);

  const startDate = document.getElementById('new-period-start-date').value;

  const endDate = document.getElementById('new-period-end-date').value;



  if (endDate < startDate) {

    showToast('Ngày kết thúc không được sớm hơn ngày bắt đầu', 'error');

    return;

  }



  const payload = {

    period_type: periodType,

    academic_year: academicYear,

    semester: semester,

    name: name,

    start_date: startDate,

    end_date: endDate

  };

  if (periodType === 'WEEK' && numVal) payload.week_number = numVal;

  if (periodType === 'MONTH' && numVal) payload.month_number = numVal;



  try {

    const res = await fetch('/api/competition/periods/', {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken')

      },

      body: JSON.stringify(payload)

    });

    const data = await res.json();

    if (res.ok) {

      showToast(`Đã tạo kỳ thi đua [${name}] và khởi tạo bảng điểm các lớp thành công!`, 'success');

      document.getElementById('form-create-period').reset();

      await loadManagePeriodsTable();

      await loadCompetitionPeriodsList(data.id);

    } else {

      showToast(data.error || data.detail || 'Lỗi tạo kỳ thi đua', 'error');

    }

  } catch (err) {

    showToast('Lỗi kết nối máy chủ', 'error');

  }

}



async function toggleLockSpecificPeriod(periodId, isCurrentlyLocked) {

  const action = isCurrentlyLocked ? 'unlock' : 'lock';

  try {

    const res = await fetch(`/api/competition/periods/${periodId}/${action}/`, {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken')

      }

    });

    const data = await res.json();

    if (res.ok) {

      showToast(data.message, 'success');

      await loadManagePeriodsTable();

      if (selectedPeriodId == periodId) {

        await loadCompetitionScores();

      }

    } else {

      showToast(data.error || 'Lỗi thao tác chốt kỳ', 'error');

    }

  } catch (err) {

    showToast('Lỗi kết nối máy chủ', 'error');

  }

}



async function deleteCompetitionPeriod(periodId, periodName) {

  if (!confirm(`Bạn có chắc chắn muốn xóa kỳ thi đua [${periodName}]? Dữ liệu điểm sẽ bị xóa hoàn toàn.`)) return;



  try {

    const res = await fetch(`/api/competition/periods/${periodId}/`, {

      method: 'DELETE',

      headers: {

        'X-CSRFToken': getCookie('csrftoken')

      }

    });

    if (res.ok || res.status === 204) {

      showToast(`Đã xóa kỳ thi đua [${periodName}] thành công`, 'success');

      await loadManagePeriodsTable();

      await loadCompetitionPeriodsList();

    } else {

      const data = await res.json();

      showToast(data.detail || data.error || 'Không thể xóa kỳ thi đua', 'error');

    }

  } catch (err) {

    showToast('Lỗi kết nối máy chủ', 'error');

  }

}



async function recalculateScores() {

  if (!selectedPeriodId) return;

  try {

    const res = await fetch(`/api/competition/periods/${selectedPeriodId}/recalculate/`, {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken')

      },

      body: JSON.stringify({ force: true })

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

  if (!selectedPeriodId || !currentPeriod) return;

  const action = currentPeriod.is_locked ? 'unlock' : 'lock';

  try {

    const res = await fetch(`/api/competition/periods/${selectedPeriodId}/${action}/`, {

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



let currentBonusIdempotencyKey = null;

function openBonusModal(scoreId, className) {

  currentBonusIdempotencyKey = window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;

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

      body: JSON.stringify({ bonus_points: bonus, note, idempotency_key: currentBonusIdempotencyKey })

    });

    const data = await res.json();

    if (res.ok) {

      showToast(data.message, 'success');

      currentBonusIdempotencyKey = null;

      closeBonusModal();

      loadCompetitionScores();

    } else {

      showToast(data.error || 'Lỗi cộng điểm', 'error');

    }

  } catch (err) {

    showToast('Lỗi kết nối', 'error');

  }

}



function exportCompetitionExcel(periodId) {

  const selectEl = document.getElementById('comp-filter-period');
  const pid = periodId || (selectEl && selectEl.value ? selectEl.value : null) || selectedPeriodId || (typeof currentPeriod !== 'undefined' && currentPeriod?.id);

  if (!pid) { showToast('Hãy chọn kỳ thi đua trước khi xuất báo cáo.', 'error'); return; }

  window.open(`/api/reports/competition/excel/${pid}/`, '_blank');

  showToast('Đang tạo và tải tệp Excel thi đua...', 'info');

}



function exportCompetitionPdf(periodId) {

  const selectEl = document.getElementById('comp-filter-period');
  const pid = periodId || (selectEl && selectEl.value ? selectEl.value : null) || selectedPeriodId || (typeof currentPeriod !== 'undefined' && currentPeriod?.id);

  if (!pid) { showToast('Hãy chọn kỳ thi đua trước khi xuất báo cáo.', 'error'); return; }

  window.open(`/api/reports/competition/pdf/${pid}/`, '_blank');

  showToast('Đang tạo và tải tệp PDF thi đua (Times New Roman)...', 'info');

}



function exportViolationsExcel() {

  const classId = document.getElementById('filter-conduct-class')?.value || '';

  const status = document.getElementById('filter-conduct-status')?.value || '';

  const params = new URLSearchParams();

  if (classId) params.append('class_id', classId);

  if (status) params.append('status', status);

  const qs = params.toString() ? `?${params.toString()}` : '';

  window.open(`/api/reports/violations/excel/${qs}`, '_blank');

  showToast('Đang tạo và tải danh sách vi phạm Excel...', 'info');

}



function exportViolationsPdf() {

  const classId = document.getElementById('filter-conduct-class')?.value || '';

  const status = document.getElementById('filter-conduct-status')?.value || '';

  const params = new URLSearchParams();

  if (classId) params.append('class_id', classId);

  if (status) params.append('status', status);

  const qs = params.toString() ? `?${params.toString()}` : '';

  window.open(`/api/reports/violations/pdf/${qs}`, '_blank');

  showToast('Đang tạo và tải danh sách vi phạm PDF (Times New Roman)...', 'info');

}



function exportViolationRecordPdf(violationId) {

  const vid = violationId || currentDetailViolationId;

  if (!vid) {

    showToast('Không xác định được bản ghi vi phạm', 'error');

    return;

  }

  window.open(`/api/reports/violations/${vid}/pdf/`, '_blank');

  showToast('Đang tạo và tải biên bản vi phạm PDF (Times New Roman)...', 'info');

}



function exportCurrentViolationPdf() {

  exportViolationRecordPdf(currentDetailViolationId);

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

let currentAdminFilter = 'ALL';



async function loadUsersManagement() {

  const tbody = document.getElementById('user-management-tbody');

  const canManage = currentUser && (

    currentUser.is_admin ||

    currentUser.is_super_admin ||

    currentUser.role === 'ADMIN' ||

    currentUser.role === 'SUPER_ADMIN' ||

    currentUser.role === 'DOAN_TRUONG' ||

    currentUser.is_doan_truong

  );

  if (!canManage) {

    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-rose-500 font-semibold">Chỉ Quản trị viên hệ thống (Admin) hoặc Đoàn trường mới có quyền truy cập trang quản lý tài khoản.</td></tr>';

    return;

  }



  try {

    // 1. Fetch Stats for 5 KPI cards

    const statsRes = await fetch('/api/core/users/stats/');

    if (statsRes.ok) {

      const stats = await statsRes.json();

      const elTotal = document.getElementById('admin-stat-total');

      const elPending = document.getElementById('admin-stat-pending');

      const elApproved = document.getElementById('admin-stat-approved');

      const elRejected = document.getElementById('admin-stat-rejected');

      const elSuspended = document.getElementById('admin-stat-suspended');

      const elBadgePending = document.getElementById('badge-filter-pending');



      if (elTotal) elTotal.textContent = stats.total ?? 0;

      if (elPending) elPending.textContent = stats.pending ?? 0;

      if (elApproved) elApproved.textContent = stats.approved ?? 0;

      if (elRejected) elRejected.textContent = stats.rejected ?? 0;

      if (elSuspended) elSuspended.textContent = stats.suspended ?? 0;

      if (elBadgePending) elBadgePending.textContent = stats.pending ?? 0;

    }



    // 2. Fetch Users List

    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-slate-400">Đang tải danh sách tài khoản...</td></tr>';

    const res = await fetch('/api/core/users/');

    if (res.status === 403) {

      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-rose-500 font-semibold">Bị từ chối: Chỉ có Admin mới được duyệt tài khoản và chức vụ.</td></tr>';

      return;

    }



    const data = await res.json();

    allUsersCache = data.results || data;

    applyUsersFilter();

  } catch (err) {

    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-rose-500">Lỗi tải dữ liệu người dùng.</td></tr>';

  }

}



function setAdminUsersFilter(status) {

  currentAdminFilter = status;

  const filterBtns = {

    'ALL': 'filter-btn-all',

    'PENDING': 'filter-btn-pending',

    'APPROVED': 'filter-btn-approved',

    'REJECTED': 'filter-btn-rejected',

    'SUSPENDED': 'filter-btn-suspended'

  };



  Object.entries(filterBtns).forEach(([key, btnId]) => {

    const el = document.getElementById(btnId);

    if (!el) return;

    if (key === status) {

      el.className = 'admin-tab-btn px-3 py-1.5 rounded-xl bg-brand-900 text-white font-semibold transition';

    } else {

      el.className = 'admin-tab-btn px-3 py-1.5 rounded-xl bg-slate-100 text-slate-600 hover:bg-slate-200 font-semibold transition';

    }

  });



  applyUsersFilter();

}



function applyUsersFilter() {

  const reqRoleVal = document.getElementById('filter-user-req-role')?.value || '';

  const searchVal = (document.getElementById('filter-user-search')?.value || '').toLowerCase().trim();



  let filtered = allUsersCache;



  // Filter by status tab

  if (currentAdminFilter !== 'ALL') {

    filtered = filtered.filter(u => u.account_status === currentAdminFilter);

  }



  // Filter by requested role or assigned role

  if (reqRoleVal) {

    filtered = filtered.filter(u => u.requested_role === reqRoleVal || u.role === reqRoleVal);

  }



  // Filter by search query

  if (searchVal) {

    filtered = filtered.filter(u =>

      (u.full_name && u.full_name.toLowerCase().includes(searchVal)) ||

      (u.username && u.username.toLowerCase().includes(searchVal)) ||

      (u.email && u.email.toLowerCase().includes(searchVal)) ||

      (u.department_or_class && u.department_or_class.toLowerCase().includes(searchVal)) ||

      (u.verification_info && u.verification_info.toLowerCase().includes(searchVal))

    );

  }



  renderUsersTable(filtered);

}



function renderUsersTable(users) {

  const tbody = document.getElementById('user-management-tbody');

  if (!users || users.length === 0) {

    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-slate-400">Không tìm thấy tài khoản nào phù hợp bộ lọc.</td></tr>';

    return;

  }



  const roleColors = {

    SUPER_ADMIN: 'bg-rose-100 text-rose-900 border-rose-300 font-bold',

    ADMIN: 'bg-purple-100 text-purple-800 border-purple-200',

    BGH: 'bg-blue-100 text-brand-800 border-blue-200',

    DOAN_TRUONG: 'bg-emerald-100 text-emerald-800 border-emerald-200',

    SAO_DO: 'bg-amber-100 text-amber-800 border-amber-200',

    GVCN: 'bg-sky-100 text-sky-800 border-sky-200',

    GVBM: 'bg-slate-100 text-slate-700 border-slate-200',

    HOC_SINH: 'bg-slate-100 text-slate-800 border-slate-200',

    CHUYEN_VIEN_TAM_LY: 'bg-pink-100 text-pink-800 border-pink-200',

  };



  const statusBadges = {

    PENDING: '<span class="badge bg-amber-100 text-amber-800 border border-amber-300 font-semibold">Chờ duyệt</span>',

    APPROVED: '<span class="badge bg-emerald-100 text-emerald-800 border border-emerald-300 font-semibold">Đã duyệt</span>',

    REJECTED: '<span class="badge bg-rose-100 text-rose-800 border border-rose-300 font-semibold">Bị từ chối</span>',

    SUSPENDED: '<span class="badge bg-purple-100 text-purple-800 border border-purple-300 font-semibold">Tạm khóa</span>',

    DISABLED: '<span class="badge bg-slate-100 text-slate-600 border border-slate-300">Vô hiệu hóa</span>'

  };



  tbody.innerHTML = users.map(u => {

    const isPending = u.account_status === 'PENDING';

    const isApproved = u.account_status === 'APPROVED';

    const isRejected = u.account_status === 'REJECTED';

    const isSuspended = u.account_status === 'SUSPENDED';



    let actionBtns = `

      <div class="flex items-center justify-end gap-1.5 flex-wrap">

        <button type="button" onclick="openUserDetailModal(${u.id})" class="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-[11px] font-semibold transition" title="Xem hồ sơ và lịch sử xét duyệt">

          Chi tiết

        </button>

    `;



    if (isPending) {

      actionBtns += `

        <button type="button" onclick="openReviewModal(${u.id}, 'approve')" class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-[11px] font-semibold transition shadow-sm">

          Phê duyệt

        </button>

        <button type="button" onclick="openReviewModal(${u.id}, 'reject')" class="px-2 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-[11px] font-semibold transition">

          Từ chối

        </button>

        <button type="button" onclick="openReviewModal(${u.id}, 'request_info')" class="px-2 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-[11px] font-semibold transition">

          Bổ sung

        </button>

      `;

    } else if (isApproved) {

      actionBtns += `

        <button type="button" onclick="openReviewModal(${u.id}, 'approve')" class="px-2 py-1 bg-blue-50 text-brand-700 hover:bg-blue-100 border border-blue-200 rounded-lg text-[11px] font-semibold transition">

          Đổi quyền

        </button>

        <button type="button" onclick="openReviewModal(${u.id}, 'suspend')" class="px-2 py-1 bg-slate-100 text-slate-700 hover:bg-rose-50 hover:text-rose-700 rounded-lg text-[11px] font-medium transition">

          Tạm khóa

        </button>

      `;

    } else if (isSuspended) {

      actionBtns += `

        <button type="button" onclick="openReviewModal(${u.id}, 'reactivate')" class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-[11px] font-semibold transition">

          Mở khóa

        </button>

      `;

    } else if (isRejected) {

      actionBtns += `

        <button type="button" onclick="openReviewModal(${u.id}, 'approve')" class="px-2 py-1 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-[11px] font-semibold transition">

          Duyệt lại

        </button>

      `;

    }



    const canDeleteUser = (typeof isAdminUser === 'function')
      ? isAdminUser(currentUser)
      : Boolean(currentUser && (currentUser.is_admin || currentUser.is_super_admin || currentUser.is_superuser || currentUser.role === 'ADMIN' || currentUser.role === 'SUPER_ADMIN'));
    if (canDeleteUser && String(u.id) !== String(currentUser?.id)) {
      actionBtns += `
        <button type="button" onclick="confirmDeleteUser(${u.id}, '${escapeHtml(u.username)}', '${escapeHtml(u.full_name || u.username)}')" class="px-2 py-1 bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 rounded-lg text-[11px] font-semibold transition" title="Xóa tài khoản vĩnh viễn">
          Xóa
        </button>
      `;
    }

    actionBtns += '</div>';



    return `

      <tr class="hover:bg-slate-50 transition border-b border-slate-100">

        <td class="py-3 px-3">

          <div class="font-bold text-slate-900">${escapeHtml(u.full_name || u.username)}</div>

          <div class="text-[11px] text-slate-500 font-mono">${escapeHtml(u.email || 'Chưa có email')}</div>

          ${u.phone ? `<div class="text-[10px] text-slate-400 font-mono">SĐT: ${escapeHtml(u.phone)}</div>` : ''}

        </td>

        <td class="py-3 px-3 font-mono font-medium text-slate-700">

          ${escapeHtml(u.username)}

          ${u.is_super_admin ? '<span class="ml-1 text-[9px] px-1 py-0.2 rounded bg-rose-50 text-rose-700 border border-rose-200 font-bold">SUPER</span>' : ''}

        </td>

        <td class="py-3 px-3">

          <div class="font-medium text-slate-800">${escapeHtml(u.requested_role_display || u.requested_role || 'Chưa chọn')}</div>

          <div class="text-[11px] text-slate-500 font-medium">${escapeHtml(u.department_or_class || 'Chưa xác định')}</div>
          ${u.pending_class_change ? `<div class="mt-1"><span class="badge bg-amber-100 text-amber-800 border border-amber-300 font-bold text-[10px]">Xin đổi sang: ${escapeHtml(u.pending_class_change.target_class_name)}</span></div>` : ''}

        </td>

        <td class="py-3 px-3 text-slate-500 font-mono text-[11px]">

          ${u.date_joined ? new Date(u.date_joined).toLocaleDateString('vi-VN') : '—'}

        </td>

        <td class="py-3 px-3">

          ${isPending ? '<span class="text-slate-400 text-xs italic">Chờ phân công</span>' : `<span class="badge border ${roleColors[u.role] || 'bg-slate-100 text-slate-700'}">${escapeHtml(u.role_display)}</span>`}

        </td>

        <td class="py-3 px-3 text-center">

          ${statusBadges[u.account_status] || `<span class="badge bg-slate-100 text-slate-700">${escapeHtml(u.account_status_display || u.account_status)}</span>`}

        </td>

        <td class="py-3 px-3 text-right">

          ${actionBtns}

        </td>

      </tr>

    `;

  }).join('');

  lucide.createIcons();

}



async function confirmDeleteUser(userId, username, fullName) {
  const nameDisplay = fullName || username;
  if (!confirm(`XÁC NHẬN XÓA TÀI KHOẢN:\n\nBạn có chắc chắn muốn xóa vĩnh viễn tài khoản "${nameDisplay}" (@${username}) khỏi hệ thống?\n\nLƯU Ý: Thao tác này sẽ xóa vĩnh viễn hồ sơ và quyền truy cập của người dùng này và KHÔNG THỂ HOÀN TÁC!`)) {
    return;
  }

  try {
    const csrfToken = (typeof getCookie === 'function' ? getCookie('csrftoken') : '') || '';
    const res = await fetch(`/api/core/users/${userId}/`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      }
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const errMsg = data.error || 'Lỗi khi xóa tài khoản.';
      if (typeof showToast === 'function') {
        showToast(errMsg, 'error');
      } else {
        alert(errMsg);
      }
      return;
    }

    const successMsg = data.message || `Đã xóa vĩnh viễn tài khoản "${nameDisplay}" thành công.`;
    if (typeof showToast === 'function') {
      showToast(successMsg, 'success');
    } else {
      alert(successMsg);
    }
    if (typeof closeUserDetailModal === 'function') {
      closeUserDetailModal();
    }
    if (typeof loadUsersManagement === 'function') {
      await loadUsersManagement();
    }
    if (typeof loadAdminUsersModule === 'function') {
      loadAdminUsersModule();
    }
  } catch (err) {
    const connErr = 'Lỗi kết nối khi gửi yêu cầu xóa tài khoản: ' + (err.message || err);
    if (typeof showToast === 'function') {
      showToast(connErr, 'error');
    } else {
      alert(connErr);
    }
  }
}

async function openUserDetailModal(userId) {
  const modal = document.getElementById('modal-user-detail');
  if (!modal) {
    alert('Không tìm thấy giao diện chi tiết người dùng.');
    return;
  }

  let u = (allUsersCache || []).find(x => String(x.id) === String(userId));
  if (!u) {
    try {
      const res = await fetch(`/api/core/users/${userId}/`);
      if (res.ok) {
        u = await res.json();
      } else {
        alert('Không tìm thấy thông tin tài khoản người dùng này.');
        return;
      }
    } catch (e) {
      alert('Không thể kết nối đến máy chủ: ' + e.message);
      return;
    }
  }



  document.getElementById('detail-user-fullname').textContent = u.full_name || u.username;

  document.getElementById('detail-user-username').textContent = u.username;



  const statusMap = {

    PENDING: '<span class="badge bg-amber-100 text-amber-800 border border-amber-300 font-semibold">Chờ duyệt</span>',

    APPROVED: '<span class="badge bg-emerald-100 text-emerald-800 border border-emerald-300 font-semibold">Đã phê duyệt</span>',

    REJECTED: '<span class="badge bg-rose-100 text-rose-800 border border-rose-300 font-semibold">Bị từ chối</span>',

    SUSPENDED: '<span class="badge bg-purple-100 text-purple-800 border border-purple-300 font-semibold">Tạm khóa</span>',

    DISABLED: '<span class="badge bg-slate-100 text-slate-600 border border-slate-300">Vô hiệu hóa</span>'

  };

  document.getElementById('detail-user-status-badge').innerHTML = statusMap[u.account_status] || u.account_status;



  document.getElementById('detail-user-email').textContent = u.email || 'Chưa cung cấp';

  document.getElementById('detail-user-phone').textContent = u.phone || 'Chưa cung cấp';

  document.getElementById('detail-user-req-role').textContent = u.requested_role_display || u.requested_role || 'Chưa chọn';

  document.getElementById('detail-user-dept').textContent = u.department_or_class || 'Chưa phân công';

  document.getElementById('detail-user-role').textContent = u.role_display || 'Chưa cấp vai trò';

  document.getElementById('detail-user-date').textContent = u.date_joined ? new Date(u.date_joined).toLocaleString('vi-VN') : '—';

    let verifText = u.verification_info || 'Không có mã hoặc ghi chú xác minh bổ sung.';
  try {
    if (u.verification_info && (u.verification_info.startsWith('{') || u.verification_info.startsWith('['))) {
      const parsed = JSON.parse(u.verification_info);
      if (typeof parsed === 'object' && parsed !== null) {
        let parts = [];
        if (parsed.subjects && parsed.subjects.length > 0) parts.push(`Môn giảng dạy: ${parsed.subjects.join(', ')}`);
        if (parsed.teaching_classes && parsed.teaching_classes.length > 0) parts.push(`Lớp đăng ký giảng dạy: ${parsed.teaching_classes.join(', ')} (${parsed.teaching_classes.length} lớp)`);
        if (parsed.homeroom_class) parts.push(`Lớp chủ nhiệm đề xuất: ${parsed.homeroom_class}`);
        if (parsed.student_code) parts.push(`Mã học sinh: ${parsed.student_code}`);
        if (parts.length > 0) verifText = parts.join(' • ');
      }
    }
  } catch (e) {}
  document.getElementById('detail-user-verification').textContent = verifText;

  // Pending class change check
  let pendingChange = u.pending_class_change;
  if (!pendingChange && u.verification_info && u.verification_info.startsWith('{')) {
    try {
      const parsed = JSON.parse(u.verification_info);
      pendingChange = parsed.pending_class_change;
    } catch(e) {}
  }

  const pendingBox = document.getElementById('detail-pending-class-box');
  if (pendingBox) {
    if (pendingChange) {
      const fromEl = document.getElementById('detail-class-change-from');
      const toEl = document.getElementById('detail-class-change-to');
      const reasonEl = document.getElementById('detail-class-change-reason');
      if (fromEl) fromEl.textContent = pendingChange.previous_class || u.department_or_class || 'Lớp cũ';
      if (toEl) toEl.textContent = pendingChange.target_class_name || 'Lớp mới';
      if (reasonEl) reasonEl.textContent = pendingChange.reason || 'Không có ghi chú thêm.';

      const btnApproveCC = document.getElementById('btn-approve-class-change');
      if (btnApproveCC) btnApproveCC.onclick = () => handleReviewClassChange(u.id, 'approve');

      const btnRejectCC = document.getElementById('btn-reject-class-change');
      if (btnRejectCC) btnRejectCC.onclick = () => handleReviewClassChange(u.id, 'reject');

      pendingBox.classList.remove('hidden');
    } else {
      pendingBox.classList.add('hidden');
    }
  }



  // Approval meta

  const appBox = document.getElementById('detail-approval-meta-box');

  if (u.approved_by_name) {

    document.getElementById('detail-user-approved-meta').textContent = `Phê duyệt bởi: ${u.approved_by_name} lúc ${u.approved_at ? new Date(u.approved_at).toLocaleString('vi-VN') : ''}`;

    appBox.classList.remove('hidden');

  } else {

    appBox.classList.add('hidden');

  }



  // Rejection reason

  const rejBox = document.getElementById('detail-rejection-meta-box');

  if (u.rejection_reason) {

    document.getElementById('detail-user-rejection-reason').textContent = u.rejection_reason;

    rejBox.classList.remove('hidden');

  } else {

    rejBox.classList.add('hidden');

  }



  // Internal notes

  const notesBox = document.getElementById('detail-internal-notes-box');

  if (u.internal_notes) {

    document.getElementById('detail-user-internal-notes').textContent = u.internal_notes;

    notesBox.classList.remove('hidden');

  } else {

    notesBox.classList.add('hidden');

  }



  // Timeline list

  const historyList = document.getElementById('detail-user-history-list');

  const historyCount = document.getElementById('detail-history-count');

  historyList.innerHTML = '<div class="p-3 text-center text-slate-400">Đang tải lịch sử xét duyệt...</div>';



  document.getElementById('modal-user-detail').classList.remove('hidden');



  try {

    const res = await fetch(`/api/core/users/${userId}/approval-history/`);

    if (res.ok) {

      const logs = await res.json();

      historyCount.textContent = `${logs.length} sự kiện`;

      if (logs.length === 0) {

        historyList.innerHTML = '<div class="p-3 text-center text-slate-400 bg-slate-50 rounded-xl">Chưa có lịch sử thay đổi trạng thái.</div>';

      } else {

        historyList.innerHTML = logs.map(l => `

          <div class="p-2.5 bg-slate-50 rounded-xl border border-slate-200">

            <div class="flex items-center justify-between text-slate-500 text-[10px]">

              <span>Người thực hiện: <b class="text-slate-800">${escapeHtml(l.reviewer_name || 'Admin')}</b></span>

              <span>${new Date(l.created_at).toLocaleString('vi-VN')}</span>

            </div>

            <div class="mt-1 text-slate-800 font-medium">

              Trạng thái: <span class="badge bg-slate-200 text-slate-700">${l.previous_status}</span> &rarr; <span class="badge bg-blue-100 text-brand-800 font-bold">${l.new_status}</span>

              ${l.assigned_role ? ` (Gán vai trò: <b>${escapeHtml(l.assigned_role)}</b>)` : ''}

            </div>

            ${l.reason ? `<div class="mt-1 text-rose-700 text-[10px]"><b>Lý do:</b> ${escapeHtml(l.reason)}</div>` : ''}

            ${l.internal_notes ? `<div class="mt-0.5 text-amber-700 text-[10px]"><b>Ghi chú nội bộ:</b> ${escapeHtml(l.internal_notes)}</div>` : ''}

          </div>

        `).join('');

      }

    }

  } catch (err) {

    historyList.innerHTML = '<div class="p-3 text-center text-rose-500">Lỗi khi tải lịch sử.</div>';

  }

  // Cấu hình các nút thao tác trong Modal Chi Tiết
  const btnDeleteModal = document.getElementById('btn-delete-user-detail');
  const canDeleteUserInModal = currentUser && (
    currentUser.is_admin ||
    currentUser.is_super_admin ||
    currentUser.role === 'ADMIN' ||
    currentUser.role === 'SUPER_ADMIN'
  );
  if (btnDeleteModal) {
    if (canDeleteUserInModal && String(u.id) !== String(currentUser.id)) {
      btnDeleteModal.classList.remove('hidden');
      btnDeleteModal.onclick = () => confirmDeleteUser(u.id, u.username, u.full_name || u.username);
    } else {
      btnDeleteModal.classList.add('hidden');
    }
  }

  const btnApproveModal = document.getElementById('btn-approve-user-detail');
  if (btnApproveModal) {
    btnApproveModal.onclick = () => {
      closeUserDetailModal();
      openReviewModal(u.id, 'approve');
    };
  }

  if (window.lucide && typeof lucide.createIcons === 'function') {
    lucide.createIcons();
  }
}



function closeUserDetailModal() {

  document.getElementById('modal-user-detail').classList.add('hidden');

}



// ==========================================
// REVIEW MODAL DYNAMIC ROLE & CLASS SELECTORS
// ==========================================
let _reviewTargetUser = null;
let _reviewTeacherSelectedClasses = new Set();
let _reviewTeacherActiveGradeTab = 10;
let _reviewStudentSelectedClassId = null;

async function onReviewRoleChange() {
  const roleSelect = document.getElementById('review-assigned-role');
  if (!roleSelect) return;
  const role = roleSelect.value;

  const secStudent = document.getElementById('review-section-student');
  const secTeacher = document.getElementById('review-section-teacher');
  const secHomeroom = document.getElementById('review-section-homeroom');
  const secOther = document.getElementById('review-section-other');

  if (secStudent) secStudent.classList.add('hidden');
  if (secTeacher) secTeacher.classList.add('hidden');
  if (secHomeroom) secHomeroom.classList.add('hidden');
  if (secOther) secOther.classList.add('hidden');

  if (typeof ensureClassesLoaded === 'function') {
    await ensureClassesLoaded();
  }

  if (role === 'HOC_SINH') {
    if (secStudent) secStudent.classList.remove('hidden');
    initReviewStudentSection();
  } else if (role === 'GVBM') {
    if (secTeacher) secTeacher.classList.remove('hidden');
    initReviewTeacherSection(false);
  } else if (role === 'GVCN') {
    if (secTeacher) secTeacher.classList.remove('hidden');
    if (secHomeroom) secHomeroom.classList.remove('hidden');
    initReviewTeacherSection(true);
    initReviewHomeroomSection();
  } else {
    if (secOther) secOther.classList.remove('hidden');
    const otherInput = document.getElementById('review-department-other');
    if (otherInput && _reviewTargetUser) {
      otherInput.value = _reviewTargetUser.department_or_class || '';
    }
  }

  if (window.lucide && typeof lucide.createIcons === 'function') {
    lucide.createIcons();
  }
}

function initReviewStudentSection() {
  let grade = 10;
  let classId = null;

  if (_reviewTargetUser) {
    if (_reviewTargetUser.student_class_info) {
      grade = _reviewTargetUser.student_class_info.grade || 10;
      classId = _reviewTargetUser.student_class_info.id;
    } else if (_reviewTargetUser.department_or_class) {
      const match = (classesCache || []).find(c => c.name.toLowerCase() === _reviewTargetUser.department_or_class.trim().toLowerCase());
      if (match) {
        grade = match.grade;
        classId = match.id;
      }
    }
  }

  const gradeSelect = document.getElementById('review-student-grade');
  if (gradeSelect) gradeSelect.value = String(grade);

  renderReviewStudentClasses(grade, classId);
}

function renderReviewStudentClasses(grade, selectedClassId) {
  const classSelect = document.getElementById('review-student-class');
  if (!classSelect) return;

  const gradeClasses = (classesCache || []).filter(c => Number(c.grade) === Number(grade));
  gradeClasses.sort((a, b) => (a.class_order || 0) - (b.class_order || 0));

  let html = '<option value="">-- Chọn lớp --</option>';
  gradeClasses.forEach(c => {
    const isSel = (selectedClassId && Number(selectedClassId) === Number(c.id));
    html += `<option value="${c.id}" ${isSel ? 'selected' : ''}>Lớp ${escapeHtml(c.name)}</option>`;
  });
  classSelect.innerHTML = html;

  if (selectedClassId) {
    classSelect.value = String(selectedClassId);
  }

  onReviewStudentClassChange(classSelect.value);
}

function onReviewStudentGradeChange(gradeVal) {
  renderReviewStudentClasses(parseInt(gradeVal, 10), null);
}

function onReviewStudentClassChange(classIdVal) {
  _reviewStudentSelectedClassId = classIdVal ? parseInt(classIdVal, 10) : null;
  const badgeText = document.getElementById('review-student-selected-text');
  const hiddenDept = document.getElementById('review-department');

  if (_reviewStudentSelectedClassId) {
    const found = (classesCache || []).find(c => Number(c.id) === Number(_reviewStudentSelectedClassId));
    if (found) {
      if (badgeText) badgeText.textContent = `Lớp ${found.name} (Khối ${found.grade})`;
      if (hiddenDept) hiddenDept.value = found.name;
      return;
    }
  }
  if (badgeText) badgeText.textContent = 'Chưa chọn';
  if (hiddenDept) hiddenDept.value = '';
}

function initReviewTeacherSection(isGvcn) {
  const subjSelect = document.getElementById('review-teacher-subject');
  if (subjSelect && _reviewTargetUser) {
    const defaultSubj = _reviewTargetUser.teacher_subject || _reviewTargetUser.department_or_class || 'Toán học';
    let cleanSubj = defaultSubj;
    if (cleanSubj.startsWith('Môn: ')) cleanSubj = cleanSubj.substring(5).trim();
    else if (cleanSubj.startsWith('Môn ')) cleanSubj = cleanSubj.substring(4).trim();

    let matched = false;
    for (let i = 0; i < subjSelect.options.length; i++) {
      if (subjSelect.options[i].value.toLowerCase() === cleanSubj.toLowerCase()) {
        subjSelect.selectedIndex = i;
        matched = true;
        break;
      }
    }
    if (!matched && cleanSubj && !cleanSubj.match(/^\d+[A-Za-zĐđ]+\d*$/)) {
      const opt = document.createElement('option');
      opt.value = cleanSubj;
      opt.textContent = cleanSubj;
      opt.selected = true;
      subjSelect.appendChild(opt);
    }
  }

  switchReviewTeacherGradeTab(_reviewTeacherActiveGradeTab || 10);
}

function switchReviewTeacherGradeTab(grade) {
  _reviewTeacherActiveGradeTab = Number(grade);

  [10, 11, 12].forEach(g => {
    const btn = document.getElementById(`review-tab-btn-${g}`);
    if (btn) {
      if (g === _reviewTeacherActiveGradeTab) {
        btn.className = 'px-2.5 py-1 text-[11px] font-bold rounded-md bg-white text-brand-700 shadow-sm transition';
      } else {
        btn.className = 'px-2.5 py-1 text-[11px] font-medium rounded-md text-slate-600 hover:text-slate-900 transition';
      }
    }
  });

  renderReviewTeacherClassesGrid();
}

function renderReviewTeacherClassesGrid() {
  const grid = document.getElementById('review-teacher-classes-grid');
  if (!grid) return;

  const gradeClasses = (classesCache || []).filter(c => Number(c.grade) === Number(_reviewTeacherActiveGradeTab));
  gradeClasses.sort((a, b) => (a.class_order || 0) - (b.class_order || 0));

  let html = '';
  gradeClasses.forEach(c => {
    const isSelected = _reviewTeacherSelectedClasses.has(c.name);
    const btnClass = isSelected
      ? 'px-2 py-1.5 rounded-lg text-[11px] font-bold bg-brand-600 text-white shadow-sm border border-brand-700 flex items-center justify-center gap-1 transition'
      : 'px-2 py-1.5 rounded-lg text-[11px] font-medium bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 flex items-center justify-center gap-1 transition';

    html += `
      <button type="button" onclick="toggleReviewTeacherClass('${escapeHtml(c.name)}')" class="${btnClass}">
        ${isSelected ? '<i data-lucide="check" class="w-3 h-3 text-white"></i>' : ''}
        <span>${escapeHtml(c.name)}</span>
      </button>
    `;
  });

  grid.innerHTML = html;

  const countBadge = document.getElementById('review-teacher-selected-count');
  if (countBadge) {
    countBadge.textContent = `Đã chọn: ${_reviewTeacherSelectedClasses.size} lớp`;
  }

  if (window.lucide && typeof lucide.createIcons === 'function') {
    lucide.createIcons();
  }
}

function toggleReviewTeacherClass(className) {
  if (_reviewTeacherSelectedClasses.has(className)) {
    _reviewTeacherSelectedClasses.delete(className);
  } else {
    _reviewTeacherSelectedClasses.add(className);
  }
  renderReviewTeacherClassesGrid();
}

function toggleReviewAllGradeClasses(selectState) {
  const gradeClasses = (classesCache || []).filter(c => Number(c.grade) === Number(_reviewTeacherActiveGradeTab));
  gradeClasses.forEach(c => {
    if (selectState) {
      _reviewTeacherSelectedClasses.add(c.name);
    } else {
      _reviewTeacherSelectedClasses.delete(c.name);
    }
  });
  renderReviewTeacherClassesGrid();
}

function initReviewHomeroomSection() {
  const hrSelect = document.getElementById('review-homeroom-class');
  if (!hrSelect) return;

  const sorted = [...(classesCache || [])].sort((a, b) => {
    if (a.grade !== b.grade) return a.grade - b.grade;
    return (a.class_order || 0) - (b.class_order || 0);
  });

  let targetHrId = null;
  if (_reviewTargetUser) {
    if (_reviewTargetUser.homeroom_class_info) {
      targetHrId = _reviewTargetUser.homeroom_class_info.id;
    } else if (_reviewTargetUser.department_or_class) {
      const match = sorted.find(c => c.name.toLowerCase() === _reviewTargetUser.department_or_class.trim().toLowerCase());
      if (match) targetHrId = match.id;
    }
  }

  let html = '<option value="">-- Chọn lớp chủ nhiệm (trong 64 lớp) --</option>';
  [10, 11, 12].forEach(g => {
    const gClasses = sorted.filter(c => Number(c.grade) === g);
    if (gClasses.length > 0) {
      html += `<optgroup label="Khối ${g} (${gClasses.length} lớp)">`;
      gClasses.forEach(c => {
        const isSel = (targetHrId && Number(targetHrId) === Number(c.id));
        const hrInfo = c.homeroom_teacher_name ? ` • GVCN: ${c.homeroom_teacher_name}` : ' • (Chưa có GVCN)';
        html += `<option value="${c.id}" data-name="${escapeHtml(c.name)}" ${isSel ? 'selected' : ''}>Lớp ${escapeHtml(c.name)}${escapeHtml(hrInfo)}</option>`;
      });
      html += '</optgroup>';
    }
  });

  hrSelect.innerHTML = html;
  if (targetHrId) {
    hrSelect.value = String(targetHrId);
  }
  onReviewHomeroomClassChange(hrSelect.value);
}

function onReviewHomeroomClassChange(classIdVal) {
  const conflictAlert = document.getElementById('review-homeroom-conflict-alert');
  const conflictMsg = document.getElementById('review-homeroom-conflict-msg');
  const hiddenDept = document.getElementById('review-department');

  if (!classIdVal) {
    if (conflictAlert) conflictAlert.classList.add('hidden');
    return;
  }

  const found = (classesCache || []).find(c => Number(c.id) === Number(classIdVal));
  if (found) {
    if (hiddenDept) hiddenDept.value = found.name;
    if (found.homeroom_teacher && _reviewTargetUser && Number(found.homeroom_teacher) !== Number(_reviewTargetUser.id)) {
      if (conflictAlert) conflictAlert.classList.remove('hidden');
      if (conflictMsg) {
        conflictMsg.textContent = `Lớp ${found.name} hiện đã có GVCN là ${found.homeroom_teacher_name || 'một giáo viên khác'}. Khi lưu, hệ thống sẽ tự động chuyển phân công GVCN lớp ${found.name} sang giáo viên này.`;
      }
    } else {
      if (conflictAlert) conflictAlert.classList.add('hidden');
    }
  }
}

async function openReviewModal(userId, actionType) {
  let u = (allUsersCache || []).find(x => String(x.id) === String(userId));
  if (!u) {
    try {
      const res = await fetch(`/api/core/users/${userId}/`);
      if (res.ok) {
        u = await res.json();
      }
    } catch (e) {
      console.error('Lỗi khi tải thông tin người dùng cho modal xét duyệt:', e);
    }
  }
  if (!u) {
    if (typeof showToast === 'function') {
      showToast('Không tìm thấy thông tin tài khoản người dùng.', 'error');
    } else {
      alert('Không tìm thấy thông tin tài khoản người dùng.');
    }
    return;
  }



  document.getElementById('review-target-user-id').value = u.id;

  document.getElementById('review-action-type').value = actionType;

  document.getElementById('review-target-fullname').textContent = u.full_name || u.username;

  document.getElementById('review-target-username').textContent = u.username;

  document.getElementById('review-target-req-role').textContent = u.requested_role_display || u.requested_role || 'Chưa xác định';

  document.getElementById('review-target-dept').textContent = u.department_or_class || 'Chưa cung cấp';



  document.getElementById('review-internal-notes').value = u.internal_notes || '';



  const approveFields = document.getElementById('review-approve-fields');

  const reasonFields = document.getElementById('review-reason-fields');

  const reactivateFields = document.getElementById('review-reactivate-fields');

  const titleEl = document.getElementById('review-modal-title');

  const submitBtn = document.getElementById('review-modal-submit-btn');



  approveFields.classList.add('hidden');

  reasonFields.classList.add('hidden');

  reactivateFields.classList.add('hidden');



  if (actionType === 'approve') {

    titleEl.textContent = 'Phê duyệt & Phân quyền tài khoản';

    approveFields.classList.remove('hidden');

    _reviewTargetUser = u;

    const candidateRole = (u.requested_role && ['HOC_SINH', 'GVCN', 'GVBM', 'SAO_DO', 'DOAN_TRUONG', 'BGH', 'CHUYEN_VIEN_TAM_LY', 'ADMIN'].includes(u.requested_role))

      ? u.requested_role : (u.role || 'HOC_SINH');

    document.getElementById('review-assigned-role').value = candidateRole;

    document.getElementById('review-department').value = u.department_or_class || '';

    document.getElementById('review-can-verify').checked = Boolean(u.can_verify_violations);

    document.getElementById('review-can-counseling').checked = Boolean(u.can_view_counseling || candidateRole === 'CHUYEN_VIEN_TAM_LY');

    _reviewTeacherSelectedClasses = new Set();
    if (Array.isArray(u.teaching_classes) && u.teaching_classes.length > 0) {
      u.teaching_classes.forEach(c => _reviewTeacherSelectedClasses.add(c));
    }

    await onReviewRoleChange();

    submitBtn.textContent = 'Phê duyệt & Kích hoạt';

    submitBtn.className = 'px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-sm transition';

  } else if (actionType === 'reject') {

    titleEl.textContent = 'Từ chối yêu cầu đăng ký';

    reasonFields.classList.remove('hidden');

    document.getElementById('review-reason-label').textContent = 'Lý do từ chối (Gửi đến người dùng)';

    document.getElementById('review-reason-input').value = u.rejection_reason || '';

    document.getElementById('review-reason-input').placeholder = 'Nhập lý do từ chối...';



    submitBtn.textContent = 'Xác nhận từ chối';

    submitBtn.className = 'px-5 py-2 bg-rose-600 hover:bg-rose-700 text-white font-bold rounded-xl shadow-sm transition';

  } else if (actionType === 'request_info') {

    titleEl.textContent = 'Yêu cầu bổ sung thông tin';

    reasonFields.classList.remove('hidden');

    document.getElementById('review-reason-label').textContent = 'Nội dung cần người dùng bổ sung';

    document.getElementById('review-reason-input').value = '';

    document.getElementById('review-reason-input').placeholder = 'VD: Vui lòng cung cấp mã học sinh chính xác hoặc ảnh thẻ học sinh...';



    submitBtn.textContent = 'Gửi yêu cầu bổ sung';

    submitBtn.className = 'px-5 py-2 bg-amber-600 hover:bg-amber-700 text-white font-bold rounded-xl shadow-sm transition';

  } else if (actionType === 'suspend') {

    titleEl.textContent = 'Tạm khóa tài khoản';

    reasonFields.classList.remove('hidden');

    document.getElementById('review-reason-label').textContent = 'Lý do tạm khóa tài khoản';

    document.getElementById('review-reason-input').value = '';

    document.getElementById('review-reason-input').placeholder = 'Nhập lý do tạm thời khóa tài khoản...';



    submitBtn.textContent = 'Xác nhận tạm khóa';

    submitBtn.className = 'px-5 py-2 bg-rose-700 hover:bg-rose-800 text-white font-bold rounded-xl shadow-sm transition';

  } else if (actionType === 'reactivate') {

    titleEl.textContent = 'Mở khóa & Kích hoạt lại tài khoản';

    reactivateFields.classList.remove('hidden');



    submitBtn.textContent = 'Kích hoạt lại ngay';

    submitBtn.className = 'px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-sm transition';

  }



  document.getElementById('modal-review-action').classList.remove('hidden');

  lucide.createIcons();

}



function closeReviewModal() {

  document.getElementById('modal-review-action').classList.add('hidden');

}



async function handleReviewActionSubmit(event) {

  event.preventDefault();

  const userId = document.getElementById('review-target-user-id').value;

  const actionType = document.getElementById('review-action-type').value;

  const internalNotes = document.getElementById('review-internal-notes').value.trim();



  const payload = {

    action: actionType,

    internal_notes: internalNotes

  };



  if (actionType === 'approve') {

    const assignedRole = document.getElementById('review-assigned-role').value;
    payload.assigned_role = assignedRole;
    payload.can_verify_violations = document.getElementById('review-can-verify').checked;
    payload.can_view_counseling = document.getElementById('review-can-counseling').checked;

    if (assignedRole === 'HOC_SINH') {
      const studentClassSelect = document.getElementById('review-student-class');
      const classId = studentClassSelect ? studentClassSelect.value : null;
      if (!classId) {
        showToast('Vui lòng chọn khối và lớp học cho học sinh.', 'warning');
        return;
      }
      payload.class_id = parseInt(classId, 10);
      const foundCls = (classesCache || []).find(c => Number(c.id) === Number(classId));
      payload.department_or_class = foundCls ? foundCls.name : '';
    } else if (assignedRole === 'GVBM') {
      const subjSelect = document.getElementById('review-teacher-subject');
      payload.subject = subjSelect ? subjSelect.value.trim() : 'Toán học';
      payload.teaching_classes = Array.from(_reviewTeacherSelectedClasses);
      payload.department_or_class = 'Môn ' + payload.subject;
    } else if (assignedRole === 'GVCN') {
      const subjSelect = document.getElementById('review-teacher-subject');
      payload.subject = subjSelect ? subjSelect.value.trim() : 'Toán học';
      payload.teaching_classes = Array.from(_reviewTeacherSelectedClasses);

      const hrSelect = document.getElementById('review-homeroom-class');
      const hrClassId = hrSelect ? hrSelect.value : null;
      if (!hrClassId) {
        showToast('Vui lòng chọn lớp chủ nhiệm cho Giáo viên chủ nhiệm.', 'warning');
        return;
      }
      payload.homeroom_class_id = parseInt(hrClassId, 10);
      const foundHr = (classesCache || []).find(c => Number(c.id) === Number(hrClassId));
      payload.homeroom_class = foundHr ? foundHr.name : '';
      payload.department_or_class = payload.homeroom_class;
    } else {
      const otherDept = document.getElementById('review-department-other');
      payload.department_or_class = otherDept ? otherDept.value.trim() : '';
    }

  } else if (['reject', 'request_info', 'suspend'].includes(actionType)) {

    const reason = document.getElementById('review-reason-input').value.trim();

    if (!reason) {

      showToast('Vui lòng nhập lý do cụ thể.', 'warning');

      return;

    }

    payload.reason = reason;

  }



  const submitBtn = document.getElementById('review-modal-submit-btn');

  submitBtn.disabled = true;



  try {

    const res = await fetch(`/api/core/users/${userId}/review/`, {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken')

      },

      body: JSON.stringify(payload)

    });

    const data = await res.json();



    if (res.ok) {

      showToast(data.message || 'Thao tác xét duyệt thành công.', 'success');

      closeReviewModal();

      await loadUsersManagement();
      if (typeof loadAdminUsersModule === "function") loadAdminUsersModule();

      loadAuditLogs();

    } else {

      showToast(data.error || 'Lỗi khi xử lý xét duyệt tài khoản.', 'error');

    }

  } catch (err) {

    showToast('Lỗi kết nối máy chủ.', 'error');

  } finally {

    submitBtn.disabled = false;

  }

}



function openCreateUserModal() {

  document.getElementById('create-user-form').reset();

  document.getElementById('create-user-error').classList.add('hidden');

  document.getElementById('create-user-result').classList.add('hidden');

  document.getElementById('create-user-actions').classList.remove('hidden');

  document.getElementById('modal-create-user').classList.remove('hidden');

  document.getElementById('create-user-username').focus();

}



function closeCreateUserModal() {

  document.getElementById('modal-create-user').classList.add('hidden');

  document.getElementById('create-user-form').reset();

  document.getElementById('create-user-temporary-password').textContent = '';

  document.getElementById('create-user-result').classList.add('hidden');

  document.getElementById('create-user-actions').classList.remove('hidden');

}



async function handleCreateUserSubmit(e) {

  e.preventDefault();

  const errorBox = document.getElementById('create-user-error');

  const submitButton = document.getElementById('create-user-submit');

  errorBox.classList.add('hidden');

  errorBox.textContent = '';

  submitButton.disabled = true;



  try {

    const res = await fetch('/api/core/users/', {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken')

      },

      body: JSON.stringify({

        username: document.getElementById('create-user-username').value,

        full_name: document.getElementById('create-user-full-name').value,

        email: document.getElementById('create-user-email').value,

        phone: document.getElementById('create-user-phone').value,

        role: document.getElementById('create-user-role').value

      })

    });

    const data = await res.json();

    if (!res.ok) {

      const firstError = data.error || Object.values(data)[0]?.[0] || 'Không thể tạo tài khoản.';

      errorBox.textContent = String(firstError);

      errorBox.classList.remove('hidden');

      return;

    }



    document.getElementById('create-user-temporary-password').textContent = data.temporary_password;

    document.getElementById('create-user-result').classList.remove('hidden');

    document.getElementById('create-user-actions').classList.add('hidden');

    showToast(data.message, 'success');

    loadUsersManagement();

  } catch (err) {

    errorBox.textContent = 'Không thể kết nối đến máy chủ. Vui lòng thử lại.';

    errorBox.classList.remove('hidden');

  } finally {

    submitButton.disabled = false;

  }

}



async function copyTemporaryPassword() {

  const password = document.getElementById('create-user-temporary-password').textContent;

  try {

    await navigator.clipboard.writeText(password);

    showToast('Đã sao chép mật khẩu tạm thời.', 'success');

  } catch (err) {

    showToast('Không thể truy cập clipboard. Hãy chọn và sao chép mật khẩu thủ công.', 'error');

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



function openMobileDrawer() {

  const backdrop = document.getElementById('mobile-drawer-backdrop');

  if (backdrop) {

    backdrop.classList.add('is-open');

    document.body.style.overflow = 'hidden';

    if (window.lucide) lucide.createIcons();

  }

}



function closeMobileDrawer() {

  const backdrop = document.getElementById('mobile-drawer-backdrop');

  if (backdrop) {

    backdrop.classList.remove('is-open');

    document.body.style.overflow = '';

  }

}



function toggleMobileMenu() {

  const backdrop = document.getElementById('mobile-drawer-backdrop');

  if (backdrop && backdrop.classList.contains('is-open')) {

    closeMobileDrawer();

  } else {

    openMobileDrawer();

  }

}



document.addEventListener('keydown', e => {

  if (e.key === 'Escape') closeMobileDrawer();

});



// ==========================================

// CẤU HÌNH VÀ THEO DÕI EMAIL ĐOÀN TRƯỜNG (ADMIN)

// ==========================================



function toggleSmtpConfigForm() {

  const form = document.getElementById('smtp-config-form');

  const btnText = document.getElementById('btn-toggle-smtp-text');

  if (!form) return;

  if (form.classList.contains('hidden')) {

    form.classList.remove('hidden');

    if (btnText) btnText.textContent = 'Thu gọn SMTP';

  } else {

    form.classList.add('hidden');

    if (btnText) btnText.textContent = 'Chỉnh sửa SMTP';

  }

}



window.allEmailRecipients = [];



function filterEmailRecipientsTable() {

  const query = (document.getElementById('search-email-recipients')?.value || '').trim().toLowerCase();

  if (!query) {

    renderEmailRecipients(window.allEmailRecipients);

    return;

  }

  const filtered = window.allEmailRecipients.filter(u => {

    const email = (u.email || '').toLowerCase();

    const name = (u.full_name || '').toLowerCase();

    const uname = (u.username || '').toLowerCase();

    const role = (u.role || '').toLowerCase();

    return email.includes(query) || name.includes(query) || uname.includes(query) || role.includes(query);

  });

  renderEmailRecipients(filtered);

}



function renderEmailRecipients(recipients) {

  const tbody = document.getElementById('email-recipients-tbody');

  const countPill = document.getElementById('email-recipients-count-pill');

  if (countPill) {

    countPill.textContent = `${(recipients || []).length} email`;

  }

  if (!tbody) return;



  if (!recipients || recipients.length === 0) {

    tbody.innerHTML = `

      <tr>

        <td colspan="6" class="px-4 py-8 text-center text-slate-400">

          <div class="flex flex-col items-center justify-center space-y-2">

            <i data-lucide="inbox" class="w-8 h-8 text-slate-300"></i>

            <p class="font-medium text-slate-500 text-xs">Chưa có địa chỉ Gmail / Email nào trong danh sách nhận thông báo.</p>

            <p class="text-[11px] text-slate-400">Hãy nhập địa chỉ Gmail vào ô phía trên và nhấn "Thêm Gmail nhận".</p>

          </div>

        </td>

      </tr>

    `;

    lucide.createIcons();

    return;

  }



  tbody.innerHTML = recipients.map((u, index) => {

    const safeEmail = (u.email || '').replace(/"/g, '&quot;');

    const safeName = (u.full_name || u.username || 'Cán bộ Đoàn').replace(/"/g, '&quot;');

    const isGmail = safeEmail.toLowerCase().endsWith('@gmail.com');

    return `

      <tr class="hover:bg-blue-50/40 transition">

        <td class="px-4 py-3 text-center font-bold text-slate-400 text-xs">

          ${index + 1}

        </td>

        <td class="px-4 py-3">

          <div class="flex items-center gap-2">

            <span class="inline-flex items-center justify-center w-6 h-6 rounded-md ${isGmail ? 'bg-red-50 text-red-600 border border-red-100' : 'bg-blue-50 text-blue-600 border border-blue-100'} text-[10px] font-black">

              ${isGmail ? 'G' : '@'}

            </span>

            <span class="font-mono text-blue-700 font-bold text-xs">${safeEmail}</span>

          </div>

        </td>

        <td class="px-4 py-3">

          <div class="font-semibold text-slate-800 text-xs">${safeName}</div>

          <div class="text-[10px] text-slate-400">@${u.username}</div>

        </td>

        <td class="px-4 py-3">

          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200">

            ${u.role || 'Đoàn trường'}

          </span>

        </td>

        <td class="px-4 py-3">

          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">

            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>

            Đang nhận Gmail

          </span>

        </td>

        <td class="px-4 py-3 text-right">

          <button type="button" onclick="confirmDeleteEmailRecipient(${u.id}, '${safeEmail}')" title="Xóa email này khỏi danh sách nhận thông báo" class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-rose-700 bg-rose-50 hover:bg-rose-100 hover:text-rose-800 border border-rose-200 rounded-lg transition shadow-2xs">

            <i data-lucide="trash-2" class="w-3.5 h-3.5 text-rose-600"></i>

            <span>Xóa email</span>

          </button>

        </td>

      </tr>

    `;

  }).join('');



  lucide.createIcons();

}



async function loadEmailSettings() {

  const alertEl = document.getElementById('email-admin-alert');

  if (alertEl) alertEl.classList.add('hidden');



  try {

    const res = await fetch('/api/conduct/email/config/');

    if (!res.ok) return;

    const data = await res.json();



    window.allEmailRecipients = data.recipients || [];

    renderEmailRecipients(window.allEmailRecipients);



    const badge = document.getElementById('email-config-source-badge');

    if (badge) {

      if (data.recipient_count > 0) {

        badge.className = 'inline-flex w-fit rounded-full bg-emerald-100 px-2.5 py-1 text-[11px] font-semibold text-emerald-800';

        badge.textContent = `${data.recipient_count} tài khoản Gmail Đoàn trường`;

      } else {

        badge.className = 'inline-flex w-fit rounded-full bg-amber-100 px-2.5 py-1 text-[11px] font-semibold text-amber-800';

        badge.textContent = 'Chưa có tài khoản Đoàn trường hợp lệ';

      }

    }



    const hostEl = document.getElementById('email-smtp-host');

    const portEl = document.getElementById('email-smtp-port');

    const userEl = document.getElementById('email-smtp-user');

    const fromEl = document.getElementById('email-default-from');



    if (hostEl) hostEl.textContent = data.smtp_host || 'smtp.gmail.com';

    if (portEl) portEl.textContent = data.smtp_port || '587';

    if (userEl) userEl.textContent = data.smtp_user || '(Chưa cấu hình)';

    if (fromEl) fromEl.textContent = data.default_from_email || '(Mặc định hệ thống)';



    const smtpUserInput = document.getElementById('smtp-user-input');

    const smtpFromInput = document.getElementById('smtp-from-input');

    if (smtpUserInput && !smtpUserInput.value) smtpUserInput.value = data.smtp_user || '';

    if (smtpFromInput && !smtpFromInput.value) smtpFromInput.value = data.default_from_email || '';



    await loadEmailHistory();

  } catch (err) {

    console.error('Không tải được cấu hình Email:', err);

  }

}



async function confirmDeleteEmailRecipient(userId, email) {

  if (!confirm(`Bạn có chắc chắn muốn xóa email "${email}" khỏi danh sách nhận thông báo vi phạm không?\n\nSau khi xóa, tài khoản này sẽ không còn nhận được email thông báo vi phạm nữa.`)) {

    return;

  }

  await removeEmailRecipient(userId, email);

}



async function removeEmailRecipient(userId, email) {

  try {

    const res = await fetch('/api/conduct/email/config/', {

      method: 'DELETE',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken') || '',

      },

      body: JSON.stringify({ user_id: userId, email: email }),

    });

    const data = await res.json();

    if (res.ok && data.success) {

      showToast(data.message || `Đã xóa email "${email}" khỏi danh sách nhận thông báo thành công!`, 'success');

      await loadEmailSettings();

      loadAuditLogs();

    } else {

      showToast(data.error || 'Không thể xóa email.', 'error');

    }

  } catch (err) {

    showToast('Lỗi kết nối khi xóa email.', 'error');

  }

}



async function addEmailRecipient(event) {

  if (event) event.preventDefault();

  const input = document.getElementById('email-recipient-input');

  const nameInput = document.getElementById('email-recipient-name-input');

  const btn = document.getElementById('btn-email-add-recipient');

  const alertEl = document.getElementById('email-admin-alert');



  const email = (input?.value || '').trim();

  const fullName = (nameInput?.value || '').trim();



  if (!email) {

    showToast('Vui lòng nhập địa chỉ Gmail Đoàn trường.', 'error');

    return;

  }



  btn.disabled = true;

  const originalHtml = btn.innerHTML;

  btn.innerHTML = `<span class="inline-block animate-spin mr-1">◌</span><span>Đang thêm...</span>`;



  try {

    const res = await fetch('/api/conduct/email/config/', {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken') || '',

      },

      body: JSON.stringify({ email, full_name: fullName }),

    });

    const data = await res.json();

    if (res.ok && data.success) {

      showToast(data.message || 'Đã thêm Gmail nhận thông báo thành công!', 'success');

      if (input) input.value = '';

      if (nameInput) nameInput.value = '';

      if (alertEl) alertEl.classList.add('hidden');

      await loadEmailSettings();

      loadAuditLogs();

    } else {

      showToast(data.error || 'Không thể thêm Gmail nhận thông báo.', 'error');

      if (alertEl) {

        alertEl.className = 'rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700';

        alertEl.textContent = data.error || 'Lỗi thêm email.';

        alertEl.classList.remove('hidden');

      }

    }

  } catch (err) {

    showToast('Lỗi kết nối máy chủ.', 'error');

  } finally {

    btn.disabled = false;

    btn.innerHTML = originalHtml;

    lucide.createIcons();

  }

}





async function saveSmtpConfig(event) {

  if (event) event.preventDefault();

  const userInput = document.getElementById('smtp-user-input');

  const pwdInput = document.getElementById('smtp-password-input');

  const fromInput = document.getElementById('smtp-from-input');

  const btn = document.getElementById('btn-save-smtp');



  const smtp_user = (userInput?.value || '').trim();

  const smtp_password = (pwdInput?.value || '').trim();

  const default_from_email = (fromInput?.value || '').trim();



  btn.disabled = true;

  const originalHtml = btn.innerHTML;

  btn.innerHTML = `<span class="inline-block animate-spin mr-1">◌</span><span>Đang lưu...</span>`;



  try {

    const res = await fetch('/api/conduct/email/config/', {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken') || '',

      },

      body: JSON.stringify({

        action: 'update_smtp',

        smtp_user,

        smtp_password,

        default_from_email,

      }),

    });

    const data = await res.json();

    if (res.ok && data.success) {

      showToast(data.message || 'Đã lưu cấu hình Gmail SMTP thành công!', 'success');

      if (pwdInput) pwdInput.value = '';

      await loadEmailSettings();

      loadAuditLogs();

    } else {

      showToast(data.error || 'Lỗi lưu cấu hình SMTP.', 'error');

    }

  } catch (err) {

    showToast('Lỗi kết nối khi lưu cấu hình SMTP.', 'error');

  } finally {

    btn.disabled = false;

    btn.innerHTML = originalHtml;

    lucide.createIcons();

  }

}



function saveEmailSettings(event) {

  return addEmailRecipient(event);

}



async function sendEmailTest() {

  const testInput = document.getElementById('email-test-recipient-input');

  const statusEl = document.getElementById('email-test-status');

  const btn = document.getElementById('btn-email-test');

  const recipient_email = (testInput?.value || '').trim();



  btn.disabled = true;

  const originalHtml = btn.innerHTML;

  btn.innerHTML = `<span class="inline-block animate-spin mr-1">◌</span><span>Đang gửi...</span>`;

  if (statusEl) statusEl.textContent = 'Đang gửi kiểm tra SMTP...';



  try {

    const res = await fetch('/api/conduct/email/test/', {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken') || '',

      },

      body: JSON.stringify({ recipient_email }),

    });

    const data = await res.json();

    if (res.ok && data.success) {

      showToast('Đã gửi email kiểm tra thành công! Vui lòng kiểm tra hộp thư.', 'success');

      if (statusEl) {

        statusEl.className = 'text-xs text-emerald-600 font-bold';

        statusEl.textContent = '✓ Gửi thành công';

      }

    } else {

      showToast(`Gửi email thử nghiệm thất bại: ${data.message || data.error}`, 'error');

      if (statusEl) {

        statusEl.className = 'text-xs text-rose-600 font-bold';

        statusEl.textContent = '✗ ' + (data.message || data.error || 'Thất bại');

      }

    }

    await loadEmailHistory();

    loadAuditLogs();

  } catch (err) {

    showToast('Lỗi kết nối khi gửi email thử nghiệm.', 'error');

    if (statusEl) {

      statusEl.className = 'text-xs text-rose-600 font-bold';

      statusEl.textContent = '✗ Lỗi kết nối';

    }

  } finally {

    btn.disabled = false;

    btn.innerHTML = originalHtml;

    lucide.createIcons();

  }

}



async function loadEmailHistory() {

  const tbody = document.getElementById('email-history-tbody');

  const summaryEl = document.getElementById('email-history-summary');

  if (!tbody) return;



  try {

    const res = await fetch('/api/conduct/email/history/');

    if (!res.ok) {

      tbody.innerHTML = `<tr><td colspan="8" class="px-3 py-4 text-center text-rose-500">Không tải được lịch sử email.</td></tr>`;

      return;

    }

    const data = await res.json();

    const list = data.results || [];



    if (summaryEl) {

      summaryEl.textContent = `Tổng cộng: ${data.total || list.length} thông báo trong hệ thống`;

    }



    if (!list.length) {

      tbody.innerHTML = `<tr><td colspan="8" class="px-3 py-5 text-center text-slate-400">Chưa có thông báo email nào được ghi nhận.</td></tr>`;

      return;

    }



    const badgeMap = {

      SENT: '<span class="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800"><span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>SMTP đã tiếp nhận</span>',

      FAILED: '<span class="inline-flex items-center gap-1 rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-bold text-rose-800"><span class="h-1.5 w-1.5 rounded-full bg-rose-500"></span>Thất bại</span>',

      PENDING: '<span class="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800"><span class="h-1.5 w-1.5 rounded-full bg-amber-500"></span>Chờ gửi</span>',

      SENDING: '<span class="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-800"><span class="h-1.5 w-1.5 rounded-full bg-blue-500"></span>Đang gửi</span>',

      SKIPPED: '<span class="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-700"><span class="h-1.5 w-1.5 rounded-full bg-slate-400"></span>Bỏ qua</span>',

    };



    tbody.innerHTML = list.map(item => {

      const timeStr = item.created_at ? new Date(item.created_at).toLocaleString('vi-VN', {

        day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'

      }) : 'N/A';

      const viCode = item.violation_code || (item.is_test ? '<span class="italic text-slate-400">[Email test]</span>' : 'N/A');

      const studentClass = item.student_name ? `${escapeHtml(item.student_name)} (${escapeHtml(item.class_name || '')})` : (item.is_test ? 'Kiểm tra hệ thống' : 'N/A');

      const badge = badgeMap[item.status] || `<span class="badge">${item.status}</span>`;

      const canRetry = item.status === 'FAILED';



      const retryBtn = canRetry

        ? `<button onclick="retryEmailNotification(${item.id})" class="rounded border border-brand-200 px-2 py-0.5 text-[10px] font-semibold text-brand-700 hover:bg-brand-50">Gửi lại</button>`

        : `<span class="text-slate-300">—</span>`;



      return `

        <tr class="hover:bg-slate-50/70">

          <td class="px-3 py-2 font-mono text-[10px] text-slate-500 whitespace-nowrap">${timeStr}</td>

          <td class="px-3 py-2 font-mono font-bold text-brand-800 whitespace-nowrap">${viCode}</td>

          <td class="px-3 py-2 text-slate-700 truncate max-w-[150px]">${studentClass}</td>

          <td class="px-3 py-2 font-mono text-slate-600 truncate max-w-[160px]">${escapeHtml(item.recipient_email || '(trống)')}</td>

          <td class="px-3 py-2 whitespace-nowrap">${badge}</td>

          <td class="px-3 py-2 text-center text-slate-500">${item.attempt_count}/${item.max_retries}</td>

          <td class="px-3 py-2 text-rose-600 max-w-[200px] truncate" title="${escapeHtml(item.last_error || '')}">${escapeHtml(item.last_error || '—')}</td>

          <td class="px-3 py-2 text-right whitespace-nowrap">${retryBtn}</td>

        </tr>

      `;

    }).join('');

  } catch (err) {

    console.error('Lỗi khi tải lịch sử email:', err);

  }

}



async function retryEmailNotification(notificationId) {

  try {

    const res = await fetch(`/api/conduct/email/${notificationId}/retry/`, {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken') || '',

      },

    });

    const data = await res.json();

    if (res.ok && data.success) {

      showToast(data.message || 'Đã đưa email vào hàng đợi gửi lại.', 'success');

    } else {

      showToast(data.message || 'Gửi lại email thất bại.', 'error');

    }

    await loadEmailHistory();

    loadAuditLogs();

  } catch (err) {

    showToast('Lỗi mạng khi thử gửi lại email.', 'error');

  }

}



/* ==========================================================================

   TEACHER MANAGEMENT & CLASS ASSIGNMENT (ADMIN)

   ========================================================================== */

let teachersCache = [];



async function loadTeachersManagement() {

  const tbody = document.getElementById('teachers-table-tbody');

  if (tbody) {

    tbody.innerHTML = '<tr><td colspan="6" class="text-center py-8 text-slate-400">Đang tải danh sách giáo viên...</td></tr>';

  }



  try {

    const res = await fetch('/api/conduct/teachers/');

    if (!res.ok) throw new Error('Không thể tải danh sách giáo viên');

    const data = await res.json();

    teachersCache = data.results || data;



    // KPI stats

    const total = teachersCache.length;

    const gvcnCount = teachersCache.filter(t => t.homeroom_class).length;

    const assignedCount = teachersCache.filter(t => t.assigned_classes_count > 0).length;



    const elTotal = document.getElementById('stat-teacher-total');

    const elGvcn = document.getElementById('stat-teacher-gvcn');

    const elAssigned = document.getElementById('stat-teacher-assigned');

    if (elTotal) elTotal.textContent = total;

    if (elGvcn) elGvcn.textContent = gvcnCount;

    if (elAssigned) elAssigned.textContent = assignedCount;



    // Subject filter dropdown

    const subjectSelect = document.getElementById('filter-teacher-subject');

    if (subjectSelect) {

      const subjects = Array.from(new Set(teachersCache.map(t => t.subject).filter(Boolean))).sort();

      subjectSelect.innerHTML = '<option value="">Tất cả môn học</option>' +

        subjects.map(s => `<option value="${escapeHtml(s)}">${escapeHtml(s)}</option>`).join('');

    }



    applyTeacherFilter();

  } catch (err) {

    console.error('Lỗi khi tải giáo viên:', err);

    if (tbody) {

      tbody.innerHTML = '<tr><td colspan="6" class="text-center py-8 text-rose-500 font-semibold">Lỗi kết nối máy chủ khi tải giáo viên.</td></tr>';

    }

  }

}



function applyTeacherFilter() {

  const tbody = document.getElementById('teachers-table-tbody');

  if (!tbody) return;



  const search = (document.getElementById('filter-teacher-search')?.value || '').toLowerCase().trim();

  const subject = document.getElementById('filter-teacher-subject')?.value || '';



  const filtered = teachersCache.filter(t => {

    const matchSearch = !search ||

      (t.full_name && t.full_name.toLowerCase().includes(search)) ||

      (t.username && t.username.toLowerCase().includes(search)) ||

      (t.email && t.email.toLowerCase().includes(search)) ||

      (t.phone && t.phone.toLowerCase().includes(search));

    const matchSubject = !subject || t.subject === subject;

    return matchSearch && matchSubject;

  });



  if (filtered.length === 0) {

    tbody.innerHTML = '<tr><td colspan="6" class="text-center py-8 text-slate-400">Không tìm thấy giáo viên nào phù hợp.</td></tr>';

    return;

  }



  tbody.innerHTML = filtered.map(t => {

    const subjectBadge = t.subject

      ? `<span class="inline-flex items-center px-2 py-0.5 rounded-lg text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200/60">${escapeHtml(t.subject)}</span>`

      : `<span class="text-slate-400 italic">Chưa đăng ký</span>`;



    const assignedCount = t.assigned_classes_count || 0;

    const classesList = (t.assigned_classes || []).map(c => c.name).join(', ');

    const assignedBadge = assignedCount > 0

      ? `<div class="group relative inline-block">

          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200/60 cursor-pointer">

            <i data-lucide="book-open" class="w-3 h-3 mr-1 inline"></i>${assignedCount} lớp

          </span>

          <div class="hidden group-hover:block absolute z-20 top-full left-0 mt-1 p-2 bg-slate-900 text-white text-[11px] rounded-lg shadow-lg max-w-xs whitespace-normal">

            ${escapeHtml(classesList)}

          </div>

        </div>`

      : `<span class="text-slate-400 text-xs">Chưa phân công</span>`;



    const homeroomBadge = t.homeroom_class

      ? `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-50 text-purple-700 border border-purple-200/60">

          <i data-lucide="award" class="w-3 h-3 mr-1 inline"></i>Lớp ${escapeHtml(t.homeroom_class.name)}

        </span>`

      : `<span class="text-slate-400 text-xs">—</span>`;



    const statusBadge = t.approval_status === 'APPROVED'

      ? `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700">Đã duyệt</span>`

      : `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700">Chờ duyệt</span>`;



    const revokeBtn = t.homeroom_class

      ? `<button onclick="revokeHomeroomTeacher(${t.id}, ${t.homeroom_class.id})" class="px-2.5 py-1 text-[11px] font-bold text-rose-600 hover:bg-rose-50 rounded-lg transition border border-rose-200" title="Miễn nhiệm GVCN">Miễn nhiệm</button>`

      : '';



    return `

      <tr class="hover:bg-slate-50/70 transition">

        <td class="py-3 px-4">

          <div class="font-bold text-slate-800 text-xs">${escapeHtml(t.full_name || t.username)}</div>

          <div class="text-[11px] text-slate-500 font-mono">${escapeHtml(t.email || '')} ${t.phone ? '· ' + escapeHtml(t.phone) : ''}</div>

        </td>

        <td class="py-3 px-4">${subjectBadge}</td>

        <td class="py-3 px-4">${assignedBadge}</td>

        <td class="py-3 px-4">${homeroomBadge}</td>

        <td class="py-3 px-4">${statusBadge}</td>

        <td class="py-3 px-4 text-right">

          <div class="inline-flex items-center gap-1.5">

            <button onclick="openAssignClassesModal(${t.id})" class="px-2.5 py-1 text-[11px] font-bold text-blue-700 hover:bg-blue-50 rounded-lg transition border border-blue-200" title="Phân công nhiều lớp dạy">

              <i data-lucide="list-checks" class="w-3 h-3 inline mr-0.5"></i>Phân công lớp

            </button>

            <button onclick="openAppointHomeroomModal(${t.id})" class="px-2.5 py-1 text-[11px] font-bold text-purple-700 hover:bg-purple-50 rounded-lg transition border border-purple-200" title="Bổ nhiệm GVCN">

              <i data-lucide="user-plus" class="w-3 h-3 inline mr-0.5"></i>Bổ nhiệm GVCN

            </button>

            ${revokeBtn}

          </div>

        </td>

      </tr>

    `;

  }).join('');



  lucide.createIcons();

}



async function ensureClassesLoaded() {

  if (!classesCache || classesCache.length === 0) {

    const res = await fetch('/api/conduct/classes/');

    if (res.ok) {

      const data = await res.json();

      classesCache = data.results || data;

    }

  }

}



async function openAssignClassesModal(teacherId) {

  const teacher = teachersCache.find(t => t.id === teacherId);

  if (!teacher) return;



  await ensureClassesLoaded();



  document.getElementById('modal-assign-teacher-id').value = teacher.id;

  document.getElementById('modal-assign-teacher-info').textContent =

    `Giáo viên: ${teacher.full_name} (${teacher.subject || 'Chưa rõ môn'}) · Email: ${teacher.email}`;



  const assignedIds = new Set((teacher.assigned_classes || []).map(c => c.id));



  // Render checkboxes by Grade

  [10, 11, 12].forEach(grade => {

    const container = document.getElementById(`modal-assign-grade-${grade}-grid`);

    if (!container) return;

    const gradeClasses = classesCache.filter(c => c.grade === grade);

    container.innerHTML = gradeClasses.map(cls => `

      <label class="flex items-center gap-1.5 p-1.5 border border-slate-200 rounded-lg bg-white hover:bg-blue-50/50 cursor-pointer text-xs">

        <input type="checkbox" name="assign-class-item" value="${cls.id}" data-grade="${grade}" ${assignedIds.has(cls.id) ? 'checked' : ''} onchange="updateAssignSelectedCount()" class="rounded border-slate-300 text-blue-600 focus:ring-blue-500">

        <span class="font-semibold text-slate-700">${escapeHtml(cls.name)}</span>

      </label>

    `).join('');

  });



  updateAssignSelectedCount();

  document.getElementById('modal-assign-classes').classList.remove('hidden');

}



function closeAssignClassesModal() {

  document.getElementById('modal-assign-classes').classList.add('hidden');

}



function updateAssignSelectedCount() {

  const checked = document.querySelectorAll('input[name="assign-class-item"]:checked');

  const countEl = document.getElementById('modal-assign-selected-count');

  if (countEl) countEl.textContent = checked.length;

}



function toggleSelectAllClasses(select) {

  document.querySelectorAll('input[name="assign-class-item"]').forEach(cb => {

    cb.checked = select;

  });

  updateAssignSelectedCount();

}



function toggleGradeClasses(grade) {

  const inputs = document.querySelectorAll(`input[name="assign-class-item"][data-grade="${grade}"]`);

  const anyUnchecked = Array.from(inputs).some(i => !i.checked);

  inputs.forEach(i => i.checked = anyUnchecked);

  updateAssignSelectedCount();

}



async function saveAssignClassesSubmit() {

  const teacherId = document.getElementById('modal-assign-teacher-id').value;

  if (!teacherId) return;



  const checked = Array.from(document.querySelectorAll('input[name="assign-class-item"]:checked')).map(cb => parseInt(cb.value, 10));

  const saveBtn = document.getElementById('btn-save-assign-classes');



  saveBtn.disabled = true;

  saveBtn.textContent = 'Đang lưu...';



  try {

    const res = await fetch(`/api/conduct/teachers/${teacherId}/assign-classes/`, {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken') || ''

      },

      body: JSON.stringify({ class_ids: checked })

    });

    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Lỗi khi lưu phân công lớp');



    showToast(data.message || 'Đã cập nhật phân công lớp thành công!', 'success');

    closeAssignClassesModal();

    loadTeachersManagement();

  } catch (err) {

    showToast(err.message, 'error');

  } finally {

    saveBtn.disabled = false;

    saveBtn.textContent = 'Lưu phân công';

  }

}



async function openAppointHomeroomModal(teacherId) {

  const teacher = teachersCache.find(t => t.id === teacherId);

  if (!teacher) return;



  await ensureClassesLoaded();



  document.getElementById('modal-appoint-teacher-id').value = teacher.id;

  document.getElementById('modal-appoint-teacher-name').textContent =

    `${teacher.full_name} (${teacher.subject || 'Chưa rõ môn'}) · Email: ${teacher.email}`;



  const select = document.getElementById('modal-appoint-class-select');

  select.innerHTML = '<option value="">-- Chọn lớp trong 64 lớp --</option>' +

    classesCache.map(c => `<option value="${c.id}" ${teacher.homeroom_class && teacher.homeroom_class.id === c.id ? 'selected' : ''}>Lớp ${escapeHtml(c.name)} (Khối ${c.grade})</option>`).join('');



  document.getElementById('modal-appoint-conflict-box').classList.add('hidden');

  document.getElementById('modal-appoint-confirm-replace').checked = false;

  document.getElementById('modal-appoint-notes').value = '';



  document.getElementById('modal-appoint-homeroom').classList.remove('hidden');

  checkHomeroomConflict();

}



function closeAppointHomeroomModal() {

  document.getElementById('modal-appoint-homeroom').classList.add('hidden');

}



function checkHomeroomConflict() {

  const classId = parseInt(document.getElementById('modal-appoint-class-select')?.value, 10);

  const teacherId = parseInt(document.getElementById('modal-appoint-teacher-id')?.value, 10);

  const conflictBox = document.getElementById('modal-appoint-conflict-box');

  const conflictMsg = document.getElementById('modal-appoint-conflict-msg');



  if (!classId) {

    conflictBox.classList.add('hidden');

    return;

  }



  // Find if another teacher currently has this homeroom class

  const existingGvcn = teachersCache.find(t => t.homeroom_class && t.homeroom_class.id === classId && t.id !== teacherId);

  if (existingGvcn) {

    conflictBox.classList.remove('hidden');

    conflictMsg.textContent = `Lớp này hiện đang có GVCN là Thầy/Cô ${existingGvcn.full_name} (${existingGvcn.email}). Bạn phải đánh dấu xác nhận để thay thế.`;

  } else {

    conflictBox.classList.add('hidden');

  }

}



async function submitAppointHomeroom() {

  const teacherId = document.getElementById('modal-appoint-teacher-id').value;

  const classId = document.getElementById('modal-appoint-class-select').value;

  const confirmReplace = document.getElementById('modal-appoint-confirm-replace').checked;

  const notes = document.getElementById('modal-appoint-notes').value.trim();

  const submitBtn = document.getElementById('btn-submit-appoint-homeroom');



  if (!classId) {

    showToast('Vui lòng chọn lớp học để bổ nhiệm GVCN.', 'error');

    return;

  }



  submitBtn.disabled = true;

  submitBtn.textContent = 'Đang bổ nhiệm...';



  try {

    const res = await fetch(`/api/conduct/teachers/${teacherId}/appoint-homeroom/`, {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken') || ''

      },

      body: JSON.stringify({

        class_id: parseInt(classId, 10),

        confirm_replace: confirmReplace,

        notes: notes

      })

    });

    const data = await res.json();

    if (!res.ok) {

      if (res.status === 409) {

        document.getElementById('modal-appoint-conflict-box').classList.remove('hidden');

        document.getElementById('modal-appoint-conflict-msg').textContent = data.error;

        showToast('Lớp đã có GVCN. Vui lòng xác nhận thay thế nếu muốn tiếp tục.', 'warning');

        return;

      }

      throw new Error(data.error || 'Lỗi khi bổ nhiệm GVCN');

    }



    showToast(data.message || 'Đã bổ nhiệm Giáo viên chủ nhiệm thành công!', 'success');

    closeAppointHomeroomModal();

    loadTeachersManagement();

  } catch (err) {

    showToast(err.message, 'error');

  } finally {

    submitBtn.disabled = false;

    submitBtn.textContent = 'Xác nhận Bổ nhiệm';

  }

}



async function revokeHomeroomTeacher(teacherId, classId) {

  if (!confirm('Bạn có chắc chắn muốn miễn nhiệm Giáo viên chủ nhiệm của lớp này không?')) return;



  try {

    const res = await fetch(`/api/conduct/teachers/${teacherId}/revoke-homeroom/`, {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken') || ''

      },

      body: JSON.stringify({ class_id: classId })

    });

    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Lỗi khi miễn nhiệm GVCN');



    showToast(data.message || 'Đã miễn nhiệm GVCN thành công.', 'success');

    loadTeachersManagement();

  } catch (err) {

    showToast(err.message, 'error');

  }

}





/* ==========================================================================

   TEACHER REFLECTIONS HUB (GVBM / GVCN / ADMIN)

   ========================================================================== */

let reflectionsCache = [];

let reflectionStatusFilter = 'ALL';



async function loadReflectionsData() {

  const tbody = document.getElementById('reflections-table-tbody');

  if (tbody) {

    tbody.innerHTML = '<tr><td colspan="8" class="text-center py-8 text-slate-400">Đang tải danh sách phản ánh...</td></tr>';

  }



  // Update role tag & notice banners

  const roleTag = document.getElementById('reflection-role-tag');

  const noClassesBanner = document.getElementById('gvbm-no-classes-banner');

  const assignedBar = document.getElementById('reflection-assigned-classes-bar');

  const assignedList = document.getElementById('reflection-assigned-classes-list');

  const homeroomBar = document.getElementById('reflection-homeroom-bar');

  const homeroomName = document.getElementById('reflection-homeroom-name');

  const createBtn = document.getElementById('btn-open-create-reflection');



  if (roleTag) {

    if (currentUser.is_admin) roleTag.textContent = 'Quản trị viên';

    else if (currentUser.is_gvcn) roleTag.textContent = 'Giáo viên chủ nhiệm';

    else roleTag.textContent = 'Giáo viên bộ môn';

  }



  // Check GVBM classes

  if (currentUser.is_gvbm && !currentUser.is_admin) {

    const teachingClasses = currentUser.teaching_classes || [];

    if (teachingClasses.length === 0) {

      if (noClassesBanner) noClassesBanner.classList.remove('hidden');

      if (assignedBar) assignedBar.classList.add('hidden');

      if (createBtn) createBtn.disabled = true;

    } else {

      if (noClassesBanner) noClassesBanner.classList.add('hidden');

      if (assignedBar) {

        assignedBar.classList.remove('hidden');

        if (assignedList) {

          assignedList.innerHTML = teachingClasses.map(c => `

            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-[#163A70] border border-blue-200">

              Lớp ${escapeHtml(c.name)}

            </span>

          `).join('');

        }

      }

      if (createBtn) createBtn.disabled = false;

    }

  }



  // Check GVCN homeroom

  if (currentUser.is_gvcn && currentUser.homeroom_class) {

    if (homeroomBar) {

      homeroomBar.classList.remove('hidden');

      if (homeroomName) homeroomName.textContent = currentUser.homeroom_class.name;

    }

  }



  try {

    const res = await fetch('/api/conduct/reflections/');

    if (!res.ok) throw new Error('Không thể tải danh sách phản ánh');

    const data = await res.json();

    reflectionsCache = data.results || data;



    // Counts

    const cAll = reflectionsCache.length;

    const cNew = reflectionsCache.filter(r => r.status === 'NEW').length;

    const cNeed = reflectionsCache.filter(r => r.status === 'NEED_INFO').length;

    const cResolved = reflectionsCache.filter(r => r.status === 'RESOLVED').length;

    const cClosed = reflectionsCache.filter(r => r.status === 'CLOSED').length;



    const elAll = document.getElementById('ref-count-all');

    const elNew = document.getElementById('ref-count-new');

    const elNeed = document.getElementById('ref-count-need_info');

    const elRes = document.getElementById('ref-count-resolved');

    const elClosed = document.getElementById('ref-count-closed');

    if (elAll) elAll.textContent = cAll;

    if (elNew) elNew.textContent = cNew;

    if (elNeed) elNeed.textContent = cNeed;

    if (elRes) elRes.textContent = cResolved;

    if (elClosed) elClosed.textContent = cClosed;



    // Sidebar badge

    const badge = document.getElementById('sidebar-reflections-badge');

    if (badge) {

      const pendingCount = cNew + cNeed;

      badge.textContent = pendingCount;

      badge.classList.toggle('hidden', pendingCount === 0);

    }



    renderReflectionsTable();

  } catch (err) {

    console.error('Lỗi khi tải phản ánh:', err);

    if (tbody) {

      tbody.innerHTML = '<tr><td colspan="8" class="text-center py-8 text-rose-500 font-semibold">Lỗi kết nối khi tải phản ánh.</td></tr>';

    }

  }

}



function setReflectionStatusFilter(status) {

  reflectionStatusFilter = status;

  const statuses = ['ALL', 'NEW', 'NEED_INFO', 'RESOLVED', 'CLOSED'];

  statuses.forEach(s => {

    const btn = document.getElementById(`ref-filter-${s.toLowerCase()}`);

    if (btn) {

      if (s === status) {

        btn.className = 'px-3 py-1.5 rounded-xl text-xs font-semibold bg-brand-900 text-white transition';

      } else {

        btn.className = 'px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200 transition';

      }

    }

  });

  renderReflectionsTable();

}



function renderReflectionsTable() {

  const tbody = document.getElementById('reflections-table-tbody');

  if (!tbody) return;



  const filtered = reflectionsCache.filter(r => {

    if (reflectionStatusFilter === 'ALL') return true;

    return r.status === reflectionStatusFilter;

  });



  if (filtered.length === 0) {

    tbody.innerHTML = '<tr><td colspan="8" class="text-center py-8 text-slate-400">Không có phản ánh nào trong danh mục này.</td></tr>';

    return;

  }



  const urgencyStyles = {

    NORMAL: 'bg-slate-100 text-slate-700 border-slate-200',

    HIGH: 'bg-amber-100 text-amber-800 border-amber-200',

    URGENT: 'bg-rose-100 text-rose-800 border-rose-200 font-bold'

  };



  const statusStyles = {

    NEW: 'bg-blue-100 text-blue-800 border-blue-200',

    RECEIVED: 'bg-indigo-100 text-indigo-800 border-indigo-200',

    VERIFYING: 'bg-purple-100 text-purple-800 border-purple-200',

    NEED_INFO: 'bg-amber-100 text-amber-800 border-amber-200',

    RESOLVED: 'bg-emerald-100 text-emerald-800 border-emerald-200',

    CLOSED: 'bg-slate-100 text-slate-700 border-slate-200',

    REJECTED: 'bg-rose-100 text-rose-800 border-rose-200'

  };



  tbody.innerHTML = filtered.map(r => {

    const occurredStr = formatDateTime(r.occurred_at);

    const urgencyClass = urgencyStyles[r.urgency] || 'bg-slate-100 text-slate-700';

    const statusClass = statusStyles[r.status] || 'bg-slate-100 text-slate-700';



    const evidenceLink = r.evidence_image

      ? `<a href="${escapeHtml(r.evidence_image)}" target="_blank" class="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-600 hover:underline">

          <i data-lucide="paperclip" class="w-3 h-3"></i>Xem ảnh

        </a>`

      : `<span class="text-slate-400">—</span>`;



    // Process button is available for GVCN of this class or Admin

    const canProcess = currentUser.is_admin || (currentUser.is_gvcn && currentUser.homeroom_class && currentUser.homeroom_class.id === r.school_class);

    const isCompleted = r.status === 'RESOLVED' || r.status === 'CLOSED';



    const processBtn = canProcess

      ? `<button onclick="openProcessReflectionModal(${r.id})" class="px-2.5 py-1 text-[11px] font-bold ${isCompleted ? 'text-slate-600 border-slate-200 hover:bg-slate-50' : 'text-blue-700 border-blue-300 hover:bg-blue-50 bg-blue-50/40'} rounded-lg transition border" title="Xử lý phản ánh">

          ${isCompleted ? 'Xem lại' : 'Xử lý'}

        </button>`

      : `<span class="text-slate-400 text-xs">—</span>`;



    return `

      <tr class="hover:bg-slate-50/70 transition">

        <td class="py-3 px-4">

          <div class="font-mono text-[11px] font-bold text-blue-900">${escapeHtml(r.reflection_code || '#' + r.id)}</div>

          <div class="text-[10px] text-slate-400 whitespace-nowrap">${occurredStr}</div>

        </td>

        <td class="py-3 px-4">

          <div class="font-bold text-slate-800 text-xs">Lớp ${escapeHtml(r.class_name || '--')}</div>

          <div class="text-[11px] text-slate-500">${escapeHtml(r.student_name || 'Toàn thể lớp')}</div>

        </td>

        <td class="py-3 px-4">

          <div class="text-xs font-semibold text-slate-800">${escapeHtml(r.teacher_name || '--')}</div>

          <div class="text-[10px] text-slate-500">${escapeHtml(r.subject || '')}</div>

        </td>

        <td class="py-3 px-4">

          <span class="inline-block px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700">${escapeHtml(r.reflection_type_display || r.reflection_type)}</span>

          <div class="mt-1">

            <span class="inline-block px-1.5 py-0.2 rounded text-[10px] border ${urgencyClass}">${escapeHtml(r.urgency_display || r.urgency)}</span>

          </div>

        </td>

        <td class="py-3 px-4 max-w-xs">

          <p class="text-xs text-slate-700 whitespace-pre-wrap line-clamp-3">${escapeHtml(r.content || '')}</p>

          ${r.feedback_notes ? `<div class="mt-1 p-1.5 rounded bg-blue-50/70 border border-blue-100 text-[10px] text-blue-800 font-medium"><b>Phản hồi GVCN:</b> ${escapeHtml(r.feedback_notes)}</div>` : ''}

        </td>

        <td class="py-3 px-4">${evidenceLink}</td>

        <td class="py-3 px-4">

          <span class="inline-block px-2 py-0.5 rounded-full text-[11px] font-bold border ${statusClass}">${escapeHtml(r.status_display || r.status)}</span>

        </td>

        <td class="py-3 px-4 text-right">${processBtn}</td>

      </tr>

    `;

  }).join('');



  lucide.createIcons();

}



async function openCreateReflectionModal() {

  await ensureClassesLoaded();



  const classSelect = document.getElementById('modal-reflection-class');

  classSelect.innerHTML = '<option value="">-- Chọn lớp học --</option>';



  let allowedClasses = [];

  if (currentUser.is_admin) {

    allowedClasses = classesCache;

  } else if (currentUser.teaching_classes && currentUser.teaching_classes.length > 0) {

    allowedClasses = currentUser.teaching_classes;

  }



  allowedClasses.forEach(cls => {

    const opt = document.createElement('option');

    opt.value = cls.id;

    opt.textContent = `Lớp ${cls.name}`;

    classSelect.appendChild(opt);

  });



  // Default occurred at to now

  const now = new Date(Date.now() + serverTimeOffsetMs);

  const timeInput = document.getElementById('modal-reflection-occurred-at');

  if (timeInput) timeInput.value = getLocalIsoString(now);



  document.getElementById('modal-reflection-student').innerHTML = '<option value="">-- Toàn thể lớp / Chọn học sinh --</option>';

  document.getElementById('modal-reflection-content').value = '';

  document.getElementById('modal-reflection-image').value = '';



  document.getElementById('modal-create-reflection').classList.remove('hidden');

}



function closeCreateReflectionModal() {

  document.getElementById('modal-create-reflection').classList.add('hidden');

}



async function onReflectionClassChange() {

  const classId = document.getElementById('modal-reflection-class')?.value;

  const studentSelect = document.getElementById('modal-reflection-student');

  if (!studentSelect) return;



  studentSelect.innerHTML = '<option value="">-- Toàn thể lớp / Chọn học sinh --</option>';

  if (!classId) return;



  try {

    const res = await fetch(`/api/conduct/students/?class_id=${classId}`);

    if (res.ok) {

      const data = await res.json();

      const students = data.results || data;

      students.forEach(s => {

        const opt = document.createElement('option');

        opt.value = s.id;

        opt.textContent = `${s.full_name} (${s.student_code || 'Chưa có mã'})`;

        studentSelect.appendChild(opt);

      });

    }

  } catch (err) {

    console.error('Lỗi tải học sinh:', err);

  }

}



async function submitReflectionForm(e) {

  e.preventDefault();

  const classId = document.getElementById('modal-reflection-class')?.value;

  const studentId = document.getElementById('modal-reflection-student')?.value;

  const refType = document.getElementById('modal-reflection-type')?.value;

  const urgency = document.getElementById('modal-reflection-urgency')?.value;

  const occurredAt = document.getElementById('modal-reflection-occurred-at')?.value;

  const content = document.getElementById('modal-reflection-content')?.value.trim();

  const imageFile = document.getElementById('modal-reflection-image')?.files[0];

  const submitBtn = document.getElementById('btn-submit-reflection');



  if (!classId || !content) {

    showToast('Vui lòng chọn lớp học và nhập nội dung phản ánh.', 'error');

    return;

  }



  submitBtn.disabled = true;

  submitBtn.innerHTML = '<span class="animate-pulse">Đang gửi phản ánh...</span>';



  const formData = new FormData();

  formData.append('class_id', classId);

  if (studentId) formData.append('student_id', studentId);

  formData.append('reflection_type', refType);

  formData.append('urgency', urgency);

  if (occurredAt) formData.append('occurred_at', occurredAt);

  formData.append('content', content);

  if (imageFile) formData.append('evidence_image', imageFile);



  try {

    const res = await fetch('/api/conduct/reflections/', {

      method: 'POST',

      headers: {

        'X-CSRFToken': getCookie('csrftoken') || ''

      },

      body: formData

    });

    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Lỗi khi gửi phản ánh');



    showToast(data.message || 'Đã gửi phản ánh nề nếp đến Giáo viên chủ nhiệm thành công!', 'success');

    closeCreateReflectionModal();

    loadReflectionsData();

  } catch (err) {

    showToast(err.message, 'error');

  } finally {

    submitBtn.disabled = false;

    submitBtn.innerHTML = '<i data-lucide="send" class="w-3.5 h-3.5"></i><span>Gửi phản ánh đến GVCN</span>';

    lucide.createIcons();

  }

}



async function openProcessReflectionModal(refId) {

  const ref = reflectionsCache.find(r => r.id === refId);

  if (!ref) return;



  document.getElementById('modal-process-ref-id').value = ref.id;

  document.getElementById('modal-process-ref-code').textContent = `Mã phản ánh: ${ref.reflection_code || '#' + ref.id}`;

  document.getElementById('modal-process-meta').textContent = `${formatDateTime(ref.occurred_at)} · Lớp ${ref.class_name} · ${ref.student_name || 'Toàn thể lớp'}`;

  document.getElementById('modal-process-urgency-badge').textContent = ref.urgency_display || ref.urgency;

  document.getElementById('modal-process-sender').textContent = `Người gửi: ${ref.teacher_name} (${ref.subject || 'Bộ môn'})`;

  document.getElementById('modal-process-content').textContent = ref.content || '';



  const evidenceBox = document.getElementById('modal-process-evidence-preview');

  const evidenceLink = document.getElementById('modal-process-evidence-link');

  if (ref.evidence_image) {

    evidenceBox.classList.remove('hidden');

    evidenceLink.href = ref.evidence_image;

  } else {

    evidenceBox.classList.add('hidden');

  }



  // Populate rules in case of violation conversion

  if (!rulesCache || rulesCache.length === 0) {

    const res = await fetch('/api/conduct/rules/');

    if (res.ok) {

      const data = await res.json();

      rulesCache = data.results || data;

    }

  }

  const ruleSelect = document.getElementById('modal-process-rule');

  if (ruleSelect && rulesCache) {

    ruleSelect.innerHTML = renderRuleOptionsGrouped(rulesCache, '-- Chọn nội quy vi phạm --', true);

  }



  // Reset radio to 'close'

  const defaultRadio = document.querySelector('input[name="process-action"][value="close"]');

  if (defaultRadio) defaultRadio.checked = true;

  onProcessActionChange();



  document.getElementById('modal-process-notes').value = ref.feedback_notes || '';

  document.getElementById('modal-process-reflection').classList.remove('hidden');

  lucide.createIcons();

}



function closeProcessReflectionModal() {

  document.getElementById('modal-process-reflection').classList.add('hidden');

}



function onProcessActionChange() {

  const action = document.querySelector('input[name="process-action"]:checked')?.value;

  const ruleBox = document.getElementById('modal-process-rule-box');

  if (ruleBox) {

    ruleBox.classList.toggle('hidden', action !== 'convert_violation');

  }

}



function onProcessRuleChange() {

  const ruleSelect = document.getElementById('modal-process-rule');

  const pointsEl = document.getElementById('modal-process-rule-points');

  if (!ruleSelect || !pointsEl) return;



  const opt = ruleSelect.selectedOptions[0];

  const points = opt?.getAttribute('data-points') || 0;

  pointsEl.textContent = `Điểm trừ dự kiến: -${points} điểm`;

}



async function submitProcessReflection() {

  const refId = document.getElementById('modal-process-ref-id').value;

  const action = document.querySelector('input[name="process-action"]:checked')?.value || 'close';

  const notes = document.getElementById('modal-process-notes').value.trim();

  const ruleId = document.getElementById('modal-process-rule').value;

  const submitBtn = document.getElementById('btn-submit-process-reflection');



  if (action === 'convert_violation' && !ruleId) {

    showToast('Vui lòng chọn nội quy vi phạm để chuyển đổi thành trừ điểm.', 'error');

    return;

  }



  submitBtn.disabled = true;

  submitBtn.textContent = 'Đang xử lý...';



  try {

    const payload = { action, notes };

    if (action === 'convert_violation') {

      payload.rule_id = parseInt(ruleId, 10);

    }



    const res = await fetch(`/api/conduct/reflections/${refId}/process/`, {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken') || ''

      },

      body: JSON.stringify(payload)

    });

    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Lỗi khi xử lý phản ánh');



    showToast(data.message || 'Đã xử lý phản ánh thành công!', 'success');

    closeProcessReflectionModal();

    loadReflectionsData();

  } catch (err) {

    showToast(err.message, 'error');

  } finally {

    submitBtn.disabled = false;

    submitBtn.textContent = 'Hoàn tất xử lý';

  }

}



// Automatic background intervals and focus resets REMOVED per user request

// Dashboard ONLY resets upon full page reload (F5) or manual 'Làm mới' click.







// =====================================================================

// MODULE: QUẢN LÝ LỚP HỌC VÀ PHẢN HỒI HỌC SINH DÀNH CHO GIÁO VIÊN

// =====================================================================



let teacherAssignedClasses = [];

let activeTeacherClass = null;

let teacherStudentsList = [];

let teacherFeedbacksList = [];

let activeStudentProfileData = null;

let activeFeedbackDetailData = null;

let currentFeedbackScopeFilter = 'all';

let studentFilterDebounceTimer = null;



const FEEDBACK_TYPE_MAP = {

  ACADEMIC: { label: 'Kết quả học tập', badgeClass: 'bg-blue-50 text-blue-700 border border-blue-200' },

  ATTITUDE: { label: 'Thái độ học tập', badgeClass: 'bg-emerald-50 text-emerald-700 border border-emerald-200' },

  DISCIPLINE: { label: 'Nền nếp nội quy', badgeClass: 'bg-amber-50 text-amber-700 border border-amber-200' },

  ATTENDANCE: { label: 'Chuyên cần', badgeClass: 'bg-purple-50 text-purple-700 border border-purple-200' },

  PROGRESS: { label: 'Sự tiến bộ', badgeClass: 'bg-teal-50 text-teal-700 border border-teal-200' },

  IMPROVEMENT: { label: 'Điểm cần cải thiện', badgeClass: 'bg-rose-50 text-rose-700 border border-rose-200' },

  COOPERATION: { label: 'Đề xuất phối hợp', badgeClass: 'bg-indigo-50 text-indigo-700 border border-indigo-200' },

  OTHER: { label: 'Nội dung khác', badgeClass: 'bg-slate-100 text-slate-700 border border-slate-200' }

};



const FEEDBACK_STATUS_MAP = {

  SENT: { label: 'Đã gửi', badgeClass: 'bg-slate-100 text-slate-700 border border-slate-200' },

  SEEN: { label: 'Đã xem', badgeClass: 'bg-blue-50 text-blue-700 border border-blue-200' },

  PROCESSING: { label: 'Đang xử lý / Phối hợp', badgeClass: 'bg-amber-50 text-amber-700 border border-amber-200' },

  RESOLVED: { label: 'Đã giải quyết', badgeClass: 'bg-emerald-50 text-emerald-700 border border-emerald-200' }

};



async function loadTeacherClassesModule(force = false) {

  try {
    if (!force && teacherAssignedClasses && teacherAssignedClasses.length > 0) {
      renderTeacherClassesBar();
      if (activeTeacherClass) {
        selectTeacherClass(activeTeacherClass.id);
      }
      return;
    }

    const roleBadgeText = document.getElementById('teacher-role-badge-text');

    if (roleBadgeText && currentUser) {

      if (isAdminUser(currentUser)) {

        roleBadgeText.textContent = 'Quản trị viên / Ban Giám hiệu (Toàn trường)';

      } else if (currentUser.role === 'DOAN_TRUONG' || currentUser.is_doan_truong) {

        roleBadgeText.textContent = 'Bí thư Đoàn trường (Giám sát toàn trường)';

      } else if (currentUser.role === 'BGH' || currentUser.is_bgh) {

        roleBadgeText.textContent = 'Ban Giám hiệu (Toàn trường)';

      } else if (currentUser.role === 'GVCN' || currentUser.is_gvcn) {

        roleBadgeText.textContent = 'Giáo viên chủ nhiệm (GVCN)';

      } else if (currentUser.role === 'GVBM' || currentUser.is_gvbm) {

        roleBadgeText.textContent = 'Giáo viên bộ môn (GVBM)';

      } else if (currentUser.is_student || currentUser.role === 'HOC_SINH') {
        roleBadgeText.textContent = 'Học sinh (Lớp học của tôi)';
      } else {
        roleBadgeText.textContent = currentUser.role_display || 'Cán bộ giáo viên';
      }

    }



    const res = await fetch('/api/conduct/teacher-classes/', {

      headers: { 'Accept': 'application/json' }

    });

    if (!res.ok) throw new Error('Không thể tải danh sách lớp phân công.');



    teacherAssignedClasses = await res.json();

    const countBadge = document.getElementById('teacher-classes-count-badge');

    if (countBadge) countBadge.textContent = `${teacherAssignedClasses.length} lớp`;



    renderTeacherClassesBar();



    if (teacherAssignedClasses.length > 0) {

      const targetClass = (activeTeacherClass && teacherAssignedClasses.some(c => c.id === activeTeacherClass.id))

        ? activeTeacherClass

        : teacherAssignedClasses[0];

      selectTeacherClass(targetClass.id);

    } else {

      const container = document.getElementById('teacher-active-class-container');

      if (container) {

        container.innerHTML = `

          <div class="bg-white rounded-2xl p-12 text-center border border-slate-200">

            <div class="w-16 h-16 rounded-2xl bg-amber-50 text-amber-600 mx-auto flex items-center justify-center mb-4">

              <i data-lucide="alert-circle" class="w-8 h-8"></i>

            </div>

            <h3 class="text-base font-bold text-slate-800">Chưa có phân công lớp học</h3>

            <p class="text-xs text-slate-500 mt-1 max-w-md mx-auto leading-relaxed">

              Tài khoản hiện chưa được phân công làm giáo viên chủ nhiệm hoặc giáo viên bộ môn cho lớp nào trong năm học hiện tại. Vui lòng liên hệ Ban Giám hiệu hoặc Quản trị viên để kiểm tra lịch phân công.

            </p>

          </div>

        `;

        if (window.lucide) lucide.createIcons();

      }

    }

  } catch (err) {

    showToast(err.message, 'error');

  }

}



function renderTeacherClassesBar() {

  const bar = document.getElementById('teacher-assigned-classes-bar');

  if (!bar) return;



  if (teacherAssignedClasses.length === 0) {

    bar.innerHTML = '<span class="text-xs text-slate-400 italic">Chưa có lớp nào trong danh sách.</span>';

    return;

  }



  const searchVal = (document.getElementById('class-quick-search-input')?.value || '').toLowerCase().trim();

  const isAdmin = currentUser && (isAdminUser(currentUser) || currentUser.role === 'BGH' || currentUser.is_bgh || currentUser.role === 'DOAN_TRUONG' || currentUser.is_doan_truong);



  // Điền dropdown chọn nhanh lớp học (nhóm theo khối 10, 11, 12)

  const quickSelect = document.getElementById('class-quick-select-dropdown');

  if (quickSelect) {

    const k10 = teacherAssignedClasses.filter(c => c.grade === 10).sort(naturalClassSort);

    const k11 = teacherAssignedClasses.filter(c => c.grade === 11).sort(naturalClassSort);

    const k12 = teacherAssignedClasses.filter(c => c.grade === 12).sort(naturalClassSort);

    

    let optHtml = '<option value="">-- Chọn nhanh lớp học --</option>';

    if (k10.length > 0) {

      optHtml += `<optgroup label="Khối 10 (${k10.length} lớp)">`;

      optHtml += k10.map(c => `<option value="${c.id}" ${activeTeacherClass && activeTeacherClass.id === c.id ? 'selected' : ''}>Lớp ${escapeHtml(c.name)} (${c.student_count} HS · GVCN: ${escapeHtml(c.homeroom_teacher_name || 'Chưa có')})</option>`).join('');

      optHtml += `</optgroup>`;

    }

    if (k11.length > 0) {

      optHtml += `<optgroup label="Khối 11 (${k11.length} lớp)">`;

      optHtml += k11.map(c => `<option value="${c.id}" ${activeTeacherClass && activeTeacherClass.id === c.id ? 'selected' : ''}>Lớp ${escapeHtml(c.name)} (${c.student_count} HS · GVCN: ${escapeHtml(c.homeroom_teacher_name || 'Chưa có')})</option>`).join('');

      optHtml += `</optgroup>`;

    }

    if (k12.length > 0) {

      optHtml += `<optgroup label="Khối 12 (${k12.length} lớp)">`;

      optHtml += k12.map(c => `<option value="${c.id}" ${activeTeacherClass && activeTeacherClass.id === c.id ? 'selected' : ''}>Lớp ${escapeHtml(c.name)} (${c.student_count} HS · GVCN: ${escapeHtml(c.homeroom_teacher_name || 'Chưa có')})</option>`).join('');

      optHtml += `</optgroup>`;

    }

    quickSelect.innerHTML = optHtml;

    if (activeTeacherClass) {

      quickSelect.value = String(activeTeacherClass.id);

    }

  }



  let filtered = teacherAssignedClasses.filter(c => {

    if (activeClassGradeFilter !== 'ALL' && String(c.grade) !== String(activeClassGradeFilter)) {

      return false;

    }

    if (searchVal && !c.name.toLowerCase().includes(searchVal) && !(c.homeroom_teacher_name && c.homeroom_teacher_name.toLowerCase().includes(searchVal))) {

      return false;

    }

    return true;

  });



  filtered.sort(naturalClassSort);



  const countBadge = document.getElementById('teacher-classes-count-badge');

  if (countBadge) {

    countBadge.textContent = `${filtered.length} / ${teacherAssignedClasses.length} lớp`;

  }



  if (filtered.length === 0) {

    bar.innerHTML = '<span class="text-xs text-slate-400 italic py-2">Không tìm thấy lớp học nào phù hợp với bộ lọc.</span>';

    return;

  }



  bar.innerHTML = filtered.map(c => {

    const isSelected = activeTeacherClass && activeTeacherClass.id === c.id;

    const isGVCN = c.assignment_role === 'GVCN';

    

    let rolePill = '';

    if (isAdmin) {

      const hasGvcn = c.homeroom_teacher_name && c.homeroom_teacher_name !== 'Chưa phân công';

      rolePill = hasGvcn

        ? `<span class="px-1.5 py-0.5 text-[10px] font-bold rounded ${isSelected ? 'bg-white/20 text-white' : 'bg-blue-50 text-blue-700 border border-blue-200'}">GVCN: ${escapeHtml(c.homeroom_teacher_name)}</span>`

        : `<span class="px-1.5 py-0.5 text-[10px] font-bold rounded ${isSelected ? 'bg-amber-400 text-slate-900' : 'bg-amber-50 text-amber-700 border border-amber-200'}">Chưa có GVCN</span>`;

    } else {

      rolePill = isGVCN 

        ? '<span class="px-1.5 py-0.5 text-[10px] font-bold rounded bg-blue-100 text-blue-800">Chủ nhiệm</span>'

        : `<span class="px-1.5 py-0.5 text-[10px] font-bold rounded bg-emerald-100 text-emerald-800">${escapeHtml(c.subjects.join(', ') || 'Bộ môn')}</span>`;

    }



    return `

      <button type="button" onclick="selectTeacherClass(${c.id})" 

        class="group px-3 py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 border shadow-sm ${

          isSelected 

            ? 'bg-blue-600 text-white border-blue-600 ring-2 ring-blue-600/30' 

            : 'bg-white text-slate-700 border-slate-200 hover:border-blue-400 hover:bg-blue-50/50'

        }">

        <span class="w-6 h-6 rounded-lg ${isSelected ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-700'} flex items-center justify-center font-bold text-[11px]">

          ${escapeHtml(c.name.substring(0, 3))}

        </span>

        <span class="font-bold text-sm">${escapeHtml(c.name)}</span>

        ${rolePill}

        <span class="text-[11px] ${isSelected ? 'text-blue-100' : 'text-slate-400'}">(${c.student_count} HS)</span>
        ${isAdmin ? `
          <span onclick="event.stopPropagation(); openAssignHomeroomModal(${c.id})" class="ml-1 px-2 py-0.5 text-[10px] font-bold rounded ${isSelected ? 'bg-white text-blue-800 hover:bg-blue-50' : 'bg-blue-100 text-blue-800 hover:bg-blue-200'} shadow-sm transition" title="Phân công GVCN cho lớp ${escapeHtml(c.name)}">
            Phân công GVCN
          </span>
        ` : ''}
      </button>

    `;

  }).join('');

}



async function selectTeacherClass(classId) {

  const found = teacherAssignedClasses.find(c => c.id === classId);

  if (!found) return;

  activeTeacherClass = found;



  const quickSelect = document.getElementById('class-quick-select-dropdown');

  if (quickSelect && quickSelect.value !== String(classId)) {

    quickSelect.value = String(classId);

  }



  renderTeacherClassesBar();



  // Update header info

  const avatar = document.getElementById('active-class-avatar');

  const title = document.getElementById('active-class-title');

  const roleTag = document.getElementById('active-class-role-tag');

  const desc = document.getElementById('active-class-desc');



  if (avatar) avatar.textContent = found.name;

  if (title) title.textContent = `Lớp ${found.name}`;

  if (roleTag) {

    roleTag.textContent = found.assignment_role_display;

    if (found.assignment_role === 'ADMIN') {

      roleTag.className = 'px-2 py-0.5 text-[11px] font-semibold rounded bg-purple-100 text-purple-800 border border-purple-200';

    } else if (found.assignment_role === 'DOAN_TRUONG') {

      roleTag.className = 'px-2 py-0.5 text-[11px] font-semibold rounded bg-indigo-100 text-indigo-800 border border-indigo-200';

    } else if (found.assignment_role === 'GVCN') {

      roleTag.className = 'px-2 py-0.5 text-[11px] font-semibold rounded bg-blue-100 text-blue-800 border border-blue-200';

    } else {

      roleTag.className = 'px-2 py-0.5 text-[11px] font-semibold rounded bg-emerald-100 text-emerald-800 border border-emerald-200';

    }

  }

  if (desc) {

    desc.textContent = `Sĩ số: ${found.student_count} học sinh • GVCN: ${found.homeroom_teacher_name || 'Chưa phân công'} • Năm học: ${found.academic_year_name}`;

  }

  updateClassMonitorHeader(found.monitor_name, found.can_assign_monitor);



  // Admin button visibility
  const canAssign = currentUser && (
    isAdminUser(currentUser) ||
    currentUser.role === 'BGH' || currentUser.is_bgh ||
    currentUser.role === 'SUPER_ADMIN' || currentUser.is_super_admin ||
    currentUser.role === 'DOAN_TRUONG' || currentUser.is_doan_truong
  );

  const adminBtn = document.getElementById('btn-admin-assign-homeroom');
  if (adminBtn) {
    adminBtn.classList.toggle('hidden', !canAssign);
  }

  const adminBtnInline = document.getElementById('btn-admin-assign-homeroom-inline');
  if (adminBtnInline) {
    adminBtnInline.classList.toggle('hidden', !canAssign);
  }

  const isStudentUser = currentUser && (currentUser.is_student || currentUser.role === 'HOC_SINH');
  document.getElementById('btn-quick-add-feedback-roster')?.classList.toggle('hidden', isStudentUser);
  document.getElementById('btn-quick-add-feedback-tab')?.classList.toggle('hidden', isStudentUser);



  // Load students, feedbacks, and teachers concurrently

  await Promise.all([

    fetchClassStudents(found.id),

    fetchClassFeedbacks(found.id),

    loadClassTeachers(found.id)

  ]);

}



async function fetchClassStudents(classId) {

  try {

    const res = await fetch(`/api/conduct/teacher-classes/${classId}/students/`);

    if (!res.ok) throw new Error('Không thể tải danh sách học sinh của lớp này.');

    const data = await res.json();

    teacherStudentsList = data.students || [];
    if (activeTeacherClass && activeTeacherClass.id === classId) {
      activeTeacherClass.monitor_id = data.monitor_id;
      activeTeacherClass.monitor_name = data.monitor_name;
      activeTeacherClass.can_assign_monitor = data.can_assign_monitor;
    }
    updateClassMonitorHeader(data.monitor_name, data.can_assign_monitor);
    filterTeacherStudentsList();

    // Populate student filter in feedbacks tab
    const stuFilter = document.getElementById('teacher-feedback-student-filter');
    if (stuFilter) {
      const prevVal = stuFilter.value;
      let optHtml = '<option value="">-- Tất cả học sinh --</option>';
      teacherStudentsList.forEach((s, idx) => {
        optHtml += `<option value="${s.id}" ${prevVal === String(s.id) ? 'selected' : ''}>${s.stt || (idx + 1)}. [${escapeHtml(s.student_code)}] ${escapeHtml(s.full_name)}</option>`;
      });
      stuFilter.innerHTML = optHtml;
    }

  } catch (err) {

    showToast(err.message, 'error');

  }

}



async function fetchClassFeedbacks(classId) {

  try {

    const res = await fetch(`/api/conduct/feedbacks/?class_id=${classId}`);

    if (!res.ok) throw new Error('Không thể tải lịch sử phản hồi.');

    const fbData = await res.json();
    teacherFeedbacksList = Array.isArray(fbData) ? fbData : (fbData.results || []);

    

    // Update count badge

    const badge = document.getElementById('class-feedback-count-badge');

    if (badge) badge.textContent = teacherFeedbacksList.length;



    renderTeacherFeedbacks();

  } catch (err) {

    console.error('Error fetching feedbacks:', err);

  }

}



function debounceTeacherStudentFilter() {

  clearTimeout(studentFilterDebounceTimer);

  studentFilterDebounceTimer = setTimeout(() => {

    filterTeacherStudentsList();

  }, 200);

}



function removeAccents(str) {

  if (!str) return '';

  return str.normalize('NFD')

    .replace(/[\u0300-\u036f]/g, '')

    .replace(/[đĐ]/g, m => m === 'đ' ? 'd' : 'D')

    .toLowerCase();

}



function filterTeacherStudentsList() {

  const searchInput = document.getElementById('teacher-student-search-input');

  const statusFilter = document.getElementById('teacher-student-status-filter');

  const query = (searchInput?.value || '').trim();

  const queryNorm = removeAccents(query);

  const statusVal = statusFilter?.value || '';



  const filtered = teacherStudentsList.filter(s => {

    if (statusVal && s.status !== statusVal) return false;

    if (query) {

      const codeMatch = s.student_code.toLowerCase().includes(query.toLowerCase());

      const nameMatch = s.full_name.toLowerCase().includes(query.toLowerCase()) || removeAccents(s.full_name).includes(queryNorm);

      if (!codeMatch && !nameMatch) return false;

    }

    return true;

  });



  const counter = document.getElementById('filtered-students-counter');

  if (counter) counter.textContent = `Hiển thị ${filtered.length} / ${teacherStudentsList.length} học sinh`;



  renderTeacherStudentsTable(filtered);

}



function renderTeacherStudentsTable(students) {
  const tbody = document.getElementById('teacher-students-table-body');
  const mobileList = document.getElementById('teacher-students-mobile-list');
  const emptyState = document.getElementById('teacher-students-empty-state');

  if (!tbody || !mobileList) return;

  if (students.length === 0) {
    tbody.innerHTML = '';
    mobileList.innerHTML = '';
    if (emptyState) emptyState.classList.remove('hidden');
    return;
  }

  if (emptyState) emptyState.classList.add('hidden');

  const isStudent = currentUser && (currentUser.is_student || currentUser.role === 'HOC_SINH');
  const myStudentCode = (currentUser?.student_code || currentUser?.meta?.student_code || currentUser?.username || '').trim().toLowerCase();
  const myStudentId = currentUser?.student_profile?.id || currentUser?.student_id || currentUser?.meta?.student_id;

  // Desktop Table
  tbody.innerHTML = students.map((s, idx) => {
    const isStudying = s.status === 'STUDYING';
    const statusBadge = isStudying
      ? '<span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">Đang học</span>'
      : `<span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">${escapeHtml(s.status_display)}</span>`;

    const feedbackCountBadge = s.feedback_count > 0
      ? `<span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-700">${s.feedback_count}</span>`
      : `<span class="text-slate-400 text-xs">0</span>`;

    const isSelf = isStudent && ((s.student_code && s.student_code.trim().toLowerCase() === myStudentCode) || (s.id && s.id === myStudentId) || (s.user_id && s.user_id === currentUser?.id));
    const isMonitor = Boolean(s.is_class_monitor || (activeTeacherClass && activeTeacherClass.monitor_id === s.id));
    const monitorBadge = isMonitor
      ? `<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 ml-1.5 shadow-2xs" title="Lớp trưởng"><i data-lucide="crown" class="w-3 h-3 text-amber-600"></i> Lớp trưởng</span>`
      : '';

    let monitorActionBtn = '';
    if (!isStudent && activeTeacherClass && activeTeacherClass.can_assign_monitor) {
      if (isMonitor) {
        monitorActionBtn = `
          <button type="button" onclick="confirmRemoveMonitor(${s.id}, '${escapeHtml(s.full_name)}')" title="Hủy vai trò Lớp trưởng"
            class="px-2 py-1 text-xs font-semibold rounded-lg text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 transition-colors flex items-center gap-1">
            <i data-lucide="crown" class="w-3.5 h-3.5 text-amber-600"></i>
            <span>Hủy LT</span>
          </button>
        `;
      } else {
        monitorActionBtn = `
          <button type="button" onclick="confirmAssignMonitor(${s.id}, '${escapeHtml(s.full_name)}')" title="Phân công làm Lớp trưởng"
            class="px-2 py-1 text-xs font-semibold rounded-lg text-slate-600 hover:text-amber-700 hover:bg-amber-50 border border-slate-200 hover:border-amber-200 transition-colors flex items-center gap-1">
            <i data-lucide="crown" class="w-3.5 h-3.5 text-amber-500"></i>
            <span>Phân LT</span>
          </button>
        `;
      }
    }

    let actionBtnsHtml = '';
    if (isStudent) {
      if (isSelf) {
        actionBtnsHtml = `
          <button type="button" onclick="openStudentProfileModal(${s.id})" title="Xem hồ sơ của tôi"
            class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 transition-colors flex items-center gap-1">
            <i data-lucide="user" class="w-3.5 h-3.5"></i>
            <span>Hồ sơ của tôi</span>
          </button>
        `;
      } else {
        actionBtnsHtml = `<span class="text-xs text-slate-400 italic">Bạn cùng lớp</span>`;
      }
    } else {
      actionBtnsHtml = `
        <button type="button" onclick="openStudentProfileModal(${s.id})" title="Xem hồ sơ chi tiết"
          class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors flex items-center gap-1">
          <i data-lucide="user" class="w-3.5 h-3.5"></i>
          <span>Hồ sơ</span>
        </button>
        ${monitorActionBtn}
        <button type="button" onclick="openSendFeedbackModal(${s.id}, ${activeTeacherClass.id}, '${escapeHtml(s.full_name)}', '${escapeHtml(activeTeacherClass.name)}')" title="Nhận xét đích danh học sinh này"
          class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-colors flex items-center gap-1">
          <i data-lucide="message-square-plus" class="w-3.5 h-3.5"></i>
          <span>Nhận xét</span>
        </button>
        <button type="button" onclick="openViolationModalForStudent(${activeTeacherClass.id}, ${s.id}, '${escapeHtml(s.full_name)}')" title="Lập biên bản vi phạm kỷ luật"
          class="px-2 py-1 text-xs font-medium rounded-lg text-rose-600 hover:bg-rose-50 transition-colors">
          <i data-lucide="scale" class="w-3.5 h-3.5"></i>
        </button>
      `;
    }

    const nameCellHtml = (isStudent && !isSelf)
      ? `<div class="flex items-center flex-wrap gap-1"><span class="font-bold text-slate-900">${escapeHtml(s.full_name)}</span>${monitorBadge}</div>`
      : `
        <div class="flex items-center flex-wrap gap-1">
          <button type="button" onclick="openStudentProfileModal(${s.id})" class="font-bold text-slate-900 hover:text-blue-600 transition-colors text-left flex items-center gap-1.5 group">
            <span>${escapeHtml(s.full_name)}</span>
            <i data-lucide="external-link" class="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 text-blue-500 transition-opacity"></i>
          </button>
          ${monitorBadge}
        </div>
      `;

    return `
      <tr class="hover:bg-slate-50/80 transition-colors ${isSelf ? 'bg-blue-50/40' : ''}">
        <td class="py-3 px-4 text-center font-medium text-slate-500">${s.stt || (idx + 1)}</td>
        <td class="py-3 px-4 font-mono font-bold text-slate-700">${escapeHtml(s.student_code)}</td>
        <td class="py-3 px-4">
          ${nameCellHtml}
        </td>
        <td class="py-3 px-4 text-slate-600">${escapeHtml(s.gender_display || '')}</td>
        <td class="py-3 px-4 text-slate-600">${escapeHtml(s.date_of_birth || '')}</td>
        <td class="py-3 px-4 text-center">${statusBadge}</td>
        <td class="py-3 px-4 text-center">${feedbackCountBadge}</td>
        <td class="py-3 px-4 text-right">
          <div class="flex items-center justify-end gap-1.5">
            ${actionBtnsHtml}
          </div>
        </td>
      </tr>
    `;
  }).join('');

  // Mobile Cards
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
      : `<div class="flex items-center flex-wrap gap-1"><button type="button" onclick="openStudentProfileModal(${s.id})" class="font-bold text-slate-900 text-sm hover:text-blue-600 text-left">${escapeHtml(s.full_name)}</button>${mobileMonitorBadge}</div>`;

    return `
      <div class="p-3.5 bg-white rounded-xl border ${isSelf ? 'border-blue-300 ring-2 ring-blue-50 bg-blue-50/20' : 'border-slate-200'} space-y-2 mb-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-xs">${s.stt || (idx + 1)}</span>
            ${mobileNameHtml}
          </div>
          <span class="font-mono text-xs font-bold text-slate-600">${escapeHtml(s.student_code)}</span>
        </div>
        <div class="flex items-center justify-between text-xs text-slate-500 pt-1 border-t border-slate-100">
          <span>${escapeHtml(s.gender_display || '')} • ${escapeHtml(s.date_of_birth || '')}</span>
          <span class="font-semibold text-blue-700">${s.feedback_count} phản hồi</span>
        </div>
        <div class="flex items-center justify-end gap-2 pt-2">
          ${mobileActionHtml}
        </div>
      </div>
    `;
  }).join('');

  if (window.lucide) lucide.createIcons();
}

function switchTeacherSubTab(tabName) {
  const btnRoster = document.getElementById('subtab-btn-roster');
  const btnFeedbacks = document.getElementById('subtab-btn-feedbacks');
  const btnTeachers = document.getElementById('subtab-btn-teachers');
  const paneRoster = document.getElementById('subtab-pane-roster');
  const paneFeedbacks = document.getElementById('subtab-pane-feedbacks');
  const paneTeachers = document.getElementById('subtab-pane-teachers');

  const activeBtnClass = 'px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-white text-slate-900 shadow-sm transition-all flex items-center gap-1.5';
  const inactiveBtnClass = 'px-3.5 py-1.5 text-xs font-semibold rounded-lg text-slate-600 hover:text-slate-900 transition-all flex items-center gap-1.5';

  if (tabName === 'roster') {
    if (btnRoster) btnRoster.className = activeBtnClass;
    if (btnFeedbacks) btnFeedbacks.className = inactiveBtnClass;
    if (btnTeachers) btnTeachers.className = inactiveBtnClass;
    if (paneRoster) paneRoster.classList.remove('hidden');
    if (paneFeedbacks) paneFeedbacks.classList.add('hidden');
    if (paneTeachers) paneTeachers.classList.add('hidden');
  } else if (tabName === 'feedbacks') {
    if (btnRoster) btnRoster.className = inactiveBtnClass;
    if (btnFeedbacks) btnFeedbacks.className = activeBtnClass;
    if (btnTeachers) btnTeachers.className = inactiveBtnClass;
    if (paneRoster) paneRoster.classList.add('hidden');
    if (paneFeedbacks) paneFeedbacks.classList.remove('hidden');
    if (paneTeachers) paneTeachers.classList.add('hidden');
    renderTeacherFeedbacks();
  } else if (tabName === 'teachers') {
    if (btnRoster) btnRoster.className = inactiveBtnClass;
    if (btnFeedbacks) btnFeedbacks.className = inactiveBtnClass;
    if (btnTeachers) btnTeachers.className = activeBtnClass;
    if (paneRoster) paneRoster.classList.add('hidden');
    if (paneFeedbacks) paneFeedbacks.classList.add('hidden');
    if (paneTeachers) paneTeachers.classList.remove('hidden');
    loadClassTeachers();
  }

  if (window.lucide) lucide.createIcons();
}



function filterFeedbacksScope(scope) {

  currentFeedbackScopeFilter = scope;

  ['all', 'my', 'attention'].forEach(id => {

    const btn = document.getElementById(`fb-filter-${id}`);

    if (btn) {

      const isTarget = (scope === 'all' && id === 'all') || (scope === 'my_sent' && id === 'my') || (scope === 'attention' && id === 'attention');

      btn.className = isTarget

        ? 'px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-50 text-blue-700 border border-blue-200 transition-colors'

        : 'px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors';

    }

  });

  renderTeacherFeedbacks();

}



function applyFeedbackFilters() {

  renderTeacherFeedbacks();

}



function renderTeacherFeedbacks() {

  const container = document.getElementById('teacher-feedbacks-container');

  const emptyState = document.getElementById('teacher-feedbacks-empty-state');

  const typeFilter = document.getElementById('teacher-feedback-type-filter');

  const selectedType = typeFilter?.value || '';



  if (!container) return;



  let filtered = [...teacherFeedbacksList];



  // Scope filter

  if (currentFeedbackScopeFilter === 'my_sent') {

    filtered = filtered.filter(f => f.teacher === currentUser.id || f.teacher_username === currentUser.username);

  } else if (currentFeedbackScopeFilter === 'attention') {

    filtered = filtered.filter(f => f.priority === 'ATTENTION' || f.priority === 'URGENT' || f.status === 'PROCESSING');

  }



  // Type filter

  if (selectedType) {

    filtered = filtered.filter(f => f.feedback_type === selectedType);

  }



  

  // Student filter
  const studentFilter = document.getElementById('teacher-feedback-student-filter');
  const selectedStudent = studentFilter?.value || '';
  if (selectedStudent) {
    filtered = filtered.filter(f => String(f.student) === String(selectedStudent));
  }
if (filtered.length === 0) {

    container.innerHTML = '';

    if (emptyState) emptyState.classList.remove('hidden');

    return;

  }



  if (emptyState) emptyState.classList.add('hidden');



  container.innerHTML = filtered.map(f => {

    const typeInfo = FEEDBACK_TYPE_MAP[f.feedback_type] || { label: f.feedback_type_display || 'Phản hồi', badgeClass: 'bg-slate-100 text-slate-700' };

    const statusInfo = FEEDBACK_STATUS_MAP[f.status] || { label: f.status_display || 'Đã gửi', badgeClass: 'bg-slate-100 text-slate-700' };

    const isAttention = f.priority === 'ATTENTION' || f.priority === 'URGENT';

    const dateStr = f.created_at ? new Date(f.created_at).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';



    return `

      <div class="bg-white rounded-2xl p-4 shadow-sm border border-slate-200 hover:border-blue-300 transition-all space-y-3 cursor-pointer" onclick="openFeedbackDetailModal(${f.id})">

        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">

          <div class="flex items-center gap-2">

            <span class="font-mono text-xs font-bold text-slate-500">${escapeHtml(f.feedback_code)}</span>

            <span class="font-bold text-slate-900">${escapeHtml(f.student_name)}</span>

            <span class="text-xs text-slate-500">(${escapeHtml(f.class_name)})</span>

          </div>

          <div class="flex items-center gap-2">

            <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold ${statusInfo.badgeClass}">${statusInfo.label}</span>

            <span class="text-xs text-slate-400 font-medium">${dateStr}</span>

          </div>

        </div>



        <div class="flex flex-wrap items-center gap-2">

          <span class="px-2 py-0.5 rounded-md text-[11px] font-semibold ${typeInfo.badgeClass}">${typeInfo.label}</span>

          ${isAttention ? '<span class="px-2 py-0.5 rounded-md text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1"><i data-lucide="alert-triangle" class="w-3 h-3"></i> Cần quan tâm</span>' : ''}

          ${f.subject ? `<span class="px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 text-slate-700">Môn ${escapeHtml(f.subject)}</span>` : ''}

          <span class="text-xs text-slate-500 ml-auto">Người gửi: <strong class="text-slate-800">${escapeHtml(f.teacher_name || f.teacher_username)}</strong> (${escapeHtml(f.teacher_role)})</span>

        </div>



        <p class="text-xs md:text-sm text-slate-700 leading-relaxed line-clamp-2">${escapeHtml(f.content)}</p>



        <div class="flex items-center justify-between pt-1 text-xs">

          <div class="flex items-center gap-1.5 text-blue-600 font-medium">

            <i data-lucide="message-square" class="w-3.5 h-3.5"></i>

            <span>${f.replies_count || (f.replies ? f.replies.length : 0)} trao đổi phối hợp</span>

          </div>

          <span class="text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1">

            <span>Chi tiết & Trả lời</span>

            <i data-lucide="chevron-right" class="w-3.5 h-3.5"></i>

          </span>

        </div>

      </div>

    `;

  }).join('');



  if (window.lucide) lucide.createIcons();

}



// ---------------------------------------------------------------------

// MODAL: GỬI PHẢN HỒI HỌC SINH

// ---------------------------------------------------------------------



function openSendFeedbackModal(studentId = null, classId = null, studentName = '', className = '') {
  const form = document.getElementById('form-send-student-feedback');
  if (form) form.reset();

  const cId = classId || activeTeacherClass?.id || '';
  const cName = className || activeTeacherClass?.name || '';
  const classIdInput = document.getElementById('fb-form-class-id');
  if (classIdInput) classIdInput.value = cId;
  const classNameEl = document.getElementById('fb-form-class-name');
  if (classNameEl) classNameEl.textContent = cName;

  // Update role badge in modal
  const roleBadge = document.getElementById('fb-form-teacher-role-badge');
  if (roleBadge && activeTeacherClass) {
    roleBadge.textContent = activeTeacherClass.assignment_role_display || (activeTeacherClass.assignment_role === 'GVBM' ? 'Giáo viên bộ môn' : 'Giáo viên chủ nhiệm');
  }

  // Populate student select dropdown with all students of active class
  const studentSelect = document.getElementById('fb-form-student-select');
  if (studentSelect) {
    let opts = '<option value="">-- Chọn đích danh học sinh từ danh sách lớp --</option>';
    if (teacherStudentsList && teacherStudentsList.length > 0) {
      teacherStudentsList.forEach((s, idx) => {
        const isSelected = studentId && (String(s.id) === String(studentId));
        opts += `<option value="${s.id}" ${isSelected ? 'selected' : ''}>${s.stt || (idx + 1)}. [${escapeHtml(s.student_code)}] ${escapeHtml(s.full_name)}${s.gender_display ? ' (' + escapeHtml(s.gender_display) + ')' : ''}</option>`;
      });
    }
    studentSelect.innerHTML = opts;
    if (studentId) {
      studentSelect.value = String(studentId);
    }
  }

  // Update student id and banner
  const studentIdInput = document.getElementById('fb-form-student-id');
  const nameEl = document.getElementById('fb-form-student-name');
  const codeEl = document.getElementById('fb-form-student-code');

  if (studentId) {
    if (studentIdInput) studentIdInput.value = studentId;
    const sObj = teacherStudentsList.find(s => String(s.id) === String(studentId));
    if (nameEl) nameEl.textContent = studentName || (sObj ? sObj.full_name : '');
    if (codeEl) codeEl.textContent = sObj ? `(${sObj.student_code})` : '';
  } else {
    if (studentIdInput) studentIdInput.value = '';
    if (nameEl) nameEl.textContent = 'Chưa chọn';
    if (codeEl) codeEl.textContent = '';
  }

  // Auto fill subject for GVBM if applicable
  const subjectInput = document.getElementById('fb-form-subject');
  if (subjectInput && activeTeacherClass) {
    if (activeTeacherClass.assignment_role === 'GVBM' && activeTeacherClass.subjects && activeTeacherClass.subjects.length > 0) {
      subjectInput.value = activeTeacherClass.subjects[0];
    } else if (activeTeacherClass.assignment_role !== 'GVBM') {
      subjectInput.value = '';
    }
  }

  updateFbCharCount();
  const errorEl = document.getElementById('fb-form-content-error');
  if (errorEl) errorEl.classList.add('hidden');

  openModal('modal-send-student-feedback');
  if (window.lucide) lucide.createIcons();
}

function onFeedbackStudentSelectChange(val) {
  const studentIdInput = document.getElementById('fb-form-student-id');
  if (studentIdInput) studentIdInput.value = val || '';
  const sObj = teacherStudentsList.find(s => String(s.id) === String(val));
  const nameEl = document.getElementById('fb-form-student-name');
  const codeEl = document.getElementById('fb-form-student-code');
  const errorEl = document.getElementById('fb-form-content-error');
  if (errorEl) errorEl.classList.add('hidden');

  if (sObj) {
    if (nameEl) nameEl.textContent = sObj.full_name;
    if (codeEl) codeEl.textContent = `(${sObj.student_code})`;
  } else {
    if (nameEl) nameEl.textContent = 'Chưa chọn';
    if (codeEl) codeEl.textContent = '';
  }
}



function insertFeedbackStarter(text) {

  const textarea = document.getElementById('fb-form-content');

  if (!textarea) return;

  if (textarea.value.trim().length > 0) {

    textarea.value += ' ' + text;

  } else {

    textarea.value = text;

  }

  updateFbCharCount();

  textarea.focus();

}



function updateFbCharCount() {

  const textarea = document.getElementById('fb-form-content');

  const counter = document.getElementById('fb-char-counter');

  if (!textarea || !counter) return;

  const len = textarea.value.length;

  counter.textContent = `${len}/1000 ký tự`;

  if (len >= 950) {

    counter.className = 'text-[11px] text-rose-500 font-mono font-bold';

  } else {

    counter.className = 'text-[11px] text-slate-400 font-mono';

  }

}



async function handleSendFeedbackSubmit(event) {

  event.preventDefault();

  const submitBtn = document.getElementById('fb-submit-btn');

  const btnText = document.getElementById('fb-submit-btn-text');

  const errorEl = document.getElementById('fb-form-content-error');



  const studentId = document.getElementById('fb-form-student-id').value;

  const classId = document.getElementById('fb-form-class-id').value;

  const content = document.getElementById('fb-form-content').value.trim();

  const feedbackType = document.getElementById('fb-form-type').value;

  const priority = document.getElementById('fb-form-priority').value;

  const visibilityScope = document.getElementById('fb-form-scope').value;

  const subject = document.getElementById('fb-form-subject').value.trim();

  const strengths = document.getElementById('fb-form-strengths')?.value?.trim() || '';

  const weaknesses = document.getElementById('fb-form-weaknesses')?.value?.trim() || '';

  const cooperationProposal = document.getElementById('fb-form-cooperation')?.value?.trim() || '';



    if (!studentId || isNaN(parseInt(studentId, 10))) {
    if (errorEl) {
      errorEl.textContent = 'Vui lòng chọn đích danh học sinh cần nhận xét.';
      errorEl.classList.remove('hidden');
    }
    document.getElementById('fb-form-student-select')?.focus();
    return;
  }

  if (!content) {

    if (errorEl) {

      errorEl.textContent = 'Vui lòng nhập nội dung phản hồi.';

      errorEl.classList.remove('hidden');

    }

    return;

  }



  try {

    if (submitBtn) submitBtn.disabled = true;

    if (btnText) btnText.textContent = 'Đang gửi...';



    const payload = {

      student_id: parseInt(studentId, 10),

      class_id: parseInt(classId, 10),

      content,

      feedback_type: feedbackType,

      priority,

      visibility_scope: visibilityScope,

      subject,

      strengths,

      weaknesses,

      cooperation_proposal: cooperationProposal

    };



    const res = await fetch('/api/conduct/feedbacks/', {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken') || ''

      },

      body: JSON.stringify(payload)

    });



    const data = await res.json();

    if (!res.ok) {

      throw new Error(data.error || 'Lỗi khi gửi phản hồi.');

    }



    showToast('Đã lưu nhận xét học sinh thành công!', 'success');

    closeModal('modal-send-student-feedback');



    // Refresh class feedbacks and students list

    if (activeTeacherClass) {

      await Promise.all([

        fetchClassFeedbacks(activeTeacherClass.id),

        fetchClassStudents(activeTeacherClass.id)

      ]);

    }

  } catch (err) {

    if (errorEl) {

      errorEl.textContent = err.message;

      errorEl.classList.remove('hidden');

    }

    showToast(err.message, 'error');

  } finally {

    if (submitBtn) submitBtn.disabled = false;

    if (btnText) btnText.textContent = 'Gửi phản hồi';

  }

}



// ---------------------------------------------------------------------

// MODAL: HỒ SƠ CHI TIẾT HỌC SINH (4 TABS)

// ---------------------------------------------------------------------



async function openStudentProfileModal(studentId) {

  try {

    const res = await fetch(`/api/conduct/students/${studentId}/profile-detail/`);

    if (!res.ok) throw new Error('Không thể tải hồ sơ chi tiết học sinh.');

    activeStudentProfileData = await res.json();



    const g = activeStudentProfileData.general;

    document.getElementById('student-modal-name').textContent = g.full_name;

    document.getElementById('student-modal-code').textContent = g.student_code;

    document.getElementById('student-modal-sub').textContent = `Lớp ${g.school_class_name} • Phòng: ${g.room_number || 'N/A'} • GVCN: ${g.homeroom_teacher_name}`;

    

    const avatar = document.getElementById('student-modal-avatar');

    if (avatar) {

      const parts = g.full_name.trim().split(' ');

      avatar.textContent = parts.length > 1 ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase() : g.full_name.substring(0, 2).toUpperCase();

    }



    // Tab 1: General Info Grid

    const generalGrid = document.getElementById('sp-general-info-grid');

    if (generalGrid) {

      generalGrid.innerHTML = `

        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">

          <span class="text-slate-400 block text-[11px] font-semibold uppercase">Mã học sinh</span>

          <span class="font-bold text-slate-800 text-sm font-mono">${escapeHtml(g.student_code)}</span>

        </div>

        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">

          <span class="text-slate-400 block text-[11px] font-semibold uppercase">Lớp học & Khối</span>

          <span class="font-bold text-slate-800 text-sm">Lớp ${escapeHtml(g.school_class_name)} (Khối ${g.grade})</span>

        </div>

        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">

          <span class="text-slate-400 block text-[11px] font-semibold uppercase">Ngày sinh</span>

          <span class="font-bold text-slate-800 text-sm">${escapeHtml(g.date_of_birth || 'Chưa cập nhật')}</span>

        </div>

        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">

          <span class="text-slate-400 block text-[11px] font-semibold uppercase">Giới tính</span>

          <span class="font-bold text-slate-800 text-sm">${escapeHtml(g.gender_display)}</span>

        </div>

        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">

          <span class="text-slate-400 block text-[11px] font-semibold uppercase">Trạng thái học tập</span>

          <span class="font-bold text-emerald-700 text-sm">${escapeHtml(g.status_display)}</span>

        </div>

        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl">

          <span class="text-slate-400 block text-[11px] font-semibold uppercase">Đoàn viên / Sao đỏ</span>

          <span class="font-bold text-slate-800 text-sm">

            ${g.is_union_member ? 'Đoàn viên TNCS' : 'Chưa kết nạp'} • ${g.is_red_star ? 'Đội viên Sao đỏ' : 'Không thuộc Sao đỏ'}

          </span>

        </div>

      `;

    }



    // Tab 2: Feedbacks

    const feedbacks = activeStudentProfileData.feedbacks || [];

    const feedbackBadge = document.getElementById('sp-feedback-badge');

    if (feedbackBadge) feedbackBadge.textContent = feedbacks.length;

    const fbList = document.getElementById('sp-feedback-list');

    if (fbList) {

      if (feedbacks.length === 0) {

        fbList.innerHTML = '<p class="text-xs text-slate-400 italic text-center p-6">Chưa có phản hồi nào được ghi nhận cho học sinh này.</p>';

      } else {

        fbList.innerHTML = feedbacks.map(f => `

          <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1.5">

            <div class="flex items-center justify-between text-xs">

              <span class="font-bold text-slate-900">${escapeHtml(f.feedback_type_display)}</span>

              <span class="text-slate-400">${new Date(f.created_at).toLocaleDateString('vi-VN')}</span>

            </div>

            <p class="text-xs text-slate-700 leading-relaxed">${escapeHtml(f.content)}</p>

            <div class="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-200/50">

              <span>Người gửi: <strong>${escapeHtml(f.teacher_name)}</strong> (${escapeHtml(f.teacher_role)})</span>

              <span class="font-semibold text-blue-700">${f.status_display}</span>

            </div>

          </div>

        `).join('');

      }

    }



    // Tab 3: Violations (Read-only)

    const violations = activeStudentProfileData.violations || [];

    const violTable = document.getElementById('sp-violations-table-body');

    if (violTable) {

      if (violations.length === 0) {

        violTable.innerHTML = '<tr><td colspan="4" class="p-4 text-center text-slate-400 text-xs italic">Học sinh không có vi phạm nào được ghi nhận. Tinh thần nền nếp rất tốt!</td></tr>';

      } else {

        violTable.innerHTML = violations.map(v => `

          <tr class="hover:bg-slate-50">

            <td class="p-3 text-slate-600 font-medium">${escapeHtml(v.occurred_at)}</td>

            <td class="p-3">

              <span class="font-bold text-slate-800 block">${escapeHtml(v.rule_name)}</span>

              <span class="text-[11px] text-slate-400">${escapeHtml(v.location || 'Khuôn viên trường')}</span>

            </td>

            <td class="p-3 text-center font-bold text-rose-600">-${v.points_deducted}đ</td>

            <td class="p-3 text-center">

              <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">${escapeHtml(v.status_display)}</span>

            </td>

          </tr>

        `).join('');

      }

    }



    // Tab 4: Competition Summary

    const comp = activeStudentProfileData.competition || {};

    const compGrid = document.getElementById('sp-competition-summary');

    if (compGrid) {

      compGrid.innerHTML = `

        <div class="p-4 bg-blue-50 border border-blue-200 rounded-xl text-center">

          <span class="text-blue-600 text-xs font-bold uppercase block mb-1">Lớp học</span>

          <span class="text-xl font-bold text-blue-900">${escapeHtml(comp.class_name || '')}</span>

        </div>

        <div class="p-4 bg-amber-50 border border-amber-200 rounded-xl text-center">

          <span class="text-amber-600 text-xs font-bold uppercase block mb-1">Tổng vụ vi phạm</span>

          <span class="text-xl font-bold text-amber-900">${comp.total_violations_count || 0}</span>

        </div>

        <div class="p-4 bg-rose-50 border border-rose-200 rounded-xl text-center">

          <span class="text-rose-600 text-xs font-bold uppercase block mb-1">Điểm trừ nền nếp</span>

          <span class="text-xl font-bold text-rose-900">-${comp.total_points_deducted || 0}đ</span>

        </div>

      `;

    }



    const isStudentViewer = currentUser && (currentUser.is_student || currentUser.role === 'HOC_SINH');
    const compTab = document.getElementById('sp-tab-competition');
    if (compTab) compTab.classList.toggle('hidden', isStudentViewer);
    const compPane = document.getElementById('sp-pane-competition');
    if (compPane && isStudentViewer) compPane.classList.add('hidden');
    const quickFbBtn = document.getElementById('sp-quick-feedback-btn');
    if (quickFbBtn) quickFbBtn.classList.toggle('hidden', isStudentViewer);

    switchStudentProfileTab('general');

    openModal('modal-student-detail-profile');

    if (window.lucide) lucide.createIcons();

  } catch (err) {

    showToast(err.message, 'error');

  }

}



function switchStudentProfileTab(tabName) {

  const tabs = ['general', 'feedback', 'violations', 'competition'];

  tabs.forEach(t => {

    const btn = document.getElementById(`sp-tab-${t}`);

    const pane = document.getElementById(`sp-pane-${t}`);

    if (t === tabName) {

      if (btn) btn.className = 'px-3.5 py-3 text-xs font-semibold text-blue-600 border-b-2 border-blue-600 flex items-center gap-1.5 whitespace-nowrap';

      if (pane) pane.classList.remove('hidden');

    } else {

      if (btn) btn.className = 'px-3.5 py-3 text-xs font-semibold text-slate-600 hover:text-slate-900 border-b-2 border-transparent flex items-center gap-1.5 whitespace-nowrap';

      if (pane) pane.classList.add('hidden');

    }

  });

}



function triggerFeedbackFromProfileModal() {

  if (!activeStudentProfileData || !activeStudentProfileData.general) return;

  const g = activeStudentProfileData.general;

  closeModal('modal-student-detail-profile');

  openSendFeedbackModal(g.id, g.school_class_id, g.full_name, g.school_class_name);

}



// ---------------------------------------------------------------------

// MODAL: CHI TIẾT PHẢN HỒI & TRAO ĐỔI PHỐI HỢP

// ---------------------------------------------------------------------



async function openFeedbackDetailModal(feedbackId) {

  try {

    // Automatically trigger mark-seen

    fetch(`/api/conduct/feedbacks/${feedbackId}/mark-seen/`, {

      method: 'POST',

      headers: { 'X-CSRFToken': getCookie('csrftoken') || '' }

    }).catch(console.error);



    const res = await fetch(`/api/conduct/feedbacks/${feedbackId}/`);

    if (!res.ok) throw new Error('Không thể tải chi tiết phản hồi.');

    activeFeedbackDetailData = await res.json();

    const f = activeFeedbackDetailData;



    document.getElementById('fd-modal-code').textContent = f.feedback_code;

    const statusInfo = FEEDBACK_STATUS_MAP[f.status] || { label: f.status_display, badgeClass: 'bg-slate-100 text-slate-700' };

    const statusBadge = document.getElementById('fd-modal-status-badge');

    if (statusBadge) {

      statusBadge.textContent = statusInfo.label;

      statusBadge.className = `px-2 py-0.5 text-[10px] font-bold rounded-full ${statusInfo.badgeClass}`;

    }



    document.getElementById('fd-modal-time').textContent = f.created_at ? new Date(f.created_at).toLocaleString('vi-VN') : '';

    document.getElementById('fd-modal-student').textContent = f.student_name;

    document.getElementById('fd-modal-class').textContent = `Lớp ${f.class_name}`;

    document.getElementById('fd-modal-author').textContent = `${f.teacher_name || f.teacher_username} (${f.teacher_role})`;

    document.getElementById('fd-modal-type-badge').textContent = f.feedback_type_display;

    document.getElementById('fd-modal-priority-badge').textContent = f.priority_display;

    document.getElementById('fd-modal-scope-badge').textContent = f.visibility_scope_display;

    document.getElementById('fd-modal-content').textContent = f.content;



    // Extra fields

    const extraContainer = document.getElementById('fd-modal-extra-container');

    if (extraContainer) {

      const hasExtra = f.strengths || f.weaknesses || f.cooperation_proposal;

      if (hasExtra) {

        extraContainer.classList.remove('hidden');

        extraContainer.innerHTML = `

          ${f.strengths ? `<div class="p-2.5 bg-emerald-50 text-emerald-900 rounded-lg text-xs"><strong>Điểm mạnh:</strong> ${escapeHtml(f.strengths)}</div>` : ''}

          ${f.weaknesses ? `<div class="p-2.5 bg-amber-50 text-amber-900 rounded-lg text-xs"><strong>Cần cải thiện:</strong> ${escapeHtml(f.weaknesses)}</div>` : ''}

          ${f.cooperation_proposal ? `<div class="p-2.5 bg-blue-50 text-blue-900 rounded-lg text-xs"><strong>Đề xuất phối hợp:</strong> ${escapeHtml(f.cooperation_proposal)}</div>` : ''}

        `;

      } else {

        extraContainer.classList.add('hidden');

      }

    }



    // Discussion Replies List

    renderFeedbackRepliesList(f.replies || []);



    // Status select

    const statusSelect = document.getElementById('fd-status-select');

    if (statusSelect) statusSelect.value = f.status;



    openModal('modal-feedback-detail-reply');

    if (window.lucide) lucide.createIcons();

  } catch (err) {

    showToast(err.message, 'error');

  }

}



function renderFeedbackRepliesList(replies) {

  const container = document.getElementById('fd-modal-replies-list');

  const countEl = document.getElementById('fd-modal-replies-count');

  if (countEl) countEl.textContent = replies.length;

  if (!container) return;



  if (replies.length === 0) {

    container.innerHTML = '<p class="text-xs text-slate-400 italic py-2">Chưa có trao đổi nào. Nhập tin nhắn phía dưới để gửi trao đổi cho đồng nghiệp.</p>';

    return;

  }



  container.innerHTML = replies.map(r => {

    const isMe = currentUser && (r.author === currentUser.id || r.author_username === currentUser.username);

    const timeStr = r.created_at ? new Date(r.created_at).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '';



    return `

      <div class="p-3 rounded-xl text-xs space-y-1 ${isMe ? 'bg-blue-50 border border-blue-200 ml-4' : 'bg-slate-50 border border-slate-200 mr-4'}">

        <div class="flex items-center justify-between font-semibold">

          <span class="${isMe ? 'text-blue-800' : 'text-slate-800'}">${escapeHtml(r.author_name || r.author_username)} (${escapeHtml(r.author_role)})</span>

          <span class="text-[11px] text-slate-400 font-normal">${timeStr}</span>

        </div>

        <p class="text-slate-700 leading-relaxed whitespace-pre-wrap">${escapeHtml(r.content)}</p>

      </div>

    `;

  }).join('');

}



async function handleSubmitFeedbackReply() {

  if (!activeFeedbackDetailData) return;

  const input = document.getElementById('fd-reply-input');

  const submitBtn = document.getElementById('fd-reply-submit-btn');

  const content = (input?.value || '').trim();



  if (!content) {

    showToast('Vui lòng nhập nội dung trao đổi.', 'warning');

    return;

  }



  try {

    if (submitBtn) submitBtn.disabled = true;

    const res = await fetch(`/api/conduct/feedbacks/${activeFeedbackDetailData.id}/reply/`, {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken') || ''

      },

      body: JSON.stringify({ content })

    });



    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Lỗi khi gửi trao đổi.');



    activeFeedbackDetailData = data;

    input.value = '';

    renderFeedbackRepliesList(data.replies || []);



    // Update status badge to processing

    const statusInfo = FEEDBACK_STATUS_MAP[data.status] || { label: data.status_display, badgeClass: 'bg-slate-100 text-slate-700' };

    const statusBadge = document.getElementById('fd-modal-status-badge');

    if (statusBadge) {

      statusBadge.textContent = statusInfo.label;

      statusBadge.className = `px-2 py-0.5 text-[10px] font-bold rounded-full ${statusInfo.badgeClass}`;

    }



    showToast('Đã gửi trao đổi thành công!', 'success');



    // Refresh class feedbacks

    if (activeTeacherClass) {

      fetchClassFeedbacks(activeTeacherClass.id);

    }

  } catch (err) {

    showToast(err.message, 'error');

  } finally {

    if (submitBtn) submitBtn.disabled = false;

  }

}



async function handleUpdateFeedbackStatus() {

  if (!activeFeedbackDetailData) return;

  const select = document.getElementById('fd-status-select');

  const statusVal = select?.value;



  try {

    const res = await fetch(`/api/conduct/feedbacks/${activeFeedbackDetailData.id}/update-status/`, {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken') || ''

      },

      body: JSON.stringify({ status: statusVal })

    });



    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Lỗi khi cập nhật trạng thái.');



    activeFeedbackDetailData = data;

    const statusInfo = FEEDBACK_STATUS_MAP[data.status] || { label: data.status_display, badgeClass: 'bg-slate-100 text-slate-700' };

    const statusBadge = document.getElementById('fd-modal-status-badge');

    if (statusBadge) {

      statusBadge.textContent = statusInfo.label;

      statusBadge.className = `px-2 py-0.5 text-[10px] font-bold rounded-full ${statusInfo.badgeClass}`;

    }



    showToast(`Đã chuyển trạng thái sang "${statusInfo.label}"`, 'success');



    if (activeTeacherClass) {

      fetchClassFeedbacks(activeTeacherClass.id);

    }

  } catch (err) {

    showToast(err.message, 'error');

  }

}



function openViolationModalForStudent(classId, studentId, studentName) {
  if (!confirm(`Xác nhận chuyển sang lập biên bản vi phạm kỷ luật cho học sinh ${studentName}?`)) {
    return;
  }

  openQuickViolationModal();

  const classSelect = document.getElementById('modal-violation-class');
  const studentSelect = document.getElementById('modal-violation-student');
  const gradeSelect = document.getElementById('modal-violation-grade');

  const foundCls = (classesCache || []).find(c => Number(c.id) === Number(classId));
  const grade = foundCls ? String(foundCls.grade || '') : '';
  if (gradeSelect) gradeSelect.value = grade;
  populateModalViolationClasses(grade, classId);

  if (classSelect) {
    classSelect.value = classId;
    if (typeof handleClassChangeForStudents === 'function') {
      handleClassChangeForStudents(classId);
      setTimeout(() => {
        if (studentSelect) studentSelect.value = studentId;
      }, 300);
    } else if (studentSelect) {
      studentSelect.value = studentId;
    }
  }

  openModal('modal-quick-violation');
}







// ---------------------------------------------------------------------

// QUẢN TRỊ VIÊN: XEM DANH SÁCH LỚP VÀ PHÂN CÔNG GIÁO VIÊN CHỦ NHIỆM

// ---------------------------------------------------------------------



let activeClassGradeFilter = 'ALL';



function filterClassesByGrade(grade) {

  activeClassGradeFilter = grade;

  ['all', '10', '11', '12'].forEach(g => {

    const btn = document.getElementById(`grade-filter-${g}`);

    if (btn) {

      const isTarget = (grade === 'ALL' && g === 'all') || (grade === g);

      btn.className = isTarget

        ? 'px-2.5 py-1 rounded-lg font-semibold bg-white text-slate-900 shadow-sm transition-all'

        : 'px-2.5 py-1 rounded-lg font-semibold text-slate-600 hover:text-slate-900 transition-all';

    }

  });

  renderTeacherClassesBar();

}



let _classQuickSearchTimer = null;
function filterClassesBySearch() {
  clearTimeout(_classQuickSearchTimer);
  _classQuickSearchTimer = setTimeout(() => {
    renderTeacherClassesBar();
  }, 150);
}



async function openAssignHomeroomModal(classId = null) {
  if (classId) {
    const target = (teacherAssignedClasses || []).find(c => c.id === classId);
    if (target) {
      activeTeacherClass = target;
      await selectTeacherClass(classId);
    }
  }

  if (!activeTeacherClass && teacherAssignedClasses && teacherAssignedClasses.length > 0) {
    activeTeacherClass = teacherAssignedClasses[0];
    await selectTeacherClass(activeTeacherClass.id);
  }

  if (!activeTeacherClass) {
    showToast('Vui lòng chọn một lớp học trước khi phân công.', 'warning');
    return;
  }

  const modal = document.getElementById('modal-assign-homeroom-teacher');
  if (!modal) return;

  const classSelect = document.getElementById('assign-homeroom-class-select');
  if (classSelect && teacherAssignedClasses && teacherAssignedClasses.length > 0) {
    classSelect.innerHTML = teacherAssignedClasses.map(c => 
      `<option value="${c.id}" ${c.id === activeTeacherClass.id ? 'selected' : ''}>Lớp ${escapeHtml(c.name)} (Khối ${c.grade})</option>`
    ).join('');
  }

  document.getElementById('assign-homeroom-class-id').value = activeTeacherClass.id;
  document.getElementById('assign-homeroom-confirm-replace').value = 'false';
  document.getElementById('assign-homeroom-class-name').textContent = `Lớp ${activeTeacherClass.name} (Khối ${activeTeacherClass.grade})`;

  const currentGvcnText = activeTeacherClass.homeroom_teacher_name && activeTeacherClass.homeroom_teacher_name !== 'Chưa phân công'
    ? activeTeacherClass.homeroom_teacher_name
    : 'Chưa phân công GVCN';
  document.getElementById('assign-homeroom-current-gvcn').textContent = currentGvcnText;

  const conflictBox = document.getElementById('assign-homeroom-conflict-box');
  if (conflictBox) conflictBox.classList.add('hidden');
  const confirmCb = document.getElementById('assign-homeroom-confirm-checkbox');
  if (confirmCb) confirmCb.checked = false;

  const notesInput = document.getElementById('assign-homeroom-notes');
  if (notesInput) notesInput.value = '';

  await loadEligibleTeachersForHomeroom();

  openModal('modal-assign-homeroom-teacher');
  if (window.lucide) lucide.createIcons();
}

async function onAssignHomeroomClassSelectChange(newClassId) {
  if (!newClassId) return;
  const numId = Number(newClassId);
  const target = (teacherAssignedClasses || []).find(c => c.id === numId);
  if (target) {
    activeTeacherClass = target;
    await selectTeacherClass(numId);
  }
  document.getElementById('assign-homeroom-class-id').value = activeTeacherClass.id;
  document.getElementById('assign-homeroom-class-name').textContent = `Lớp ${activeTeacherClass.name} (Khối ${activeTeacherClass.grade})`;
  const currentGvcnText = activeTeacherClass.homeroom_teacher_name && activeTeacherClass.homeroom_teacher_name !== 'Chưa phân công'
    ? activeTeacherClass.homeroom_teacher_name
    : 'Chưa phân công GVCN';
  document.getElementById('assign-homeroom-current-gvcn').textContent = currentGvcnText;
  const conflictBox = document.getElementById('assign-homeroom-conflict-box');
  if (conflictBox) conflictBox.classList.add('hidden');
  const confirmCb = document.getElementById('assign-homeroom-confirm-checkbox');
  if (confirmCb) confirmCb.checked = false;
  await loadEligibleTeachersForHomeroom();
}



async function loadEligibleTeachersForHomeroom() {

  const select = document.getElementById('assign-homeroom-teacher-select');

  if (!select) return;

  select.innerHTML = '<option value="">-- Đang tải danh sách giáo viên... --</option>';



  try {

    const res = await fetch('/api/conduct/teacher-classes/eligible-teachers/');

    if (!res.ok) throw new Error('Không thể tải danh sách giáo viên.');

    const teachers = await res.json();



    if (teachers.length === 0) {

      select.innerHTML = '<option value="">-- Không có giáo viên nào sẵn sàng --</option>';

      return;

    }



    select.innerHTML = '<option value="">-- Chọn Giáo viên bổ nhiệm làm GVCN --</option>' +

      teachers.map(t => {

        const isCurrent = activeTeacherClass && t.id === activeTeacherClass.homeroom_teacher_id;

        const cnInfo = t.current_homeroom_class ? ` [Hiện đang CN lớp ${t.current_homeroom_class}]` : '';

        const subjectInfo = t.subject ? ` (Môn ${t.subject})` : '';

        return `<option value="${t.id}" ${isCurrent ? 'selected' : ''}>${escapeHtml(t.full_name || t.username)}${subjectInfo}${cnInfo}</option>`;

      }).join('');

  } catch (err) {

    select.innerHTML = '<option value="">-- Lỗi tải danh sách giáo viên --</option>';

    showToast(err.message, 'error');

  }

}



function toggleConfirmReplaceCheckbox(checked) {

  const input = document.getElementById('assign-homeroom-confirm-replace');

  if (input) input.value = checked ? 'true' : 'false';

}



async function handleAssignHomeroomSubmit(event) {

  event.preventDefault();

  if (!activeTeacherClass) return;



  const select = document.getElementById('assign-homeroom-teacher-select');

  const teacherId = select?.value;

  const notes = document.getElementById('assign-homeroom-notes')?.value?.trim() || '';

  const confirmReplace = document.getElementById('assign-homeroom-confirm-replace')?.value === 'true';

  const submitBtn = document.getElementById('btn-submit-assign-homeroom');



  if (!teacherId) {

    showToast('Vui lòng chọn một giáo viên để phân công làm GVCN.', 'warning');

    return;

  }



  try {

    if (submitBtn) submitBtn.disabled = true;



    const payload = {

      teacher_id: parseInt(teacherId, 10),

      notes,

      confirm_replace: confirmReplace

    };



    const res = await fetch(`/api/conduct/teacher-classes/${activeTeacherClass.id}/assign-homeroom/`, {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken') || ''

      },

      body: JSON.stringify(payload)

    });



    const data = await res.json();



    // Handle 409 Conflict (class already has GVCN and need confirmation)

    if (res.status === 409 && data.conflict) {

      const conflictBox = document.getElementById('assign-homeroom-conflict-box');

      const conflictMsg = document.getElementById('assign-homeroom-conflict-msg');

      if (conflictBox) conflictBox.classList.remove('hidden');

      if (conflictMsg) conflictMsg.textContent = data.message || 'Lớp này hiện đã có GVCN. Vui lòng xác nhận thay thế.';

      showToast('Lớp đã có GVCN. Vui lòng tích xác nhận thay thế để tiếp tục.', 'warning');

      return;

    }



    if (!res.ok) {

      throw new Error(data.error || 'Lỗi khi phân công GVCN.');

    }



    showToast(data.message || 'Phân công Giáo viên chủ nhiệm thành công!', 'success');

    closeModal('modal-assign-homeroom-teacher');



    // Update in-memory state

    activeTeacherClass.homeroom_teacher_name = data.homeroom_teacher_name;

    activeTeacherClass.homeroom_teacher_id = data.homeroom_teacher_id;

    const foundIdx = teacherAssignedClasses.findIndex(c => c.id === activeTeacherClass.id);

    if (foundIdx !== -1) {

      teacherAssignedClasses[foundIdx].homeroom_teacher_name = data.homeroom_teacher_name;

      teacherAssignedClasses[foundIdx].homeroom_teacher_id = data.homeroom_teacher_id;

    }



    // Update active class header

    const desc = document.getElementById('active-class-desc');

    if (desc) {

      desc.textContent = `Sĩ số: ${activeTeacherClass.student_count} học sinh • GVCN: ${data.homeroom_teacher_name} • Năm học: ${activeTeacherClass.academic_year_name}`;

    }



    renderTeacherClassesBar();
    await loadClassTeachers(activeTeacherClass.id);

  } catch (err) {

    showToast(err.message, 'error');

  } finally {

    if (submitBtn) submitBtn.disabled = false;

  }

}



async function handleRevokeHomeroom() {

  if (!activeTeacherClass) return;

  if (!confirm(`Bạn có chắc chắn muốn thu hồi phân công GVCN của Lớp ${activeTeacherClass.name}?`)) {

    return;

  }



  try {

    const res = await fetch(`/api/conduct/teacher-classes/${activeTeacherClass.id}/assign-homeroom/`, {

      method: 'POST',

      headers: {

        'Content-Type': 'application/json',

        'X-CSRFToken': getCookie('csrftoken') || ''

      },

      body: JSON.stringify({ teacher_id: null })

    });



    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Lỗi khi thu hồi GVCN.');



    showToast('Đã thu hồi phân công GVCN thành công.', 'success');

    closeModal('modal-assign-homeroom-teacher');



    activeTeacherClass.homeroom_teacher_name = 'Chưa phân công';

    activeTeacherClass.homeroom_teacher_id = null;

    const foundIdx = teacherAssignedClasses.findIndex(c => c.id === activeTeacherClass.id);

    if (foundIdx !== -1) {

      teacherAssignedClasses[foundIdx].homeroom_teacher_name = 'Chưa phân công';

      teacherAssignedClasses[foundIdx].homeroom_teacher_id = null;

    }



    const desc = document.getElementById('active-class-desc');

    if (desc) {

      desc.textContent = `Sĩ số: ${activeTeacherClass.student_count} học sinh • GVCN: Chưa phân công • Năm học: ${activeTeacherClass.academic_year_name}`;

    }



    renderTeacherClassesBar();
    await loadClassTeachers(activeTeacherClass.id);

  } catch (err) {

    showToast(err.message, 'error');

  }

}







function renderRuleOptionsGrouped(rulesList, emptyLabel = '-- Chọn lỗi vi phạm --', showPoints = true) {

  if (!Array.isArray(rulesList) || rulesList.length === 0) {

    return `<option value="">${emptyLabel}</option>`;

  }

  const activeRules = rulesList.filter(r => r.is_active !== false);

  const groups = {};

  activeRules.forEach(r => {

    const cat = r.category_name || 'Nội quy chung';

    if (!groups[cat]) groups[cat] = [];

    groups[cat].push(r);

  });

  let html = `<option value="">${emptyLabel}</option>`;

  for (const [catName, list] of Object.entries(groups)) {

    html += `<optgroup label="📁 ${escapeHtml(catName)}">`;

    list.forEach(r => {

      const pt = parseFloat(r.default_points_deducted || r.point_deduction || 0);

      const ptStr = showPoints ? ` (-${pt.toFixed(pt % 1 === 0 ? 0 : 1)}đ)` : '';

      html += `<option value="${r.id}" data-points="${pt}">[${escapeHtml(r.code)}] ${escapeHtml(r.name)}${ptStr}</option>`;

    });

    html += `</optgroup>`;

  }

  return html;

}



let activeRulesFilterCategory = 'ALL';



function openRulesReferenceModal(selectedRuleId = null) {

  const modal = document.getElementById('modal-conduct-rules-lookup');

  if (!modal) return;

  modal.classList.remove('hidden');



  renderRulesCategoryChips();

  filterRulesReferenceTable();



  if (typeof lucide !== 'undefined' && lucide.createIcons) {

    lucide.createIcons();

  }

}



function closeRulesReferenceModal() {

  const modal = document.getElementById('modal-conduct-rules-lookup');

  if (modal) modal.classList.add('hidden');

}



function renderRulesCategoryChips() {

  const container = document.getElementById('rules-category-chips');

  if (!container) return;



  const activeRules = (rulesCache || []).filter(r => r.is_active !== false);

  const catCounts = {};

  activeRules.forEach(r => {

    const c = r.category_name || 'Khác';

    catCounts[c] = (catCounts[c] || 0) + 1;

  });



  const categories = Object.keys(catCounts);



  let html = `<button type="button" onclick="setRulesFilterCategory('ALL')" class="px-2.5 py-1 rounded-lg text-xs font-semibold whitespace-nowrap transition ${activeRulesFilterCategory === 'ALL' ? 'bg-brand-600 text-white shadow-xs' : 'bg-slate-200/70 text-slate-700 hover:bg-slate-300'}">Tất cả (${activeRules.length})</button>`;



  categories.forEach(cat => {

    const isActive = activeRulesFilterCategory === cat;

    html += `<button type="button" onclick="setRulesFilterCategory('${escapeHtml(cat)}')" class="px-2.5 py-1 rounded-lg text-xs font-semibold whitespace-nowrap transition ${isActive ? 'bg-brand-600 text-white shadow-xs' : 'bg-slate-200/70 text-slate-700 hover:bg-slate-300'}">${escapeHtml(cat)} (${catCounts[cat]})</button>`;

  });



  container.innerHTML = html;

}



function setRulesFilterCategory(cat) {

  activeRulesFilterCategory = cat;

  renderRulesCategoryChips();

  filterRulesReferenceTable();

}



let _rulesFilterTimer = null;
function filterRulesReferenceTable() {
  clearTimeout(_rulesFilterTimer);
  _rulesFilterTimer = setTimeout(() => {
    _doExecuteRulesReferenceFilter();
  }, 150);
}

function _doExecuteRulesReferenceFilter() {
  const tbody = document.getElementById('rules-reference-tbody');

  const countBadge = document.getElementById('rules-filter-count-badge');

  const searchInput = document.getElementById('rules-filter-search');

  if (!tbody) return;



  const activeRules = (rulesCache || []).filter(r => r.is_active !== false);

  const query = (searchInput?.value || '').trim().toLowerCase();



  const filtered = activeRules.filter(r => {

    const matchCat = (activeRulesFilterCategory === 'ALL' || r.category_name === activeRulesFilterCategory);

    if (!matchCat) return false;

    if (!query) return true;

    const code = (r.code || '').toLowerCase();

    const name = (r.name || '').toLowerCase();

    const cat = (r.category_name || '').toLowerCase();

    const pt = String(r.default_points_deducted || '');

    return code.includes(query) || name.includes(query) || cat.includes(query) || pt.includes(query);

  });



  if (countBadge) {

    countBadge.textContent = `Hiển thị: ${filtered.length} / ${activeRules.length} quy định`;

  }



  if (filtered.length === 0) {

    tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-slate-400">Không tìm thấy quy tắc nào phù hợp với từ khóa "${escapeHtml(query)}"</td></tr>`;

    return;

  }



  const getPointsBadge = (pt) => {

    const p = parseFloat(pt);

    if (p <= 3) return `<span class="px-2 py-0.5 rounded-full font-mono font-bold text-xs bg-emerald-50 text-emerald-700 border border-emerald-200">-${p.toFixed(p % 1 === 0 ? 0 : 1)}đ</span>`;

    if (p <= 5) return `<span class="px-2 py-0.5 rounded-full font-mono font-bold text-xs bg-amber-50 text-amber-700 border border-amber-200">-${p.toFixed(p % 1 === 0 ? 0 : 1)}đ</span>`;

    if (p <= 10) return `<span class="px-2 py-0.5 rounded-full font-mono font-bold text-xs bg-orange-50 text-orange-700 border border-orange-200">-${p.toFixed(p % 1 === 0 ? 0 : 1)}đ</span>`;

    return `<span class="px-2 py-0.5 rounded-full font-mono font-bold text-xs bg-rose-50 text-rose-700 border border-rose-200">-${p.toFixed(p % 1 === 0 ? 0 : 1)}đ</span>`;

  };



  const getSeverityBadge = (sev, pt) => {

    const p = parseFloat(pt);

    if (p <= 3) return `<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700">Nhẹ</span>`;

    if (p <= 5) return `<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-amber-50 text-amber-700">Trung bình</span>`;

    if (p <= 10) return `<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-orange-50 text-orange-700">Nghiêm trọng</span>`;

    return `<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-rose-50 text-rose-700">Rất nghiêm trọng</span>`;

  };



  let rowsHtml = '';

  filtered.forEach((r, idx) => {

    rowsHtml += `

      <tr class="hover:bg-slate-50 transition border-b border-slate-100">

        <td class="py-2.5 px-3 text-center text-slate-400 font-mono text-[11px]">${idx + 1}</td>

        <td class="py-2.5 px-3 font-mono font-bold text-brand-700">

          <span class="px-2 py-0.5 rounded bg-blue-50 border border-blue-200/80">${escapeHtml(r.code)}</span>

        </td>

        <td class="py-2.5 px-3 font-medium text-slate-800 leading-snug">${escapeHtml(r.name)}</td>

        <td class="py-2.5 px-3 text-slate-500">

          <span class="inline-flex items-center gap-1">

            <span class="w-1.5 h-1.5 rounded-full bg-slate-400"></span>

            ${escapeHtml(r.category_name || 'Chung')}

          </span>

        </td>

        <td class="py-2.5 px-3 text-center">${getPointsBadge(r.default_points_deducted)}</td>

        <td class="py-2.5 px-3 text-center">${getSeverityBadge(r.severity, r.default_points_deducted)}</td>

        <td class="py-2.5 px-3 text-right">

          <button type="button" onclick="selectRuleFromModal(${r.id})" class="px-2.5 py-1 bg-brand-50 hover:bg-brand-600 text-brand-700 hover:text-white rounded-lg font-semibold text-[11px] transition">

            Chọn lỗi

          </button>

        </td>

      </tr>

    `;

  });



  tbody.innerHTML = rowsHtml;

}



function selectRuleFromModal(ruleId) {

  const rule = (rulesCache || []).find(r => Number(r.id) === Number(ruleId));

  if (!rule) return;



  const quickModal = document.getElementById('modal-quick-violation');

  const processModal = document.getElementById('modal-process-report');

  const saoDoSelect = document.getElementById('sao-do-report-rule');



  if (quickModal && !quickModal.classList.contains('hidden')) {

    const select = document.getElementById('modal-violation-rule');

    if (select) {

      select.value = rule.id;

      updateViolationPointsPreview();

    }

    closeRulesReferenceModal();

    showToast(`Đã chọn: [${rule.code}] ${rule.name}`, 'info');

    return;

  }



  if (processModal && !processModal.classList.contains('hidden')) {

    const select = document.getElementById('modal-process-rule');

    if (select) {

      select.value = rule.id;

      if (typeof onProcessRuleChange === 'function') onProcessRuleChange();

    }

    closeRulesReferenceModal();

    showToast(`Đã chọn: [${rule.code}] ${rule.name}`, 'info');

    return;

  }



  if (saoDoSelect && saoDoSelect.offsetParent !== null) {

    saoDoSelect.value = rule.id;

    closeRulesReferenceModal();

    showToast(`Đã chọn: [${rule.code}] ${rule.name}`, 'info');

    return;

  }



  // Otherwise, copy to clipboard

  const textToCopy = `[${rule.code}] ${rule.name} (-${rule.default_points_deducted}đ)`;

  if (navigator.clipboard && navigator.clipboard.writeText) {

    navigator.clipboard.writeText(textToCopy).then(() => {

      showToast(`Đã sao chép: ${rule.code} (-${rule.default_points_deducted}đ)`, 'success');

    }).catch(() => {

      showToast(`Mã quy định: ${rule.code} (-${rule.default_points_deducted}đ)`, 'info');

    });

  } else {

    showToast(`Mã quy định: ${rule.code} (-${rule.default_points_deducted}đ)`, 'info');

  }

}



// Expose user detail, delete & review action functions globally
window.openUserDetailModal = openUserDetailModal;
window.closeUserDetailModal = closeUserDetailModal;
window.confirmDeleteUser = confirmDeleteUser;
window.openReviewModal = openReviewModal;

// ==============================================================================
// ĐỘI NGŨ GIÁO VIÊN (GVCN & BỘ MÔN) QUẢN TRỊ TRỰC TIẾP
// ==============================================================================
const SUBJECT_MAP = {
  'TOAN': 'Toán học',
  'VAN': 'Ngữ văn',
  'ANH': 'Tiếng Anh',
  'LY': 'Vật lý',
  'HOA': 'Hóa học',
  'SINH': 'Sinh học',
  'SU': 'Lịch sử',
  'DIA': 'Địa lý',
  'GDCD': 'GDCD/GDKT&PL',
  'TIN': 'Tin học',
  'CN': 'Công nghệ',
  'TD': 'Giáo dục thể chất',
  'QP': 'Giáo dục QP-AN',
  'AM_NHAC': 'Âm nhạc',
  'MY_THUAT': 'Mỹ thuật',
  'HDTN': 'Hoạt động trải nghiệm'
};

let currentClassTeachersData = null;
let eligibleTeachersCache = [];

async function loadClassTeachers(classId = null) {
  const targetId = classId || (activeTeacherClass ? activeTeacherClass.id : null);
  if (!targetId) return;

  const paneTitle = document.getElementById('teachers-pane-class-title');
  const gvcnName = document.getElementById('class-gvcn-name');
  const gvcnDetails = document.getElementById('class-gvcn-details');
  const gvcnStatus = document.getElementById('class-gvcn-status-badge');
  const revokeBtn = document.getElementById('btn-pane-revoke-gvcn');
  const tbody = document.getElementById('class-subject-teachers-tbody');
  const emptyState = document.getElementById('class-subject-teachers-empty');
  const countBadge = document.getElementById('subject-teachers-count-badge');
  const tabBadge = document.getElementById('class-teacher-count-badge');

  try {
    const res = await fetch(`/api/conduct/teacher-classes/${targetId}/assigned-teachers/`);
    if (!res.ok) throw new Error('Không thể tải danh sách giáo viên phụ trách.');
    const data = await res.json();
    currentClassTeachersData = data;

    if (paneTitle && data.class_name) {
      paneTitle.textContent = `Đội ngũ giáo viên - Lớp ${data.class_name} (Khối ${data.grade})`;
    }

    const canManageTeachers = currentUser && (
      isAdminUser(currentUser) ||
      currentUser.role === 'BGH' || currentUser.is_bgh ||
      currentUser.role === 'DOAN_TRUONG' || currentUser.is_doan_truong
    );

    const btnAssignGvcn = document.getElementById('btn-pane-assign-gvcn');
    const btnAssignGvbm = document.getElementById('btn-pane-assign-gvbm');
    const btnChangeGvcn = document.getElementById('btn-pane-change-gvcn');
    const thActions = document.getElementById('th-subject-teachers-actions');
    if (btnAssignGvcn) btnAssignGvcn.classList.toggle('hidden', !canManageTeachers);
    if (btnAssignGvbm) btnAssignGvbm.classList.toggle('hidden', !canManageTeachers);
    if (btnChangeGvcn) btnChangeGvcn.classList.toggle('hidden', !canManageTeachers);
    if (thActions) thActions.textContent = canManageTeachers ? 'Thao tác' : 'Trạng thái';

    // GVCN Card
    if (data.homeroom_teacher) {
      const ht = data.homeroom_teacher;
      if (gvcnName) gvcnName.textContent = ht.full_name || ht.username;
      if (gvcnDetails) {
        gvcnDetails.textContent = `Môn chuyên môn: ${ht.subject_display || ht.subject || 'Chưa phân môn'} • Email: ${ht.email || 'Chưa có'} • SĐT: ${ht.phone || 'Chưa có'}`;
      }
      if (gvcnStatus) {
        gvcnStatus.className = 'px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-100 text-emerald-700';
        gvcnStatus.textContent = 'Đang hoạt động';
      }
      if (revokeBtn) revokeBtn.classList.toggle('hidden', !canManageTeachers);

      if (activeTeacherClass && activeTeacherClass.id === targetId) {
        activeTeacherClass.homeroom_teacher_name = ht.full_name;
        activeTeacherClass.homeroom_teacher_id = ht.id;
      }
    } else {
      if (gvcnName) gvcnName.textContent = 'Chưa phân công GVCN';
      if (gvcnDetails) gvcnDetails.textContent = 'Lớp hiện chưa có giáo viên chủ nhiệm nhiệm kỳ này.';
      if (gvcnStatus) {
        gvcnStatus.className = 'px-2 py-0.5 text-[10px] font-bold rounded-full bg-amber-100 text-amber-700';
        gvcnStatus.textContent = 'Chưa phân công';
      }
      if (revokeBtn) revokeBtn.classList.add('hidden');

      if (activeTeacherClass && activeTeacherClass.id === targetId) {
        activeTeacherClass.homeroom_teacher_name = 'Chưa phân công';
        activeTeacherClass.homeroom_teacher_id = null;
      }
    }

    // Subject teachers table
    const subjectTeachers = data.subject_teachers || [];
    if (countBadge) countBadge.textContent = `${subjectTeachers.length} môn đã phân công`;
    if (tabBadge) tabBadge.textContent = `${(data.homeroom_teacher ? 1 : 0) + subjectTeachers.length}`;

    if (tbody) {
      if (subjectTeachers.length === 0) {
        tbody.innerHTML = '';
        if (emptyState) emptyState.classList.remove('hidden');
      } else {
        if (emptyState) emptyState.classList.add('hidden');
        tbody.innerHTML = subjectTeachers.map((st, idx) => {
          const formattedDate = st.assigned_at ? new Date(st.assigned_at).toLocaleDateString('vi-VN') : (st.start_date || '--');
          const actionCell = canManageTeachers
            ? `<button type="button" onclick="removeSubjectTeacher(${st.assignment_id})" class="px-2.5 py-1 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-lg transition" title="Thu hồi phân công môn ${escapeHtml(st.subject_display || st.subject)}">Thu hồi</button>`
            : `<span class="text-xs text-slate-400 font-medium">Đang giảng dạy</span>`;
          return `
            <tr class="hover:bg-slate-50/80 transition-colors">
              <td class="py-3 px-4 text-center font-bold text-slate-400">${idx + 1}</td>
              <td class="py-3 px-4">
                <span class="px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">
                  ${escapeHtml(st.subject_display || SUBJECT_MAP[st.subject] || st.subject)}
                </span>
              </td>
              <td class="py-3 px-4 font-semibold text-slate-800">
                ${escapeHtml(st.teacher_name || st.full_name || st.username)}
              </td>
              <td class="py-3 px-4 text-slate-500">${escapeHtml(st.email || st.teacher_email || '--')}</td>
              <td class="py-3 px-4 text-slate-500">${escapeHtml(st.phone || st.teacher_phone || '--')}</td>
              <td class="py-3 px-4 text-center text-slate-500">${formattedDate}</td>
              <td class="py-3 px-4 text-right">
                ${actionCell}
              </td>
            </tr>
          `;
        }).join('');
      }
    }

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error('Error loading class teachers:', err);
    if (gvcnName) gvcnName.textContent = 'Lỗi tải dữ liệu';
  }
}

async function openAssignSubjectTeacherModal() {
  if (!activeTeacherClass && teacherAssignedClasses && teacherAssignedClasses.length > 0) {
    activeTeacherClass = teacherAssignedClasses[0];
    await selectTeacherClass(activeTeacherClass.id);
  }

  if (!activeTeacherClass) {
    showToast('Vui lòng chọn một lớp học trước khi phân công.', 'warning');
    return;
  }

  const modal = document.getElementById('modal-assign-subject-teacher');
  if (!modal) return;

  // Populate class dropdown
  const classSelect = document.getElementById('assign-subject-class-select');
  if (classSelect && teacherAssignedClasses && teacherAssignedClasses.length > 0) {
    classSelect.innerHTML = teacherAssignedClasses.map(c => 
      `<option value="${c.id}" ${c.id === activeTeacherClass.id ? 'selected' : ''}>Lớp ${escapeHtml(c.name)} (Khối ${c.grade})</option>`
    ).join('');
  }

  // Reset subject & teacher selects
  const subjectSelect = document.getElementById('assign-subject-code-select');
  if (subjectSelect) subjectSelect.value = '';

  const teacherSelect = document.getElementById('assign-subject-teacher-select');
  if (teacherSelect) teacherSelect.innerHTML = '<option value="">-- Chọn môn học trước để lọc giáo viên phù hợp --</option>';

  const conflictBox = document.getElementById('assign-subject-conflict-box');
  if (conflictBox) conflictBox.classList.add('hidden');

  // Load eligible teachers
  try {
    const res = await fetch('/api/conduct/teacher-classes/eligible-teachers/');
    if (res.ok) {
      eligibleTeachersCache = await res.json();
    }
  } catch(e) {
    console.error('Failed to load eligible teachers:', e);
  }

  openModal('modal-assign-subject-teacher');
  if (window.lucide) lucide.createIcons();
}

function onAssignSubjectChange(subjectCode) {
  const teacherSelect = document.getElementById('assign-subject-teacher-select');
  const conflictBox = document.getElementById('assign-subject-conflict-box');
  const conflictMsg = document.getElementById('assign-subject-conflict-msg');
  if (!teacherSelect) return;

  if (!subjectCode) {
    teacherSelect.innerHTML = '<option value="">-- Chọn môn học trước để lọc giáo viên phù hợp --</option>';
    if (conflictBox) conflictBox.classList.add('hidden');
    return;
  }

  // Check if subject is already assigned in this class
  if (currentClassTeachersData && currentClassTeachersData.subject_teachers) {
    const existing = currentClassTeachersData.subject_teachers.find(st => st.subject === subjectCode);
    if (existing) {
      if (conflictBox) conflictBox.classList.remove('hidden');
      if (conflictMsg) conflictMsg.textContent = `Môn này hiện đã được phân công cho Thầy/Cô ${existing.teacher_name || existing.full_name}. Lưu phân công mới sẽ thay thế giáo viên này.`;
    } else {
      if (conflictBox) conflictBox.classList.add('hidden');
    }
  }

  if (eligibleTeachersCache.length === 0) {
    teacherSelect.innerHTML = '<option value="">-- Không có giáo viên nào --</option>';
    return;
  }

  // Partition matching teachers vs others
  const matching = [];
  const others = [];

  eligibleTeachersCache.forEach(t => {
    const tSubject = (t.subject || '').toUpperCase();
    if (tSubject === subjectCode.toUpperCase() || tSubject.includes(subjectCode.toUpperCase())) {
      matching.push(t);
    } else {
      others.push(t);
    }
  });

  let optionsHtml = '<option value="">-- Chọn Giáo viên phụ trách --</option>';
  if (matching.length > 0) {
    optionsHtml += `<optgroup label="Giáo viên chuyên môn ${SUBJECT_MAP[subjectCode] || subjectCode}">`;
    matching.forEach(t => {
      optionsHtml += `<option value="${t.id}">${escapeHtml(t.full_name || t.username)} [Đúng chuyên môn]</option>`;
    });
    optionsHtml += `</optgroup>`;
  }

  if (others.length > 0) {
    optionsHtml += `<optgroup label="Tất cả giáo viên khác">`;
    others.forEach(t => {
      const subjectNote = t.subject ? ` (Môn ${t.subject})` : '';
      optionsHtml += `<option value="${t.id}">${escapeHtml(t.full_name || t.username)}${subjectNote}</option>`;
    });
    optionsHtml += `</optgroup>`;
  }

  teacherSelect.innerHTML = optionsHtml;
}

async function handleAssignSubjectTeacherSubmit(event) {
  event.preventDefault();

  const classSelect = document.getElementById('assign-subject-class-select');
  const classId = classSelect ? classSelect.value : (activeTeacherClass ? activeTeacherClass.id : null);
  const subjectCode = document.getElementById('assign-subject-code-select')?.value;
  const teacherId = document.getElementById('assign-subject-teacher-select')?.value;
  const submitBtn = document.getElementById('btn-submit-assign-subject');

  if (!classId) {
    showToast('Vui lòng chọn lớp học.', 'warning');
    return;
  }
  if (!subjectCode) {
    showToast('Vui lòng chọn môn học.', 'warning');
    return;
  }
  if (!teacherId) {
    showToast('Vui lòng chọn giáo viên phụ trách.', 'warning');
    return;
  }

  try {
    if (submitBtn) submitBtn.disabled = true;

    const res = await fetch(`/api/conduct/teacher-classes/${classId}/assign-subject-teacher/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify({
        teacher_id: parseInt(teacherId, 10),
        subject: subjectCode
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Lỗi khi phân công giáo viên bộ môn.');

    showToast(data.message || 'Phân công Giáo viên Bộ môn thành công!', 'success');
    closeModal('modal-assign-subject-teacher');
    await loadClassTeachers(Number(classId));
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

async function removeSubjectTeacher(assignmentId) {
  if (!activeTeacherClass) return;
  if (!confirm('Bạn có chắc chắn muốn thu hồi phân công giáo viên môn này?')) return;

  try {
    const res = await fetch(`/api/conduct/teacher-classes/${activeTeacherClass.id}/remove-subject-teacher/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify({
        assignment_id: assignmentId
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Lỗi khi thu hồi phân công.');

    showToast(data.message || 'Đã thu hồi phân công giáo viên bộ môn.', 'success');
    await loadClassTeachers(activeTeacherClass.id);
  } catch (err) {
    showToast(err.message, 'error');
  }
}


window.closeReviewModal = closeReviewModal;
window.onReviewRoleChange = onReviewRoleChange;
window.onReviewStudentGradeChange = onReviewStudentGradeChange;
window.onReviewStudentClassChange = onReviewStudentClassChange;
window.switchReviewTeacherGradeTab = switchReviewTeacherGradeTab;
window.toggleReviewTeacherClass = toggleReviewTeacherClass;
window.toggleReviewAllGradeClasses = toggleReviewAllGradeClasses;
window.onReviewHomeroomClassChange = onReviewHomeroomClassChange;
window.handleReviewActionSubmit = handleReviewActionSubmit;
window.closeApproveRoleModal = closeReviewModal;
window.openAssignHomeroomModal = openAssignHomeroomModal;
window.handleAssignHomeroomSubmit = handleAssignHomeroomSubmit;
window.revokeHomeroomTeacher = revokeHomeroomTeacher;

window.filterProfileTeacherGrade = filterProfileTeacherGrade;
window.updateProfileTeacherClassesCount = updateProfileTeacherClassesCount;
window.submitStudentClassChangeRequest = submitStudentClassChangeRequest;
window.cancelStudentClassChangeRequest = cancelStudentClassChangeRequest;
window.submitTeacherClassesUpdate = submitTeacherClassesUpdate;
window.handleReviewClassChange = handleReviewClassChange;


window.openModal = openModal;
window.closeModal = closeModal;
window.openAssignHomeroomModal = openAssignHomeroomModal;
window.onAssignHomeroomClassSelectChange = onAssignHomeroomClassSelectChange;
window.handleAssignHomeroomSubmit = handleAssignHomeroomSubmit;
window.handleRevokeHomeroom = handleRevokeHomeroom;
window.revokeHomeroomTeacher = handleRevokeHomeroom;
window.switchTeacherSubTab = switchTeacherSubTab;
window.loadClassTeachers = loadClassTeachers;
window.openAssignSubjectTeacherModal = openAssignSubjectTeacherModal;
window.onAssignSubjectChange = onAssignSubjectChange;
window.handleAssignSubjectTeacherSubmit = handleAssignSubjectTeacherSubmit;
window.removeSubjectTeacher = removeSubjectTeacher;


// =============================================================================
// CLASS MONITOR (LỚP TRƯỞNG) MANAGEMENT FUNCTIONS
// =============================================================================

function updateClassMonitorHeader(monitorName, canAssign) {
  const badge = document.getElementById('active-class-monitor-badge');
  const nameEl = document.getElementById('active-class-monitor-name');
  const btnHeader = document.getElementById('btn-assign-monitor-header');

  if (badge && nameEl) {
    if (monitorName) {
      nameEl.textContent = monitorName;
      badge.classList.remove('hidden');
    } else {
      nameEl.textContent = 'Chưa có';
      if (canAssign) {
        badge.classList.remove('hidden');
      } else {
        badge.classList.add('hidden');
      }
    }
  }

  if (btnHeader) {
    btnHeader.classList.toggle('hidden', !canAssign);
  }
}

function openAssignMonitorModal() {
  if (!activeTeacherClass) {
    showToast('Vui lòng chọn một lớp học trước.', 'warning');
    return;
  }

  const modal = document.getElementById('modal-assign-class-monitor');
  if (!modal) return;

  const subtitle = document.getElementById('modal-assign-monitor-class-subtitle');
  if (subtitle) subtitle.textContent = `Lớp ${activeTeacherClass.name}`;

  const classIdInput = document.getElementById('assign-monitor-class-id');
  if (classIdInput) classIdInput.value = activeTeacherClass.id;

  const currentNameEl = document.getElementById('assign-monitor-current-name');
  const unassignBtn = document.getElementById('btn-unassign-monitor-modal');

  if (currentNameEl) {
    currentNameEl.textContent = activeTeacherClass.monitor_name || 'Chưa phân công';
  }
  if (unassignBtn) {
    unassignBtn.classList.toggle('hidden', !activeTeacherClass.monitor_id);
  }

  // Populate student select dropdown
  const studentSelect = document.getElementById('assign-monitor-select-student');
  if (studentSelect) {
    let optHtml = '<option value="">-- Chọn học sinh trong lớp --</option>';
    teacherStudentsList.forEach((s, idx) => {
      const isCur = Boolean(s.is_class_monitor || (activeTeacherClass.monitor_id === s.id));
      optHtml += `<option value="${s.id}" ${isCur ? 'selected' : ''}>${s.stt || (idx + 1)}. [${escapeHtml(s.student_code)}] ${escapeHtml(s.full_name)} ${isCur ? '⭐ (Hiện là LT)' : ''}</option>`;
    });
    studentSelect.innerHTML = optHtml;
  }

  modal.classList.remove('hidden');
  lucide.createIcons();
}

async function handleAssignMonitorSubmit(e) {
  e.preventDefault();
  const classId = document.getElementById('assign-monitor-class-id')?.value || activeTeacherClass?.id;
  const studentId = document.getElementById('assign-monitor-select-student')?.value;

  if (!classId) {
    showToast('Không xác định được lớp học.', 'error');
    return;
  }
  if (!studentId) {
    showToast('Vui lòng chọn một học sinh để phân công làm Lớp trưởng.', 'warning');
    return;
  }

  await executeAssignMonitor(Number(classId), Number(studentId));
}

function confirmAssignMonitor(studentId, studentName) {
  if (!activeTeacherClass) return;
  if (!confirm(`Bạn có chắc chắn muốn phân công học sinh "${studentName}" làm Lớp trưởng của lớp ${activeTeacherClass.name}?`)) {
    return;
  }
  executeAssignMonitor(activeTeacherClass.id, studentId);
}

function confirmRemoveMonitor(studentId, studentName) {
  if (!activeTeacherClass) return;
  if (!confirm(`Bạn có chắc chắn muốn hủy vai trò Lớp trưởng của học sinh "${studentName}"?`)) {
    return;
  }
  executeAssignMonitor(activeTeacherClass.id, null);
}

function confirmRemoveMonitorFromModal() {
  if (!activeTeacherClass) return;
  if (!confirm(`Bạn có chắc chắn muốn hủy vai trò Lớp trưởng của lớp ${activeTeacherClass.name}?`)) {
    return;
  }
  closeModal('modal-assign-class-monitor');
  executeAssignMonitor(activeTeacherClass.id, null);
}

async function executeAssignMonitor(classId, studentId) {
  const submitBtn = document.getElementById('btn-submit-assign-monitor');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i><span>Đang xử lý...</span>';
    lucide.createIcons();
  }

  try {
    const res = await fetch(`/api/conduct/teacher-classes/${classId}/assign-monitor/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify({ student_id: studentId })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || 'Không thể thực hiện phân công Lớp trưởng.');
    }

    showToast(data.message || 'Cập nhật Lớp trưởng thành công!', 'success');
    closeModal('modal-assign-class-monitor');

    // Update activeTeacherClass state
    if (activeTeacherClass && activeTeacherClass.id === classId) {
      activeTeacherClass.monitor_id = data.monitor_id;
      activeTeacherClass.monitor_name = data.monitor_name;
    }

    // Update teacherStudentsList locally
    teacherStudentsList.forEach(s => {
      s.is_class_monitor = Boolean(studentId && s.id === Number(studentId));
    });

    // Refresh UI
    updateClassMonitorHeader(data.monitor_name, true);
    filterTeacherStudentsList();
    lucide.createIcons();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i data-lucide="check" class="w-3.5 h-3.5"></i><span>Lưu phân công</span>';
      lucide.createIcons();
    }
  }
}
