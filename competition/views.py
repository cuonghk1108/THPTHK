from decimal import Decimal
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ScoreCriterion, CompetitionPeriod, ClassCompetitionScore
from .serializers import ScoreCriterionSerializer, CompetitionPeriodSerializer, ClassCompetitionScoreSerializer
from .services import recalculate_period_scores, lock_competition_period, unlock_competition_period


class ScoreCriterionViewSet(viewsets.ModelViewSet):
    queryset = ScoreCriterion.objects.all().select_related('academic_year')
    serializer_class = ScoreCriterionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()


class CompetitionPeriodViewSet(viewsets.ModelViewSet):
    queryset = CompetitionPeriod.objects.all().select_related('academic_year', 'semester')
    serializer_class = CompetitionPeriodSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='scores')
    def scores(self, request, pk=None):
        """Lấy bảng xếp hạng thi đua của kỳ"""
        period = self.get_object()
        
        # Nếu chưa khóa và là Đoàn trường/Admin thì tự động cập nhật
        if not period.is_locked and (request.user.is_admin or request.user.is_doan_truong):
            recalculate_period_scores(period)

        scores = ClassCompetitionScore.objects.filter(competition_period=period).select_related('school_class', 'school_class__homeroom_teacher')
        
        grade = request.query_params.get('grade')
        if grade:
            scores = scores.filter(school_class__grade=grade)

        serializer = ClassCompetitionScoreSerializer(scores, many=True)
        return Response({
            'period': self.get_serializer(period).data,
            'scores': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='recalculate')
    def recalculate(self, request, pk=None):
        """Tính toán lại điểm thi đua tự động từ các bản ghi đã xác minh"""
        user = request.user
        if not (user.is_admin or user.is_doan_truong):
            return Response({'error': 'Bạn không có quyền tính lại điểm thi đua'}, status=status.HTTP_403_FORBIDDEN)

        period = self.get_object()
        if period.is_locked:
            return Response({'error': 'Kỳ thi đua đã chốt sổ, không thể tính lại'}, status=status.HTTP_400_BAD_REQUEST)

        recalculate_period_scores(period)
        return Response({'message': f'Đã cập nhật lại bảng xếp hạng thi đua kỳ [{period.name}] thành công'})

    @action(detail=True, methods=['post'], url_path='lock')
    def lock(self, request, pk=None):
        """Chốt sổ kỳ thi đua"""
        user = request.user
        if not (user.is_admin or user.is_bgh or user.is_doan_truong):
            return Response({'error': 'Bạn không có quyền chốt sổ thi đua'}, status=status.HTTP_403_FORBIDDEN)

        period = lock_competition_period(pk, user)
        return Response({'message': f'Đã chốt sổ kỳ thi đua [{period.name}] thành công'})

    @action(detail=True, methods=['post'], url_path='unlock')
    def unlock(self, request, pk=None):
        """Mở khóa kỳ thi đua (Chỉ BGH hoặc Admin)"""
        user = request.user
        if not (user.is_admin or user.is_bgh):
            return Response({'error': 'Chỉ Ban Giám hiệu hoặc Quản trị viên mới có quyền mở lại kỳ thi đua đã chốt'}, status=status.HTTP_403_FORBIDDEN)

        period = unlock_competition_period(pk, user)
        return Response({'message': f'Đã mở lại kỳ thi đua [{period.name}] để cập nhật dữ liệu'})


class ClassCompetitionScoreViewSet(viewsets.ModelViewSet):
    queryset = ClassCompetitionScore.objects.all().select_related('competition_period', 'school_class')
    serializer_class = ClassCompetitionScoreSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='add-bonus')
    def add_bonus(self, request, pk=None):
        """Đoàn trường cộng điểm phong trào cho Chi đoàn"""
        user = request.user
        if not (user.is_admin or user.is_doan_truong):
            return Response({'error': 'Chỉ Đoàn trường mới có quyền cộng điểm phong trào'}, status=status.HTTP_403_FORBIDDEN)

        score_obj = self.get_object()
        if score_obj.competition_period.is_locked:
            return Response({'error': 'Kỳ thi đua đã bị khóa'}, status=status.HTTP_400_BAD_REQUEST)

        bonus = request.data.get('bonus_points', 0)
        note = request.data.get('note', '')

        score_obj.bonus_points += Decimal(str(bonus))
        if note:
            score_obj.bonus_notes = f"{score_obj.bonus_notes}\n+{bonus}đ: {note}".strip()
        score_obj.calculate_total()
        score_obj.save()

        # Cập nhật lại thứ hạng
        recalculate_period_scores(score_obj.competition_period)

        serializer = self.get_serializer(score_obj)
        return Response({'message': 'Đã cộng điểm phong trào thành công', 'score': serializer.data})
