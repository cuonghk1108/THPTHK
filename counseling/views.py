from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CounselingRequest, CounselingPrivateNote
from .serializers import (
    CounselingRequestDetailSerializer, CounselingPublicTrackSerializer, CounselingPrivateNoteSerializer
)
from .services import submit_counseling_request, update_counseling_status, add_counseling_private_note


class CounselingSubmitAPIView(APIView):
    """
    Kênh gửi đề nghị hỗ trợ tâm lý học đường 'Góc sẻ chia'.
    Học sinh có thể chọn gửi ẩn danh hoặc có định danh.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        topic = request.data.get('topic')
        content = request.data.get('content')
        preferred_channel = request.data.get('preferred_channel', 'IN_PERSON')
        contact_info = request.data.get('contact_info', '')
        preferred_schedule = request.data.get('preferred_schedule', '')
        is_anonymous = request.data.get('is_anonymous', False)
        alias_name = request.data.get('alias_name', '')

        if not topic or not content:
            return Response({'error': 'Vui lòng chọn chủ đề và nhập nội dung cần sẻ chia'}, status=status.HTTP_400_BAD_REQUEST)

        student = None
        if request.user.is_authenticated and hasattr(request.user, 'student_profile') and not is_anonymous:
            student = request.user.student_profile

        req = submit_counseling_request(
            topic=topic,
            content=content,
            preferred_channel=preferred_channel,
            contact_info=contact_info,
            preferred_schedule=preferred_schedule,
            is_anonymous=is_anonymous,
            alias_name=alias_name,
            student=student
        )

        response_data = {
            'message': 'Đã gửi đề nghị hỗ trợ tâm lý thành công. Cán bộ tư vấn sẽ tiếp nhận và đồng hành cùng bạn.',
            'tracking_code': req.tracking_code,
            'is_urgent_safety': req.is_urgent_safety,
            'emergency_guidance': (
                "Nếu bạn hoặc bạn bè đang trong tình huống khẩn cấp, cảm thấy không an toàn hoặc có ý định tự gây hại, "
                "hãy liên hệ ngay người lớn đáng tin cậy hoặc gọi Tổng đài Quốc gia Bảo vệ Trẻ em: 111 (miễn phí 24/7) "
                "hoặc đến trực tiếp Phòng Y tế / Tư vấn tâm lý Trường THPT Hương Khê."
            ) if req.is_urgent_safety else ""
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class CounselingTrackAPIView(APIView):
    """Tra cứu tiến độ hỗ trợ bằng mã hồ sơ bảo mật (không yêu cầu đăng nhập)"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, tracking_code):
        try:
            req = CounselingRequest.objects.get(tracking_code=tracking_code)
            serializer = CounselingPublicTrackSerializer(req)
            return Response(serializer.data)
        except CounselingRequest.DoesNotExist:
            return Response({'error': 'Không tìm thấy hồ sơ với mã tra cứu này'}, status=status.HTTP_404_NOT_FOUND)


class CounselingRequestViewSet(viewsets.ModelViewSet):
    """
    Phân hệ quản lý dành riêng cho Chuyên viên tư vấn tâm lý học đường.
    NGHIÊM NGẶT: Chỉ tài khoản có 'has_counseling_access' mới được truy cập!
    """
    queryset = CounselingRequest.objects.all().select_related('student', 'assigned_counselor').prefetch_related('private_notes')
    serializer_class = CounselingRequestDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.has_counseling_access:
            # Nếu người dùng không có quyền chuyên biệt: Tuyệt đối không trả về dữ liệu!
            return CounselingRequest.objects.none()

        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        topic_filter = self.request.query_params.get('topic')
        urgent_filter = self.request.query_params.get('is_urgent')

        if status_filter:
            qs = qs.filter(status=status_filter)
        if topic_filter:
            qs = qs.filter(topic=topic_filter)
        if urgent_filter is not None:
            qs = qs.filter(is_urgent_safety=urgent_filter.lower() == 'true')

        return qs

    def check_permissions(self, request):
        super().check_permissions(request)
        if not request.user.has_counseling_access:
            self.permission_denied(
                request,
                message='Bạn không có quyền truy cập hồ sơ tư vấn tâm lý nhạy cảm. Đây là khu vực bảo mật chuyên biệt.'
            )

    @action(detail=True, methods=['post'], url_path='update-status')
    def change_status(self, request, pk=None):
        new_status = request.data.get('status')
        scheduled_meeting = request.data.get('scheduled_meeting')

        if not new_status:
            return Response({'error': 'Vui lòng cung cấp trạng thái mới'}, status=status.HTTP_400_BAD_REQUEST)

        req = update_counseling_status(
            request_id=pk,
            counselor=request.user,
            new_status=new_status,
            scheduled_meeting=scheduled_meeting
        )
        serializer = self.get_serializer(req)
        return Response({'message': 'Cập nhật trạng thái hỗ trợ thành công', 'request': serializer.data})

    @action(detail=True, methods=['post'], url_path='add-note')
    def add_note(self, request, pk=None):
        note_content = request.data.get('note_content')
        recommendation = request.data.get('recommendation', '')

        if not note_content:
            return Response({'error': 'Vui lòng nhập nội dung ghi chép chuyên môn'}, status=status.HTTP_400_BAD_REQUEST)

        note = add_counseling_private_note(
            request_id=pk,
            counselor=request.user,
            note_content=note_content,
            recommendation=recommendation
        )
        serializer = CounselingPrivateNoteSerializer(note)
        return Response({'message': 'Đã lưu ghi chép chuyên môn an toàn', 'note': serializer.data})
