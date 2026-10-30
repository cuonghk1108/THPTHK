import os
import sys

BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"

# ==============================================================================
# 1. UPDATE core/views.py
# ==============================================================================
views_path = os.path.join(BASE_DIR, "core", "views.py")
with open(views_path, "r", encoding="utf-8") as f:
    views_code = f.read()

views_norm = views_code.replace("\r\n", "\n")

# A. In index_view, redirect students from /competition and /conduct to /dashboard
old_route_guard = """        if normalized_path == '/admin/users' and not (user.is_admin or user.is_superuser):
            return redirect('/dashboard')"""

new_route_guard = """        if normalized_path == '/admin/users' and not (user.is_admin or user.is_superuser):
            return redirect('/dashboard')
        if (user.is_student or user.role == User.ROLE_HOC_SINH) and normalized_path in {'/competition', '/conduct'}:
            return redirect('/dashboard')"""

if old_route_guard in views_norm and new_route_guard not in views_norm:
    views_norm = views_norm.replace(old_route_guard, new_route_guard)
    print("SUCCESS: Added student route guard in index_view (core/views.py)")
else:
    print("NOTE: index_view student route guard already present or old pattern not matched")

# B. In SystemStatsAPIView, return my_violations_list and omit class_score_info for students
old_student_stats = """            own_violations = ViolationRecord.objects.filter(student=student)
            from competition.services import get_current_competition_period
            current_year = AcademicYear.objects.filter(is_current=True).first()
            current_period = get_current_competition_period(current_year, CompetitionPeriod.TYPE_WEEK)
            class_score_info = None
            if student.school_class_id and current_period:
                cs = ClassCompetitionScore.objects.filter(competition_period=current_period, school_class_id=student.school_class_id).first()
                if cs:
                    class_score_info = {
                        'total_score': float(cs.total_score),
                        'rank': cs.rank,
                        'rank_in_grade': cs.rank_in_grade,
                    }
            data = {
                'scope': 'student',
                'profile_available': True,
                'student_name': student.full_name,
                'student_code': student.student_code,
                'student_class': student.school_class.name if student.school_class_id else '',
                'my_violations_verified': own_violations.filter(status__in=verified_statuses).count(),
                'my_violations_pending': own_violations.filter(status=ViolationRecord.STATUS_PENDING).count(),
                'class_score_info': class_score_info,
                'user_role': user.role,
                'user_role_display': user.get_role_display(),
            }"""

new_student_stats = """            own_violations = ViolationRecord.objects.filter(student=student).select_related('rule').order_by('-occurred_at')
            my_violations_list = [
                {
                    'id': v.id,
                    'record_code': v.record_code,
                    'occurred_at': v.occurred_at.strftime('%d/%m/%Y %H:%M') if v.occurred_at else '',
                    'rule_name': v.rule.name if v.rule else (v.custom_title or 'Vi phạm nội quy'),
                    'rule_code': v.rule.code if v.rule else '',
                    'location': v.location or 'Khuôn viên trường',
                    'points_deducted': float(v.points_deducted),
                    'status': v.status,
                    'status_display': v.get_status_display(),
                }
                for v in own_violations[:20]
            ]
            data = {
                'scope': 'student',
                'profile_available': True,
                'student_name': student.full_name,
                'student_code': student.student_code,
                'student_class': student.school_class.name if student.school_class_id else '',
                'student_class_id': student.school_class_id,
                'room_number': student.school_class.room_number if student.school_class_id else '',
                'homeroom_teacher': student.school_class.homeroom_teacher.full_name if (student.school_class_id and student.school_class.homeroom_teacher) else 'Chưa phân công',
                'my_violations_count': own_violations.count(),
                'my_violations_verified': own_violations.filter(status__in=verified_statuses).count(),
                'my_violations_pending': own_violations.filter(status=ViolationRecord.STATUS_PENDING).count(),
                'my_violations_list': my_violations_list,
                'class_score_info': None,
                'user_role': user.role,
                'user_role_display': user.get_role_display(),
            }"""

if old_student_stats in views_norm:
    views_norm = views_norm.replace(old_student_stats, new_student_stats)
    print("SUCCESS: Updated student stats payload in core/views.py")
else:
    print("WARNING: old_student_stats not found in core/views.py")

with open(views_path, "w", encoding="utf-8") as f:
    f.write(views_norm)
print("Finished core/views.py")

# ==============================================================================
# 2. UPDATE competition/views.py
# ==============================================================================
comp_views_path = os.path.join(BASE_DIR, "competition", "views.py")
with open(comp_views_path, "r", encoding="utf-8") as f:
    comp_code = f.read()

comp_norm = comp_code.replace("\r\n", "\n")

# A. Deny ClassCompetitionScoreViewSet for students
old_comp_perm = """class ClassCompetitionScoreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ClassCompetitionScore.objects.all().select_related('competition_period', 'school_class')
    serializer_class = ClassCompetitionScoreSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)"""

new_comp_perm = """class ClassCompetitionScoreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ClassCompetitionScore.objects.all().select_related('competition_period', 'school_class')
    serializer_class = ClassCompetitionScoreSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if request.user.is_student or getattr(request.user, 'role', '') == 'HOC_SINH':
            self.permission_denied(request, message='Học sinh không có quyền truy cập bảng xếp hạng thi đua Chi đoàn.')"""

if old_comp_perm in comp_norm:
    comp_norm = comp_norm.replace(old_comp_perm, new_comp_perm)
    print("SUCCESS: Denied ClassCompetitionScoreViewSet for students in competition/views.py")
else:
    print("WARNING: old_comp_perm not found in competition/views.py")

# B. Deny competition dashboard snapshot for students
old_comp_dash = """    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        \"\"\"Shared, role-scoped competition snapshot for all role dashboards.\"\"\"
        user = request.user"""

new_comp_dash = """    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        \"\"\"Shared, role-scoped competition snapshot for all role dashboards.\"\"\"
        user = request.user
        if user.is_student or getattr(user, 'role', '') == 'HOC_SINH':
            return Response({'academic_year': None, 'periods': {}, 'classes': []})"""

if old_comp_dash in comp_norm:
    comp_norm = comp_norm.replace(old_comp_dash, new_comp_dash)
    print("SUCCESS: Guarded competition dashboard for students in competition/views.py")
else:
    print("WARNING: old_comp_dash not found in competition/views.py")

with open(comp_views_path, "w", encoding="utf-8") as f:
    f.write(comp_norm)
print("Finished competition/views.py")

# ==============================================================================
# 3. UPDATE conduct/views.py
# ==============================================================================
conduct_views_path = os.path.join(BASE_DIR, "conduct", "views.py")
with open(conduct_views_path, "r", encoding="utf-8") as f:
    cond_code = f.read()

cond_norm = cond_code.replace("\r\n", "\n")

# A. TeacherClassViewSet.list: Support student role to view their own class
old_tc_list = """        if user.is_admin or user.is_bgh or user.is_doan_truong:
            all_classes = SchoolClass.objects.filter(is_active=True).select_related('academic_year', 'homeroom_teacher')
            role_code = 'DOAN_TRUONG' if (user.is_doan_truong and not (user.is_admin or user.is_bgh)) else 'ADMIN'
            role_disp = 'Bí thư Đoàn trường' if (user.is_doan_truong and not (user.is_admin or user.is_bgh)) else 'Quản trị viên / Ban giám hiệu'
            for c in all_classes:
                classes_map[c.id] = {
                    'id': c.id,
                    'name': c.name,
                    'grade': c.grade,
                    'academic_year_name': c.academic_year.name if c.academic_year else '',
                    'student_count': c.students.filter(status='STUDYING').count() or c.student_count,
                    'assignment_role': role_code,
                    'assignment_role_display': role_disp,
                    'subjects': ['Toàn trường'],
                    'homeroom_teacher_name': c.homeroom_teacher.full_name if c.homeroom_teacher else 'Chưa phân công',
                    'homeroom_teacher_id': c.homeroom_teacher_id,
                }
        else:"""

new_tc_list = """        if user.is_admin or user.is_bgh or user.is_doan_truong:
            all_classes = SchoolClass.objects.filter(is_active=True).select_related('academic_year', 'homeroom_teacher')
            role_code = 'DOAN_TRUONG' if (user.is_doan_truong and not (user.is_admin or user.is_bgh)) else 'ADMIN'
            role_disp = 'Bí thư Đoàn trường' if (user.is_doan_truong and not (user.is_admin or user.is_bgh)) else 'Quản trị viên / Ban giám hiệu'
            for c in all_classes:
                classes_map[c.id] = {
                    'id': c.id,
                    'name': c.name,
                    'grade': c.grade,
                    'academic_year_name': c.academic_year.name if c.academic_year else '',
                    'student_count': c.students.filter(status='STUDYING').count() or c.student_count,
                    'assignment_role': role_code,
                    'assignment_role_display': role_disp,
                    'subjects': ['Toàn trường'],
                    'homeroom_teacher_name': c.homeroom_teacher.full_name if c.homeroom_teacher else 'Chưa phân công',
                    'homeroom_teacher_id': c.homeroom_teacher_id,
                }
        elif user.is_student or getattr(user, 'role', '') == 'HOC_SINH':
            student = getattr(user, 'student_profile', None)
            sclass = student.school_class if student else None
            if not sclass and user.department_or_class:
                sclass = SchoolClass.objects.filter(name__iexact=user.department_or_class.strip(), is_active=True).first()
            if sclass:
                classes_map[sclass.id] = {
                    'id': sclass.id,
                    'name': sclass.name,
                    'grade': sclass.grade,
                    'academic_year_name': sclass.academic_year.name if sclass.academic_year else '',
                    'student_count': sclass.students.filter(status='STUDYING').count() or sclass.student_count,
                    'assignment_role': 'HOC_SINH',
                    'assignment_role_display': f'Học sinh lớp {sclass.name}',
                    'subjects': ['Lớp học của tôi'],
                    'homeroom_teacher_name': sclass.homeroom_teacher.full_name if sclass.homeroom_teacher else 'Chưa phân công',
                    'homeroom_teacher_id': sclass.homeroom_teacher_id,
                }
        else:"""

if old_tc_list in cond_norm:
    cond_norm = cond_norm.replace(old_tc_list, new_tc_list)
    print("SUCCESS: Added student branch to TeacherClassViewSet.list in conduct/views.py")
else:
    print("WARNING: old_tc_list not found in conduct/views.py")

# B. TeacherClassViewSet.students: Allow student to view roster of their own class
old_tc_students = """        elif TeacherClassAssignment.objects.filter(school_class=school_class, teacher=user, is_active=True).exists():
            has_access = True"""

new_tc_students = """        elif TeacherClassAssignment.objects.filter(school_class=school_class, teacher=user, is_active=True).exists():
            has_access = True
        elif user.is_student or getattr(user, 'role', '') == 'HOC_SINH':
            student = getattr(user, 'student_profile', None)
            if student and student.school_class_id == school_class.id:
                has_access = True
            elif user.department_or_class and user.department_or_class.strip().lower() == school_class.name.strip().lower():
                has_access = True"""

if old_tc_students in cond_norm:
    cond_norm = cond_norm.replace(old_tc_students, new_tc_students)
    print("SUCCESS: Allowed student to access own class students in conduct/views.py")
else:
    print("WARNING: old_tc_students not found in conduct/views.py")

# C. TeacherClassViewSet.assigned_teachers: Allow student to view teachers of their own class, but guard other classes
old_assigned_teachers = """    @action(detail=True, methods=['get'], url_path='assigned-teachers')
    def assigned_teachers(self, request, pk=None):
        \"\"\"
        Lấy thông tin toàn bộ đội ngũ giáo viên của một lớp học:
        - Giáo viên chủ nhiệm (GVCN)
        - Toàn bộ Giáo viên bộ môn (GVBM) đang giảng dạy các môn
        \"\"\"
        sclass = get_object_or_404(SchoolClass, pk=pk)"""

new_assigned_teachers = """    @action(detail=True, methods=['get'], url_path='assigned-teachers')
    def assigned_teachers(self, request, pk=None):
        \"\"\"
        Lấy thông tin toàn bộ đội ngũ giáo viên của một lớp học:
        - Giáo viên chủ nhiệm (GVCN)
        - Toàn bộ Giáo viên bộ môn (GVBM) đang giảng dạy các môn
        \"\"\"
        sclass = get_object_or_404(SchoolClass, pk=pk)
        user = request.user
        has_access = False
        if user.is_admin or user.is_bgh or user.is_doan_truong:
            has_access = True
        elif sclass.homeroom_teacher_id == user.id:
            has_access = True
        elif HomeroomAssignment.objects.filter(school_class=sclass, teacher=user, is_active=True).exists():
            has_access = True
        elif TeacherClassAssignment.objects.filter(school_class=sclass, teacher=user, is_active=True).exists():
            has_access = True
        elif user.is_student or getattr(user, 'role', '') == 'HOC_SINH':
            student = getattr(user, 'student_profile', None)
            if student and student.school_class_id == sclass.id:
                has_access = True
            elif user.department_or_class and user.department_or_class.strip().lower() == sclass.name.strip().lower():
                has_access = True
        if not has_access:
            return Response({'error': 'Bạn không có quyền xem đội ngũ giáo viên của lớp học này.'}, status=status.HTTP_403_FORBIDDEN)"""

if old_assigned_teachers in cond_norm:
    cond_norm = cond_norm.replace(old_assigned_teachers, new_assigned_teachers)
    print("SUCCESS: Added RBAC to assigned_teachers in conduct/views.py")
else:
    print("WARNING: old_assigned_teachers not found in conduct/views.py")

# D. ViolationRecordViewSet: Block students from creating violations
old_viol_perm = """    def check_permissions(self, request):
        super().check_permissions(request)
        if self.action in ['update', 'partial_update', 'destroy'] and not (request.user.is_admin or request.user.is_superuser or request.user.is_doan_truong):
            self.permission_denied(request, message='Chỉ Quản trị viên hoặc Đoàn trường mới có thể chỉnh sửa hoặc xóa bản ghi vi phạm.')"""

new_viol_perm = """    def check_permissions(self, request):
        super().check_permissions(request)
        if self.action in ['update', 'partial_update', 'destroy'] and not (request.user.is_admin or request.user.is_superuser or request.user.is_doan_truong):
            self.permission_denied(request, message='Chỉ Quản trị viên hoặc Đoàn trường mới có thể chỉnh sửa hoặc xóa bản ghi vi phạm.')
        if self.action == 'create' and ((request.user.is_student or getattr(request.user, 'role', '') == 'HOC_SINH') and not request.user.is_active_red_star):
            self.permission_denied(request, message='Học sinh không có quyền lập biên bản vi phạm.')"""

if old_viol_perm in cond_norm:
    cond_norm = cond_norm.replace(old_viol_perm, new_viol_perm)
    print("SUCCESS: Blocked regular students from creating violation records in conduct/views.py")
else:
    print("WARNING: old_viol_perm not found in conduct/views.py")

# E. StudentFeedbackViewSet: For students, only return their own feedbacks
old_fb_filter = """        if user.is_admin or user.is_bgh or user.is_doan_truong:
            pass
        else:"""

new_fb_filter = """        if user.is_admin or user.is_bgh or user.is_doan_truong:
            pass
        elif user.is_student or getattr(user, 'role', '') == 'HOC_SINH':
            qs = qs.filter(student__user=user)
            return qs
        else:"""

if old_fb_filter in cond_norm:
    cond_norm = cond_norm.replace(old_fb_filter, new_fb_filter)
    print("SUCCESS: Restricted feedbacks to student self in conduct/views.py")
else:
    print("WARNING: old_fb_filter not found in conduct/views.py")

with open(conduct_views_path, "w", encoding="utf-8") as f:
    f.write(cond_norm)
print("Finished conduct/views.py")
