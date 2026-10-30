import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. Update competition/services.py
p_services = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\competition\services.py'
with open(p_services, 'r', encoding='utf-8') as f:
    services_text = f.read()

target1 = """    if not user.is_active or not getattr(user, 'is_approved', False):
        return classes.none()
    if user.is_admin or user.is_bgh:
        return classes"""

replace1 = """    if not user.is_active or not getattr(user, 'is_approved', False):
        return classes.none()
    if user.is_admin or user.is_bgh or user.is_doan_truong:
        return classes"""

if target1 in services_text:
    services_text = services_text.replace(target1, replace1, 1)
    with open(p_services, 'w', encoding='utf-8') as f:
        f.write(services_text)
    print("[OK] Updated get_competition_class_scope in competition/services.py")
else:
    print("[SKIP] target1 not found in competition/services.py")

# 2. Update competition/views.py
p_views = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\competition\views.py'
with open(p_views, 'r', encoding='utf-8') as f:
    views_text = f.read()

replacements = [
    # perform_create
    (
        'if not (user.is_admin or user.is_bgh):\n        raise permissions.PermissionDenied("Chỉ Quản trị viên hoặc BGH mới có quyền tạo kỳ thi đua.")',
        'if not (user.is_admin or user.is_bgh or user.is_doan_truong):\n        raise permissions.PermissionDenied("Chỉ Quản trị viên, BGH hoặc Đoàn trường mới có quyền tạo kỳ thi đua.")'
    ),
    # perform_update
    (
        'if not (user.is_admin or user.is_bgh):\n        raise permissions.PermissionDenied("Bạn không có quyền chỉnh sửa kỳ thi đua.")',
        'if not (user.is_admin or user.is_bgh or user.is_doan_truong):\n        raise permissions.PermissionDenied("Bạn không có quyền chỉnh sửa kỳ thi đua.")'
    ),
    # dashboard
    (
        'may_view_unpublished = user.is_admin or user.is_bgh\n        current_periods = {}',
        'may_view_unpublished = user.is_admin or user.is_bgh or user.is_doan_truong\n        current_periods = {}'
    ),
    # init_standard_schedule
    (
        'if not (user.is_admin or user.is_bgh):\n            return Response({\'error\': \'Bạn không có quyền khởi tạo lịch trình năm học\'}, status=status.HTTP_403_FORBIDDEN)',
        'if not (user.is_admin or user.is_bgh or user.is_doan_truong):\n            return Response({\'error\': \'Bạn không có quyền khởi tạo lịch trình năm học\'}, status=status.HTTP_403_FORBIDDEN)'
    ),
    # scores - period.is_published
    (
        'if not period.is_published and not (user.is_admin or user.is_bgh):\n            return Response({\'error\': \'Kỳ thi đua chưa được công bố.\'}, status=status.HTTP_404_NOT_FOUND)\n        class_scope = get_competition_class_scope(user, period.academic_year)\n        class_ids = None if user.is_admin or user.is_bgh else list(class_scope.values_list(\'id\', flat=True))',
        'if not period.is_published and not (user.is_admin or user.is_bgh or user.is_doan_truong):\n            return Response({\'error\': \'Kỳ thi đua chưa được công bố.\'}, status=status.HTTP_404_NOT_FOUND)\n        class_scope = get_competition_class_scope(user, period.academic_year)\n        class_ids = None if (user.is_admin or user.is_bgh or user.is_doan_truong) else list(class_scope.values_list(\'id\', flat=True))'
    ),
    # scores - may_view_unpublished
    (
        '# Lấy kỳ trước đó tương ứng (để lấy điểm và thứ hạng so sánh)\n        may_view_unpublished = user.is_admin or user.is_bgh',
        '# Lấy kỳ trước đó tương ứng (để lấy điểm và thứ hạng so sánh)\n        may_view_unpublished = user.is_admin or user.is_bgh or user.is_doan_truong'
    ),
    # class_detail - is_published & scope
    (
        'if not period.is_published and not (user.is_admin or user.is_bgh):\n            return Response({\'error\': \'Kỳ thi đua chưa được công bố.\'}, status=status.HTTP_404_NOT_FOUND)',
        'if not period.is_published and not (user.is_admin or user.is_bgh or user.is_doan_truong):\n            return Response({\'error\': \'Kỳ thi đua chưa được công bố.\'}, status=status.HTTP_404_NOT_FOUND)'
    ),
    (
        'class_scope = get_competition_class_scope(user, period.academic_year)\n        if not (user.is_admin or user.is_bgh) and not class_scope.filter(pk=school_class.pk).exists():',
        'class_scope = get_competition_class_scope(user, period.academic_year)\n        if not (user.is_admin or user.is_bgh or user.is_doan_truong) and not class_scope.filter(pk=school_class.pk).exists():'
    ),
    # class_detail - score_obj calendar_review
    (
        'score_obj = None if state[\'code\'] == \'NOT_STARTED\' or (\n            state[\'calendar_review\'] and not (user.is_admin or user.is_bgh)\n        ) else score_query.first()',
        'score_obj = None if state[\'code\'] == \'NOT_STARTED\' or (\n            state[\'calendar_review\'] and not (user.is_admin or user.is_bgh or user.is_doan_truong)\n        ) else score_query.first()'
    ),
    # class_detail - history_scores
    (
        'if not (user.is_admin or user.is_bgh):\n            history_scores = history_scores.filter(competition_period__is_published=True)',
        'if not (user.is_admin or user.is_bgh or user.is_doan_truong):\n            history_scores = history_scores.filter(competition_period__is_published=True)'
    ),
    # class_detail - history_scores calendar_review
    (
        'if not (user.is_admin or user.is_bgh) and get_period_status(hs.competition_period)[\'calendar_review\']:',
        'if not (user.is_admin or user.is_bgh or user.is_doan_truong) and get_period_status(hs.competition_period)[\'calendar_review\']:'
    )
]

for old, new in replacements:
    if old in views_text:
        views_text = views_text.replace(old, new, 1)
        print("[OK] Replaced pattern in competition/views.py")
    else:
        print(f"[SKIP] Pattern not found in competition/views.py: {old[:50]}...")

with open(p_views, 'w', encoding='utf-8') as f:
    f.write(views_text)

# 3. Update reports/services.py
p_rep = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\reports\services.py'
with open(p_rep, 'r', encoding='utf-8') as f:
    rep_text = f.read()

rep_replacements = [
    (
        'if exported_by and not period.is_published and not (exported_by.is_admin or exported_by.is_bgh):',
        'if exported_by and not period.is_published and not (exported_by.is_admin or exported_by.is_bgh or exported_by.is_doan_truong):'
    ),
    (
        'if exported_by and not (exported_by.is_admin or exported_by.is_bgh):',
        'if exported_by and not (exported_by.is_admin or exported_by.is_bgh or exported_by.is_doan_truong):'
    ),
    (
        'def _scope_violation_queryset(queryset, exported_by):\n    if not exported_by or exported_by.is_admin or exported_by.is_bgh:',
        'def _scope_violation_queryset(queryset, exported_by):\n    if not exported_by or exported_by.is_admin or exported_by.is_bgh or exported_by.is_doan_truong:'
    )
]

for old, new in rep_replacements:
    count = rep_text.count(old)
    if count > 0:
        rep_text = rep_text.replace(old, new)
        print(f"[OK] Replaced {count} occurrence(s) in reports/services.py: {old[:50]}...")
    else:
        print(f"[SKIP] Pattern not found in reports/services.py: {old[:50]}...")

with open(p_rep, 'w', encoding='utf-8') as f:
    f.write(rep_text)

print("Patching completed successfully!")
