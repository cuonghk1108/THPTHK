from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScoreCriterionViewSet, CompetitionPeriodViewSet, ClassCompetitionScoreViewSet

router = DefaultRouter()
router.register(r'criteria', ScoreCriterionViewSet, basename='score-criterion')
router.register(r'periods', CompetitionPeriodViewSet, basename='competition-period')
router.register(r'scores', ClassCompetitionScoreViewSet, basename='class-competition-score')

urlpatterns = [
    path('', include(router.urls)),
]
