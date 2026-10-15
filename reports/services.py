import io
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from competition.models import CompetitionPeriod, ClassCompetitionScore
from conduct.models import ViolationRecord
from .models import ReportExportHistory


def export_competition_excel(period_id, exported_by=None):
    """Xuất bảng tổng hợp thi đua Chi đoàn ra tệp Excel (.xlsx) tiêu chuẩn"""
    period = CompetitionPeriod.objects.get(id=period_id)
    scores = ClassCompetitionScore.objects.filter(competition_period=period).select_related('school_class').order_by('rank')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"ThiDua_Tuan_{period.week_number or 'Ky'}"[:30]

    # Styles
    title_font = Font(name='Arial', size=14, bold=True, color='1E3A8A')
    sub_font = Font(name='Arial', size=11, bold=True, color='374151')
    header_font = Font(name='Arial', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1E3A8A', end_color='1E3A8A', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )

    # Headers
    ws.merge_cells('A1:I1')
    ws['A1'] = "SỞ GIÁO DỤC VÀ ĐÀO TẠO HÀ TĨNH - TRƯỜNG THPT HƯƠNG KHÊ"
    ws['A1'].font = sub_font
    ws['A1'].alignment = Alignment(horizontal='left')

    ws.merge_cells('A2:I2')
    ws['A2'] = f"BẢNG TỔNG HỢP XẾP HẠNG THI ĐUA CHI ĐOÀN – {period.name.upper()}"
    ws['A2'].font = title_font
    ws['A2'].alignment = Alignment(horizontal='center')

    ws.merge_cells('A3:I3')
    now_str = timezone.now().strftime('%d/%m/%Y %H:%M')
    creator_str = exported_by.full_name or exported_by.username if exported_by else 'Ban Thi đua Đoàn trường'
    ws['A3'] = f"Thời gian áp dụng: {period.start_date.strftime('%d/%m/%Y')} đến {period.end_date.strftime('%d/%m/%Y')} | Xuất lúc: {now_str} | Người lập: {creator_str}"
    ws['A3'].font = Font(name='Arial', size=9, italic=True, color='6B7280')
    ws['A3'].alignment = Alignment(horizontal='center')

    headers = [
        "Thứ hạng", "Lớp / Chi đoàn", "Khối", "Điểm gốc", "Điểm cộng", 
        "Điểm trừ vi phạm", "Tổng điểm thi đua", "Số lỗi vi phạm", "Biến động hạng"
    ]
    
    ws.append([]) # Row 4 empty
    ws.append(headers) # Row 5
    header_row = 5
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=header_row, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')

    row_idx = 6
    for item in scores:
        trend = "0"
        if item.rank_change > 0:
            trend = f"+{item.rank_change} ▲"
        elif item.rank_change < 0:
            trend = f"{item.rank_change} ▼"

        row_data = [
            item.rank,
            item.school_class.name,
            f"Khối {item.school_class.grade}",
            float(item.base_points),
            float(item.bonus_points),
            float(item.penalty_points),
            float(item.total_score),
            item.verified_violations_count,
            trend
        ]
        ws.append(row_data)

        # Style data cells
        for c_idx in range(1, len(row_data) + 1):
            cell = ws.cell(row=row_idx, column=c_idx)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center' if c_idx in [1, 3, 8, 9] else ('right' if c_idx in [4, 5, 6, 7] else 'left'))
            if c_idx == 7: # Tổng điểm
                cell.font = Font(name='Arial', size=10, bold=True, color='1E3A8A')
        row_idx += 1

    # Adjust column widths
    column_widths = [12, 18, 12, 14, 14, 18, 18, 16, 16]
    for i, width in enumerate(column_widths, 1):
        col_letter = openpyxl.utils.get_column_letter(i)
        ws.column_dimensions[col_letter].width = width

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    ReportExportHistory.objects.create(
        report_type=ReportExportHistory.REPORT_COMPETITION,
        file_format=ReportExportHistory.FORMAT_EXCEL,
        title=f"Báo cáo thi đua {period.name}",
        parameters=f'{{"period_id": {period.id}}}',
        exported_by=exported_by
    )

    return output.getvalue()


def export_competition_pdf(period_id, exported_by=None):
    """Xuất báo cáo thi đua Chi đoàn dạng PDF có tiêu đề trường THPT Hương Khê"""
    period = CompetitionPeriod.objects.get(id=period_id)
    scores = ClassCompetitionScore.objects.filter(competition_period=period).select_related('school_class').order_by('rank')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'SchoolTitle',
        parent=styles['Heading2'],
        fontSize=12,
        leading=14,
        alignment=0,
        textColor=colors.HexColor('#1e3a8a')
    )
    main_title = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=14,
        leading=18,
        alignment=1,
        textColor=colors.HexColor('#111827'),
        fontName='Helvetica-Bold'
    )
    subtitle = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor('#6b7280')
    )

    elements = []
    elements.append(Paragraph("<b>TRƯỜNG THPT HƯƠNG KHÊ – HÀ TĨNH</b><br/>ĐOÀN THANH NIÊN CỘNG SẢN HỒ CHÍ MINH", title_style))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"BẢNG XẾP HẠNG THI ĐUA NỀN NẾP CHI ĐOÀN<br/><b>{period.name.upper()}</b>", main_title))
    elements.append(Paragraph(f"Thời gian: {period.start_date.strftime('%d/%m/%Y')} - {period.end_date.strftime('%d/%m/%Y')}", subtitle))
    elements.append(Spacer(1, 15))

    # Table data
    data = [["Hạng", "Chi đoàn", "Khối", "Điểm gốc", "Điểm cộng", "Điểm trừ", "Tổng điểm", "Số vi phạm"]]
    for sc in scores:
        data.append([
            str(sc.rank),
            sc.school_class.name,
            f"K{sc.school_class.grade}",
            f"{sc.base_points:.1f}",
            f"{sc.bonus_points:.1f}",
            f"{sc.penalty_points:.1f}",
            f"{sc.total_score:.1f}",
            str(sc.verified_violations_count)
        ])

    table = Table(data, colWidths=[40, 90, 50, 65, 65, 65, 80, 75])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    elements.append(table)

    # Signatures
    elements.append(Spacer(1, 30))
    sig_data = [
        ["", "Hương Khê, ngày ..... tháng ..... năm 2026"],
        ["TM. ĐOÀN TRƯỜNG\nBÍ THƯ", "HIỆU TRƯỞNG\n(Phê duyệt)"],
        ["\n\n(Ký, ghi rõ họ tên)", "\n\n(Ký, đóng dấu)"]
    ]
    sig_table = Table(sig_data, colWidths=[260, 260])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    buffer.seek(0)

    ReportExportHistory.objects.create(
        report_type=ReportExportHistory.REPORT_COMPETITION,
        file_format=ReportExportHistory.FORMAT_PDF,
        title=f"Báo cáo PDF thi đua {period.name}",
        parameters=f'{{"period_id": {period.id}}}',
        exported_by=exported_by
    )

    return buffer.getvalue()


def export_violations_excel(filters=None, exported_by=None):
    """Xuất danh sách vi phạm nền nếp ra Excel với bộ lọc"""
    queryset = ViolationRecord.objects.select_related('school_class', 'student', 'rule', 'reporter').all()
    if filters:
        if 'class_id' in filters and filters['class_id']:
            queryset = queryset.filter(school_class_id=filters['class_id'])
        if 'status' in filters and filters['status']:
            queryset = queryset.filter(status=filters['status'])

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DS Vi phạm nền nếp"

    headers = ["Mã bản ghi", "Thời gian", "Lớp", "Học sinh", "Lỗi vi phạm", "Vị trí", "Điểm trừ", "Trạng thái", "Người ghi nhận"]
    ws.append(["TRƯỜNG THPT HƯƠNG KHÊ - BÁO CÁO VI PHẠM NỀN NẾP HỌC SINH"])
    ws.append([f"Xuất ngày: {timezone.now().strftime('%d/%m/%Y %H:%M')}"])
    ws.append([])
    ws.append(headers)

    header_font = Font(name='Arial', size=10, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1E3A8A', end_color='1E3A8A', fill_type='solid')
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=4, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')

    for rec in queryset:
        ws.append([
            rec.record_code,
            rec.occurred_at.strftime('%d/%m/%Y %H:%M'),
            rec.school_class.name,
            rec.student_name_snapshot or (rec.student.full_name if rec.student else "Tập thể"),
            rec.rule.name,
            rec.location,
            float(rec.points_deducted),
            rec.get_status_display(),
            rec.reporter.full_name or rec.reporter.username
        ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()
