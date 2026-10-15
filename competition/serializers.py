from rest_framework import serializers
from .models import ScoreCriterion, CompetitionPeriod, ClassCompetitionScore


class ScoreCriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoreCriterion
        fields = '__all__'


class CompetitionPeriodSerializer(serializers.ModelSerializer):
    period_type_display = serializers.CharField(source='get_period_type_display', read_only=True)

    class Meta:
        model = CompetitionPeriod
        fields = ['id', 'period_type', 'period_type_display', 'name', 'week_number', 'month_number',
                  'academic_year', 'semester', 'start_date', 'end_date', 'is_locked', 'is_published']


class ClassCompetitionScoreSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='school_class.name', read_only=True)
    grade = serializers.IntegerField(source='school_class.grade', read_only=True)
    homeroom_teacher_name = serializers.CharField(source='school_class.homeroom_teacher.full_name', read_only=True, default='')

    class Meta:
        model = ClassCompetitionScore
        fields = [
            'id', 'competition_period', 'school_class', 'class_name', 'grade', 'homeroom_teacher_name',
            'base_points', 'bonus_points', 'penalty_points', 'total_score',
            'rank', 'rank_in_grade', 'rank_change', 'verified_violations_count',
            'bonus_notes', 'notes', 'updated_at'
        ]
