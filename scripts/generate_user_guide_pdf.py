# -*- coding: utf-8 -*-
"""
Script khởi tạo tài liệu PDF Sổ tay Hướng dẫn Sử dụng Chi tiết & Trực quan
Hệ thống HK Student Hub – Trường THPT Hương Khê (Hà Tĩnh).
Tên miền chính thức: http://hkstudenthub.io.vn

Đặc điểm tài liệu:
- Phân tách rõ ràng thành các phần độc lập: HỌC SINH & LỚP TRƯỞNG, GIÁO VIÊN (GVCN & GVBM), ĐOÀN TRƯỜNG & SAO ĐỎ, QUẢN TRỊ VIÊN.
- Sử dụng ReportLab nhúng font Times New Roman Unicode tiếng Việt.
- Bố cục hai lượt (two-pass) với NumberedCanvas hiển thị 'Trang X / Y'.
- Đầy đủ ảnh nhận diện Logo trường (LOGO.jpg), ảnh giao diện trực quan (TRANGCHU.JPG), thẻ hướng dẫn từng bước (Step cards),
  hộp ghi chú (Callouts), bảng biểu đối soát nghiệp vụ, lưu đồ vòng đời vi phạm và bảng tra cứu nhanh.
"""
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import shutil
from pathlib import Path
from datetime import datetime

# Thiết lập đường dẫn dự án
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')

import django
django.setup()

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak, HRFlowable, Image
)
from reportlab.pdfgen import canvas
from reports.pdf_utils import setup_times_new_roman_fonts


class UserGuideCanvas(canvas.Canvas):
    """
    Canvas hai lượt (two-pass) của ReportLab dành riêng cho Sổ tay Hướng dẫn sử dụng:
    - Bỏ qua vẽ header/footer ở Trang bìa (Trang 1).
    - Từ trang 2 trở đi: Vẽ Running Header và Running Footer kèm số trang 'Trang X / Y'.
    - Đảm bảo 100% font nhúng Times New Roman hỗ trợ tiếng Việt có dấu.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # Trang bìa nghệ thuật, không hiển thị thanh chạy
            return

        self.saveState()
        setup_times_new_roman_fonts()
        page_width, page_height = self._pagesize
        left = 36
        right = page_width - 36

        # --- RUNNING HEADER ---
        header_y = page_height - 26
        self.setFont('TimesNewRoman-Bold', 7.8)
        self.setFillColor(colors.HexColor('#163A70'))
        self.drawString(left, header_y, "SỔ TAY HƯỚNG DẪN SỬ DỤNG HỆ THỐNG – HK STUDENT HUB")

        self.setFont('TimesNewRoman-Italic', 7.5)
        self.setFillColor(colors.HexColor('#64748B'))
        self.drawRightString(right, header_y, "TRƯỜNG THPT HƯƠNG KHÊ • http://hkstudenthub.io.vn")

        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(0.6)
        self.line(left, header_y - 4, right, header_y - 4)

        # --- RUNNING FOOTER ---
        footer_y = 22
        self.setStrokeColor(colors.HexColor('#E2E8F0'))
        self.setLineWidth(0.6)
        self.line(left, footer_y + 10, right, footer_y + 10)

        self.setFont('TimesNewRoman-Italic', 7.5)
        self.setFillColor(colors.HexColor('#64748B'))
        self.drawString(left, footer_y, "Tài liệu lưu hành nội bộ • Cổng thông tin: http://hkstudenthub.io.vn • Bản quyền © 2026")

        page_str = f"Trang {self._pageNumber} / {page_count}"
        self.setFont('TimesNewRoman-Bold', 8)
        self.setFillColor(colors.HexColor('#163A70'))
        self.drawRightString(right, footer_y, page_str)

        self.restoreState()


def build_user_guide_pdf(output_paths):
    setup_times_new_roman_fonts()
    font_name = 'TimesNewRoman'
    bold_font = 'TimesNewRoman-Bold'
    italic_font = 'TimesNewRoman-Italic'
    bold_italic_font = 'TimesNewRoman-BoldItalic'

    # Bảng màu chủ đạo (Visual Palette)
    PRIMARY = colors.HexColor('#163A70')      # Xanh Navy đậm - Trường THPT Hương Khê
    SECONDARY = colors.HexColor('#0284C7')    # Sky Blue - Tươi sáng, công nghệ
    ACCENT = colors.HexColor('#D97706')       # Vàng Amber - Điểm nhấn, huy hiệu ⭐
    SUCCESS = colors.HexColor('#059669')      # Xanh lá ngọc - Phê duyệt, đạt chuẩn
    DANGER = colors.HexColor('#DC2626')       # Đỏ Ruby - Vi phạm, cảnh báo
    PURPLE = colors.HexColor('#7C3AED')       # Tím Indigo - Góc sẻ chia tâm lý
    DARK = colors.HexColor('#0F172A')         # Slate 900 - Chữ chính
    MUTED = colors.HexColor('#475569')        # Slate 600 - Chú thích
    BG_LIGHT = colors.HexColor('#F8FAFC')     # Nền xám rất nhạt
    BG_ROW_ALT = colors.HexColor('#F1F5F9')   # Nền xen kẽ bảng
    BORDER = colors.HexColor('#CBD5E1')       # Viền xám mảnh

    styles = {
        'CoverTopSchool': ParagraphStyle('CoverTopSchool', fontName=bold_font, fontSize=11, leading=15, alignment=1, textColor=PRIMARY),
        'CoverTopSub': ParagraphStyle('CoverTopSub', fontName=font_name, fontSize=9.5, leading=13.5, alignment=1, textColor=MUTED),
        'CoverDocTitle': ParagraphStyle('CoverDocTitle', fontName=bold_font, fontSize=21, leading=27, alignment=1, textColor=PRIMARY, spaceAfter=6),
        'CoverDocSub': ParagraphStyle('CoverDocSub', fontName=bold_font, fontSize=12, leading=17, alignment=1, textColor=SECONDARY, spaceAfter=8),
        'CoverSlogan': ParagraphStyle('CoverSlogan', fontName=bold_italic_font, fontSize=10, leading=14, alignment=1, textColor=ACCENT, spaceAfter=12),
        'CoverMetaBox': ParagraphStyle('CoverMetaBox', fontName=font_name, fontSize=8.5, leading=13, textColor=DARK),

        'SecTitle': ParagraphStyle('SecTitle', fontName=bold_font, fontSize=12, leading=16, textColor=colors.white, spaceAfter=0),
        'SecSub': ParagraphStyle('SecSub', fontName=italic_font, fontSize=8.2, leading=11, textColor=colors.HexColor('#E2E8F0')),
        
        'H1': ParagraphStyle('H1', fontName=bold_font, fontSize=10.5, leading=14.5, textColor=PRIMARY, spaceBefore=8, spaceAfter=3.5, keepWithNext=True),
        'H2': ParagraphStyle('H2', fontName=bold_font, fontSize=9.2, leading=13, textColor=DARK, spaceBefore=6, spaceAfter=2.5, keepWithNext=True),
        
        'Body': ParagraphStyle('Body', fontName=font_name, fontSize=8.4, leading=12.2, textColor=DARK, alignment=4, spaceAfter=3),
        'BodyBold': ParagraphStyle('BodyBold', fontName=bold_font, fontSize=8.4, leading=12.2, textColor=DARK, spaceAfter=2.5),
        'BodyItalic': ParagraphStyle('BodyItalic', fontName=italic_font, fontSize=8, leading=11.5, textColor=MUTED, spaceAfter=2.5),
        
        'Bullet': ParagraphStyle('Bullet', fontName=font_name, fontSize=8.2, leading=11.8, textColor=DARK, leftIndent=12, firstLineIndent=-8, spaceAfter=2),
        'BulletBold': ParagraphStyle('BulletBold', fontName=bold_font, fontSize=8.2, leading=11.8, textColor=PRIMARY, leftIndent=12, firstLineIndent=-8, spaceAfter=2),
        
        'TableTh': ParagraphStyle('TableTh', fontName=bold_font, fontSize=7.8, leading=10.5, alignment=1, textColor=colors.white),
        'TableTd': ParagraphStyle('TableTd', fontName=font_name, fontSize=7.8, leading=10.5, textColor=DARK),
        'TableTdCenter': ParagraphStyle('TableTdCenter', fontName=font_name, fontSize=7.8, leading=10.5, alignment=1, textColor=DARK),
        'TableTdBold': ParagraphStyle('TableTdBold', fontName=bold_font, fontSize=7.8, leading=10.5, textColor=DARK),
        'TableTdCode': ParagraphStyle('TableTdCode', fontName=bold_font, fontSize=7.5, leading=10, alignment=1, textColor=SECONDARY),
        
        'CalloutTitle': ParagraphStyle('CalloutTitle', fontName=bold_font, fontSize=8.5, leading=11.5),
        'CalloutText': ParagraphStyle('CalloutText', fontName=font_name, fontSize=8, leading=11.2, textColor=DARK),
        
        'StepBadge': ParagraphStyle('StepBadge', fontName=bold_font, fontSize=8, leading=10.5, alignment=1, textColor=colors.white),
        'StepTitle': ParagraphStyle('StepTitle', fontName=bold_font, fontSize=8.8, leading=12, textColor=PRIMARY),
        'StepDesc': ParagraphStyle('StepDesc', fontName=font_name, fontSize=8, leading=11.2, textColor=DARK),
    }

    content_width = 523.27
    story = []

    # =========================================================================
    # HÀM BỔ TRỢ GIAO DIỆN (VISUAL HELPERS)
    # =========================================================================

    def make_section_banner(title_text, subtitle_text="", bg_color=PRIMARY):
        """Tạo dải băng tiêu đề phân chương sắc nét"""
        p_title = Paragraph(title_text, styles['SecTitle'])
        if subtitle_text:
            p_sub = Paragraph(subtitle_text, styles['SecSub'])
            cell_data = [[p_title], [p_sub]]
        else:
            cell_data = [[p_title]]
        t = Table(cell_data, colWidths=[content_width])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg_color),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 9),
            ('RIGHTPADDING', (0,0), (-1,-1), 9),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        return t

    def make_callout(title, text, kind="tip"):
        """Tạo hộp ghi chú trực quan viền màu"""
        cfg = {
            'tip': {'border': SUCCESS, 'bg': colors.HexColor('#F0FDF4'), 'title_color': SUCCESS, 'icon': '💡 MẸO SỬ DỤNG:'},
            'warning': {'border': DANGER, 'bg': colors.HexColor('#FEF2F2'), 'title_color': DANGER, 'icon': '⚠️ LƯU Ý BẮT BUỘC:'},
            'info': {'border': SECONDARY, 'bg': colors.HexColor('#F0F9FF'), 'title_color': SECONDARY, 'icon': 'ℹ️ THÔNG TIN CẦN BIẾT:'},
            'note': {'border': ACCENT, 'bg': colors.HexColor('#FFFBEB'), 'title_color': ACCENT, 'icon': '📌 NỘI QUY TRỌNG TÂM:'},
            'counseling': {'border': PURPLE, 'bg': colors.HexColor('#FAF5FF'), 'title_color': PURPLE, 'icon': '💜 BẢO MẬT GÓC SẺ CHIA:'},
        }.get(kind, {'border': SECONDARY, 'bg': BG_LIGHT, 'title_color': SECONDARY, 'icon': 'ℹ️'})

        p_title = Paragraph(f"<font color='{cfg['title_color'].hexval()}'><b>{cfg['icon']} {title}</b></font>", styles['CalloutTitle'])
        p_text = Paragraph(text, styles['CalloutText'])
        
        t = Table([[p_title], [Spacer(1, 1.5)], [p_text]], colWidths=[content_width])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), cfg['bg']),
            ('LINELEFT', (0,0), (-1,-1), 3.5, cfg['border']),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 7),
            ('RIGHTPADDING', (0,0), (-1,-1), 7),
        ]))
        return t

    def make_step_card(step_num, title, details, badge_color=PRIMARY):
        """Tạo thẻ hướng dẫn từng bước kèm huy hiệu số"""
        p_badge = Paragraph(f"<b>BƯỚC<br/>{step_num:02d}</b>", styles['StepBadge'])
        p_title = Paragraph(f"<b>{title}</b>", styles['StepTitle'])
        p_desc = Paragraph(details, styles['StepDesc'])

        badge_table = Table([[p_badge]], colWidths=[48], rowHeights=[32])
        badge_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), badge_color),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))

        content_table = Table([[p_title], [Spacer(1, 1)], [p_desc]], colWidths=[content_width - 58])
        content_table.setStyle(TableStyle([
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 1.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ]))

        card = Table([[badge_table, content_table]], colWidths=[52, content_width - 52])
        card.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
            ('BOX', (0,0), (-1,-1), 0.5, BORDER),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 3.5),
            ('RIGHTPADDING', (0,0), (-1,-1), 3.5),
        ]))
        return card

    # =========================================================================
    # TRANG 1: TRANG BÌA CHÍNH THỨC (COVER PAGE)
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("SỞ GIÁO DỤC VÀ ĐÀO TẠO HÀ TĨNH<br/><b>TRƯỜNG TRUNG HỌC PHỔ THÔNG HƯƠNG KHÊ</b>", styles['CoverTopSchool']))
    story.append(Spacer(1, 2))
    story.append(Paragraph("<i>Mã định danh trường học: 42008 • Thị trấn Hương Khê, Huyện Hương Khê, Tỉnh Hà Tĩnh</i>", styles['CoverTopSub']))
    
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="65%", thickness=1.2, color=PRIMARY, spaceBefore=0, spaceAfter=16))

    # Nhúng Logo Trường
    logo_path = BASE_DIR / 'static' / 'LOGO.jpg'
    if logo_path.exists():
        logo_img = Image(str(logo_path), width=85, height=85)
        story.append(logo_img)
        story.append(Spacer(1, 14))

    story.append(Paragraph("SỔ TAY HƯỚNG DẪN SỬ DỤNG HỆ THỐNG", styles['CoverDocTitle']))
    story.append(Paragraph("HK STUDENT HUB – CỔNG THÔNG TIN NỀN NẾP, THI ĐUA & KẾT NỐI HỌC ĐƯỜNG SỐ", styles['CoverDocSub']))
    story.append(Paragraph("★ “KỶ CƯƠNG SỐ – THI ĐUA MINH BẠCH – ĐỒNG HÀNH GIÁO DỤC TOÀN DIỆN” ★", styles['CoverSlogan']))

    story.append(Spacer(1, 10))

    # Khung metadata trang bìa
    cover_meta = [
        [
            Paragraph("<b>Đơn vị ban hành:</b> Ban Giám hiệu & Đoàn trường THPT Hương Khê<br/>"
                      "<b>Cổng thông tin chính thức:</b> <font color='#0284C7'><u>http://hkstudenthub.io.vn</u></font><br/>"
                      "<b>Mã nguồn phát triển:</b> github.com/cuonghk1108/THPTHK<br/>"
                      "<b>Hạ tầng mạng:</b> Cloudflare Tunnel SSL/TLS bảo mật cao", styles['CoverMetaBox']),
            Paragraph("<b>Phiên bản tài liệu:</b> Version 2.5 (Cập nhật tháng 10/2026)<br/>"
                      "<b>Cấu trúc tài liệu:</b> Tách riêng Học sinh, Giáo viên, Đoàn trường<br/>"
                      "<b>Phạm vi áp dụng:</b> Toàn thể 65 Chi đoàn Khối 10, 11, 12<br/>"
                      "<b>Hỗ trợ đa kênh:</b> SMS Gateway SpeedSMS & Gmail SMTP", styles['CoverMetaBox'])
        ]
    ]
    t_cover_meta = Table(cover_meta, colWidths=[260, 263])
    t_cover_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 9),
        ('RIGHTPADDING', (0,0), (-1,-1), 9),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_cover_meta)

    story.append(Spacer(1, 14))
    story.append(make_callout(
        "MỤC ĐÍCH VÀ NGUYÊN TẮC THỰC HIỆN TOÀN TRƯỜNG",
        "Tài liệu này là cẩm nang hướng dẫn bắt buộc dành cho cán bộ quản lý, giáo viên, đoàn viên và học sinh trường THPT Hương Khê. "
        "Mọi hoạt động chấm điểm thi đua, ghi nhận nề nếp, gửi khiếu nại và nhận xét học sinh phải thực hiện trực tiếp trên hệ thống "
        "tại tên miền chính thức: <b>http://hkstudenthub.io.vn</b>.",
        "note"
    ))

    # Hết Trang 1 -> Chuyển sang Trang 2
    story.append(PageBreak())

    # =========================================================================
    # TRANG 2: TỔNG QUAN HỆ THỐNG & SƠ ĐỒ ĐIỀU HƯỚNG GIAO DIỆN
    # =========================================================================
    story.append(make_section_banner(
        "PHẦN 1: TỔNG QUAN NỀN TẢNG & BẢN ĐỒ GIAO DIỆN TRỰC QUAN",
        "Cổng thông tin quản lý nề nếp & thi đua: http://hkstudenthub.io.vn"
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "<b>HK Student Hub</b> (địa chỉ truy cập: <b>http://hkstudenthub.io.vn</b>) là nền tảng quản lý trường học số tiên phong của "
        "Trường THPT Hương Khê. Nền tảng số hóa 100% quy trình thi đua, chấm dứt tình trạng ghi chép sổ sách giấy thủ công, tự động hóa tính điểm "
        "và xếp hạng 65 Chi đoàn theo thời gian thực, đồng thời cung cấp không gian tư vấn tâm lý an toàn tuyệt đối.",
        styles['Body']
    ))
    story.append(Spacer(1, 3))

    # Ảnh chụp màn hình giao diện
    tc_path = BASE_DIR / 'static' / 'TRANGCHU.JPG'
    if tc_path.exists():
        story.append(Paragraph("<b>HÌNH 1: GIAO DIỆN BẢNG ĐIỀU KHIỂN TRUNG TÂM (DASHBOARD) TẠI http://hkstudenthub.io.vn</b>", styles['BodyBold']))
        story.append(Spacer(1, 2))
        tc_img = Image(str(tc_path), width=480, height=265)
        story.append(tc_img)
        story.append(Spacer(1, 5))

    ui_map_data = [
        [
            Paragraph("<b>Khu vực</b>", styles['TableTh']),
            Paragraph("<b>Tên phân vùng giao diện</b>", styles['TableTh']),
            Paragraph("<b>Ý nghĩa chức năng & Hướng dẫn thao tác nhanh</b>", styles['TableTh'])
        ],
        [
            Paragraph("<b>[ 1 ]</b>", styles['TableTdCode']),
            Paragraph("<b>Thanh Sidebar điều hướng</b><br/><i>(Navigation Drawer)</i>", styles['TableTdBold']),
            Paragraph("Truy cập nhanh các phân hệ nghiệp vụ tùy theo vai trò: Bảng điều khiển, Quản lý lớp học, Nề nếp kỷ luật, Bảng thi đua, Phê duyệt học sinh, Góc sẻ chia, Báo cáo và Cài đặt.", styles['TableTd'])
        ],
        [
            Paragraph("<b>[ 2 ]</b>", styles['TableTdCode']),
            Paragraph("<b>Thẻ chỉ số tổng quan</b><br/><i>(KPI Analytics Cards)</i>", styles['TableTdBold']),
            Paragraph("Cập nhật tự động 4 chỉ số tức thì: Số vi phạm phát sinh trong tuần, Tỷ lệ khiếu nại đã xử lý thành công (%), Điểm thi đua trung bình toàn trường, Số lượt tâm sự cần tư vấn.", styles['TableTd'])
        ],
        [
            Paragraph("<b>[ 3 ]</b>", styles['TableTdCode']),
            Paragraph("<b>Bục vinh danh Podium</b><br/><i>(Top 3 Chi đoàn dẫn đầu)</i>", styles['TableTdBold']),
            Paragraph("Vinh danh 3 Chi đoàn có điểm thi đua xuất sắc nhất tuần với cúp Vàng, Bạc, Đồng; tự động nhảy hạng sau mỗi quyết định duyệt điểm của Đoàn trường.", styles['TableTd'])
        ],
        [
            Paragraph("<b>[ 4 ]</b>", styles['TableTdCode']),
            Paragraph("<b>Bảng tin nề nếp trực tiếp</b><br/><i>(Live Activity Stream)</i>", styles['TableTdBold']),
            Paragraph("Dòng thời gian hiển thị các bản ghi vi phạm mới nhất, quyết định giải quyết khiếu nại và thông báo chỉ đạo khẩn cấp từ Ban Giám hiệu.", styles['TableTd'])
        ],
        [
            Paragraph("<b>[ 5 ]</b>", styles['TableTdCode']),
            Paragraph("<b>Thanh công cụ cá nhân</b><br/><i>(User Profile & Header)</i>", styles['TableTdBold']),
            Paragraph("Hiển thị ảnh đại diện, vai trò tài khoản, huy hiệu ⭐ Lớp trưởng (nếu được bổ nhiệm), chuông thông báo và nút Đăng xuất an toàn.", styles['TableTd'])
        ],
    ]
    t_ui_map = Table(ui_map_data, colWidths=[38, 145, 340])
    t_ui_map.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,1), (-1,1), BG_LIGHT),
        ('BACKGROUND', (0,3), (-1,3), BG_LIGHT),
        ('BACKGROUND', (0,5), (-1,5), BG_LIGHT),
    ]))
    story.append(t_ui_map)

    # Hết Trang 2 -> Chuyển sang Trang 3 (Bắt đầu Phần Học sinh)
    story.append(PageBreak())

    # =========================================================================
    # TRANG 3: CẨM NANG HƯỚNG DẪN CHI TIẾT DÀNH CHO HỌC SINH (PHẦN 1)
    # =========================================================================
    story.append(make_section_banner(
        "PHẦN 2: CẨM NANG HƯỚNG DẪN DÀNH CHO HỌC SINH & LỚP TRƯỞNG",
        "Dành cho đoàn viên, học sinh toàn thể 65 Chi đoàn Trường THPT Hương Khê",
        bg_color=colors.HexColor('#0284C7')
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>CHƯƠNG 2.1: QUY TRÌNH ĐĂNG NHẬP & HOÀN THIỆN HỒ SƠ HỌC SINH MỚI</b>", styles['H1']))
    story.append(Paragraph(
        "Học sinh khi lần đầu truy cập <b>http://hkstudenthub.io.vn</b> cần thực hiện đúng quy trình 3 bước sau để được kích hoạt tài khoản:",
        styles['Body']
    ))

    story.append(make_step_card(
        1,
        "ĐĂNG NHẬP 1 CHẠM VỚI TÀI KHOẢN GOOGLE (SSO)",
        "• Truy cập trình duyệt web trên điện thoại hoặc máy tính: <b>http://hkstudenthub.io.vn</b>.<br/>"
        "• Bấm nút <b>'Đăng nhập với Google'</b>: Chọn tài khoản Gmail cá nhân để liên kết xác thực an toàn, không cần nhớ mật khẩu riêng.",
        PRIMARY
    ))
    story.append(Spacer(1, 4))

    story.append(make_step_card(
        2,
        "HOÀN THIỆN HỒ SƠ LỚP HỌC (/complete-profile)",
        "• Sau khi đăng nhập Google lần đầu, hệ thống tự động hiển thị màn hình <b>Hoàn thiện hồ sơ</b>.<br/>"
        "• <b>Chọn Khối học:</b> Nhấn tab Khối tương ứng (Khối 10, Khối 11 hoặc Khối 12).<br/>"
        "• <b>Chọn Chi đoàn:</b> Chọn đúng lớp học trong danh sách 65 lớp (10A1 - 10A22, 11A1 - 11A21, 12A1 - 12A22).<br/>"
        "• <b>Thông tin bổ sung:</b> Nhập Họ và tên thật (có dấu), Mã học sinh và Số điện thoại phụ huynh để nhận SMS nề nếp.<br/>"
        "• Bấm <b>'Lưu hồ sơ'</b>: Tài khoản được chuyển sang trạng thái <font color='#D97706'><b>PENDING (Chờ duyệt)</b></font>.",
        SECONDARY
    ))
    story.append(Spacer(1, 4))

    story.append(make_step_card(
        3,
        "ĐOÀN TRƯỜNG PHÊ DUYỆT & KÍCH HOẠT TÀI KHOẢN",
        "• Thầy/Cô Đoàn trường đối soát danh sách lớp thực tế và bấm phê duyệt.<br/>"
        "• Khi tài khoản chuyển sang trạng thái <b>APPROVED</b>, em có thể tra cứu toàn bộ thông tin nề nếp và tham gia thi đua.",
        SUCCESS
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>CHƯƠNG 2.2: THEO DÕI NỀ NẾP CÁ NHÂN & SỔ TAY NHẬN XÉT CỦA GIÁO VIÊN</b>", styles['H1']))
    story.append(Paragraph("• <b>Xem lịch sử nề nếp:</b> Vào mục <b>'Hồ sơ cá nhân'</b> -> Chọn tab <b>'Nề nếp'</b>: Em sẽ thấy toàn bộ danh sách các biên bản vi phạm kỷ luật (nếu có), trạng thái biên bản (PENDING/VERIFIED/ADJUSTED), số điểm bị trừ và ảnh bằng chứng đính kèm.", styles['Bullet']))
    story.append(Paragraph("• <b>Đọc nhận xét của Thầy Cô bộ môn:</b> Trong từng tuần học, thầy cô dạy các môn sẽ gửi nhận xét trực tiếp về tinh thần phát biểu, chuẩn bị bài, kết quả kiểm tra miệng hoặc nhắc nhở ý thức. Học sinh xem chi tiết trong sổ nhận xét để kịp thời phát huy ưu điểm và sửa chữa thiếu sót.", styles['Bullet']))
    story.append(Paragraph("• <b>Tự giải trình vi phạm cá nhân:</b> Nếu phát hiện bản thân bị ghi nhận vi phạm nhầm lẫn (ví dụ: bị nhầm tên với bạn khác hoặc nghỉ học có giấy phép y tế), em có quyền bấm nút <b>'Giải trình lỗi cá nhân'</b> để nộp minh chứng gửi về Đoàn trường.", styles['Bullet']))
    story.append(Spacer(1, 4))

    story.append(make_callout(
        "LƯU Ý DÀNH CHO HỌC SINH MỚI ĐĂNG KÝ",
        "Nếu sau khi hoàn thiện hồ sơ mà em chưa vào được các chức năng chính, tài khoản của em đang ở trạng thái chờ duyệt. "
        "Hãy báo ngay cho Lớp trưởng hoặc Thầy/Cô chủ nhiệm để Đoàn trường kích hoạt tài khoản trong giờ sinh hoạt đầu tuần.",
        "warning"
    ))

    # Hết Trang 3 -> Chuyển sang Trang 4 (Tiếp tục Học sinh: Lớp trưởng & Góc sẻ chia)
    story.append(PageBreak())

    # =========================================================================
    # TRANG 4: CẨM NANG HƯỚNG DẪN CHI TIẾT DÀNH CHO HỌC SINH (PHẦN 2)
    # =========================================================================
    story.append(make_section_banner(
        "PHẦN 2 (TIẾP THEO): QUYỀN HẠN ⭐ LỚP TRƯỞNG & PHÂN HỆ 'GÓC SẺ CHIA'",
        "Đại diện bảo vệ quyền lợi Chi đoàn và không gian tư vấn tâm lý học đường an toàn",
        bg_color=colors.HexColor('#0284C7')
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>CHƯƠNG 2.3: ĐẶC QUYỀN VÀ TRÁCH NHIỆM CỦA ⭐ LỚP TRƯỞNG (CLASS MONITOR)</b>", styles['H1']))
    story.append(Paragraph(
        "Lớp trưởng là thủ lĩnh thanh niên đại diện cho quyền lợi thi đua và danh dự của toàn thể Chi đoàn:",
        styles['Body']
    ))
    story.append(Paragraph("• <b>Huy hiệu ⭐ Ngôi sao vàng:</b> Được hiển thị trang trọng bên cạnh họ tên của Lớp trưởng trên giao diện lớp học và danh sách toàn trường.", styles['BulletBold']))
    story.append(Paragraph("• <b>Quyền giám sát biên bản vi phạm của Chi đoàn:</b> Lớp trưởng được cấp quyền đặc biệt truy cập phân hệ <b>Nề nếp (conduct)</b>. Tại đây, Lớp trưởng có thể xem danh sách tất cả các học sinh trong lớp bị ghi nhận vi phạm kèm ảnh bằng chứng của Sao đỏ.", styles['Bullet']))
    story.append(Paragraph("• <b>Quy trình gửi Đơn khiếu nại (Appeal) bảo vệ điểm thi đua lớp:</b>", styles['BulletBold']))

    appeal_data = [
        [
            Paragraph("<b>Bước thao tác</b>", styles['TableTh']),
            Paragraph("<b>Hành động cụ thể của Lớp trưởng ⭐</b>", styles['TableTh']),
            Paragraph("<b>Kết quả trên hệ thống</b>", styles['TableTh']),
        ],
        [
            Paragraph("<b>Bước 1</b>", styles['TableTdCenter']),
            Paragraph("Kiểm tra danh mục vi phạm lớp tại mục <b>Nề nếp</b>. Khi phát hiện lỗi sai sót (nhầm lớp, lý do chính đáng), bấm nút <b>'Khiếu nại vi phạm'</b>.", styles['TableTd']),
            Paragraph("Mở hộp thoại Khiếu nại", styles['TableTdCenter']),
        ],
        [
            Paragraph("<b>Bước 2</b>", styles['TableTdCenter']),
            Paragraph("Nhập nội dung giải trình rõ ràng (Họ tên học sinh, nguyên nhân khách quan, sự việc thực tế) và tải kèm ảnh minh chứng (giấy phép nghỉ học, xác nhận của GV).", styles['TableTd']),
            Paragraph("Trạng thái chuyển sang:<br/><font color='#7C3AED'><b>APPEALING</b></font>", styles['TableTdCenter']),
        ],
        [
            Paragraph("<b>Bước 3</b>", styles['TableTdCenter']),
            Paragraph("Đoàn trường tiếp nhận, đối soát lại với Đội Sao đỏ. Nếu khiếu nại đúng, Đoàn trường phê duyệt phục hồi điểm thi đua cho Chi đoàn.", styles['TableTd']),
            Paragraph("Trạng thái chuyển sang:<br/><font color='#059669'><b>ADJUSTED (Hoàn 100% điểm)</b></font>", styles['TableTdCenter']),
        ],
    ]
    t_appeal = Table(appeal_data, colWidths=[60, 310, 153])
    t_appeal.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,1), (-1,1), BG_LIGHT),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#F0FDF4')),
    ]))
    story.append(t_appeal)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>CHƯƠNG 2.4: PHÂN HỆ 'GÓC SẺ CHIA' – TƯ VẤN TÂM LÝ HỌC ĐƯỜNG</b>", styles['H1']))
    story.append(Paragraph(
        "Phân hệ <b>'Góc sẻ chia'</b> là nơi học sinh có thể tâm sự những khó khăn về học tập, quan hệ bạn bè, gia đình, tình bạn tuổi học trò, "
        "bạo lực học đường hoặc các khúc mắc tâm lý với chuyên viên tư vấn của nhà trường với nguyên tắc <b>BẢO MẬT & CÁCH LY TUYỆT ĐỐI</b>:",
        styles['Body']
    ))
    story.append(Paragraph("• <b>Quyền gửi tâm sự ẩn danh:</b> Học sinh có thể tích chọn <i>'Gửi ẩn danh'</i>. Hệ thống sẽ sinh bí danh ngẫu nhiên, không ai (kể cả BGH hay GVCN) biết người gửi là ai.", styles['Bullet']))
    story.append(Paragraph("• <b>Mã tra cứu bí mật độc nhất (Tracking Code):</b> Sau khi gửi thành công, màn hình sẽ hiển thị mã bí mật dạng <b>GSC-2026-XXXX</b>. Em hãy lưu lại mã này vào sổ tay hoặc điện thoại để sau đó vào tra cứu thư trả lời của thầy cô tư vấn tâm lý.", styles['Bullet']))
    story.append(Paragraph("• <b>Hỗ trợ khẩn cấp:</b> Trong tình huống bị đe dọa bạo lực hoặc khủng hoảng tâm lý nghiêm trọng, hệ thống cung cấp đường dây nóng trực tiếp <b>111</b> (Tổng đài Quốc gia Bảo vệ Trẻ em) và chỉ dẫn trợ giúp khẩn cấp tại phòng Y tế / Đoàn trường.", styles['Bullet']))
    story.append(Spacer(1, 4))

    story.append(make_callout(
        "CAM KẾT CÁCH LY VÀ KHÔNG ẢNH HƯỞNG THI ĐUA HẠNH KIỂM",
        "Dữ liệu tại phân hệ 'Góc sẻ chia' được mã hóa độc lập trong hệ thống. Thầy cô chủ nhiệm và Ban thi đua Đoàn trường "
        "hoàn toàn không được xem nội dung tâm sự. Học sinh yên tâm chia sẻ để được thấu hiểu và đồng hành.",
        "counseling"
    ))

    # Hết Trang 4 -> Chuyển sang Trang 5 (Bắt đầu Phần Giáo viên)
    story.append(PageBreak())

    # =========================================================================
    # TRANG 5: CẨM NANG HƯỚNG DẪN CHI TIẾT DÀNH CHO GIÁO VIÊN (PHẦN 1)
    # =========================================================================
    story.append(make_section_banner(
        "PHẦN 3: CẨM NANG HƯỚNG DẪN DÀNH CHO GIÁO VIÊN (GVCN & GVBM)",
        "Quản lý lớp học, sổ tay nhận xét tiết dạy, phân công ⭐ Lớp trưởng và bảo vệ Chi đoàn",
        bg_color=colors.HexColor('#163A70')
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>CHƯƠNG 3.1: HƯỚNG DẪN DÀNH CHO GIÁO VIÊN BỘ MÔN (GVBM)</b>", styles['H1']))
    story.append(Paragraph(
        "Hệ thống HK Student Hub hỗ trợ các thầy cô giáo bộ môn dễ dàng quản lý học sinh theo từng lớp dạy và từng tiết học trên lớp:",
        styles['Body']
    ))
    story.append(Paragraph("• <b>Bộ lọc Khối & Lớp thông minh toàn trường:</b> Thầy cô truy cập tab <b>'Quản lý Lớp học' (Teacher Classes)</b>. Chọn tab Khối (Khối 10, Khối 11, Khối 12) để hiển thị danh sách lớp. Hệ thống áp dụng thuật toán sắp xếp tự nhiên hiển thị đầy đủ 65 lớp từ 10A1 - 10A22, 11A1 - 11A21, 12A1 - 12A22 theo đúng bảng chữ cái.", styles['Bullet']))
    story.append(Paragraph("• <b>Sổ tay nhận xét đích danh học sinh theo tiết dạy:</b> Trong giờ lên lớp, thầy cô mở danh sách học sinh của lớp -> Bấm vào học sinh cần đánh giá -> Chọn <b>'Thêm nhận xét'</b>: Thầy cô có thể khen ngợi học sinh phát biểu tích cực, nhắc nhở học sinh chưa làm bài tập về nhà, hoặc ghi nhận điểm số kiểm tra.", styles['Bullet']))
    story.append(Paragraph("• <b>Ghi nhận vi phạm nề nếp trong giờ học:</b> Nếu phát sinh vi phạm nghiêm trọng trong tiết dạy (gian lận trong giờ kiểm tra, sử dụng điện thoại khi chưa cho phép, vô lễ), thầy cô bấm <b>'Lập biên bản vi phạm'</b> để chuyển thông tin ngay về Đoàn trường và GVCN.", styles['Bullet']))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>CHƯƠNG 3.2: HƯỚNG DẪN DÀNH CHO GIÁO VIÊN CHỦ NHIỆM (GVCN)</b>", styles['H1']))
    story.append(Paragraph(
        "Giáo viên chủ nhiệm có vai trò quản lý toàn diện nề nếp, học tập và bảo vệ quyền lợi thi đua chính đáng của tập thể lớp mình phụ trách:",
        styles['Body']
    ))

    # Bảng 4 trách nhiệm nòng cốt của GVCN
    gvcn_tasks = [
        [
            Paragraph("<b>Nghiệp vụ GVCN</b>", styles['TableTh']),
            Paragraph("<b>Quy trình thao tác cụ thể trên hệ thống</b>", styles['TableTh']),
            Paragraph("<b>Mục tiêu & Tác động</b>", styles['TableTh']),
        ],
        [
            Paragraph("<b>1. Bổ nhiệm & Miễn nhiệm ⭐ Lớp trưởng</b>", styles['TableTdBold']),
            Paragraph("Vào danh sách lớp mình -> Tìm học sinh được giao trọng trách -> Bấm nút <b>'Chỉ định Lớp trưởng'</b>. Để thay đổi nhân sự, bấm <b>'Hủy vai trò Lớp trưởng'</b>.", styles['TableTd']),
            Paragraph("Cấp quyền giám sát nề nếp và khiếu nại cho Lớp trưởng; hiển thị huy hiệu ⭐.", styles['TableTd']),
        ],
        [
            Paragraph("<b>2. Giám sát vi phạm nề nếp của lớp</b>", styles['TableTdBold']),
            Paragraph("Hệ thống tự động gửi <b>Email SMTP</b> đến hòm thư của GVCN khi lớp có học sinh bị lập biên bản. GVCN đăng nhập để xem ảnh bằng chứng và đối chiếu sự việc.", styles['TableTd']),
            Paragraph("Nắm bắt vi phạm kịp thời trong ngày, không bị bất ngờ vào cuối tuần.", styles['TableTd']),
        ],
        [
            Paragraph("<b>3. GVCN gửi Khiếu nại bảo vệ Chi đoàn</b>", styles['TableTdBold']),
            Paragraph("Nếu Đội Sao đỏ chấm nhầm hoặc học sinh vi phạm có lý do bất khả kháng (ốm đau đột xuất có xác nhận y tế), GVCN trực tiếp bấm <b>'Khiếu nại vi phạm'</b> gửi Đoàn trường.", styles['TableTd']),
            Paragraph("Bảo vệ điểm thi đua công bằng cho tập thể lớp mình chủ nhiệm.", styles['TableTd']),
        ],
        [
            Paragraph("<b>4. Xuất báo cáo nề nếp lớp (Excel/PDF)</b>", styles['TableTdBold']),
            Paragraph("Vào mục Báo cáo -> Chọn Lớp mình -> Bấm <b>'Xuất Excel'</b> hoặc <b>'Xuất PDF'</b> theo tuần, tháng hoặc học kỳ.", styles['TableTd']),
            Paragraph("Cung cấp số liệu minh bạch cho các buổi họp Chi đoàn và họp Phụ huynh.", styles['TableTd']),
        ],
    ]
    t_gvcn = Table(gvcn_tasks, colWidths=[120, 260, 143])
    t_gvcn.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,1), (-1,1), BG_LIGHT),
        ('BACKGROUND', (0,3), (-1,3), BG_LIGHT),
    ]))
    story.append(t_gvcn)

    # Hết Trang 5 -> Chuyển sang Trang 6 (Bắt đầu Phần Đoàn trường & Sao đỏ)
    story.append(PageBreak())

    # =========================================================================
    # TRANG 6: CẨM NANG HƯỚNG DẪN CHI TIẾT DÀNH CHO ĐOÀN TRƯỜNG & SAO ĐỎ (PHẦN 1)
    # =========================================================================
    story.append(make_section_banner(
        "PHẦN 4: CẨM NANG HƯỚNG DẪN DÀNH CHO ĐOÀN TRƯỜNG & ĐỘI SAO ĐỎ",
        "Quy trình chấm điểm nề nếp, thẩm định vi phạm 5 bước và quản lý thi đua tự động",
        bg_color=colors.HexColor('#059669')
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>CHƯƠNG 4.1: HƯỚNG DẪN CHẤM ĐIỂM TRÊN DI ĐỘNG CHO ĐỘI SAO ĐỎ (30 GIÂY)</b>", styles['H1']))
    story.append(Paragraph(
        "Đội Cờ đỏ / Sao đỏ được phân công trực tuần tại các vị trí (Cổng trường, Nhà xe, Khu phòng học, Giờ chào cờ) "
        "thực hiện việc chấm điểm và lập biên bản nề nếp trên điện thoại thông minh theo đúng 4 bước chuẩn hóa sau:",
        styles['Body']
    ))

    story.append(make_step_card(
        1,
        "ĐĂNG NHẬP & CHỌN MỤC 'GHI NHẬN VI PHẠM'",
        "Sao đỏ mở trình duyệt web trên điện thoại truy cập <b>http://hkstudenthub.io.vn</b> -> Đăng nhập tài khoản Sao đỏ -> Bấm nút <b>'Ghi nhận vi phạm'</b>.",
        PRIMARY
    ))
    story.append(Spacer(1, 3.5))

    story.append(make_step_card(
        2,
        "CHỌN KHỐI, LỚP VÀ HỌC SINH VI PHẠM",
        "• Chọn tab Khối (10, 11 hoặc 12) -> Chọn đúng Chi đoàn (ví dụ: 10A5, 11A2, 12A1).<br/>"
        "• Tìm chọn đích danh học sinh vi phạm trong danh sách lớp (hoặc tích chọn 'Lỗi tập thể' nếu lỗi do cả lớp như vệ sinh bẩn, bàn ghế lộn xộn).",
        SECONDARY
    ))
    story.append(Spacer(1, 3.5))

    story.append(make_step_card(
        3,
        "CHỌN MÃ NỘI QUY & CHỤP ẢNH BẰNG CHỨNG HIỆN TRƯỜNG",
        "• Chọn Danh mục nội quy (Đồng phục, Chuyên cần, Học tập, Vệ sinh, An toàn giao thông...) và chọn đúng Mã lỗi vi phạm.<br/>"
        "• Bấm nút <b>'Chụp ảnh minh chứng'</b> để kích hoạt camera điện thoại chụp ảnh bằng chứng (ảnh học sinh vi phạm đồng phục, xe vi phạm, rác lớp...).",
        ACCENT
    ))
    story.append(Spacer(1, 3.5))

    story.append(make_step_card(
        4,
        "BẤM 'GỬI BIÊN BẢN' – CHUYỂN TRẠNG THÁI PENDING",
        "Biên bản lập tức được gửi lên hệ thống và chuyển trạng thái sang <b>PENDING (Chờ xác minh)</b>. Hệ thống ghi nhận chính xác thời gian và tên Sao đỏ lập biên bản.",
        SUCCESS
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>CHƯƠNG 4.2: QUY TRÌNH THẨM ĐỊNH & DUYỆT VI PHẠM 5 BƯỚC CỦA ĐOÀN TRƯỜNG</b>", styles['H1']))
    story.append(Paragraph(
        "Đoàn trường là cơ quan duy nhất có thẩm quyền xem xét chứng cứ và ra quyết định trừ điểm thi đua của các Chi đoàn:",
        styles['Body']
    ))

    # Bảng 5 bước thẩm định
    steps_5_data = [
        [
            Paragraph("<b>Trạng thái</b>", styles['TableTh']),
            Paragraph("<b>Bản chất nghiệp vụ Đoàn trường</b>", styles['TableTh']),
            Paragraph("<b>Tác động điểm số</b>", styles['TableTh']),
            Paragraph("<b>Thao tác xử lý của Thầy/Cô Đoàn trường</b>", styles['TableTh']),
        ],
        [
            Paragraph("<b>PENDING</b>", styles['TableTdCode']),
            Paragraph("Biên bản mới gửi từ Sao đỏ hoặc GV.", styles['TableTd']),
            Paragraph("Chưa trừ điểm", styles['TableTdCenter']),
            Paragraph("Mở ảnh bằng chứng kiểm tra tính rõ nét và đúng quy định.", styles['TableTd']),
        ],
        [
            Paragraph("<b>VERIFIED</b>", styles['TableTdCode']),
            Paragraph("Chứng cứ chuẩn xác, duyệt áp dụng kỷ luật.", styles['TableTd']),
            Paragraph("<font color='#DC2626'><b>Trừ điểm ngay</b></font>", styles['TableTdCenter']),
            Paragraph("Bấm nút <font color='#DC2626'><b>'Xác nhận vi phạm'</b></font> để chính thức trừ điểm thi đua của lớp.", styles['TableTd']),
        ],
        [
            Paragraph("<b>APPEALING</b>", styles['TableTdCode']),
            Paragraph("Lớp trưởng hoặc GVCN gửi đơn khiếu nại.", styles['TableTd']),
            Paragraph("Tạm giữ mức trừ", styles['TableTdCenter']),
            Paragraph("Kiểm tra nội dung giải trình và tài liệu bổ sung của lớp.", styles['TableTd']),
        ],
        [
            Paragraph("<b>ADJUSTED</b>", styles['TableTdCode']),
            Paragraph("Chấp thuận khiếu nại có lý do chính đáng.", styles['TableTd']),
            Paragraph("<font color='#059669'><b>Hoàn 100% điểm</b></font>", styles['TableTdCenter']),
            Paragraph("Bấm <font color='#059669'><b>'Chấp thuận khiếu nại'</b></font>: Điểm thi đua của Chi đoàn được tự động phục hồi.", styles['TableTd']),
        ],
        [
            Paragraph("<b>DISMISSED</b>", styles['TableTdCode']),
            Paragraph("Ảnh mờ, lập nhầm đối tượng, sai quy định.", styles['TableTd']),
            Paragraph("Không trừ điểm", styles['TableTdCenter']),
            Paragraph("Bấm <font color='#64748B'><b>'Bác bỏ biên bản'</b></font>: Hủy bỏ bản ghi khỏi hệ thống tính điểm.", styles['TableTd']),
        ],
    ]
    t_steps5 = Table(steps_5_data, colWidths=[70, 160, 95, 198])
    t_steps5.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#FFFBEB')),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#FEF2F2')),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#FAF5FF')),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor('#F0FDF4')),
        ('BACKGROUND', (0,5), (-1,5), BG_LIGHT),
    ]))
    story.append(t_steps5)

    # Hết Trang 6 -> Chuyển sang Trang 7 (Tiếp tục Đoàn trường: Thi đua, Podium, Khóa sổ, Báo cáo)
    story.append(PageBreak())

    # =========================================================================
    # TRANG 7: CẨM NANG HƯỚNG DẪN CHI TIẾT DÀNH CHO ĐOÀN TRƯỜNG & SAO ĐỎ (PHẦN 2)
    # =========================================================================
    story.append(make_section_banner(
        "PHẦN 4 (TIẾP THEO): THI ĐUA CHI ĐOÀN, KHÓA SỔ & XUẤT BÁO CÁO VĂN BẢN",
        "Công thức thi đua minh bạch, Bục vinh danh Podium và thủ tục công bố điểm tuần",
        bg_color=colors.HexColor('#059669')
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>CHƯƠNG 4.3: QUẢN LÝ THI ĐUA CHI ĐOÀN & NHẬP ĐIỂM CỘNG PHONG TRÀO</b>", styles['H1']))
    story.append(Paragraph(
        "Hệ thống tính điểm thi đua tự động vận hành trên nền tảng biểu điểm công bằng tuyệt đối:",
        styles['Body']
    ))
    story.append(Paragraph("• <b>Điểm chuẩn đầu tuần:</b> Mỗi Chi đoàn nhận mặc định <b>100.0 điểm</b> vào 00h00 sáng thứ Hai.", styles['Bullet']))
    story.append(Paragraph("• <b>Trừ điểm tự động:</b> Hệ thống chỉ trừ điểm đối với các lỗi ở trạng thái <b>VERIFIED</b>. Tuyệt đối không trừ điểm đối với lỗi PENDING hoặc đang khiếu nại APPEALING.", styles['Bullet']))
    story.append(Paragraph("• <b>Quy trình nhập Điểm cộng phong trào:</b> Thầy/Cô Đoàn trường vào mục <b>Thi đua (competition)</b> -> Bấm <b>'Cộng điểm phong trào'</b> -> Chọn Chi đoàn -> Chọn loại hoạt động (Hoa điểm mười, thi văn nghệ 20/11, giải bóng đá/điền kinh, lao động tình nguyện...) -> Nhập số điểm cộng kèm quyết định khen thưởng.", styles['BulletBold']))
    story.append(Spacer(1, 5))

    story.append(Paragraph("<b>CHƯƠNG 4.4: BỤC VINH DANH PODIUM & QUY TRÌNH KHÓA SỔ KỲ THI ĐUA (LOCKING)</b>", styles['H1']))
    story.append(Paragraph(
        "• <b>Bục vinh danh Podium Top 3:</b> Hiển thị nổi bật tại trang chủ thi đua với mô hình 3 bậc vinh danh Chi đoàn xếp thứ 1 (Cúp Vàng), thứ 2 (Cúp Bạc) và thứ 3 (Cúp Đồng). Điểm số và thứ bậc tự động cập nhật ngay khi có biên bản mới được duyệt.",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>Quy trình Khóa sổ kỳ thi đua (17h00 thứ Bảy hàng tuần):</b><br/>"
        "  1. Đoàn trường rà soát toàn bộ các đơn khiếu nại trong tuần để đảm bảo không còn đơn tồn đọng.<br/>"
        "  2. Vào mục Cài đặt kỳ thi đua -> Bấm nút <font color='#D97706'><b>'Khóa sổ thi đua tuần'</b></font>.<br/>"
        "  3. Sau khi khóa, hệ thống <b>cố định vĩnh viễn bảng điểm tuần</b>, ngăn chặn mọi hành vi can thiệp sửa đổi điểm số, đảm bảo tính pháp lý tuyệt đối.",
        styles['Body']
    ))
    story.append(Spacer(1, 5))

    story.append(Paragraph("<b>CHƯƠNG 4.5: XUẤT BÁO CÁO THI ĐUA VĂN BẢN (EXCEL & PDF)</b>", styles['H1']))
    story.append(Paragraph(
        "Đoàn trường có thể xuất bản bảng tổng hợp thi đua phục vụ lễ chào cờ đầu tuần chỉ với 1 cú nhấp chuột:",
        styles['Body']
    ))
    story.append(Paragraph("• <b>Xuất file Excel (.xlsx):</b> Bảng tính chi tiết xếp hạng toàn bộ 65 lớp, phân rã số lỗi theo từng nhóm nội quy, tính điểm trung bình theo khối (Khối 10, Khối 11, Khối 12) để lưu trữ nội bộ.", styles['Bullet']))
    story.append(Paragraph("• <b>Xuất file PDF (.pdf) hành chính chuẩn:</b> Báo cáo văn bản đúng thể thức Bộ Giáo dục, đầy đủ Quốc hiệu, Tiêu ngữ, bảng xếp hạng trang trọng, chữ ký của Bí thư Đoàn trường và Hiệu trưởng sẵn sàng in ấn niêm yết tại bảng tin trường.", styles['Bullet']))
    story.append(Spacer(1, 5))

    story.append(make_callout(
        "QUY ĐỊNH VỀ THỜI HẠN GIẢI QUYẾT KHIẾU NẠI THI ĐUA",
        "Mọi khiếu nại của Lớp trưởng và GVCN phải được gửi trước 12h00 thứ Bảy hàng tuần. "
        "Sau 17h00 thứ Bảy khi Đoàn trường đã bấm 'Khóa sổ thi đua tuần', hệ thống sẽ không tiếp nhận khiếu nại bổ sung của tuần đó.",
        "warning"
    ))

    # Hết Trang 7 -> Chuyển sang Trang 8 (Bắt đầu Phần Quản trị viên & Hệ thống cảnh báo)
    story.append(PageBreak())

    # =========================================================================
    # TRANG 8: HƯỚNG DẪN DÀNH CHO QUẢN TRỊ VIÊN & HỆ THỐNG CẢNH BÁO ĐA KÊNH
    # =========================================================================
    story.append(make_section_banner(
        "PHẦN 5: HƯỚNG DẪN DÀNH CHO QUẢN TRỊ VIÊN (ADMIN) & CẢNH BÁO ĐA KÊNH",
        "Cấu hình năm học, quản lý tài khoản, nhật ký kiểm toán và cổng SMS/Email",
        bg_color=PRIMARY
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>CHƯƠNG 5.1: HỆ THỐNG CẢNH BÁO TỰ ĐỘNG ĐA KÊNH (EMAIL & SMS)</b>", styles['H1']))
    story.append(Paragraph(
        "HK Student Hub tích hợp 2 kênh truyền thông tự động đảm bảo thông tin thông suốt giữa Nhà trường, Giáo viên và Phụ huynh:",
        styles['Body']
    ))

    notif_table_data = [
        [
            Paragraph("<b>Kênh cảnh báo</b>", styles['TableTh']),
            Paragraph("<b>Công nghệ sử dụng</b>", styles['TableTh']),
            Paragraph("<b>Đối tượng nhận</b>", styles['TableTh']),
            Paragraph("<b>Kịch bản gửi tự động tức thời</b>", styles['TableTh']),
        ],
        [
            Paragraph("<b>Email thông báo</b><br/><i>(SMTP Gmail)</i>", styles['TableTdBold']),
            Paragraph("Transactional Outbox + Django Core Mail", styles['TableTd']),
            Paragraph("• GVCN lớp vi phạm<br/>• Bí thư Đoàn trường", styles['TableTd']),
            Paragraph("Gửi email tức thì ngay khi học sinh bị lập biên bản vi phạm mới, khi Lớp trưởng gửi đơn khiếu nại hoặc khi có kết quả hoàn điểm.", styles['TableTd']),
        ],
        [
            Paragraph("<b>Tin nhắn SMS</b><br/><i>(SpeedSMS Gateway)</i>", styles['TableTdBold']),
            Paragraph("SpeedSMS REST API Service", styles['TableTd']),
            Paragraph("• Phụ huynh học sinh<br/>• Giáo viên chủ nhiệm", styles['TableTd']),
            Paragraph("Tự động bắn tin nhắn SMS đến số điện thoại phụ huynh đối với các lỗi kỷ luật nghiêm trọng: Bỏ tiết, trốn học, đánh nhau, hút thuốc lá điện tử...", styles['TableTd']),
        ],
    ]
    t_notif = Table(notif_table_data, colWidths=[95, 120, 110, 198])
    t_notif.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,1), (-1,1), BG_LIGHT),
    ]))
    story.append(t_notif)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>CHƯƠNG 5.2: NGHIỆP VỤ QUẢN TRỊ VIÊN HỆ THỐNG (ADMIN)</b>", styles['H1']))
    story.append(Paragraph("• <b>Khởi tạo Năm học & Tự động sinh 35 tuần thi đua:</b> Quản trị viên vào Cài đặt -> Tạo Năm học mới (ví dụ: 2026 - 2027), chọn ngày bắt đầu tuần 1. Hệ thống tự động sinh 35 tuần thi đua chuẩn theo biên chế năm học của Sở GD&ĐT.", styles['Bullet']))
    story.append(Paragraph("• <b>Quản lý Tài khoản & Phân quyền:</b> Cấp quyền Admin, BGH, Đoàn trường, GVCN, GVBM, Sao đỏ, Chuyên viên tâm lý. Thao tác Khóa tạm thời (Suspended) đối với tài khoản vi phạm chính sách mạng hoặc mở khóa khi đã hoàn thành kiểm điểm.", styles['Bullet']))
    story.append(Paragraph("• <b>Nhật ký Kiểm toán (Audit Logs):</b> Mọi hành vi đăng nhập, thay đổi điểm số, duyệt/hủy vi phạm đều được lưu vết thời gian chính xác đến từng mili-giây cùng địa chỉ IP truy cập, đảm bảo tính minh bạch tuyệt đối.", styles['Bullet']))
    story.append(Spacer(1, 5))

    story.append(Paragraph("<b>CHƯƠNG 5.3: HẠ TẦNG MẠNG VÀ BẢO MẬT CLOUDFLARE EDGE</b>", styles['H1']))
    story.append(Paragraph(
        "Hệ thống vận hành thông qua công nghệ <b>Cloudflare Edge Tunnel</b> tại tên miền chính thức <b>http://hkstudenthub.io.vn</b>. "
        "Mọi kết nối được mã hóa đầu cuối, tự động lọc mã độc XSS/CSRF, phòng chống tấn công DDoS và duy trì tốc độ phản hồi trang dưới 0.3 giây "
        "ngay cả khi hơn 2.500 học sinh cùng truy cập đồng thời trong các buổi chào cờ đầu tuần.",
        styles['Body']
    ))

    # Hết Trang 8 -> Chuyển sang Trang 9 (Bảng Cheatsheet & Biểu điểm)
    story.append(PageBreak())

    # =========================================================================
    # TRANG 9: BẢNG TRA CỨU NHANH THEO VAI TRÒ & BIỂU ĐIỂM VI PHẠM THƯỜNG GẶP
    # =========================================================================
    story.append(make_section_banner(
        "PHẦN 6: BẢNG TRA CỨU NHANH THEO VAI TRÒ & TRÍCH DẪN BIỂU ĐIỂM NỘI QUY",
        "Cẩm nang tóm tắt thao tác 1 phút và bảng điểm trừ chuẩn hóa Trường THPT Hương Khê"
    ))
    story.append(Spacer(1, 6))

    # Bảng Cheatsheet 1 phút
    cs_data = [
        [
            Paragraph("<b>Nhóm người dùng</b>", styles['TableTh']),
            Paragraph("<b>Mục tiêu chính</b>", styles['TableTh']),
            Paragraph("<b>Thao tác trọng tâm cần thực hiện</b>", styles['TableTh']),
        ],
        [
            Paragraph("<b>Học sinh</b>", styles['TableTdBold']),
            Paragraph("Tu dưỡng & Kết nối", styles['TableTd']),
            Paragraph("Đăng nhập Google, hoàn thiện hồ sơ lớp, tra cứu nề nếp cá nhân, gửi tâm sự ẩn danh tại Góc sẻ chia và lưu mã GSC-xxxx.", styles['TableTd']),
        ],
        [
            Paragraph("<b>⭐ Lớp trưởng</b>", styles['TableTdBold']),
            Paragraph("Đại diện Chi đoàn", styles['TableTd']),
            Paragraph("Vào mục Nề nếp giám sát vi phạm của lớp mình, gửi Đơn khiếu nại (Appeal) giải trình khi có lỗi ghi nhầm.", styles['TableTd']),
        ],
        [
            Paragraph("<b>Giáo viên BM</b>", styles['TableTdBold']),
            Paragraph("Sổ nhận xét tiết dạy", styles['TableTd']),
            Paragraph("Lọc Khối/Lớp, ghi nhận xét đích danh học sinh theo tiết học về thái độ học tập, bài tập về nhà và bài kiểm tra.", styles['TableTd']),
        ],
        [
            Paragraph("<b>Giáo viên CN</b>", styles['TableTdBold']),
            Paragraph("Quản lý & Bảo vệ lớp", styles['TableTd']),
            Paragraph("Bổ nhiệm ⭐ Lớp trưởng, theo dõi cảnh báo vi phạm qua Email/SMS, gửi khiếu nại bảo vệ điểm thi đua của Chi đoàn.", styles['TableTd']),
        ],
        [
            Paragraph("<b>Đội Sao đỏ</b>", styles['TableTdBold']),
            Paragraph("Chấm điểm di động", styles['TableTd']),
            Paragraph("Chọn Khối -> Lớp -> Học sinh vi phạm -> Chọn mã lỗi -> Chụp ảnh bằng chứng hiện trường -> Bấm gửi biên bản (30 giây).", styles['TableTd']),
        ],
        [
            Paragraph("<b>Đoàn trường</b>", styles['TableTdBold']),
            Paragraph("Thẩm định & Thi đua", styles['TableTd']),
            Paragraph("Duyệt học sinh mới, thẩm định vi phạm PENDING -> VERIFIED, xử lý khiếu nại, cộng điểm phong trào, khóa sổ tuần lúc 17h thứ Bảy.", styles['TableTd']),
        ],
        [
            Paragraph("<b>Ban Giám hiệu</b>", styles['TableTdBold']),
            Paragraph("Giám sát toàn trường", styles['TableTd']),
            Paragraph("Xem Dashboard trực quan, theo dõi Bục vinh danh Podium Top 3, phê duyệt thi đua và xem báo cáo xuất file định kỳ.", styles['TableTd']),
        ],
    ]
    t_cs = Table(cs_data, colWidths=[90, 115, 318])
    t_cs.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4.5),
        ('RIGHTPADDING', (0,0), (-1,-1), 4.5),
        ('BACKGROUND', (0,1), (-1,1), BG_LIGHT),
        ('BACKGROUND', (0,3), (-1,3), BG_LIGHT),
        ('BACKGROUND', (0,5), (-1,5), BG_LIGHT),
        ('BACKGROUND', (0,7), (-1,7), BG_LIGHT),
    ]))
    story.append(t_cs)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>TRÍCH DẪN MỘT SỐ MÃ LỖI VI PHẠM & BIỂU ĐIỂM TRỪ NỀ NẾP CHUẨN:</b>", styles['H1']))

    rule_data = [
        [
            Paragraph("<b>Mã lỗi</b>", styles['TableTh']),
            Paragraph("<b>Danh mục nội quy</b>", styles['TableTh']),
            Paragraph("<b>Mô tả hành vi vi phạm</b>", styles['TableTh']),
            Paragraph("<b>Điểm trừ thi đua</b>", styles['TableTh']),
            Paragraph("<b>Mức độ xử lý</b>", styles['TableTh']),
        ],
        [
            Paragraph("DP-01", styles['TableTdCode']),
            Paragraph("Trang phục – Tác phong", styles['TableTd']),
            Paragraph("Không mặc áo đồng phục hoặc không đeo phù hiệu trường.", styles['TableTd']),
            Paragraph("<font color='#DC2626'><b>-2.0 điểm</b></font>", styles['TableTdCenter']),
            Paragraph("Nhắc nhở / Lập biên bản", styles['TableTd']),
        ],
        [
            Paragraph("CC-02", styles['TableTdCode']),
            Paragraph("Chuyên cần – Điểm danh", styles['TableTd']),
            Paragraph("Đi học muộn sau khi đã có hiệu lệnh trống vào lớp.", styles['TableTd']),
            Paragraph("<font color='#DC2626'><b>-2.0 điểm</b></font>", styles['TableTdCenter']),
            Paragraph("Ghi nhận danh sách", styles['TableTd']),
        ],
        [
            Paragraph("CC-05", styles['TableTdCode']),
            Paragraph("Chuyên cần – Nghỉ học", styles['TableTd']),
            Paragraph("Nghỉ học không có giấy phép hoặc trốn tiết giữa giờ.", styles['TableTd']),
            Paragraph("<font color='#DC2626'><b>-5.0 điểm</b></font>", styles['TableTdCenter']),
            Paragraph("Bắn tin nhắn SMS về PH", styles['TableTd']),
        ],
        [
            Paragraph("HT-03", styles['TableTdCode']),
            Paragraph("Nề nếp học tập", styles['TableTd']),
            Paragraph("Sử dụng điện thoại di động trong giờ học không phục vụ môn học.", styles['TableTd']),
            Paragraph("<font color='#DC2626'><b>-5.0 điểm</b></font>", styles['TableTdCenter']),
            Paragraph("Tạm giữ & biên bản", styles['TableTd']),
        ],
        [
            Paragraph("GT-01", styles['TableTdCode']),
            Paragraph("An toàn giao thông", styles['TableTd']),
            Paragraph("Học sinh đi xe máy điện / xe gắn máy không đội mũ bảo hiểm.", styles['TableTd']),
            Paragraph("<font color='#DC2626'><b>-10.0 điểm</b></font>", styles['TableTdCenter']),
            Paragraph("Hạ bậc hạnh kiểm tuần", styles['TableTd']),
        ],
        [
            Paragraph("KL-09", styles['TableTdCode']),
            Paragraph("Kỷ luật nghiêm trọng", styles['TableTd']),
            Paragraph("Gây gổ, đánh nhau, mang chất kích thích / thuốc lá điện tử.", styles['TableTd']),
            Paragraph("<font color='#DC2626'><b>-20.0 điểm</b></font>", styles['TableTdCenter']),
            Paragraph("Hội đồng Kỷ luật xử lý", styles['TableTd']),
        ],
    ]
    t_rules = Table(rule_data, colWidths=[48, 110, 195, 80, 90])
    t_rules.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('BACKGROUND', (0,1), (-1,1), BG_LIGHT),
        ('BACKGROUND', (0,3), (-1,3), BG_LIGHT),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor('#FEF2F2')),
    ]))
    story.append(t_rules)

    # Hết Trang 9 -> Chuyển sang Trang 10 (FAQ & Hỗ trợ kỹ thuật)
    story.append(PageBreak())

    # =========================================================================
    # TRANG 10: HỎI ĐÁP SỰ CỐ THƯỜNG GẶP (FAQ) & THÔNG TIN HỖ TRỢ KỸ THUẬT
    # =========================================================================
    story.append(make_section_banner(
        "PHẦN 7: CÂU HỎI THƯỜNG GẶP (FAQ) & HỖ TRỢ KỸ THUẬT CHÍNH THỨC",
        "Kênh tiếp nhận hỗ trợ: http://hkstudenthub.io.vn • Trường THPT Hương Khê"
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>1. GIẢI ĐÁP CÁC TÌNH HUỐNG SỰ CỐ THƯỜNG GẶP (FAQ):</b>", styles['H1']))
    story.append(Paragraph(
        "<b>Câu hỏi 1: Học sinh đăng nhập tài khoản Google thành công nhưng không thể xem bảng điểm thi đua?</b><br/>"
        "<i>Trả lời:</i> Sau khi đăng nhập Google lần đầu, tài khoản ở trạng thái PENDING. Học sinh cần hoàn thành biểu mẫu hoàn thiện hồ sơ "
        "tại <b>http://hkstudenthub.io.vn/complete-profile</b> và báo Lớp trưởng hoặc Thầy/Cô chủ nhiệm để Đoàn trường phê duyệt kích hoạt.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>Câu hỏi 2: Lớp trưởng nộp đơn khiếu nại (Appeal) thì sau bao lâu sẽ có kết quả phân giải?</b><br/>"
        "<i>Trả lời:</i> Thầy/Cô phụ trách nề nếp Đoàn trường sẽ tiếp nhận và phản hồi chậm nhất trong 24 giờ làm việc. "
        "Mọi khiếu nại hợp lệ sẽ được giải quyết dứt điểm trước 17h00 thứ Bảy trước khi tiến hành khóa sổ tuần.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>Câu hỏi 3: Học sinh gửi tâm sự ở phân hệ 'Góc sẻ chia' nhưng quên mất Mã tra cứu thì phải làm sao?</b><br/>"
        "<i>Trả lời:</i> Nhằm bảo đảm tính bảo mật và cách ly tuyệt đối, hệ thống hoàn toàn không lưu vết danh tính người hỏi. "
        "Nếu làm mất mã tra cứu, em vui lòng gửi lại một tâm sự mới và ghi chép lại mã <b>GSC-2026-XXXX</b> ngay khi hệ thống cấp.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>Câu hỏi 4: Đội Sao đỏ khi chấm điểm gặp sự cố mất mạng Internet 4G/Wifi thì biên bản có bị mất không?</b><br/>"
        "<i>Trả lời:</i> Ứng dụng tích hợp công nghệ đệm dữ liệu cục bộ (Offline Cache). Khi mạng gián đoạn, ảnh và thông tin lỗi tạm lưu "
        "trên máy và sẽ tự động đồng bộ gửi về máy chủ ngay khi điện thoại kết nối lại Internet.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>Câu hỏi 5: Thầy/Cô giáo viên chủ nhiệm muốn xuất danh sách vi phạm của lớp mình để họp phụ huynh thì thao tác thế nào?</b><br/>"
        "<i>Trả lời:</i> Thầy cô vào mục <b>Báo cáo (reports)</b> -> Chọn lớp mình chủ nhiệm -> Chọn khoảng thời gian (Tuần, Tháng hoặc Học kỳ) "
        "-> Bấm nút <b>'Xuất Excel'</b> hoặc <b>'Xuất PDF'</b>. Hệ thống sẽ kết xuất tệp văn bản đã được căn lề, định dạng chuẩn để in ấn trực tiếp.",
        styles['Body']
    ))
    story.append(Spacer(1, 8))

    # Khung liên hệ chính thức
    contact_box = [
        [
            Paragraph("<b>TRUNG TÂM QUẢN TRỊ KỸ THUẬT & HỖ TRỢ NGƯỜI DÙNG HK STUDENT HUB</b><br/>"
                      "• <b>Cơ quan chủ quản:</b> Ban Giám hiệu & Đoàn Thanh niên – Trường THPT Hương Khê<br/>"
                      "• <b>Địa chỉ:</b> Thị trấn Hương Khê, Huyện Hương Khê, Tỉnh Hà Tĩnh<br/>"
                      "• <b>Cổng thông tin trực tuyến:</b> <font color='#0284C7'><u>http://hkstudenthub.io.vn</u></font><br/>"
                      "• <b>Hòm thư điện tử tiếp nhận phản ánh:</b> thpthk.edumentor@gmail.com<br/>"
                      "• <b>Hỗ trợ kỹ thuật phần mềm:</b> Tổ Công nghệ Thông tin – Trường THPT Hương Khê<br/>"
                      "• <b>Đường dây nóng khẩn cấp bảo vệ học sinh:</b> <b>111</b> (Tổng đài Quốc gia Bảo vệ Trẻ em – 24/7)", styles['CoverMetaBox']),
        ]
    ]
    t_contact = Table(contact_box, colWidths=[content_width])
    t_contact.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
        ('BOX', (0,0), (-1,-1), 1.2, PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_contact)

    # =========================================================================
    # XÂY DỰNG FILE PDF
    # =========================================================================
    primary_target = output_paths[0]
    os.makedirs(os.path.dirname(primary_target), exist_ok=True)
    doc = SimpleDocTemplate(
        primary_target,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=38,
        bottomMargin=36,
        title="Sổ tay Hướng dẫn Sử dụng Hệ thống HK Student Hub – THPT Hương Khê",
        author="Ban Quản trị CNTT THPT Hương Khê",
        subject="Tài liệu Hướng dẫn sử dụng trực quan cổng thông tin http://hkstudenthub.io.vn",
    )
    doc.build(story, canvasmaker=UserGuideCanvas)
    print(f"[*] Xuất bản thành công: {primary_target} ({os.path.getsize(primary_target):,} bytes)")

    for secondary_target in output_paths[1:]:
        os.makedirs(os.path.dirname(secondary_target), exist_ok=True)
        shutil.copyfile(primary_target, secondary_target)
        print(f"[*] Bản sao chép thành công: {secondary_target} ({os.path.getsize(secondary_target):,} bytes)")


if __name__ == '__main__':
    targets = [
        str(BASE_DIR / 'HUONG_DAN_SU_DUNG_HK_STUDENT_HUB.pdf'),
        str(Path(r'C:\Users\XC\Desktop\prj\HUONG_DAN_SU_DUNG_HK_STUDENT_HUB.pdf')),
        str(Path(r'C:\Users\XC\.gemini\antigravity\brain\7c14edee-4ce4-41ce-bbb6-ad094938a704\HUONG_DAN_SU_DUNG_HK_STUDENT_HUB.pdf')),
    ]
    build_user_guide_pdf(targets)
