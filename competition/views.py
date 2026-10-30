from decimal import Decimal
from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from core.cache_utils import get_cache_version, invalidate_all_caches

from core.models import User, AcademicYear, Semester, AuditLog
from conduct.models import SchoolClass, ViolationRecord
from .models import ScoreCriterion, CompetitionPeriod, ClassCompetitionScore, ScoreAdjustment
from .serializers import ScoreCriterionSerializer, CompetitionPeriodSerializer, ClassCompetitionScoreSerializer
from .services import (
    get_current_score_criterion,
    recalculate_period_scores,
    lock_competition_period,
    unlock_competition_period,
    init_standard_35_weeks_schedule,
    get_current_competition_period,
    get_period_status,
    get_competition_class_scope,
    get_valid_aggregate_class_ids,
    _period_weeks,
)


class ScoreCriterionViewSet(viewsets.ModelViewSet):
    queryset = ScoreCriterion.objects.all().select_related('academic_year')
    serializer_class = ScoreCriterionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()


class CompetitionPeriodViewSet(viewsets.ModelViewSet):
    queryset = CompetitionPeriod.objects.all().select_related('academic_year', 'semester', 'locked_by')
    serializer_class = CompetitionPeriodSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def check_permissions(self, request):
        super().check_permissions(request)

    def get_queryset(self):
        qs = super().get_queryset()
        academic_year = self.request.query_params.get('academic_year')
        if academic_year:
            qs = qs.filter(academic_year_id=academic_year)

        period_type = self.request.query_params.get('period_type')
        if period_type:
            qs = qs.filter(period_type=period_type)
            if period_type == CompetitionPeriod.TYPE_MONTH and not (self.request.user.is_admin or self.request.user.is_bgh or self.request.user.is_doan_truong):
                qs = qs.filter(internal_month_number__isnull=False)

        semester = self.request.query_params.get('semester')
        if semester:
            qs = qs.filter(semester_id=semester)

        semester_number = self.request.query_params.get('semester_number')
        if semester_number:
            qs = qs.filter(semester__semester_number=semester_number)

        is_locked = self.request.query_params.get('is_locked')
        if is_locked is not None:
            if is_locked.lower() in ['true', '1']:
                qs = qs.filter(is_locked=True)
            elif is_locked.lower() in ['false', '0']:
                qs = qs.filter(is_locked=False)

        # Với kỳ tuần: sắp xếp theo tuần tăng dần (hoặc ngày bắt đầu)
        if period_type == CompetitionPeriod.TYPE_WEEK:
            qs = qs.order_by('week_number', 'start_date')
        elif period_type == CompetitionPeriod.TYPE_MONTH:
            qs = qs.order_by('internal_month_number', 'start_date')

        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_admin or user.is_bgh or user.is_doan_truong):
            raise permissions.PermissionDenied("Chỉ Quản trị viên, BGH hoặc Đoàn trường mới có quyền tạo kỳ thi đua.")
        
        period = serializer.save()
        # Tự động tính toán điểm khởi tạo ban đầu cho toàn bộ các lớp trong năm học
        recalculate_period_scores(period, force=True)

        AuditLog.objects.create(
            user=user,
            action='CREATE',
            resource_type='SCORE',
            resource_id=str(period.id),
            details=f"Tạo kỳ thi đua mới [{period.name}] ({period.get_period_type_display()}) từ {period.start_date} đến {period.end_date}"
        )

    def perform_update(self, serializer):
        user = self.request.user
        if not (user.is_admin or user.is_bgh or user.is_doan_truong):
            raise permissions.PermissionDenied("Bạn không có quyền chỉnh sửa kỳ thi đua.")
        
        period = serializer.save()
        if not period.is_locked:
            recalculate_period_scores(period)

        AuditLog.objects.create(
            user=user,
            action='UPDATE',
            resource_type='SCORE',
            resource_id=str(period.id),
            details=f"Cập nhật cấu hình kỳ thi đua [{period.name}]"
        )

    def perform_destroy(self, instance):
        user = self.request.user
        if not user.is_admin:
            raise permissions.PermissionDenied("Chỉ Quản trị viên hệ thống mới có quyền xóa kỳ thi đua.")
        if instance.is_locked:
            raise permissions.PermissionDenied("Kỳ thi đua đã chốt sổ chính thức, không thể xóa để bảo toàn lịch sử.")

        period_name = instance.name
        period_id = instance.id
        instance.delete()

        AuditLog.objects.create(
            user=user,
            action='DELETE',
            resource_type='SCORE',
            resource_id=str(period_id),
            details=f"Xóa kỳ thi đua [{period_name}]"
        )

    @action(detail=False, methods=['get'], url_path='filters-meta')
    def filters_meta(self, request):
        """Trả về dữ liệu danh mục phục vụ bộ lọc xếp hạng thi đua (Năm học, Học kỳ, Loại kỳ, Tiêu chí)"""
        cache_key = f"comp_filters_meta_v{get_cache_version()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        years = AcademicYear.objects.all().order_by('-start_date')
        semesters = Semester.objects.all().select_related('academic_year').order_by('academic_year', 'semester_number')
        
        current_year = years.filter(is_current=True).first() or years.first()
        criterion = get_current_score_criterion(current_year) if current_year else {
            'initial_base_points': Decimal('100.00'),
            'min_score': Decimal('0.00'),
            'max_score': Decimal('150.00'),
            'tie_breaker': 'EQUAL_RANK'
        }

        res_data = {
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
        return Response(res_data)

    @action(detail=False, methods=['get'], url_path='current')
    def current_period(self, request):
        """Lấy kỳ thi đua tuần hiện tại (hoặc kỳ đang diễn ra gần nhất)"""
        period_type = request.query_params.get('period_type', CompetitionPeriod.TYPE_WEEK)
        academic_year_id = request.query_params.get('academic_year')
        ay = AcademicYear.objects.filter(id=academic_year_id).first() if academic_year_id else AcademicYear.objects.filter(is_current=True).first()
        period = get_current_competition_period(ay, period_type=period_type)
        if not period:
            return Response({'error': 'Chưa có kỳ thi đua nào được thiết lập'}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(period).data)

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """Shared, role-scoped competition snapshot for all role dashboards."""
        user = request.user
        if user.is_student or getattr(user, 'role', '') == 'HOC_SINH':
            return Response({'academic_year': None, 'periods': {}, 'classes': []})
        if user.is_student or getattr(user, 'role', '') == 'HOC_SINH':
            return Response({'academic_year': None, 'periods': {}, 'classes': []})
        year_id = request.query_params.get('academic_year')
        year = AcademicYear.objects.filter(pk=year_id).first() if year_id else None
        year = year or AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.order_by('-start_date').first()
        if not year:
            return Response({'academic_year': None, 'periods': {}, 'classes': []})

        scope_key = user.id if user.role in (User.ROLE_GVCN, User.ROLE_GVBM, User.ROLE_HOC_SINH) else 'all'
        cache_key = f"comp_dash_v{get_cache_version()}_{year.id}_{user.role}_{scope_key}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        visible_classes = get_competition_class_scope(user, year)
        classes = list(visible_classes.filter(is_active=True).select_related('homeroom_teacher').order_by('grade', 'name'))
        class_ids = [school_class.id for school_class in classes]
        may_view_unpublished = user.is_admin or user.is_bgh or user.is_doan_truong
        current_periods = {}
        score_maps = {}

        for period_type in (CompetitionPeriod.TYPE_WEEK, CompetitionPeriod.TYPE_MONTH, CompetitionPeriod.TYPE_SEMESTER):
            period = get_current_competition_period(year, period_type)
            if period and (period.is_published or may_view_unpublished):
                state = get_period_status(period)
                current_periods[period_type] = {
                    'id': period.id,
                    'name': period.name,
                    'period_type': period.period_type,
                    'week_number': period.week_number,
                    'internal_month_number': period.internal_month_number,
                    'semester_number': period.semester.semester_number if period.semester_id else None,
                    'start_date': str(period.start_date),
                    'end_date': str(period.end_date),
                    'is_locked': period.is_locked,
                    'status': state['code'],
                    'status_display': state['display'],
                    'expected_weeks': state['expected_weeks'],
                    'included_weeks': state['included_weeks'],
                    'complete_schedule': state['complete_schedule'],
                    'complete_result': state['complete_result'],
                    'requires_review': state['requires_review'],
                }
                if state['code'] == 'NOT_STARTED':
                    score_maps[period_type] = {}
                    continue
                if state['calendar_review'] and not may_view_unpublished:
                    score_maps[period_type] = {}
                    continue
                valid_ids = get_valid_aggregate_class_ids(period)
                score_query = ClassCompetitionScore.objects.filter(
                    competition_period=period,
                    school_class_id__in=class_ids,
                ).select_related('school_class')
                if valid_ids is not None:
                    score_query = score_query.filter(school_class_id__in=valid_ids)
                score_maps[period_type] = {
                    score.school_class_id: {
                        'total_score': float(score.total_score),
                        'rank': score.rank,
                        'rank_in_grade': score.rank_in_grade,
                        'verified_violations_count': score.verified_violations_count,
                        'base_points': float(score.base_points),
                        'bonus_points': float(score.bonus_points),
                        'penalty_points': float(score.penalty_points),
                    }
                    for score in score_query
                }
            else:
                current_periods[period_type] = None
                score_maps[period_type] = {}

        result_classes = []
        for school_class in classes:
            result_classes.append({
                'id': school_class.id,
                'name': school_class.name,
                'grade': school_class.grade,
                'week': score_maps.get(CompetitionPeriod.TYPE_WEEK, {}).get(school_class.id),
                'month': score_maps.get(CompetitionPeriod.TYPE_MONTH, {}).get(school_class.id),
                'semester': score_maps.get(CompetitionPeriod.TYPE_SEMESTER, {}).get(school_class.id),
            })

        current_week_period = current_periods.get(CompetitionPeriod.TYPE_WEEK)
        current_end_date = current_week_period['end_date'] if current_week_period else None

        trend_periods_query = CompetitionPeriod.objects.filter(
            academic_year=year,
            period_type=CompetitionPeriod.TYPE_WEEK,
        )
        if current_end_date:
            trend_periods_query = trend_periods_query.filter(start_date__lte=current_end_date)
        if not may_view_unpublished:
            trend_periods_query = trend_periods_query.filter(is_published=True)
        trend_periods = list(trend_periods_query.order_by('start_date'))

        weekly_averages = []
        if trend_periods:
            from django.db.models import Avg
            avg_map = {
                item['competition_period']: round(float(item['avg_score'] or 100.0), 2)
                for item in ClassCompetitionScore.objects.filter(
                    competition_period__in=trend_periods
                ).values('competition_period').annotate(avg_score=Avg('total_score'))
            }
            for p in trend_periods:
                weekly_averages.append({
                    'period_id': p.id,
                    'week_number': p.week_number,
                    'name': p.name,
                    'average_score': avg_map.get(p.id, 100.0),
                    'is_locked': p.is_locked,
                })

        trend = {}
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
        return Response(res_data)

    @action(detail=False, methods=['post'], url_path='init-standard-schedule')
    def init_standard_schedule(self, request):
        """Khởi tạo / Chuẩn hóa 35 tuần học (18 tuần HK I + 17 tuần HK II) cho nhà trường"""
        user = request.user
        if not (user.is_admin or user.is_bgh or user.is_doan_truong):
            return Response({'error': 'Bạn không có quyền khởi tạo lịch trình năm học'}, status=status.HTTP_403_FORBIDDEN)

        force = request.data.get('force') in (True, 1, '1', 'true', 'True')
        academic_year_id = request.data.get('academic_year')
        ay = AcademicYear.objects.filter(id=academic_year_id).first() if academic_year_id else None
        
        result = init_standard_35_weeks_schedule(academic_year=ay, force_recalculate=force)

        AuditLog.objects.create(
            user=user,
            action='UPDATE',
            resource_type='SCORE',
            resource_id=str(ay.id if ay else 0),
            details=(
                f"Khởi tạo / Chuẩn hóa khung thời gian 35 tuần (18 tuần HK I, 17 tuần HK II) "
                f"bởi {user.full_name or user.username}. Vấn đề lịch: "
                f"{' | '.join(result['configuration_issues']) or 'Không phát hiện'}"
            )
        )
        return Response({
            'message': f"Đã chuẩn hóa thành công {result['total_weeks']} tuần học ({result['hk1_weeks']} tuần HK I, {result['hk2_weeks']} tuần HK II).",
            'data': result
        })

    @action(detail=True, methods=['get'], url_path='scores')
    def scores(self, request, pk=None):
        """
        Lấy bảng xếp hạng thi đua của kỳ với đầy đủ so sánh kỳ trước và thống kê tổng quan (KPI).
        Hỗ trợ lọc theo khối (grade) và tìm kiếm lớp (search).
        """
        period = self.get_object()
        user = request.user

        if not period.is_published and not (user.is_admin or user.is_bgh or user.is_doan_truong):
            return Response({'error': 'Kỳ thi đua chưa được công bố.'}, status=status.HTTP_404_NOT_FOUND)

        grade = request.query_params.get('grade')
        search = request.query_params.get('search', '').strip()
        scope_key = user.id if user.role in (User.ROLE_GVCN, User.ROLE_GVBM, User.ROLE_HOC_SINH) else 'all'
        cache_key = f"comp_scores_v{get_cache_version()}_{period.id}_{user.role}_{scope_key}_{grade}_{search}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        class_scope = get_competition_class_scope(user, period.academic_year)
        class_ids = None if (user.is_admin or user.is_bgh or user.is_doan_truong) else list(class_scope.values_list('id', flat=True))
        state = get_period_status(period)
        if state['code'] == 'NOT_STARTED':
            return Response({
                'period': self.get_serializer(period).data,
                'period_status': state,
                'summary': {'total_classes': 0, 'top_class': None, 'highest_score': None,
                            'improved_classes_count': 0, 'worsened_classes_count': 0,
                            'total_violations_in_period': 0, 'last_updated': None,
                            'is_locked': period.is_locked, 'locked_at': None, 'locked_by': None},
                'scores': [],
            })

        # Lấy kỳ trước đó tương ứng (để lấy điểm và thứ hạng so sánh)
        may_view_unpublished = user.is_admin or user.is_bgh or user.is_doan_truong
        previous_periods = CompetitionPeriod.objects.filter(
            academic_year=period.academic_year,
            period_type=period.period_type,
            is_locked=True,
            start_date__lt=period.start_date
        ).exclude(pk=period.pk)
        if not may_view_unpublished:
            previous_periods = previous_periods.filter(is_published=True)
        if period.period_type == CompetitionPeriod.TYPE_MONTH:
            previous_periods = previous_periods.filter(internal_month_number__isnull=False)
        previous_period = previous_periods.order_by('-start_date').first()

        prev_scores_map = {}
        if previous_period:
            previous_scores = ClassCompetitionScore.objects.filter(competition_period=previous_period)
            previous_valid_ids = get_valid_aggregate_class_ids(previous_period)
            if previous_valid_ids is not None:
                previous_scores = previous_scores.filter(school_class_id__in=previous_valid_ids)
            if class_ids is not None:
                previous_scores = previous_scores.filter(school_class_id__in=class_ids)
            for ps in previous_scores:
                prev_scores_map[ps.school_class_id] = {
                    'rank': ps.rank,
                    'total_score': ps.total_score
                }

        # Query scores của kỳ hiện tại
        scores_qs = ClassCompetitionScore.objects.filter(
            competition_period=period
        ).select_related('school_class', 'school_class__homeroom_teacher').order_by('rank', 'school_class__grade', 'school_class__class_order', 'school_class__name')
        if state['calendar_review'] and not may_view_unpublished:
            scores_qs = scores_qs.none()
        if class_ids is not None:
            scores_qs = scores_qs.filter(school_class_id__in=class_ids)
        valid_class_ids = get_valid_aggregate_class_ids(period)
        if valid_class_ids is not None:
            scores_qs = scores_qs.filter(school_class_id__in=valid_class_ids)

        # Thống kê tổng quan (KPI) trước khi lọc khối / search
        all_scores = list(scores_qs)
        total_classes = len(all_scores)
        top_class = None
        highest_score = None
        improved_classes = 0
        worsened_classes = 0
        total_violations = 0

        for s in all_scores:
            prev_info = prev_scores_map.get(s.school_class_id)
            if prev_info:
                s._prev_rank = prev_info['rank']
                s._prev_score = prev_info['total_score']
                s._score_change = s.total_score - prev_info['total_score']
            else:
                s._prev_rank = None
                s._prev_score = None
                s._score_change = None

            total_violations += s.verified_violations_count

            if s.rank_change is not None:
                if s.rank_change > 0:
                    improved_classes += 1
                elif s.rank_change < 0:
                    worsened_classes += 1

        if all_scores:
            top_class = {
                'class_name': all_scores[0].school_class.name,
                'total_score': float(all_scores[0].total_score),
                'rank': all_scores[0].rank
            }
            highest_score = float(all_scores[0].total_score)

        # Áp dụng bộ lọc khối và tìm kiếm hiển thị
        grade = request.query_params.get('grade')
        search = request.query_params.get('search', '').strip()

        filtered_scores = all_scores
        if grade:
            filtered_scores = [s for s in filtered_scores if str(s.school_class.grade) == str(grade)]
        if search:
            search_lower = search.lower()
            filtered_scores = [
                s for s in filtered_scores
                if search_lower in s.school_class.name.lower() or
                   (s.school_class.homeroom_teacher and search_lower in s.school_class.homeroom_teacher.full_name.lower())
            ]

        serializer = ClassCompetitionScoreSerializer(filtered_scores, many=True)

        visible_score_ids = [score.id for score in all_scores]
        last_updated_score = ClassCompetitionScore.objects.filter(
            id__in=visible_score_ids
        ).order_by('-updated_at').first()
        last_updated_time = last_updated_score.updated_at.strftime('%d/%m/%Y %H:%M') if last_updated_score else timezone.now().strftime('%d/%m/%Y %H:%M')

        res_data = {
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
        return Response(res_data)

    @action(detail=True, methods=['get'], url_path=r'classes/(?P<class_id>\d+)/detail')
    def class_detail(self, request, pk=None, class_id=None):
        """
        Chi tiết thi đua của một lớp trong kỳ: danh sách vi phạm, điểm cộng,
        tổng kết và lịch sử thứ hạng qua các kỳ.
        Tuân thủ RBAC: Học sinh chỉ được xem chi tiết lớp của mình.
        """
        period = self.get_object()
        user = request.user
        if not period.is_published and not (user.is_admin or user.is_bgh or user.is_doan_truong):
            return Response({'error': 'Kỳ thi đua chưa được công bố.'}, status=status.HTTP_404_NOT_FOUND)

        # Kiểm tra lớp học
        school_class = SchoolClass.objects.filter(id=class_id).first()
        if not school_class:
            return Response({'error': 'Không tìm thấy lớp học yêu cầu'}, status=status.HTTP_404_NOT_FOUND)

        class_scope = get_competition_class_scope(user, period.academic_year)
        if not (user.is_admin or user.is_bgh or user.is_doan_truong) and not class_scope.filter(pk=school_class.pk).exists():
            return Response({'error': 'Bạn không có quyền xem dữ liệu của lớp này.'}, status=status.HTTP_403_FORBIDDEN)
        state = get_period_status(period)

        # Bản ghi điểm của lớp trong kỳ
        valid_class_ids = get_valid_aggregate_class_ids(period)
        score_query = ClassCompetitionScore.objects.filter(competition_period=period, school_class=school_class)
        if valid_class_ids is not None:
            score_query = score_query.filter(school_class_id__in=valid_class_ids)
        score_obj = None if state['code'] == 'NOT_STARTED' or (
            state['calendar_review'] and not (user.is_admin or user.is_bgh or user.is_doan_truong)
        ) else score_query.first()

        # Danh sách các vi phạm nền nếp trong kỳ
        violations = ViolationRecord.objects.filter(
            school_class=school_class,
            occurred_at__date__gte=period.start_date,
            occurred_at__date__lte=period.end_date,
            status__in=[ViolationRecord.STATUS_VERIFIED, ViolationRecord.STATUS_ADJUSTED]
        )
        score_week_ids = [period.id] if period.period_type == CompetitionPeriod.TYPE_WEEK else []
        if period.period_type != CompetitionPeriod.TYPE_WEEK:
            locked_weeks = list(_period_weeks(period).filter(is_locked=True).values_list('id', 'start_date', 'end_date'))
            score_week_ids = [week_id for week_id, _, _ in locked_weeks]
            period_date_filter = Q(pk__in=[])
            for _, start_date, end_date in locked_weeks:
                period_date_filter |= Q(occurred_at__date__gte=start_date, occurred_at__date__lte=end_date)
            violations = violations.filter(period_date_filter)
        violations = violations.select_related('student', 'rule', 'reporter').order_by('-occurred_at')

        violation_events = [
            {
                'id': v.id,
                'event_type': 'VIOLATION',
                'record_code': v.record_code,
                'time': timezone.localtime(v.occurred_at).strftime('%d/%m/%Y %H:%M') if v.occurred_at else '',
                'student_name': v.student.full_name if v.student else (v.student_name_snapshot or 'Tập thể lớp'),
                'rule_code': v.rule.code if v.rule else 'VP',
                'rule_name': v.rule.name if v.rule else (v.description or 'Vi phạm nền nếp'),
                'points_deducted': float(v.points_deducted),
                'reporter_name': v.reporter.full_name or v.reporter.username if v.reporter else 'Hệ thống',
                'status': v.get_status_display(),
                'location': v.location or ''
            }
            for v in violations
        ]
        adjustment_events = [
            {
                'id': adjustment.id,
                'event_type': 'SCORE_ADJUSTMENT',
                'record_code': f'ADJ-{adjustment.id}',
                'time': timezone.localtime(adjustment.approved_at or adjustment.created_at).strftime('%d/%m/%Y %H:%M'),
                'amount': float(adjustment.amount),
                'reason': adjustment.reason,
                'created_by_name': (adjustment.created_by.full_name or adjustment.created_by.username) if adjustment.created_by else 'Hệ thống',
                'approved_by_name': (adjustment.approved_by.full_name or adjustment.approved_by.username) if adjustment.approved_by else 'Chưa ghi nhận',
                'status': adjustment.get_status_display(),
            }
            for adjustment in ScoreAdjustment.objects.filter(
                school_class=school_class,
                competition_period_id__in=score_week_ids,
                status=ScoreAdjustment.STATUS_APPROVED,
            ).select_related('created_by', 'approved_by').order_by('created_at')
        ]
        violation_events.extend(adjustment_events)

        # Lịch sử biến động thứ hạng qua các kỳ trong năm học (cho biểu đồ / bảng tiến trình)
        history_scores = ClassCompetitionScore.objects.filter(
            school_class=school_class,
            competition_period__academic_year=period.academic_year,
            competition_period__period_type=period.period_type,
            competition_period__start_date__lte=timezone.localdate(),
        )
        if not (user.is_admin or user.is_bgh or user.is_doan_truong):
            history_scores = history_scores.filter(competition_period__is_published=True)
        if period.period_type == CompetitionPeriod.TYPE_MONTH:
            history_scores = history_scores.filter(competition_period__internal_month_number__isnull=False)
        history_scores = history_scores.select_related('competition_period').order_by('competition_period__start_date')

        history_list = []
        for hs in history_scores:
            if not (user.is_admin or user.is_bgh or user.is_doan_truong) and get_period_status(hs.competition_period)['calendar_review']:
                continue
            if hs.competition_period.period_type != CompetitionPeriod.TYPE_WEEK:
                valid_ids = get_valid_aggregate_class_ids(hs.competition_period)
                if valid_ids is not None and school_class.id not in valid_ids:
                    continue
            history_list.append({
                'period_id': hs.competition_period_id,
                'period_name': hs.competition_period.name,
                'period_code': hs.competition_period.period_code,
                'start_date': str(hs.competition_period.start_date),
                'end_date': str(hs.competition_period.end_date),
                'total_score': float(hs.total_score),
                'rank': hs.rank,
                'rank_in_grade': hs.rank_in_grade,
                'rank_change': hs.rank_change,
                'is_locked': hs.competition_period.is_locked,
                'is_current': hs.competition_period_id == period.id
            })

        return Response({
            'school_class': {
                'id': school_class.id,
                'name': school_class.name,
                'grade': school_class.grade,
                'homeroom_teacher': school_class.homeroom_teacher.full_name if school_class.homeroom_teacher else 'Chưa phân công',
                'room_number': school_class.room_number or ''
            },
            'period': {
                'id': period.id,
                'name': period.name,
                'period_type': period.period_type,
                'period_type_display': period.get_period_type_display(),
                'start_date': str(period.start_date),
                'end_date': str(period.end_date),
                'is_locked': period.is_locked,
                'status': state['code'],
                'status_display': state['display']
            },
            'score': {
                'base_points': float(score_obj.base_points) if score_obj else None,
                'bonus_points': float(score_obj.bonus_points) if score_obj else 0.0,
                'penalty_points': float(score_obj.penalty_points) if score_obj else 0.0,
                'total_score': float(score_obj.total_score) if score_obj else None,
                'rank': score_obj.rank if score_obj else None,
                'rank_in_grade': score_obj.rank_in_grade if score_obj else None,
                'rank_change': score_obj.rank_change if score_obj else None,
                'verified_violations_count': score_obj.verified_violations_count if score_obj else 0,
                'bonus_notes': score_obj.bonus_notes if score_obj else ''
            },
            'events': violation_events,
            'history': history_list
        })

    @action(detail=True, methods=['post'], url_path='recalculate')
    def recalculate(self, request, pk=None):
        """Tính toán lại điểm thi đua tự động từ các bản ghi đã xác minh"""
        user = request.user
        if not (user.is_admin or user.is_bgh or user.is_doan_truong):
            return Response({'error': 'Bạn không có quyền tính lại điểm thi đua'}, status=status.HTTP_403_FORBIDDEN)

        period = self.get_object()
        force = request.data.get('force') in (True, 1, '1', 'true', 'True')
        if period.is_locked and not force:
            return Response({
                'error': 'Kỳ thi đua đã chốt sổ. Nếu cần tính lại do bổ sung vi phạm muộn, vui lòng mở lại kỳ hoặc xác nhận tính lại cưỡng bức.'
            }, status=status.HTTP_400_BAD_REQUEST)

        recalculate_period_scores(period, force=force)

        AuditLog.objects.create(
            user=user,
            action='UPDATE',
            resource_type='SCORE',
            resource_id=str(period.id),
            details=f"Tính toán lại bảng xếp hạng thi đua kỳ [{period.name}]"
        )
        return Response({'message': f'Đã cập nhật lại bảng xếp hạng thi đua kỳ [{period.name}] thành công'})

    @action(detail=True, methods=['post'], url_path='lock')
    def lock(self, request, pk=None):
        """Chốt sổ kỳ thi đua"""
        user = request.user
        if not (user.is_admin or user.is_bgh or user.is_doan_truong):
            return Response({'error': 'Bạn không có quyền chốt sổ thi đua'}, status=status.HTTP_403_FORBIDDEN)

        try:
            period = lock_competition_period(pk, user)
        except ValueError as error:
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': f'Đã chốt sổ kỳ thi đua [{period.name}] thành công'})

    @action(detail=True, methods=['post'], url_path='unlock')
    def unlock(self, request, pk=None):
        """Mở khóa kỳ thi đua (BGH, Admin hoặc Đoàn trường)"""
        user = request.user
        if not (user.is_admin or user.is_bgh or user.is_doan_truong):
            return Response({'error': 'Chỉ Ban Giám hiệu, Quản trị viên hoặc Đoàn trường mới có quyền mở lại kỳ thi đua đã chốt'}, status=status.HTTP_403_FORBIDDEN)

        period = unlock_competition_period(pk, user)
        return Response({'message': f'Đã mở lại kỳ thi đua [{period.name}] để cập nhật dữ liệu'})


class ClassCompetitionScoreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ClassCompetitionScore.objects.all().select_related('competition_period', 'school_class')
    serializer_class = ClassCompetitionScoreSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if request.user.is_student or getattr(request.user, 'role', '') == 'HOC_SINH':
            self.permission_denied(request, message='Học sinh không có quyền truy cập bảng xếp hạng thi đua Chi đoàn.')
        if request.user.is_student or getattr(request.user, 'role', '') == 'HOC_SINH':
            self.permission_denied(request, message='Học sinh không có quyền truy cập bảng xếp hạng thi đua Chi đoàn.')

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_admin or user.is_bgh or user.is_doan_truong:
            return queryset
        scope = get_competition_class_scope(user)
        queryset = queryset.filter(
            school_class__in=scope,
            competition_period__is_published=True,
        )
        review_period_ids = [
            period.id for period in CompetitionPeriod.objects.filter(is_published=True).select_related(
                'academic_year', 'semester'
            ) if get_period_status(period)['calendar_review']
        ]
        return queryset.exclude(competition_period_id__in=review_period_ids)

    @action(detail=True, methods=['post'], url_path='add-bonus')
    def add_bonus(self, request, pk=None):
        """Quản trị viên cộng điểm phong trào cho Chi đoàn"""
        user = request.user
        if not (user.is_admin or user.is_doan_truong):
            return Response({'error': 'Chỉ Quản trị viên hoặc Đoàn trường mới có quyền cộng điểm phong trào'}, status=status.HTTP_403_FORBIDDEN)

        score_obj = self.get_object()
        if score_obj.competition_period.period_type != CompetitionPeriod.TYPE_WEEK:
            return Response({'error': 'Điểm điều chỉnh phải gắn với tuần; điểm tháng và học kỳ được tổng hợp từ các tuần đã chốt.'}, status=status.HTTP_400_BAD_REQUEST)
        if score_obj.competition_period.is_locked:
            return Response({'error': 'Kỳ thi đua đã bị khóa'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            bonus = Decimal(str(request.data.get('bonus_points', '0')))
        except Exception:
            return Response({'error': 'Điểm cộng không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        note = str(request.data.get('note', '')).strip()
        key = request.data.get('idempotency_key') or request.headers.get('Idempotency-Key')
        if bonus <= 0 or not note:
            return Response({'error': 'Cần điểm cộng lớn hơn 0 và lý do điều chỉnh.'}, status=status.HTTP_400_BAD_REQUEST)
        if not key:
            return Response({'error': 'Thiếu mã chống ghi trùng; hãy tải lại biểu mẫu rồi thử lại.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            adjustment, created = ScoreAdjustment.objects.get_or_create(
                idempotency_key=key,
                defaults={
                    'competition_period': score_obj.competition_period,
                    'school_class': score_obj.school_class,
                    'amount': bonus,
                    'reason': note,
                    'status': ScoreAdjustment.STATUS_APPROVED,
                    'created_by': user,
                    'approved_by': user,
                    'approved_at': timezone.now(),
                },
            )
        except Exception as exc:
            return Response({'error': f'Mã chống ghi trùng không hợp lệ: {exc}'}, status=status.HTTP_400_BAD_REQUEST)
        if not created and (
            adjustment.competition_period_id != score_obj.competition_period_id
            or adjustment.school_class_id != score_obj.school_class_id
            or adjustment.amount != bonus
            or adjustment.reason != note
        ):
            return Response({'error': 'Mã chống ghi trùng đã được dùng cho một khoản điểm khác.'}, status=status.HTTP_409_CONFLICT)

        if created:
            now_str = timezone.localtime().strftime('%d/%m/%Y %H:%M')
            score_obj.bonus_notes = f"{score_obj.bonus_notes}\n[{now_str}] +{bonus}đ: {note}".strip()
            score_obj.save(update_fields=['bonus_notes'])

        recalculate_period_scores(score_obj.competition_period)
        score_obj.refresh_from_db()

        AuditLog.objects.create(
            user=user,
            action='UPDATE',
            resource_type='SCORE',
            resource_id=str(score_obj.id),
            details=f"Cộng +{bonus}đ cho lớp {score_obj.school_class.name} trong kỳ [{score_obj.competition_period.name}]. Lý do: {note}. Adjustment ID: {adjustment.id}"
        )

        serializer = self.get_serializer(score_obj)
        return Response({'message': 'Đã cộng điểm phong trào thành công', 'score': serializer.data})
