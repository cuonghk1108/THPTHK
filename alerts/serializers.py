from rest_framework import serializers
from .models import EarlyWarningRule, EarlyWarningAlert, HomeroomIntervention


class EarlyWarningRuleSerializer(serializers.ModelSerializer):
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)

    class Meta:
        model = EarlyWarningRule
        fields = ['id', 'name', 'rule_type', 'rule_type_display', 'threshold', 'time_window_days',
                  'is_active', 'suggested_action']


class HomeroomInterventionSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True, default='')

    class Meta:
        model = HomeroomIntervention
        fields = ['id', 'alert', 'teacher', 'teacher_name', 'action_taken', 'outcome', 'status', 'created_at']


class EarlyWarningAlertSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='school_class.name', read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True, default='Tập thể')
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    interventions = HomeroomInterventionSerializer(many=True, read_only=True)

    class Meta:
        model = EarlyWarningAlert
        fields = [
            'id', 'rule', 'school_class', 'class_name', 'student', 'student_name',
            'alert_title', 'details', 'severity', 'severity_display',
            'status', 'status_display', 'homeroom_teacher', 'created_at', 'interventions'
        ]
