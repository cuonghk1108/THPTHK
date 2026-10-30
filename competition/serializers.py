from rest_framework import serializers
from .models import ScoreCriterion, CompetitionPeriod, ClassCompetitionScore
from .services import get_period_status


class ScoreCriterionSerializer(serializers.ModelSerializer):
    tie_breaker_display = serializers.CharField(source='get_tie_breaker_display', read_only=True)

    class Meta:
        model = ScoreCriterion
        fields = '__all__'


class CompetitionPeriodSerializer(serializers.ModelSerializer):
    period_type_display = serializers.CharField(source='get_period_type_display', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    semester_name = serializers.CharField(source='semester.name', read_only=True, default='')
    semester_number = serializers.IntegerField(source='semester.semester_number', read_only=True, default=None)
    semester_week_number = serializers.IntegerField(read_only=True)
    display_week_label = serializers.CharField(read_only=True)
    locked_by_name = serializers.CharField(source='locked_by.full_name', read_only=True, default='')
    period_code = serializers.CharField(read_only=True)
    result_status = serializers.SerializerMethodField()
    calendar_progress = serializers.SerializerMethodField()
    calendar_requires_review = serializers.SerializerMethodField()

    class Meta:
        model = CompetitionPeriod
        fields = [
            'id', 'period_type', 'period_type_display', 'name', 'period_code',
            'week_number', 'month_number', 'internal_month_number', 'semester_number', 'semester_week_number',
            'display_week_label', 'academic_year', 'academic_year_name',
            'semester', 'semester_name', 'start_date', 'end_date',
            'is_locked', 'locked_at', 'locked_by_name', 'is_published', 'created_at',
            'result_status', 'calendar_progress', 'calendar_requires_review'
        ]
        read_only_fields = [
            'is_locked', 'locked_at', 'locked_by_name', 'created_at',
            'result_status', 'calendar_progress', 'calendar_requires_review',
        ]

    def validate(self, data):
        start_date = data.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = data.get('end_date', getattr(self.instance, 'end_date', None))
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({'end_date': 'Ngày kết thúc không được sớm hơn ngày bắt đầu.'})
        period_type = data.get('period_type', getattr(self.instance, 'period_type', None))
        internal_month = data.get('internal_month_number', getattr(self.instance, 'internal_month_number', None))
        if internal_month is not None and period_type not in [CompetitionPeriod.TYPE_WEEK, CompetitionPeriod.TYPE_MONTH]:
            raise serializers.ValidationError({'internal_month_number': 'Chỉ kỳ tuần hoặc kỳ tháng mới liên kết tháng thi đua nội bộ.'})
        if internal_month is not None and not 1 <= int(internal_month) <= 10:
            raise serializers.ValidationError({'internal_month_number': 'Tháng thi đua nội bộ phải nằm trong khoảng 1–10.'})
        if self.instance and self.instance.is_locked:
            protected = ['start_date', 'end_date', 'week_number', 'month_number', 'internal_month_number', 'semester', 'period_type']
            changed = [field for field in protected if field in data and data[field] != getattr(self.instance, field)]
            if changed:
                raise serializers.ValidationError('Kỳ đã chốt. Hãy mở khóa theo quy trình trước khi sửa lịch.')
        return data

    def get_result_status(self, obj):
        return get_period_status(obj)['code']

    def get_calendar_requires_review(self, obj):
        return get_period_status(obj)['requires_review']

    def get_calendar_progress(self, obj):
        state = get_period_status(obj)
        return {
            'display': state['display'],
            'expected_weeks': state['expected_weeks'],
            'configured_weeks': state['configured_weeks'],
            'included_weeks': state['included_weeks'],
            'complete_schedule': state['complete_schedule'],
            'complete_result': state['complete_result'],
            'requires_review': state['requires_review'],
        }


class ClassCompetitionScoreSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='school_class.name', read_only=True)
    grade = serializers.IntegerField(source='school_class.grade', read_only=True)
    homeroom_teacher_name = serializers.CharField(source='school_class.homeroom_teacher.full_name', read_only=True, default='')

    prev_rank = serializers.SerializerMethodField()
    prev_score = serializers.SerializerMethodField()
    score_change = serializers.SerializerMethodField()
    has_comparison = serializers.SerializerMethodField()

    class Meta:
        model = ClassCompetitionScore
        fields = [
            'id', 'competition_period', 'school_class', 'class_name', 'grade', 'homeroom_teacher_name',
            'base_points', 'bonus_points', 'penalty_points', 'total_score',
            'rank', 'rank_in_grade', 'rank_change', 'verified_violations_count',
            'prev_rank', 'prev_score', 'score_change', 'has_comparison',
            'bonus_notes', 'notes', 'updated_at'
        ]

    def get_prev_rank(self, obj):
        return getattr(obj, '_prev_rank', None)

    def get_prev_score(self, obj):
        val = getattr(obj, '_prev_score', None)
        return float(val) if val is not None else None

    def get_score_change(self, obj):
        val = getattr(obj, '_score_change', None)
        return float(val) if val is not None else None

    def get_has_comparison(self, obj):
        return getattr(obj, '_prev_rank', None) is not None
