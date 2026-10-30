import sys

with open('competition/services.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add import
old_import = 'from django.utils import timezone'
new_import = 'from django.utils import timezone\nfrom django.core.cache import cache\nfrom core.cache_utils import get_cache_version'
if 'get_cache_version' not in text:
    assert old_import in text, 'old_import not found'
    text = text.replace(old_import, new_import, 1)

# Target get_period_status
old_func = '''def get_period_status(period, today=None):
    today = today or timezone.localdate()
    if period.is_locked:'''

new_func = '''def get_period_status(period, today=None):
    today = today or timezone.localdate()
    cache_attr = f"_status_cache_{today}"
    if hasattr(period, cache_attr):
        return getattr(period, cache_attr)

    cache_key = None
    if getattr(period, 'pk', None):
        cache_key = f"comp_period_status_v{get_cache_version()}_{period.pk}_{today}_{getattr(period, 'is_locked', False)}"
        cached = cache.get(cache_key)
        if cached is not None:
            setattr(period, cache_attr, cached)
            return cached

    if period.is_locked:'''

if '_status_cache_' not in text:
    assert old_func in text, 'old_func not found'
    text = text.replace(old_func, new_func, 1)

old_return = '''    return {
        'code': code,
        'calendar_review': calendar_review,
        'display': {
            'NOT_STARTED': 'Chưa diễn ra',
            'TEMPORARY': 'Tạm tính',
            'WAITING_LOCK': 'Chờ chốt',
            'LOCKED': 'Đã chốt',
        }[code],
        'expected_week_numbers': sorted(expected),
        'configured_week_numbers': sorted(configured_numbers),
        'locked_week_numbers': sorted(locked_numbers),
        'expected_weeks': len(expected),
        'configured_weeks': len(configured_numbers),
        'included_weeks': int(period.is_locked) if period.period_type == CompetitionPeriod.TYPE_WEEK else len(locked_numbers),
        'complete_schedule': bool(expected) and expected.issubset(configured_numbers),
        'complete_result': bool(expected) and expected.issubset(locked_numbers),
        'requires_review': calendar_review or legacy_bonus_query.exists(),
    }'''

new_return = '''    res = {
        'code': code,
        'calendar_review': calendar_review,
        'display': {
            'NOT_STARTED': 'Chưa diễn ra',
            'TEMPORARY': 'Tạm tính',
            'WAITING_LOCK': 'Chờ chốt',
            'LOCKED': 'Đã chốt',
        }[code],
        'expected_week_numbers': sorted(expected),
        'configured_week_numbers': sorted(configured_numbers),
        'locked_week_numbers': sorted(locked_numbers),
        'expected_weeks': len(expected),
        'configured_weeks': len(configured_numbers),
        'included_weeks': int(period.is_locked) if period.period_type == CompetitionPeriod.TYPE_WEEK else len(locked_numbers),
        'complete_schedule': bool(expected) and expected.issubset(configured_numbers),
        'complete_result': bool(expected) and expected.issubset(locked_numbers),
        'requires_review': calendar_review or legacy_bonus_query.exists(),
    }
    setattr(period, cache_attr, res)
    if cache_key:
        cache.set(cache_key, res, timeout=60)
    return res'''

if 'setattr(period, cache_attr, res)' not in text:
    assert old_return in text, 'old_return not found'
    text = text.replace(old_return, new_return, 1)

with open('competition/services.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Successfully updated competition/services.py')
