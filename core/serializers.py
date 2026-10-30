import re
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User, AcademicYear, Semester, SystemSetting, AuditLog, ApprovalLog, Notification


class UserSerializer(serializers.ModelSerializer):
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
    is_class_monitor = serializers.BooleanField(read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True, default='')
    rejected_by_name = serializers.CharField(source='rejected_by.full_name', read_only=True, default='')
    permissions = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.ImageField(read_only=True)
    pending_class_change = serializers.SerializerMethodField(read_only=True)
    teaching_classes = serializers.SerializerMethodField(read_only=True)
    teacher_subject = serializers.SerializerMethodField(read_only=True)
    homeroom_class_info = serializers.SerializerMethodField(read_only=True)
    student_class_info = serializers.SerializerMethodField(read_only=True)

    def get_permissions(self, obj):
        return obj.get_effective_permissions()

    def get_pending_class_change(self, obj):
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
        return None

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'phone', 'avatar', 'role', 'role_display',
            'account_status', 'account_status_display', 'requested_role',
            'department_or_class', 'verification_info', 'rejection_reason', 'internal_notes',
            'approved_by', 'approved_by_name', 'approved_at',
            'rejected_by', 'rejected_by_name', 'rejected_at',
            'doan_truong_permissions', 'permissions',
            'can_view_counseling', 'can_verify_violations', 'is_active', 'is_admin', 'is_super_admin',
            'is_doan_truong', 'is_sao_do', 'is_active_red_star',
            'is_gvcn', 'is_gvbm', 'is_student', 'is_class_monitor',
            'must_change_password', 'date_joined', 'last_login', 'google_id', 'google_avatar_url', 'profile_completed', 'submitted_at',
            'pending_class_change', 'teaching_classes', 'teacher_subject', 'homeroom_class_info', 'student_class_info'
        ]
        read_only_fields = [
            'id', 'role_display', 'account_status_display', 'is_admin', 'is_super_admin',
            'is_doan_truong', 'is_sao_do', 'is_active_red_star',
            'is_gvcn', 'is_gvbm', 'is_student', 'is_class_monitor', 'permissions',
            'approved_by_name', 'rejected_by_name', 'must_change_password', 'date_joined', 'last_login', 'google_id', 'google_avatar_url', 'profile_completed', 'submitted_at', 'avatar',
            'pending_class_change', 'teaching_classes', 'teacher_subject', 'homeroom_class_info', 'student_class_info'
        ]


class ProfileSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    account_status_display = serializers.CharField(source='get_account_status_display', read_only=True)
    avatar = serializers.ImageField(read_only=True)
    pending_class_change = serializers.SerializerMethodField(read_only=True)
    teaching_classes = serializers.SerializerMethodField(read_only=True)
    student_class_name = serializers.SerializerMethodField(read_only=True)
    student_class_id = serializers.SerializerMethodField(read_only=True)
    teacher_subject = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'phone', 'avatar',
            'role', 'role_display', 'account_status_display',
            'department_or_class', 'date_joined',
            'pending_class_change', 'teaching_classes',
            'student_class_name', 'student_class_id', 'teacher_subject'
        ]
        read_only_fields = fields

    def get_pending_class_change(self, obj):
        if not obj.verification_info:
            return None
        try:
            if obj.verification_info.startswith('{'):
                info = json.loads(obj.verification_info)
                return info.get('pending_class_change')
        except Exception:
            pass
        return None

    def get_teaching_classes(self, obj):
        if hasattr(obj, 'teaching_assignments'):
            return list(obj.teaching_assignments.filter(is_active=True).values_list('school_class__name', flat=True))
        return []

    def get_student_class_name(self, obj):
        profile = getattr(obj, 'student_profile', None)
        if profile and profile.school_class:
            return profile.school_class.name
        return obj.department_or_class or ''

    def get_student_class_id(self, obj):
        profile = getattr(obj, 'student_profile', None)
        if profile and profile.school_class:
            return profile.school_class_id
        return None

    def get_teacher_subject(self, obj):
        profile = getattr(obj, 'teacher_profile', None)
        if profile:
            return profile.subject or ''
        return ''


class ProfileUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    current_password = serializers.CharField(max_length=128, required=False, allow_blank=True, write_only=True)
    new_password = serializers.CharField(max_length=128, required=False, allow_blank=True, write_only=True)
    confirm_password = serializers.CharField(max_length=128, required=False, allow_blank=True, write_only=True)
    # Student class change request:
    target_class_id = serializers.IntegerField(required=False, allow_null=True)
    target_class_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    class_change_reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    cancel_class_change = serializers.BooleanField(required=False, default=False)
    # Teacher classes update:
    teaching_classes = serializers.ListField(child=serializers.CharField(), required=False)
    subject = serializers.CharField(max_length=100, required=False, allow_blank=True)
    subjects = serializers.ListField(child=serializers.CharField(), required=False)

    def to_internal_value(self, data):
        allowed_fields = {
            'full_name', 'phone', 'email',
            'current_password', 'new_password', 'confirm_password',
            'target_class_id', 'target_class_name', 'class_change_reason', 'cancel_class_change',
            'teaching_classes', 'subject', 'subjects'
        }
        unexpected_fields = set(data) - allowed_fields
        if unexpected_fields:
            raise serializers.ValidationError({
                'non_field_errors': f'Trường không được phép cập nhật: {", ".join(unexpected_fields)}'
            })
        if not data:
            raise serializers.ValidationError({'non_field_errors': 'Hãy nhập thông tin cần cập nhật.'})
        return super().to_internal_value(data)

    def validate_full_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Họ và tên không được để trống.')
        return value

    def validate_phone(self, value):
        value = value.strip() if value else ''
        if not value:
            return ''
        normalized = re.sub(r'[\s.-]', '', value)
        if not re.fullmatch(r'\+?[0-9]{9,15}', normalized):
            raise serializers.ValidationError('Số điện thoại cần có từ 9 đến 15 chữ số.')
        return normalized

    def validate_email(self, value):
        value = value.strip().lower() if value else ''
        if not value:
            raise serializers.ValidationError('Địa chỉ email không được để trống.')
        request = self.context.get('request')
        user = request.user if request else None
        qs = User.objects.filter(email__iexact=value).exclude(email='')
        if user:
            qs = qs.exclude(id=user.id)
        if qs.exists():
            raise serializers.ValidationError('Địa chỉ email này đã được sử dụng bởi một tài khoản khác trong hệ thống.')
        return value

    def validate(self, attrs):
        new_pwd = attrs.get('new_password')
        cur_pwd = attrs.get('current_password')
        conf_pwd = attrs.get('confirm_password')

        if new_pwd:
            if not cur_pwd:
                raise serializers.ValidationError({'current_password': 'Vui lòng nhập mật khẩu hiện tại để xác nhận đổi mật khẩu.'})
            if not conf_pwd:
                raise serializers.ValidationError({'confirm_password': 'Vui lòng xác nhận mật khẩu mới.'})
            if new_pwd != conf_pwd:
                raise serializers.ValidationError({'confirm_password': 'Mật khẩu xác nhận không khớp.'})
            request = self.context.get('request')
            if request and request.user and not request.user.check_password(cur_pwd):
                raise serializers.ValidationError({'current_password': 'Mật khẩu hiện tại không chính xác.'})
            try:
                validate_password(new_pwd, user=request.user if request else None)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({'new_password': exc.messages}) from exc
        return attrs


class RegisterSerializer(serializers.Serializer):
    REQUESTED_ROLE_CHOICES = [
        ('HOC_SINH', 'Học sinh'),
        ('GVBM', 'Giáo viên bộ môn'),
        ('OTHER', 'Nhân sự khác được nhà trường cho phép'),
    ]

    full_name = serializers.CharField(max_length=150, min_length=2, error_messages={
        'required': 'Vui lòng nhập họ và tên đầy đủ.',
        'blank': 'Họ và tên không được để trống.',
        'min_length': 'Họ và tên quá ngắn.'
    })
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(error_messages={
        'required': 'Vui lòng nhập địa chỉ email hợp lệ.',
        'invalid': 'Địa chỉ email không đúng định dạng.'
    })
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6, error_messages={
        'required': 'Vui lòng nhập mật khẩu.',
        'min_length': 'Mật khẩu phải có ít nhất 6 ký tự.'
    })
    confirm_password = serializers.CharField(write_only=True, required=True, error_messages={
        'required': 'Vui lòng nhập lại mật khẩu xác nhận.'
    })
    requested_role = serializers.CharField(error_messages={
        'required': 'Vui lòng chọn đối tượng đăng ký.',
        'blank': 'Đối tượng đăng ký không được để trống.'
    })
    grade_level = serializers.IntegerField(required=False, allow_null=True)
    class_id = serializers.IntegerField(required=False, allow_null=True)
    department_or_class = serializers.CharField(max_length=100, required=False, allow_blank=True)
    subject = serializers.CharField(max_length=200, required=False, allow_blank=True)
    subjects = serializers.ListField(child=serializers.CharField(), required=False)
    teaching_classes = serializers.ListField(child=serializers.CharField(), required=False)
    verification_info = serializers.CharField(required=False, allow_blank=True)
    terms_accepted = serializers.BooleanField(required=True, error_messages={
        'required': 'Bạn phải đồng ý với điều khoản sử dụng và chính sách quyền riêng tư.'
    })

    def validate_requested_role(self, value):
        val = (value or '').strip()
        if val in ['ADMIN', 'SUPER_ADMIN', 'DOAN_TRUONG', 'SAO_DO', 'BGH', 'GVCN']:
            raise serializers.ValidationError('Bạn không được tự chọn vai trò quản trị, Đoàn trường, GVCN hoặc Sao đỏ; các quyền này do nhà trường cấp.')
        allowed_roles = [choice[0] for choice in self.REQUESTED_ROLE_CHOICES]
        if val not in allowed_roles:
            raise serializers.ValidationError('Đối tượng đăng ký không hợp lệ.')
        return val

    def validate_full_name(self, value):
        return value.strip()

    def validate_username(self, value):
        if not value:
            return ''
        value = value.strip().lower()
        if not re.match(r'^[a-zA-Z0-9_.-]+$', value):
            raise serializers.ValidationError('Tên đăng nhập chỉ được chứa chữ cái không dấu, chữ số, dấu gạch dưới, dấu gạch ngang hoặc dấu chấm.')
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Tên đăng nhập này đã được sử dụng. Vui lòng chọn tên khác.')
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exclude(email='').exists():
            raise serializers.ValidationError('Địa chỉ email này đã được đăng ký trong hệ thống.')
        return value

    def validate_phone(self, value):
        value = value.strip() if value else ''
        if value:
            clean_digits = re.sub(r'[\s.-]', '', value)
            if not re.match(r'^\+?[0-9]{9,15}$', clean_digits):
                raise serializers.ValidationError('Số điện thoại không hợp lệ (cần từ 9 đến 15 chữ số).')
            return clean_digits
        return ''

    def validate_terms_accepted(self, value):
        if not value:
            raise serializers.ValidationError('Bạn phải đánh dấu đồng ý với điều khoản sử dụng và chính sách bảo mật.')
        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({'confirm_password': 'Mật khẩu nhập lại không khớp với mật khẩu đã nhập.'})
        
        # Validate password strength with Django validators
        try:
            validate_password(attrs.get('password'))
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)}) from exc

        # Auto-generate username from email if not provided
        email = attrs.get('email', '').strip().lower()
        username = attrs.get('username')
        if not username:
            base_user = re.sub(r'[^a-zA-Z0-9_.-]', '', email.split('@')[0]) or 'user'
            candidate = base_user
            idx = 1
            while User.objects.filter(username__iexact=candidate).exists():
                candidate = f"{base_user}{idx}"
                idx += 1
            attrs['username'] = candidate

        requested_role = attrs.get('requested_role')
        from conduct.models import SchoolClass

        # 1. Ràng buộc học sinh: Bắt buộc chọn khối và lớp hợp lệ
        if requested_role == 'HOC_SINH':
            grade_level = attrs.get('grade_level')
            class_id = attrs.get('class_id')
            dept = (attrs.get('department_or_class') or '').strip()

            class_obj = None
            if class_id:
                class_obj = SchoolClass.objects.filter(id=class_id, is_active=True).first()
                if not class_obj:
                    raise serializers.ValidationError({'class_id': 'Lớp học được chọn không tồn tại hoặc đã bị khóa.'})
            elif dept:
                clean_dept = dept
                if clean_dept.lower().startswith('lớp '):
                    clean_dept = clean_dept[4:].strip()
                elif clean_dept.lower().startswith('lop '):
                    clean_dept = clean_dept[4:].strip()
                class_obj = SchoolClass.objects.filter(name__iexact=clean_dept, is_active=True).first()
                if not class_obj:
                    class_obj = SchoolClass.objects.filter(name__iexact=dept, is_active=True).first()

            if not class_obj:
                raise serializers.ValidationError({'class_id': 'Vui lòng chọn lớp học chính thức của học sinh.'})

            # Kiểm tra khối của lớp có khớp với khối đã chọn không
            if grade_level and class_obj.grade != grade_level:
                raise serializers.ValidationError({
                    'class_id': f'Lớp {class_obj.name} thuộc Khối {class_obj.grade}, không khớp với Khối {grade_level} bạn đã chọn.'
                })

            attrs['validated_school_class'] = class_obj
            attrs['department_or_class'] = class_obj.name

        # 2. Ràng buộc giáo viên bộ môn: Bắt buộc chọn môn giảng dạy (hỗ trợ nhiều môn & nhiều lớp)
        elif requested_role == 'GVBM':
            import json
            subjects_list = attrs.get('subjects') or []
            if isinstance(subjects_list, str):
                try:
                    subjects_list = json.loads(subjects_list)
                except Exception:
                    subjects_list = [s.strip() for s in subjects_list.split(',') if s.strip()]

            subject = (attrs.get('subject') or attrs.get('department_or_class') or '').strip()
            if subject and not subjects_list:
                subjects_list = [s.strip() for s in subject.split(',') if s.strip()]

            clean_subjects = []
            for s in subjects_list:
                sc = s.strip()
                if sc.startswith('Môn '):
                    sc = sc[4:].strip()
                elif sc.startswith('Môn: '):
                    sc = sc[5:].strip()
                if sc and sc not in clean_subjects:
                    clean_subjects.append(sc)

            if not clean_subjects:
                raise serializers.ValidationError({'subject': 'Vui lòng chọn ít nhất một môn giảng dạy của giáo viên.'})

            attrs['validated_subjects'] = clean_subjects
            attrs['validated_subject'] = ", ".join(clean_subjects)
            attrs['department_or_class'] = f"Môn: {', '.join(clean_subjects)}" if len(clean_subjects) > 1 else f"Môn {clean_subjects[0]}"

            classes_input = attrs.get('teaching_classes') or []
            if isinstance(classes_input, str):
                try:
                    classes_input = json.loads(classes_input)
                except Exception:
                    classes_input = [c.strip() for c in classes_input.split(',') if c.strip()]

            from conduct.models import SchoolClass
            valid_classes = []
            for item in classes_input:
                if isinstance(item, int) or (isinstance(item, str) and item.isdigit()):
                    sc_obj = SchoolClass.objects.filter(id=int(item), is_active=True).first()
                else:
                    sc_obj = SchoolClass.objects.filter(name__iexact=str(item).strip(), is_active=True).first()
                if sc_obj and sc_obj not in valid_classes:
                    valid_classes.append(sc_obj)

            attrs['validated_teaching_classes'] = valid_classes

        else:
            if not attrs.get('department_or_class'):
                raise serializers.ValidationError({'department_or_class': 'Vui lòng nhập lớp hoặc đơn vị công tác.'})

        return attrs

    def create(self, validated_data):
        import uuid
        from django.utils import timezone
        from conduct.models import Student, Teacher

        import json
        validated_data.pop('confirm_password', None)
        validated_data.pop('terms_accepted', None)
        class_obj = validated_data.pop('validated_school_class', None)
        validated_data.pop('class_id', None)
        validated_data.pop('grade_level', None)
        subject_str = validated_data.pop('validated_subject', None)
        validated_subjects = validated_data.pop('validated_subjects', [])
        validated_classes = validated_data.pop('validated_teaching_classes', [])
        validated_data.pop('subject', None)
        validated_data.pop('subjects', None)
        validated_data.pop('teaching_classes', None)
        password = validated_data.pop('password')

        requested_role = validated_data['requested_role']
        is_student = (requested_role == 'HOC_SINH')
        is_teacher = (requested_role == 'GVBM')

        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            phone=validated_data.get('phone', ''),
            requested_role=requested_role,
            department_or_class=validated_data.get('department_or_class', ''),
            verification_info=validated_data.get('verification_info', ''),
            account_status=User.STATUS_PENDING,
            role=User.ROLE_HOC_SINH if is_student else (User.ROLE_GVBM if is_teacher else User.ROLE_HOC_SINH),
            is_active=False,  # Inactive until approved
            is_staff=False,
            is_superuser=False,
            can_verify_violations=False,
            can_view_counseling=False,
            must_change_password=False,
        )
        user.set_password(password)
        user.save()

        # Tạo hồ sơ học sinh liên kết duy nhất 1 lớp
        if is_student and class_obj:
            student_code = f"HK{class_obj.grade}-{timezone.now().strftime('%y%m')}-{uuid.uuid4().hex[:4].upper()}"
            Student.objects.create(
                user=user,
                student_code=student_code,
                full_name=user.full_name,
                date_of_birth=timezone.now().date(),
                gender='M',
                school_class=class_obj,
                status='STUDYING'
            )

        # Tạo hồ sơ giáo viên bộ môn & lưu thông tin đăng ký lớp / môn
        if is_teacher:
            subj_final = ", ".join(validated_subjects) if validated_subjects else (subject_str or 'Chưa phân công')
            user.verification_info = json.dumps({
                'role_type': 'teacher',
                'subjects': validated_subjects or ([subj_final] if subj_final else []),
                'teaching_classes': [c.name for c in validated_classes],
                'teaching_class_ids': [c.id for c in validated_classes],
            }, ensure_ascii=False)
            user.save(update_fields=['verification_info'])

            teacher_code = f"GV-{timezone.now().strftime('%y%m')}-{uuid.uuid4().hex[:4].upper()}"
            Teacher.objects.create(
                user=user,
                teacher_code=teacher_code,
                full_name=user.full_name,
                subject=subj_final,
                phone=user.phone
            )

            from conduct.models import TeacherClassAssignment
            for sc in validated_classes:
                primary_s = validated_subjects[0] if validated_subjects else subj_final
                TeacherClassAssignment.objects.get_or_create(
                    teacher=user,
                    school_class=sc,
                    subject=primary_s,
                    defaults={'is_active': False}
                )

        return user


class ApprovalActionSerializer(serializers.Serializer):
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
    teaching_class_ids = serializers.ListField(child=serializers.IntegerField(), required=False)

    def validate(self, attrs):
        action = attrs.get('action')
        if action == 'approve':
            if not attrs.get('assigned_role'):
                raise serializers.ValidationError({'assigned_role': 'Khi phê duyệt tài khoản, Admin bắt buộc phải chọn vai trò/chức vụ được cấp.'})
        elif action in ['reject', 'suspend', 'request_info']:
            if not attrs.get('reason'):
                raise serializers.ValidationError({'reason': f'Vui lòng nhập lý do cụ thể khi thực hiện thao tác {action}.'})
        return attrs


class ApprovalLogSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.full_name', read_only=True, default='Hệ thống')
    reviewer_username = serializers.CharField(source='reviewer.username', read_only=True, default='')
    user_name = serializers.CharField(source='user.full_name', read_only=True, default='')
    user_username = serializers.CharField(source='user.username', read_only=True, default='')

    class Meta:
        model = ApprovalLog
        fields = [
            'id', 'user', 'user_name', 'user_username', 'reviewer', 'reviewer_name',
            'reviewer_username', 'previous_status', 'new_status', 'assigned_role',
            'reason', 'internal_notes', 'created_at'
        ]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 'link', 'is_read', 'read_at', 'created_at'
        ]


class UserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default=User.ROLE_HOC_SINH)

    def validate_username(self, value):
        value = value.strip().lower()
        try:
            User._meta.get_field('username').run_validators(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Tên đăng nhập này đã tồn tại.')
        return value

    def create(self, validated_data):
        temporary_password = validated_data.pop('temporary_password')
        user = User(
            **validated_data,
            account_status=User.STATUS_APPROVED,
            profile_completed=True,
            is_active=True,
            is_staff=False,
            is_superuser=False,
            can_verify_violations=False,
            can_view_counseling=False,
            must_change_password=True,
        )
        user.set_password(temporary_password)
        user.save()
        return user


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Mật khẩu xác nhận không khớp.'})
        try:
            validate_password(attrs['new_password'], user=self.context['request'].user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'new_password': exc.messages}) from exc
        return attrs


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


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)

    def validate_email(self, value):
        val = value.strip().lower()
        if not val:
            raise serializers.ValidationError("Vui lòng nhập địa chỉ email hoặc tên đăng nhập.")
        return val


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
        error_messages={'min_length': 'Mật khẩu mới phải có độ dài tối thiểu 8 ký tự.'}
    )
    confirm_password = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
        error_messages={'min_length': 'Mật khẩu xác nhận phải có độ dài tối thiểu 8 ký tự.'}
    )

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError({'confirm_password': 'Mật khẩu xác nhận không khớp.'})

        return attrs


class StudentAccountSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    account_status_display = serializers.CharField(source='get_account_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True, default='')
    rejected_by_name = serializers.CharField(source='rejected_by.full_name', read_only=True, default='')
    student_code = serializers.SerializerMethodField(read_only=True)
    school_class_name = serializers.SerializerMethodField(read_only=True)
    grade = serializers.SerializerMethodField(read_only=True)
    is_red_star = serializers.BooleanField(source='is_active_red_star', read_only=True)
    pending_class_change = serializers.SerializerMethodField(read_only=True)

    def get_pending_class_change(self, obj):
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
        return None

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'phone', 'role', 'role_display',
            'account_status', 'account_status_display', 'requested_role',
            'department_or_class', 'verification_info', 'rejection_reason',
            'approved_by', 'approved_by_name', 'approved_at',
            'rejected_by', 'rejected_by_name', 'rejected_at',
            'student_code', 'school_class_name', 'grade', 'is_red_star',
            'date_joined', 'last_login', 'pending_class_change'
        ]

    def get_student_code(self, obj):
        profile = getattr(obj, 'student_profile', None)
        return profile.student_code if profile else ''

    def get_school_class_name(self, obj):
        profile = getattr(obj, 'student_profile', None)
        if profile and profile.school_class:
            return profile.school_class.name
        return obj.department_or_class or ''

    def get_grade(self, obj):
        profile = getattr(obj, 'student_profile', None)
        if profile and profile.school_class:
            return profile.school_class.grade
        # Extract from department_or_class if possible
        dept = obj.department_or_class or ''
        m = re.search(r'(10|11|12)', dept)
        return int(m.group(1)) if m else None


class StudentApprovalActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject', 'request_info', 'suspend', 'approve_class_change', 'reject_class_change'])
    reason = serializers.CharField(required=False, allow_blank=True, default='')
    class_id = serializers.IntegerField(required=False, allow_null=True)
    internal_notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        action = attrs.get('action')
        reason = attrs.get('reason', '').strip()
        if action in ['reject', 'request_info'] and not reason:
            raise serializers.ValidationError({'reason': 'Vui lòng nhập lý do từ chối hoặc yêu cầu bổ sung thông tin.'})
        return attrs


class StudentBulkApprovalSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    user_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    reason = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        if attrs.get('action') == 'reject' and not attrs.get('reason', '').strip():
            raise serializers.ValidationError({'reason': 'Vui lòng nhập lý do từ chối hàng loạt.'})
        return attrs


class DoanTruongMemberSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email', 'phone', 'role', 'role_display',
            'account_status', 'doan_truong_permissions', 'permissions', 'date_joined'
        ]

    def get_permissions(self, obj):
        return obj.get_effective_permissions()


class DoanTruongPermissionUpdateSerializer(serializers.Serializer):
    permissions = serializers.ListField(
        child=serializers.CharField(),
        required=True
    )

    def validate_permissions(self, value):
        from .models import ALL_DOAN_TRUONG_PERMISSIONS
        invalid = [p for p in value if p not in ALL_DOAN_TRUONG_PERMISSIONS]
        if invalid:
            raise serializers.ValidationError(f"Các quyền không hợp lệ: {', '.join(invalid)}")
        return value




class CompleteProfileSerializer(serializers.Serializer):
    ROLE_TYPE_STUDENT = 'student'
    ROLE_TYPE_TEACHER = 'teacher'
    ROLE_TYPE_CHOICES = [
        (ROLE_TYPE_STUDENT, 'Học sinh'),
        (ROLE_TYPE_TEACHER, 'Giáo viên'),
    ]

    role_type = serializers.ChoiceField(choices=ROLE_TYPE_CHOICES)
    full_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    # Student specific
    grade = serializers.IntegerField(required=False, min_value=10, max_value=12)
    class_id = serializers.IntegerField(required=False, allow_null=True)
    class_name = serializers.CharField(required=False, allow_blank=True, max_length=50)
    dob = serializers.DateField(required=False, allow_null=True)
    gender = serializers.CharField(required=False, allow_blank=True, max_length=10)
    student_code = serializers.CharField(required=False, allow_blank=True, max_length=50)

    # Teacher specific
    subject = serializers.CharField(required=False, allow_blank=True, max_length=200)
    subjects = serializers.ListField(child=serializers.CharField(), required=False)
    teacher_type = serializers.ChoiceField(choices=['gvbm', 'gvcn'], required=False, allow_blank=True)
    teaching_classes = serializers.ListField(child=serializers.CharField(), required=False)
    homeroom_class = serializers.CharField(required=False, allow_blank=True, max_length=50)
    teacher_code = serializers.CharField(required=False, allow_blank=True, max_length=50)

    def validate(self, attrs):
        role_type = attrs.get('role_type')
        if role_type == self.ROLE_TYPE_STUDENT:
            if not attrs.get('class_id') and not attrs.get('class_name'):
                raise serializers.ValidationError({'class_name': 'Học sinh bắt buộc phải chọn lớp học.'})
            if not attrs.get('grade'):
                raise serializers.ValidationError({'grade': 'Vui lòng chọn khối lớp (10, 11 hoặc 12).'})
        elif role_type == self.ROLE_TYPE_TEACHER:
            if not attrs.get('phone'):
                raise serializers.ValidationError({'phone': 'Giáo viên bắt buộc phải cung cấp số điện thoại liên lạc.'})
            if not attrs.get('subject') and not attrs.get('subjects'):
                raise serializers.ValidationError({'subject': 'Vui lòng chọn môn giảng dạy trong danh sách.'})
            if not attrs.get('subject') and attrs.get('subjects'):
                attrs['subject'] = ", ".join(attrs['subjects'])
            if not attrs.get('teacher_type'):
                attrs['teacher_type'] = 'gvbm'
        return attrs
