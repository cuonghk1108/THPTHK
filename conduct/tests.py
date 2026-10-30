import uuid
from datetime import timedelta
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.utils import timezone

from core.models import User, AcademicYear, Semester
from conduct.models import (
    SchoolClass, Student, ConductRuleCategory, ConductRule, ViolationRecord,
    SmsNotification, SmsAttempt, SmsConfiguration,
)
from conduct.services import create_violation_record, can_user_deduct_directly


from competition.models import CompetitionPeriod

class ConductAndSmsRemovalTests(TestCase):
    """
    Kiểm thử chức năng ghi nhận vi phạm, trừ điểm thi đua trực tiếp,
    và xác nhận việc loại bỏ hoàn toàn các endpoint và dịch vụ SMS.
    """
    def setUp(self):
        self.client = Client()
        self.year = AcademicYear.objects.create(name='2026-2027', start_date='2026-09-05', end_date='2027-05-30', is_current=True)
        self.semester = Semester.objects.create(academic_year=self.year, semester_number=1, name='Học kỳ I', start_date='2026-09-05', end_date='2027-01-15', is_current=True)
        self.period = CompetitionPeriod.objects.create(
            academic_year=self.year,
            name='Kỳ thi đua tháng 10',
            period_type='MONTH',
            start_date='2026-10-01',
            end_date='2026-10-31',
            is_locked=False
        )
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        CompetitionPeriod.objects.create(
            academic_year=self.year,
            semester=self.semester,
            name='Tuần kiểm thử hiện tại',
            period_type=CompetitionPeriod.TYPE_WEEK,
            week_number=7,
            internal_month_number=2,
            start_date=week_start,
            end_date=week_start + timedelta(days=6),
            is_locked=False,
        )
        self.school_class = SchoolClass.objects.create(name='10A1', grade=10, academic_year=self.year)

        self.student = Student.objects.create(
            student_code='HK261001',
            full_name='Trần Minh Quân',
            date_of_birth='2010-01-01',
            school_class=self.school_class
        )

        self.category = ConductRuleCategory.objects.create(name='Nền nếp & Tác phong')
        self.rule = ConductRule.objects.create(
            category=self.category,
            code='VP01',
            name='Không mặc đồng phục',
            default_points_deducted=Decimal('2.00')
        )

        # Admin
        self.admin = User.objects.create_user(
            username='admin.hk',
            email='admin@thpthuongkhe.edu.vn',
            password='AdminPassword123!',
            role=User.ROLE_ADMIN,
            account_status=User.STATUS_APPROVED
        )

        # Đoàn trường (chỉ duyệt tài khoản và quản lý phân công Sao đỏ)
        self.doan_truong = User.objects.create_user(
            username='doan.truong',
            email='doantruong@thpthuongkhe.edu.vn',
            password='DoanPassword123!',
            role=User.ROLE_DOAN_TRUONG,
            can_verify_violations=True,  # Legacy flags must not grant discipline access.
            account_status=User.STATUS_APPROVED
        )

        # Sao đỏ (chỉ có quyền báo cáo chờ duyệt)
        self.sao_do = User.objects.create_user(
            username='saodo.10a1',
            email='saodo@thpthuongkhe.edu.vn',
            password='SaodoPassword123!',
            role=User.ROLE_SAO_DO,
            account_status=User.STATUS_APPROVED
        )

        # Học sinh thường (bị chặn báo cáo vi phạm)
        self.hoc_sinh = User.objects.create_user(
            username='hocsinh.10a1',
            email='hocsinh@thpthuongkhe.edu.vn',
            password='HocSinhPassword123!',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED
        )

    def test_doan_truong_can_record_and_student_cannot(self):
        """Đoàn trường có thẩm quyền xử lý nền nếp, trong khi học sinh thường bị từ chối."""
        self.assertTrue(can_user_deduct_directly(self.doan_truong))
        student_user = User.objects.create_user(
            username='student.test',
            email='student.test@thpthuongkhe.edu.vn',
            password='StudentPassword123!',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED
        )
        self.assertFalse(can_user_deduct_directly(student_user))
        with self.assertRaises(PermissionError):
            create_violation_record(
                class_id=self.school_class.id,
                student_id=self.student.id,
                rule_id=self.rule.id,
                reporter=student_user,
                direct_deduct=True,
                description='Học sinh không được tự ghi nhận trừ điểm'
            )
        self.client.force_login(student_user)
        response = self.client.post('/api/conduct/violations/', {
            'school_class': self.school_class.id,
            'student': self.student.id,
            'rule': self.rule.id,
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ViolationRecord.objects.count(), 0)

    def test_sao_do_creates_pending_violation(self):
        """Sao đỏ ghi nhận vi phạm thì trạng thái phải là PENDING chờ xác minh, không được trừ điểm ngay."""
        self.assertFalse(can_user_deduct_directly(self.sao_do))

        violation = create_violation_record(
            class_id=self.school_class.id,
            student_id=self.student.id,
            rule_id=self.rule.id,
            reporter=self.sao_do,
            direct_deduct=False,
            description='Sao đỏ ghi nhận vi phạm cổng trường'
        )

        self.assertEqual(violation.status, ViolationRecord.STATUS_PENDING)
        self.assertIsNone(violation.verified_by)
        self.assertIsNone(violation.score_after)

    def test_direct_report_without_unique_open_week_is_saved_pending(self):
        occurred_at = timezone.make_aware(timezone.datetime(2026, 9, 6, 8, 0))
        violation = create_violation_record(
            reporter=self.admin,
            class_id=self.school_class.id,
            student_id=self.student.id,
            rule_id=self.rule.id,
            occurred_at=occurred_at,
            direct_deduct=True,
        )

        self.assertEqual(violation.status, ViolationRecord.STATUS_PENDING)
        self.assertEqual(violation.points_deducted, Decimal('0.00'))
        self.assertIn('chưa khớp duy nhất', violation.verification_notes)

    def test_student_forbidden_from_creating_violation(self):
        """Học sinh thông thường không được phép gửi báo cáo vi phạm (403 Forbidden)."""
        self.client.force_login(self.hoc_sinh)
        res = self.client.post('/api/conduct/violations/', {
            'school_class': self.school_class.id,
            'student': self.student.id,
            'rule': self.rule.id,
            'description': 'Học sinh tự báo cáo',
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn('Học sinh không có quyền', res.json()['error'])

    def test_violation_with_evidence_image_and_notes(self):
        """Bản ghi vi phạm có thể đính kèm minh chứng ảnh và ghi chú bảo mật."""
        fake_image = SimpleUploadedFile(
            name='evidence.jpg',
            content=b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb',
            content_type='image/jpeg'
        )

        violation = create_violation_record(
            class_id=self.school_class.id,
            student_id=self.student.id,
            rule_id=self.rule.id,
            reporter=self.admin,
            direct_deduct=True,
            description='Vi phạm có kèm minh chứng ảnh',
            evidence_image=fake_image,
            evidence_notes='Ảnh chụp cổng trường lúc 07:15'
        )

        self.assertTrue(bool(violation.evidence_image))
        self.assertEqual(violation.evidence_notes, 'Ảnh chụp cổng trường lúc 07:15')

    def test_all_sms_endpoints_return_404_not_found(self):
        """Xác nhận tất cả các API route của SMS đã bị xóa hoàn toàn và trả về 404."""
        self.client.force_login(self.admin)

        sms_endpoints = [
            ('/api/conduct/sms/config/', 'get'),
            ('/api/conduct/sms/config/', 'patch'),
            ('/api/conduct/sms/history/', 'get'),
            ('/api/conduct/sms/test/', 'post'),
            ('/api/conduct/sms/account/', 'get'),
            ('/api/conduct/sms/1/retry/', 'post'),
            ('/api/conduct/sms/1/status/', 'post'),
            ('/api/conduct/sms/twilio-status/', 'post'),
            ('/api/webhooks/speedsms/delivery-report/dummysecret123456789012345678901234567890/', 'post'),
        ]

        for url, method in sms_endpoints:
            with self.subTest(url=url, method=method):
                if method == 'get':
                    res = self.client.get(url)
                elif method == 'post':
                    res = self.client.post(url)
                elif method == 'patch':
                    res = self.client.patch(url)
                self.assertEqual(res.status_code, 404, f"Endpoint {url} ({method}) phải trả về 404.")

    def test_historical_sms_data_preserved_safely(self):
        """Bảng dữ liệu lịch sử SMS vẫn được bảo toàn an toàn trong cơ sở dữ liệu."""
        config = SmsConfiguration.objects.create(
            pk=999,
            is_enabled=False,
            recipient_phone='+84901234567'
        )
        self.assertEqual(config.recipient_phone, '+84901234567')

        notification = SmsNotification.objects.create(
            recipient_phone='+84901234567',
            message_content='Thông báo lịch sử',
            status=SmsNotification.STATUS_SENT
        )
        self.assertEqual(notification.status, 'SENT')

        attempt = SmsAttempt.objects.create(
            notification=notification,
            attempt_number=1,
            status=SmsAttempt.STATUS_SENT
        )
        self.assertEqual(attempt.attempt_number, 1)

        self.hoc_sinh.phone_number = '0987654321'
        self.hoc_sinh.save()
        self.hoc_sinh.refresh_from_db()
        self.assertEqual(self.hoc_sinh.phone_number, '0987654321')

    def test_record_violation_with_real_time_success(self):
        """Ghi nhận vi phạm với thời gian thực thành công"""
        self.client.force_login(self.admin)
        now = timezone.localtime(timezone.now())
        res = self.client.post('/api/conduct/violations/', {
            'school_class': self.school_class.id,
            'student': self.student.id,
            'rule': self.rule.id,
            'location': 'Cổng trường',
            'description': 'Kiểm tra ghi nhận thời gian thực',
            'occurred_at': now.strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn('occurred_at', data)
        self.assertEqual(data['status'], 'VERIFIED')

    def test_record_violation_future_time_rejected(self):
        """Từ chối ghi nhận vi phạm nếu thời gian ở tương lai"""
        from datetime import timedelta
        self.client.force_login(self.admin)
        future_time = timezone.localtime(timezone.now()) + timedelta(minutes=20)
        res = self.client.post('/api/conduct/violations/', {
            'school_class': self.school_class.id,
            'student': self.student.id,
            'rule': self.rule.id,
            'location': 'Cổng trường',
            'description': 'Vi phạm tương lai giả định',
            'occurred_at': future_time.strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('Thời gian xảy ra vi phạm không thể ở tương lai', res.json().get('error', ''))

    def test_service_rejects_future_occurred_at(self):
        """Hàm dịch vụ create_violation_record từ chối thời gian tương lai bằng ValueError"""
        from datetime import timedelta
        future_time = timezone.now() + timedelta(minutes=15)
        with self.assertRaises(ValueError) as ctx:
            create_violation_record(
                reporter=self.admin,
                class_id=self.school_class.id,
                rule_id=self.rule.id,
                student_id=self.student.id,
                occurred_at=future_time,
            )
        self.assertIn('không thể ở tương lai', str(ctx.exception))
