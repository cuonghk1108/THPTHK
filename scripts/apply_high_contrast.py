"""
High Contrast Color System for HK Student Hub.
Applies bold, vivid, high-contrast colors and deep framing:
- Deep Midnight Navy Header with crisp white & gold typography.
- High-contrast sidebar with dark group labels and royal electric active pill.
- Rich Olympic podium with real Gold, Silver, and Bronze contrast.
- High contrast Leaderboard Table with dark navy header and crisp readable text.
- High contrast KPI cards with vibrant numbers and bold border states.
- High contrast Chart.js datasets.
"""
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Xuan Cuong\Desktop\hk-student-hub")
INDEX_PATH = BASE_DIR / "templates" / "index.html"
APP_JS_PATH = BASE_DIR / "static" / "app.js"

# ==============================================================================
# 1. HIGH CONTRAST APP SHELL CSS
# ==============================================================================
HIGH_CONTRAST_SHELL_CSS = """    /* ===== HIGH-CONTRAST EDTECH APP SHELL (HEADER, SIDEBAR & WORKSPACE) ===== */
    .app-header {
      position: sticky;
      top: 0;
      z-index: 40;
      background: linear-gradient(90deg, #07152b 0%, #0d2244 50%, #102a54 100%);
      border-bottom: 2px solid #1e3a8a;
      box-shadow: 0 4px 20px rgba(7, 21, 43, 0.35);
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
      transition: transform 0.15s ease;
    }
    .app-brand:hover {
      transform: scale(1.02);
    }
    .app-brand-icon {
      width: 40px;
      height: 40px;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, #1d4ed8 0%, #38bdf8 100%);
      border-radius: 12px;
      color: #ffffff;
      box-shadow: 0 0 14px rgba(56, 189, 248, 0.45);
      border: 1.5px solid rgba(255, 255, 255, 0.3);
    }
    .app-brand-name {
      font-size: 15px;
      font-weight: 900;
      color: #ffffff !important;
      letter-spacing: -0.01em;
      line-height: 1.2;
      text-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }
    .app-brand-sub {
      font-size: 11px;
      color: #38bdf8 !important;
      font-weight: 750;
      margin-top: 1px;
      letter-spacing: 0.02em;
    }
    .app-header-meta {
      flex: 1;
      display: flex;
      align-items: center;
      gap: 14px;
      justify-content: center;
    }
    .app-year-badge {
      font-size: 12px;
      font-weight: 800;
      color: #fde047 !important;
      background: rgba(30, 58, 138, 0.6);
      border: 1.5px solid #3b82f6;
      border-radius: 9999px;
      padding: 5px 16px;
      box-shadow: 0 0 10px rgba(59, 130, 246, 0.25);
    }
    .app-datetime {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 12px;
      font-weight: 700;
      color: #ffffff !important;
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid rgba(255, 255, 255, 0.2);
      padding: 5px 12px;
      border-radius: 8px;
    }
    .app-header-actions {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;
      position: relative;
    }
    .app-notif-btn {
      position: relative;
      width: 40px;
      height: 40px;
      display: grid;
      place-items: center;
      color: #e2e8f0;
      background: rgba(255, 255, 255, 0.1);
      border: 1.5px solid rgba(255, 255, 255, 0.2);
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.18s ease;
    }
    .app-notif-btn:hover {
      background: #1d4ed8;
      color: #ffffff;
      border-color: #60a5fa;
      transform: translateY(-1px);
      box-shadow: 0 0 12px rgba(96, 165, 250, 0.4);
    }
    .app-notif-badge {
      position: absolute;
      top: -3px;
      right: -3px;
      min-width: 19px;
      height: 19px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0 5px;
      background: #dc2626;
      color: #ffffff;
      font-size: 10px;
      font-weight: 900;
      border-radius: 9999px;
      line-height: 1;
      border: 2px solid #07152b;
      box-shadow: 0 0 8px rgba(220, 38, 38, 0.8);
    }
    .app-notif-dropdown {
      position: absolute;
      top: calc(100% + 10px);
      right: 0;
      z-index: 50;
      width: 360px;
      background: #ffffff;
      border: 2px solid #0f2b59;
      border-radius: 16px;
      box-shadow: 0 20px 45px -10px rgba(0, 0, 0, 0.35);
      overflow: hidden;
      animation: edtechFadeIn 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .app-notif-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 18px;
      background: #0f2b59;
      color: #ffffff;
      font-size: 14px;
      font-weight: 850;
    }
    .app-notif-mark-all {
      font-size: 11.5px;
      color: #93c5fd;
      background: transparent;
      border: 0;
      cursor: pointer;
      font-weight: 750;
    }
    .app-notif-mark-all:hover {
      color: #ffffff;
      text-decoration: underline;
    }
    .app-notif-list {
      max-height: 360px;
      overflow-y: auto;
      color: #0f172a;
    }
    .app-user-badge {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 5px 14px 5px 6px;
      background: rgba(255, 255, 255, 0.1);
      border: 1.5px solid rgba(255, 255, 255, 0.25);
      border-radius: 9999px;
      transition: all 0.18s ease;
      cursor: pointer;
    }
    .app-user-badge:hover {
      background: rgba(255, 255, 255, 0.2);
      border-color: #60a5fa;
    }
    .app-user-avatar {
      width: 32px;
      height: 32px;
      flex-shrink: 0;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%);
      color: #ffffff;
      border-radius: 50%;
      font-size: 12px;
      font-weight: 900;
      box-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
    }
    .app-user-avatar-img {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      object-fit: cover;
    }
    .app-user-name {
      font-size: 13px;
      font-weight: 800;
      color: #ffffff !important;
      max-width: 140px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .app-user-role {
      font-size: 11px;
      color: #fcd34d !important;
      font-weight: 750;
    }
    .app-logout-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 14px;
      background: #dc2626;
      border: 1.5px solid #ef4444;
      color: #ffffff !important;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 800;
      cursor: pointer;
      transition: all 0.18s ease;
      box-shadow: 0 2px 8px rgba(220, 38, 38, 0.35);
    }
    .app-logout-btn:hover {
      background: #b91c1c;
      border-color: #f87171;
      transform: translateY(-1px);
      box-shadow: 0 4px 14px rgba(220, 38, 38, 0.5);
    }
    .app-mobile-menu-btn {
      width: 40px;
      height: 40px;
      display: none;
      place-items: center;
      background: rgba(255, 255, 255, 0.12);
      color: #ffffff;
      border: 1.5px solid rgba(255, 255, 255, 0.25);
      border-radius: 12px;
      cursor: pointer;
    }

    /* HIGH-CONTRAST SIDEBAR NAVIGATION */
    .app-sidebar nav {
      background: #ffffff;
      border: 2px solid #cbd5e1;
      border-radius: 20px;
      padding: 14px 10px;
      box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
    }
    .nav-group-heading {
      padding: 12px 12px 4px;
      font-size: 10.5px;
      font-weight: 900;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #1e293b !important;
    }
    .nav-item {
      display: flex !important;
      align-items: center;
      gap: 10px;
      width: 100%;
      padding: 10px 14px;
      margin-bottom: 3px;
      font-size: 13.5px;
      font-weight: 700;
      color: #1e293b;
      background: transparent;
      border: 1.5px solid transparent;
      border-radius: 12px;
      text-align: left;
      cursor: pointer;
      transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .nav-item:hover {
      background: #eff6ff;
      color: #1d4ed8;
      border-color: #93c5fd;
      transform: translateX(3px);
    }
    .nav-item.is-active,
    .nav-item.active {
      background: linear-gradient(135deg, #07152b 0%, #1d4ed8 100%) !important;
      color: #ffffff !important;
      font-weight: 850;
      border-color: #1e40af;
      box-shadow: 0 6px 18px rgba(29, 78, 216, 0.35);
      transform: translateX(3px);
    }
    .nav-item.is-active i,
    .nav-item.is-active svg,
    .nav-item.active i,
    .nav-item.active svg {
      color: #fde047 !important;
    }
    .nav-item i, .nav-item svg {
      width: 18px;
      height: 18px;
      flex-shrink: 0;
      color: #2563eb;
      transition: transform 0.18s ease;
    }
    .nav-item:hover i, .nav-item:hover svg {
      transform: scale(1.12);
      color: #1d4ed8;
    }

    /* HIGH-CONTRAST QUICK ACTION WIDGET */
    #quick-action-widget {
      border-radius: 18px;
      background: linear-gradient(135deg, #07152b 0%, #1d4ed8 100%);
      padding: 16px;
      color: #ffffff;
      box-shadow: 0 8px 24px -4px rgba(7, 21, 43, 0.35);
      border: 2px solid #3b82f6;
    }

    /* HIGH-CONTRAST WORKSPACE HEADERS & CARDS */
    .workspace-page-head {
      background: #ffffff;
      border: 2px solid #cbd5e1;
      border-radius: 18px;
      padding: 20px 24px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05);
    }
    .workspace-page-head h1 {
      margin: 4px 0 2px;
      font-size: 22px;
      font-weight: 900;
      color: #07152b;
      letter-spacing: -0.02em;
    }
    .workspace-page-head p {
      margin: 0;
      font-size: 13.5px;
      color: #334155;
      font-weight: 550;
      line-height: 1.45;
    }
    .workspace-kicker {
      font-size: 11px;
      font-weight: 900;
      letter-spacing: 0.07em;
      text-transform: uppercase;
      color: #1d4ed8;
      margin-bottom: 2px;
    }
    .workspace-refresh {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 8px 16px;
      background: #f8fafc;
      border: 1.5px solid #cbd5e1;
      border-radius: 12px;
      font-size: 12.5px;
      font-weight: 750;
      color: #0f172a;
      cursor: pointer;
      transition: all 0.18s ease;
    }
    .workspace-refresh:hover {
      background: #1d4ed8;
      border-color: #1d4ed8;
      color: #ffffff;
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(29, 78, 216, 0.25);
    }
    .tab-pane { animation: edtechFadeIn 0.22s cubic-bezier(0.16, 1, 0.3, 1); }
    @media (max-width:768px) {
      .app-header-inner { padding: 0 16px; height: 56px; gap: 12px; }
      .app-header-meta { display: none; }
      .app-brand-name { max-width: 140px; font-size: 13px; }
      .app-brand-sub { display: none; }
      .app-notif-dropdown { width: min(320px, calc(100vw - 24px)); right: -8px; }
      .app-mobile-menu-btn { display: grid; }
    }
"""

# ==============================================================================
# 2. HIGH CONTRAST DASHBOARD CSS
# ==============================================================================
HIGH_CONTRAST_DASHBOARD_CSS = """    /* ===== HIGH-CONTRAST EDTECH DASHBOARD (BOLD, VIVID, CRISP) ===== */
    @keyframes edtechFadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes edtechPulse {
      0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
      70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
      100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    .edtech-dash-wrap {
      animation: edtechFadeIn 0.28s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    /* 1. HIGH-CONTRAST HERO GREETING CARD */
    .edtech-hero-card {
      background: linear-gradient(135deg, #061325 0%, #0d2347 48%, #1d4ed8 100%);
      border-radius: 20px;
      padding: 24px 28px;
      color: #ffffff;
      position: relative;
      overflow: hidden;
      box-shadow: 0 16px 36px -10px rgba(7, 21, 43, 0.45);
      margin-bottom: 22px;
      border: 2px solid #2563eb;
    }
    .edtech-hero-card::after {
      content: "";
      position: absolute;
      top: -60px;
      right: -60px;
      width: 240px;
      height: 240px;
      background: radial-gradient(circle, rgba(56, 189, 248, 0.2) 0%, transparent 70%);
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
      font-size: clamp(21px, 2.4vw, 28px);
      font-weight: 900;
      color: #ffffff !important;
      letter-spacing: -0.025em;
      line-height: 1.25;
      text-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }
    .edtech-greeting-box p {
      margin: 0;
      font-size: 14px;
      color: #e2e8f0 !important;
      line-height: 1.5;
      font-weight: 550;
    }
    .edtech-role-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #000000;
      border: 2px solid #f59e0b;
      padding: 5px 14px;
      border-radius: 9999px;
      font-size: 11.5px;
      font-weight: 850;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: #fde047 !important;
      box-shadow: 0 0 12px rgba(245, 158, 11, 0.35);
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
      background: #042f2e;
      border: 1.5px solid #10b981;
      color: #34d399 !important;
      padding: 6px 14px;
      border-radius: 10px;
      font-size: 12.5px;
      font-weight: 800;
      box-shadow: 0 0 10px rgba(16, 185, 129, 0.25);
    }
    .edtech-live-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      animation: edtechPulse 2s infinite;
    }
    .edtech-hero-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #ffffff;
      border: 2px solid #ffffff;
      color: #07152b !important;
      padding: 8px 16px;
      border-radius: 12px;
      font-size: 13px;
      font-weight: 850;
      cursor: pointer;
      transition: all 0.18s ease;
      box-shadow: 0 3px 10px rgba(0,0,0,0.25);
    }
    .edtech-hero-btn:hover {
      background: #fde047;
      border-color: #fde047;
      color: #000000 !important;
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(253, 224, 71, 0.4);
    }
    .edtech-hero-btn-primary {
      background: #f59e0b !important;
      border-color: #fbbf24 !important;
      color: #000000 !important;
    }
    .edtech-hero-btn-primary:hover {
      background: #fbbf24 !important;
      transform: translateY(-2px);
    }

    /* 2. HIGH-CONTRAST KPI METRIC CARDS */
    .edtech-kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 16px;
      margin-bottom: 22px;
    }
    .edtech-kpi-card {
      background: #ffffff;
      border: 2px solid #cbd5e1;
      border-radius: 18px;
      padding: 18px 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
      position: relative;
      overflow: hidden;
      cursor: pointer;
      box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
    }
    .edtech-kpi-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 14px 28px -6px rgba(15, 23, 42, 0.14);
      border-color: #1d4ed8;
    }
    .edtech-kpi-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 12px;
    }
    .edtech-kpi-title {
      font-size: 13.5px;
      font-weight: 800;
      color: #0f172a !important;
      line-height: 1.3;
    }
    .edtech-kpi-icon {
      width: 44px;
      height: 44px;
      border-radius: 14px;
      display: grid;
      place-items: center;
      flex-shrink: 0;
      transition: transform 0.2s ease;
    }
    .edtech-kpi-card:hover .edtech-kpi-icon {
      transform: scale(1.1);
    }
    .edtech-kpi-val-row {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 8px;
    }
    .edtech-kpi-val {
      font-size: 32px;
      font-weight: 900;
      line-height: 1.1;
      font-variant-numeric: tabular-nums;
      letter-spacing: -0.025em;
    }
    .edtech-kpi-badge {
      font-size: 11.5px;
      font-weight: 850;
      padding: 4px 10px;
      border-radius: 8px;
      display: inline-flex;
      align-items: center;
      gap: 3px;
    }
    .edtech-kpi-footer {
      font-size: 12px;
      font-weight: 650;
      color: #334155 !important;
      margin-top: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-top: 10px;
      border-top: 1.5px dashed #e2e8f0;
    }

    /* 3. HIGH-CONTRAST SEGMENTED CONTROLS */
    .edtech-tabs-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }
    .edtech-segmented-nav {
      background: #e2e8f0;
      padding: 5px;
      border-radius: 16px;
      display: inline-flex;
      gap: 5px;
      border: 2px solid #cbd5e1;
    }
    .edtech-seg-btn {
      padding: 9px 18px;
      font-size: 13.5px;
      font-weight: 750;
      border-radius: 12px;
      transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
      border: none;
      background: transparent;
      color: #1e293b;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }
    .edtech-seg-btn:hover {
      color: #000000;
      background: rgba(255, 255, 255, 0.5);
    }
    .edtech-seg-btn.active {
      background: #07152b !important;
      color: #ffffff !important;
      box-shadow: 0 4px 12px rgba(7, 21, 43, 0.35);
      font-weight: 900;
    }
    .edtech-seg-btn.active i {
      color: #fde047 !important;
    }

    /* 4. HIGH-CONTRAST OLYMPIC PODIUM 3D */
    .edtech-podium-card {
      background: #ffffff;
      border: 2px solid #cbd5e1;
      border-radius: 20px;
      padding: 24px;
      margin-bottom: 22px;
      box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05);
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
      background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 50%, #fde68a 100%);
      border: 3px solid #f59e0b !important;
      box-shadow: 0 14px 34px -4px rgba(245, 158, 11, 0.45);
      min-height: 260px;
      order: 2;
    }
    .podium-silver {
      background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 60%, #e2e8f0 100%);
      border: 2.5px solid #64748b !important;
      box-shadow: 0 8px 24px -4px rgba(100, 116, 139, 0.3);
      min-height: 225px;
      order: 1;
    }
    .podium-bronze {
      background: linear-gradient(180deg, #fff7ed 0%, #ffedd5 60%, #fed7aa 100%);
      border: 2.5px solid #ea580c !important;
      box-shadow: 0 8px 24px -4px rgba(234, 88, 12, 0.3);
      min-height: 210px;
      order: 3;
    }
    @media (max-width: 768px) {
      .podium-gold { order: 1; min-height: auto; }
      .podium-silver { order: 2; min-height: auto; }
      .podium-bronze { order: 3; min-height: auto; }
    }
    .podium-crown-badge {
      width: 52px;
      height: 52px;
      border-radius: 16px;
      display: grid;
      place-items: center;
      font-size: 24px;
      margin-bottom: 10px;
      box-shadow: 0 4px 14px rgba(0,0,0,0.14);
      background: #ffffff;
      border: 2px solid rgba(0,0,0,0.08);
    }
    .podium-class-title {
      font-size: 20px;
      font-weight: 900;
      color: #000000 !important;
      letter-spacing: -0.01em;
    }
    .podium-score-pill {
      font-size: 26px;
      font-weight: 950;
      margin: 6px 0 4px;
      font-variant-numeric: tabular-nums;
    }
    .podium-sub-text {
      font-size: 12px;
      font-weight: 750;
    }

    /* 5. HIGH-CONTRAST LEADERBOARD TABLE */
    .edtech-table-container {
      background: #ffffff;
      border: 2px solid #cbd5e1;
      border-radius: 18px;
      overflow: hidden;
      box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05);
    }
    .edtech-table-toolbar {
      padding: 14px 18px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      background: #ffffff;
      border-bottom: 2px solid #e2e8f0;
    }
    .edtech-search-input {
      background: #f8fafc;
      border: 2px solid #cbd5e1;
      border-radius: 10px;
      padding: 8px 14px 8px 34px;
      font-size: 13px;
      font-weight: 600;
      color: #0f172a;
      width: 230px;
      transition: all 0.16s ease;
    }
    .edtech-search-input:focus {
      background: #ffffff;
      border-color: #1d4ed8;
      outline: none;
      box-shadow: 0 0 0 3px rgba(29, 78, 216, 0.2);
    }
    .edtech-filter-pills {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }
    .edtech-filter-pill {
      font-size: 12.5px;
      font-weight: 750;
      padding: 6px 14px;
      border-radius: 10px;
      border: 2px solid #cbd5e1;
      background: #f8fafc;
      color: #1e293b;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .edtech-filter-pill:hover {
      background: #eff6ff;
      color: #1d4ed8;
      border-color: #93c5fd;
    }
    .edtech-filter-pill.active {
      background: #07152b !important;
      color: #ffffff !important;
      border-color: #07152b !important;
      box-shadow: 0 3px 10px rgba(7, 21, 43, 0.35);
    }
    .edtech-table-head-dark {
      background: #07152b !important;
      color: #ffffff !important;
      font-weight: 850;
    }
    .edtech-table-head-dark th {
      padding: 12px 14px;
      color: #ffffff !important;
      font-weight: 850;
      border-bottom: 2px solid #1e3a8a;
    }

    /* 6. HIGH-CONTRAST CHARTS SECTION */
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
      border: 2px solid #cbd5e1;
      border-radius: 18px;
      padding: 22px 24px;
      box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05);
    }
    .edtech-chart-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 16px;
      padding-bottom: 14px;
      border-bottom: 2px solid #e2e8f0;
    }
    .edtech-chart-title {
      font-size: 15px;
      font-weight: 900;
      color: #07152b !important;
      margin: 0;
    }
    .edtech-chart-desc {
      font-size: 12.5px;
      color: #334155 !important;
      font-weight: 600;
      margin: 2px 0 0;
    }
    .edtech-chart-canvas-wrap {
      position: relative;
      width: 100%;
      height: 290px;
    }

    /* 7. HOMEROOM / STUDENT PERSONAL CARD */
    .edtech-personal-card {
      background: linear-gradient(135deg, #ffffff 0%, #ecfdf5 100%);
      border: 2.5px solid #10b981;
      border-radius: 18px;
      padding: 22px 26px;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      box-shadow: 0 6px 20px rgba(16, 185, 129, 0.15);
    }
"""

print("Defined High Contrast CSS!")
"""
Complete High Contrast Color System Application Script.
"""
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Xuan Cuong\Desktop\hk-student-hub")
INDEX_PATH = BASE_DIR / "templates" / "index.html"
APP_JS_PATH = BASE_DIR / "static" / "app.js"

# 1. CSS TO INJECT INTO templates/index.html
from scripts.apply_high_contrast import HIGH_CONTRAST_SHELL_CSS, HIGH_CONTRAST_DASHBOARD_CSS

def update_index_css():
    print("Reading templates/index.html...")
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        text = f.read()

    # Replace Shell CSS
    s1 = text.find("/* ===== PREMIUM EDTECH APP SHELL")
    s2 = text.find("/* ===== MODERN EDTECH DASHBOARD DESIGN SYSTEM 2.0")
    s3 = text.find("/* ===== MODERN SCHOOL PORTAL & EDTECH DESIGN SYSTEM ===== */")

    if s1 != -1 and s2 != -1 and s3 != -1:
        print(f"Replacing Shell CSS ({s1} to {s2}) and Dashboard CSS ({s2} to {s3})...")
        new_text = text[:s1] + HIGH_CONTRAST_SHELL_CSS + "\n" + HIGH_CONTRAST_DASHBOARD_CSS + "\n    " + text[s3:]
        with open(INDEX_PATH, 'w', encoding='utf-8') as f:
            f.write(new_text)
        print("Updated index.html CSS successfully!")
    else:
        print(f"Tokens not found: s1={s1}, s2={s2}, s3={s3}")

if __name__ == '__main__':
    update_index_css()
