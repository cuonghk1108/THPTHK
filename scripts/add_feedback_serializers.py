# -*- coding: utf-8 -*-
import sys

SERIALIZER_CODE = '''

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
'''

target_path = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\conduct\serializers.py'
with open(target_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Check imports
if 'StudentFeedback' not in content:
    # Add imports to top
    content = content.replace(
        'RedStarAssignment, RedStarReport,',
        'RedStarAssignment, RedStarReport,\n    StudentFeedback, StudentFeedbackReply,'
    )
    content += SERIALIZER_CODE
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Serializers added to conduct/serializers.py")
else:
    print("ALREADY EXISTS: StudentFeedback serializer already in conduct/serializers.py")
