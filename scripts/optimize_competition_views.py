import sys

with open('competition/views.py', 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8').replace('\r\n', '\n')

# 1. Imports
old_import = 'from rest_framework.response import Response'
new_import = '''from rest_framework.response import Response
from django.core.cache import cache
from core.cache_utils import get_cache_version, invalidate_all_caches'''
if 'get_cache_version' not in text:
    assert old_import in text, 'old_import not found'
    text = text.replace(old_import, new_import, 1)

# 2. filters_meta optimization
old_filters_meta = '''    @action(detail=False, methods=['get'], url_path='filters-meta')
    def filters_meta(self, request):
        """Trả về dữ liệu danh mục phục vụ bộ lọc xếp hạng thi đua (Năm học, Học kỳ, Loại kỳ, Tiêu chí)"""
        years = AcademicYear.objects.all().order_by('-start_date')'''

new_filters_meta = '''    @action(detail=False, methods=['get'], url_path='filters-meta')
    def filters_meta(self, request):
        """Trả về dữ liệu danh mục phục vụ bộ lọc xếp hạng thi đua (Năm học, Học kỳ, Loại kỳ, Tiêu chí)"""
        cache_key = f"comp_filters_meta_v{get_cache_version()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        years = AcademicYear.objects.all().order_by('-start_date')'''

if 'comp_filters_meta_v' not in text:
    assert old_filters_meta in text, 'old_filters_meta not found'
    text = text.replace(old_filters_meta, new_filters_meta, 1)

old_filters_block = '''        return Response({
            'academic_years': [
                {'id': y.id, 'name': y.name, 'is_current': y.is_current, 'start_date': str(y.start_date), 'end_date': str(y.end_date)}
                for y in years
            ],
            'semesters': [
                {'id': s.id, 'academic_year_id': s.academic_year_id, 'name': s.name, 'semester_number': s.semester_number, 'is_current': s.is_current}
                for s in semesters
            ],
            'period_types': [
                {'code': CompetitionPeriod.TYPE_WEEK, 'label': 'Thi đua theo Tuần'},
                {'code': CompetitionPeriod.TYPE_MONTH, 'label': 'Thi đua theo Tháng'},
                {'code': CompetitionPeriod.TYPE_SEMESTER, 'label': 'Thi đua theo Học kỳ'},
            ],
            'criterion': {
                'initial_base_points': float(criterion['initial_base_points']),
                'min_score': float(criterion['min_score']),
                'max_score': float(criterion['max_score']),
                'tie_breaker': criterion.get('tie_breaker', 'EQUAL_RANK')
            }
        })'''

new_filters_block = '''        res_data = {
            'academic_years': [
                {'id': y.id, 'name': y.name, 'is_current': y.is_current, 'start_date': str(y.start_date), 'end_date': str(y.end_date)}
                for y in years
            ],
            'semesters': [
                {'id': s.id, 'academic_year_id': s.academic_year_id, 'name': s.name, 'semester_number': s.semester_number, 'is_current': s.is_current}
                for s in semesters
            ],
            'period_types': [
                {'code': CompetitionPeriod.TYPE_WEEK, 'label': 'Thi đua theo Tuần'},
                {'code': CompetitionPeriod.TYPE_MONTH, 'label': 'Thi đua theo Tháng'},
                {'code': CompetitionPeriod.TYPE_SEMESTER, 'label': 'Thi đua theo Học kỳ'},
            ],
            'criterion': {
                'initial_base_points': float(criterion['initial_base_points']),
                'min_score': float(criterion['min_score']),
                'max_score': float(criterion['max_score']),
                'tie_breaker': criterion.get('tie_breaker', 'EQUAL_RANK')
            }
        }
        cache.set(cache_key, res_data, timeout=300)
        return Response(res_data)'''

if 'cache.set(cache_key, res_data, timeout=300)' not in text:
    assert old_filters_block in text, 'old_filters_block not found'
    text = text.replace(old_filters_block, new_filters_block, 1)

# 3. dashboard caching & memoized loop
old_dash_top = '''    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """Shared, role-scoped competition snapshot for all role dashboards."""
        user = request.user
        year_id = request.query_params.get('academic_year')
        year = AcademicYear.objects.filter(pk=year_id).first() if year_id else None
        year = year or AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.order_by('-start_date').first()
        if not year:
            return Response({'academic_year': None, 'periods': {}, 'classes': []})'''

new_dash_top = '''    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """Shared, role-scoped competition snapshot for all role dashboards."""
        user = request.user
        year_id = request.query_params.get('academic_year')
        year = AcademicYear.objects.filter(pk=year_id).first() if year_id else None
        year = year or AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.order_by('-start_date').first()
        if not year:
            return Response({'academic_year': None, 'periods': {}, 'classes': []})

        scope_key = user.id if user.role in (User.ROLE_GVCN, User.ROLE_GVBM, User.ROLE_STUDENT) else 'all'
        cache_key = f"comp_dash_v{get_cache_version()}_{year.id}_{user.role}_{scope_key}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)'''

if 'comp_dash_v' not in text:
    assert old_dash_top in text, 'old_dash_top not found'
    text = text.replace(old_dash_top, new_dash_top, 1)

old_dash_trend_and_return = '''        trend = {}
        for score in ClassCompetitionScore.objects.filter(
            competition_period__in=trend_periods,
            school_class_id__in=class_ids,
        ).select_related('competition_period', 'school_class'):
            if not may_view_unpublished and get_period_status(score.competition_period)['calendar_review']:
                continue
            trend.setdefault(score.school_class_id, []).append({
                'period_id': score.competition_period_id,
                'week_number': score.competition_period.week_number,
                'name': score.competition_period.name,
                'total_score': float(score.total_score),
                'rank': score.rank,
                'start_date': str(score.competition_period.start_date),
                'end_date': str(score.competition_period.end_date),
            })
        for row in result_classes:
            row['trend'] = trend.get(row['id'], [])

        return Response({
            'academic_year': {'id': year.id, 'name': year.name},
            'periods': current_periods,
            'classes': result_classes,
            'weekly_trend': weekly_averages,
        })'''

new_dash_trend_and_return = '''        trend = {}
        period_review_map = {
            p.id: get_period_status(p)['calendar_review']
            for p in trend_periods
        }
        for score in ClassCompetitionScore.objects.filter(
            competition_period__in=trend_periods,
            school_class_id__in=class_ids,
        ).select_related('competition_period'):
            if not may_view_unpublished and period_review_map.get(score.competition_period_id, False):
                continue
            trend.setdefault(score.school_class_id, []).append({
                'period_id': score.competition_period_id,
                'week_number': score.competition_period.week_number,
                'name': score.competition_period.name,
                'total_score': float(score.total_score),
                'rank': score.rank,
                'start_date': str(score.competition_period.start_date),
                'end_date': str(score.competition_period.end_date),
            })
        for row in result_classes:
            row['trend'] = trend.get(row['id'], [])

        res_data = {
            'academic_year': {'id': year.id, 'name': year.name},
            'periods': current_periods,
            'classes': result_classes,
            'weekly_trend': weekly_averages,
        }
        cache.set(cache_key, res_data, timeout=30)
        return Response(res_data)'''

if 'period_review_map' not in text:
    assert old_dash_trend_and_return in text, 'old_dash_trend_and_return not found'
    text = text.replace(old_dash_trend_and_return, new_dash_trend_and_return, 1)

# 4. scores caching
old_scores_top = '''        if not period.is_published and not (user.is_admin or user.is_bgh or user.is_doan_truong):
            return Response({'error': 'Kỳ thi đua chưa được công bố.'}, status=status.HTTP_404_NOT_FOUND)
        class_scope = get_competition_class_scope(user, period.academic_year)
        class_ids = None if (user.is_admin or user.is_bgh or user.is_doan_truong) else list(class_scope.values_list('id', flat=True))'''

new_scores_top = '''        if not period.is_published and not (user.is_admin or user.is_bgh or user.is_doan_truong):
            return Response({'error': 'Kỳ thi đua chưa được công bố.'}, status=status.HTTP_404_NOT_FOUND)

        grade = request.query_params.get('grade')
        search = request.query_params.get('search', '').strip()
        scope_key = user.id if user.role in (User.ROLE_GVCN, User.ROLE_GVBM, User.ROLE_STUDENT) else 'all'
        cache_key = f"comp_scores_v{get_cache_version()}_{period.id}_{user.role}_{scope_key}_{grade}_{search}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        class_scope = get_competition_class_scope(user, period.academic_year)
        class_ids = None if (user.is_admin or user.is_bgh or user.is_doan_truong) else list(class_scope.values_list('id', flat=True))'''

if 'comp_scores_v' not in text:
    assert old_scores_top in text, 'old_scores_top not found'
    text = text.replace(old_scores_top, new_scores_top, 1)

old_scores_return = '''        return Response({
            'period': self.get_serializer(period).data,
            'prev_period': {
                'id': previous_period.id,
                'name': previous_period.name,
                'start_date': str(previous_period.start_date),
                'end_date': str(previous_period.end_date)
            } if previous_period else None,
            'summary': {
                'total_classes': total_classes,
                'top_class': top_class,
                'highest_score': highest_score,
                'improved_classes_count': improved_classes,
                'worsened_classes_count': worsened_classes,
                'total_violations_in_period': total_violations,
                'last_updated': last_updated_time,
                'is_locked': period.is_locked,
                'locked_at': period.locked_at.strftime('%d/%m/%Y %H:%M') if period.locked_at else None,
                'locked_by': period.locked_by.full_name if period.locked_by else None
            },
            'period_status': state,
            'scores': serializer.data
        })'''

new_scores_return = '''        res_data = {
            'period': self.get_serializer(period).data,
            'prev_period': {
                'id': previous_period.id,
                'name': previous_period.name,
                'start_date': str(previous_period.start_date),
                'end_date': str(previous_period.end_date)
            } if previous_period else None,
            'summary': {
                'total_classes': total_classes,
                'top_class': top_class,
                'highest_score': highest_score,
                'improved_classes_count': improved_classes,
                'worsened_classes_count': worsened_classes,
                'total_violations_in_period': total_violations,
                'last_updated': last_updated_time,
                'is_locked': period.is_locked,
                'locked_at': period.locked_at.strftime('%d/%m/%Y %H:%M') if period.locked_at else None,
                'locked_by': period.locked_by.full_name if period.locked_by else None
            },
            'period_status': state,
            'scores': serializer.data
        }
        cache.set(cache_key, res_data, timeout=30)
        return Response(res_data)'''

if 'comp_scores_v' not in text or 'cache.set(cache_key, res_data, timeout=30)\n        return Response(res_data)' not in text:
    assert old_scores_return in text, 'old_scores_return not found'
    text = text.replace(old_scores_return, new_scores_return, 1)

with open('competition/views.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Successfully optimized competition/views.py!')
