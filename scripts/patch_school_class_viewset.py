import os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

file_path = r'conduct/views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern for SchoolClassViewSet
old_sc_pattern = r'class SchoolClassViewSet\(viewsets\.ReadOnlyModelViewSet\):.*?(?=class StudentViewSet)'
new_sc_code = '''class SchoolClassViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SchoolClass.objects.all().select_related('academic_year', 'homeroom_teacher')
    serializer_class = SchoolClassSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        qs = SchoolClass.objects.filter(is_active=True).select_related('academic_year', 'homeroom_teacher')
        user = self.request.user

        is_all = (
            self.request.query_params.get('all') in ['true', '1'] or
            self.request.query_params.get('scope') == 'all' or
            self.request.query_params.get('for_violation') in ['true', '1']
        )

        if user.is_admin or user.is_bgh or user.is_doan_truong:
            pass
        elif user.is_student and not (user.role == User.ROLE_SAO_DO or getattr(user, 'is_sao_do', False) or user.is_active_red_star):
            # Học sinh chỉ được xem thông tin lớp học của chính mình
            student = getattr(user, 'student_profile', None)
            qs = qs.filter(id=student.school_class_id) if student and student.school_class_id else qs.none()
        elif is_all or user.is_staff or user.is_gvcn or user.is_gvbm or user.role in [User.ROLE_GVCN, User.ROLE_GVBM, User.ROLE_SAO_DO] or getattr(user, 'is_sao_do', False) or user.is_active_red_star:
            # Cho phép GVCN, GVBM, Sao đỏ truy cập toàn bộ 64 lớp học để phục vụ ghi nhận vi phạm nề nếp, duyệt hồ sơ và tra cứu
            pass
        else:
            qs = qs.none()

        grade = self.request.query_params.get('grade')
        if grade:
            qs = qs.filter(grade=grade)

        return qs.order_by('grade', 'class_order', 'name')

'''

m = re.search(old_sc_pattern, content, flags=re.DOTALL)
if not m:
    print("ERROR: old_sc_pattern not found!")
    sys.exit(1)

content = content[:m.start()] + new_sc_code + content[m.end():]
print("SchoolClassViewSet replaced.")

# Pattern for StudentViewSet up to profile_detail
old_st_pattern = r'class StudentViewSet\(viewsets\.ReadOnlyModelViewSet\):.*?(?=@action\(detail=True)'
new_st_code = '''class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Student.objects.all().select_related('school_class')
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        is_all = (
            self.request.query_params.get('all') in ['true', '1'] or
            self.request.query_params.get('scope') == 'all' or
            self.request.query_params.get('for_violation') in ['true', '1']
        )
        class_id = self.request.query_params.get('class_id')

        if user.is_admin or user.is_bgh or user.is_doan_truong:
            pass
        elif user.is_student and not (user.role == User.ROLE_SAO_DO or getattr(user, 'is_sao_do', False) or user.is_active_red_star):
            qs = qs.filter(user_id=user.id)
        elif (user.is_gvcn or user.is_gvbm or user.role in [User.ROLE_GVCN, User.ROLE_GVBM, User.ROLE_SAO_DO] or getattr(user, 'is_sao_do', False) or user.is_active_red_star) and (is_all or class_id):
            # Cho phép GV và Sao đỏ xem danh sách học sinh theo lớp để phục vụ ghi nhận vi phạm / nhận xét
            pass
        elif user.is_gvcn or user.is_gvbm or user.role in [User.ROLE_GVCN, User.ROLE_GVBM]:
            homeroom_ids = list(HomeroomAssignment.objects.filter(teacher=user, is_active=True).values_list('school_class_id', flat=True))
            teaching_ids = list(TeacherClassAssignment.objects.filter(teacher=user, is_active=True).values_list('school_class_id', flat=True))
            qs = qs.filter(Q(school_class__homeroom_teacher=user) | Q(school_class_id__in=homeroom_ids) | Q(school_class_id__in=teaching_ids)).distinct()
        elif getattr(user, 'is_sao_do', False) or user.is_active_red_star:
            active_assignments = list(user.red_star_assignments.filter(
                status=RedStarAssignment.STATUS_ACTIVE,
                start_date__lte=timezone.localdate(),
            ).filter(Q(end_date__isnull=True) | Q(end_date__gte=timezone.localdate())))
            covered_ids = [
                school_class.id for school_class in SchoolClass.objects.filter(is_active=True)
                if any(assignment.can_cover_class(school_class) for assignment in active_assignments)
            ]
            qs = qs.filter(school_class_id__in=covered_ids)
        else:
            qs = qs.none()

        if self.request.query_params.get('red_star_candidates') == 'true':
            qs = qs.filter(user__account_status=User.STATUS_APPROVED, status='STUDYING')

        if class_id:
            qs = qs.filter(school_class_id=class_id)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(full_name__icontains=search) |
                Q(student_code__icontains=search)
            )

        return qs.order_by('full_name')

    '''

m2 = re.search(old_st_pattern, content, flags=re.DOTALL)
if not m2:
    print("ERROR: old_st_pattern not found!")
    sys.exit(1)

content = content[:m2.start()] + new_st_code + content[m2.end():]
print("StudentViewSet replaced.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully saved conduct/views.py!")
