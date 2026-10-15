from rest_framework import serializers
from .models import User, AcademicYear, Semester, SystemSetting, AuditLog


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'phone', 'role', 'role_display',
                  'can_view_counseling', 'can_verify_violations', 'is_active']
        read_only_fields = ['id', 'role_display']


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = '__all__'


class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = '__all__'


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = '__all__'


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default='Hệ thống')
    user_full_name = serializers.CharField(source='user.full_name', read_only=True, default='')

    class Meta:
        model = AuditLog
        fields = ['id', 'username', 'user_full_name', 'action', 'resource_type', 'resource_id', 'details', 'ip_address', 'created_at']
