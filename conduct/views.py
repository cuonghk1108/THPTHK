from decimal import Decimal
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import User
from .models import SchoolClass, Student, Teacher, ConductRuleCategory, ConductRule, ViolationRecord
from .serializers import (
    SchoolClassSerializer, StudentSerializer, ConductRuleCategorySerializer,
    ConductRuleSerializer, ViolationRecordSerializer
)
from .services import create_violation_record, verify_violation, submit_violation_appeal


class SchoolClassViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SchoolClass.objects.all().select_related('academic_year', 'homeroom_teacher')
    serializer_class = SchoolClassSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        grade = self.request.query_params.get('grade')
        if grade:
            qs = qs.filter(grade=grade)
        return qs


class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Student.objects.all().select_related('school_class')
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        class_id = self.request.query_params.get('class_id')
        search = self.request.query_params.get('search')
        if class_id:
            qs = qs.filter(school_class_id=class_id)
        if search:
            qs = qs.filter(Q(full_name__icontains=search) | Q(student_code__icontains=search))
        return qs


class ConductRuleCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ConductRuleCategory.objects.all()
    serializer_class = ConductRuleCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class ConductRuleViewSet(viewsets.ModelViewSet):
    queryset = ConductRule.objects.all().select_related('category')
    serializer_class = ConductRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        category_id = self.request.query_params.get('category_id')
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs


class ViolationRecordViewSet(viewsets.ModelViewSet):
    queryset = ViolationRecord.objects.all().select_related('school_class', 'student', 'rule', 'rule__category', 'reporter', 'verified_by')
    serializer_class = ViolationRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        # Áp dụng bộ lọc quyền hạn (Object-Level RBAC)
        if user.is_admin or user.is_bgh or user.is_doan_truong:
            # Đoàn trường, BGH, Admin thấy toàn trường
            pass
        elif user.is_gvcn:
            # GVCN chỉ thấy vi phạm của lớp mình chủ nhiệm
            homeroom_classes = user.homeroom_classes.all()
            qs = qs.filter(school_class__in=homeroom_classes)
        elif user.is_student:
            # Học sinh CHỈ thấy vi phạm của bản thân mình
            if hasattr(user, 'student_profile'):
                qs = qs.filter(student=user.student_profile)
            else:
                qs = qs.none()
        elif user.is_sao_do:
            # Sao đỏ thấy các vi phạm do mình lập hoặc các vi phạm đã công bố
            qs = qs.filter(Q(reporter=user) | Q(status__in=[ViolationRecord.STATUS_VERIFIED, ViolationRecord.STATUS_ADJUSTED]))

        # Bộ lọc URL parameters
        class_id = self.request.query_params.get('class_id')
        status_filter = self.request.query_params.get('status')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        student_id = self.request.query_params.get('student_id')

        if class_id:
            qs = qs.filter(school_class_id=class_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if student_id:
            qs = qs.filter(student_id=student_id)
        if date_from:
            qs = qs.filter(occurred_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(occurred_at__date__lte=date_to)

        return qs

    def create(self, request, *args, **kwargs):
        """
        Quy trình nhập liệu vi phạm nhanh cho Sao đỏ & Giáo viên:
        Bước 1: Chọn lớp
        Bước 2: Chọn học sinh (hoặc tập thể)
        Bước 3: Chọn lỗi
        Bước 4: Thời gian, vị trí, mô tả
        Bước 5: Ảnh minh chứng (tùy chọn)
        Bước 6: Gửi bản ghi
        """
        class_id = request.data.get('school_class')
        student_id = request.data.get('student')
        rule_id = request.data.get('rule')
        location = request.data.get('location', 'Khuôn viên trường')
        description = request.data.get('description', '')
        occurred_at = request.data.get('occurred_at') or timezone.now()
        evidence_image = request.FILES.get('evidence_image')
        evidence_notes = request.data.get('evidence_notes', '')

        if not class_id or not rule_id:
            return Response({'error': 'Vui lòng chọn lớp học và lỗi vi phạm'}, status=status.HTTP_400_BAD_REQUEST)

        violation = create_violation_record(
            reporter=request.user,
            class_id=class_id,
            rule_id=rule_id,
            student_id=student_id if student_id else None,
            occurred_at=occurred_at,
            location=location,
            description=description,
            evidence_image=evidence_image,
            evidence_notes=evidence_notes
        )

        serializer = self.get_serializer(violation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='verify')
    def verify(self, request, pk=None):
        """
        Xác minh bản ghi vi phạm (Chỉ Đoàn trường / Admin).
        Kiểm tra nghiêm ngặt quyền hạn ở cả server-side!
        """
        user = request.user
        if not (user.is_admin or user.is_doan_truong or user.can_verify_violations):
            return Response({'error': 'Bạn không có thẩm quyền xác minh bản ghi vi phạm này'}, status=status.HTTP_403_FORBIDDEN)

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
        # Kiểm tra quyền: Chỉ học sinh liên quan, GVCN của lớp đó hoặc Admin mới được gửi giải trình
        is_owner_student = hasattr(user, 'student_profile') and violation.student_id == user.student_profile.id
        is_homeroom = user.is_gvcn and violation.school_class.homeroom_teacher_id == user.id

        if not (is_owner_student or is_homeroom or user.is_admin):
            return Response({'error': 'Bạn không có quyền khiếu nại bản ghi vi phạm này'}, status=status.HTTP_403_FORBIDDEN)

        updated_violation = submit_violation_appeal(violation.id, user, reason)
        serializer = self.get_serializer(updated_violation)
        return Response({
            'message': 'Đã gửi yêu cầu giải trình/khiếu nại thành công đến Đoàn trường',
            'violation': serializer.data
        })
