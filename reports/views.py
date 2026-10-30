from django.http import HttpResponse
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ReportExportHistory
from .services import (
    export_competition_excel,
    export_competition_pdf,
    export_violations_excel,
    export_violations_pdf,
    export_violation_detail_pdf,
)


class DoanRestrictedAPIView(APIView):
    """Report exports include school-wide score and discipline records."""

    def check_permissions(self, request):
        super().check_permissions(request)


class ExportCompetitionExcelAPIView(DoanRestrictedAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, period_id):
        excel_content = export_competition_excel(period_id=period_id, exported_by=request.user)
        response = HttpResponse(
            excel_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="Thi_Dua_Chi_Doan_THPT_Huong_Khe_Ky_{period_id}.xlsx"'
        return response


class ExportCompetitionPdfAPIView(DoanRestrictedAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, period_id):
        pdf_content = export_competition_pdf(period_id=period_id, exported_by=request.user)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Bang_Xep_Hang_Thi_Dua_THPT_Huong_Khe_{period_id}.pdf"'
        return response


class ExportViolationsExcelAPIView(DoanRestrictedAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        filters = {
            'class_id': request.query_params.get('class_id'),
            'status': request.query_params.get('status'),
            'start_date': request.query_params.get('start_date'),
            'end_date': request.query_params.get('end_date'),
        }
        excel_content = export_violations_excel(filters=filters, exported_by=request.user)
        response = HttpResponse(
            excel_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="Danh_Sach_Vi_Pham_THPT_Huong_Khe.xlsx"'
        return response


class ExportViolationsPdfAPIView(DoanRestrictedAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        filters = {
            'class_id': request.query_params.get('class_id'),
            'status': request.query_params.get('status'),
            'start_date': request.query_params.get('start_date'),
            'end_date': request.query_params.get('end_date'),
        }
        pdf_content = export_violations_pdf(filters=filters, exported_by=request.user)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Danh_Sach_Vi_Pham_THPT_Huong_Khe.pdf"'
        return response


class ExportViolationDetailPdfAPIView(DoanRestrictedAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, violation_id):
        pdf_content = export_violation_detail_pdf(violation_id=violation_id, exported_by=request.user)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Bien_Ban_Vi_Pham_{violation_id}.pdf"'
        return response


class ReportExportHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReportExportHistory.objects.all().select_related('exported_by')
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_admin or self.request.user.is_bgh or self.request.user.is_doan_truong:
            return queryset
        return queryset.filter(exported_by=self.request.user)

    def check_permissions(self, request):
        super().check_permissions(request)

    def list(self, request, *args, **kwargs):
        histories = self.get_queryset()[:20]
        data = [
            {
                'id': h.id,
                'title': h.title,
                'report_type': h.get_report_type_display(),
                'file_format': h.get_file_format_display(),
                'exported_by': h.exported_by.full_name if h.exported_by else 'Hệ thống',
                'created_at': h.created_at.strftime('%d/%m/%Y %H:%M')
            }
            for h in histories
        ]
        return Response(data)
