from rest_framework import serializers

from .models import (

    SchoolClass, Student, Teacher, ConductRuleCategory, ConductRule,

    ViolationRecord, ViolationReviewHistory,

    ViolationEmailNotification,

    TeacherClassAssignment, HomeroomAssignment,

    TeacherReflection, ReflectionHistory,

    RedStarAssignment, RedStarReport,

    StudentFeedback, StudentFeedbackReply,

)





class SchoolClassSerializer(serializers.ModelSerializer):
    homeroom_teacher_name = serializers.CharField(source='homeroom_teacher.full_name', read_only=True, default='')
    monitor_name = serializers.CharField(source='monitor.full_name', read_only=True, default='')

    class Meta:
        model = SchoolClass
        fields = ['id', 'name', 'grade', 'academic_year', 'homeroom_teacher', 'homeroom_teacher_name',
                  'student_count', 'room_number', 'union_branch_name', 'monitor', 'monitor_name']


class StudentSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='school_class.name', read_only=True)
    class_id = serializers.IntegerField(source='school_class_id', read_only=True)
    class_id = serializers.IntegerField(source='school_class_id', read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'student_code', 'full_name', 'date_of_birth', 'gender', 'school_class',
                  'class_name', 'is_union_member', 'is_red_star', 'is_class_monitor', 'status']


class ConductRuleCategorySerializer(serializers.ModelSerializer):

    rules_count = serializers.SerializerMethodField()



    class Meta:

        model = ConductRuleCategory

        fields = ['id', 'name', 'description', 'icon', 'order', 'rules_count']



    def get_rules_count(self, obj):

        return obj.rules.filter(is_active=True).count()





class ConductRuleSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(source='category.name', read_only=True)

    category_order = serializers.IntegerField(source='category.order', read_only=True)

    category_icon = serializers.CharField(source='category.icon', read_only=True)

    severity_display = serializers.CharField(source='get_severity_display', read_only=True)



    class Meta:

        model = ConductRule

        fields = ['id', 'code', 'name', 'category', 'category_name', 'category_order', 'category_icon',

                  'default_points_deducted', 'severity', 'severity_display', 'description', 'is_active']





class ViolationReviewHistorySerializer(serializers.ModelSerializer):

    performer_name = serializers.CharField(source='performed_by.full_name', read_only=True, default='')



    class Meta:

        model = ViolationReviewHistory

        fields = ['id', 'performer_name', 'previous_status', 'new_status', 'points_applied',

                  'score_before', 'score_after', 'reason', 'created_at']





class ViolationRecordSerializer(serializers.ModelSerializer):

    class_name = serializers.CharField(source='school_class.name', read_only=True)

    class_id = serializers.IntegerField(source='school_class_id', read_only=True)

    student_name = serializers.SerializerMethodField()

    rule_code = serializers.CharField(source='rule.code', read_only=True)

    rule_name = serializers.CharField(source='rule.name', read_only=True)

    rule_category = serializers.CharField(source='rule.category.name', read_only=True)

    reporter_name = serializers.CharField(source='reporter.full_name', read_only=True, default='')

    reporter_username = serializers.CharField(source='reporter.username', read_only=True, default='')

    reporter_role = serializers.CharField(source='reporter.get_role_display', read_only=True, default='')

    verifier_name = serializers.CharField(source='verified_by.full_name', read_only=True, default='')

    status_display = serializers.CharField(source='get_status_display', read_only=True)

    evidence_image_url = serializers.SerializerMethodField()

    email_status = serializers.SerializerMethodField()

    reviews = ViolationReviewHistorySerializer(many=True, read_only=True)



    class Meta:

        model = ViolationRecord

        fields = [

            'id', 'record_code', 'school_class', 'class_name', 'class_id', 'student', 'student_name',

            'rule', 'rule_code', 'rule_name', 'rule_category', 'occurred_at', 'location',

            'description', 'reporter', 'reporter_name', 'reporter_username', 'reporter_role',

            'status', 'status_display', 'points_deducted', 'score_before', 'score_after',

            'evidence_image_url', 'evidence_notes',

            'verified_by', 'verifier_name', 'verified_at', 'verification_notes',

            'appeal_reason', 'appeal_submitted_at', 'created_at', 'reviews',

            'email_status',

        ]

        read_only_fields = ['record_code', 'points_deducted', 'score_before', 'score_after', 'verified_by', 'verified_at', 'created_at']



    def get_student_name(self, obj):

        if obj.student:

            return obj.student.full_name

        return obj.student_name_snapshot or f"Tập thể {obj.school_class.name}"



    def get_evidence_image_url(self, obj):

        if obj.evidence_image:

            return obj.evidence_image.url

        return None



    def get_email_status(self, obj):

        notifications = list(obj.email_notifications.all())

        if not notifications:

            return None



        statuses = {notif.status for notif in notifications}

        if ViolationEmailNotification.STATUS_FAILED in statuses:

            status = ViolationEmailNotification.STATUS_FAILED

        elif ViolationEmailNotification.STATUS_SENDING in statuses:

            status = ViolationEmailNotification.STATUS_SENDING

        elif ViolationEmailNotification.STATUS_PENDING in statuses:

            status = ViolationEmailNotification.STATUS_PENDING

        elif ViolationEmailNotification.STATUS_SENT in statuses:

            status = ViolationEmailNotification.STATUS_SENT

        elif statuses == {ViolationEmailNotification.STATUS_SKIPPED}:

            status = ViolationEmailNotification.STATUS_SKIPPED

        else:

            status = 'UNKNOWN'



        messages = {

            ViolationEmailNotification.STATUS_PENDING: 'Email thông báo Đoàn trường đang chờ gửi.',

            ViolationEmailNotification.STATUS_SENDING: 'Đang gửi email thông báo Đoàn trường.',

            ViolationEmailNotification.STATUS_SENT: 'Máy chủ SMTP đã tiếp nhận email; không xác nhận thư đã vào hộp thư người nhận.',

            ViolationEmailNotification.STATUS_FAILED: 'Gửi email cho Đoàn trường thất bại; Quản trị viên có thể gửi lại.',

            ViolationEmailNotification.STATUS_SKIPPED: notifications[0].last_error or 'Chưa cấu hình email nhận của Đoàn trường.',

        }

        return {

            'status': status,

            'message': messages.get(status, 'Chưa có trạng thái Email.'),

        }





class ViolationEmailNotificationSerializer(serializers.ModelSerializer):

    violation_code = serializers.CharField(source='violation.record_code', read_only=True, default='')

    class_name = serializers.CharField(source='violation.school_class.name', read_only=True, default='')

    student_name = serializers.CharField(source='violation.student_name_snapshot', read_only=True, default='')

    status_display = serializers.CharField(source='get_status_display', read_only=True)



    class Meta:

        model = ViolationEmailNotification

        fields = [

            'id', 'violation', 'violation_code', 'class_name', 'student_name',

            'recipient_email', 'is_test', 'status', 'status_display', 'subject', 'body_text',

            'attempt_count', 'max_retries', 'next_attempt_at', 'last_error', 'last_attempt_at',

            'sent_at', 'created_at', 'updated_at',

        ]





class TeacherClassAssignmentSerializer(serializers.ModelSerializer):

    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)

    teacher_email = serializers.CharField(source='teacher.email', read_only=True)

    teacher_phone = serializers.CharField(source='teacher.phone', read_only=True)

    class_name = serializers.CharField(source='school_class.name', read_only=True)

    class_grade = serializers.IntegerField(source='school_class.grade', read_only=True)

    assigned_by_name = serializers.CharField(source='assigned_by.full_name', read_only=True, default='')



    class Meta:

        model = TeacherClassAssignment

        fields = [

            'id', 'teacher', 'teacher_name', 'teacher_email', 'teacher_phone',

            'school_class', 'class_name', 'class_grade', 'subject',

            'assigned_by', 'assigned_by_name', 'start_date', 'end_date', 'is_active', 'created_at'

        ]





class HomeroomAssignmentSerializer(serializers.ModelSerializer):

    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)

    teacher_email = serializers.CharField(source='teacher.email', read_only=True)

    teacher_phone = serializers.CharField(source='teacher.phone', read_only=True)

    class_name = serializers.CharField(source='school_class.name', read_only=True)

    class_grade = serializers.IntegerField(source='school_class.grade', read_only=True)

    assigned_by_name = serializers.CharField(source='assigned_by.full_name', read_only=True, default='')



    class Meta:

        model = HomeroomAssignment

        fields = [

            'id', 'teacher', 'teacher_name', 'teacher_email', 'teacher_phone',

            'school_class', 'class_name', 'class_grade',

            'assigned_by', 'assigned_by_name', 'start_date', 'end_date', 'is_active', 'notes', 'created_at'

        ]





class ReflectionHistorySerializer(serializers.ModelSerializer):

    performer_name = serializers.CharField(source='performed_by.full_name', read_only=True, default='')



    class Meta:

        model = ReflectionHistory

        fields = [

            'id', 'action', 'performed_by', 'performer_name',

            'previous_status', 'new_status', 'notes', 'created_at'

        ]





class TeacherReflectionSerializer(serializers.ModelSerializer):

    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)

    teacher_email = serializers.CharField(source='teacher.email', read_only=True)

    class_name = serializers.CharField(source='school_class.name', read_only=True)

    class_grade = serializers.IntegerField(source='school_class.grade', read_only=True)

    student_name = serializers.CharField(source='student.full_name', read_only=True, default='')

    reflection_type_display = serializers.CharField(source='get_reflection_type_display', read_only=True)

    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)

    status_display = serializers.CharField(source='get_status_display', read_only=True)

    processed_by_name = serializers.CharField(source='processed_by.full_name', read_only=True, default='')

    violation_code = serializers.CharField(source='violation_record.record_code', read_only=True, default='')

    evidence_image_url = serializers.SerializerMethodField()

    histories = ReflectionHistorySerializer(many=True, read_only=True)



    class Meta:

        model = TeacherReflection

        fields = [

            'id', 'reflection_code', 'teacher', 'teacher_name', 'teacher_email',

            'school_class', 'class_name', 'class_grade', 'student', 'student_name',

            'student_name_snapshot', 'reflection_type', 'reflection_type_display',

            'content', 'occurred_at', 'urgency', 'urgency_display',

            'evidence_image_url', 'status', 'status_display',

            'feedback_notes', 'processed_by', 'processed_by_name', 'processed_at',

            'violation_record', 'violation_code', 'created_at', 'updated_at',

            'histories'

        ]



    def get_evidence_image_url(self, obj):

        if obj.evidence_image:

            return obj.evidence_image.url

        return None





class RedStarAssignmentSerializer(serializers.ModelSerializer):

    student_name = serializers.CharField(source='user.full_name', read_only=True)

    student_username = serializers.CharField(source='user.username', read_only=True)

    student_code = serializers.CharField(source='student.student_code', read_only=True, default='')

    home_class_name = serializers.CharField(source='student.school_class.name', read_only=True, default='')

    assigned_by_name = serializers.CharField(source='assigned_by.full_name', read_only=True, default='')

    assigned_class_name = serializers.CharField(source='assigned_class.name', read_only=True, default='')

    scope_display = serializers.CharField(source='get_scope_display_text', read_only=True)

    status_display = serializers.CharField(source='get_status_display', read_only=True)

    is_active_now = serializers.BooleanField(read_only=True)

    assigned_class_ids = serializers.PrimaryKeyRelatedField(

        many=True, queryset=SchoolClass.objects.all(), source='assigned_classes', required=False

    )



    class Meta:

        model = RedStarAssignment

        fields = [

            'id', 'user', 'student', 'student_name', 'student_username', 'student_code',

            'home_class_name', 'scope_type', 'scope_display',

            'assigned_class', 'assigned_class_name', 'assigned_classes', 'assigned_class_ids',

            'assigned_grade', 'area_name',

            'assigned_by', 'assigned_by_name',

            'start_date', 'end_date', 'status', 'status_display', 'is_active_now',

            'notes', 'revoked_by', 'revoked_at', 'revoke_reason',

            'created_at', 'updated_at'

        ]

        read_only_fields = ['id', 'assigned_by', 'revoked_by', 'revoked_at', 'created_at', 'updated_at']





class RedStarReportSerializer(serializers.ModelSerializer):

    reporter_name = serializers.CharField(source='reporter.full_name', read_only=True, default='')

    reporter_username = serializers.CharField(source='reporter.username', read_only=True, default='')

    class_name = serializers.CharField(source='school_class.name', read_only=True)

    class_grade = serializers.IntegerField(source='school_class.grade', read_only=True)

    rule_name = serializers.CharField(source='rule.name', read_only=True, default='')

    rule_code = serializers.CharField(source='rule.code', read_only=True, default='')

    status_display = serializers.CharField(source='get_status_display', read_only=True)

    reviewed_by_name = serializers.CharField(source='reviewed_by.full_name', read_only=True, default='')

    evidence_image_url = serializers.SerializerMethodField()



    class Meta:

        model = RedStarReport

        fields = [

            'id', 'report_code', 'reporter', 'reporter_name', 'reporter_username',

            'assignment', 'school_class', 'class_name', 'class_grade',

            'student', 'student_name_snapshot',

            'rule', 'rule_name', 'rule_code', 'incident_type',

            'incident_time', 'location', 'description',

            'evidence_image', 'evidence_image_url',

            'status', 'status_display',

            'reviewed_by', 'reviewed_by_name', 'reviewed_at', 'review_note',

            'violation_record', 'created_at', 'updated_at'

        ]

        read_only_fields = [

            'id', 'report_code', 'reporter', 'status', 'status_display',

            'reviewed_by', 'reviewed_at', 'violation_record', 'created_at', 'updated_at'

        ]



    def get_evidence_image_url(self, obj):

        if obj.evidence_image:

            return obj.evidence_image.url

        return None









class StudentFeedbackReplySerializer(serializers.ModelSerializer):

    author_name = serializers.CharField(source='author.full_name', read_only=True, default='')

    author_username = serializers.CharField(source='author.username', read_only=True, default='')



    class Meta:

        model = StudentFeedbackReply

        fields = [

            'id', 'feedback', 'author', 'author_name', 'author_username',

            'author_role', 'content', 'created_at', 'updated_at'

        ]

        read_only_fields = ['id', 'author', 'created_at', 'updated_at']





class StudentFeedbackSerializer(serializers.ModelSerializer):

    student_name = serializers.CharField(source='student.full_name', read_only=True)

    student_code = serializers.CharField(source='student.student_code', read_only=True)

    class_name = serializers.CharField(source='school_class.name', read_only=True)

    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True, default='')

    teacher_username = serializers.CharField(source='teacher.username', read_only=True, default='')

    feedback_type_display = serializers.CharField(source='get_feedback_type_display', read_only=True)

    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    visibility_scope_display = serializers.CharField(source='get_visibility_scope_display', read_only=True)

    status_display = serializers.CharField(source='get_status_display', read_only=True)

    replies = StudentFeedbackReplySerializer(many=True, read_only=True)

    replies_count = serializers.IntegerField(source='replies.count', read_only=True)



    class Meta:

        model = StudentFeedback

        fields = [

            'id', 'feedback_code', 'student', 'student_name', 'student_code',

            'school_class', 'class_name', 'teacher', 'teacher_name', 'teacher_username',

            'teacher_role', 'subject', 'feedback_type', 'feedback_type_display',

            'priority', 'priority_display', 'visibility_scope', 'visibility_scope_display',

            'content', 'strengths', 'weaknesses', 'cooperation_proposal',

            'status', 'status_display', 'seen_at', 'replies', 'replies_count',

            'created_at', 'updated_at'

        ]

        read_only_fields = [

            'id', 'feedback_code', 'teacher', 'teacher_name', 'teacher_username',

            'status_display', 'feedback_type_display', 'priority_display',

            'visibility_scope_display', 'seen_at', 'created_at', 'updated_at'

        ]





class TeacherAssignedClassSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    grade = serializers.IntegerField()
    academic_year_name = serializers.CharField()
    student_count = serializers.IntegerField()
    assignment_role = serializers.CharField()
    assignment_role_display = serializers.CharField()
    subjects = serializers.ListField(child=serializers.CharField())
    homeroom_teacher_name = serializers.CharField()
    homeroom_teacher_id = serializers.IntegerField(allow_null=True, required=False)
    monitor_id = serializers.IntegerField(allow_null=True, required=False)
    monitor_name = serializers.CharField(allow_null=True, required=False)
    can_assign_monitor = serializers.BooleanField(default=False, required=False)
