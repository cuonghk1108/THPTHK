# scripts/patch_js_part3.py
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Verify markers before making changes
assert 'container.innerHTML = `' in lines[5078], f"Podium marker mismatch: {lines[5078]}"
assert 'let rankBadge =' in lines[5276], f"Table marker mismatch: {lines[5276]}"
assert 'h-36 rounded-2xl bg-gradient-to-r from-blue-900' in lines[6334], f"Skeleton marker mismatch: {lines[6334]}"
assert 'Biên bản nề nếp đã phản ánh' in lines[7354], f"GVBM marker mismatch: {lines[7354]}"
assert 'Biên bản đã gửi' in lines[7502], f"Sao do marker mismatch: {lines[7502]}"
assert 'Hồ sơ cá nhân' in lines[7652], f"Student marker mismatch: {lines[7652]}"

# Replacements from bottom to top so indices remain valid
# 6. Student (lines 7650 to 7760)
new_student_lines = [
"""              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Hồ sơ cá nhân</span>
                <div class="edtech-kpi-icon bg-blue-50 text-blue-600"><i data-lucide="user" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-slate-800">${escapeHtml(clsName)}</span>
                <span class="edtech-kpi-badge bg-blue-50 text-blue-700 border border-blue-200/60 font-medium">Mã: ${escapeHtml(code)}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Thông tin đoàn viên</span>
                <span class="text-blue-600 font-medium">Xem hồ sơ →</span>
              </div>
            </div>

            <div class="edtech-kpi-card" onclick="navigateTab('competition')">
              <div class="edtech-kpi-header">
                <span class="edtech-kpi-title">Điểm thi đua lớp (${weekLabel})</span>
                <div class="edtech-kpi-icon bg-emerald-50 text-emerald-600"><i data-lucide="award" class="w-5 h-5"></i></div>
              </div>
              <div class="edtech-kpi-val-row">
                <span class="edtech-kpi-val text-emerald-700">${clsScore}</span>
                <span class="edtech-kpi-badge bg-emerald-50 text-emerald-700 border border-emerald-200/60 font-medium">Hạng: ${clsRank}</span>
              </div>
              <div class="edtech-kpi-footer">
                <span>Toàn trường</span>
                <span class="text-emerald-700 font-medium">Bảng vàng →</span>
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
                <span>${myV === 0 ? 'Tuyệt vời! Tiếp tục giữ vững nhé ✨' : 'Cần chú ý nội quy nhà trường'}</span>
              </div>
            </div>
          </div>

          <!-- PODIUM VINH DANH CHO HỌC SINH -->
          <div class="edtech-podium-card">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-semibold text-slate-800 text-base flex items-center gap-2">
                <i data-lucide="crown" class="w-5 h-5 text-amber-500"></i>
                Top 3 Chi Đoàn Dẫn Đầu Toàn Trường
              </h3>
"""
]
lines[7650:7760] = new_student_lines
print("[OK] Replaced Student")

# 5. Sao do (lines 7498 to 7564)
new_saodo_lines = [
"""            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
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
"""
]
lines[7498:7564] = new_saodo_lines
print("[OK] Replaced Sao do")

# 4. GVBM (lines 7350 to 7392)
new_gvbm_lines = [
"""            <div class="edtech-kpi-card" onclick="navigateTab('conduct')">
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
"""
]
lines[7350:7392] = new_gvbm_lines
print("[OK] Replaced GVBM")

# 3. Skeleton (lines 6334 to 6348)
new_skeleton_lines = [
"""      <div class="h-36 rounded-2xl bg-gradient-to-r from-blue-50 via-indigo-50 to-slate-50 border border-slate-200 animate-pulse"></div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="h-28 rounded-2xl bg-slate-100/70 border border-slate-200/70 animate-pulse"></div>
        <div class="h-28 rounded-2xl bg-slate-100/70 border border-slate-200/70 animate-pulse"></div>
        <div class="h-28 rounded-2xl bg-slate-100/70 border border-slate-200/70 animate-pulse"></div>
        <div class="h-28 rounded-2xl bg-slate-100/70 border border-slate-200/70 animate-pulse"></div>
      </div>
"""
]
lines[6334:6348] = new_skeleton_lines
print("[OK] Replaced Skeleton")

# 2. Table (lines 5276 to 5337)
new_table_lines = [
"""    let rankBadge = `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-slate-50 text-slate-500 font-medium text-xs border border-slate-200/60">${rankNum}</span>`;
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
"""
]
lines[5276:5337] = new_table_lines
print("[OK] Replaced Table")

# 1. Podium (lines 5078 to 5143)
new_podium_lines = [
"""  container.innerHTML = `
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
"""
]
lines[5078:5143] = new_podium_lines
print("[OK] Replaced Podium")

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Patch 3 executed successfully!")
