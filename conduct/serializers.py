from rest_framework import serializers
from .models import SchoolClass, Student, Teacher, ConductRuleCategory, ConductRule, ViolationRecord, ViolationReviewHistory


class SchoolClassSerializer(serializers.ModelSerializer):
    homeroom_teacher_name = serializers.CharField(source='homeroom_teacher.full_name', read_only=True, default='')

    class Meta:
        model = SchoolClass
        fields = ['id', 'name', 'grade', 'academic_year', 'homeroom_teacher', 'homeroom_teacher_name',
                  'student_count', 'room_number', 'union_branch_name']


class StudentSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='school_class.name', read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'student_code', 'full_name', 'date_of_birth', 'gender', 'school_class',
                  'class_name', 'is_union_member', 'is_red_star', 'parent_phone', 'status']


class ConductRuleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ConductRuleCategory
        fields = '__all__'


class ConductRuleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)

    class Meta:
        model = ConductRule
        fields = ['id', 'code', 'name', 'category', 'category_name', 'default_points_deducted',
                  'severity', 'severity_display', 'description', 'is_active']


class ViolationReviewHistorySerializer(serializers.ModelSerializer):
    performer_name = serializers.CharField(source='performed_by.full_name', read_only=True, default='')

    class Meta:
        model = ViolationReviewHistory
        fields = ['id', 'performer_name', 'previous_status', 'new_status', 'points_applied', 'reason', 'created_at']


class ViolationRecordSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='school_class.name', read_only=True)
    student_name = serializers.SerializerMethodField()
    rule_code = serializers.CharField(source='rule.code', read_only=True)
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    rule_category = serializers.CharField(source='rule.category.name', read_only=True)
    reporter_name = serializers.CharField(source='reporter.full_name', read_only=True, default='')
    verifier_name = serializers.CharField(source='verified_by.full_name', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    evidence_image_url = serializers.SerializerMethodField()
    reviews = ViolationReviewHistorySerializer(many=True, read_only=True)

    class Meta:
        model = ViolationRecord
        fields = [
            'id', 'record_code', 'school_class', 'class_name', 'student', 'student_name',
            'rule', 'rule_code', 'rule_name', 'rule_category', 'occurred_at', 'location',
            'description', 'reporter', 'reporter_name', 'status', 'status_display',
            'points_deducted', 'evidence_image_url', 'evidence_notes',
            'verified_by', 'verifier_name', 'verified_at', 'verification_notes',
            'appeal_reason', 'appeal_submitted_at', 'created_at', 'reviews'
        ]
        read_only_fields = ['record_code', 'points_deducted', 'verified_by', 'verified_at', 'created_at']

    def get_student_name(self, obj):
        if obj.student:
            return obj.student.full_name
        return obj.student_name_snapshot or f"Tập thể {obj.school_class.name}"

    def get_evidence_image_url(self, obj):
        if obj.evidence_image:
            return obj.evidence_image.url
        return None
