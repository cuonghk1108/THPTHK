from rest_framework import serializers
from .models import CounselingRequest, CounselingPrivateNote


class CounselingPrivateNoteSerializer(serializers.ModelSerializer):
    counselor_name = serializers.CharField(source='counselor.full_name', read_only=True, default='')

    class Meta:
        model = CounselingPrivateNote
        fields = ['id', 'request', 'counselor', 'counselor_name', 'note_content', 'recommendation', 'created_at']


class CounselingRequestDetailSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True, default='Học sinh giấu tên')
    class_name = serializers.CharField(source='student.school_class.name', read_only=True, default='')
    topic_display = serializers.CharField(source='get_topic_display', read_only=True)
    channel_display = serializers.CharField(source='get_preferred_channel_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    counselor_name = serializers.CharField(source='assigned_counselor.full_name', read_only=True, default='')
    private_notes = CounselingPrivateNoteSerializer(many=True, read_only=True)

    class Meta:
        model = CounselingRequest
        fields = [
            'id', 'tracking_code', 'student', 'student_name', 'class_name',
            'is_anonymous', 'alias_name', 'topic', 'topic_display', 'content',
            'preferred_channel', 'channel_display', 'contact_info', 'preferred_schedule',
            'status', 'status_display', 'assigned_counselor', 'counselor_name',
            'scheduled_meeting', 'is_urgent_safety', 'safety_notes', 'created_at', 'private_notes'
        ]


class CounselingPublicTrackSerializer(serializers.ModelSerializer):
    topic_display = serializers.CharField(source='get_topic_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    counselor_name = serializers.CharField(source='assigned_counselor.full_name', read_only=True, default='Ban Tư vấn tâm lý')

    class Meta:
        model = CounselingRequest
        fields = ['tracking_code', 'topic_display', 'status', 'status_display', 'scheduled_meeting', 'counselor_name', 'created_at']
