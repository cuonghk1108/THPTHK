from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ExportCompetitionExcelAPIView, ExportCompetitionPdfAPIView,
    ExportViolationsExcelAPIView, ExportViolationsPdfAPIView,
    ExportViolationDetailPdfAPIView, ReportExportHistoryViewSet
)

router = DefaultRouter()
router.register(r'history', ReportExportHistoryViewSet, basename='report-export-history')

urlpatterns = [
    path('competition/excel/<int:period_id>/', ExportCompetitionExcelAPIView.as_view(), name='export-competition-excel'),
    path('competition/pdf/<int:period_id>/', ExportCompetitionPdfAPIView.as_view(), name='export-competition-pdf'),
    path('violations/excel/', ExportViolationsExcelAPIView.as_view(), name='export-violations-excel'),
    path('violations/pdf/', ExportViolationsPdfAPIView.as_view(), name='export-violations-pdf'),
    path('violations/<int:violation_id>/pdf/', ExportViolationDetailPdfAPIView.as_view(), name='export-violation-detail-pdf'),
    path('', include(router.urls)),
]
