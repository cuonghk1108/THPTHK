from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import EarlyWarningRule, EarlyWarningAlert, HomeroomIntervention
from .serializers import EarlyWarningRuleSerializer, EarlyWarningAlertSerializer, HomeroomInterventionSerializer
from .services import record_gvcn_intervention


class EarlyWarningRuleViewSet(viewsets.ModelViewSet):
    queryset = EarlyWarningRule.objects.all()
    serializer_class = EarlyWarningRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()


class EarlyWarningAlertViewSet(viewsets.ModelViewSet):
    queryset = EarlyWarningAlert.objects.all().select_related('school_class', 'student', 'rule', 'homeroom_teacher')
    serializer_class = EarlyWarningAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if user.is_admin or user.is_bgh or user.is_doan_truong:
            pass
        elif user.is_gvcn:
            # GVCN chỉ thấy cảnh báo liên quan đến lớp của mình
            homeroom_classes = user.homeroom_classes.all()
            qs = qs.filter(school_class__in=homeroom_classes)
        else:
            # Học sinh hoặc vai trò khác không thấy cảnh báo sư phạm
            qs = qs.none()

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs

    @action(detail=True, methods=['post'], url_path='intervene')
    def intervene(self, request, pk=None):
        """
        GVCN ghi nhận biện pháp hỗ trợ và kết quả theo dõi.
        """
        alert = self.get_object()
        action_taken = request.data.get('action_taken')
        outcome = request.data.get('outcome', '')
        intervention_status = request.data.get('status', 'COMPLETED')

        if not action_taken:
            return Response({'error': 'Vui lòng mô tả biện pháp sư phạm đã thực hiện'}, status=status.HTTP_400_BAD_REQUEST)

        intervention = record_gvcn_intervention(
            alert_id=alert.id,
            teacher=request.user,
            action_taken=action_taken,
            outcome=outcome,
            status=intervention_status
        )

        serializer = self.get_serializer(alert)
        return Response({
            'message': 'Đã ghi nhận biện pháp hỗ trợ học sinh thành công',
            'alert': serializer.data
        })
