with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update setDashboardTimeframe tab button styling to avoid harsh dark colors
old_set_tf = """  if (type === 'week') {
    btnWeek?.classList.add('active');
    btnSem?.classList.remove('active');
    if (btnWeek) { btnWeek.style.background = '#07152b !important'; btnWeek.style.color = '#ffffff !important'; }
    if (btnSem) { btnSem.style.background = 'transparent'; btnSem.style.color = '#1e293b'; }
    weekSelector?.classList.remove('hidden');
    semSelector?.classList.add('hidden');
  } else {
    btnSem?.classList.add('active');
    btnWeek?.classList.remove('active');
    if (btnSem) { btnSem.style.background = '#07152b !important'; btnSem.style.color = '#ffffff !important'; }
    if (btnWeek) { btnWeek.style.background = 'transparent'; btnWeek.style.color = '#1e293b'; }
    weekSelector?.classList.add('hidden');
    semSelector?.classList.remove('hidden');
  }"""

new_set_tf = """  if (type === 'week') {
    btnWeek?.classList.add('active');
    btnSem?.classList.remove('active');
    if (btnWeek) { btnWeek.style.background = ''; btnWeek.style.color = ''; }
    if (btnSem) { btnSem.style.background = ''; btnSem.style.color = ''; }
    weekSelector?.classList.remove('hidden');
    semSelector?.classList.add('hidden');
  } else {
    btnSem?.classList.add('active');
    btnWeek?.classList.remove('active');
    if (btnSem) { btnSem.style.background = ''; btnSem.style.color = ''; }
    if (btnWeek) { btnWeek.style.background = ''; btnWeek.style.color = ''; }
    weekSelector?.classList.add('hidden');
    semSelector?.classList.remove('hidden');
  }"""

# 2. Update renderDashboardTable
old_table_rows = """    let rankBadge = `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-slate-200 text-slate-900 font-black text-xs">${rankNum}</span>`;
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
    `;"""

new_table_rows = """    let rankBadge = `<span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-slate-100 text-slate-600 font-semibold text-xs">${rankNum}</span>`;
    if (rankNum === 1) rankBadge = `<span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-amber-100 text-amber-800 font-bold text-xs border border-amber-200" title="Hạng 1">🥇</span>`;
    else if (rankNum === 2) rankBadge = `<span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-slate-200 text-slate-700 font-bold text-xs" title="Hạng 2">🥈</span>`;
    else if (rankNum === 3) rankBadge = `<span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-orange-100 text-orange-800 font-bold text-xs border border-orange-200" title="Hạng 3">🥉</span>`;
    else if (rankNum <= 10) rankBadge = `<span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-50 text-blue-700 font-semibold text-xs border border-blue-200/60">${rankNum}</span>`;

    const scoreNum = Number(score);
    const progressWidth = Math.min(100, Math.max(0, (scoreNum / 100) * 100));
    let progressColor = 'bg-emerald-500';
    if (scoreNum < 85) progressColor = 'bg-rose-500';
    else if (scoreNum < 95) progressColor = 'bg-amber-400';

    return `
      <tr class="hover:bg-slate-50/70 border-b border-slate-100 transition-colors text-xs">
        <td class="py-2.5 px-3.5 text-center">${rankBadge}</td>
        <td class="py-2.5 px-3.5 font-semibold text-slate-900">${escapeHtml(c.name)}</td>
        <td class="py-2.5 px-3 text-center"><span class="text-[11px] font-medium px-2 py-0.5 rounded-md bg-slate-100 text-slate-600">Khối ${c.grade}</span></td>
        <td class="py-2.5 px-3 text-right font-medium font-mono text-emerald-600">+${bonus}</td>
        <td class="py-2.5 px-3 text-right font-medium font-mono text-rose-600">-${penalty}</td>
        <td class="py-2.5 px-3.5 text-right font-bold font-mono text-slate-900">${score}</td>
        <td class="py-2.5 px-4">
          <div class="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden flex" title="${progressWidth}% chuẩn">
            <div class="${progressColor} h-1.5 rounded-full transition-all duration-300" style="width: ${progressWidth}%"></div>
          </div>
        </td>
        <td class="py-2.5 px-3 text-center">
          <span class="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-xs font-medium ${violations > 0 ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-slate-100 text-slate-500'}">${violations}</span>
        </td>
      </tr>
    `;"""

# 3. Update podium render
old_podium_html = """  container.innerHTML = `
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
  `;"""

new_podium_html = """  container.innerHTML = `
    <!-- HẠNG 2 (Á QUÂN - BẠC) -->
    ${c2 ? `
    <div class="podium-pillar podium-silver" onclick="navigateTab('competition')">
      <div class="podium-crown-badge">🥈</div>
      <span class="text-[11px] font-semibold uppercase tracking-wider text-slate-600">Á Quân · Hạng 2</span>
      <h4 class="podium-class-title text-base text-slate-800 font-bold">${escapeHtml(c2.name)}</h4>
      <div class="podium-score-pill text-xl text-slate-700 font-bold font-mono">${s2}đ</div>
      <div class="podium-sub-text text-slate-500 font-medium">Cộng +${b2} · Trừ -${p2}</div>
    </div>
    ` : '<div class="podium-pillar podium-silver opacity-40"><div class="podium-crown-badge">🥈</div><span class="text-xs text-slate-400 font-medium">Đang cập nhật</span></div>'}

    <!-- HẠNG 1 (QUÁN QUÂN - VÀNG) -->
    <div class="podium-pillar podium-gold" onclick="navigateTab('competition')">
      <div class="podium-crown-badge">👑</div>
      <span class="text-[11px] font-semibold uppercase tracking-wider text-amber-800">Quán Quân · Hạng 1</span>
      <h3 class="podium-class-title text-lg text-slate-900 font-bold">${escapeHtml(c1.name)}</h3>
      <div class="podium-score-pill text-2xl text-amber-700 font-bold font-mono">${s1}đ</div>
      <div class="podium-sub-text text-amber-800/80 font-medium">Cộng +${b1} · Trừ -${p1} điểm</div>
    </div>

    <!-- HẠNG 3 (QUÝ QUÂN - ĐỒNG) -->
    ${c3 ? `
    <div class="podium-pillar podium-bronze" onclick="navigateTab('competition')">
      <div class="podium-crown-badge">🥉</div>
      <span class="text-[11px] font-semibold uppercase tracking-wider text-orange-700">Quý Quân · Hạng 3</span>
      <h4 class="podium-class-title text-base text-slate-800 font-bold">${escapeHtml(c3.name)}</h4>
      <div class="podium-score-pill text-xl text-orange-700 font-bold font-mono">${s3}đ</div>
      <div class="podium-sub-text text-orange-700/80 font-medium">Cộng +${b3} · Trừ -${p3}</div>
    </div>
    ` : '<div class="podium-pillar podium-bronze opacity-40"><div class="podium-crown-badge">🥉</div><span class="text-xs text-slate-400 font-medium">Đang cập nhật</span></div>'}
  `;"""

content_norm = content.replace('\r\n', '\n')
old_set_tf_norm = old_set_tf.replace('\r\n', '\n')
new_set_tf_norm = new_set_tf.replace('\r\n', '\n')
old_table_rows_norm = old_table_rows.replace('\r\n', '\n')
new_table_rows_norm = new_table_rows.replace('\r\n', '\n')
old_podium_html_norm = old_podium_html.replace('\r\n', '\n')
new_podium_html_norm = new_podium_html.replace('\r\n', '\n')

assert old_set_tf_norm in content_norm, "old_set_tf not found"
content_norm = content_norm.replace(old_set_tf_norm, new_set_tf_norm, 1)

assert old_table_rows_norm in content_norm, "old_table_rows not found"
content_norm = content_norm.replace(old_table_rows_norm, new_table_rows_norm, 1)

assert old_podium_html_norm in content_norm, "old_podium_html not found"
content_norm = content_norm.replace(old_podium_html_norm, new_podium_html_norm, 1)

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content_norm.replace('\n', '\r\n'))

print("Updated table rows, podiums, and timeframe buttons in static/app.js successfully!")
