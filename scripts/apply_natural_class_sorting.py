# -*- coding: utf-8 -*-
import sys
import os
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"
conduct_models_path = os.path.join(BASE_DIR, "conduct", "models.py")
conduct_views_path = os.path.join(BASE_DIR, "conduct", "views.py")
comp_services_path = os.path.join(BASE_DIR, "competition", "services.py")
comp_views_path = os.path.join(BASE_DIR, "competition", "views.py")
core_views_path = os.path.join(BASE_DIR, "core", "views.py")
app_js_path = os.path.join(BASE_DIR, "static", "app.js")

# ==============================================================================
# 1. UPDATE conduct/models.py
# ==============================================================================
with open(conduct_models_path, "r", encoding="utf-8") as f:
    models_code = f.read()

# Add natural_class_sort_key if not present
if "def natural_class_sort_key" not in models_code:
    helper_code = '''
def natural_class_sort_key(val):
    """
    Sắp xếp tự nhiên chuẩn theo số thứ tự lớp từ nhỏ đến lớn:
    Ví dụ: 10A1 -> 10A2 -> ... -> 10A9 -> 10A10 -> ... -> 10A22
    """
    if val is None:
        return (0, '', 0)
    if hasattr(val, 'name'):
        name = val.name
        grade = getattr(val, 'grade', 0)
    elif hasattr(val, 'school_class'):
        name = val.school_class.name
        grade = getattr(val.school_class, 'grade', 0)
    elif isinstance(val, dict):
        name = val.get('name') or val.get('class_name') or val.get('school_class_name') or ''
        grade = val.get('grade') or 0
    else:
        name = str(val)
        grade = 0
    import re
    m = re.match(r'^(\\d+)([A-Za-zĐđ]+)(\\d+)$', name.strip())
    if m:
        return (int(m.group(1)), m.group(2).upper(), int(m.group(3)))
    m2 = re.match(r'^(\\d+)(.*)$', name.strip())
    if m2:
        try:
            num = int(re.search(r'\\d+', m2.group(2)).group()) if re.search(r'\\d+', m2.group(2)) else 0
        except Exception:
            num = 0
        return (int(m2.group(1)), m2.group(2).strip(), num)
    return (grade, name, 0)
'''
    models_code = helper_code + "\n" + models_code

target_class_def = """class SchoolClass(models.Model):
    name = models.CharField(max_length=20, verbose_name='Tên lớp (VD: 10A1, 11A2)')
    grade = models.PositiveSmallIntegerField(choices=[(10, 'Khối 10'), (11, 'Khối 11'), (12, 'Khối 12')], verbose_name='Khối lớp')"""

replacement_class_def = """class SchoolClass(models.Model):
    name = models.CharField(max_length=20, verbose_name='Tên lớp (VD: 10A1, 11A2)')
    grade = models.PositiveSmallIntegerField(choices=[(10, 'Khối 10'), (11, 'Khối 11'), (12, 'Khối 12')], verbose_name='Khối lớp')
    class_order = models.PositiveSmallIntegerField(default=1, verbose_name='Thứ tự lớp (1-22)')"""

if target_class_def in models_code and "class_order = models.PositiveSmallIntegerField" not in models_code:
    models_code = models_code.replace(target_class_def, replacement_class_def)

# Add save() method to SchoolClass
target_meta = """    class Meta:
        unique_together = ('name', 'academic_year')
        ordering = ['grade', 'name']"""

replacement_meta = """    def save(self, *args, **kwargs):
        if self.name:
            import re
            m = re.match(r'^(\\d+)[A-Za-zĐđ]+(\\d+)$', self.name.strip())
            if m:
                self.class_order = int(m.group(2))
            else:
                m2 = re.search(r'(\\d+)$', self.name.strip())
                if m2:
                    self.class_order = int(m2.group(1))
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('name', 'academic_year')
        ordering = ['grade', 'class_order', 'name']"""

if target_meta in models_code:
    models_code = models_code.replace(target_meta, replacement_meta)

with open(conduct_models_path, "w", encoding="utf-8") as f:
    f.write(models_code)

print("1. conduct/models.py updated successfully!")

# ==============================================================================
# 2. UPDATE conduct/views.py
# ==============================================================================
with open(conduct_views_path, "r", encoding="utf-8") as f:
    cviews_code = f.read()

# Add import if needed
if "from .models import (" in cviews_code and "natural_class_sort_key" not in cviews_code:
    cviews_code = cviews_code.replace("from .models import (", "from .models import (\n    natural_class_sort_key,")

# SchoolClassViewSet ordering
cviews_code = cviews_code.replace("return qs.order_by('grade', 'name')", "return qs.order_by('grade', 'class_order', 'name')")

# TeacherClassViewSet sorting
cviews_code = cviews_code.replace("res.sort(key=lambda x: (x['grade'], x['name']))", "res.sort(key=lambda x: natural_class_sort_key(x['name']))")

with open(conduct_views_path, "w", encoding="utf-8") as f:
    f.write(cviews_code)

print("2. conduct/views.py updated successfully!")

# ==============================================================================
# 3. UPDATE competition/services.py
# ==============================================================================
with open(comp_services_path, "r", encoding="utf-8") as f:
    services_code = f.read()

# Import natural_class_sort_key
if "from conduct.models import" in services_code and "natural_class_sort_key" not in services_code:
    services_code = services_code.replace("from conduct.models import", "from conduct.models import natural_class_sort_key,")
elif "natural_class_sort_key" not in services_code:
    services_code = "from conduct.models import natural_class_sort_key\n" + services_code

# Replace assign_ranks sort
target_assign_ranks = "scores.sort(key=lambda item: (-item.total_score, item.school_class.name))"
replacement_assign_ranks = "scores.sort(key=lambda item: (-item.total_score, natural_class_sort_key(item.school_class)))"
services_code = services_code.replace(target_assign_ranks, replacement_assign_ranks)

# Replace assign_grade_ranks sort
target_assign_grade = "grade_scores.sort(key=lambda item: (-item.total_score, item.school_class.name))"
replacement_assign_grade = "grade_scores.sort(key=lambda item: (-item.total_score, natural_class_sort_key(item.school_class)))"
services_code = services_code.replace(target_assign_grade, replacement_assign_grade)

# Replace classes query ordering in recalculate_period_scores
target_classes_query = "classes = list(SchoolClass.objects.filter(\n        academic_year=period.academic_year\n    ).order_by('name'))"
replacement_classes_query = "classes = list(SchoolClass.objects.filter(\n        academic_year=period.academic_year\n    ).order_by('grade', 'class_order', 'name'))"
services_code = services_code.replace(target_classes_query, replacement_classes_query)

with open(comp_services_path, "w", encoding="utf-8") as f:
    f.write(services_code)

print("3. competition/services.py updated successfully!")

# ==============================================================================
# 4. UPDATE competition/views.py
# ==============================================================================
with open(comp_views_path, "r", encoding="utf-8") as f:
    comp_views_code = f.read()

# Replace scores_qs ordering
comp_views_code = comp_views_code.replace(
    ".order_by('rank', 'school_class__name')",
    ".order_by('rank', 'school_class__grade', 'school_class__class_order', 'school_class__name')"
)

with open(comp_views_path, "w", encoding="utf-8") as f:
    f.write(comp_views_code)

print("4. competition/views.py updated successfully!")

# ==============================================================================
# 5. UPDATE core/views.py
# ==============================================================================
with open(core_views_path, "r", encoding="utf-8") as f:
    core_code = f.read()

core_code = core_code.replace(
    ".values('id', 'name', 'grade')\n            .order_by('grade', 'name')",
    ".values('id', 'name', 'grade')\n            .order_by('grade', 'class_order', 'name')"
)

with open(core_views_path, "w", encoding="utf-8") as f:
    f.write(core_code)

print("5. core/views.py updated successfully!")

# ==============================================================================
# 6. UPDATE static/app.js (Frontend natural class sort)
# ==============================================================================
with open(app_js_path, "r", encoding="utf-8") as f:
    js_code = f.read()

# Add naturalClassSort function if not present
if "function naturalClassSort" not in js_code:
    js_sort_func = """
// ==============================================================================
// SẮP XẾP LỚP HỌC TỰ NHIÊN HỆ THỐNG: A1 -> A2 -> ... -> A22 (TỪ NHỎ ĐẾN LỚN)
// ==============================================================================
function parseClassSortKey(val) {
  const str = (typeof val === 'string' ? val : (val?.name || val?.class_name || val?.school_class_name || '')).trim().toUpperCase();
  const m = str.match(/^(\\d+)?([A-ZĐ_]+)?(\\d+)?$/);
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
"""
    # Insert near the top after imports / state
    idx = js_code.find("let currentUser = null;")
    if idx != -1:
        js_code = js_code[:idx] + js_sort_func + "\n" + js_code[idx:]
    else:
        js_code = js_sort_func + "\n" + js_code

# Update renderTeacherClassesBar to sort filtered classes naturally
target_bar_sort = """    return true;
  });

  const countBadge = document.getElementById('teacher-classes-count-badge');"""

replacement_bar_sort = """    return true;
  });

  filtered.sort(naturalClassSort);

  const countBadge = document.getElementById('teacher-classes-count-badge');"""

if target_bar_sort in js_code:
    js_code = js_code.replace(target_bar_sort, replacement_bar_sort)

# Update class-quick-select-dropdown to sort each grade naturally
target_quick_drop = """    const k10 = teacherAssignedClasses.filter(c => c.grade === 10);
    const k11 = teacherAssignedClasses.filter(c => c.grade === 11);
    const k12 = teacherAssignedClasses.filter(c => c.grade === 12);"""

replacement_quick_drop = """    const k10 = teacherAssignedClasses.filter(c => c.grade === 10).sort(naturalClassSort);
    const k11 = teacherAssignedClasses.filter(c => c.grade === 11).sort(naturalClassSort);
    const k12 = teacherAssignedClasses.filter(c => c.grade === 12).sort(naturalClassSort);"""

if target_quick_drop in js_code:
    js_code = js_code.replace(target_quick_drop, replacement_quick_drop)

# Update renderDashboardTable tie breaker
target_dash_table_sort = """  list.sort((a, b) => {
    const pA = a[periodKey] || a.current_view || a.week || {};
    const pB = b[periodKey] || b.current_view || b.week || {};
    const sA = pA.total_score != null ? pA.total_score : 100;
    const sB = pB.total_score != null ? pB.total_score : 100;
    return sB - sA;
  });"""

replacement_dash_table_sort = """  list.sort((a, b) => {
    const pA = a[periodKey] || a.current_view || a.week || {};
    const pB = b[periodKey] || b.current_view || b.week || {};
    const sA = pA.total_score != null ? pA.total_score : 100;
    const sB = pB.total_score != null ? pB.total_score : 100;
    if (sB !== sA) return sB - sA;
    return naturalClassSort(a, b);
  });"""

if target_dash_table_sort in js_code:
    js_code = js_code.replace(target_dash_table_sort, replacement_dash_table_sort)

# Update renderClassComparisonChart tie breaker
target_chart_sort = """  list.sort((a, b) => {
    const pA = a[periodKey] || a.current_view || a.week || {};
    const pB = b[periodKey] || b.current_view || b.week || {};
    const sA = pA.total_score != null ? pA.total_score : 100;
    const sB = pB.total_score != null ? pB.total_score : 100;
    return sB - sA;
  });"""

# (If target_chart_sort appears multiple times, replace all)
js_code = js_code.replace(target_chart_sort, replacement_dash_table_sort)

with open(app_js_path, "w", encoding="utf-8") as f:
    f.write(js_code)

print("6. static/app.js updated successfully with naturalClassSort!")
print("ALL CODE UPDATES DONE!")
