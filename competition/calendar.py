"""School competition calendar defaults for the 2026–2027 school year.

Persisted CompetitionPeriod rows remain the operational calendar. These values
are used only to create missing periods; existing rows are never rewritten by
the schedule initializer.
"""

from datetime import date, timedelta

DEFAULT_ACADEMIC_YEAR = '2026-2027'
DEFAULT_YEAR_START = date(2026, 9, 7)
DEFAULT_YEAR_END = date(2027, 5, 9)
DEFAULT_WEEK_COUNT = 35
SEMESTER_WEEK_RANGES = {
    1: (1, 18),
    2: (19, 35),
}
COMPETITION_MONTH_WEEK_RANGES = {
    1: (1, 4),
    2: (5, 8),
    3: (9, 12),
    4: (13, 16),
    5: (17, 18),
    6: (19, 22),
    7: (23, 26),
    8: (27, 30),
    9: (31, 34),
    10: (35, 35),
}


def default_week_range(week_number):
    if not 1 <= int(week_number) <= DEFAULT_WEEK_COUNT:
        raise ValueError('Số tuần phải nằm trong khoảng 1–35.')
    start = DEFAULT_YEAR_START + timedelta(weeks=int(week_number) - 1)
    return start, start + timedelta(days=6)


def weeks_for_internal_month(month_number):
    return COMPETITION_MONTH_WEEK_RANGES.get(int(month_number))


def internal_month_number_for_week(week_number):
    week_number = int(week_number)
    for month_number, (first_week, last_week) in COMPETITION_MONTH_WEEK_RANGES.items():
        if first_week <= week_number <= last_week:
            return month_number
    return None
