from django.db import models
from core.models import User


class ReportExportHistory(models.Model):
    REPORT_COMPETITION = 'COMPETITION'
    REPORT_VIOLATIONS = 'VIOLATIONS'
    REPORT_ALERTS = 'ALERTS'
    REPORT_COUNSELING_STAT = 'COUNSELING_STAT'

    REPORT_TYPES = [
        (REPORT_COMPETITION, 'Báo cáo xếp hạng thi đua Chi đoàn'),
        (REPORT_VIOLATIONS, 'Báo cáo thống kê vi phạm nền nếp'),
        (REPORT_ALERTS, 'Báo cáo cảnh báo sớm & phối hợp GVCN'),
        (REPORT_COUNSELING_STAT, 'Thống kê tổng hợp tư vấn tâm lý (ẩn danh)'),
    ]

    FORMAT_EXCEL = 'XLSX'
    FORMAT_PDF = 'PDF'
    FORMAT_CHOICES = [
        (FORMAT_EXCEL, 'Bảng tính Excel (.xlsx)'),
        (FORMAT_PDF, 'Tài liệu PDF (.pdf)'),
    ]

    report_type = models.CharField(max_length=30, choices=REPORT_TYPES, verbose_name='Loại báo cáo')
    file_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, verbose_name='Định dạng tệp')
    title = models.CharField(max_length=255, verbose_name='Tiêu đề báo cáo')
    parameters = models.TextField(blank=True, verbose_name='Tham số bộ lọc (JSON)')
    exported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Người xuất báo cáo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời điểm xuất')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lịch sử xuất báo cáo'
        verbose_name_plural = 'Lịch sử xuất báo cáo'

    def __str__(self):
        user_str = self.exported_by.username if self.exported_by else 'Hệ thống'
        return f"[{self.file_format}] {self.title} bởi {user_str} lúc {self.created_at.strftime('%d/%m/%Y %H:%M')}"
