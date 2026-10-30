# -*- coding: utf-8 -*-
"""
Script tạo file PDF Báo cáo tổng thể hệ thống HK Student Hub – THPT Hương Khê.
Sử dụng ReportLab, font Times New Roman nhúng chuẩn Unicode tiếng Việt,
NumberedCanvas đánh số trang 'Trang X / Y', bố cục hành chính và thiết kế chuyên nghiệp.
"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from datetime import datetime

# Setup paths and django environment
BASE_DIR = Path(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub')
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')

import django
django.setup()

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak, HRFlowable
)
from reports.pdf_utils import setup_times_new_roman_fonts, NumberedCanvas

def build_system_report_pdf(output_paths):
    font_name = setup_times_new_roman_fonts()
    bold_font = 'TimesNewRoman-Bold'
    italic_font = 'TimesNewRoman-Italic'
    bold_italic_font = 'TimesNewRoman-BoldItalic'

    # Color palette
    PRIMARY_COLOR = colors.HexColor('#163A70')     # Deep Navy
    SECONDARY_COLOR = colors.HexColor('#0284C7')   # Sky Blue
    ACCENT_AMBER = colors.HexColor('#D97706')      # Amber Gold
    TEXT_MAIN = colors.HexColor('#0F172A')         # Slate 900
    TEXT_MUTED = colors.HexColor('#475569')        # Slate 600
    BG_LIGHT = colors.HexColor('#F8FAFC')          # Slate 50
    BG_ROW_ALT = colors.HexColor('#F1F5F9')        # Slate 100
    BORDER_COLOR = colors.HexColor('#CBD5E1')      # Slate 300
    BORDER_DARK = colors.HexColor('#94A3B8')       # Slate 400
    SUCCESS_COLOR = colors.HexColor('#059669')     # Emerald 600

    base_styles = getSampleStyleSheet()

    # Custom typography styles
    style_national_top = ParagraphStyle(
        'NationalTop',
        fontName=bold_font,
        fontSize=9.5,
        leading=13,
        alignment=1, # Center
        textColor=TEXT_MAIN
    )
    style_national_sub = ParagraphStyle(
        'NationalSub',
        fontName=bold_font,
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=PRIMARY_COLOR
    )
    style_school_top = ParagraphStyle(
        'SchoolTop',
        fontName=font_name,
        fontSize=9.5,
        leading=13,
        alignment=1,
        textColor=TEXT_MAIN
    )
    style_school_bold = ParagraphStyle(
        'SchoolBold',
        fontName=bold_font,
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=PRIMARY_COLOR
    )

    style_title = ParagraphStyle(
        'ReportTitle',
        fontName=bold_font,
        fontSize=16,
        leading=22,
        alignment=1,
        textColor=PRIMARY_COLOR,
        spaceAfter=4
    )
    style_subtitle = ParagraphStyle(
        'ReportSubtitle',
        fontName=italic_font,
        fontSize=10.5,
        leading=15,
        alignment=1,
        textColor=TEXT_MUTED,
        spaceAfter=14
    )

    style_h1 = ParagraphStyle(
        'ReportH1',
        fontName=bold_font,
        fontSize=12.5,
        leading=17,
        textColor=PRIMARY_COLOR,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    style_h2 = ParagraphStyle(
        'ReportH2',
        fontName=bold_font,
        fontSize=11,
        leading=15,
        textColor=TEXT_MAIN,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    style_body = ParagraphStyle(
        'ReportBody',
        fontName=font_name,
        fontSize=10,
        leading=14.5,
        textColor=TEXT_MAIN,
        alignment=4, # Justify
        spaceAfter=6
    )
    style_body_bold = ParagraphStyle(
        'ReportBodyBold',
        fontName=bold_font,
        fontSize=10,
        leading=14.5,
        textColor=TEXT_MAIN,
        spaceAfter=4
    )
    style_bullet = ParagraphStyle(
        'ReportBullet',
        fontName=font_name,
        fontSize=9.5,
        leading=14,
        textColor=TEXT_MAIN,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    )

    style_table_header = ParagraphStyle(
        'ReportTh',
        fontName=bold_font,
        fontSize=8.5,
        leading=11.5,
        alignment=1,
        textColor=colors.white
    )
    style_table_cell = ParagraphStyle(
        'ReportTd',
        fontName=font_name,
        fontSize=8.5,
        leading=11.5,
        textColor=TEXT_MAIN
    )
    style_table_cell_center = ParagraphStyle(
        'ReportTdCenter',
        fontName=font_name,
        fontSize=8.5,
        leading=11.5,
        alignment=1,
        textColor=TEXT_MAIN
    )
    style_table_cell_bold = ParagraphStyle(
        'ReportTdBold',
        fontName=bold_font,
        fontSize=8.5,
        leading=11.5,
        textColor=PRIMARY_COLOR
    )

    style_meta_box = ParagraphStyle(
        'MetaBoxText',
        fontName=font_name,
        fontSize=9.5,
        leading=14,
        textColor=TEXT_MAIN
    )

    # Document container width: 595.27 - 72 = 523.27 pt
    content_width = 523.27
    story = []

    # =========================================================================
    # HEADER HÀNH CHÍNH
    # =========================================================================
    header_data = [
        [
            Paragraph("SỞ GIÁO DỤC VÀ ĐÀO TẠO HÀ TĨNH<br/><b>TRƯỜNG THPT HƯƠNG KHÊ</b><br/><i>Số: 108/BC-THPTHK</i>", style_school_top),
            Paragraph("<b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b><br/><b>Độc lập – Tự do – Hạnh phúc</b><br/><i>Hà Tĩnh, ngày 30 tháng 10 năm 2026</i>", style_national_top)
        ]
    ]
    t_header = Table(header_data, colWidths=[250, 273])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_header)

    # Dấu gạch phân cách tiêu ngữ
    hr_table = Table([
        [
            HRFlowable(width="35%", thickness=0.8, color=PRIMARY_COLOR, spaceBefore=3, spaceAfter=14),
            HRFlowable(width="40%", thickness=0.8, color=TEXT_MAIN, spaceBefore=3, spaceAfter=14)
        ]
    ], colWidths=[250, 273])
    hr_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(hr_table)

    # =========================================================================
    # TIÊU ĐỀ BÁO CÁO
    # =========================================================================
    story.append(Paragraph("BÁO CÁO TỔNG THỂ DỰ ÁN", style_title))
    story.append(Paragraph("HỆ THỐNG QUẢN LÝ NỀN NẾP, THI ĐUA VÀ KẾT NỐI HỌC SINH (HK STUDENT HUB)", ParagraphStyle('SubT', fontName=bold_font, fontSize=12, leading=16, alignment=1, textColor=SECONDARY_COLOR)))
    story.append(Paragraph("<i>Mã dự án: THPTHK • Production URL: https://edumentor.io.vn • GitHub: https://github.com/cuonghk1108/THPTHK</i>", style_subtitle))

    # Hộp thông tin tóm tắt tổng quan
    info_box_data = [
        [
            Paragraph("<b>Đơn vị chủ quản:</b> Trường THPT Hương Khê – Hà Tĩnh<br/>"
                      "<b>Mô hình triển khai:</b> Nền tảng Web số hóa học đường (SPA + RESTful API)<br/>"
                      "<b>Đối tượng phục vụ:</b> Ban Giám hiệu, Đoàn trường, GVCN, GVBM, Lớp trưởng, Đội Sao đỏ, Học sinh", style_meta_box),
            Paragraph("<b>Thời gian hoàn thiện:</b> Tháng 10/2026<br/>"
                      "<b>Kiểm thử chất lượng:</b> Đạt 100% test suites (15/15 kịch bản tích hợp)<br/>"
                      "<b>Hạ tầng mạng:</b> Cloudflare Edge Tunnel SSL/TLS bảo mật cao", style_meta_box)
        ]
    ]
    t_info = Table(info_box_data, colWidths=[270, 253])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 10))

    # =========================================================================
    # PHẦN I: GIỚI THIỆU & MỤC TIÊU DỰ ÁN
    # =========================================================================
    story.append(Paragraph("I. GIỚI THIỆU VÀ MỤC TIÊU CỐT LÕI CỦA DỰ ÁN", style_h1))
    story.append(Paragraph(
        "<b>1. Bối cảnh thực tiễn:</b> Trường THPT Hương Khê (Hà Tĩnh) là ngôi trường có quy mô lớn với hơn 64 lớp học trải dài từ Khối 10 đến Khối 12. Phương pháp chấm điểm thi đua truyền thống qua sổ sách tay phát sinh nhiều hạn chế: ghi chép dễ thất lạc, thời gian tổng hợp mất nhiều ngày, nguy cơ sai lệch số liệu và thiếu kênh phản hồi minh bạch, kịp thời giữa nhà trường, phụ huynh và học sinh.",
        style_body
    ))
    story.append(Paragraph(
        "<b>2. Sứ mệnh hệ thống:</b> HK Student Hub được xây dựng với khẩu hiệu hành động <i>“Kỷ cương số – Thi đua minh bạch – Đồng hành giáo dục toàn diện”</i> nhằm giải quyết triệt để các tồn tại trên qua 4 mục tiêu trọng tâm:",
        style_body
    ))
    story.append(Paragraph("• <b>Minh bạch hóa 100% dữ liệu nề nếp:</b> Mọi vi phạm đều phải qua quy trình kiểm duyệt chứng cứ 5 bước, chỉ vi phạm đã được Đoàn trường xác minh mới trừ điểm thi đua.", style_bullet))
    story.append(Paragraph("• <b>Tự động hóa xếp hạng thi đua:</b> Tính toán thời gian thực theo tuần, tháng, học kỳ; bục vinh danh Top 3 và xuất biên bản PDF/Excel chuẩn hành chính giáo dục.", style_bullet))
    story.append(Paragraph("• <b>Trao quyền đại diện cho học sinh:</b> Thiết lập vai trò Lớp trưởng có thẩm quyền thay mặt tập thể lớp khiếu nại, giải trình các lỗi ghi nhận chưa chính xác trực tiếp tới Đoàn trường.", style_bullet))
    story.append(Paragraph("• <b>Đồng hành tâm lý học đường an toàn:</b> Tích hợp phân hệ “Góc sẻ chia” cách ly độc lập, hỗ trợ học sinh tâm sự ẩn danh và cấp mã bí mật bảo vệ học sinh.", style_bullet))

    story.append(Spacer(1, 8))

    # =========================================================================
    # PHẦN II: KIẾN TRÚC CÔNG NGHỆ & BẢO MẬT HẠ TẦNG
    # =========================================================================
    story.append(Paragraph("II. KIẾN TRÚC CÔNG NGHỆ VÀ BẢO MẬT HẠ TẦNG", style_h1))
    story.append(Paragraph(
        "Hệ thống được thiết kế theo kiến trúc hiện đại, phân tầng rõ rệt (Clean Architecture) bảo đảm khả năng chịu tải và tính khả mở cao:",
        style_body
    ))

    tech_matrix_data = [
        [Paragraph("Thành phần", style_table_header), Paragraph("Công nghệ & Thư viện", style_table_header), Paragraph("Đặc tả vai trò kỹ thuật trong dự án", style_table_header)],
        [
            Paragraph("<b>Backend Core</b>", style_table_cell_bold),
            Paragraph("Python 3.12, Django 5.x / 6.x, DRF", style_table_cell),
            Paragraph("Xây dựng RESTful API bảo mật cao, ORM tối ưu truy vấn, xử lý logic thi đua, phân quyền RBAC và quản lý phiên.", style_table_cell)
        ],
        [
            Paragraph("<b>Frontend Client</b>", style_table_cell_bold),
            Paragraph("Responsive SPA, Tailwind CSS, Lucide Icons", style_table_cell),
            Paragraph("Giao diện người dùng đơn trang, tải trang nhanh không giật lag, tối ưu hoàn hảo cho cả máy tính và điện thoại di động.", style_table_cell)
        ],
        [
            Paragraph("<b>Cơ sở dữ liệu</b>", style_table_cell_bold),
            Paragraph("SQLite (Local) / PostgreSQL (Cloud)", style_table_cell),
            Paragraph("Hệ quản trị CSDL quan hệ với 21 migration chuẩn hóa, lập chỉ mục (index) tăng tốc tìm kiếm và khóa ngoại toàn vẹn dữ liệu.", style_table_cell)
        ],
        [
            Paragraph("<b>Xác thực Single Sign-On</b>", style_table_cell_bold),
            Paragraph("Google OAuth 2.0 (SSO)", style_table_cell),
            Paragraph("Đăng nhập 1 chạm an toàn với tài khoản Google, bảo vệ theo chuẩn GitHub Secret Scanning (khóa bảo mật lưu trong .env).", style_table_cell)
        ],
        [
            Paragraph("<b>Động cơ Xuất báo cáo</b>", style_table_cell_bold),
            Paragraph("ReportLab 5.0, OpenPyXL", style_table_cell),
            Paragraph("Xuất báo cáo PDF chuẩn phông Times New Roman hỗ trợ tiếng Việt có dấu; xuất Excel xếp hạng thi đua 64 lớp tự nhiên.", style_table_cell)
        ],
        [
            Paragraph("<b>Hạ tầng Edge & Mạng</b>", style_table_cell_bold),
            Paragraph("Cloudflare Edge Tunnel (cloudflared)", style_table_cell),
            Paragraph("Phát hành dịch vụ trực tiếp ra Internet với domain https://edumentor.io.vn có chứng chỉ SSL/TLS mà không cần mở cổng IP tĩnh.", style_table_cell)
        ],
        [
            Paragraph("<b>Thông báo đa kênh</b>", style_table_cell_bold),
            Paragraph("Gmail SMTP Queue, SpeedSMS API", style_table_cell),
            Paragraph("Gửi email cảnh báo vi phạm tới GVCN qua hàng đợi giao dịch nền (transactional outbox) và gửi SMS cảnh báo phụ huynh khi khẩn cấp.", style_table_cell)
        ]
    ]
    t_tech = Table(tech_matrix_data, colWidths=[100, 150, 273])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_ROW_ALT]),
    ]))
    story.append(t_tech)

    # Sang trang 2 cho Phần III
    story.append(PageBreak())

    # =========================================================================
    # PHẦN III: CÁC PHÂN HỆ NGHIỆP VỤ CỐT LÕI ĐÃ HOÀN THIỆN
    # =========================================================================
    story.append(Paragraph("III. CÁC PHÂN HỆ NGHIỆP VỤ CỐT LÕI ĐÃ HOÀN THIỆN", style_h1))

    # 1. Phân hệ Lớp học & Nhận xét
    story.append(Paragraph("1. Phân hệ Quản lý Lớp học & Sổ tay Nhận xét Học sinh (Teacher Classes)", style_h2))
    story.append(Paragraph(
        "Phân hệ trung tâm kết nối giữa nhà trường và giáo viên với các tính năng chuyên biệt:",
        style_body
    ))
    story.append(Paragraph("• <b>Quản lý 64 lớp học toàn trường:</b> Bộ lọc theo khối thông minh (Khối 10, Khối 11, Khối 12) cùng danh sách lớp được sắp xếp tự nhiên theo chữ cái và thứ tự chuẩn (10A1 - 10A22, 11A1 - 11A21, 12A1 - 12A22).", style_bullet))
    story.append(Paragraph("• <b>Phân công chủ nhiệm & giảng dạy:</b> Admin và Đoàn trường có thể phân công Giáo viên chủ nhiệm (GVCN) và Giáo viên bộ môn (GVBM) trực tiếp trên giao diện.", style_bullet))
    story.append(Paragraph("• <b>Nhận xét đích danh học sinh:</b> Giáo viên bộ môn khi vào lớp có thể click nhận xét trực tiếp từng em học sinh theo tiết dạy hoặc kỳ học, tạo sợi dây liên lạc mật thiết và liên tục với phụ huynh.", style_bullet))

    # 2. Phân hệ Lớp trưởng & Khiếu nại
    story.append(Paragraph("2. Phân hệ Bổ nhiệm Lớp trưởng & Quy trình Khiếu nại Vi phạm Lớp", style_h2))
    story.append(Paragraph(
        "Nâng cao quyền tự chủ và tinh thần trách nhiệm của học sinh với cơ chế phân quyền đột phá:",
        style_body
    ))
    story.append(Paragraph("• <b>Thẩm quyền bổ nhiệm nghiêm ngặt:</b> Chỉ Admin, Đoàn trường, hoặc GVCN của chính lớp đó mới có quyền phân công hoặc hủy bỏ Lớp trưởng (chặn 403 đối với GVBM hoặc học sinh khác).", style_bullet))
    story.append(Paragraph("• <b>Huy hiệu ⭐ Lớp trưởng:</b> Tự động hiển thị nổi bật trên cả bảng danh sách học sinh và thẻ thông tin lớp học, mang lại niềm tự hào và trọng trách cho cán bộ lớp.", style_bullet))
    story.append(Paragraph("• <b>Nhiệm vụ khiếu nại lỗi sai của lớp:</b> Lớp trưởng được hệ thống cấp quyền truy cập mục Nền nếp (`conduct`) để giám sát toàn bộ các bản ghi vi phạm của lớp mình. Khi phát hiện lỗi bị ghi nhận nhầm lẫn hoặc chưa khách quan, Lớp trưởng có quyền nhấn <b>Khiếu nại</b> gửi giải trình trực tiếp về Đoàn trường để xác minh lại.", style_bullet))

    # 3. Quản lý Nền nếp & Vi phạm
    story.append(Paragraph("3. Quản lý Nền nếp Học sinh & Quy trình Thẩm định 5 Bước", style_h2))
    story.append(Paragraph(
        "Quy trình xử lý vi phạm kỷ luật được chuẩn hóa khép kín nhằm bảo đảm sự công bằng tuyệt đối:",
        style_body
    ))

    conduct_steps = [
        [Paragraph("Trạng thái", style_table_header), Paragraph("Ý nghĩa nghiệp vụ", style_table_header), Paragraph("Tác động điểm thi đua", style_table_header)],
        [
            Paragraph("<b>PENDING</b>", style_table_cell_center),
            Paragraph("Bản ghi do Đội Sao đỏ / Người trực ghi nhận, đang chờ xác minh.", style_table_cell),
            Paragraph("<b>Chưa trừ điểm</b> (Giữ nguyên 100đ)", style_table_cell)
        ],
        [
            Paragraph("<b>VERIFIED</b>", style_table_cell_center),
            Paragraph("Đoàn trường thẩm định minh chứng và phê duyệt vi phạm.", style_table_cell),
            Paragraph("<font color='#DC2626'><b>Trừ điểm</b></font> theo khung quy chế", style_table_cell)
        ],
        [
            Paragraph("<b>APPEALING</b>", style_table_cell_center),
            Paragraph("Lớp trưởng, Học sinh hoặc GVCN gửi văn bản giải trình / khiếu nại.", style_table_cell),
            Paragraph("Tạm dừng, chuyển Đoàn trường xem xét", style_table_cell)
        ],
        [
            Paragraph("<b>ADJUSTED</b>", style_table_cell_center),
            Paragraph("Đoàn trường chấp thuận khiếu nại, điều chỉnh hoặc hoàn tác biên bản.", style_table_cell),
            Paragraph("<font color='#059669'><b>Phục hồi điểm</b></font> thi đua của Chi đoàn", style_table_cell)
        ],
        [
            Paragraph("<b>DISMISSED</b>", style_table_cell_center),
            Paragraph("Bác bỏ bản ghi do không đủ căn cứ minh chứng xác thực.", style_table_cell),
            Paragraph("Không trừ điểm, lưu trữ kiểm toán", style_table_cell)
        ]
    ]
    t_conduct = Table(conduct_steps, colWidths=[90, 260, 173])
    t_conduct.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_ROW_ALT]),
    ]))
    story.append(t_conduct)
    story.append(Spacer(1, 6))

    # 4. Thi đua Chi đoàn Tự động
    story.append(Paragraph("4. Thi đua Chi đoàn Tự động & Xuất Báo cáo Chuẩn hóa", style_h2))
    story.append(Paragraph(
        "• <b>Công thức tính điểm:</b> <code>Điểm Chi đoàn = 100 + Điểm cộng phong trào − Điểm trừ vi phạm (đã duyệt)</code>.<br/>"
        "• <b>Bảng xếp hạng trực quan:</b> Vinh danh Top 3 trên bục Podium, phân loại hạng A, B, C, D tự động theo mức điểm đạt được.<br/>"
        "• <b>Chốt sổ thi đua & Xuất báo cáo:</b> Sau khi kỳ thi đua kết thúc, Đoàn trường bấm chốt sổ để khóa bảng điểm; xuất file Excel và PDF có đầy đủ quốc hiệu, tiêu ngữ, chữ ký BGH và Đoàn trường.",
        style_body
    ))

    # 5. Góc sẻ chia & An toàn học đường
    story.append(Paragraph("5. Phân hệ Góc sẻ chia – Tư vấn Tâm lý Học đường & Bảo vệ Trẻ em", style_h2))
    story.append(Paragraph(
        "• <b>Cách ly dữ liệu tuyệt đối:</b> Phân hệ tư vấn tâm lý được bảo vệ độc lập, chỉ tài khoản chuyên viên tư vấn tâm lý mới có quyền truy cập (chặn hoàn toàn BGH, Đoàn trường, GVCN và các học sinh khác).<br/>"
        "• <b>Mã tra cứu bí mật:</b> Học sinh có thể gửi tâm sự ẩn danh và nhận mã bí mật dạng <code>GSC-2026-XXXX</code> để tra cứu câu trả lời của chuyên gia mà không sợ bị lộ danh tính.<br/>"
        "• <b>Hỗ trợ khẩn cấp:</b> Tích hợp nút gọi khẩn cấp Tổng đài Quốc gia Bảo vệ Trẻ em <b>111</b> và quy trình phản ứng nhanh khi có nguy cơ bạo lực học đường hoặc tự hại.",
        style_body
    ))

    # Sang trang 3 cho Phần IV & V
    story.append(PageBreak())

    # =========================================================================
    # PHẦN IV: MA TRẬN PHÂN QUYỀN TRUY CẬP (RBAC MATRIX)
    # =========================================================================
    story.append(Paragraph("IV. MA TRẬN PHÂN QUYỀN TRUY CẬP HỆ THỐNG (RBAC)", style_h1))
    story.append(Paragraph(
        "Hệ thống phân định rạch ròi 8 nhóm vai trò người dùng nhằm bảo đảm tính bảo mật, riêng tư và trách nhiệm giải trình:",
        style_body
    ))

    rbac_table_data = [
        [
            Paragraph("Quyền hạn / Chức năng", style_table_header),
            Paragraph("Admin", style_table_header),
            Paragraph("Đoàn trường", style_table_header),
            Paragraph("BGH", style_table_header),
            Paragraph("GVCN", style_table_header),
            Paragraph("GVBM", style_table_header),
            Paragraph("Lớp trưởng", style_table_header),
            Paragraph("Học sinh", style_table_header),
            Paragraph("Tâm lý", style_table_header),
        ],
        [
            Paragraph("Quản trị người dùng & Phê duyệt", style_table_cell),
            Paragraph("Toàn quyền", style_table_cell_center),
            Paragraph("Duyệt HS", style_table_cell_center),
            Paragraph("Xem", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
        ],
        [
            Paragraph("Phân công Lớp trưởng", style_table_cell),
            Paragraph("✓", style_table_cell_center),
            Paragraph("✓", style_table_cell_center),
            Paragraph("✓", style_table_cell_center),
            Paragraph("Lớp mình", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
        ],
        [
            Paragraph("Phân công GVCN & GVBM", style_table_cell),
            Paragraph("✓", style_table_cell_center),
            Paragraph("✓", style_table_cell_center),
            Paragraph("✓", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
        ],
        [
            Paragraph("Nhận xét đích danh học sinh", style_table_cell),
            Paragraph("✓", style_table_cell_center),
            Paragraph("✓", style_table_cell_center),
            Paragraph("✓", style_table_cell_center),
            Paragraph("✓", style_table_cell_center),
            Paragraph("✓", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
        ],
        [
            Paragraph("Xem danh sách & Hồ sơ lớp", style_table_cell),
            Paragraph("Toàn trường", style_table_cell_center),
            Paragraph("Toàn trường", style_table_cell_center),
            Paragraph("Toàn trường", style_table_cell_center),
            Paragraph("Lớp mình", style_table_cell_center),
            Paragraph("Lớp dạy", style_table_cell_center),
            Paragraph("Lớp mình", style_table_cell_center),
            Paragraph("Lớp mình", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
        ],
        [
            Paragraph("Xác minh vi phạm & Phê duyệt điểm", style_table_cell),
            Paragraph("✓", style_table_cell_center),
            Paragraph("✓", style_table_cell_center),
            Paragraph("Xem", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
        ],
        [
            Paragraph("Gửi khiếu nại / Giải trình lỗi", style_table_cell),
            Paragraph("✓", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("Lớp mình", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("Lớp mình", style_table_cell_center),
            Paragraph("Lỗi mình", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
        ],
        [
            Paragraph("Theo dõi & Chốt thi đua Chi đoàn", style_table_cell),
            Paragraph("✓", style_table_cell_center),
            Paragraph("✓", style_table_cell_center),
            Paragraph("Phê duyệt", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
        ],
        [
            Paragraph("Tư vấn tâm lý 'Góc sẻ chia'", style_table_cell),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("—", style_table_cell_center),
            Paragraph("Gửi ẩn danh", style_table_cell_center),
            Paragraph("Toàn quyền", style_table_cell_center),
        ],
    ]
    t_rbac = Table(rbac_table_data, colWidths=[155, 46, 50, 42, 45, 45, 50, 48, 42])
    t_rbac.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_ROW_ALT]),
    ]))
    story.append(t_rbac)
    story.append(Spacer(1, 10))

    # =========================================================================
    # PHẦN V: KẾT QUẢ KIỂM THỬ CHẤT LƯỢNG & AN NINH HỆ THỐNG
    # =========================================================================
    story.append(Paragraph("V. KẾT QUẢ KIỂM THỬ CHẤT LƯỢNG & AN NINH HỆ THỐNG", style_h1))
    story.append(Paragraph(
        "Hệ thống đã trải qua kiểm thử hộp trắng (White-box Testing) và kiểm thử chức năng tự động 100% đạt yêu cầu kỹ thuật nghiêm ngặt:",
        style_body
    ))

    test_results_data = [
        [Paragraph("Bộ kịch bản kiểm thử (Test Suite)", style_table_header), Paragraph("Số test", style_table_header), Paragraph("Kết quả", style_table_header), Paragraph("Mục tiêu nghiệm thu kỹ thuật", style_table_header)],
        [
            Paragraph("<code>test_lop_truong_workflow.py</code>", style_table_cell_bold),
            Paragraph("6 / 6", style_table_cell_center),
            Paragraph("<font color='#059669'><b>100% PASS</b></font>", style_table_cell_center),
            Paragraph("Chặn 403 người không có thẩm quyền phân công; GVCN, Đoàn trường, Admin phân công thành công; Lớp trưởng xem và khiếu nại lỗi toàn lớp; học sinh thường bị chặn.", style_table_cell)
        ],
        [
            Paragraph("<code>test_student_role_scope.py</code>", style_table_cell_bold),
            Paragraph("9 / 9", style_table_cell_center),
            Paragraph("<font color='#059669'><b>100% PASS</b></font>", style_table_cell_center),
            Paragraph("Bảo vệ phạm vi dữ liệu: học sinh chỉ xem lớp của mình và vi phạm cá nhân; chặn truy cập điểm thi đua chi đoàn, danh sách lớp khác và hồ sơ tư vấn tâm lý.", style_table_cell)
        ],
        [
            Paragraph("<b>Kiểm toán An ninh OWASP Top 10</b>", style_table_cell_bold),
            Paragraph("Toàn diện", style_table_cell_center),
            Paragraph("<font color='#059669'><b>AN TOÀN</b></font>", style_table_cell_center),
            Paragraph("Chống SQLi qua ORM chuẩn, ngăn chặn XSS, IDOR; toàn bộ Secret Keys và OAuth Credentials được đưa vào biến môi trường an toàn.", style_table_cell)
        ],
        [
            Paragraph("<b>Đồng bộ & Đẩy mã nguồn GitHub</b>", style_table_cell_bold),
            Paragraph("Branch main", style_table_cell_center),
            Paragraph("<font color='#059669'><b>THÀNH CÔNG</b></font>", style_table_cell_center),
            Paragraph("Đã vượt qua kiểm tra GitHub Push Protection, mã nguồn được đẩy nguyên vẹn lên kho https://github.com/cuonghk1108/THPTHK.", style_table_cell)
        ]
    ]
    t_test = Table(test_results_data, colWidths=[150, 45, 75, 253])
    t_test.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_ROW_ALT]),
    ]))
    story.append(t_test)
    story.append(Spacer(1, 10))

    # =========================================================================
    # PHẦN VI: KẾT LUẬN & ĐỀ XUẤT VẬN HÀNH
    # =========================================================================
    story.append(Paragraph("VI. KẾT LUẬN VÀ KIẾN NGHỊ VẬN HÀNH", style_h1))
    story.append(Paragraph(
        "<b>1. Kết luận:</b> Dự án <b>HK Student Hub</b> đã hoàn thành 100% các mục tiêu đặt ra, sẵn sàng vận hành chính thức phục vụ năm học 2026 - 2027 tại Trường THPT Hương Khê. Nền tảng đem lại bước tiến vượt bậc trong chuyển đổi số học đường: từ công tác chấm thi đua minh bạch, khách quan đến trao quyền tự quản cho học sinh qua vai trò Lớp trưởng, đồng thời bảo vệ sức khỏe tâm thần học sinh qua Góc sẻ chia.",
        style_body
    ))
    story.append(Paragraph(
        "<b>2. Kiến nghị vận hành:</b><br/>"
        "• Tổ chức tập huấn ngắn hạn cho Ban Chấp hành Đoàn trường và Đội Sao đỏ về quy trình ghi nhận vi phạm trên thiết bị di động.<br/>"
        "• Phổ biến rộng rãi đến 64 Chi đoàn về quy chế giải trình / khiếu nại của Lớp trưởng để phát huy tính dân chủ trong học đường.<br/>"
        "• Duy trì máy chủ và kết nối Cloudflare Tunnel ổn định để bảo đảm thông suốt dịch vụ.",
        style_body
    ))
    story.append(Spacer(1, 14))

    # Chữ ký phê duyệt hành chính
    sig_data = [
        [
            Paragraph("<b>ĐẠI DIỆN ĐOÀN TRƯỜNG</b><br/><i>(Ký và ghi rõ họ tên)</i><br/><br/><br/><br/><b>Bí thư Đoàn trường</b>", ParagraphStyle('Sig1', fontName=font_name, fontSize=9.5, leading=13, alignment=1)),
            Paragraph("<b>NGƯỜI LẬP BÁO CÁO</b><br/><i>(Ký và ghi rõ họ tên)</i><br/><br/><br/><br/><b>Kỹ sư Trưởng dự án</b><br/><i>cuongdev1108</i>", ParagraphStyle('Sig2', fontName=font_name, fontSize=9.5, leading=13, alignment=1)),
            Paragraph("<b>HIỆU TRƯỞNG PHÊ DUYỆT</b><br/><i>(Ký tên và đóng dấu)</i><br/><br/><br/><br/><b>Trường THPT Hương Khê</b>", ParagraphStyle('Sig3', fontName=font_name, fontSize=9.5, leading=13, alignment=1))
        ]
    ]
    t_sig = Table(sig_data, colWidths=[174, 174, 175])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(KeepTogether(t_sig))

    # Tạo tệp PDF tại đường dẫn đầu tiên và sao chép sang các đường dẫn khác
    first_path = output_paths[0]
    os.makedirs(os.path.dirname(first_path), exist_ok=True)
    doc = SimpleDocTemplate(
        first_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=40,
        bottomMargin=40
    )
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Đã xuất thành công tệp PDF: {first_path} ({os.path.getsize(first_path):,} bytes)")

    import shutil
    for other_path in output_paths[1:]:
        os.makedirs(os.path.dirname(other_path), exist_ok=True)
        shutil.copy2(first_path, other_path)
        print(f"Đã sao chép tệp PDF sang: {other_path} ({os.path.getsize(other_path):,} bytes)")

if __name__ == '__main__':
    project_pdf = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\BAO_CAO_HE_THONG_HK_STUDENT_HUB.pdf'
    artifact_pdf = r'C:\Users\Xuan Cuong\.gemini\antigravity\brain\5a5dcb7f-ba1d-4f8d-8a94-94f428cd0bbe\BAO_CAO_HE_THONG_HK_STUDENT_HUB.pdf'
    scratch_pdf = r'C:\Users\Xuan Cuong\.gemini\antigravity\scratch\hk-student-hub\BAO_CAO_HE_THONG_HK_STUDENT_HUB.pdf'
    build_system_report_pdf([project_pdf, artifact_pdf, scratch_pdf])
