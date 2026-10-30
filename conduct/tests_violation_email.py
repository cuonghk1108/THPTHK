import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, Client, override_settings
from django.core import mail
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import User, AcademicYear, Semester, AuditLog, Notification
from conduct.models import (
    SchoolClass, Student, ConductRuleCategory, ConductRule, ViolationRecord,
    ViolationEmailNotification,
)
from conduct.email import (
    get_eligible_union_recipients, send_violation_email, queue_violation_email,
)
from conduct.services import create_violation_record


@override_settings(
    DEFAULT_FROM_EMAIL='HK Student Hub <hkstudenthub@gmail.com>',
    FRONTEND_BASE_URL='http://127.0.0.1:8000',
    IS_TESTING=True,
)
class ViolationEmailNotificationComprehensiveTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Admin user
        self.admin = User.objects.create_user(
            username='admin.hk',
            email='admin@thpthuongkhe.edu.vn',
            password='AdminPassword123!',
            role=User.ROLE_ADMIN,
            account_status=User.STATUS_APPROVED
        )

        # Đoàn trường user 1 (eligible)
        self.doan_truong_1 = User.objects.create_user(
            username='doan.truong1',
            email='doan1@thpthuongkhe.edu.vn',
            password='DoanPassword123!',
            role=User.ROLE_DOAN_TRUONG,
            can_verify_violations=True,
            account_status=User.STATUS_APPROVED,
            is_active=True,
        )

        # Đoàn trường user 2 (eligible)
        self.doan_truong_2 = User.objects.create_user(
            username='doan.truong2',
            email='doan2@thpthuongkhe.edu.vn',
            password='DoanPassword123!',
            role=User.ROLE_DOAN_TRUONG,
            can_verify_violations=False,
            account_status=User.STATUS_APPROVED,
            is_active=True,
        )

        # Sao đỏ
        self.sao_do = User.objects.create_user(
            username='saodo.10a1',
            email='saodo@thpthuongkhe.edu.vn',
            password='SaodoPassword123!',
            role=User.ROLE_SAO_DO,
            account_status=User.STATUS_APPROVED
        )

        self.year = AcademicYear.objects.create(name='2026-2027', start_date='2026-09-05', end_date='2027-05-30', is_current=True)
        self.semester = Semester.objects.create(academic_year=self.year, semester_number=1, name='Học kỳ I', start_date='2026-09-05', end_date='2027-01-15', is_current=True)
        from competition.models import CompetitionPeriod
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

        self.school_class = SchoolClass.objects.create(
            name='10A1', grade=10, academic_year=self.year,
        )
        self.student = Student.objects.create(
            student_code='HK261001',
            full_name='Trần Minh Quân',
            date_of_birth='2010-01-01',
            school_class=self.school_class
        )

        self.category = ConductRuleCategory.objects.create(name='Đồng phục & Tác phong')
        self.rule = ConductRule.objects.create(
            category=self.category,
            code='DP01',
            name='Không mặc đồng phục đúng quy định',
            default_points_deducted=Decimal('2.00')
        )

    def test_eligible_recipients_filters_properly(self):
        """Kiểm tra chỉ lấy tài khoản Đoàn trường đã duyệt, active và email hợp lệ."""
        # User unapproved
        User.objects.create_user(
            username='doan.pending',
            email='doan.pending@thpthuongkhe.edu.vn',
            role=User.ROLE_DOAN_TRUONG,
            account_status=User.STATUS_PENDING,
            is_active=True,
        )
        # User inactive
        User.objects.create_user(
            username='doan.inactive',
            email='doan.inactive@thpthuongkhe.edu.vn',
            role=User.ROLE_DOAN_TRUONG,
            account_status=User.STATUS_APPROVED,
            is_active=False,
        )
        # User duplicate email
        User.objects.create_user(
            username='doan.dup',
            email='doan1@thpthuongkhe.edu.vn',  # same as doan_truong_1
            role=User.ROLE_DOAN_TRUONG,
            account_status=User.STATUS_APPROVED,
            is_active=True,
        )
        # User with invalid email format
        User.objects.create_user(
            username='doan.invalidemail',
            email='not-an-email',
            role=User.ROLE_DOAN_TRUONG,
            account_status=User.STATUS_APPROVED,
            is_active=True,
        )

        recipients = get_eligible_union_recipients()
        emails = [u.email for u in recipients]

        self.assertIn('doan1@thpthuongkhe.edu.vn', emails)
        self.assertIn('doan2@thpthuongkhe.edu.vn', emails)
        self.assertNotIn('doan.pending@thpthuongkhe.edu.vn', emails)
        self.assertNotIn('doan.inactive@thpthuongkhe.edu.vn', emails)
        self.assertNotIn('not-an-email', emails)
        # Unique email check: doan1 only appears once
        self.assertEqual(emails.count('doan1@thpthuongkhe.edu.vn'), 1)

    def test_multi_recipient_email_queuing_and_delivery(self):
        """Ghi nhận vi phạm tạo email outbox cho TẤT CẢ các tài khoản Đoàn trường hợp lệ."""
        with self.captureOnCommitCallbacks(execute=True):
            violation = create_violation_record(
                class_id=self.school_class.id,
                student_id=self.student.id,
                rule_id=self.rule.id,
                reporter=self.admin,
                direct_deduct=True,
                description='Học sinh không mặc đồng phục thứ Hai'
            )

        self.assertEqual(violation.status, ViolationRecord.STATUS_VERIFIED)
        self.assertEqual(violation.points_deducted, Decimal('2.00'))

        notifications = list(ViolationEmailNotification.objects.filter(violation=violation))
        self.assertEqual(len(notifications), 2)
        notif_emails = {n.recipient_email for n in notifications}
        self.assertEqual(notif_emails, {'doan1@thpthuongkhe.edu.vn', 'doan2@thpthuongkhe.edu.vn'})

        # Dispatch each queued notification
        for n in notifications:
            self.assertEqual(n.status, ViolationEmailNotification.STATUS_PENDING)
            self.assertTrue(send_violation_email(n.id))
            n.refresh_from_db()
            self.assertEqual(n.status, ViolationEmailNotification.STATUS_SENT)

        self.assertEqual(len(mail.outbox), 2)
        sent_recipients = {msg.to[0] for msg in mail.outbox}
        self.assertEqual(sent_recipients, {'doan1@thpthuongkhe.edu.vn', 'doan2@thpthuongkhe.edu.vn'})

        # Verify subject and content format
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, "[HK Student Hub] Thông báo ghi nhận vi phạm và trừ điểm thi đua")
        self.assertIn('Trường THPT Hương Khê – Hà Tĩnh', msg.body)
        self.assertIn(violation.record_code, msg.body)
        self.assertIn('Trần Minh Quân', msg.body)
        self.assertIn('10A1', msg.body)
        self.assertIn('Không mặc đồng phục đúng quy định', msg.body)
        self.assertIn('-2.00đ', msg.body)
        self.assertIn('Điểm thi đua của Chi đoàn sau khi trừ:', msg.body)
        self.assertIn('/?tab=conduct&violation=', msg.body)

    def test_violation_with_evidence_notes_in_email(self):
        """Bản ghi có minh chứng được phản ánh đúng trạng thái bảo mật trong nội dung email."""
        fake_image = SimpleUploadedFile(
            name='test_minh_chung.jpg',
            content=b'fake image data',
            content_type='image/jpeg'
        )
        with self.captureOnCommitCallbacks(execute=True):
            violation = create_violation_record(
                class_id=self.school_class.id,
                student_id=self.student.id,
                rule_id=self.rule.id,
                reporter=self.admin,
                direct_deduct=True,
                description='Có ảnh chụp xe đạp điện vi phạm',
                evidence_image=fake_image,
                evidence_notes='Ảnh chụp cổng phụ 06:50'
            )

        notifications = list(ViolationEmailNotification.objects.filter(violation=violation))
        notif = notifications[0]
        self.assertIn('Có minh chứng đính kèm (Lưu trữ bảo mật trong hệ thống)', notif.body_text)
        self.assertIn('Ảnh chụp cổng phụ 06:50', notif.body_text)
        self.assertIn('xem chi tiết vi phạm & minh chứng', notif.body_html.lower())

    def test_no_eligible_recipients_creates_skipped_and_admin_notification(self):
        """Khi không có tài khoản Đoàn trường nào hợp lệ, ghi nhận SKIPPED và gửi cảnh báo cho Admin."""
        # Deactivate all union users
        User.objects.filter(role=User.ROLE_DOAN_TRUONG).update(is_active=False)

        with self.captureOnCommitCallbacks(execute=True):
            violation = create_violation_record(
                class_id=self.school_class.id,
                student_id=self.student.id,
                rule_id=self.rule.id,
                reporter=self.admin,
                direct_deduct=True,
                description='Không có ai nhận email'
            )

        self.assertEqual(violation.status, ViolationRecord.STATUS_VERIFIED)
        notifications = list(ViolationEmailNotification.objects.filter(violation=violation))
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].status, ViolationEmailNotification.STATUS_SKIPPED)
        self.assertIn('không tìm thấy tài khoản đoàn trường', notifications[0].last_error.lower())

        # Verify admin received system notification
        admin_notif = Notification.objects.filter(recipient=self.admin, notification_type=Notification.TYPE_CONDUCT).first()
        self.assertIsNotNone(admin_notif)
        self.assertIn('Cảnh báo Email', admin_notif.title)

    def test_smtp_failure_does_not_rollback_violation_or_deduct_twice(self):
        """Lỗi gửi SMTP ghi nhận an toàn, không rollback vi phạm và không trừ điểm lần 2."""
        initial_score = Decimal('100.00')

        with patch('django.core.mail.EmailMultiAlternatives.send', side_effect=Exception('Connection refused by SMTP')):
            with self.captureOnCommitCallbacks(execute=True):
                violation = create_violation_record(
                    class_id=self.school_class.id,
                    student_id=self.student.id,
                    rule_id=self.rule.id,
                    reporter=self.admin,
                    direct_deduct=True,
                    description='Kiểm tra SMTP failure'
                )

        # Violation still recorded and verified
        self.assertEqual(violation.status, ViolationRecord.STATUS_VERIFIED)
        self.assertEqual(violation.score_after, initial_score - Decimal('2.00'))

        notif = ViolationEmailNotification.objects.filter(violation=violation).first()
        with patch('django.core.mail.EmailMultiAlternatives.send', side_effect=Exception('Connection refused by SMTP')):
            result = send_violation_email(notif.id)
            self.assertFalse(result)

        notif.refresh_from_db()
        self.assertEqual(notif.attempt_count, 1)
        self.assertIn('Connection refused by SMTP', notif.last_error)

        # Re-verify score did NOT decrease again
        violation.refresh_from_db()
        self.assertEqual(violation.score_after, initial_score - Decimal('2.00'))

    def test_retry_email_does_not_duplicate_violation_or_deduction(self):
        """Gửi lại email thất bại qua API không tạo mới vi phạm hay trừ điểm tiếp."""
        violation = create_violation_record(
            class_id=self.school_class.id,
            student_id=self.student.id,
            rule_id=self.rule.id,
            reporter=self.admin,
            direct_deduct=True,
            description='Chuẩn bị cho retry'
        )
        notif = ViolationEmailNotification.objects.filter(violation=violation).first()
        notif.status = ViolationEmailNotification.STATUS_FAILED
        notif.last_error = 'Lỗi gửi thử'
        notif.save()

        count_before = ViolationRecord.objects.count()
        score_before = violation.score_after

        self.client.force_login(self.admin)
        res = self.client.post(f'/api/conduct/email/{notif.id}/retry/')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()['success'])

        notif.refresh_from_db()
        self.assertEqual(notif.status, ViolationEmailNotification.STATUS_PENDING)

        # Violation records and score must remain completely unchanged
        self.assertEqual(ViolationRecord.objects.count(), count_before)
        violation.refresh_from_db()
        self.assertEqual(violation.score_after, score_before)

    def test_admin_email_config_api_returns_eligible_recipients(self):
        """API cấu hình email trả về danh sách các tài khoản Đoàn trường hợp lệ."""
        self.client.force_login(self.admin)
        res = self.client.get('/api/conduct/email/config/')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['recipient_count'], 2)
        emails = [r['email'] for r in data['recipients']]
        self.assertIn(self.doan_truong_1.email, emails)
        self.assertIn(self.doan_truong_2.email, emails)

    def test_admin_email_test_api(self):
        """Admin gửi email kiểm thử SMTP thành công."""
        self.client.force_login(self.admin)
        res = self.client.post(
            '/api/conduct/email/test/',
            data=json.dumps({'recipient_email': 'test@example.com'}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()['success'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])
        self.assertIn('Kiểm tra kết nối', mail.outbox[0].subject)

    def test_non_admin_forbidden_from_email_management(self):
        """Người dùng không phải Admin không được phép truy cập API quản lý email."""
        self.client.force_login(self.sao_do)

        self.assertEqual(self.client.get('/api/conduct/email/config/').status_code, 403)
        self.assertEqual(self.client.post('/api/conduct/email/config/', data={'email': 'test@gmail.com'}).status_code, 403)
        self.assertEqual(self.client.delete('/api/conduct/email/config/').status_code, 403)
        self.assertEqual(self.client.post('/api/conduct/email/test/', data={}).status_code, 403)
        self.assertEqual(self.client.get('/api/conduct/email/history/').status_code, 403)

    def test_admin_can_add_gmail_recipient(self):
        """Admin có thể thêm mới một địa chỉ Gmail vào danh sách Đoàn trường nhận thông báo."""
        self.client.force_login(self.admin)
        res = self.client.post(
            '/api/conduct/email/config/',
            data=json.dumps({
                'email': 'doan.huongkhe.new@gmail.com',
                'full_name': 'Nguyễn Văn Minh - Bí thư Đoàn'
            }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertIn('Đã thêm thành công', data['message'])
        self.assertEqual(data['recipient_count'], 3)

        new_user = User.objects.get(email='doan.huongkhe.new@gmail.com')
        self.assertEqual(new_user.role, User.ROLE_DOAN_TRUONG)
        self.assertEqual(new_user.account_status, User.STATUS_APPROVED)
        self.assertTrue(new_user.is_active)
        self.assertFalse(new_user.can_verify_violations)
        self.assertEqual(new_user.full_name, 'Nguyễn Văn Minh - Bí thư Đoàn')

    def test_admin_can_add_multiple_gmail_recipients_at_once(self):
        """Admin có thể nhập nhiều địa chỉ Gmail cách nhau bởi dấu phẩy để thêm đồng thời."""
        self.client.force_login(self.admin)
        res = self.client.post(
            '/api/conduct/email/config/',
            data=json.dumps({
                'email': 'canbo1@gmail.com, canbo2@gmail.com',
                'full_name': 'Tổ Giám thị Đoàn'
            }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['recipient_count'], 4)  # 2 existing + 2 new

        self.assertTrue(User.objects.filter(email='canbo1@gmail.com').exists())
        self.assertTrue(User.objects.filter(email='canbo2@gmail.com').exists())

    def test_admin_can_elevate_existing_user_by_adding_their_email(self):
        """Nếu email đã thuộc tài khoản hiện có (ví dụ GVBM), hệ thống sẽ cấp quyền Đoàn trường và kích hoạt nhận thông báo."""
        teacher = User.objects.create(
            username='gv_hoa',
            email='gv.hoa@gmail.com',
            full_name='Cô Hoa Hóa học',
            role=User.ROLE_GVBM,
            account_status=User.STATUS_APPROVED,
            is_active=True,
            can_verify_violations=False,
        )

        self.client.force_login(self.admin)
        res = self.client.post(
            '/api/conduct/email/config/',
            data=json.dumps({'email': 'gv.hoa@gmail.com'}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        teacher.refresh_from_db()
        self.assertEqual(teacher.role, User.ROLE_DOAN_TRUONG)
        self.assertFalse(teacher.can_verify_violations)

    def test_admin_can_remove_gmail_recipient(self):
        """Admin có thể gỡ một tài khoản khỏi danh sách nhận email Đoàn trường."""
        self.client.force_login(self.admin)
        res = self.client.delete(
            f'/api/conduct/email/config/?id={self.doan_truong_2.id}'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['recipient_count'], 1)

        self.doan_truong_2.refresh_from_db()
        self.assertFalse(self.doan_truong_2.can_verify_violations)
        self.assertNotEqual(self.doan_truong_2.role, User.ROLE_DOAN_TRUONG)

    def test_admin_can_update_smtp_settings(self):
        """Admin có thể cập nhật cấu hình máy chủ SMTP Gmail gửi đi."""
        self.client.force_login(self.admin)
        res = self.client.post(
            '/api/conduct/email/config/',
            data=json.dumps({
                'action': 'update_smtp',
                'smtp_user': 'sender.hk@gmail.com',
                'smtp_password': 'abcd efgh ijkl mnop',
                'default_from_email': 'HK Student Hub <sender.hk@gmail.com>'
            }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['smtp_user'], 'sender.hk@gmail.com')
        self.assertEqual(data['default_from_email'], 'HK Student Hub <sender.hk@gmail.com>')
        self.assertTrue(data['smtp_configured'])

    def test_add_invalid_gmail_returns_error(self):
        """Nhập email sai định dạng sẽ trả về mã lỗi 400 Bad Request rõ ràng."""
        self.client.force_login(self.admin)
        res = self.client.post(
            '/api/conduct/email/config/',
            data=json.dumps({'email': 'not-an-email-address'}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn('error', res.json())

