# scripts/patch_competition_deduct_and_export.py
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

# 1. Update reports/services.py
p_reports = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\reports\services.py'
with open(p_reports, 'r', encoding='utf-8') as f:
    rep_content = f.read()

# Helper natural sort function to insert into reports/services.py if needed
helper_code = """
def get_natural_class_sort_key(score_item):
    c = score_item.school_class
    order = getattr(c, 'class_order', None)
    if order is not None:
        return (c.grade or 0, order, c.name)
    m = re.search(r'\\d+', c.name.replace(str(c.grade or ''), '', 1))
    num = int(m.group(0)) if m else 999
    return (c.grade or 0, num, c.name)
"""

if 'def get_natural_class_sort_key' not in rep_content:
    rep_content = helper_code + '\n' + rep_content
    print("[OK] Added get_natural_class_sort_key helper to reports/services.py")

old_excel_query = """    scores = ClassCompetitionScore.objects.filter(competition_period=period).select_related('school_class').order_by('rank')
    if exported_by and not (exported_by.is_admin or exported_by.is_bgh):
        scores = scores.filter(school_class__in=get_competition_class_scope(exported_by, period.academic_year))
    valid_ids = get_valid_aggregate_class_ids(period)
    if valid_ids is not None:
        scores = scores.filter(school_class_id__in=valid_ids)"""

new_excel_query = """    # Đảm bảo tính lại điểm thi đua thực tế mới nhất trước khi xuất file
    from competition.services import recalculate_period_scores
    recalculate_period_scores(period, force=True)

    scores_qs = ClassCompetitionScore.objects.filter(competition_period=period).select_related('school_class')
    if exported_by and not (exported_by.is_admin or exported_by.is_bgh):
        scores_qs = scores_qs.filter(school_class__in=get_competition_class_scope(exported_by, period.academic_year))
    valid_ids = get_valid_aggregate_class_ids(period)
    if valid_ids is not None:
        scores_qs = scores_qs.filter(school_class_id__in=valid_ids)
    
    # Sắp xếp các lớp từ 10A1-10A22, 11A1-11A21, 12A1-12A22 theo đúng yêu cầu
    scores = sorted(list(scores_qs), key=get_natural_class_sort_key)"""

if old_excel_query in rep_content:
    rep_content = rep_content.replace(old_excel_query, new_excel_query, 1)
    print("[OK] Updated export_competition_excel in reports/services.py")
else:
    print("[SKIP] export_competition_excel query pattern not found")

old_pdf_query = """    scores = ClassCompetitionScore.objects.filter(competition_period=period).select_related('school_class').order_by('rank')
    if exported_by and not (exported_by.is_admin or exported_by.is_bgh):
        scores = scores.filter(school_class__in=get_competition_class_scope(exported_by, period.academic_year))
    valid_ids = get_valid_aggregate_class_ids(period)
    if valid_ids is not None:
        scores = scores.filter(school_class_id__in=valid_ids)"""

# In PDF export
if old_pdf_query in rep_content:
    rep_content = rep_content.replace(old_pdf_query, new_excel_query, 1)
    print("[OK] Updated export_competition_pdf in reports/services.py")

with open(p_reports, 'w', encoding='utf-8') as f:
    f.write(rep_content)

# 2. Update competition/services.py
p_comp = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\competition\services.py'
with open(p_comp, 'r', encoding='utf-8') as f:
    comp_content = f.read()

old_aggregate = """    else:
        closed_weeks = list(_period_weeks(period).filter(is_locked=True))
        if not closed_weeks:
            return
        week_ids = [week.id for week in closed_weeks]
        source_scores = list(ClassCompetitionScore.objects.filter(
            competition_period_id__in=week_ids,
            school_class__in=classes,
        ).select_related('school_class'))
        by_class = {}
        for score in source_scores:
            by_class.setdefault(score.school_class_id, {})[score.competition_period_id] = score
        existing = {
            score.school_class_id: score
            for score in ClassCompetitionScore.objects.filter(competition_period=period).select_related('school_class')
        }
        scores_to_update = []
        for class_id, week_scores in by_class.items():
            if not all(week_id in week_scores for week_id in week_ids):
                continue
            rows = [week_scores[week_id] for week_id in week_ids]"""

new_aggregate = """    else:
        # Kỳ tổng hợp (Tháng, Học kỳ, Năm học):
        # Lấy tất cả các tuần đã khóa (is_locked=True) HOẶC các tuần đã/đang diễn ra (start_date <= today)
        today = timezone.localdate()
        closed_weeks = list(
            _period_weeks(period).filter(Q(is_locked=True) | Q(start_date__lte=today))
        )
        if not closed_weeks:
            return
        week_ids = [week.id for week in closed_weeks]
        source_scores = list(ClassCompetitionScore.objects.filter(
            competition_period_id__in=week_ids,
            school_class__in=classes,
        ).select_related('school_class'))
        by_class = {}
        for score in source_scores:
            by_class.setdefault(score.school_class_id, {})[score.competition_period_id] = score
        existing = {
            score.school_class_id: score
            for score in ClassCompetitionScore.objects.filter(competition_period=period).select_related('school_class')
        }
        scores_to_update = []
        for class_id, week_scores in by_class.items():
            rows = [week_scores[w_id] for w_id in week_ids if w_id in week_scores]
            if not rows:
                continue"""

if old_aggregate in comp_content:
    comp_content = comp_content.replace(old_aggregate, new_aggregate, 1)
    with open(p_comp, 'w', encoding='utf-8') as f:
        f.write(comp_content)
    print("[OK] Updated aggregate weeks logic in competition/services.py")
else:
    print("[SKIP] aggregate weeks logic pattern not found in competition/services.py")

# 3. Update static/app.js
p_app = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js'
with open(p_app, 'r', encoding='utf-8') as f:
    app_content = f.read()

# Make defaultPeriod prioritize TEMPORARY (ongoing week)
old_default_p = """    if (!defaultPeriod) {
      defaultPeriod = periodsCache.find(p => !p.calendar_requires_review && p.result_status === 'WAITING_LOCK')
        || periodsCache.find(p => !p.calendar_requires_review && p.result_status === 'NOT_STARTED')
        || periodsCache.find(p => !p.calendar_requires_review)
        || periodsCache[0];
    }"""

new_default_p = """    if (!defaultPeriod) {
      defaultPeriod = periodsCache.find(p => p.result_status === 'TEMPORARY')
        || periodsCache.find(p => !p.calendar_requires_review && p.result_status === 'WAITING_LOCK')
        || periodsCache.find(p => !p.calendar_requires_review && p.result_status === 'NOT_STARTED')
        || periodsCache.find(p => !p.calendar_requires_review)
        || periodsCache[0];
    }"""

if old_default_p in app_content:
    app_content = app_content.replace(old_default_p, new_default_p, 1)
    print("[OK] Updated defaultPeriod in static/app.js")
else:
    print("[SKIP] defaultPeriod pattern not found in static/app.js")

# Update exportCompetitionExcel & exportCompetitionPdf to check dropdown
old_export_fns = """function exportCompetitionExcel(periodId) {
  const pid = periodId || selectedPeriodId || (typeof currentPeriod !== 'undefined' && currentPeriod?.id);
  if (!pid) { showToast('Hãy chọn kỳ thi đua trước khi xuất báo cáo.', 'error'); return; }
  window.open(`/api/reports/competition/excel/${pid}/`, '_blank');
  showToast('Đang tạo và tải tệp Excel thi đua...', 'info');
}

function exportCompetitionPdf(periodId) {
  const pid = periodId || selectedPeriodId || (typeof currentPeriod !== 'undefined' && currentPeriod?.id);
  if (!pid) { showToast('Hãy chọn kỳ thi đua trước khi xuất báo cáo.', 'error'); return; }
  window.open(`/api/reports/competition/pdf/${pid}/`, '_blank');
  showToast('Đang tạo và tải tệp PDF thi đua (Times New Roman)...', 'info');
}"""

new_export_fns = """function exportCompetitionExcel(periodId) {
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
}"""

if old_export_fns in app_content:
    app_content = app_content.replace(old_export_fns, new_export_fns, 1)
    print("[OK] Updated export functions in static/app.js")
else:
    print("[SKIP] export functions pattern not found in static/app.js")

with open(p_app, 'w', encoding='utf-8') as f:
    f.write(app_content)

print("Patch complete!")
