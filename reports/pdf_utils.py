# -*- coding: utf-8 -*-
"""
Tiện ích xuất PDF chuẩn hóa sử dụng Font Times New Roman cho hệ thống HK Student Hub – THPT Hương Khê, Hà Tĩnh.
Hỗ trợ đầy đủ tiếng Việt có dấu, nhúng font TrueType, bố cục hành chính chuẩn, header, footer và đánh số trang.
"""
import os
import re
import unicodedata
from pathlib import Path
from django.conf import settings
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet


_FONTS_INITIALIZED = False
_PRIMARY_FONT_NAME = 'TimesNewRoman'
_BOLD_FONT_NAME = 'TimesNewRoman-Bold'
_ITALIC_FONT_NAME = 'TimesNewRoman-Italic'
_BOLD_ITALIC_FONT_NAME = 'TimesNewRoman-BoldItalic'


def find_font_file(filename_candidates):
    """
    Tìm kiếm tệp font trong thư mục static của dự án và các thư mục font hệ điều hành (Windows, Linux).
    """
    if isinstance(filename_candidates, str):
        filename_candidates = [filename_candidates]

    search_dirs = [
        settings.BASE_DIR / 'static' / 'fonts',
        settings.BASE_DIR / 'reports' / 'fonts',
        Path('C:/Windows/Fonts'),
        Path('C:/WINDOWS/Fonts'),
        Path('/usr/share/fonts/truetype/msttcorefonts'),
        Path('/usr/share/fonts/truetype'),
        Path('/usr/share/fonts'),
    ]

    for d in search_dirs:
        if not d.exists():
            continue
        for candidate in filename_candidates:
            p = d / candidate
            if p.exists() and p.is_file():
                return str(p)
            # Case insensitive check
            for item in d.glob('*'):
                if item.name.lower() == candidate.lower():
                    return str(item)
    return None


def setup_times_new_roman_fonts():
    """
    Đăng ký bộ font Times New Roman (Regular, Bold, Italic, BoldItalic) vào ReportLab.
    Bảo đảm nhúng font trực tiếp vào PDF để hỗ trợ tiếng Việt trên mọi thiết bị.
    """
    global _FONTS_INITIALIZED, _PRIMARY_FONT_NAME, _BOLD_FONT_NAME, _ITALIC_FONT_NAME, _BOLD_ITALIC_FONT_NAME

    if _FONTS_INITIALIZED:
        return _PRIMARY_FONT_NAME

    reg_path = find_font_file(['times.ttf', 'Times.ttf', 'times_new_roman.ttf', 'TimesNewRoman.ttf'])
    bold_path = find_font_file(['timesbd.ttf', 'Timesbd.ttf', 'times_bold.ttf', 'TimesBold.ttf'])
    italic_path = find_font_file(['timesi.ttf', 'Timesi.ttf', 'times_italic.ttf', 'TimesItalic.ttf'])
    bolditalic_path = find_font_file(['timesbi.ttf', 'Timesbi.ttf', 'times_bold_italic.ttf'])

    # Fallback to LiberationSerif or DejaVuSerif if Times New Roman is missing in environment
    if not reg_path:
        reg_path = find_font_file(['LiberationSerif-Regular.ttf', 'DejaVuSerif.ttf'])
        bold_path = find_font_file(['LiberationSerif-Bold.ttf', 'DejaVuSerif-Bold.ttf']) or reg_path
        italic_path = find_font_file(['LiberationSerif-Italic.ttf', 'DejaVuSerif-Italic.ttf']) or reg_path
        bolditalic_path = find_font_file(['LiberationSerif-BoldItalic.ttf', 'DejaVuSerif-BoldItalic.ttf']) or bold_path

    if not reg_path:
        raise FileNotFoundError(
            "Không tìm thấy tệp font Times New Roman (.ttf) hợp lệ hỗ trợ tiếng Việt Unicode. "
            "Vui lòng đảm bảo các tệp times.ttf, timesbd.ttf, timesi.ttf được lưu trong static/fonts/."
        )

    # Register Regular
    pdfmetrics.registerFont(TTFont(_PRIMARY_FONT_NAME, reg_path))

    # Register Bold
    if bold_path and os.path.exists(bold_path):
        pdfmetrics.registerFont(TTFont(_BOLD_FONT_NAME, bold_path))
    else:
        pdfmetrics.registerFont(TTFont(_BOLD_FONT_NAME, reg_path))

    # Register Italic
    if italic_path and os.path.exists(italic_path):
        pdfmetrics.registerFont(TTFont(_ITALIC_FONT_NAME, italic_path))
    else:
        pdfmetrics.registerFont(TTFont(_ITALIC_FONT_NAME, reg_path))

    # Register BoldItalic
    if bolditalic_path and os.path.exists(bolditalic_path):
        pdfmetrics.registerFont(TTFont(_BOLD_ITALIC_FONT_NAME, bolditalic_path))
    else:
        pdfmetrics.registerFont(TTFont(_BOLD_ITALIC_FONT_NAME, _BOLD_FONT_NAME if bold_path else reg_path))

    # Register family mapping so <b> and <i> tags in Paragraph automatically resolve correctly
    pdfmetrics.registerFontFamily(
        _PRIMARY_FONT_NAME,
        normal=_PRIMARY_FONT_NAME,
        bold=_BOLD_FONT_NAME,
        italic=_ITALIC_FONT_NAME,
        boldItalic=_BOLD_ITALIC_FONT_NAME
    )

    _FONTS_INITIALIZED = True
    return _PRIMARY_FONT_NAME


class NumberedCanvas(canvas.Canvas):
    """
    Canvas hai lượt (two-pass) của ReportLab:
    - Lưu lại tất cả lệnh vẽ trang
    - Đến trang cuối cùng, duyệt lại để vẽ Header và Footer với số trang chính xác "Trang X / Y"
    - Bảo đảm Header/Footer và lề in đều chuẩn hóa với font Times New Roman
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
        self.saveState()

        # Ensure Times New Roman font is registered
        setup_times_new_roman_fonts()

        page_width, page_height = self._pagesize

        # Margins: 20mm (~56.7pt)
        left = 45
        right = page_width - 45

        # 1. HEADER (chỉ hiển thị từ trang 2 trở đi hoặc trang 1 nếu báo cáo dài)
        if self._pageNumber > 1:
            header_y = page_height - 32
            self.setFont(_BOLD_FONT_NAME, 8.5)
            self.setFillColor(colors.HexColor('#163A70'))
            self.drawString(left, header_y, "TRƯỜNG THPT HƯƠNG KHÊ – HÀ TĨNH")

            self.setFont(_ITALIC_FONT_NAME, 8)
            self.setFillColor(colors.HexColor('#64748B'))
            self.drawRightString(right, header_y, "HK Student Hub – Hệ thống quản lý & thi đua nền nếp")

            self.setStrokeColor(colors.HexColor('#CBD5E1'))
            self.setLineWidth(0.5)
            self.line(left, header_y - 4, right, header_y - 4)

        # 2. FOOTER (ở tất cả các trang)
        footer_y = 28
        self.setStrokeColor(colors.HexColor('#E2E8F0'))
        self.setLineWidth(0.5)
        self.line(left, footer_y + 12, right, footer_y + 12)

        self.setFont(_ITALIC_FONT_NAME, 8.5)
        self.setFillColor(colors.HexColor('#64748B'))
        self.drawString(left, footer_y, "HK Student Hub – Báo cáo chính thức Trường THPT Hương Khê • code by cuongdev1108")

        page_str = f"Trang {self._pageNumber} / {page_count}"
        self.drawRightString(right, footer_y, page_str)

        self.restoreState()


def get_standard_pdf_styles():
    """
    Tạo bộ ParagraphStyle chuẩn hóa hành chính sử dụng 100% font Times New Roman.
    """
    setup_times_new_roman_fonts()
    base = getSampleStyleSheet()

    styles = {
        'OrgHeader': ParagraphStyle(
            'OrgHeader',
            parent=base['Normal'],
            fontName=_PRIMARY_FONT_NAME,
            fontSize=10,
            leading=13,
            alignment=0,  # Left
            textColor=colors.HexColor('#163A70'),
        ),
        'OrgHeaderRight': ParagraphStyle(
            'OrgHeaderRight',
            parent=base['Normal'],
            fontName=_PRIMARY_FONT_NAME,
            fontSize=10,
            leading=13,
            alignment=2,  # Right
            textColor=colors.HexColor('#1E293B'),
        ),
        'DocTitle': ParagraphStyle(
            'DocTitle',
            parent=base['Heading1'],
            fontName=_PRIMARY_FONT_NAME,
            fontSize=15,
            leading=19,
            alignment=1,  # Center
            textColor=colors.HexColor('#163A70'),
            spaceAfter=4,
        ),
        'DocSubtitle': ParagraphStyle(
            'DocSubtitle',
            parent=base['Normal'],
            fontName=_PRIMARY_FONT_NAME,
            fontSize=10.5,
            leading=14,
            alignment=1,  # Center
            textColor=colors.HexColor('#475569'),
            spaceAfter=12,
        ),
        'SectionHeading': ParagraphStyle(
            'SectionHeading',
            parent=base['Heading2'],
            fontName=_PRIMARY_FONT_NAME,
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=8,
            spaceAfter=4,
        ),
        'Body': ParagraphStyle(
            'Body',
            parent=base['Normal'],
            fontName=_PRIMARY_FONT_NAME,
            fontSize=10.5,
            leading=14.5,
            textColor=colors.HexColor('#1E293B'),
            alignment=4,  # Justified
        ),
        'BodyItalic': ParagraphStyle(
            'BodyItalic',
            parent=base['Normal'],
            fontName=_PRIMARY_FONT_NAME,
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor('#64748B'),
        ),
        'TableHead': ParagraphStyle(
            'TableHead',
            parent=base['Normal'],
            fontName=_PRIMARY_FONT_NAME,
            fontSize=9.5,
            leading=12,
            alignment=1,  # Center
            textColor=colors.white,
        ),
        'TableCell': ParagraphStyle(
            'TableCell',
            parent=base['Normal'],
            fontName=_PRIMARY_FONT_NAME,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#1E293B'),
        ),
        'TableCellCenter': ParagraphStyle(
            'TableCellCenter',
            parent=base['Normal'],
            fontName=_PRIMARY_FONT_NAME,
            fontSize=9,
            leading=12,
            alignment=1,  # Center
            textColor=colors.HexColor('#1E293B'),
        ),
        'TableCellBold': ParagraphStyle(
            'TableCellBold',
            parent=base['Normal'],
            fontName=_PRIMARY_FONT_NAME,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#163A70'),
        ),
        'SignatureTitle': ParagraphStyle(
            'SignatureTitle',
            parent=base['Normal'],
            fontName=_PRIMARY_FONT_NAME,
            fontSize=10,
            leading=13,
            alignment=1,
            textColor=colors.HexColor('#1E293B'),
        ),
        'SignatureDate': ParagraphStyle(
            'SignatureDate',
            parent=base['Normal'],
            fontName=_PRIMARY_FONT_NAME,
            fontSize=9.5,
            leading=13,
            alignment=1,
            textColor=colors.HexColor('#475569'),
        ),
    }
    return styles


def safe_filename(name):
    """
    Chuyển đổi tên file sang dạng an toàn chuẩn ASCII/Header HTTP.
    Ví dụ: 'Báo cáo vi phạm 12A1.pdf' -> 'Bao_cao_vi_pham_12A1.pdf'
    """
    nfkd = unicodedata.normalize('NFKD', name)
    no_accents = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    no_accents = no_accents.replace('đ', 'd').replace('Đ', 'D')
    clean = re.sub(r'[^\w\s.-]', '', no_accents)
    clean = re.sub(r'[\s]+', '_', clean)
    return clean
