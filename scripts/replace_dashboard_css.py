NEW_EDTECH_CSS = """    .edtech-dash-wrap {
      animation: edtechFadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      background-color: #ffffff !important;
    }

    @keyframes edtechFadeIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* 1. HERO GREETING BANNER */
    .edtech-hero-card {
      background: linear-gradient(135deg, #f8fafc 0%, #f0f7ff 60%, #eff6ff 100%) !important;
      border: 1px solid #e2e8f0 !important;
      border-radius: 18px;
      padding: 22px 26px;
      color: #0f172a !important;
      position: relative;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
      margin-bottom: 20px;
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
      margin: 6px 0 4px;
      font-size: clamp(20px, 2.2vw, 25px);
      font-weight: 700;
      color: #0f172a !important;
      letter-spacing: -0.015em;
      line-height: 1.3;
    }

    .edtech-greeting-box p {
      margin: 0;
      font-size: 13px;
      color: #64748b !important;
      line-height: 1.5;
      font-weight: 400;
    }

    .edtech-role-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      background: #eff6ff !important;
      border: 1px solid #bfdbfe !important;
      padding: 3.5px 11px;
      border-radius: 9999px;
      font-size: 11.5px;
      font-weight: 600;
      letter-spacing: 0.02em;
      color: #1d4ed8 !important;
    }

    .edtech-live-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #f0fdf4 !important;
      border: 1px solid #bbf7d0 !important;
      color: #15803d !important;
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 11.5px;
      font-weight: 500;
    }

    .edtech-live-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #16a34a;
      box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.2);
    }

    .edtech-hero-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }

    .edtech-hero-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #ffffff !important;
      border: 1px solid #cbd5e1 !important;
      color: #334155 !important;
      padding: 7px 14px;
      border-radius: 10px;
      font-size: 12.5px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.15s ease;
      box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }

    .edtech-hero-btn:hover {
      background: #f8fafc !important;
      border-color: #94a3b8 !important;
      color: #0f172a !important;
    }

    .edtech-hero-btn-primary {
      background: #2563eb !important;
      border-color: #2563eb !important;
      color: #ffffff !important;
      box-shadow: 0 2px 8px rgba(37, 99, 235, 0.22);
    }

    .edtech-hero-btn-primary:hover {
      background: #1d4ed8 !important;
      border-color: #1d4ed8 !important;
      color: #ffffff !important;
      transform: translateY(-1px);
    }

    /* 2. KPI METRIC CARDS */
    .edtech-kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
      margin-bottom: 20px;
    }

    .edtech-kpi-card {
      background: #ffffff !important;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 16px 18px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      position: relative;
      overflow: hidden;
      cursor: pointer;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }

    .edtech-kpi-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
      border-color: #cbd5e1;
    }

    .edtech-kpi-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 10px;
    }

    .edtech-kpi-title {
      font-size: 12.5px;
      font-weight: 500;
      color: #64748b !important;
      line-height: 1.3;
    }

    .edtech-kpi-icon {
      width: 38px;
      height: 38px;
      border-radius: 10px;
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
      font-size: 27px;
      font-weight: 700;
      color: #0f172a;
      line-height: 1.15;
      font-variant-numeric: tabular-nums;
      letter-spacing: -0.02em;
    }

    .edtech-kpi-badge {
      font-size: 11px;
      font-weight: 500;
      padding: 3px 8px;
      border-radius: 6px;
      display: inline-flex;
      align-items: center;
      gap: 3px;
    }

    .edtech-kpi-footer {
      font-size: 11.5px;
      font-weight: 500;
      color: #64748b !important;
      margin-top: 10px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-top: 8px;
      border-top: 1px solid #f1f5f9;
    }

    /* 3. SEGMENTED CONTROLS */
    .edtech-tabs-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 18px;
      flex-wrap: wrap;
    }

    .edtech-segmented-nav {
      background: #f1f5f9;
      padding: 3.5px;
      border-radius: 12px;
      display: inline-flex;
      gap: 3px;
      border: 1px solid #e2e8f0;
    }

    .edtech-seg-btn {
      padding: 6.5px 14px;
      font-size: 12.5px;
      font-weight: 500;
      border-radius: 9px;
      transition: all 0.16s ease;
      border: none;
      background: transparent;
      color: #64748b;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .edtech-seg-btn:hover {
      color: #0f172a;
      background: rgba(255, 255, 255, 0.6);
    }

    .edtech-seg-btn.active {
      background: #ffffff !important;
      color: #1e40af !important;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
      font-weight: 600;
    }

    .edtech-seg-btn.active i {
      color: #2563eb !important;
    }

    /* 4. TASTEFUL TOP 3 PODIUM */
    .edtech-podium-card {
      background: #ffffff !important;
      border: 1px solid #e2e8f0;
      border-radius: 18px;
      padding: 20px 22px;
      margin-bottom: 18px;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }

    .edtech-podium-grid {
      display: grid;
      grid-template-columns: 1fr 1.05fr 1fr;
      gap: 14px;
      align-items: flex-end;
      margin-top: 14px;
    }

    @media (max-width: 768px) {
      .edtech-podium-grid {
        grid-template-columns: 1fr;
        align-items: stretch;
      }
    }

    .podium-pillar {
      border-radius: 16px;
      padding: 18px 16px;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      position: relative;
      overflow: hidden;
      transition: all 0.2s ease;
      cursor: pointer;
    }

    .podium-pillar:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    }

    .podium-gold {
      background: linear-gradient(180deg, #fffdf5 0%, #fefce8 60%, #fef08a 100%);
      border: 1px solid #fde047 !important;
      box-shadow: 0 4px 16px rgba(234, 179, 8, 0.12);
      min-height: 220px;
      order: 2;
    }

    .podium-silver {
      background: linear-gradient(180deg, #ffffff 0%, #f8fafc 60%, #f1f5f9 100%);
      border: 1px solid #e2e8f0 !important;
      box-shadow: 0 2px 10px rgba(100, 116, 139, 0.08);
      min-height: 195px;
      order: 1;
    }

    .podium-bronze {
      background: linear-gradient(180deg, #fffaf5 0%, #fff7ed 60%, #ffedd5 100%);
      border: 1px solid #fed7aa !important;
      box-shadow: 0 2px 10px rgba(234, 88, 12, 0.08);
      min-height: 185px;
      order: 3;
    }

    @media (max-width: 768px) {
      .podium-gold { order: 1; min-height: auto; }
      .podium-silver { order: 2; min-height: auto; }
      .podium-bronze { order: 3; min-height: auto; }
    }

    .podium-crown-badge {
      width: 40px;
      height: 40px;
      border-radius: 12px;
      display: grid;
      place-items: center;
      font-size: 19px;
      margin-bottom: 8px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.06);
      background: #ffffff;
      border: 1px solid rgba(0,0,0,0.05);
    }

    .podium-class-title {
      font-size: 17px;
      font-weight: 700;
      color: #0f172a !important;
      letter-spacing: -0.01em;
    }

    .podium-score-pill {
      font-size: 22px;
      font-weight: 700;
      margin: 4px 0 2px;
      font-variant-numeric: tabular-nums;
    }

    .podium-sub-text {
      font-size: 11.5px;
      font-weight: 500;
    }

    /* 5. LEADERBOARD TABLE */
    .edtech-table-container {
      background: #ffffff !important;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }

    .edtech-table-toolbar {
      padding: 12px 18px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      background: #ffffff !important;
      border-bottom: 1px solid #f1f5f9;
    }

    .edtech-search-input {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 9px;
      padding: 6px 12px 6px 32px;
      font-size: 12.5px;
      font-weight: 400;
      color: #0f172a;
      width: 220px;
      transition: all 0.16s ease;
    }

    .edtech-search-input:focus {
      background: #ffffff;
      border-color: #2563eb;
      outline: none;
      box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
    }

    .edtech-filter-pills {
      display: flex;
      align-items: center;
      gap: 5px;
      flex-wrap: wrap;
    }

    .edtech-filter-pill {
      font-size: 12px;
      font-weight: 500;
      padding: 5px 12px;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
      background: #f8fafc;
      color: #64748b;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .edtech-filter-pill:hover {
      background: #f1f5f9;
      color: #0f172a;
    }

    .edtech-filter-pill.active {
      background: #eff6ff !important;
      color: #1d4ed8 !important;
      border-color: #bfdbfe !important;
      font-weight: 600;
    }

    .edtech-table-head-dark {
      background: #f8fafc !important;
      color: #475569 !important;
      font-weight: 600;
    }

    .edtech-table-head-dark th {
      padding: 10px 14px;
      color: #475569 !important;
      font-weight: 600;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      border-bottom: 1px solid #e2e8f0;
    }

    /* 6. CHARTS SECTION */
    .edtech-chart-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
      gap: 16px;
      margin-bottom: 20px;
    }

    @media (max-width: 768px) {
      .edtech-chart-grid { grid-template-columns: 1fr; }
    }

    .edtech-chart-card {
      background: #ffffff !important;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 18px 20px;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }

    .edtech-chart-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 14px;
      padding-bottom: 10px;
      border-bottom: 1px solid #f1f5f9;
    }

    .edtech-chart-title {
      font-size: 13.5px;
      font-weight: 600;
      color: #0f172a !important;
      margin: 0;
    }

    .edtech-chart-desc {
      font-size: 12px;
      color: #64748b !important;
      font-weight: 400;
      margin: 2px 0 0;
    }

    .edtech-chart-canvas-wrap {
      position: relative;
      width: 100%;
      height: 270px;
    }

    /* 7. HOMEROOM & PERSONAL SPOTLIGHT CARDS */
    .edtech-personal-card {
      background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 60%, #f0fdf4 100%) !important;
      border: 1px solid #bbf7d0;
      border-radius: 16px;
      padding: 18px 22px;
      margin-bottom: 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      box-shadow: 0 1px 3px rgba(16, 185, 129, 0.05);
    }
"""

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\templates\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

start_str = "    .edtech-dash-wrap {"
end_str = "    /* ===== MODERN SCHOOL PORTAL & EDTECH DESIGN SYSTEM ===== */"

start_pos = content.find(start_str)
end_pos = content.find(end_str)

assert start_pos != -1 and end_pos != -1, "Could not locate start or end pos"

new_content = content[:start_pos] + NEW_EDTECH_CSS + "\n" + content[end_pos:]

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\templates\index.html', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(new_content)

print("Updated templates/index.html edtech CSS successfully!")
