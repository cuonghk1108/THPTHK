from django.shortcuts import get_object_or_404



from datetime import timedelta



from decimal import Decimal



from collections.abc import Mapping



import hmac



import re



from secrets import token_urlsafe



from uuid import UUID







from django.conf import settings



from django.db import transaction



from django.db.models import Count, Q, Sum



from django.utils.dateparse import parse_date, parse_datetime



from django.utils import timezone



from django.views.decorators.csrf import csrf_exempt



from rest_framework import viewsets, permissions, status



from rest_framework.decorators import action, api_view, permission_classes



from rest_framework.response import Response



from rest_framework.permissions import AllowAny, IsAuthenticated



from django.core.validators import validate_email, ValidationError



from core.models import User, AuditLog, SystemSetting, ApprovalLog



from .models import (



    natural_class_sort_key,



    SchoolClass, Student, Teacher, ConductRuleCategory, ConductRule,



    ViolationRecord, ViolationEmailNotification,



    TeacherClassAssignment, HomeroomAssignment,



    TeacherReflection, ReflectionHistory,



    RedStarAssignment, RedStarReport,



    StudentFeedback, StudentFeedbackReply,



)



from .email import (



    get_eligible_union_recipients,



    get_school_union_notification_email,



    send_test_union_email,



    dispatch_email_async,



)



from .serializers import (



    SchoolClassSerializer, StudentSerializer, ConductRuleCategorySerializer,



    ConductRuleSerializer, ViolationRecordSerializer,



    ViolationEmailNotificationSerializer,



    TeacherClassAssignmentSerializer, HomeroomAssignmentSerializer,



    TeacherReflectionSerializer, ReflectionHistorySerializer,



    RedStarAssignmentSerializer, RedStarReportSerializer,



    StudentFeedbackSerializer, StudentFeedbackReplySerializer, TeacherAssignedClassSerializer,



)



from .services import (



    create_violation_record, verify_violation, submit_violation_appeal,



    can_user_deduct_directly, adjust_or_undo_violation, get_class_score_snapshot



)











class SchoolClassViewSet(viewsets.ReadOnlyModelViewSet):
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

class StudentViewSet(viewsets.ReadOnlyModelViewSet):
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

    @action(detail=True, methods=['get'], url_path='profile-detail')



    def profile_detail(self, request, pk=None):



        student = self.get_object()



        user = request.user
        if (user.is_student or getattr(user, 'role', '') == 'HOC_SINH') and student.user_id != user.id:
            return Response({'error': 'Học sinh chỉ có quyền xem hồ sơ và lỗi vi phạm của bản thân.'}, status=status.HTTP_403_FORBIDDEN)







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







        if user.is_student or getattr(user, 'role', '') == 'HOC_SINH':
            competition_data = {}
        return Response({



            'general': general_info,



            'feedbacks': feedbacks_data,



            'violations': violations_data,



            'competition': competition_data,



        })











class ConductRuleCategoryViewSet(viewsets.ReadOnlyModelViewSet):



    queryset = ConductRuleCategory.objects.all().order_by('order', 'id')



    serializer_class = ConductRuleCategorySerializer



    permission_classes = [permissions.IsAuthenticated]







    def check_permissions(self, request):



        super().check_permissions(request)











class ConductRuleViewSet(viewsets.ModelViewSet):



    queryset = ConductRule.objects.all().select_related('category')



    serializer_class = ConductRuleSerializer



    permission_classes = [permissions.IsAuthenticated]







    def check_permissions(self, request):



        super().check_permissions(request)



        if self.action not in ['list', 'retrieve'] and not (request.user.is_admin or request.user.is_superuser or request.user.is_doan_truong):



            self.permission_denied(request, message='Chỉ Quản trị viên hoặc Đoàn trường mới có thể thay đổi nội quy.')
        if self.action == 'create' and ((request.user.is_student or getattr(request.user, 'role', '') == 'HOC_SINH') and not getattr(request.user, 'is_active_red_star', False)):
            self.permission_denied(request, message='Học sinh không có quyền lập biên bản vi phạm.')







    def get_queryset(self):



        qs = super().get_queryset()



        category_id = self.request.query_params.get('category_id')



        if category_id:



            qs = qs.filter(category_id=category_id)







        is_active = self.request.query_params.get('is_active')



        if is_active is not None:



            if is_active.lower() in ['true', '1']:



                qs = qs.filter(is_active=True)



            elif is_active.lower() in ['false', '0']:



                qs = qs.filter(is_active=False)



        elif not self.request.query_params.get('all'):



            # Mặc định chỉ trả về các quy tắc đang áp dụng cho dropdown chọn vi phạm



            qs = qs.filter(is_active=True)







        return qs.order_by('category__order', 'code')











class ViolationRecordViewSet(viewsets.ModelViewSet):



    queryset = ViolationRecord.objects.all().select_related(



        'school_class', 'student', 'rule', 'rule__category', 'reporter',



        'verified_by',



    ).prefetch_related(



        'email_notifications',



        'reviews__performed_by',



    )



    serializer_class = ViolationRecordSerializer



    permission_classes = [permissions.IsAuthenticated]







    def check_permissions(self, request):



        super().check_permissions(request)



        if self.action in ['update', 'partial_update', 'destroy'] and not (request.user.is_admin or request.user.is_superuser or request.user.is_doan_truong):



            self.permission_denied(request, message='Chỉ Quản trị viên hoặc Đoàn trường mới có thể chỉnh sửa hoặc xóa bản ghi vi phạm.')







    def get_queryset(self):



        user = self.request.user



        qs = super().get_queryset()







        # Áp dụng bộ lọc quyền hạn (Object-Level RBAC)



        if user.is_admin or user.is_bgh or user.is_doan_truong:



            pass



        elif user.is_gvcn:



            # GVCN chỉ thấy vi phạm của lớp mình chủ nhiệm



            homeroom_classes = user.homeroom_classes.all()



            qs = qs.filter(school_class__in=homeroom_classes)

        elif user.is_student:
            if hasattr(user, 'student_profile'):
                student = user.student_profile
                if getattr(student, 'is_class_monitor', False) or (student.school_class and student.school_class.monitor_id == student.id):
                    # Lớp trưởng được xem toàn bộ vi phạm của lớp mình để khiếu nại những lỗi sai của lớp
                    qs = qs.filter(school_class=student.school_class)
                else:
                    # Học sinh bình thường CHỈ thấy vi phạm của bản thân mình
                    qs = qs.filter(student=student)
            else:
                qs = qs.none()



        elif user.is_active_red_star:



            # Sao đỏ thấy các vi phạm do mình lập hoặc các vi phạm đã công bố



            qs = qs.filter(Q(reporter=user) | Q(status__in=[ViolationRecord.STATUS_VERIFIED, ViolationRecord.STATUS_ADJUSTED]))



        elif user.is_gvbm:



            qs = qs.filter(reporter=user)



        else:



            qs = qs.none()







        # Bộ lọc URL parameters



        class_id = self.request.query_params.get('class_id')



        status_filter = self.request.query_params.get('status')



        date_from = self.request.query_params.get('date_from')



        date_to = self.request.query_params.get('date_to')



        student_id = self.request.query_params.get('student_id')



        reporter_id = self.request.query_params.get('reporter_id')



        reporter_role = self.request.query_params.get('reporter_role')



        rule_id = self.request.query_params.get('rule_id')



        search = self.request.query_params.get('search')







        if class_id:



            qs = qs.filter(school_class_id=class_id)



        if status_filter:



            qs = qs.filter(status=status_filter)



        if student_id:



            qs = qs.filter(student_id=student_id)



        if reporter_id:



            qs = qs.filter(reporter_id=reporter_id)



        if reporter_role:



            qs = qs.filter(reporter__role=reporter_role)



        if rule_id:



            qs = qs.filter(rule_id=rule_id)



        if date_from:



            qs = qs.filter(occurred_at__date__gte=date_from)



        if date_to:



            qs = qs.filter(occurred_at__date__lte=date_to)



        if search:



            qs = qs.filter(



                Q(record_code__icontains=search)



                | Q(student_name_snapshot__icontains=search)



                | Q(reporter__full_name__icontains=search)



                | Q(reporter__username__icontains=search)



                | Q(rule__name__icontains=search)



            )







        return qs







    def create(self, request, *args, **kwargs):



        """



        Quy trình ghi nhận vi phạm:



        - Admin / người được phân quyền chuyên biệt: Trừ điểm thi đua trực tiếp.



        - Sao đỏ / vai trò thông thường: Gửi bản ghi chờ xác minh.



        - Học sinh: Bị chặn hoàn toàn (403).



        """



        # Kiểm tra học sinh thông thường không có chức danh Sao đỏ



        is_student_user = (request.user.role == User.ROLE_HOC_SINH or getattr(request.user, 'is_student', False))



        is_active_sao_do = getattr(request.user, 'is_active_red_star', False)







        if is_student_user and not is_active_sao_do:



            return Response({'error': 'Học sinh không có quyền ghi nhận vi phạm nền nếp.'}, status=status.HTTP_403_FORBIDDEN)







        # Kiểm tra tài khoản chưa được phê duyệt



        if request.user.account_status != User.STATUS_APPROVED:



            return Response({'error': 'Tài khoản chưa được phê duyệt, không thể thực hiện thao tác này.'}, status=status.HTTP_403_FORBIDDEN)















        class_id = request.data.get('school_class') or request.data.get('class_id')



        student_id = request.data.get('student') or request.data.get('student_id')



        rule_id = request.data.get('rule')



        location = request.data.get('location', 'Khuôn viên trường')



        description = request.data.get('description', '')



        occurred_at_raw = request.data.get('occurred_at')



        evidence_image = request.FILES.get('evidence_image')



        evidence_notes = request.data.get('evidence_notes', '')



        raw_submission_key = request.data.get('submission_key')







        # QUY TẮC QUAN TRỌNG: Giáo viên bộ môn (GVBM) chỉ có quyền gửi phản ánh



        if request.user.role == User.ROLE_GVBM and not (request.user.is_admin or request.user.is_superuser):



            return Response(



                {'error': 'Giáo viên bộ môn chỉ có quyền gửi phản ánh nền nếp, không có quyền trực tiếp lập báo cáo trừ điểm thi đua.'},



                status=status.HTTP_403_FORBIDDEN



            )







        direct_requested = str(request.data.get('direct_deduct', '')).lower() in ['true', '1', 'yes']



        if is_active_sao_do and direct_requested:



            return Response(



                {'error': 'Sao đỏ chưa được cấp quyền trừ điểm trực tiếp.'},



                status=status.HTTP_403_FORBIDDEN



            )







        can_report = (



            request.user.is_admin



            or request.user.is_bgh



            or request.user.is_doan_truong



            or request.user.role == User.ROLE_DOAN_TRUONG



            or is_active_sao_do



            or request.user.is_gvcn



            or request.user.can_verify_violations



        )



        if not can_report:



            return Response({'error': 'Tài khoản của bạn chưa được cấp quyền báo cáo vi phạm.'}, status=status.HTTP_403_FORBIDDEN)







        # Kiểm tra phạm vi nhiệm vụ của Sao đỏ



        if is_active_sao_do and not (request.user.is_admin or request.user.is_doan_truong):



            today = timezone.now().date()



            active_assignments = request.user.red_star_assignments.filter(



                status=RedStarAssignment.STATUS_ACTIVE,



                start_date__lte=today



            ).filter(



                Q(end_date__isnull=True) | Q(end_date__gte=today)



            )



            if not active_assignments.exists():



                return Response({'error': 'Nhiệm vụ Sao đỏ của bạn đã hết hạn hoặc bị thu hồi.'}, status=status.HTTP_403_FORBIDDEN)







            target_class = SchoolClass.objects.filter(id=class_id).first()



            if target_class and active_assignments.exists():



                in_scope = any(asgn.can_cover_class(target_class) for asgn in active_assignments)



                if not in_scope:



                    return Response(



                        {'error': 'Học sinh Sao đỏ chỉ được ghi nhận vi phạm trong phạm vi lớp/khối/khu vực được phân công.'},



                        status=status.HTTP_400_BAD_REQUEST



                    )







        # Sao đỏ TUYỆT ĐỐI không được trừ điểm trực tiếp



        if is_active_sao_do and not (request.user.is_admin or request.user.is_doan_truong):



            is_direct = False



        else:



            raw_direct = request.data.get('direct_deduct')



            if raw_direct is not None:



                is_direct = str(raw_direct).lower() in ['true', '1']



                if is_direct and not can_user_deduct_directly(request.user):



                    return Response({'error': 'Tài khoản của bạn chưa được cấp quyền trừ điểm thi đua trực tiếp.'}, status=status.HTTP_403_FORBIDDEN)



            else:



                is_direct = can_user_deduct_directly(request.user)







        try:



            submission_key = UUID(str(raw_submission_key)) if raw_submission_key else None



        except (ValueError, TypeError, AttributeError):



            return Response({'error': 'Mã gửi báo cáo không hợp lệ; vui lòng tải lại biểu mẫu.'}, status=status.HTTP_400_BAD_REQUEST)







        if not class_id or not rule_id:



            return Response({'error': 'Vui lòng chọn lớp học và lỗi vi phạm'}, status=status.HTTP_400_BAD_REQUEST)







        if occurred_at_raw:



            occurred_at = parse_datetime(str(occurred_at_raw))



            if occurred_at is None:



                return Response({'error': 'Thời gian vi phạm không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)



            if timezone.is_naive(occurred_at):



                occurred_at = timezone.make_aware(occurred_at, timezone.get_current_timezone())



        else:



            occurred_at = timezone.now()







        if occurred_at > timezone.now() + timedelta(minutes=5):



            return Response(



                {'error': 'Thời gian xảy ra vi phạm không thể ở tương lai. Vui lòng ghi nhận thời gian thực.'},



                status=status.HTTP_400_BAD_REQUEST



            )







        if not SchoolClass.objects.filter(pk=class_id).exists() or not ConductRule.objects.filter(pk=rule_id).exists():



            return Response({'error': 'Lớp hoặc lỗi vi phạm không tồn tại.'}, status=status.HTTP_400_BAD_REQUEST)



        if student_id and not Student.objects.filter(pk=student_id, school_class_id=class_id).exists():



            return Response({'error': 'Học sinh không thuộc lớp đã chọn.'}, status=status.HTTP_400_BAD_REQUEST)







        try:



            violation = create_violation_record(



                reporter=request.user,



                class_id=class_id,



                rule_id=rule_id,



                student_id=student_id if student_id else None,



                occurred_at=occurred_at,



                location=location,



                description=description,



                evidence_image=evidence_image,



                evidence_notes=evidence_notes,



                submission_key=submission_key,



                direct_deduct=is_direct,



            )



        except PermissionError as pe:



            return Response({'error': str(pe)}, status=status.HTTP_403_FORBIDDEN)



        except ValueError as ve:



            return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)







        serializer = self.get_serializer(violation)



        response_data = dict(serializer.data)



        response_data['score_before'] = float(violation.score_before) if violation.score_before is not None else None



        response_data['score_after'] = float(violation.score_after) if violation.score_after is not None else None



        response_data['points_deducted'] = float(violation.points_deducted)







        notifs = list(violation.email_notifications.all())



        if not notifs:



            email_status_str = 'PENDING'



            email_note = 'Đang chuẩn bị gửi email thông báo...'



        elif any(n.status == ViolationEmailNotification.STATUS_FAILED for n in notifs):



            email_status_str = 'FAILED'



            email_note = 'Vi phạm đã được ghi nhận, nhưng email thông báo chưa gửi được. Hệ thống sẽ thử gửi lại.'



        elif all(n.status == ViolationEmailNotification.STATUS_SKIPPED for n in notifs):



            email_status_str = 'SKIPPED'



            email_note = 'Chưa có tài khoản Đoàn trường hợp lệ để gửi email thông báo.'



        elif all(n.status == ViolationEmailNotification.STATUS_SENT for n in notifs):



            email_status_str = 'SENT'



            email_note = 'Đã gửi email thành công.'



        else:



            email_status_str = 'PENDING'



            email_note = 'Đang chờ gửi email.'







        response_data['email_status'] = email_status_str



        response_data['email_message'] = email_note







        if violation.status == ViolationRecord.STATUS_VERIFIED:



            response_data['message'] = 'Đã ghi nhận vi phạm và cập nhật điểm thi đua thành công.'



        else:



            response_data['message'] = 'Đã gửi bản ghi vi phạm để xác minh.'







        return Response(response_data, status=status.HTTP_201_CREATED if getattr(violation, '_created_now', True) else status.HTTP_200_OK)







    @action(detail=False, methods=['get'], url_path='preview-deduction')



    def preview_deduction(self, request):



        """



        Xem trước số điểm trừ và điểm thi đua lớp trước/sau khi trừ trước khi bấm xác nhận.



        """



        class_id = request.query_params.get('class_id')



        rule_id = request.query_params.get('rule_id')



        if not class_id or not rule_id:



            return Response({'error': 'Vui lòng cung cấp class_id và rule_id.'}, status=status.HTTP_400_BAD_REQUEST)







        try:



            school_class = SchoolClass.objects.get(pk=class_id)



            rule = ConductRule.objects.get(pk=rule_id)



        except (SchoolClass.DoesNotExist, ConductRule.DoesNotExist):



            return Response({'error': 'Lớp học hoặc lỗi vi phạm không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)







        current_score, period = get_class_score_snapshot(school_class)

        if current_score is None:

            current_score = Decimal('100.00')



        deduct_points = rule.default_points_deducted



        projected_score = max(Decimal('0.00'), current_score - deduct_points)







        return Response({



            'class_id': school_class.id,



            'class_name': school_class.name,



            'rule_id': rule.id,



            'rule_code': rule.code,



            'rule_name': rule.name,



            'points_to_deduct': float(deduct_points),



            'current_score': float(current_score),



            'projected_score': float(projected_score),



            'period_name': period.name if period else 'Kỳ thi đua hiện tại'



        })







    @action(detail=True, methods=['post'], url_path='adjust-or-undo')



    def adjust_or_undo(self, request, pk=None):



        """



        Điều chỉnh hoặc hoàn tác bản ghi vi phạm đã trừ điểm:



        - action == 'undo': Hủy bỏ vi phạm, phục hồi điểm thi đua của lớp



        - action == 'adjust': Điều chỉnh số điểm trừ mới và tính lại điểm thi đua



        """



        user = request.user



        if not can_user_deduct_directly(user):



            return Response({'error': 'Bạn không có thẩm quyền điều chỉnh hoặc hoàn tác vi phạm.'}, status=status.HTTP_403_FORBIDDEN)







        action_type = request.data.get('action')



        reason = request.data.get('reason')



        adjusted_points = request.data.get('adjusted_points')







        if not reason or not str(reason).strip():



            return Response({'error': 'Vui lòng nhập lý do điều chỉnh hoặc hoàn tác cụ thể.'}, status=status.HTTP_400_BAD_REQUEST)







        if action_type not in ['undo', 'adjust']:



            return Response({'error': "Hành động không hợp lệ. Phải là 'undo' hoặc 'adjust'."}, status=status.HTTP_400_BAD_REQUEST)







        try:



            violation, score_before, score_after = adjust_or_undo_violation(



                violation_id=pk,



                user=user,



                action_type=action_type,



                reason=reason,



                adjusted_points=adjusted_points



            )



        except ValueError as ve:



            return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)



        except PermissionError as pe:



            return Response({'error': str(pe)}, status=status.HTTP_403_FORBIDDEN)







        serializer = self.get_serializer(violation)



        action_name = 'hoàn tác' if action_type == 'undo' else 'điều chỉnh'



        return Response({



            'message': f'Đã {action_name} bản ghi vi phạm {violation.record_code} và cập nhật điểm thi đua thành công.',



            'score_before': float(score_before),



            'score_after': float(score_after),



            'violation': serializer.data



        })







    @action(detail=True, methods=['post'], url_path='verify')



    def verify(self, request, pk=None):



        """



        Xác minh bản ghi vi phạm (chỉ Admin hoặc người được cấp quyền chuyên biệt).



        Kiểm tra nghiêm ngặt quyền hạn ở cả server-side!



        """



        user = request.user



        # Sao đỏ, học sinh, GVBM không có quyền xác minh



        can_verify = (



            user.is_admin



            or user.is_superuser



            or user.is_doan_truong



            or user.can_verify_violations



        )



        if not can_verify or user.is_sao_do or user.is_student or user.role in [User.ROLE_SAO_DO, User.ROLE_HOC_SINH, User.ROLE_GVBM]:



            if not user.is_admin and not user.is_superuser:



                return Response({'error': 'Bạn không có thẩm quyền xác minh bản ghi vi phạm này.'}, status=status.HTTP_403_FORBIDDEN)







        target_violation = self.get_object()







        # Người ghi nhận tuyệt đối không được tự xác minh bản ghi của chính mình



        if target_violation.reporter_id == user.id and not (user.is_admin or user.is_superuser):



            return Response({'error': 'Người ghi nhận không được phép tự thẩm định hoặc xác minh bản ghi do chính mình tạo ra.'}, status=status.HTTP_400_BAD_REQUEST)







        new_status = request.data.get('status')



        if new_status not in [ViolationRecord.STATUS_VERIFIED, ViolationRecord.STATUS_REJECTED, ViolationRecord.STATUS_ADJUSTED]:



            return Response({'error': 'Trạng thái xác minh không hợp lệ'}, status=status.HTTP_400_BAD_REQUEST)







        adjusted_points = request.data.get('adjusted_points')



        verification_notes = request.data.get('verification_notes', '')



        reason = request.data.get('reason', '')







        violation = verify_violation(



            violation_id=pk,



            user=user,



            new_status=new_status,



            adjusted_points=adjusted_points,



            verification_notes=verification_notes,



            reason=reason



        )







        serializer = self.get_serializer(violation)



        return Response({



            'message': f'Đã xác minh bản ghi {violation.record_code}: {violation.get_status_display()}',



            'violation': serializer.data



        })







    @action(detail=True, methods=['post'], url_path='appeal')



    def appeal(self, request, pk=None):



        """



        Học sinh hoặc GVCN gửi yêu cầu giải trình / khiếu nại bản ghi vi phạm.



        """



        violation = self.get_object()



        reason = request.data.get('reason')



        if not reason:



            return Response({'error': 'Vui lòng nhập lý do giải trình hoặc khiếu nại'}, status=status.HTTP_400_BAD_REQUEST)







        user = request.user



        # Kiểm tra quyền: Học sinh liên quan, GVCN của lớp đó, Lớp trưởng của lớp đó, Đoàn trường hoặc Admin
        is_owner_student = hasattr(user, 'student_profile') and violation.student_id == user.student_profile.id
        is_homeroom = user.is_gvcn and (
            violation.school_class.homeroom_teacher_id == user.id or
            HomeroomAssignment.objects.filter(school_class=violation.school_class, teacher=user, is_active=True).exists()
        )
        is_monitor = (
            hasattr(user, 'student_profile') and
            violation.school_class is not None and
            violation.school_class.monitor_id == user.student_profile.id
        )

        if not (is_owner_student or is_homeroom or is_monitor or user.is_admin or user.is_doan_truong):



            return Response({'error': 'Bạn không có quyền khiếu nại bản ghi vi phạm này'}, status=status.HTTP_403_FORBIDDEN)







        updated_violation = submit_violation_appeal(violation.id, user, reason)



        serializer = self.get_serializer(updated_violation)



        return Response({



            'message': 'Đã gửi yêu cầu giải trình/khiếu nại thành công đến Đoàn trường',



            'violation': serializer.data



        })















































# ==============================================================================



# QUẢN TRỊ THÔNG BÁO EMAIL ĐOÀN TRƯỜNG (DÀNH CHO ADMIN)



# ==============================================================================







@api_view(['GET'])



@permission_classes([IsAuthenticated])



def violation_email_history_api(request):



    """



    Lấy danh sách lịch sử gửi email thông báo vi phạm cho Đoàn trường (Phân trang, lọc theo trạng thái/tìm kiếm).



    Chỉ Quản trị viên mới có quyền xem.



    """



    if not (request.user.role == User.ROLE_ADMIN or request.user.is_superuser):



        return Response({'error': 'Chỉ Quản trị viên mới có quyền xem lịch sử email.'}, status=status.HTTP_403_FORBIDDEN)







    qs = ViolationEmailNotification.objects.all().select_related('violation', 'violation__school_class')



    st = request.query_params.get('status')



    if st:



        qs = qs.filter(status=st)



    search = request.query_params.get('search')



    if search:



        qs = qs.filter(



            Q(recipient_email__icontains=search) |



            Q(subject__icontains=search) |



            Q(violation__record_code__icontains=search) |



            Q(violation__student_name_snapshot__icontains=search)



        )







    total = qs.count()



    try:



        page = max(1, int(request.query_params.get('page', 1)))



        page_size = max(1, min(100, int(request.query_params.get('page_size', 20))))



    except ValueError:



        page = 1



        page_size = 20







    start = (page - 1) * page_size



    items = qs[start:start + page_size]



    serializer = ViolationEmailNotificationSerializer(items, many=True)







    return Response({



        'total': total,



        'page': page,



        'page_size': page_size,



        'results': serializer.data,



    })











@api_view(['POST'])



@permission_classes([IsAuthenticated])



def violation_email_retry_api(request, notification_id):



    """



    Đưa thông báo email thất bại trở lại outbox để worker gửi nền.



    """



    if not (request.user.role == User.ROLE_ADMIN or request.user.is_superuser):



        return Response({'error': 'Chỉ Quản trị viên mới có quyền gửi lại email.'}, status=status.HTTP_403_FORBIDDEN)







    try:



        notif = ViolationEmailNotification.objects.get(id=notification_id)



    except ViolationEmailNotification.DoesNotExist:



        return Response({'error': 'Không tìm thấy thông báo email.'}, status=status.HTTP_404_NOT_FOUND)







    current_union_email = notif.recipient_email or (notif.recipient_user.email if notif.recipient_user else '') or get_school_union_notification_email()



    if not notif.recipient_email and current_union_email:



        notif.recipient_email = current_union_email



    if not notif.recipient_email:



        return Response({'error': 'Không có địa chỉ email Đoàn trường hợp lệ để gửi lại.'}, status=status.HTTP_400_BAD_REQUEST)



    if notif.status != ViolationEmailNotification.STATUS_FAILED:



        return Response({'error': 'Chỉ có thể thử lại email đang ở trạng thái thất bại.'}, status=status.HTTP_400_BAD_REQUEST)







    notif.status = ViolationEmailNotification.STATUS_PENDING



    notif.attempt_count = 0



    notif.next_attempt_at = timezone.now()



    notif.last_error = ''



    notif.save(update_fields=[



        'recipient_email', 'status', 'attempt_count', 'next_attempt_at', 'last_error', 'updated_at',



    ])







    AuditLog.objects.create(



        user=request.user,



        action='RETRY_EMAIL',



        resource_type='EMAIL_NOTIFICATION',



        resource_id=str(notif.id),



        details=f"Admin {request.user.username} gửi lại email thông báo vi phạm {notif.violation.record_code if notif.violation else 'N/A'}. Kết quả: {notif.status}.",



        ip_address=request.META.get('REMOTE_ADDR'),



    )







    transaction.on_commit(lambda: dispatch_email_async(notif.id))







    return Response({



        'success': True,



        'notification': ViolationEmailNotificationSerializer(notif).data,



        'message': 'Đã đưa email vào hàng đợi gửi lại.',



    })











@api_view(['POST'])



@permission_classes([IsAuthenticated])



def violation_email_test_api(request):



    """



    Gửi email thử nghiệm đến địa chỉ Đoàn trường để kiểm tra cấu hình SMTP.



    """



    if not (request.user.role == User.ROLE_ADMIN or request.user.is_superuser):



        return Response({'error': 'Chỉ Quản trị viên mới có quyền gửi email kiểm tra.'}, status=status.HTTP_403_FORBIDDEN)







    recipient = (request.data.get('recipient_email') or '').strip()



    if recipient:



        try:



            validate_email(recipient)



        except ValidationError:



            return Response({'error': 'Địa chỉ email không đúng định dạng.'}, status=status.HTTP_400_BAD_REQUEST)







    recent_tests = AuditLog.objects.filter(



        user=request.user,



        action='TEST_EMAIL',



        created_at__gte=timezone.now() - timezone.timedelta(minutes=10),



    ).count()



    if recent_tests >= 5:



        return Response(



            {'error': 'Bạn đã gửi quá nhiều email kiểm tra. Vui lòng thử lại sau 10 phút.'},



            status=status.HTTP_429_TOO_MANY_REQUESTS,



        )







    success, message, notif = send_test_union_email(recipient_email=recipient or None, requested_by=request.user)







    AuditLog.objects.create(



        user=request.user,



        action='TEST_EMAIL',



        resource_type='EMAIL_NOTIFICATION',



        resource_id=str(notif.id) if notif else '',



        details=f"Admin {request.user.username} gửi email kiểm tra tới {recipient or get_school_union_notification_email()}. Kết quả: {message}",



        ip_address=request.META.get('REMOTE_ADDR'),



    )







    return Response({



        'success': success,



        'message': message,



        'notification': ViolationEmailNotificationSerializer(notif).data if notif else None,



    }, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)















def add_or_update_union_email_recipient(email: str, full_name: str = '', created_by=None):



    clean_email = email.strip().lower()



    validate_email(clean_email)







    user = User.objects.filter(email__iexact=clean_email).first()



    if user:



        preserve_doan_permissions = user.is_doan_truong



        user.role = User.ROLE_DOAN_TRUONG



        user.can_verify_violations = False



        user.can_view_counseling = False



        if not preserve_doan_permissions:



            user.doan_truong_permissions = []



        user.account_status = User.STATUS_APPROVED



        user.is_active = True



        if full_name and not user.full_name:



            user.full_name = full_name.strip()



        user.save()



        return user, False







    base_prefix = re.sub(r'[^a-zA-Z0-9_.-]', '', clean_email.split('@')[0])



    if len(base_prefix) < 3 or not base_prefix[0].isalnum():



        base_prefix = f"doan_{base_prefix}".strip('_')



    if len(base_prefix) < 3:



        base_prefix = "doan_truong"







    username = base_prefix



    counter = 1



    while User.objects.filter(username__iexact=username).exists():



        username = f"{base_prefix}_{counter}"



        counter += 1







    display_name = full_name.strip() if full_name else f"Cán bộ Đoàn trường ({clean_email.split('@')[0]})"



    user = User(



        username=username,



        email=clean_email,



        full_name=display_name,



        role=User.ROLE_DOAN_TRUONG,



        can_verify_violations=False,



        account_status=User.STATUS_APPROVED,



        is_active=True,



        department_or_class="Văn phòng Đoàn trường",



        must_change_password=True,



    )



    user.set_password(token_urlsafe(16))



    user.save()







    ApprovalLog.objects.create(



        user=user,



        reviewer=created_by,



        previous_status='NEW',



        new_status=User.STATUS_APPROVED,



        assigned_role=User.ROLE_DOAN_TRUONG,



        reason='Thêm tài khoản Đoàn trường nhận email thông báo qua Cấu hình hệ thống',



        internal_notes=f'Thêm bởi {created_by.username if created_by else "Admin"}'



    )



    return user, True











def remove_union_email_recipient(user_id=None, email=None, removed_by=None):



    user = None



    if user_id:



        user = User.objects.filter(id=user_id).first()



    elif email:



        user = User.objects.filter(email__iexact=email.strip().lower()).first()







    if not user:



        return False, "Không tìm thấy tài khoản người dùng."







    user.can_verify_violations = False



    if user.role == User.ROLE_DOAN_TRUONG:



        user.role = User.ROLE_GVBM



        user.doan_truong_permissions = []



    user.save()



    return True, f"Đã gỡ bỏ quyền nhận thông báo vi phạm của tài khoản {user.email or user.username}."











def update_smtp_settings(data: dict):



    env_updates = {}



    if 'smtp_user' in data:



        user_val = (data['smtp_user'] or '').strip()



        env_updates['EMAIL_HOST_USER'] = user_val



        env_updates['GMAIL_SENDER_EMAIL'] = user_val



        settings.EMAIL_HOST_USER = user_val



    if 'smtp_password' in data and data['smtp_password'].strip():



        pwd_val = data['smtp_password'].strip().replace(' ', '')



        env_updates['EMAIL_HOST_PASSWORD'] = pwd_val



        env_updates['GMAIL_APP_PASSWORD'] = pwd_val



        settings.EMAIL_HOST_PASSWORD = pwd_val



    if 'default_from_email' in data:



        from_val = (data['default_from_email'] or '').strip()



        if from_val:



            env_updates['DEFAULT_FROM_EMAIL'] = from_val



            settings.DEFAULT_FROM_EMAIL = from_val



        elif getattr(settings, 'EMAIL_HOST_USER', ''):



            env_updates['DEFAULT_FROM_EMAIL'] = f"HK Student Hub <{settings.EMAIL_HOST_USER}>"



            settings.DEFAULT_FROM_EMAIL = env_updates['DEFAULT_FROM_EMAIL']



    if 'smtp_host' in data and data['smtp_host'].strip():



        host_val = data['smtp_host'].strip()



        env_updates['EMAIL_HOST'] = host_val



        settings.EMAIL_HOST = host_val



    if 'smtp_port' in data and str(data['smtp_port']).strip():



        try:



            port_val = int(data['smtp_port'])



            env_updates['EMAIL_PORT'] = str(port_val)



            settings.EMAIL_PORT = port_val



        except ValueError:



            pass







    settings.SMTP_EMAIL_CONFIGURED = bool(



        getattr(settings, 'EMAIL_HOST_USER', '') and



        getattr(settings, 'EMAIL_HOST_PASSWORD', '') and



        getattr(settings, 'DEFAULT_FROM_EMAIL', '')



    )







    # Persist changes to .env file



    env_path = settings.BASE_DIR / '.env'



    lines = []



    if env_path.exists():



        try:



            with open(env_path, 'r', encoding='utf-8') as f:



                lines = f.readlines()



        except Exception:



            lines = []







    updated_keys = set()



    new_lines = []



    for line in lines:



        stripped = line.strip()



        if stripped and not stripped.startswith('#') and '=' in stripped:



            k = stripped.split('=', 1)[0].strip()



            if k in env_updates:



                new_lines.append(f"{k}={env_updates[k]}\n")



                updated_keys.add(k)



                continue



        new_lines.append(line)







    for k, v in env_updates.items():



        if k not in updated_keys:



            new_lines.append(f"{k}={v}\n")







    try:



        with open(env_path, 'w', encoding='utf-8') as f:



            f.writelines(new_lines)



    except Exception:



        pass











@api_view(['GET', 'POST', 'PATCH', 'DELETE'])



@permission_classes([IsAuthenticated])



def violation_email_config_api(request):



    """



    Xem và quản lý cấu hình email hệ thống, thêm/xóa các tài khoản Gmail Đoàn trường nhận thông báo,



    và cấu hình máy chủ SMTP Gmail gửi đi.



    """



    if not (request.user.role == User.ROLE_ADMIN or request.user.is_superuser):



        return Response({'error': 'Chỉ Quản trị viên mới có quyền quản lý cấu hình email.'}, status=status.HTTP_403_FORBIDDEN)







    if request.method == 'GET':



        recipients = get_eligible_union_recipients()



        recipient_list = [



            {



                'id': u.id,



                'username': u.username,



                'full_name': u.full_name or u.username,



                'email': u.email,



                'role': u.get_role_display(),



                'can_verify_violations': u.can_verify_violations,



            }



            for u in recipients



        ]







        return Response({



            'recipients': recipient_list,



            'recipient_count': len(recipients),



            'email': get_school_union_notification_email(),



            'smtp_host': getattr(settings, 'EMAIL_HOST', 'localhost'),



            'smtp_port': getattr(settings, 'EMAIL_PORT', 587),



            'smtp_user': getattr(settings, 'EMAIL_HOST_USER', ''),



            'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', ''),



            'backend': getattr(settings, 'EMAIL_BACKEND', ''),



            'smtp_configured': getattr(settings, 'SMTP_EMAIL_CONFIGURED', False),



        })







    if request.method == 'DELETE':



        user_id = request.data.get('user_id') or request.query_params.get('id')



        email = (request.data.get('email') or request.query_params.get('email') or '').strip()



        ok, msg = remove_union_email_recipient(user_id=user_id, email=email, removed_by=request.user)



        if not ok:



            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)







        AuditLog.objects.create(



            user=request.user,



            action='DELETE_UNION_EMAIL',



            resource_type='EMAIL_RECIPIENT',



            resource_id=str(user_id or email),



            details=f"Admin {request.user.username} đã gỡ bỏ Gmail/email Đoàn trường {email or user_id}.",



            ip_address=request.META.get('REMOTE_ADDR'),



        )



        recipients = get_eligible_union_recipients()



        return Response({



            'success': True,



            'message': msg,



            'recipients': [



                {



                    'id': u.id,



                    'username': u.username,



                    'full_name': u.full_name or u.username,



                    'email': u.email,



                    'role': u.get_role_display(),



                    'can_verify_violations': u.can_verify_violations,



                }



                for u in recipients



            ],



            'recipient_count': len(recipients),



            'email': get_school_union_notification_email(),



        })







    # POST or PATCH



    action = request.data.get('action')



    if action == 'remove_recipient':



        user_id = request.data.get('user_id') or request.query_params.get('id')



        email = (request.data.get('email') or request.query_params.get('email') or '').strip()



        ok, msg = remove_union_email_recipient(user_id=user_id, email=email, removed_by=request.user)



        if not ok:



            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)







        AuditLog.objects.create(



            user=request.user,



            action='DELETE_UNION_EMAIL',



            resource_type='EMAIL_RECIPIENT',



            resource_id=str(user_id or email),



            details=f"Admin {request.user.username} đã gỡ bỏ Gmail/email Đoàn trường {email or user_id}.",



            ip_address=request.META.get('REMOTE_ADDR'),



        )



        recipients = get_eligible_union_recipients()



        return Response({



            'success': True,



            'message': msg,



            'recipients': [



                {



                    'id': u.id,



                    'username': u.username,



                    'full_name': u.full_name or u.username,



                    'email': u.email,



                    'role': u.get_role_display(),



                    'can_verify_violations': u.can_verify_violations,



                }



                for u in recipients



            ],



            'recipient_count': len(recipients),



            'email': get_school_union_notification_email(),



        })







    if action == 'update_smtp':



        update_smtp_settings(request.data)



        AuditLog.objects.create(



            user=request.user,



            action='UPDATE_SMTP_CONFIG',



            resource_type='SYSTEM_CONFIG',



            resource_id='SMTP',



            details=f"Admin {request.user.username} đã cập nhật cấu hình máy chủ SMTP / Gmail gửi đi.",



            ip_address=request.META.get('REMOTE_ADDR'),



        )



        return Response({



            'success': True,



            'message': 'Đã lưu cấu hình máy chủ SMTP / Gmail gửi đi thành công.',



            'smtp_host': getattr(settings, 'EMAIL_HOST', 'localhost'),



            'smtp_port': getattr(settings, 'EMAIL_PORT', 587),



            'smtp_user': getattr(settings, 'EMAIL_HOST_USER', ''),



            'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', ''),



            'smtp_configured': getattr(settings, 'SMTP_EMAIL_CONFIGURED', False),



        })







    # Default action: Add recipient(s)



    raw_emails = request.data.get('email') or request.data.get('emails') or ''



    full_name = (request.data.get('full_name') or '').strip()







    if isinstance(raw_emails, str):



        email_list = [e.strip() for e in re.split(r'[,;\s]+', raw_emails) if e.strip()]



    elif isinstance(raw_emails, list):



        email_list = [str(e).strip() for e in raw_emails if str(e).strip()]



    else:



        email_list = []







    if not email_list:



        return Response({'error': 'Vui lòng cung cấp ít nhất một địa chỉ email hoặc Gmail hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)







    added_recipients = []



    errors = []



    with transaction.atomic():



        for email_item in email_list:



            try:



                user, is_new = add_or_update_union_email_recipient(



                    email=email_item,



                    full_name=full_name,



                    created_by=request.user



                )



                added_recipients.append({



                    'email': user.email,



                    'username': user.username,



                    'is_new': is_new



                })



            except ValidationError:



                errors.append(f"{email_item} (định dạng không đúng)")



            except Exception as ex:



                errors.append(f"{email_item} ({str(ex)})")







    if not added_recipients:



        return Response({'error': f'Không thể thêm email. Lỗi: {", ".join(errors)}'}, status=status.HTTP_400_BAD_REQUEST)







    AuditLog.objects.create(



        user=request.user,



        action='ADD_UNION_EMAIL',



        resource_type='EMAIL_RECIPIENT',



        resource_id=','.join([r['email'] for r in added_recipients]),



        details=f"Admin {request.user.username} đã thêm/cập nhật {len(added_recipients)} Gmail/email nhận thông báo Đoàn trường: {', '.join([r['email'] for r in added_recipients])}",



        ip_address=request.META.get('REMOTE_ADDR'),



    )







    recipients = get_eligible_union_recipients()



    recipient_list = [



        {



            'id': u.id,



            'username': u.username,



            'full_name': u.full_name or u.username,



            'email': u.email,



            'role': u.get_role_display(),



            'can_verify_violations': u.can_verify_violations,



        }



        for u in recipients



    ]







    msg = f"Đã thêm thành công {len(added_recipients)} địa chỉ Gmail vào danh sách Đoàn trường nhận thông báo."



    if errors:



        msg += f" (Bỏ qua địa chỉ lỗi: {', '.join(errors)})"







    return Response({



        'success': True,



        'message': msg,



        'added_recipients': added_recipients,



        'recipients': recipient_list,



        'recipient_count': len(recipients),



        'email': get_school_union_notification_email(),



    })











class TeacherManagementViewSet(viewsets.ViewSet):



    """



    Quản lý giáo viên và phân công lớp học (Admin only):



    - Danh sách giáo viên kèm môn học, số lớp giảng dạy, lớp chủ nhiệm.



    - Phân công giáo viên bộ môn vào nhiều lớp trong 64 lớp.



    - Bổ nhiệm giáo viên chủ nhiệm (GVCN) với kiểm tra cảnh báo xung đột nếu lớp đã có GVCN.



    - Thu hồi phân công GVCN.



    - Lịch sử phân công chuyên môn và chủ nhiệm.



    """



    permission_classes = [permissions.IsAuthenticated]







    def check_admin_permission(self, request):



        if not (request.user.is_admin or request.user.is_superuser or request.user.is_doan_truong):



            return Response(



                {'error': 'Chỉ có Quản trị viên (Admin) hoặc Đoàn trường mới có quyền xem và phân công giáo viên.'},



                status=status.HTTP_403_FORBIDDEN



            )



        return None







    def list(self, request):



        perm = self.check_admin_permission(request)



        if perm:



            return perm







        teachers = User.objects.filter(



            Q(role__in=[User.ROLE_GVBM, User.ROLE_GVCN]) |



            Q(teacher_profile__isnull=False) |



            Q(teaching_assignments__isnull=False) |



            Q(homeroom_assignments__isnull=False)



        ).distinct().order_by('full_name', 'username')







        search = request.query_params.get('search', '').strip()



        if search:



            teachers = teachers.filter(



                Q(full_name__icontains=search) |



                Q(username__icontains=search) |



                Q(email__icontains=search) |



                Q(phone__icontains=search) |



                Q(department_or_class__icontains=search)



            )







        status_param = request.query_params.get('status')



        if status_param:



            teachers = teachers.filter(account_status=status_param)







        data = []



        for t in teachers:



            active_teaching = t.teaching_assignments.filter(is_active=True).select_related('school_class')



            active_hr = t.homeroom_assignments.filter(is_active=True).select_related('school_class').first()



            if not active_hr and hasattr(t, 'homeroom_classes'):



                active_hr_class = t.homeroom_classes.filter(is_active=True).first()



            else:



                active_hr_class = active_hr.school_class if active_hr else None







            subject_val = ''



            if hasattr(t, 'teacher_profile') and t.teacher_profile.subject:



                subject_val = t.teacher_profile.subject



            elif t.department_or_class and t.department_or_class.startswith('Môn '):



                subject_val = t.department_or_class[4:].strip()



            else:



                subject_val = t.department_or_class or 'Chưa phân môn'







            data.append({



                'id': t.id,



                'username': t.username,



                'full_name': t.full_name or t.username,



                'email': t.email,



                'phone': t.phone,



                'role': t.role,



                'role_display': t.get_role_display(),



                'account_status': t.account_status,



                'account_status_display': t.get_account_status_display(),



                'subject': subject_val,



                'teaching_classes_count': active_teaching.count(),



                'teaching_classes': [



                    {



                        'id': a.school_class.id,



                        'name': a.school_class.name,



                        'grade': a.school_class.grade,



                        'subject': a.subject



                    }



                    for a in active_teaching



                ],



                'homeroom_class': {



                    'id': active_hr_class.id,



                    'name': active_hr_class.name,



                    'grade': active_hr_class.grade



                } if active_hr_class else None,



                'date_joined': t.date_joined.strftime('%d/%m/%Y'),



                'is_active': t.is_active



            })







        return Response({



            'total': len(data),



            'teachers': data



        })







    @action(detail=True, methods=['post'], url_path='assign-classes')



    def assign_classes(self, request, pk=None):



        perm = self.check_admin_permission(request)



        if perm:



            return perm







        teacher = User.objects.filter(pk=pk).first()



        if not teacher:



            return Response({'error': 'Không tìm thấy giáo viên.'}, status=status.HTTP_404_NOT_FOUND)







        if teacher.account_status != User.STATUS_APPROVED:



            return Response({'error': 'Không thể phân công lớp cho tài khoản chưa được phê duyệt.'}, status=status.HTTP_400_BAD_REQUEST)



        if not teacher.is_active:



            return Response({'error': 'Không thể phân công lớp cho tài khoản đang bị khóa.'}, status=status.HTTP_400_BAD_REQUEST)







        class_ids = request.data.get('class_ids', [])



        if not isinstance(class_ids, list):



            return Response({'error': 'Danh sách lớp (class_ids) không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)







        # Subject



        default_subject = ''



        if hasattr(teacher, 'teacher_profile') and teacher.teacher_profile.subject:



            default_subject = teacher.teacher_profile.subject



        elif teacher.department_or_class and teacher.department_or_class.startswith('Môn '):



            default_subject = teacher.department_or_class[4:].strip()



        subject = (request.data.get('subject') or default_subject or 'Toán').strip()







        with transaction.atomic():



            # Deactivate assignments not in class_ids



            teacher.teaching_assignments.filter(is_active=True).exclude(school_class_id__in=class_ids).update(



                is_active=False,



                end_date=timezone.now().date()



            )







            assigned_classes = []



            for cid in class_ids:



                sclass = SchoolClass.objects.filter(id=cid, is_active=True).first()



                if not sclass:



                    continue



                assignment, created = TeacherClassAssignment.objects.get_or_create(



                    teacher=teacher,



                    school_class=sclass,



                    subject=subject,



                    defaults={



                        'assigned_by': request.user,



                        'is_active': True,



                        'start_date': timezone.now().date()



                    }



                )



                if not created and not assignment.is_active:



                    assignment.is_active = True



                    assignment.end_date = None



                    assignment.assigned_by = request.user



                    assignment.save(update_fields=['is_active', 'end_date', 'assigned_by', 'updated_at'])



                assigned_classes.append(sclass.name)







            class_list_str = ', '.join(assigned_classes) if assigned_classes else 'Không có lớp nào'



            AuditLog.objects.create(



                user=request.user,



                action='ASSIGN_TEACHER_CLASSES',



                resource_type='USER',



                resource_id=str(teacher.id),



                details=f"Admin {request.user.username} đã phân công giáo viên {teacher.full_name or teacher.username} giảng dạy môn {subject} cho các lớp: {class_list_str}",



                ip_address=request.META.get('REMOTE_ADDR')



            )







            from core.models import Notification



            Notification.objects.create(



                recipient=teacher,



                notification_type=Notification.TYPE_SYSTEM,



                title='Cập nhật phân công lớp giảng dạy',



                message=f"Quản trị viên đã cập nhật phân công giảng dạy môn {subject} của Thầy/Cô. Các lớp được phân công: {class_list_str}.",



                link='/'



            )







        return Response({



            'success': True,



            'message': f"Đã phân công thành công giáo viên {teacher.full_name or teacher.username} giảng dạy {len(assigned_classes)} lớp.",



            'assigned_classes': assigned_classes



        })







    @action(detail=True, methods=['post'], url_path='appoint-homeroom')



    def appoint_homeroom(self, request, pk=None):



        perm = self.check_admin_permission(request)



        if perm:



            return perm







        teacher = User.objects.filter(pk=pk).first()



        if not teacher:



            return Response({'error': 'Không tìm thấy giáo viên.'}, status=status.HTTP_404_NOT_FOUND)







        if teacher.account_status != User.STATUS_APPROVED:



            return Response({'error': 'Không thể bổ nhiệm tài khoản chưa được phê duyệt.'}, status=status.HTTP_400_BAD_REQUEST)



        if not teacher.is_active:



            return Response({'error': 'Không thể bổ nhiệm tài khoản đang bị khóa.'}, status=status.HTTP_400_BAD_REQUEST)







        class_id = request.data.get('class_id')



        if not class_id:



            return Response({'error': 'Vui lòng chọn lớp học để bổ nhiệm GVCN.'}, status=status.HTTP_400_BAD_REQUEST)







        sclass = SchoolClass.objects.filter(id=class_id, is_active=True).first()



        if not sclass:



            return Response({'error': 'Lớp học không tồn tại hoặc đã bị khóa.'}, status=status.HTTP_400_BAD_REQUEST)







        notes = request.data.get('notes', '').strip()



        force = (



            str(request.data.get('force', '')).lower() in ['true', '1'] or



            str(request.data.get('confirm_replace', '')).lower() in ['true', '1'] or



            request.data.get('confirm_replace') is True or



            request.data.get('force') is True



        )







        current_assignment = HomeroomAssignment.objects.filter(school_class=sclass, is_active=True).select_related('teacher').first()



        if current_assignment and current_assignment.teacher_id != teacher.id:



            if not force:



                current_name = current_assignment.teacher.full_name or current_assignment.teacher.username



                msg = f"Xung đột GVCN: Lớp {sclass.name} hiện đã có GVCN là {current_name}. Bạn có chắc chắn muốn kết thúc nhiệm kỳ của {current_name} và bổ nhiệm {teacher.full_name or teacher.username} làm GVCN mới?"



                return Response({



                    'warning': True,



                    'conflict': True,



                    'error': msg,



                    'message': msg,



                    'current_gvcn_id': current_assignment.teacher_id,



                    'current_gvcn_name': current_name,



                    'class_name': sclass.name,



                }, status=status.HTTP_409_CONFLICT)







        with transaction.atomic():



            if current_assignment and current_assignment.teacher_id != teacher.id:



                current_assignment.is_active = False



                current_assignment.end_date = timezone.now().date()



                current_assignment.save(update_fields=['is_active', 'end_date', 'updated_at'])







            HomeroomAssignment.objects.filter(teacher=teacher, is_active=True).exclude(school_class=sclass).update(



                is_active=False,



                end_date=timezone.now().date()



            )







            HomeroomAssignment.objects.create(



                teacher=teacher,



                school_class=sclass,



                assigned_by=request.user,



                start_date=timezone.now().date(),



                is_active=True,



                notes=notes



            )







            sclass.homeroom_teacher = teacher



            sclass.save(update_fields=['homeroom_teacher'])







            if teacher.role not in [User.ROLE_ADMIN, User.ROLE_SUPER_ADMIN, User.ROLE_BGH]:



                teacher.role = User.ROLE_GVCN



                teacher.save(update_fields=['role'])







            AuditLog.objects.create(



                user=request.user,



                action='APPOINT_HOMEROOM_TEACHER',



                resource_type='SCHOOL_CLASS',



                resource_id=str(sclass.id),



                details=f"Admin {request.user.username} đã bổ nhiệm {teacher.full_name or teacher.username} làm GVCN lớp {sclass.name}. Ghi chú: {notes}",



                ip_address=request.META.get('REMOTE_ADDR')



            )







            from core.models import Notification



            Notification.objects.create(



                recipient=teacher,



                notification_type=Notification.TYPE_SYSTEM,



                title='Quyết định phân công Giáo viên chủ nhiệm',



                message=f"Thầy/Cô đã được Ban Giám hiệu / Quản trị viên phân công làm Giáo viên chủ nhiệm lớp {sclass.name} từ ngày {timezone.now().strftime('%d/%m/%Y')}.",



                link='/'



            )







        return Response({



            'success': True,



            'message': f"Đã bổ nhiệm Thầy/Cô {teacher.full_name or teacher.username} làm GVCN lớp {sclass.name} thành công.",



            'homeroom_class': {'id': sclass.id, 'name': sclass.name, 'grade': sclass.grade}



        })







    @action(detail=True, methods=['post'], url_path='revoke-homeroom')



    def revoke_homeroom(self, request, pk=None):



        perm = self.check_admin_permission(request)



        if perm:



            return perm







        teacher = User.objects.filter(pk=pk).first()



        if not teacher:



            return Response({'error': 'Không tìm thấy giáo viên.'}, status=status.HTTP_404_NOT_FOUND)







        class_id = request.data.get('class_id')



        with transaction.atomic():



            qs = HomeroomAssignment.objects.filter(teacher=teacher, is_active=True)



            if class_id:



                qs = qs.filter(school_class_id=class_id)







            for hr in qs:



                sclass = hr.school_class



                hr.is_active = False



                hr.end_date = timezone.now().date()



                hr.save(update_fields=['is_active', 'end_date', 'updated_at'])



                if sclass.homeroom_teacher_id == teacher.id:



                    sclass.homeroom_teacher = None



                    sclass.save(update_fields=['homeroom_teacher'])







            if not HomeroomAssignment.objects.filter(teacher=teacher, is_active=True).exists():



                if teacher.role == User.ROLE_GVCN:



                    teacher.role = User.ROLE_GVBM



                    teacher.save(update_fields=['role'])







            AuditLog.objects.create(



                user=request.user,



                action='REVOKE_HOMEROOM_TEACHER',



                resource_type='USER',



                resource_id=str(teacher.id),



                details=f"Admin {request.user.username} đã thu hồi quyền GVCN của {teacher.full_name or teacher.username}.",



                ip_address=request.META.get('REMOTE_ADDR')



            )







        return Response({'success': True, 'message': 'Đã thu hồi quyền Giáo viên chủ nhiệm thành công.'})







    @action(detail=True, methods=['get'], url_path='history')



    def history(self, request, pk=None):



        perm = self.check_admin_permission(request)



        if perm:



            return perm







        teacher = User.objects.filter(pk=pk).first()



        if not teacher:



            return Response({'error': 'Không tìm thấy giáo viên.'}, status=status.HTTP_404_NOT_FOUND)







        teaching = TeacherClassAssignment.objects.filter(teacher=teacher).order_by('-start_date')



        homeroom = HomeroomAssignment.objects.filter(teacher=teacher).order_by('-start_date')







        return Response({



            'teaching_history': TeacherClassAssignmentSerializer(teaching, many=True).data,



            'homeroom_history': HomeroomAssignmentSerializer(homeroom, many=True).data



        })











class TeacherReflectionViewSet(viewsets.ModelViewSet):



    """



    Phân hệ quản lý Phản ánh nền nếp của Giáo viên bộ môn (Reflections):



    - GVBM: Chỉ xem và gửi phản ánh cho các lớp được phân công giảng dạy.



    - GVBM TUYỆT ĐỐI không có quyền trừ điểm trực tiếp hay lập vi phạm trừ điểm.



    - GVCN: Xem và xử lý các phản ánh thuộc lớp chủ nhiệm của mình.



    - Admin: Xem và xử lý toàn bộ phản ánh toàn trường.



    """



    serializer_class = TeacherReflectionSerializer



    permission_classes = [permissions.IsAuthenticated]







    def get_queryset(self):



        user = self.request.user



        qs = TeacherReflection.objects.all().select_related(



            'teacher', 'school_class', 'student', 'processed_by', 'violation_record'



        ).prefetch_related('histories')







        if user.is_admin or user.is_super_admin or user.is_bgh:



            pass  # Admin / BGH sees all



        elif user.is_gvcn:



            hr_class_ids = list(SchoolClass.objects.filter(



                Q(homeroom_assignments__teacher=user, homeroom_assignments__is_active=True) |



                Q(homeroom_teacher=user)



            ).values_list('id', flat=True))



            qs = qs.filter(Q(school_class_id__in=hr_class_ids) | Q(teacher=user))



        elif user.role == User.ROLE_GVBM or hasattr(user, 'teaching_assignments'):



            qs = qs.filter(teacher=user)



        elif user.is_student and hasattr(user, 'student_profile'):



            qs = qs.filter(



                student=user.student_profile,



                status__in=[TeacherReflection.STATUS_RESOLVED, TeacherReflection.STATUS_VERIFYING]



            )



        else:



            qs = qs.none()







        class_id = self.request.query_params.get('class_id')



        if class_id:



            qs = qs.filter(school_class_id=class_id)



        status_param = self.request.query_params.get('status')



        if status_param:



            qs = qs.filter(status=status_param)



        urgency = self.request.query_params.get('urgency')



        if urgency:



            qs = qs.filter(urgency=urgency)



        reflection_type = self.request.query_params.get('reflection_type')



        if reflection_type:



            qs = qs.filter(reflection_type=reflection_type)



        search = self.request.query_params.get('search')



        if search:



            qs = qs.filter(



                Q(reflection_code__icontains=search) |



                Q(student_name_snapshot__icontains=search) |



                Q(content__icontains=search)



            )







        return qs.order_by('-created_at')







    def create(self, request, *args, **kwargs):



        user = request.user



        if user.is_student:



            return Response({'error': 'Học sinh không có quyền gửi phản ánh nền nếp.'}, status=status.HTTP_403_FORBIDDEN)







        class_id = request.data.get('school_class') or request.data.get('class_id')



        student_id = request.data.get('student') or request.data.get('student_id')



        reflection_type = request.data.get('reflection_type', TeacherReflection.TYPE_ACADEMIC)



        content = (request.data.get('content') or '').strip()



        urgency = request.data.get('urgency', TeacherReflection.URGENCY_LOW)



        occurred_at_raw = request.data.get('occurred_at')



        evidence_image = request.FILES.get('evidence_image')







        if not class_id:



            return Response({'error': 'Vui lòng chọn lớp học liên quan.'}, status=status.HTTP_400_BAD_REQUEST)



        if not content:



            return Response({'error': 'Vui lòng nhập nội dung chi tiết phản ánh sự việc.'}, status=status.HTTP_400_BAD_REQUEST)







        school_class = SchoolClass.objects.filter(id=class_id, is_active=True).first()



        if not school_class:



            return Response({'error': 'Lớp học không tồn tại hoặc đã bị khóa.'}, status=status.HTTP_400_BAD_REQUEST)







        # RÀNG BUỘC PHÂN CÔNG: Nếu là GVBM (không phải Admin), giáo viên phải được phân công dạy lớp đó!



        if not (user.is_admin or user.is_superuser):



            is_assigned = TeacherClassAssignment.objects.filter(



                teacher=user, school_class=school_class, is_active=True



            ).exists()



            is_homeroom = (school_class.homeroom_teacher_id == user.id) or HomeroomAssignment.objects.filter(



                teacher=user, school_class=school_class, is_active=True



            ).exists()



            if not is_assigned and not is_homeroom:



                return Response(



                    {'error': f'Bạn chưa được phân công giảng dạy lớp {school_class.name}. Chỉ được gửi phản ánh đối với các lớp được phân công.'},



                    status=status.HTTP_403_FORBIDDEN



                )







        # RÀNG BUỘC HỌC SINH: Nếu chọn học sinh, học sinh phải thuộc đúng lớp này



        student_obj = None



        if student_id:



            student_obj = Student.objects.filter(id=student_id, school_class=school_class).first()



            if not student_obj:



                return Response({'error': f'Học sinh được chọn không thuộc lớp {school_class.name}.'}, status=status.HTTP_400_BAD_REQUEST)







        occurred_at = timezone.now()



        if occurred_at_raw:



            parsed = parse_datetime(str(occurred_at_raw))



            if parsed:



                if timezone.is_naive(parsed):



                    parsed = timezone.make_aware(parsed, timezone.get_current_timezone())



                if parsed > timezone.now() + timedelta(minutes=5):



                    return Response({'error': 'Thời gian xảy ra không thể ở tương lai.'}, status=status.HTTP_400_BAD_REQUEST)



                occurred_at = parsed







        with transaction.atomic():



            reflection = TeacherReflection(



                teacher=user,



                school_class=school_class,



                student=student_obj,



                student_name_snapshot=student_obj.full_name if student_obj else f"Tập thể {school_class.name}",



                reflection_type=reflection_type,



                content=content,



                occurred_at=occurred_at,



                urgency=urgency,



                evidence_image=evidence_image,



                status=TeacherReflection.STATUS_NEW



            )



            reflection.save()







            ReflectionHistory.objects.create(



                reflection=reflection,



                action='CREATE',



                performed_by=user,



                previous_status='',



                new_status=TeacherReflection.STATUS_NEW,



                notes=f"Giáo viên {user.full_name or user.username} gửi phản ánh mới."



            )







            from core.models import Notification



            if school_class.homeroom_teacher and school_class.homeroom_teacher_id != user.id:



                Notification.objects.create(



                    recipient=school_class.homeroom_teacher,



                    notification_type=Notification.TYPE_SYSTEM,



                    title=f'Phản ánh nền nếp mới - Lớp {school_class.name}',



                    message=f"Thầy/Cô {user.full_name} vừa gửi phản ánh ({reflection.get_reflection_type_display()}) về {reflection.student_name_snapshot}.",



                    link='/'



                )







            from .email import send_reflection_notification_email



            send_reflection_notification_email(reflection)







            AuditLog.objects.create(



                user=user,



                action='CREATE_TEACHER_REFLECTION',



                resource_type='REFLECTION',



                resource_id=str(reflection.id),



                details=f"Giáo viên {user.username} gửi phản ánh {reflection.reflection_code} cho lớp {school_class.name}. Tuyệt đối không trừ điểm.",



                ip_address=request.META.get('REMOTE_ADDR')



            )







        serializer = self.get_serializer(reflection)



        data = serializer.data



        data['reflection_id'] = reflection.id



        data['message'] = 'Gửi phản ánh nề nếp thành công.'



        return Response(data, status=status.HTTP_201_CREATED)







    @action(detail=True, methods=['post'], url_path='process')



    def process_reflection(self, request, pk=None):



        reflection = self.get_object()



        user = request.user







        is_admin = user.is_admin or user.is_superuser



        is_hr = (reflection.school_class.homeroom_teacher_id == user.id) or HomeroomAssignment.objects.filter(



            teacher=user, school_class=reflection.school_class, is_active=True



        ).exists()







        if not is_admin and not is_hr:



            return Response(



                {'error': 'Chỉ Quản trị viên hoặc Giáo viên chủ nhiệm của lớp mới có quyền xử lý phản ánh này.'},



                status=status.HTTP_403_FORBIDDEN



            )







        action_type = request.data.get('action')



        feedback_notes = (request.data.get('feedback_notes') or '').strip()







        if action_type not in ['request_info', 'close', 'praise', 'convert_violation']:



            return Response({'error': 'Thao tác xử lý không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)







        previous_status = reflection.status







        with transaction.atomic():



            if action_type == 'request_info':



                reflection.status = TeacherReflection.STATUS_NEED_INFO



                reflection.feedback_notes = feedback_notes or 'Yêu cầu giáo viên bộ môn cung cấp thêm thông tin minh chứng.'



                reflection.processed_by = user



                reflection.processed_at = timezone.now()



                reflection.save()







                ReflectionHistory.objects.create(



                    reflection=reflection,



                    action='REQUEST_INFO',



                    performed_by=user,



                    previous_status=previous_status,



                    new_status=TeacherReflection.STATUS_NEED_INFO,



                    notes=reflection.feedback_notes



                )







            elif action_type == 'close':



                reflection.status = TeacherReflection.STATUS_CLOSED



                reflection.feedback_notes = feedback_notes or 'Đã xem xét và đóng phản ánh (không đủ căn cứ hoặc đã xử lý nội bộ).'



                reflection.processed_by = user



                reflection.processed_at = timezone.now()



                reflection.save()







                ReflectionHistory.objects.create(



                    reflection=reflection,



                    action='CLOSE',



                    performed_by=user,



                    previous_status=previous_status,



                    new_status=TeacherReflection.STATUS_CLOSED,



                    notes=reflection.feedback_notes



                )







            elif action_type == 'praise':



                reflection.status = TeacherReflection.STATUS_RESOLVED



                reflection.feedback_notes = feedback_notes or 'Đã biểu dương, ghi nhận tinh thần tích cực của học sinh.'



                reflection.processed_by = user



                reflection.processed_at = timezone.now()



                reflection.save()







                ReflectionHistory.objects.create(



                    reflection=reflection,



                    action='RESOLVE_PRAISE',



                    performed_by=user,



                    previous_status=previous_status,



                    new_status=TeacherReflection.STATUS_RESOLVED,



                    notes=reflection.feedback_notes



                )







            elif action_type == 'convert_violation':



                rule_id = request.data.get('rule_id')



                if not rule_id:



                    return Response({'error': 'Vui lòng chọn nội quy vi phạm để chuyển đổi xử lý thi đua.'}, status=status.HTTP_400_BAD_REQUEST)







                rule = ConductRule.objects.filter(id=rule_id, is_active=True).first()



                if not rule:



                    return Response({'error': 'Nội quy vi phạm không tồn tại hoặc đã bị vô hiệu hóa.'}, status=status.HTTP_400_BAD_REQUEST)







                from .services import create_violation_record



                violation = create_violation_record(



                    reporter=user,



                    class_id=reflection.school_class_id,



                    rule_id=rule.id,



                    student_id=reflection.student_id,



                    occurred_at=reflection.occurred_at,



                    location=f"Lớp {reflection.school_class.name}",



                    description=reflection.content,



                    evidence_image=reflection.evidence_image,



                    evidence_notes=f"Xác nhận từ phản ánh {reflection.reflection_code}. {feedback_notes}".strip(),



                    direct_deduct=True



                )







                reflection.violation_record = violation



                reflection.status = TeacherReflection.STATUS_RESOLVED



                reflection.feedback_notes = feedback_notes or f"Đã xác minh vi phạm [{rule.code}] {rule.name} và áp dụng trừ điểm theo quy chế."



                reflection.processed_by = user



                reflection.processed_at = timezone.now()



                reflection.save()







                ReflectionHistory.objects.create(



                    reflection=reflection,



                    action='CONVERT_VIOLATION',



                    performed_by=user,



                    previous_status=previous_status,



                    new_status=TeacherReflection.STATUS_RESOLVED,



                    notes=f"Đã lập bản ghi vi phạm {violation.record_code} (-{violation.points_deducted}đ)."



                )







            from core.models import Notification



            Notification.objects.create(



                recipient=reflection.teacher,



                notification_type=Notification.TYPE_SYSTEM,



                title=f'Cập nhật kết quả phản ánh {reflection.reflection_code}',



                message=f"Phản ánh về {reflection.student_name_snapshot} đã được {user.full_name or user.username} xử lý: {reflection.get_status_display()}.",



                link='/'



            )







        serializer = self.get_serializer(reflection)



        return Response(serializer.data)











class RedStarAssignmentViewSet(viewsets.ModelViewSet):



    """



    Quản lý phân công nhiệm vụ Sao đỏ / Cờ đỏ:



    - Admin có toàn quyền.



    - Đoàn trường cần quyền 'red_star.view' để xem, 'red_star.assign' để phân công/gia hạn, 'red_star.revoke' để thu hồi/tạm dừng.



    - GVCN, GVBM, Sao đỏ, Học sinh KHÔNG có quyền phân công (403 Forbidden).



    """



    queryset = RedStarAssignment.objects.all().select_related('user', 'student', 'assigned_class', 'assigned_by').prefetch_related('assigned_classes')



    serializer_class = RedStarAssignmentSerializer



    permission_classes = [permissions.IsAuthenticated]







    def check_permissions(self, request):



        super().check_permissions(request)



        if self.action in ['update', 'partial_update', 'destroy'] and not (request.user.is_admin or request.user.is_superuser):



            self.permission_denied(request, message='Hãy dùng thao tác phân công hoặc thu hồi có kiểm tra quyền và lưu lịch sử.')







    def get_queryset(self):



        user = self.request.user



        if user.is_admin or user.is_superuser:



            qs = super().get_queryset()



        elif user.is_doan_truong:



            allowed = {



                'list': user.has_custom_perm('red_star.view') or user.has_custom_perm('red_star.revoke'),



                'retrieve': user.has_custom_perm('red_star.view'),



                'revoke': user.has_custom_perm('red_star.revoke'),



                'suspend': user.has_custom_perm('red_star.revoke'),



                'reactivate': user.has_custom_perm('red_star.assign'),



            }.get(self.action, False)



            if not allowed:



                self.permission_denied(self.request, message='Bạn chưa được cấp quyền cho thao tác phân công Sao đỏ này.')



            qs = super().get_queryset()



        elif self.action == 'my_duty' and (getattr(user, 'is_active_red_star', False) or user.is_sao_do):



            return RedStarAssignment.objects.filter(user=user)



        else:



            self.permission_denied(self.request, message='Bạn không có quyền xem danh sách phân công Sao đỏ.')







        status_param = self.request.query_params.get('status')



        if status_param:



            qs = qs.filter(status=status_param)







        grade_param = self.request.query_params.get('grade')



        if grade_param:



            qs = qs.filter(Q(assigned_grade=grade_param) | Q(assigned_class__grade=grade_param) | Q(student__school_class__grade=grade_param))







        class_param = self.request.query_params.get('class_id')



        if class_param:



            qs = qs.filter(Q(assigned_class_id=class_param) | Q(assigned_classes__id=class_param))







        search = self.request.query_params.get('search')



        if search:



            q = search.strip()



            qs = qs.filter(



                Q(user__full_name__icontains=q)



                | Q(user__username__icontains=q)



                | Q(student__student_code__icontains=q)



                | Q(area_name__icontains=q)



            )







        return qs







    def create(self, request, *args, **kwargs):



        user = request.user



        if not (user.is_admin or (user.is_doan_truong and user.has_custom_perm('red_star.assign'))):



            return Response(



                {'error': 'Chỉ Quản trị viên hoặc Đoàn trường có quyền mới được phân công chức danh Sao đỏ.'},



                status=status.HTTP_403_FORBIDDEN



            )







        user_id = request.data.get('user') or request.data.get('user_id')



        student_id = request.data.get('student') or request.data.get('student_id')



        scope_type = request.data.get('scope_type', RedStarAssignment.SCOPE_CLASS)



        assigned_class_id = request.data.get('assigned_class') or request.data.get('assigned_class_id')



        assigned_class_ids = request.data.get('assigned_classes') or request.data.get('assigned_class_ids') or []



        assigned_grade = request.data.get('assigned_grade')



        area_name = request.data.get('area_name', '').strip()



        start_date_raw = request.data.get('start_date')



        end_date_raw = request.data.get('end_date')



        start_date = parse_date(str(start_date_raw)) if start_date_raw else timezone.localdate()



        end_date = parse_date(str(end_date_raw)) if end_date_raw else None



        notes = request.data.get('notes', '').strip()







        if start_date is None or (end_date_raw and end_date is None):



            return Response({'error': 'Ngày bắt đầu hoặc kết thúc không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)







        allowed_scopes = {value for value, _label in RedStarAssignment.SCOPE_CHOICES}



        if scope_type not in allowed_scopes:



            return Response({'error': 'Phạm vi phân công không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)







        target_user = None



        if user_id:



            target_user = User.objects.filter(id=user_id).first()



        elif student_id:



            st = Student.objects.filter(id=student_id).first()



            if st and st.user:



                target_user = st.user







        if not target_user:



            return Response({'error': 'Không tìm thấy tài khoản học sinh cần phân công.'}, status=status.HTTP_400_BAD_REQUEST)







        if target_user.pk == user.pk:



            return Response({'error': 'Không thể tự cấp nhiệm vụ Sao đỏ cho chính mình.'}, status=status.HTTP_403_FORBIDDEN)



        if target_user.role != User.ROLE_HOC_SINH:



            return Response({'error': 'Chỉ tài khoản học sinh mới đủ điều kiện nhận nhiệm vụ Sao đỏ.'}, status=status.HTTP_400_BAD_REQUEST)







        # QUY TẮC: Chỉ học sinh đã được duyệt tài khoản (APPROVED) mới được cấp chức danh Sao đỏ



        if target_user.account_status != User.STATUS_APPROVED:



            return Response(



                {'error': 'Chỉ học sinh đã được duyệt tài khoản chính thức (APPROVED) mới có thể được phân công làm Sao đỏ.'},



                status=status.HTTP_400_BAD_REQUEST



            )







        # Tạo hoặc lấy hồ sơ Student



        student_profile = getattr(target_user, 'student_profile', None)



        if not student_profile:



            return Response({'error': 'Học sinh chưa có hồ sơ trong danh sách lớp, chưa thể phân công Sao đỏ.'}, status=status.HTTP_400_BAD_REQUEST)







        if scope_type == RedStarAssignment.SCOPE_CLASS:



            if not assigned_class_id or not SchoolClass.objects.filter(id=assigned_class_id, is_active=True).exists():



                return Response({'error': 'Vui lòng chọn lớp đang hoạt động cho phạm vi phân công.'}, status=status.HTTP_400_BAD_REQUEST)



        elif scope_type == RedStarAssignment.SCOPE_MULTI_CLASS:



            if not isinstance(assigned_class_ids, list):



                return Response({'error': 'Danh sách lớp phân công không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)



            valid_class_ids = list(SchoolClass.objects.filter(id__in=assigned_class_ids, is_active=True).values_list('id', flat=True))



            if not valid_class_ids:



                return Response({'error': 'Vui lòng chọn ít nhất một lớp đang hoạt động.'}, status=status.HTTP_400_BAD_REQUEST)



            assigned_class_ids = valid_class_ids



        elif scope_type == RedStarAssignment.SCOPE_GRADE and assigned_grade not in [10, 11, 12, '10', '11', '12']:



            return Response({'error': 'Khối lớp phân công không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)



        elif scope_type == RedStarAssignment.SCOPE_AREA and not area_name:



            return Response({'error': 'Vui lòng nhập khu vực trực.'}, status=status.HTTP_400_BAD_REQUEST)



        if start_date and end_date and end_date < start_date:



            return Response({'error': 'Ngày kết thúc phải sau hoặc bằng ngày bắt đầu.'}, status=status.HTTP_400_BAD_REQUEST)







        with transaction.atomic():



            assignment = RedStarAssignment.objects.create(



                user=target_user,



                student=student_profile,



                scope_type=scope_type,



                assigned_class_id=assigned_class_id if scope_type == RedStarAssignment.SCOPE_CLASS else None,



                assigned_grade=assigned_grade if scope_type == RedStarAssignment.SCOPE_GRADE else None,



                area_name=area_name if scope_type == RedStarAssignment.SCOPE_AREA else '',



                assigned_by=user,



                start_date=start_date,



                end_date=end_date,



                status=RedStarAssignment.STATUS_ACTIVE,



                notes=notes



            )



            if scope_type == RedStarAssignment.SCOPE_MULTI_CLASS and assigned_class_ids:



                assignment.assigned_classes.set(assigned_class_ids)







            # Cập nhật cờ is_red_star trên hồ sơ Student



            if student_profile:



                student_profile.is_red_star = True



                student_profile.save(update_fields=['is_red_star'])







            AuditLog.objects.create(



                user=user,



                action='ASSIGN_RED_STAR',



                resource_type='RED_STAR',



                resource_id=str(assignment.id),



                details=(



                    f"{user.username} đã phân công học sinh {target_user.full_name or target_user.username} "



                    f"làm Sao đỏ (Phạm vi: {assignment.get_scope_display_text()})."



                ),



                ip_address=request.META.get('REMOTE_ADDR')



            )







        serializer = self.get_serializer(assignment)



        return Response({



            'message': f'Phân công Sao đỏ thành công cho học sinh {target_user.full_name or target_user.username}.',



            'assignment': serializer.data



        }, status=status.HTTP_201_CREATED)







    @action(detail=True, methods=['post'], url_path='revoke')



    def revoke(self, request, pk=None):



        """Thu hồi chức danh Sao đỏ"""



        user = request.user



        if not (user.is_admin or (user.is_doan_truong and user.has_custom_perm('red_star.revoke'))):



            return Response(



                {'error': 'Bạn không có quyền thu hồi chức danh Sao đỏ.'},



                status=status.HTTP_403_FORBIDDEN



            )







        assignment = self.get_object()



        reason = request.data.get('reason', '').strip()



        assignment.status = RedStarAssignment.STATUS_REVOKED



        assignment.revoked_by = user



        assignment.revoked_at = timezone.now()



        assignment.revoke_reason = reason



        assignment.save()







        # Kiểm tra xem học sinh còn phân công active nào khác không



        remaining = RedStarAssignment.objects.filter(



            user=assignment.user,



            status=RedStarAssignment.STATUS_ACTIVE



        ).exclude(id=assignment.id).exists()







        if not remaining and assignment.student:



            assignment.student.is_red_star = False



            assignment.student.save(update_fields=['is_red_star'])







        AuditLog.objects.create(



            user=user,



            action='REVOKE_RED_STAR',



            resource_type='RED_STAR',



            resource_id=str(assignment.id),



            details=f"{user.username} đã thu hồi chức danh Sao đỏ của {assignment.user.username}. Lý do: {reason or 'Không có'}",



            ip_address=request.META.get('REMOTE_ADDR')



        )







        return Response({



            'message': f'Đã thu hồi chức danh Sao đỏ của {assignment.user.full_name or assignment.user.username}.',



            'assignment': self.get_serializer(assignment).data



        })







    @action(detail=True, methods=['post'], url_path='suspend')



    def suspend(self, request, pk=None):



        """Tạm dừng nhiệm vụ Sao đỏ"""



        user = request.user



        if not (user.is_admin or (user.is_doan_truong and user.has_custom_perm('red_star.revoke'))):



            return Response({'error': 'Bạn không có quyền tạm dừng nhiệm vụ Sao đỏ.'}, status=status.HTTP_403_FORBIDDEN)







        assignment = self.get_object()



        reason = request.data.get('reason', '').strip()



        assignment.status = RedStarAssignment.STATUS_SUSPENDED



        assignment.revoke_reason = reason



        assignment.save(update_fields=['status', 'revoke_reason', 'updated_at'])







        AuditLog.objects.create(



            user=user,



            action='SUSPEND_RED_STAR',



            resource_type='RED_STAR',



            resource_id=str(assignment.id),



            details=f"{user.username} tạm dừng nhiệm vụ Sao đỏ của {assignment.user.username}.",



            ip_address=request.META.get('REMOTE_ADDR')



        )



        return Response({'message': f'Đã tạm dừng nhiệm vụ Sao đỏ của {assignment.user.username}.', 'assignment': self.get_serializer(assignment).data})







    @action(detail=True, methods=['post'], url_path='reactivate')



    def reactivate(self, request, pk=None):



        """Kích hoạt lại nhiệm vụ Sao đỏ"""



        user = request.user



        if not (user.is_admin or (user.is_doan_truong and user.has_custom_perm('red_star.assign'))):



            return Response({'error': 'Bạn không có quyền kích hoạt nhiệm vụ Sao đỏ.'}, status=status.HTTP_403_FORBIDDEN)







        assignment = self.get_object()



        assignment.status = RedStarAssignment.STATUS_ACTIVE



        assignment.save(update_fields=['status', 'updated_at'])







        if assignment.student:



            assignment.student.is_red_star = True



            assignment.student.save(update_fields=['is_red_star'])







        AuditLog.objects.create(



            user=user,



            action='REACTIVATE_RED_STAR',



            resource_type='RED_STAR',



            resource_id=str(assignment.id),



            details=f"{user.username} kích hoạt lại nhiệm vụ Sao đỏ của {assignment.user.username}.",



            ip_address=request.META.get('REMOTE_ADDR')



        )



        return Response({'message': f'Đã kích hoạt lại nhiệm vụ Sao đỏ của {assignment.user.username}.', 'assignment': self.get_serializer(assignment).data})







    @action(detail=False, methods=['get'], url_path='my-duty')



    def my_duty(self, request):



        """Dành cho học sinh đăng nhập xem ca trực và phạm vi nhiệm vụ của mình"""



        user = request.user



        assignments = RedStarAssignment.objects.filter(user=user, status=RedStarAssignment.STATUS_ACTIVE)



        active_list = []



        covered_classes = []



        for asgn in assignments:



            if asgn.is_active_now():



                active_list.append(RedStarAssignmentSerializer(asgn).data)



                if asgn.scope_type == RedStarAssignment.SCOPE_CLASS and asgn.assigned_class:



                    covered_classes.append({'id': asgn.assigned_class.id, 'name': asgn.assigned_class.name})



                elif asgn.scope_type == RedStarAssignment.SCOPE_MULTI_CLASS:



                    for c in asgn.assigned_classes.all():



                        covered_classes.append({'id': c.id, 'name': c.name})



                elif asgn.scope_type == RedStarAssignment.SCOPE_GRADE and asgn.assigned_grade:



                    for c in SchoolClass.objects.filter(grade=asgn.assigned_grade, is_active=True):



                        covered_classes.append({'id': c.id, 'name': c.name})



                elif asgn.scope_type in [RedStarAssignment.SCOPE_ALL_SCHOOL, RedStarAssignment.SCOPE_AREA]:



                    for c in SchoolClass.objects.filter(is_active=True):



                        covered_classes.append({'id': c.id, 'name': c.name})







        unique_classes = {c['id']: c for c in covered_classes}.values()







        return Response({



            'is_sao_do': len(active_list) > 0 or getattr(user, 'is_active_red_star', False) or user.role == User.ROLE_SAO_DO,



            'active_assignments': active_list,



            'covered_classes': list(unique_classes)



        })







    @action(detail=False, methods=['get'], url_path='stats')



    def stats(self, request):



        """Thống kê tổng quan tình hình Sao đỏ"""



        user = request.user



        if not (user.is_admin or (user.is_doan_truong and user.has_custom_perm('red_star.view'))):



            return Response({'error': 'Bạn không có quyền xem thống kê phân công Sao đỏ.'}, status=status.HTTP_403_FORBIDDEN)



        total = RedStarAssignment.objects.count()



        active = RedStarAssignment.objects.filter(status=RedStarAssignment.STATUS_ACTIVE).count()



        suspended = RedStarAssignment.objects.filter(status=RedStarAssignment.STATUS_SUSPENDED).count()



        revoked = RedStarAssignment.objects.filter(status=RedStarAssignment.STATUS_REVOKED).count()



        return Response({



            'total': total,



            'active': active,



            'suspended': suspended,



            'revoked': revoked,



        })











class RedStarReportViewSet(viewsets.ModelViewSet):



    """



    Báo cáo ghi nhận nền nếp của Sao đỏ:



    - Sao đỏ gửi báo cáo: luôn ở trạng thái Chờ xác minh (PENDING).



    - KHÔNG tự động trừ điểm thi đua của lớp/học sinh.



    - Sao đỏ không thể tự xác minh báo cáo của mình.



    """



    queryset = RedStarReport.objects.all().select_related('reporter', 'school_class', 'student', 'rule', 'reviewed_by')



    serializer_class = RedStarReportSerializer



    permission_classes = [permissions.IsAuthenticated]







    def check_permissions(self, request):



        super().check_permissions(request)



        if self.action in ['update', 'partial_update', 'destroy'] and not (request.user.is_admin or request.user.is_superuser or request.user.is_doan_truong):



            self.permission_denied(request, message='Không thể sửa hoặc xóa báo cáo đã gửi.')







    def get_queryset(self):



        user = self.request.user



        if user.is_admin or user.is_superuser or user.is_doan_truong:



            qs = super().get_queryset()



        else:



            qs = RedStarReport.objects.filter(reporter=user)







        class_id = self.request.query_params.get('class_id')



        status_param = self.request.query_params.get('status')



        if class_id:



            qs = qs.filter(school_class_id=class_id)



        if status_param:



            qs = qs.filter(status=status_param)



        return qs







    def create(self, request, *args, **kwargs):



        user = request.user



        if not (user.is_admin or user.is_superuser or user.is_doan_truong or getattr(user, 'is_active_red_star', False)):



            return Response(



                {'error': 'Chỉ Sao đỏ đang có nhiệm vụ được phân công mới có quyền gửi báo cáo nền nếp.'},



                status=status.HTTP_403_FORBIDDEN



            )







        class_id = request.data.get('school_class') or request.data.get('class_id')



        rule_id = request.data.get('rule') or request.data.get('rule_id')



        incident_type = request.data.get('incident_type', '').strip()



        student_id = request.data.get('student') or request.data.get('student_id')



        student_name_snapshot = request.data.get('student_name_snapshot', '').strip()



        location = request.data.get('location', 'Khuôn viên trường')



        description = request.data.get('description', '').strip()



        evidence_image = request.FILES.get('evidence_image')







        school_class = SchoolClass.objects.filter(id=class_id).first()



        if not school_class:



            return Response({'error': 'Vui lòng chọn lớp học hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)



        if not school_class.is_active:



            return Response({'error': 'Không thể gửi báo cáo cho lớp đã ngừng hoạt động.'}, status=status.HTTP_400_BAD_REQUEST)







        # Kiểm tra phạm vi nhiệm vụ của Sao đỏ



        assignment = None



        if getattr(user, 'is_active_red_star', False) and not (user.is_admin or user.is_doan_truong):



            active_assignments = user.red_star_assignments.filter(



                status=RedStarAssignment.STATUS_ACTIVE,



                start_date__lte=timezone.localdate(),



            ).filter(Q(end_date__isnull=True) | Q(end_date__gte=timezone.localdate()))



            assignment = next((asgn for asgn in active_assignments if asgn.can_cover_class(school_class)), None)



            if not assignment:



                return Response(



                    {'error': 'Học sinh Sao đỏ chỉ được ghi nhận vi phạm trong phạm vi lớp/khối/khu vực được phân công.'},



                    status=status.HTTP_400_BAD_REQUEST



                )







        student = None



        if student_id:



            student = Student.objects.filter(id=student_id, school_class=school_class, status='STUDYING').first()



            if not student:



                return Response({'error': 'Học sinh không thuộc lớp đang chọn hoặc không còn trạng thái đang học.'}, status=status.HTTP_400_BAD_REQUEST)







        incident_time_raw = request.data.get('incident_time')



        incident_time = timezone.now()



        if incident_time_raw:



            incident_time = parse_datetime(str(incident_time_raw))



            if incident_time is None:



                return Response({'error': 'Thời điểm sự việc không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)



            if timezone.is_naive(incident_time):



                incident_time = timezone.make_aware(incident_time, timezone.get_current_timezone())



            if incident_time > timezone.now() + timedelta(minutes=5):



                return Response({'error': 'Thời điểm sự việc không thể ở tương lai.'}, status=status.HTTP_400_BAD_REQUEST)







        rule_obj = ConductRule.objects.filter(id=rule_id).first() if rule_id else None



        if not incident_type and rule_obj:



            incident_type = rule_obj.name







        report = RedStarReport.objects.create(



            reporter=user,



            assignment=assignment,



            school_class=school_class,



            student=student,



            student_name_snapshot=student.full_name if student else '',



            rule=rule_obj,



            incident_type=incident_type or 'Vi phạm nền nếp',



            incident_time=incident_time,



            location=location,



            description=description,



            evidence_image=evidence_image,



            status=RedStarReport.STATUS_PENDING



        )







        AuditLog.objects.create(



            user=user,



            action='RED_STAR_REPORT',



            resource_type='RED_STAR_REPORT',



            resource_id=report.report_code,



            details=f"Sao đỏ {user.username} gửi báo cáo nền nếp [{report.incident_type}] đối với {report.student_name_snapshot} ({school_class.name}).",



            ip_address=request.META.get('REMOTE_ADDR')



        )







        return Response({



            'message': 'Đã gửi báo cáo nền nếp thành công. Báo cáo đang chờ Quản trị viên xử lý.',



            'report': self.get_serializer(report).data



        }, status=status.HTTP_201_CREATED)







    @action(detail=True, methods=['post'], url_path='verify')



    def verify(self, request, pk=None):



        """Xác minh báo cáo của Sao đỏ bởi Admin hoặc Đoàn trường"""



        user = request.user



        if not (user.is_admin or user.is_superuser or user.is_doan_truong):



            return Response({'error': 'Bạn không có quyền xác minh báo cáo nền nếp.'}, status=status.HTTP_403_FORBIDDEN)







        report = self.get_object()



        if report.reporter_id == user.id:



            return Response({'error': 'Người gửi báo cáo không được tự xác minh báo cáo của mình.'}, status=status.HTTP_400_BAD_REQUEST)







        verdict = request.data.get('status')



        review_note = request.data.get('review_note', '').strip()







        if verdict not in [RedStarReport.STATUS_VERIFIED, RedStarReport.STATUS_REJECTED, RedStarReport.STATUS_RESOLVED]:



            return Response({'error': 'Trạng thái xác minh không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)







        report.status = verdict



        report.reviewed_by = user



        report.reviewed_at = timezone.now()



        report.review_note = review_note



        report.save()







        if verdict == RedStarReport.STATUS_VERIFIED and report.rule:



            from .services import create_violation_record



            try:



                v = create_violation_record(



                    class_id=report.school_class_id,



                    rule_id=report.rule_id,



                    reporter=user,



                    student_id=report.student_id,



                    location=report.location,



                    description=f"[Từ báo cáo Sao đỏ {report.report_code}] {report.description}",



                    occurred_at=report.incident_time,



                    direct_deduct=True



                )



                report.violation_record = v



                report.save(update_fields=['violation_record'])



            except Exception:



                pass







        AuditLog.objects.create(



            user=user,



            action='VERIFY_RED_STAR_REPORT',



            resource_type='RED_STAR_REPORT',



            resource_id=report.report_code,



            details=f"{user.username} đã xác minh báo cáo {report.report_code}: {report.get_status_display()}.",



            ip_address=request.META.get('REMOTE_ADDR')



        )







        return Response({



            'message': f'Đã cập nhật trạng thái báo cáo: {report.get_status_display()}.',



            'report': self.get_serializer(report).data



        })



























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
                    'monitor_id': c.monitor_id,
                    'monitor_name': c.monitor.full_name if c.monitor else None,
                    'can_assign_monitor': True,



                }



        elif user.is_student or getattr(user, 'role', '') == 'HOC_SINH':
            student = getattr(user, 'student_profile', None)
            if not student:
                student = Student.objects.filter(user=user).first()
            if not student and user.full_name:
                unlinked = Student.objects.filter(user__isnull=True, full_name__iexact=user.full_name.strip()).first()
                if unlinked:
                    unlinked.user = user
                    unlinked.save(update_fields=['user'])
                    if not user.department_or_class and unlinked.school_class:
                        user.department_or_class = unlinked.school_class.name
                        user.save(update_fields=['department_or_class'])
                    student = unlinked
            sclass = student.school_class if student else None
            if not sclass and user.department_or_class:
                clean_dept = user.department_or_class.replace('Lớp', '').replace('lop', '').strip()
                sclass = SchoolClass.objects.filter(name__iexact=clean_dept, is_active=True).first()
                if not sclass:
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
                    'monitor_id': sclass.monitor_id,
                    'monitor_name': sclass.monitor.full_name if sclass.monitor else None,
                    'can_assign_monitor': False,
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



                    'homeroom_teacher_id': user.id,
                    'monitor_id': c.monitor_id,
                    'monitor_name': c.monitor.full_name if c.monitor else None,
                    'can_assign_monitor': True,



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



                        'homeroom_teacher_id': c.homeroom_teacher_id,
                        'monitor_id': c.monitor_id,
                        'monitor_name': c.monitor.full_name if c.monitor else None,
                        'can_assign_monitor': False,
                    }







        res = list(classes_map.values())



        res.sort(key=lambda x: natural_class_sort_key(x['name']))



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







        elif user.is_student or getattr(user, 'role', '') == 'HOC_SINH':
            student = getattr(user, 'student_profile', None)
            if not student:
                student = Student.objects.filter(user=user).first()
            if student and student.school_class_id == school_class.id:
                has_access = True
            elif user.department_or_class:
                clean_dept = user.department_or_class.replace('Lớp', '').replace('lop', '').strip().lower()
                if clean_dept == school_class.name.strip().lower() or user.department_or_class.strip().lower() == school_class.name.strip().lower():
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



            .annotate(cnt=Count('id'))



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
                'is_class_monitor': bool(getattr(s, 'is_class_monitor', False) or (school_class.monitor_id == s.id)),



            })







        students_list.sort(key=lambda item: get_vietnamese_sort_key(item['full_name']))







        for idx, item in enumerate(students_list, start=1):



            item['stt'] = idx







        return Response({
            'class_id': school_class.id,
            'class_name': school_class.name,
            'grade': school_class.grade,
            'monitor_id': school_class.monitor_id,
            'monitor_name': school_class.monitor.full_name if school_class.monitor else None,
            'can_assign_monitor': bool(
                user.is_admin or user.is_bgh or user.is_doan_truong or
                (user.is_gvcn and (school_class.homeroom_teacher_id == user.id or HomeroomAssignment.objects.filter(school_class=school_class, teacher=user, is_active=True).exists()))
            ),
            'total_students': len(students_list),
            'students': students_list
        })

    @action(detail=True, methods=['post'], url_path='assign-monitor')
    def assign_monitor(self, request, pk=None):
        """
        Đoàn trường, Admin, và Giáo viên chủ nhiệm của lớp có quyền phân công hoặc hủy Lớp trưởng.
        """
        user = request.user
        school_class = get_object_or_404(SchoolClass, pk=pk)

        # RBAC Check: Only Admin, BGH, Đoàn trường, or GVCN of THIS specific class
        is_admin_or_doan = user.is_admin or user.is_bgh or user.is_doan_truong
        is_homeroom_of_class = user.is_gvcn and (
            school_class.homeroom_teacher_id == user.id or
            HomeroomAssignment.objects.filter(school_class=school_class, teacher=user, is_active=True).exists()
        )

        if not (is_admin_or_doan or is_homeroom_of_class):
            return Response(
                {'error': 'Chỉ Quản trị viên, Đoàn trường hoặc Giáo viên chủ nhiệm của lớp này mới có quyền phân công Lớp trưởng.'},
                status=status.HTTP_403_FORBIDDEN
            )

        student_id = request.data.get('student_id')
        if student_id:
            student = get_object_or_404(Student, pk=student_id, school_class=school_class)
            # Remove previous monitors of this class
            Student.objects.filter(school_class=school_class, is_class_monitor=True).exclude(pk=student.id).update(is_class_monitor=False)
            student.is_class_monitor = True
            student.save(update_fields=['is_class_monitor'])
            school_class.monitor = student
            school_class.save(update_fields=['monitor'])

            try:
                AuditLog.objects.create(
                    user=user,
                    action='ASSIGN_MONITOR',
                    resource_type='SCHOOL_CLASS',
                    resource_id=school_class.name,
                    details=f"Phân công học sinh {student.full_name} ({student.student_code}) làm Lớp trưởng lớp {school_class.name}"
                )
            except Exception:
                pass

            return Response({
                'success': True,
                'message': f'Đã phân công học sinh {student.full_name} làm Lớp trưởng lớp {school_class.name}.',
                'class_id': school_class.id,
                'monitor_id': student.id,
                'monitor_name': student.full_name,
                'monitor_student_code': student.student_code,
            })
        else:
            # Unassign monitor
            if school_class.monitor:
                prev_monitor = school_class.monitor
                prev_monitor.is_class_monitor = False
                prev_monitor.save(update_fields=['is_class_monitor'])
            Student.objects.filter(school_class=school_class, is_class_monitor=True).update(is_class_monitor=False)
            school_class.monitor = None
            school_class.save(update_fields=['monitor'])

            try:
                AuditLog.objects.create(
                    user=user,
                    action='REMOVE_MONITOR',
                    resource_type='SCHOOL_CLASS',
                    resource_id=school_class.name,
                    details=f"Hủy phân công Lớp trưởng lớp {school_class.name}"
                )
            except Exception:
                pass

            return Response({
                'success': True,
                'message': f'Đã hủy phân công Lớp trưởng lớp {school_class.name}.',
                'class_id': school_class.id,
                'monitor_id': None,
                'monitor_name': None,
                'monitor_student_code': None,
            })

















    @action(detail=False, methods=['get'], url_path='eligible-teachers')



    def eligible_teachers(self, request):



        user = request.user



        if not (user.is_admin or user.is_bgh or user.is_doan_truong):



            return Response({'error': 'Bạn không có quyền thực hiện chức năng này.'}, status=status.HTTP_403_FORBIDDEN)







        teachers = User.objects.filter(



            Q(role__in=[User.ROLE_GVBM, User.ROLE_GVCN]) |



            Q(teacher_profile__isnull=False) |



            Q(teaching_assignments__isnull=False) |



            Q(homeroom_assignments__isnull=False),



            account_status=User.STATUS_APPROVED,



            is_active=True



        ).distinct().order_by('full_name', 'username')







        res = []



        for t in teachers:



            active_hr = t.homeroom_assignments.filter(is_active=True).select_related('school_class').first()



            if not active_hr and hasattr(t, 'homeroom_classes'):



                active_hr_class = t.homeroom_classes.filter(is_active=True).first()



            else:



                active_hr_class = active_hr.school_class if active_hr else None







            subject_val = ''



            if hasattr(t, 'teacher_profile') and t.teacher_profile.subject:



                subject_val = t.teacher_profile.subject



            elif t.department_or_class and t.department_or_class.startswith('Môn '):



                subject_val = t.department_or_class[4:].strip()



            else:



                subject_val = t.department_or_class or 'Chưa phân môn'







            res.append({



                'id': t.id,



                'full_name': t.full_name or t.username,



                'username': t.username,



                'role': t.role,



                'role_display': t.get_role_display(),



                'subject': subject_val,



                'current_homeroom_class': active_hr_class.name if active_hr_class else None,



            })







        return Response(res)







    @action(detail=True, methods=['post'], url_path='assign-homeroom')



    def assign_homeroom(self, request, pk=None):



        user = request.user



        if not (user.is_admin or user.is_bgh or user.is_doan_truong):



            return Response({'error': 'Chỉ Quản trị viên (Admin) hoặc Ban Giám hiệu mới có quyền phân công GVCN.'}, status=status.HTTP_403_FORBIDDEN)







        sclass = get_object_or_404(SchoolClass, pk=pk)



        teacher_id = request.data.get('teacher_id')



        notes = request.data.get('notes', '').strip()



        force = (



            str(request.data.get('force', '')).lower() in ['true', '1'] or



            str(request.data.get('confirm_replace', '')).lower() in ['true', '1'] or



            request.data.get('confirm_replace') is True or



            request.data.get('force') is True



        )







        if not teacher_id:



            with transaction.atomic():



                HomeroomAssignment.objects.filter(school_class=sclass, is_active=True).update(



                    is_active=False,



                    end_date=timezone.now().date()



                )



                sclass.homeroom_teacher = None



                sclass.save(update_fields=['homeroom_teacher'])







                AuditLog.objects.create(



                    user=user,



                    action='REVOKE_HOMEROOM_TEACHER',



                    resource_type='SCHOOL_CLASS',



                    resource_id=str(sclass.id),



                    details=f"Admin {user.username} đã thu hồi phân công GVCN lớp {sclass.name}.",



                    ip_address=request.META.get('REMOTE_ADDR')



                )







            return Response({



                'success': True,



                'message': f"Đã thu hồi phân công GVCN lớp {sclass.name}.",



                'class_id': sclass.id,



                'class_name': sclass.name,



                'homeroom_teacher_id': None,



                'homeroom_teacher_name': 'Chưa phân công'



            })







        teacher = User.objects.filter(pk=teacher_id).first()



        if not teacher:



            return Response({'error': 'Không tìm thấy giáo viên được chọn.'}, status=status.HTTP_404_NOT_FOUND)







        if teacher.account_status != User.STATUS_APPROVED:



            return Response({'error': 'Không thể bổ nhiệm tài khoản chưa được phê duyệt.'}, status=status.HTTP_400_BAD_REQUEST)



        if not teacher.is_active:



            return Response({'error': 'Không thể bổ nhiệm tài khoản đang bị khóa.'}, status=status.HTTP_400_BAD_REQUEST)







        current_assignment = HomeroomAssignment.objects.filter(school_class=sclass, is_active=True).select_related('teacher').first()



        current_teacher = sclass.homeroom_teacher or (current_assignment.teacher if current_assignment else None)







        if current_teacher and current_teacher.id != teacher.id:



            if not force:



                current_name = current_teacher.full_name or current_teacher.username



                msg = f"Lớp {sclass.name} hiện đã có GVCN là {current_name}. Bạn có chắc chắn muốn thay thế {current_name} bằng {teacher.full_name or teacher.username} làm GVCN mới?"



                return Response({



                    'warning': True,



                    'conflict': True,



                    'message': msg,



                    'error': msg,



                    'current_gvcn_id': current_teacher.id,



                    'current_gvcn_name': current_name,



                    'class_name': sclass.name,



                }, status=status.HTTP_409_CONFLICT)







        with transaction.atomic():



            if current_assignment and current_assignment.teacher_id != teacher.id:



                current_assignment.is_active = False



                current_assignment.end_date = timezone.now().date()



                current_assignment.save(update_fields=['is_active', 'end_date', 'updated_at'])







            HomeroomAssignment.objects.filter(teacher=teacher, is_active=True).exclude(school_class=sclass).update(



                is_active=False,



                end_date=timezone.now().date()



            )







            HomeroomAssignment.objects.create(



                teacher=teacher,



                school_class=sclass,



                assigned_by=user,



                start_date=timezone.now().date(),



                is_active=True,



                notes=notes



            )







            sclass.homeroom_teacher = teacher



            sclass.save(update_fields=['homeroom_teacher'])







            if teacher.role not in [User.ROLE_ADMIN, User.ROLE_SUPER_ADMIN, User.ROLE_BGH]:



                teacher.role = User.ROLE_GVCN



                teacher.save(update_fields=['role'])







            AuditLog.objects.create(



                user=user,



                action='APPOINT_HOMEROOM_TEACHER',



                resource_type='SCHOOL_CLASS',



                resource_id=str(sclass.id),



                details=f"Admin {user.username} đã phân công {teacher.full_name or teacher.username} làm GVCN lớp {sclass.name}. Ghi chú: {notes}",



                ip_address=request.META.get('REMOTE_ADDR')



            )







            try:



                from core.models import Notification



                Notification.objects.create(



                    recipient=teacher,



                    notification_type=Notification.TYPE_SYSTEM,



                    title='Quyết định phân công Giáo viên chủ nhiệm',



                    message=f"Thầy/Cô đã được Quản trị viên phân công làm Giáo viên chủ nhiệm lớp {sclass.name} từ ngày {timezone.now().strftime('%d/%m/%Y')}.",



                    link='/#teacher-classes'



                )



            except Exception:



                pass







        return Response({



            'success': True,



            'message': f"Đã phân công Thầy/Cô {teacher.full_name or teacher.username} làm GVCN lớp {sclass.name} thành công.",



            'class_id': sclass.id,



            'class_name': sclass.name,



            'homeroom_teacher_id': teacher.id,



            'homeroom_teacher_name': teacher.full_name or teacher.username,



        })











    @action(detail=True, methods=['get'], url_path='assigned-teachers')
    def assigned_teachers(self, request, pk=None):
        """
        Lấy thông tin toàn bộ đội ngũ giáo viên của một lớp học:
        - Giáo viên chủ nhiệm (GVCN)
        - Toàn bộ Giáo viên bộ môn (GVBM) đang giảng dạy các môn
        """
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
            if not student:
                student = Student.objects.filter(user=user).first()
            if student and student.school_class_id == sclass.id:
                has_access = True
            elif user.department_or_class:
                clean_dept = user.department_or_class.replace('Lớp', '').replace('lop', '').strip().lower()
                if clean_dept == sclass.name.strip().lower() or user.department_or_class.strip().lower() == sclass.name.strip().lower():
                    has_access = True
        if not has_access:
            return Response({'error': 'Bạn không có quyền xem đội ngũ giáo viên của lớp học này.'}, status=status.HTTP_403_FORBIDDEN)
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
            return Response({'error': 'Bạn không có quyền xem đội ngũ giáo viên của lớp học này.'}, status=status.HTTP_403_FORBIDDEN)

        # 1. GVCN
        SUBJECT_MAP = {
            'TOAN': 'Toán học', 'VAN': 'Ngữ văn', 'ANH': 'Tiếng Anh',
            'LY': 'Vật lý', 'HOA': 'Hóa học', 'SINH': 'Sinh học',
            'SU': 'Lịch sử', 'DIA': 'Địa lý', 'GDCD': 'GDCD/GDKT&PL',
            'TIN': 'Tin học', 'CN': 'Công nghệ', 'TD': 'Giáo dục thể chất',
            'QP': 'Giáo dục QP-AN', 'AM_NHAC': 'Âm nhạc', 'MY_THUAT': 'Mỹ thuật',
            'HDTN': 'Hoạt động trải nghiệm'
        }
        hr_teacher = sclass.homeroom_teacher
        hr_data = None
        if hr_teacher:
            hr_assign = HomeroomAssignment.objects.filter(school_class=sclass, teacher=hr_teacher, is_active=True).first()
            hr_subj = ''
            if hasattr(hr_teacher, 'teacher_profile') and hr_teacher.teacher_profile:
                hr_subj = hr_teacher.teacher_profile.subject
            hr_data = {
                'id': hr_teacher.id,
                'full_name': hr_teacher.full_name or hr_teacher.username,
                'username': hr_teacher.username,
                'email': hr_teacher.email or '',
                'phone': hr_teacher.phone or '',
                'subject': hr_subj,
                'subject_display': SUBJECT_MAP.get(hr_subj, hr_subj),
                'start_date': str(hr_assign.start_date) if hr_assign else None,
                'notes': hr_assign.notes if hr_assign else ''
            }

        # 2. GVBM
        active_tcas = TeacherClassAssignment.objects.filter(
            school_class=sclass, is_active=True
        ).select_related('teacher', 'teacher__teacher_profile').order_by('subject', 'teacher__full_name')

        subject_teachers_data = []
        for tca in active_tcas:
            t = tca.teacher
            subject_teachers_data.append({
                'assignment_id': tca.id,
                'teacher_id': t.id,
                'teacher_name': t.full_name or t.username,
                'full_name': t.full_name or t.username,
                'teacher_username': t.username,
                'username': t.username,
                'teacher_email': t.email or '',
                'email': t.email or '',
                'teacher_phone': t.phone or '',
                'phone': t.phone or '',
                'subject': tca.subject,
                'subject_display': SUBJECT_MAP.get(tca.subject, tca.subject),
                'start_date': str(tca.start_date),
                'assigned_at': str(tca.start_date),
                'is_active': tca.is_active
            })

        return Response({
            'class_id': sclass.id,
            'class_name': sclass.name,
            'grade': sclass.grade,
            'homeroom_teacher': hr_data,
            'subject_teachers': subject_teachers_data
        })

    @action(detail=True, methods=['post'], url_path='assign-subject-teacher')
    def assign_subject_teacher(self, request, pk=None):
        """Phân công giáo viên bộ môn cho lớp học này"""
        user = request.user
        if not (user.is_admin or user.is_bgh or user.is_doan_truong):
            return Response({'error': 'Chỉ Quản trị viên (Admin) hoặc Ban Giám hiệu mới có quyền phân công giáo viên.'}, status=status.HTTP_403_FORBIDDEN)

        sclass = get_object_or_404(SchoolClass, pk=pk)
        teacher_id = request.data.get('teacher_id')
        subject = (request.data.get('subject') or '').strip()

        if not teacher_id:
            return Response({'error': 'Vui lòng chọn giáo viên giảng dạy.'}, status=status.HTTP_400_BAD_REQUEST)
        if not subject:
            return Response({'error': 'Vui lòng nhập hoặc chọn môn giảng dạy.'}, status=status.HTTP_400_BAD_REQUEST)

        teacher = User.objects.filter(pk=teacher_id).first()
        if not teacher:
            return Response({'error': 'Không tìm thấy giáo viên được chọn.'}, status=status.HTTP_404_NOT_FOUND)
        if teacher.account_status != User.STATUS_APPROVED:
            return Response({'error': 'Không thể phân công tài khoản chưa được phê duyệt.'}, status=status.HTTP_400_BAD_REQUEST)
        if not teacher.is_active:
            return Response({'error': 'Không thể phân công tài khoản đang bị khóa.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            from conduct.models import Teacher
            t_prof, _ = Teacher.objects.get_or_create(
                user=teacher,
                defaults={
                    'teacher_code': f"GV-{timezone.now().strftime('%y%m')}-{teacher.id:04d}",
                    'full_name': teacher.full_name or teacher.username,
                    'subject': subject,
                    'phone': teacher.phone or ''
                }
            )

            tca, created = TeacherClassAssignment.objects.get_or_create(
                teacher=teacher,
                school_class=sclass,
                subject=subject,
                defaults={
                    'is_active': True,
                    'assigned_by': user,
                    'start_date': timezone.now().date()
                }
            )
            if not created and not tca.is_active:
                tca.is_active = True
                tca.end_date = None
                tca.save(update_fields=['is_active', 'end_date', 'updated_at'])

            AuditLog.objects.create(
                user=user,
                action='ASSIGN_SUBJECT_TEACHER',
                resource_type='SCHOOL_CLASS',
                resource_id=str(sclass.id),
                details=f"Admin {user.username} đã phân công {teacher.full_name or teacher.username} dạy môn {subject} tại lớp {sclass.name}.",
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return Response({
            'success': True,
            'message': f"Đã phân công Thầy/Cô {teacher.full_name or teacher.username} giảng dạy môn {subject} lớp {sclass.name} thành công.",
            'assignment_id': tca.id,
            'teacher_id': teacher.id,
            'teacher_name': teacher.full_name or teacher.username,
            'subject': subject,
            'class_id': sclass.id,
            'class_name': sclass.name
        })

    @action(detail=True, methods=['post'], url_path='remove-subject-teacher')
    def remove_subject_teacher(self, request, pk=None):
        """Hủy phân công giáo viên bộ môn khỏi lớp học này"""
        user = request.user
        if not (user.is_admin or user.is_bgh or user.is_doan_truong):
            return Response({'error': 'Chỉ Quản trị viên (Admin) hoặc Ban Giám hiệu mới có quyền thay đổi phân công.'}, status=status.HTTP_403_FORBIDDEN)

        sclass = get_object_or_404(SchoolClass, pk=pk)
        assignment_id = request.data.get('assignment_id')
        teacher_id = request.data.get('teacher_id')
        subject = request.data.get('subject')

        tca = None
        if assignment_id:
            tca = TeacherClassAssignment.objects.filter(pk=assignment_id, school_class=sclass).first()
        elif teacher_id and subject:
            tca = TeacherClassAssignment.objects.filter(school_class=sclass, teacher_id=teacher_id, subject=subject, is_active=True).first()

        if not tca:
            return Response({'error': 'Không tìm thấy phân công giảng dạy tương ứng.'}, status=status.HTTP_404_NOT_FOUND)

        tca.is_active = False
        tca.end_date = timezone.now().date()
        tca.save(update_fields=['is_active', 'end_date', 'updated_at'])

        AuditLog.objects.create(
            user=user,
            action='REMOVE_SUBJECT_TEACHER',
            resource_type='SCHOOL_CLASS',
            resource_id=str(sclass.id),
            details=f"Admin {user.username} đã hủy phân công GV {tca.teacher.username} dạy môn {tca.subject} tại lớp {sclass.name}.",
            ip_address=request.META.get('REMOTE_ADDR')
        )

        return Response({
            'success': True,
            'message': f"Đã thu hồi phân công môn {tca.subject} của Thầy/Cô {tca.teacher.full_name or tca.teacher.username} tại lớp {sclass.name}."
        })


class StudentFeedbackViewSet(viewsets.ModelViewSet):



    """



    Quản lý phản hồi học sinh dành cho GVCN và GVBM.



    """



    serializer_class = StudentFeedbackSerializer



    permission_classes = [permissions.IsAuthenticated]

    pagination_class = None







    def get_queryset(self):



        user = self.request.user



        qs = StudentFeedback.objects.select_related('student', 'school_class', 'teacher').prefetch_related('replies__author')







        if user.is_admin or user.is_bgh or user.is_doan_truong:



            pass



        elif user.is_student or getattr(user, 'role', '') == 'HOC_SINH':
            qs = qs.filter(student__user=user)
            return qs
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



            teacher_role = 'DOAN_TRUONG' if (user.is_doan_truong and not (user.is_admin or user.is_bgh)) else 'ADMIN'



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



