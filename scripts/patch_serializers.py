import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('core/serializers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update UserSerializer
old_user_serializer_head = """class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    account_status_display = serializers.CharField(source='get_account_status_display', read_only=True)
    is_admin = serializers.BooleanField(read_only=True)
    is_super_admin = serializers.BooleanField(read_only=True)
    is_doan_truong = serializers.BooleanField(read_only=True)
    is_sao_do = serializers.BooleanField(read_only=True)
    is_active_red_star = serializers.BooleanField(read_only=True)
    is_gvcn = serializers.BooleanField(read_only=True)
    is_gvbm = serializers.BooleanField(read_only=True)
    is_student = serializers.BooleanField(read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True, default='')
    rejected_by_name = serializers.CharField(source='rejected_by.full_name', read_only=True, default='')
    permissions = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.ImageField(read_only=True)
    pending_class_change = serializers.SerializerMethodField(read_only=True)"""

new_user_serializer_head = """class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    account_status_display = serializers.CharField(source='get_account_status_display', read_only=True)
    is_admin = serializers.BooleanField(read_only=True)
    is_super_admin = serializers.BooleanField(read_only=True)
    is_doan_truong = serializers.BooleanField(read_only=True)
    is_sao_do = serializers.BooleanField(read_only=True)
    is_active_red_star = serializers.BooleanField(read_only=True)
    is_gvcn = serializers.BooleanField(read_only=True)
    is_gvbm = serializers.BooleanField(read_only=True)
    is_student = serializers.BooleanField(read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True, default='')
    rejected_by_name = serializers.CharField(source='rejected_by.full_name', read_only=True, default='')
    permissions = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.ImageField(read_only=True)
    pending_class_change = serializers.SerializerMethodField(read_only=True)
    teaching_classes = serializers.SerializerMethodField(read_only=True)
    teacher_subject = serializers.SerializerMethodField(read_only=True)
    homeroom_class_info = serializers.SerializerMethodField(read_only=True)
    student_class_info = serializers.SerializerMethodField(read_only=True)"""

# In UserSerializer methods:
old_user_methods = """    def get_pending_class_change(self, obj):
        if not obj.verification_info:
            return None
        try:
            if obj.verification_info.startswith('{'):
                data = json.loads(obj.verification_info)
                return data.get('pending_class_change')
        except Exception:
            pass
        return None"""

new_user_methods = """    def get_pending_class_change(self, obj):
        if not obj.verification_info:
            return None
        try:
            if obj.verification_info.startswith('{'):
                data = json.loads(obj.verification_info)
                return data.get('pending_class_change')
        except Exception:
            pass
        return None

    def get_teaching_classes(self, obj):
        if hasattr(obj, 'teaching_assignments'):
            active_tcas = list(obj.teaching_assignments.filter(is_active=True).values_list('school_class__name', flat=True))
            if active_tcas:
                return active_tcas
        if obj.verification_info and obj.verification_info.startswith('{'):
            try:
                data = json.loads(obj.verification_info)
                if data.get('teaching_classes'):
                    return data.get('teaching_classes')
            except Exception:
                pass
        return []

    def get_teacher_subject(self, obj):
        if hasattr(obj, 'teacher_profile') and obj.teacher_profile and obj.teacher_profile.subject:
            return obj.teacher_profile.subject
        if obj.verification_info and obj.verification_info.startswith('{'):
            try:
                data = json.loads(obj.verification_info)
                if data.get('subjects'):
                    return data.get('subjects')[0]
                if data.get('subject'):
                    return data.get('subject')
            except Exception:
                pass
        if obj.department_or_class:
            dept = obj.department_or_class.strip()
            if dept.startswith('Môn: '): return dept[5:].strip()
            if dept.startswith('Môn '): return dept[4:].strip()
        return ''

    def get_homeroom_class_info(self, obj):
        from conduct.models import HomeroomAssignment, SchoolClass
        active_hr = HomeroomAssignment.objects.filter(teacher=obj, is_active=True).select_related('school_class').first()
        if active_hr and active_hr.school_class:
            return {'id': active_hr.school_class.id, 'name': active_hr.school_class.name, 'grade': active_hr.school_class.grade}
        hr_cls = SchoolClass.objects.filter(homeroom_teacher=obj, is_active=True).first()
        if hr_cls:
            return {'id': hr_cls.id, 'name': hr_cls.name, 'grade': hr_cls.grade}
        if obj.role == User.ROLE_GVCN and obj.department_or_class:
            sc = SchoolClass.objects.filter(name__iexact=obj.department_or_class.strip(), is_active=True).first()
            if sc:
                return {'id': sc.id, 'name': sc.name, 'grade': sc.grade}
        return None

    def get_student_class_info(self, obj):
        from conduct.models import SchoolClass
        if hasattr(obj, 'student_profile') and obj.student_profile and obj.student_profile.school_class:
            sc = obj.student_profile.school_class
            return {'id': sc.id, 'name': sc.name, 'grade': sc.grade}
        if obj.department_or_class:
            sc = SchoolClass.objects.filter(name__iexact=obj.department_or_class.strip(), is_active=True).first()
            if sc:
                return {'id': sc.id, 'name': sc.name, 'grade': sc.grade}
        return None"""

old_user_fields = """            'must_change_password', 'date_joined', 'last_login', 'google_id', 'google_avatar_url', 'profile_completed', 'submitted_at',
            'pending_class_change'
        ]
        read_only_fields = [
            'id', 'role_display', 'account_status_display', 'is_admin', 'is_super_admin',
            'is_doan_truong', 'is_sao_do', 'is_active_red_star',
            'is_gvcn', 'is_gvbm', 'is_student', 'permissions',
            'approved_by_name', 'rejected_by_name', 'must_change_password', 'date_joined', 'last_login', 'google_id', 'google_avatar_url', 'profile_completed', 'submitted_at', 'avatar',
            'pending_class_change'
        ]"""

new_user_fields = """            'must_change_password', 'date_joined', 'last_login', 'google_id', 'google_avatar_url', 'profile_completed', 'submitted_at',
            'pending_class_change', 'teaching_classes', 'teacher_subject', 'homeroom_class_info', 'student_class_info'
        ]
        read_only_fields = [
            'id', 'role_display', 'account_status_display', 'is_admin', 'is_super_admin',
            'is_doan_truong', 'is_sao_do', 'is_active_red_star',
            'is_gvcn', 'is_gvbm', 'is_student', 'permissions',
            'approved_by_name', 'rejected_by_name', 'must_change_password', 'date_joined', 'last_login', 'google_id', 'google_avatar_url', 'profile_completed', 'submitted_at', 'avatar',
            'pending_class_change', 'teaching_classes', 'teacher_subject', 'homeroom_class_info', 'student_class_info'
        ]"""

old_approval_serializer = """class ApprovalActionSerializer(serializers.Serializer):
    ACTION_CHOICES = [
        ('approve', 'Phê duyệt tài khoản'),
        ('reject', 'Từ chối yêu cầu'),
        ('request_info', 'Yêu cầu bổ sung thông tin'),
        ('suspend', 'Tạm khóa tài khoản'),
        ('reactivate', 'Kích hoạt lại tài khoản'),
        ('approve_class_change', 'Phê duyệt chuyển lớp'),
        ('reject_class_change', 'Từ chối chuyển lớp'),
    ]

    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    assigned_role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=False, allow_blank=True)
    department_or_class = serializers.CharField(required=False, allow_blank=True)
    can_verify_violations = serializers.BooleanField(required=False)
    can_view_counseling = serializers.BooleanField(required=False)
    reason = serializers.CharField(required=False, allow_blank=True)
    internal_notes = serializers.CharField(required=False, allow_blank=True)"""

new_approval_serializer = """class ApprovalActionSerializer(serializers.Serializer):
    ACTION_CHOICES = [
        ('approve', 'Phê duyệt tài khoản'),
        ('reject', 'Từ chối yêu cầu'),
        ('request_info', 'Yêu cầu bổ sung thông tin'),
        ('suspend', 'Tạm khóa tài khoản'),
        ('reactivate', 'Kích hoạt lại tài khoản'),
        ('approve_class_change', 'Phê duyệt chuyển lớp'),
        ('reject_class_change', 'Từ chối chuyển lớp'),
    ]

    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    assigned_role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=False, allow_blank=True)
    department_or_class = serializers.CharField(required=False, allow_blank=True)
    can_verify_violations = serializers.BooleanField(required=False)
    can_view_counseling = serializers.BooleanField(required=False)
    reason = serializers.CharField(required=False, allow_blank=True)
    internal_notes = serializers.CharField(required=False, allow_blank=True)
    class_id = serializers.IntegerField(required=False, allow_null=True)
    homeroom_class = serializers.CharField(required=False, allow_blank=True)
    homeroom_class_id = serializers.IntegerField(required=False, allow_null=True)
    subject = serializers.CharField(required=False, allow_blank=True)
    subjects = serializers.ListField(child=serializers.CharField(), required=False)
    teaching_classes = serializers.ListField(child=serializers.CharField(), required=False)
    teaching_class_ids = serializers.ListField(child=serializers.IntegerField(), required=False)"""

content_normalized = content.replace('\r\n', '\n')

assert old_user_serializer_head in content_normalized, "old_user_serializer_head not found"
assert old_user_methods in content_normalized, "old_user_methods not found"
assert old_user_fields in content_normalized, "old_user_fields not found"
assert old_approval_serializer in content_normalized, "old_approval_serializer not found"

content_normalized = content_normalized.replace(old_user_serializer_head, new_user_serializer_head)
content_normalized = content_normalized.replace(old_user_methods, new_user_methods)
content_normalized = content_normalized.replace(old_user_fields, new_user_fields)
content_normalized = content_normalized.replace(old_approval_serializer, new_approval_serializer)

with open('core/serializers.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content_normalized)

print("core/serializers.py patched successfully!")
