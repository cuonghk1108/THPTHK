# -*- coding: utf-8 -*-
import sys

VIEWS_CODE = '''

# =====================================================================
# MODULE: QUẢN LÝ LỚP HỌC VÀ PHẢN HỒI HỌC SINH DÀNH CHO GIÁO VIÊN
# =====================================================================

import unicodedata

VIETNAMESE_ALPHABET = "aàáảãạăằắẳẵặâầấẩẫậbcdđeèéẻẽẹêềếểễệghiìíỉĩịklmnoòóỏõọôồốổỗộơờớởỡợpqrstuùúủũụưừứửữựvxy"
VIETNAMESE_ORDER = {char: i for i, char in enumerate(VIETNAMESE_ALPHABET)}

def remove_vietnamese_accents(text):
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.replace('đ', 'd').replace('Đ', 'D')
    return text.lower()

def vietnamese_char_key(char):
    c = char.lower()
    return VIETNAMESE_ORDER.get(c, 1000 + ord(c))

def vietnamese_string_key(s):
    return [vietnamese_char_key(c) for c in s.strip()]

def get_vietnamese_sort_key(full_name):
    if not full_name:
        return ([], [])
    parts = full_name.strip().split()
    if not parts:
        return ([], [])
    first_name = parts[-1]
    rest_name = ' '.join(parts[:-1])
    return (vietnamese_string_key(first_name), vietnamese_string_key(rest_name))


class TeacherClassViewSet(viewsets.ViewSet):
    """
    API phục vụ GVCN và GVBM quản lý lớp học và học sinh được phân công.
    Tự động phân định danh sách lớp dựa trên dữ liệu phân công chính thức:
    - GVCN: SchoolClass.homeroom_teacher hoặc HomeroomAssignment đang hoạt động.
    - GVBM: TeacherClassAssignment đang hoạt động kèm môn học được phân công.
    - Admin/BGH: Toàn bộ danh sách lớp trong năm học.
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        user = request.user
        classes_map = {}

        if user.is_admin or user.is_bgh or user.is_doan_truong:
            all_classes = SchoolClass.objects.filter(is_active=True).select_related('academic_year', 'homeroom_teacher')
            for c in all_classes:
                classes_map[c.id] = {
                    'id': c.id,
                    'name': c.name,
                    'grade': c.grade,
                    'academic_year_name': c.academic_year.name if c.academic_year else '',
                    'student_count': c.students.filter(status='STUDYING').count() or c.student_count,
                    'assignment_role': 'ADMIN',
                    'assignment_role_display': 'Quản trị viên / Ban giám hiệu',
                    'subjects': ['Toàn trường'],
                    'homeroom_teacher_name': c.homeroom_teacher.full_name if c.homeroom_teacher else 'Chưa phân công',
                }
        else:
            # 1. Homeroom assignments
            homeroom_classes = SchoolClass.objects.filter(
                Q(homeroom_teacher=user) | Q(homeroom_assignments__teacher=user, homeroom_assignments__is_active=True),
                is_active=True
            ).distinct().select_related('academic_year', 'homeroom_teacher')

            for c in homeroom_classes:
                classes_map[c.id] = {
                    'id': c.id,
                    'name': c.name,
                    'grade': c.grade,
                    'academic_year_name': c.academic_year.name if c.academic_year else '',
                    'student_count': c.students.filter(status='STUDYING').count() or c.student_count,
                    'assignment_role': 'GVCN',
                    'assignment_role_display': 'Giáo viên chủ nhiệm',
                    'subjects': ['Chủ nhiệm'],
                    'homeroom_teacher_name': user.full_name or user.username,
                }

            # 2. Teaching assignments (GVBM)
            teaching_assignments = TeacherClassAssignment.objects.filter(
                teacher=user, is_active=True, school_class__is_active=True
            ).select_related('school_class__academic_year', 'school_class__homeroom_teacher')

            for ta in teaching_assignments:
                c = ta.school_class
                if c.id in classes_map:
                    if ta.subject not in classes_map[c.id]['subjects']:
                        classes_map[c.id]['subjects'].append(ta.subject)
                else:
                    classes_map[c.id] = {
                        'id': c.id,
                        'name': c.name,
                        'grade': c.grade,
                        'academic_year_name': c.academic_year.name if c.academic_year else '',
                        'student_count': c.students.filter(status='STUDYING').count() or c.student_count,
                        'assignment_role': 'GVBM',
                        'assignment_role_display': 'Giáo viên bộ môn',
                        'subjects': [ta.subject],
                        'homeroom_teacher_name': c.homeroom_teacher.full_name if c.homeroom_teacher else 'Chưa phân công',
                    }

        res = list(classes_map.values())
        res.sort(key=lambda x: (x['grade'], x['name']))
        serializer = TeacherAssignedClassSerializer(res, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='students')
    def students(self, request, pk=None):
        user = request.user
        school_class = get_object_or_404(SchoolClass, pk=pk)

        # RBAC Check: Ensure teacher is assigned or admin
        has_access = False
        if user.is_admin or user.is_bgh or user.is_doan_truong:
            has_access = True
        elif school_class.homeroom_teacher_id == user.id:
            has_access = True
        elif HomeroomAssignment.objects.filter(school_class=school_class, teacher=user, is_active=True).exists():
            has_access = True
        elif TeacherClassAssignment.objects.filter(school_class=school_class, teacher=user, is_active=True).exists():
            has_access = True

        if not has_access:
            return Response(
                {'error': 'Bạn không có quyền truy cập danh sách học sinh của lớp học này.'},
                status=status.HTTP_403_FORBIDDEN
            )

        students_qs = Student.objects.filter(school_class=school_class)

        status_filter = request.query_params.get('status')
        if status_filter:
            students_qs = students_qs.filter(status=status_filter)

        fb_counts = dict(
            StudentFeedback.objects.filter(school_class=school_class)
            .values('student_id')
            .annotate(cnt=models.Count('id'))
            .values_list('student_id', 'cnt')
        )

        search_query = request.query_params.get('search', '').strip()
        search_norm = remove_vietnamese_accents(search_query) if search_query else ''

        students_list = []
        for s in students_qs:
            if search_query:
                code_match = search_query.lower() in s.student_code.lower()
                name_match = (search_query.lower() in s.full_name.lower()) or (search_norm and search_norm in remove_vietnamese_accents(s.full_name))
                if not (code_match or name_match):
                    continue

            students_list.append({
                'id': s.id,
                'student_code': s.student_code,
                'full_name': s.full_name,
                'gender': s.gender,
                'gender_display': s.get_gender_display(),
                'date_of_birth': s.date_of_birth.strftime('%d/%m/%Y') if s.date_of_birth else '',
                'status': s.status,
                'status_display': s.get_status_display(),
                'feedback_count': fb_counts.get(s.id, 0),
            })

        students_list.sort(key=lambda item: get_vietnamese_sort_key(item['full_name']))

        for idx, item in enumerate(students_list, start=1):
            item['stt'] = idx

        return Response({
            'class_id': school_class.id,
            'class_name': school_class.name,
            'grade': school_class.grade,
            'total_students': len(students_list),
            'students': students_list
        })


class StudentFeedbackViewSet(viewsets.ModelViewSet):
    """
    Quản lý phản hồi học sinh dành cho GVCN và GVBM.
    """
    serializer_class = StudentFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = StudentFeedback.objects.select_related('student', 'school_class', 'teacher').prefetch_related('replies__author')

        if user.is_admin or user.is_bgh or user.is_doan_truong:
            pass
        else:
            homeroom_ids = set(SchoolClass.objects.filter(homeroom_teacher=user).values_list('id', flat=True))
            homeroom_ids.update(HomeroomAssignment.objects.filter(teacher=user, is_active=True).values_list('school_class_id', flat=True))

            teaching_ids = set(TeacherClassAssignment.objects.filter(teacher=user, is_active=True).values_list('school_class_id', flat=True))

            cond_my_feedbacks = Q(teacher=user)
            cond_gvcn_feedbacks = Q(school_class_id__in=homeroom_ids)
            cond_gvbm_feedbacks = Q(
                school_class_id__in=teaching_ids,
                visibility_scope__in=[StudentFeedback.SCOPE_HOMEROOM_AND_TEACHERS, StudentFeedback.SCOPE_PARENTS_PUBLIC]
            )

            qs = qs.filter(cond_my_feedbacks | cond_gvcn_feedbacks | cond_gvbm_feedbacks).distinct()

        class_id = self.request.query_params.get('class_id')
        student_id = self.request.query_params.get('student_id')
        feedback_type = self.request.query_params.get('feedback_type')
        priority = self.request.query_params.get('priority')
        status_param = self.request.query_params.get('status')
        my_sent = self.request.query_params.get('my_sent')

        if class_id:
            qs = qs.filter(school_class_id=class_id)
        if student_id:
            qs = qs.filter(student_id=student_id)
        if feedback_type:
            qs = qs.filter(feedback_type=feedback_type)
        if priority:
            qs = qs.filter(priority=priority)
        if status_param:
            qs = qs.filter(status=status_param)
        if my_sent == 'true':
            qs = qs.filter(teacher=user)

        return qs.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        user = request.user
        student_id = request.data.get('student_id')
        content = request.data.get('content', '').strip()
        feedback_type = request.data.get('feedback_type', StudentFeedback.TYPE_ATTITUDE)
        priority = request.data.get('priority', StudentFeedback.PRIORITY_NORMAL)
        visibility_scope = request.data.get('visibility_scope', StudentFeedback.SCOPE_HOMEROOM_AND_TEACHERS)
        strengths = request.data.get('strengths', '').strip()
        weaknesses = request.data.get('weaknesses', '').strip()
        cooperation_proposal = request.data.get('cooperation_proposal', '').strip()
        subject = request.data.get('subject', '').strip()

        if not student_id:
            return Response({'error': 'Vui lòng chọn học sinh.'}, status=status.HTTP_400_BAD_REQUEST)
        if not content:
            return Response({'error': 'Nội dung phản hồi không được để trống.'}, status=status.HTTP_400_BAD_REQUEST)

        student = get_object_or_404(Student, pk=student_id)
        school_class = student.school_class

        # RBAC Check: Is teacher assigned to this student/class or admin?
        has_access = False
        teacher_role = 'GVBM'

        if user.is_admin or user.is_bgh or user.is_doan_truong:
            has_access = True
            teacher_role = 'ADMIN'
        elif school_class.homeroom_teacher_id == user.id or HomeroomAssignment.objects.filter(school_class=school_class, teacher=user, is_active=True).exists():
            has_access = True
            teacher_role = 'GVCN'
        else:
            teaching_assignment = TeacherClassAssignment.objects.filter(school_class=school_class, teacher=user, is_active=True).first()
            if teaching_assignment:
                has_access = True
                teacher_role = 'GVBM'
                if not subject:
                    subject = teaching_assignment.subject

        if not has_access:
            return Response(
                {'error': 'Bạn không có quyền gửi phản hồi cho học sinh thuộc lớp này.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Duplicate submission check (within 30 seconds)
        recent_threshold = timezone.now() - timezone.timedelta(seconds=30)
        is_duplicate = StudentFeedback.objects.filter(
            teacher=user,
            student=student,
            content=content,
            created_at__gte=recent_threshold
        ).exists()
        if is_duplicate:
            return Response(
                {'error': 'Phản hồi tương tự đã được gửi gần đây. Vui lòng không gửi lặp.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        feedback = StudentFeedback.objects.create(
            student=student,
            student_name_snapshot=student.full_name,
            school_class=school_class,
            class_name_snapshot=school_class.name,
            teacher=user,
            teacher_role=teacher_role,
            subject=subject,
            feedback_type=feedback_type,
            priority=priority,
            visibility_scope=visibility_scope,
            content=content,
            strengths=strengths,
            weaknesses=weaknesses,
            cooperation_proposal=cooperation_proposal,
            status=StudentFeedback.STATUS_SENT,
        )

        AuditLog.objects.create(
            user=user,
            action='CREATE_STUDENT_FEEDBACK',
            resource_type='STUDENT_FEEDBACK',
            resource_id=feedback.feedback_code,
            details=f"{user.username} đã gửi phản hồi cho học sinh {student.full_name} ({school_class.name}) - Loại: {feedback.get_feedback_type_display()}",
            ip_address=request.META.get('REMOTE_ADDR')
        )

        # In-app notifications to relevant recipients (safe execution)
        try:
            from core.models import Notification
            if teacher_role == 'GVBM':
                homeroom_user = school_class.homeroom_teacher
                if not homeroom_user:
                    active_hr = HomeroomAssignment.objects.filter(school_class=school_class, is_active=True).first()
                    if active_hr:
                        homeroom_user = active_hr.teacher
                
                if homeroom_user and homeroom_user != user:
                    Notification.objects.create(
                        recipient=homeroom_user,
                        notification_type=Notification.TYPE_CONDUCT,
                        title=f"Phản hồi mới về học sinh {student.full_name} ({school_class.name})",
                        message=f"Thầy/Cô {user.full_name or user.username} ({subject or 'Bộ môn'}) vừa gửi phản hồi về học sinh {student.full_name}. Mức độ: {feedback.get_priority_display()}.",
                        link="/#teacher-classes"
                    )
            elif teacher_role == 'GVCN':
                if subject:
                    gvbm_assignment = TeacherClassAssignment.objects.filter(
                        school_class=school_class, subject=subject, is_active=True
                    ).first()
                    if gvbm_assignment and gvbm_assignment.teacher != user:
                        Notification.objects.create(
                            recipient=gvbm_assignment.teacher,
                            notification_type=Notification.TYPE_CONDUCT,
                            title=f"GVCN trao đổi về học sinh {student.full_name} ({school_class.name})",
                            message=f"GVCN {user.full_name or user.username} vừa gửi phản hồi liên quan đến môn {subject}.",
                            link="/#teacher-classes"
                        )
        except Exception:
            pass

        serializer = self.get_serializer(feedback)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='mark-seen')
    def mark_seen(self, request, pk=None):
        feedback = self.get_object()
        user = request.user

        if user not in feedback.seen_by.all():
            feedback.seen_by.add(user)

        if not feedback.seen_at:
            feedback.seen_at = timezone.now()

        if user != feedback.teacher and feedback.status == StudentFeedback.STATUS_SENT:
            feedback.status = StudentFeedback.STATUS_SEEN
            feedback.save(update_fields=['status', 'seen_at'])

        return Response(self.get_serializer(feedback).data)

    @action(detail=True, methods=['post'], url_path='reply')
    def reply(self, request, pk=None):
        feedback = self.get_object()
        user = request.user
        content = request.data.get('content', '').strip()

        if not content:
            return Response({'error': 'Nội dung trao đổi không được để trống.'}, status=status.HTTP_400_BAD_REQUEST)

        school_class = feedback.school_class
        author_role = 'GVBM'
        if user.is_admin or user.is_bgh or user.is_doan_truong:
            author_role = 'BGH / Quản lý'
        elif school_class.homeroom_teacher_id == user.id or HomeroomAssignment.objects.filter(school_class=school_class, teacher=user, is_active=True).exists():
            author_role = 'GVCN'
        elif user == feedback.teacher:
            author_role = feedback.teacher_role

        reply_obj = StudentFeedbackReply.objects.create(
            feedback=feedback,
            author=user,
            author_role=author_role,
            content=content
        )

        if feedback.status in [StudentFeedback.STATUS_SENT, StudentFeedback.STATUS_SEEN]:
            feedback.status = StudentFeedback.STATUS_PROCESSING
            feedback.save(update_fields=['status', 'updated_at'])

        try:
            from core.models import Notification
            target_recipient = None
            if user == feedback.teacher:
                target_recipient = school_class.homeroom_teacher
                if not target_recipient:
                    hr = HomeroomAssignment.objects.filter(school_class=school_class, is_active=True).first()
                    if hr:
                        target_recipient = hr.teacher
            else:
                target_recipient = feedback.teacher

            if target_recipient and target_recipient != user:
                Notification.objects.create(
                    recipient=target_recipient,
                    notification_type=Notification.TYPE_CONDUCT,
                    title=f"Trao đổi mới về học sinh {feedback.student_name_snapshot}",
                    message=f"Thầy/Cô {user.full_name or user.username} ({author_role}) vừa trả lời phản hồi mã [{feedback.feedback_code}].",
                    link="/#teacher-classes"
                )
        except Exception:
            pass

        return Response(self.get_serializer(feedback).data)

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        feedback = self.get_object()
        user = request.user
        new_status = request.data.get('status')

        valid_statuses = dict(StudentFeedback.STATUS_CHOICES).keys()
        if new_status not in valid_statuses:
            return Response({'error': 'Trạng thái không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

        is_homeroom = (feedback.school_class.homeroom_teacher_id == user.id) or HomeroomAssignment.objects.filter(school_class=feedback.school_class, teacher=user, is_active=True).exists()
        is_author = (feedback.teacher_id == user.id)
        is_admin = (user.is_admin or user.is_bgh or user.is_doan_truong)

        if not (is_homeroom or is_author or is_admin):
            return Response({'error': 'Bạn không có quyền thay đổi trạng thái phản hồi này.'}, status=status.HTTP_403_FORBIDDEN)

        feedback.status = new_status
        feedback.save(update_fields=['status', 'updated_at'])

        AuditLog.objects.create(
            user=user,
            action='UPDATE_FEEDBACK_STATUS',
            resource_type='STUDENT_FEEDBACK',
            resource_id=feedback.feedback_code,
            details=f"{user.username} đã cập nhật trạng thái phản hồi {feedback.feedback_code} thành {feedback.get_status_display()}.",
            ip_address=request.META.get('REMOTE_ADDR')
        )

        return Response(self.get_serializer(feedback).data)
'''

target_path = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\conduct\views.py'
with open(target_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
if 'StudentFeedback' not in content:
    content = content.replace(
        'RedStarAssignment, RedStarReport,',
        'RedStarAssignment, RedStarReport,\n    StudentFeedback, StudentFeedbackReply,'
    )
    content = content.replace(
        'RedStarAssignmentSerializer, RedStarReportSerializer,',
        'RedStarAssignmentSerializer, RedStarReportSerializer,\n    StudentFeedbackSerializer, StudentFeedbackReplySerializer, TeacherAssignedClassSerializer,'
    )

# 2. Update SchoolClassViewSet.get_queryset for GVCN & GVBM
old_schoolclass_get_qs = """        elif user.is_gvcn:
            qs = qs.filter(homeroom_teacher=user)"""

new_schoolclass_get_qs = """        elif user.is_gvcn or user.is_gvbm or user.role in [User.ROLE_GVCN, User.ROLE_GVBM]:
            homeroom_ids = list(HomeroomAssignment.objects.filter(teacher=user, is_active=True).values_list('school_class_id', flat=True))
            teaching_ids = list(TeacherClassAssignment.objects.filter(teacher=user, is_active=True).values_list('school_class_id', flat=True))
            qs = qs.filter(Q(homeroom_teacher=user) | Q(id__in=homeroom_ids) | Q(id__in=teaching_ids)).distinct()"""

if old_schoolclass_get_qs in content:
    content = content.replace(old_schoolclass_get_qs, new_schoolclass_get_qs)

# 3. Update StudentViewSet.get_queryset for GVCN & GVBM
old_student_get_qs = """        elif user.is_gvcn:
            qs = qs.filter(school_class__homeroom_teacher=user)"""

new_student_get_qs = """        elif user.is_gvcn or user.is_gvbm or user.role in [User.ROLE_GVCN, User.ROLE_GVBM]:
            homeroom_ids = list(HomeroomAssignment.objects.filter(teacher=user, is_active=True).values_list('school_class_id', flat=True))
            teaching_ids = list(TeacherClassAssignment.objects.filter(teacher=user, is_active=True).values_list('school_class_id', flat=True))
            qs = qs.filter(Q(school_class__homeroom_teacher=user) | Q(school_class_id__in=homeroom_ids) | Q(school_class_id__in=teaching_ids)).distinct()"""

if old_student_get_qs in content:
    content = content.replace(old_student_get_qs, new_student_get_qs)

# 4. Add profile_detail action to StudentViewSet if not present
profile_detail_code = '''
    @action(detail=True, methods=['get'], url_path='profile-detail')
    def profile_detail(self, request, pk=None):
        student = self.get_object()
        user = request.user

        general_info = {
            'id': student.id,
            'student_code': student.student_code,
            'full_name': student.full_name,
            'date_of_birth': student.date_of_birth.strftime('%d/%m/%Y') if student.date_of_birth else '',
            'gender': student.gender,
            'gender_display': student.get_gender_display(),
            'school_class_id': student.school_class_id,
            'school_class_name': student.school_class.name,
            'grade': student.school_class.grade,
            'room_number': student.school_class.room_number,
            'homeroom_teacher_name': student.school_class.homeroom_teacher.full_name if student.school_class.homeroom_teacher else 'Chưa phân công',
            'status': student.status,
            'status_display': student.get_status_display(),
            'is_union_member': student.is_union_member,
            'is_red_star': student.is_red_star,
        }

        feedback_qs = StudentFeedback.objects.filter(student=student).select_related('teacher', 'school_class').prefetch_related('replies__author')
        if not (user.is_admin or user.is_bgh or user.is_doan_truong):
            is_homeroom = (student.school_class.homeroom_teacher_id == user.id) or HomeroomAssignment.objects.filter(school_class=student.school_class, teacher=user, is_active=True).exists()
            if is_homeroom:
                pass
            else:
                is_teaching = TeacherClassAssignment.objects.filter(school_class=student.school_class, teacher=user, is_active=True).exists()
                if is_teaching:
                    feedback_qs = feedback_qs.filter(Q(teacher=user) | ~Q(visibility_scope=StudentFeedback.SCOPE_HOMEROOM_ONLY))
                else:
                    feedback_qs = feedback_qs.filter(teacher=user)

        feedbacks_data = StudentFeedbackSerializer(feedback_qs, many=True).data

        violations_qs = ViolationRecord.objects.filter(
            student=student
        ).select_related('rule', 'reporter').order_by('-occurred_at')
        violations_data = [
            {
                'id': v.id,
                'record_code': v.record_code,
                'occurred_at': v.occurred_at.strftime('%d/%m/%Y %H:%M') if v.occurred_at else '',
                'rule_code': v.rule.code if v.rule else '',
                'rule_name': v.rule.name if v.rule else v.custom_title,
                'points_deducted': v.points_deducted,
                'status': v.status,
                'status_display': v.get_status_display(),
                'location': v.location,
                'reporter_name': v.reporter.full_name if v.reporter else 'Hệ thống',
            }
            for v in violations_qs[:30]
        ]

        competition_data = {
            'class_name': student.school_class.name,
            'grade': student.school_class.grade,
            'total_violations_count': violations_qs.count(),
            'total_points_deducted': sum(v.points_deducted for v in violations_qs if v.status in ['VERIFIED', 'RESOLVED']),
        }

        return Response({
            'general': general_info,
            'feedbacks': feedbacks_data,
            'violations': violations_data,
            'competition': competition_data,
        })
'''

if 'def profile_detail(' not in content:
    target_pos = content.find("class ConductRuleCategoryViewSet")
    if target_pos != -1:
        content = content[:target_pos] + profile_detail_code + "\n\n" + content[target_pos:]

# 5. Append new ViewSets at the end
if 'class TeacherClassViewSet(' not in content:
    content += "\n" + VIEWS_CODE

with open(target_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: conduct/views.py successfully updated with TeacherClassViewSet and StudentFeedbackViewSet!")
