"""Inject premium CSS into index.html after the prefers-reduced-motion block."""
import os, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
html_path = BASE / "templates" / "index.html"

content = html_path.read_text(encoding="utf-8")

MARKER = "    }\r\n  </style>\r\n</head>"
if MARKER not in content:
    # try LF
    MARKER = "    }\n  </style>\n</head>"

if MARKER not in content:
    print("ERROR: Could not find insertion marker")
    sys.exit(1)

CSS_BLOCK = """    }

    /* ===== PREMIUM DESIGN SYSTEM v2 ===== */
    .app-header { position:sticky; top:0; z-index:40; background:var(--hk-navy); box-shadow:0 1px 3px rgba(0,0,0,.15); }
    .app-header-inner { max-width:1280px; margin:0 auto; padding:0 20px; height:58px; display:flex; align-items:center; gap:16px; }
    .app-brand { display:flex; align-items:center; gap:10px; flex-shrink:0; text-decoration:none; color:white; }
    .app-brand-icon { width:32px; height:32px; display:grid; place-items:center; background:rgba(255,255,255,.12); border-radius:8px; color:white; }
    .app-brand-name { font-size:13px; font-weight:700; color:white; letter-spacing:-.01em; line-height:1.2; max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .app-brand-sub { font-size:10px; color:rgba(255,255,255,.5); font-weight:500; }
    .app-header-meta { flex:1; display:flex; align-items:center; gap:14px; justify-content:center; }
    .app-year-badge { font-size:11px; font-weight:600; color:rgba(255,255,255,.8); background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.15); border-radius:20px; padding:3px 10px; }
    .app-datetime { font-family:ui-monospace,monospace; font-size:11px; color:rgba(255,255,255,.6); }
    .app-header-actions { display:flex; align-items:center; gap:6px; flex-shrink:0; position:relative; }
    .app-notif-btn { position:relative; width:34px; height:34px; display:grid; place-items:center; color:rgba(255,255,255,.7); background:transparent; border:0; border-radius:7px; cursor:pointer; }
    .app-notif-btn:hover { background:rgba(255,255,255,.1); color:white; }
    .app-notif-badge { position:absolute; top:3px; right:3px; min-width:16px; height:16px; display:inline-flex; align-items:center; justify-content:center; padding:0 4px; background:var(--hk-error); color:white; font-size:9px; font-weight:700; border-radius:99px; line-height:1; }
    .app-notif-dropdown { position:absolute; top:calc(100% + 8px); right:0; z-index:50; width:340px; background:white; border:1px solid var(--hk-line); border-radius:12px; box-shadow:0 12px 40px rgba(20,35,55,.15); overflow:hidden; }
    .app-notif-header { display:flex; align-items:center; justify-content:space-between; padding:12px 14px; border-bottom:1px solid var(--hk-line); font-size:13px; font-weight:700; color:var(--hk-ink); }
    .app-notif-mark-all { font-size:11px; color:var(--hk-blue); background:transparent; border:0; cursor:pointer; font-weight:600; }
    .app-notif-list { max-height:360px; overflow-y:auto; }
    .app-user-badge { display:flex; align-items:center; gap:8px; padding:5px 8px; background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.12); border-radius:8px; }
    .app-user-avatar { width:26px; height:26px; flex-shrink:0; display:grid; place-items:center; background:var(--hk-blue); color:white; border-radius:50%; font-size:10px; font-weight:700; }
    .app-user-avatar-img { width:26px; height:26px; border-radius:50%; object-fit:cover; }
    .app-user-name { font-size:12px; font-weight:700; color:white; max-width:120px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .app-user-role { font-size:10px; color:rgba(255,255,255,.55); }
    .app-logout-btn { display:flex; align-items:center; gap:5px; padding:6px 10px; background:rgba(184,61,69,.15); border:1px solid rgba(184,61,69,.25); color:#f9a0a5; border-radius:7px; font-size:11px; font-weight:600; cursor:pointer; font-family:inherit; }
    .app-logout-btn:hover { background:rgba(184,61,69,.3); color:white; }
    .app-mobile-menu-btn { width:34px; height:34px; display:none; place-items:center; background:rgba(255,255,255,.08); color:rgba(255,255,255,.8); border:1px solid rgba(255,255,255,.12); border-radius:7px; cursor:pointer; }
    .app-sidebar-inner { position:sticky; top:74px; background:white; border:1px solid var(--hk-line); border-radius:12px; padding:8px; box-shadow:0 1px 3px rgba(32,42,53,.04); }
    .nav-group-label { padding:12px 10px 4px; font-size:10px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--hk-muted); }
    .nav-group-sep { margin:4px 10px; border:0; border-top:1px solid var(--hk-line); }
    .nav-item { display:flex !important; align-items:center; gap:10px; width:100%; padding:8px 10px; margin-bottom:1px; font-size:13px; font-weight:500; color:#5a6978; background:transparent; border:0; border-radius:8px; text-align:left; cursor:pointer; transition:background .15s,color .15s; border-left:3px solid transparent; }
    .nav-item i,.nav-item svg { width:16px; height:16px; flex-shrink:0; }
    .nav-item:hover { background:#f0f4f8; color:var(--hk-navy); }
    .nav-item.is-active { background:#eff4fa; color:var(--hk-navy); font-weight:700; border-left-color:var(--hk-blue); }
    .quick-widget { margin-top:10px; padding:14px; background:var(--hk-navy); border-radius:10px; color:white; }
    .quick-widget h3 { font-size:12px; font-weight:700; margin:0 0 4px; display:flex; align-items:center; gap:6px; }
    .quick-widget p { font-size:11px; opacity:.6; margin:0 0 10px; line-height:1.5; }
    .quick-widget-btn { width:100%; padding:8px; background:#f59e0b; color:#111; border:0; border-radius:7px; font-size:12px; font-weight:700; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:6px; font-family:inherit; }
    .quick-widget-btn:hover { background:#fbbf24; }
    .tab-pane { animation:hkFadeIn .18s ease; }
    @keyframes hkFadeIn { from{opacity:.6;transform:translateY(4px)} to{opacity:1;transform:translateY(0)} }
    .workspace-stat-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:1px; background:var(--hk-line); border:1px solid var(--hk-line); border-radius:10px; overflow:hidden; }
    .workspace-stat { padding:16px 18px; background:white; border-right:0; }
    .workspace-stat-label { font-size:11px; color:var(--hk-muted); font-weight:600; letter-spacing:.02em; display:block; margin-bottom:6px; }
    .workspace-stat-value { font-size:26px; font-weight:800; color:var(--hk-navy); line-height:1; display:block; font-variant-numeric:tabular-nums; }
    .workspace-action-list { display:grid; grid-template-columns:repeat(auto-fill,minmax(155px,1fr)); gap:8px; border-top:0; }
    .workspace-action { display:flex; align-items:center; justify-content:space-between; gap:8px; padding:11px 13px; background:white; border:1px solid var(--hk-line) !important; border-radius:9px; color:var(--hk-navy); font-size:13px; font-weight:650; cursor:pointer; transition:all .15s; margin-right:0 !important; }
    .workspace-action:hover { border-color:var(--hk-blue) !important; background:#f7fbff; color:var(--hk-blue); }
    .loading-dot { animation:hkPulse 1.2s ease-in-out infinite; }
    @keyframes hkPulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(.8)} }
    .toast { display:flex; align-items:center; gap:10px; padding:12px 16px; border-radius:9px; font-size:13px; font-weight:600; color:white; box-shadow:0 8px 24px rgba(0,0,0,.15); pointer-events:all; animation:hkSlideIn .22s ease; max-width:360px; transition:opacity .3s,transform .3s; }
    @keyframes hkSlideIn { from{transform:translateX(100%);opacity:0} to{transform:translateX(0);opacity:1} }
    .toast.success { background:var(--hk-ok); }
    .toast.error { background:var(--hk-error); }
    .toast.warning { background:var(--hk-warn); }
    .toast.info { background:var(--hk-blue); }
    .workspace-status { display:inline-flex; align-items:center; gap:4px; min-height:22px; padding:2px 8px; font-size:11px; font-weight:650; border-radius:4px; white-space:nowrap; }
    .workspace-status.pending { color:#834e0d; background:#fef3c7; border:1px solid #fde68a; }
    .workspace-status.approved,.workspace-status.active { color:#166534; background:#dcfce7; border:1px solid #bbf7d0; }
    .workspace-status.rejected,.workspace-status.revoked { color:#991b1b; background:#fee2e2; border:1px solid #fecaca; }
    .workspace-empty { padding:32px 16px; text-align:center; color:var(--hk-muted); font-size:13px; line-height:1.6; }
    .workspace-error { padding:12px 14px; background:#fff5f5; border:1px solid #fecaca; border-radius:8px; color:var(--hk-error); font-size:12px; }
    .workspace-error button { margin-left:8px; color:var(--hk-error); text-decoration:underline; background:none; border:0; cursor:pointer; }
    .comp-grade-tab { padding:7px 16px; border-radius:7px; font-size:12px; font-weight:600; border:0; cursor:pointer; transition:all .15s; }
    .comp-grade-tab:hover:not([class*="bg-brand"]) { background:#f0f4f8; color:var(--hk-navy); }
    .mobile-nav-button { display:flex; flex-direction:column; align-items:center; gap:3px; min-width:50px; padding:5px 6px; font-size:10px; font-weight:600; color:var(--hk-muted); background:transparent; border:0; border-radius:7px; cursor:pointer; }
    .mobile-nav-button.is-active { color:var(--hk-blue); }
    .mobile-nav-button span { max-width:60px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    @media (max-width:768px) {
      .app-header-inner { padding:0 14px; height:52px; gap:10px; }
      .app-header-meta { display:none; }
      .app-brand-name { max-width:110px; font-size:11px; }
      .app-brand-sub { display:none; }
      .app-notif-dropdown { width:min(320px,calc(100vw - 24px)); right:-8px; }
      .app-mobile-menu-btn { display:grid; }
    }
  </style>
</head>"""

# Find the LAST occurrence of the marker (the closing of reduced-motion block + </style></head>)
idx = content.rfind(MARKER)
if idx == -1:
    print("ERROR: marker not found")
    sys.exit(1)

# Replace closing block with CSS + closing
new_content = content[:idx] + CSS_BLOCK + content[idx + len(MARKER):]
html_path.write_text(new_content, encoding="utf-8")
print("CSS injected successfully!")
print("File size:", len(new_content))
