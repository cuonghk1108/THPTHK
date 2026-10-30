import re

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Let's inspect what lines in app.js have 'font-black' or 'border-2'
# We can do targeted clean replacements

replacements = [
    # Hero buttons
    ('<i data-lucide="refresh-cw" class="w-4 h-4 text-blue-700"></i> Làm mới',
     '<i data-lucide="refresh-cw" class="w-3.5 h-3.5 text-slate-500"></i> Làm mới'),
    ('<i data-lucide="plus-circle" class="w-4 h-4 text-black"></i> Ghi vi phạm',
     '<i data-lucide="plus-circle" class="w-3.5 h-3.5 text-white"></i> Ghi vi phạm'),

    # Admin KPI 1
    ('<div class="edtech-kpi-icon bg-blue-100 text-blue-800 border-2 border-blue-300">',
     '<div class="edtech-kpi-icon bg-blue-50 text-blue-600">'),
    ('<span class="edtech-kpi-val text-[#07152b]">${avgScore}</span>',
     '<span class="edtech-kpi-val text-slate-900">${avgScore}</span>'),
    ('<span class="edtech-kpi-badge bg-emerald-100 text-emerald-950 border border-emerald-500 font-black">Chuẩn 100đ</span>',
     '<span class="edtech-kpi-badge bg-blue-50 text-blue-700 border border-blue-200/60 font-medium">Chuẩn 100đ</span>'),
    ('<span class="text-blue-700 font-extrabold">Bảng vàng →</span>',
     '<span class="text-brand-600 font-medium">Bảng vàng →</span>'),

    # Admin KPI 2
    ('<div class="edtech-kpi-icon bg-amber-100 text-amber-800 border-2 border-amber-300">',
     '<div class="edtech-kpi-icon bg-amber-50 text-amber-600">'),
    ('<span class="edtech-kpi-val text-amber-800">${pendingV}</span>',
     '<span class="edtech-kpi-val text-amber-600">${pendingV}</span>'),
    ("${pendingV > 0 ? 'bg-amber-400 text-black border border-amber-600 font-black' : 'bg-slate-200 text-slate-800 font-bold'}",
     "${pendingV > 0 ? 'bg-amber-50 text-amber-700 border border-amber-200/80 font-medium' : 'bg-slate-100 text-slate-600 font-medium'}"),
    ('<span class="text-amber-800 font-extrabold">Xử lý ngay →</span>',
     '<span class="text-amber-700 font-medium">Xử lý ngay →</span>'),

    # Admin KPI 3
    ('<div class="edtech-kpi-icon bg-rose-100 text-rose-800 border-2 border-rose-300">',
     '<div class="edtech-kpi-icon bg-rose-50 text-rose-600">'),
    ('<span class="edtech-kpi-val text-rose-700">${todayV}</span>',
     '<span class="edtech-kpi-val text-rose-600">${todayV}</span>'),
    ('<span class="edtech-kpi-badge bg-rose-100 text-rose-950 border border-rose-400 font-black">Tuần: ${verifiedW}</span>',
     '<span class="edtech-kpi-badge bg-rose-50 text-rose-700 border border-rose-200/80 font-medium">Tuần: ${verifiedW}</span>'),
    ('<span class="text-rose-700 font-extrabold">Xem nề nếp →</span>',
     '<span class="text-rose-600 font-medium">Xem nề nếp →</span>'),

    # Admin KPI 4
    ('<div class="edtech-kpi-icon bg-emerald-100 text-emerald-800 border-2 border-emerald-300">',
     '<div class="edtech-kpi-icon bg-emerald-50 text-emerald-600">'),
    ('<span class="edtech-kpi-val text-emerald-700">${isDoan ? rsPending : pendingAcc}</span>',
     '<span class="edtech-kpi-val text-emerald-600">${isDoan ? rsPending : pendingAcc}</span>'),
    ("${(isDoan ? rsPending : pendingAcc) > 0 ? 'bg-emerald-500 text-white border border-emerald-700 font-black' : 'bg-slate-200 text-slate-800 font-bold'}",
     "${(isDoan ? rsPending : pendingAcc) > 0 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/80 font-medium' : 'bg-slate-100 text-slate-600 font-medium'}"),
    ('<span class="text-emerald-700 font-extrabold">Phê duyệt →</span>',
     '<span class="text-emerald-700 font-medium">Phê duyệt →</span>'),

    # Timeframe bar
    ('<div class="edtech-segmented-nav inline-flex border-2 border-slate-300 p-0.5 rounded-xl bg-slate-100">',
     '<div class="edtech-segmented-nav inline-flex border border-slate-200/80 p-0.5 rounded-xl bg-slate-100/90">'),
    ('<button type="button" id="dash-btn-tf-week" onclick="setDashboardTimeframe(\'week\')" class="edtech-seg-btn active" style="background:#07152b !important; color:#ffffff !important;">',
     '<button type="button" id="dash-btn-tf-week" onclick="setDashboardTimeframe(\'week\')" class="edtech-seg-btn active">'),
    ('<button type="button" id="dash-btn-tf-semester" onclick="setDashboardTimeframe(\'semester\')" class="edtech-seg-btn" style="background:transparent; color:#1e293b;">',
     '<button type="button" id="dash-btn-tf-semester" onclick="setDashboardTimeframe(\'semester\')" class="edtech-seg-btn">'),
    ('<span class="text-xs font-black text-slate-800">Tuần:</span>',
     '<span class="text-xs font-medium text-slate-500">Tuần:</span>'),
    ('<select id="dash-week-select" onchange="onDashboardWeekSelect(this.value)" class="bg-white border-2 border-slate-300 rounded-xl px-2.5 py-1.5 text-xs font-black text-slate-900 focus:border-blue-600 focus:outline-none shadow-sm cursor-pointer min-w-[210px]">',
     '<select id="dash-week-select" onchange="onDashboardWeekSelect(this.value)" class="bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs font-semibold text-slate-800 focus:ring-1 focus:ring-brand-500 focus:outline-none shadow-xs cursor-pointer min-w-[200px]">'),
    ('<span class="text-xs font-black text-slate-800">Kỳ:</span>',
     '<span class="text-xs font-medium text-slate-500">Kỳ:</span>'),
    ('<select id="dash-sem-select" onchange="onDashboardSemesterSelect(this.value)" class="bg-white border-2 border-slate-300 rounded-xl px-2.5 py-1.5 text-xs font-black text-slate-900 focus:border-blue-600 focus:outline-none shadow-sm cursor-pointer min-w-[190px]">',
     '<select id="dash-sem-select" onchange="onDashboardSemesterSelect(this.value)" class="bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs font-semibold text-slate-800 focus:ring-1 focus:ring-brand-500 focus:outline-none shadow-xs cursor-pointer min-w-[190px]">'),

    # Podium Header
    ('<h3 class="font-black text-[#07152b] text-lg flex items-center gap-2" id="dashboard-podium-title">',
     '<h3 class="font-bold text-slate-900 text-base flex items-center gap-2" id="dashboard-podium-title">'),
    ('<p class="text-xs text-slate-700 font-semibold mt-0.5" id="dashboard-podium-sub">',
     '<p class="text-xs text-slate-500 font-normal mt-0.5" id="dashboard-podium-sub">'),
    ('<span class="text-xs font-black text-slate-800 mr-1">Khối lớp:</span>',
     '<span class="text-xs font-medium text-slate-500 mr-1">Khối lớp:</span>'),

    # Table Header & Count
    ('<h4 class="font-black text-slate-900 text-sm" id="dashboard-table-title">',
     '<h4 class="font-bold text-slate-900 text-sm" id="dashboard-table-title">'),
    ('<span id="dashboard-table-count" class="text-xs font-black text-white bg-[#07152b] px-2.5 py-0.5 rounded-full shadow-sm">',
     '<span id="dashboard-table-count" class="text-xs font-medium text-slate-600 bg-slate-100 px-2.5 py-0.5 rounded-full border border-slate-200/70">'),
    ('<i data-lucide="search" class="w-4 h-4 text-slate-600 absolute left-3 top-2.5"></i>',
     '<i data-lucide="search" class="w-4 h-4 text-slate-400 absolute left-3 top-2.5"></i>'),

    # Activity & Handbook cards
    ('<div class="bg-white p-5 rounded-2xl border-2 border-slate-300 shadow-sm">',
     '<div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">'),
    ('<div class="flex items-center justify-between mb-3 border-b-2 border-slate-100 pb-2">',
     '<div class="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">'),
    ('<h4 class="font-black text-slate-900 text-sm flex items-center gap-2">',
     '<h4 class="font-bold text-slate-900 text-sm flex items-center gap-2">'),
    ('<span class="text-xs text-slate-700 font-bold">Tuần hiện tại</span>',
     '<span class="text-xs text-slate-500">Tuần hiện tại</span>'),
    ('<span class="text-xs text-slate-700 font-bold">Quy chuẩn 2026</span>',
     '<span class="text-xs text-slate-500">Quy chuẩn 2026</span>'),
    ('<div class="p-3 bg-amber-50 border-2 border-amber-300 rounded-xl text-xs text-amber-950 flex items-center justify-between">',
     '<div class="p-3.5 bg-amber-50/70 border border-amber-200/80 rounded-xl text-xs text-amber-900 flex items-center justify-between">'),
    ('<strong class="font-black text-amber-900">Chi đoàn có điểm dưới 90đ:</strong>',
     '<strong class="font-semibold text-amber-900">Chi đoàn có điểm dưới 90đ:</strong>'),
    ('<p class="text-slate-800 font-medium mt-0.5">',
     '<p class="text-slate-600 mt-0.5">'),
    ('<button onclick="navigateTab(\'conduct\')" class="hk-btn hk-btn-primary text-xs py-1.5 px-3">Kiểm tra ngay</button>',
     '<button onclick="navigateTab(\'conduct\')" class="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-medium transition">Kiểm tra ngay</button>'),
    ('class="p-3 bg-slate-100 rounded-xl border-1.5 border-slate-300 flex items-center gap-2.5"',
     'class="p-3 bg-slate-50/80 rounded-xl border border-slate-100 flex items-center gap-2.5 text-slate-700"'),
    ('<strong class="font-black text-slate-950">', '<strong class="font-semibold text-slate-900">'),

    # GVCN Spotlight
    ('<div class="w-16 h-16 rounded-2xl bg-emerald-700 text-white flex items-center justify-center font-black text-2xl shadow border-2 border-emerald-900">',
     '<div class="w-14 h-14 rounded-2xl bg-emerald-600 text-white flex items-center justify-center font-bold text-xl shadow-xs">'),
    ('<span class="text-xs font-black text-emerald-900 uppercase tracking-wider">Tiêu điểm Chi đoàn chủ nhiệm</span>',
     '<span class="text-[11px] font-semibold text-emerald-800 uppercase tracking-wider">Tiêu điểm Chi đoàn chủ nhiệm</span>'),
    ('<h3 class="text-2xl font-black text-slate-950 mt-0.5">',
     '<h3 class="text-xl font-bold text-slate-900 mt-0.5">'),
    ('<p class="text-xs text-slate-700 font-bold">',
     '<p class="text-xs text-slate-600">'),
    ('<strong class="text-emerald-800 text-sm">${rank}</strong>',
     '<strong class="text-emerald-700 font-semibold">${rank}</strong>'),
    ('<strong class="text-emerald-800 text-sm">${rankGrade}</strong>',
     '<strong class="text-emerald-700 font-semibold">${rankGrade}</strong>'),
    ('<span class="text-xs text-slate-700 font-bold">Điểm thi đua ${weekLabel}:</span>',
     '<span class="text-xs text-slate-500 font-medium">Điểm thi đua ${weekLabel}:</span>'),
    ('<div class="text-3xl font-black text-[#07152b]">${score}đ</div>',
     '<div class="text-2xl font-bold font-mono text-slate-900">${score}đ</div>'),
    ('<span class="text-xs text-slate-800 font-bold">Cộng <strong class="text-emerald-700">+${bonus}</strong> · Trừ <strong class="text-rose-700">-${penalty}</strong></span>',
     '<span class="text-xs text-slate-600">Cộng <strong class="text-emerald-600">+${bonus}</strong> · Trừ <strong class="text-rose-600">-${penalty}</strong></span>'),

    # GVCN KPI Icons
    ('<div class="edtech-kpi-icon bg-blue-100 text-blue-900 border-2 border-blue-300"><i data-lucide="users" class="w-6 h-6"></i></div>',
     '<div class="edtech-kpi-icon bg-blue-50 text-blue-600"><i data-lucide="users" class="w-5 h-5"></i></div>'),
    ('<div class="edtech-kpi-icon bg-amber-100 text-amber-900 border-2 border-amber-300"><i data-lucide="bell" class="w-6 h-6"></i></div>',
     '<div class="edtech-kpi-icon bg-amber-50 text-amber-600"><i data-lucide="bell" class="w-5 h-5"></i></div>'),
    ('<div class="edtech-kpi-icon bg-emerald-100 text-emerald-900 border-2 border-emerald-300"><i data-lucide="trophy" class="w-6 h-6"></i></div>',
     '<div class="edtech-kpi-icon bg-emerald-50 text-emerald-600"><i data-lucide="trophy" class="w-5 h-5"></i></div>'),
    ('<span class="edtech-kpi-badge bg-blue-100 text-blue-950 font-black">Học sinh</span>',
     '<span class="edtech-kpi-badge bg-blue-50 text-blue-700 border border-blue-200/60 font-medium">Học sinh</span>'),
    ('<span class="edtech-kpi-badge bg-emerald-100 text-emerald-950 font-black">',
     '<span class="edtech-kpi-badge bg-emerald-50 text-emerald-700 border border-emerald-200/60 font-medium">'),
    ('<span class="text-blue-700 font-black">Xem chi tiết →</span>',
     '<span class="text-brand-600 font-medium">Xem chi tiết →</span>'),
    ('<span class="text-amber-800 font-black">Xem vi phạm →</span>',
     '<span class="text-amber-700 font-medium">Xem vi phạm →</span>'),
    ('<span class="text-emerald-700 font-black">Bảng thi đua →</span>',
     '<span class="text-emerald-700 font-medium">Bảng thi đua →</span>'),

    # GVBM KPI
    ('<div class="edtech-kpi-icon bg-blue-100 text-blue-900 border-2 border-blue-300"><i data-lucide="book-open" class="w-6 h-6"></i></div>',
     '<div class="edtech-kpi-icon bg-blue-50 text-blue-600"><i data-lucide="book-open" class="w-5 h-5"></i></div>'),
    ('<span class="edtech-kpi-badge bg-blue-100 text-blue-950 font-black">Lớp học</span>',
     '<span class="edtech-kpi-badge bg-blue-50 text-blue-700 border border-blue-200/60 font-medium">Lớp học</span>'),

    # Sao Đỏ KPI
    ('<div class="edtech-kpi-icon bg-blue-100 text-blue-900 border-2 border-blue-300"><i data-lucide="shield-check" class="w-6 h-6"></i></div>',
     '<div class="edtech-kpi-icon bg-blue-50 text-blue-600"><i data-lucide="shield-check" class="w-5 h-5"></i></div>'),
    ('<span class="edtech-kpi-badge bg-blue-100 text-blue-950 font-black">Đang trực</span>',
     '<span class="edtech-kpi-badge bg-blue-50 text-blue-700 border border-blue-200/60 font-medium">Đang trực</span>'),
    ('<div class="edtech-kpi-icon bg-amber-100 text-amber-900 border-2 border-amber-300"><i data-lucide="file-text" class="w-6 h-6"></i></div>',
     '<div class="edtech-kpi-icon bg-amber-50 text-amber-600"><i data-lucide="file-text" class="w-5 h-5"></i></div>'),
    ('<div class="edtech-kpi-icon bg-emerald-100 text-emerald-900 border-2 border-emerald-300"><i data-lucide="check-circle" class="w-6 h-6"></i></div>',
     '<div class="edtech-kpi-icon bg-emerald-50 text-emerald-600"><i data-lucide="check-circle" class="w-5 h-5"></i></div>'),

    # Student KPI & Podium
    ('border-2 border-${myV > 0 ? \'rose\' : \'emerald\'}-300', ''),
    ('border border-${myV > 0 ? \'rose\' : \'emerald\'}-400 font-black',
     'border border-${myV > 0 ? \'rose\' : \'emerald\'}-200 font-medium'),
    ('<span class="text-xs text-slate-800 font-black">${currentWeekName}',
     '<span class="text-xs text-slate-500 font-medium">${currentWeekName}'),
    ('<span class="text-emerald-700 font-black">Bảng vàng →</span>',
     '<span class="text-emerald-700 font-medium">Bảng vàng →</span>'),
]

matched = 0
for old, new in replacements:
    if old in code:
        code = code.replace(old, new)
        matched += 1
    else:
        print(f"Warning: pattern not found: {old[:50]}...")

print(f"Total replacements applied: {matched} / {len(replacements)}")

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(code)

print("Updated static/app.js successfully!")
