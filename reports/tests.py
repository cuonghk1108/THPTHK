# -*- coding: utf-8 -*-
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import User, AcademicYear, Semester
from conduct.models import SchoolClass, Student, ConductRuleCategory, ConductRule, ViolationRecord
from competition.models import CompetitionPeriod, ClassCompetitionScore
from reports.models import ReportExportHistory
from reports.pdf_utils import setup_times_new_roman_fonts, find_font_file
from reports.services import (
    export_competition_pdf,
    export_violations_pdf,
    export_violation_detail_pdf,
)

User = get_user_model()


class PdfExportTimesNewRomanTests(TestCase):
    """
    Bộ kiểm thử chuẩn hóa xuất báo cáo PDF sử dụng font Times New Roman
    đảm bảo hỗ trợ tiếng Việt đầy đủ và đúng quy chuẩn hành chính.
    """

    def setUp(self):
        self.client = APIClient()

        # Create academic year & semester
        self.year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=date(2026, 9, 5),
            end_date=date(2027, 5, 30),
            is_current=True
        )
        self.semester = Semester.objects.create(
            academic_year=self.year,
            semester_number=1,
            name='Học kỳ I',
            start_date=date(2026, 9, 5),
            end_date=date(2027, 1, 15),
            is_current=True
        )

        # Create admin user
        self.admin = User.objects.create_user(
            username='admin_test',
            email='admin@thpthuongkhe.edu.vn',
            full_name='Thầy Nguyễn Văn Hiệu',
            role=User.ROLE_ADMIN,
            account_status=User.STATUS_APPROVED
        )
        self.admin.set_password('AdminPass123@')
        self.admin.save()

        # Create class
        self.school_class = SchoolClass.objects.create(
            name='12A1',
            grade=12,
            academic_year=self.year,
            room_number='P201'
        )

        # Create student user and student profile
        self.student_user = User.objects.create_user(
            username='hs_nguyenvana',
            email='nguyenvana@gmail.com',
            full_name='Nguyễn Văn An',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED
        )
        self.student = Student.objects.create(
            user=self.student_user,
            student_code='HK26-001',
            full_name='Nguyễn Văn An',
            date_of_birth=date(2010, 1, 1),
            school_class=self.school_class
        )

        # Create conduct rule
        self.category = ConductRuleCategory.objects.create(
            name='Nền nếp & Kỷ luật',
            description='Các quy định về trật tự, trang phục'
        )
        self.rule = ConductRule.objects.create(
            category=self.category,
            code='VP-01',
            name='Đi học muộn không phép',
            description='Học sinh đến trường sau hiệu lệnh trống vào lớp 15 phút',
            default_points_deducted=Decimal('2.00')
        )

        # Create violation record
        self.violation = ViolationRecord.objects.create(
            record_code='VP-2026-10-001',
            school_class=self.school_class,
            student=self.student,
            student_name_snapshot='Nguyễn Văn An',
            rule=self.rule,
            points_deducted=Decimal('2.00'),
            reporter=self.admin,
            status=ViolationRecord.STATUS_VERIFIED,
            occurred_at=timezone.now(),
            description='Đi trễ 15 phút tiết 1 buổi sáng có minh chứng ghi nhận tại cổng trường',
            location='Cổng chính Trường THPT Hương Khê'
        )

        # Create competition period & scores
        today = timezone.now().date()
        self.period = CompetitionPeriod.objects.create(
            name='Thi đua Tuần 10 - Tháng 10/2026',
            period_type=CompetitionPeriod.TYPE_WEEK,
            academic_year=self.year,
            semester=self.semester,
            week_number=10,
            start_date=today - timedelta(days=3),
            end_date=today + timedelta(days=3),
            is_locked=False
        )
        self.score = ClassCompetitionScore.objects.create(
            competition_period=self.period,
            school_class=self.school_class,
            base_points=Decimal('100.00'),
            bonus_points=Decimal('5.00'),
            penalty_points=Decimal('2.00'),
            total_score=Decimal('103.00'),
            rank=1,
            rank_change=0,
            verified_violations_count=1
        )

    def test_01_times_new_roman_fonts_available_and_registered(self):
        """Kiểm tra tệp font Times New Roman có sẵn và hàm đăng ký không lỗi"""
        regular_path = find_font_file('times.ttf')
        self.assertIsNotNone(regular_path, "Font times.ttf phải tồn tại trong static/fonts/ hoặc thư mục hệ thống")
        # Gọi đăng ký font
        result = setup_times_new_roman_fonts()
        self.assertTrue(result, "Hàm setup_times_new_roman_fonts phải trả về True")

    def test_02_export_competition_pdf_service(self):
        """Kiểm tra dịch vụ sinh PDF bảng xếp hạng thi đua tuần/kỳ"""
        pdf_bytes = export_competition_pdf(self.period.id, self.admin)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'), "File trả về phải có header chuẩn PDF")
        self.assertGreater(len(pdf_bytes), 5000, "File PDF thi đua phải có dung lượng đầy đủ")

        # Kiểm tra ghi nhận lịch sử xuất
        history = ReportExportHistory.objects.filter(
            report_type=ReportExportHistory.REPORT_COMPETITION,
            file_format=ReportExportHistory.FORMAT_PDF
        ).first()
        self.assertIsNotNone(history)

    def test_03_export_violations_pdf_service(self):
        """Kiểm tra dịch vụ sinh PDF danh sách vi phạm nền nếp"""
        # Không có bộ lọc
        pdf_bytes = export_violations_pdf(filters=None, exported_by=self.admin)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))
        self.assertGreater(len(pdf_bytes), 5000)

        # Có bộ lọc lớp
        filters = {'class_id': self.school_class.id, 'status': ViolationRecord.STATUS_VERIFIED}
        filtered_pdf_bytes = export_violations_pdf(filters=filters, exported_by=self.admin)
        self.assertIsInstance(filtered_pdf_bytes, bytes)
        self.assertTrue(filtered_pdf_bytes.startswith(b'%PDF-'))

    def test_04_export_violation_detail_pdf_service(self):
        """Kiểm tra dịch vụ sinh PDF biên bản vi phạm và minh chứng trừ điểm chính thức"""
        pdf_bytes = export_violation_detail_pdf(self.violation.id, self.admin)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))
        self.assertGreater(len(pdf_bytes), 5000)

        # Kiểm tra ghi nhận lịch sử xuất
        history = ReportExportHistory.objects.filter(
            report_type=ReportExportHistory.REPORT_VIOLATIONS,
            file_format=ReportExportHistory.FORMAT_PDF,
            title__contains=self.violation.record_code
        ).first()
        self.assertIsNotNone(history)

    def test_05_api_export_competition_pdf(self):
        """Kiểm tra endpoint API xuất PDF bảng xếp hạng thi đua"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f'/api/reports/competition/pdf/{self.period.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename=', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF-'))

    def test_06_api_export_violations_pdf(self):
        """Kiểm tra endpoint API xuất PDF danh sách vi phạm nền nếp"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f'/api/reports/violations/pdf/?class_id={self.school_class.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename=', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF-'))

    def test_07_api_export_violation_detail_pdf(self):
        """Kiểm tra endpoint API xuất PDF biên bản vi phạm chi tiết"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f'/api/reports/violations/{self.violation.id}/pdf/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename=', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF-'))

    def test_08_api_requires_authentication(self):
        """Kiểm tra các endpoint xuất PDF yêu cầu đăng nhập"""
        self.client.logout()
        res1 = self.client.get(f'/api/reports/competition/pdf/{self.period.id}/')
        self.assertIn(res1.status_code, [401, 403])

        res2 = self.client.get('/api/reports/violations/pdf/')
        self.assertIn(res2.status_code, [401, 403])

        res3 = self.client.get(f'/api/reports/violations/{self.violation.id}/pdf/')
        self.assertIn(res3.status_code, [401, 403])
