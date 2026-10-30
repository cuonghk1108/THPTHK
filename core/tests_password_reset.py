import json
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, Client, override_settings
from django.core import mail
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils import timezone
from django.core.cache import cache

from core.models import User, AuditLog


@override_settings(DEFAULT_FROM_EMAIL='HK Student Hub <hkstudenthub@gmail.com>')
class PasswordResetTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            username='teacher.an',
            email='an.nguyen@thpthuongkhe.edu.vn',
            password='OldSecurePassword123!',
            full_name='Nguyễn Văn An',
            role=User.ROLE_GVCN,
            account_status=User.STATUS_APPROVED,
        )

    def test_forgot_password_valid_email_sends_email_and_neutral_response(self):
        response = self.client.post(
            '/api/core/auth/forgot-password/',
            data=json.dumps({'email': 'an.nguyen@thpthuongkhe.edu.vn'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Nếu địa chỉ email hợp lệ', response.json()['message'])
        self.assertEqual(len(mail.outbox), 1)

        sent = mail.outbox[0]
        self.assertEqual(sent.to, ['an.nguyen@thpthuongkhe.edu.vn'])
        self.assertEqual(sent.from_email, 'HK Student Hub <hkstudenthub@gmail.com>')
        self.assertIn('Hướng dẫn đặt lại mật khẩu', sent.subject)
        self.assertIn('reset-password', sent.body)
        self.assertIn('THPT Hương Khê', sent.body)

        # AuditLog recorded
        self.assertTrue(
            AuditLog.objects.filter(action='FORGOT_PASSWORD_REQUEST', resource_id=str(self.user.id)).exists()
        )

    def test_forgot_password_unknown_email_returns_neutral_response_no_email(self):
        response = self.client.post(
            '/api/core/auth/forgot-password/',
            data=json.dumps({'email': 'nonexistent@example.com'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Nếu địa chỉ email hợp lệ', response.json()['message'])
        self.assertEqual(len(mail.outbox), 0)

    def test_forgot_password_rate_limiting(self):
        # 5 requests allowed
        for i in range(5):
            res = self.client.post(
                '/api/core/auth/forgot-password/',
                data=json.dumps({'email': 'an.nguyen@thpthuongkhe.edu.vn'}),
                content_type='application/json'
            )
            self.assertEqual(res.status_code, 200)

        # 6th request is throttled
        res = self.client.post(
            '/api/core/auth/forgot-password/',
            data=json.dumps({'email': 'an.nguyen@thpthuongkhe.edu.vn'}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 429)
        self.assertIn('quá nhiều yêu cầu', res.json()['error'])

    def test_reset_password_success(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.post(
            '/api/core/auth/reset-password/',
            data=json.dumps({
                'uid': uid,
                'token': token,
                'new_password': 'BrandNewPassword2026@',
                'confirm_password': 'BrandNewPassword2026@'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('thành công', response.json()['message'])

        # Verify old password cannot log in
        login_old = self.client.post(
            '/api/core/auth/login/',
            data=json.dumps({'username': 'teacher.an', 'password': 'OldSecurePassword123!'}),
            content_type='application/json'
        )
        self.assertEqual(login_old.status_code, 400)

        # Verify new password can log in
        login_new = self.client.post(
            '/api/core/auth/login/',
            data=json.dumps({'username': 'teacher.an', 'password': 'BrandNewPassword2026@'}),
            content_type='application/json'
        )
        self.assertEqual(login_new.status_code, 200)

        # Verify token is invalidated and cannot be reused
        response_reuse = self.client.post(
            '/api/core/auth/reset-password/',
            data=json.dumps({
                'uid': uid,
                'token': token,
                'new_password': 'AnotherPassword999!',
                'confirm_password': 'AnotherPassword999!'
            }),
            content_type='application/json'
        )
        self.assertEqual(response_reuse.status_code, 400)
        self.assertIn('không hợp lệ', response_reuse.json()['error'])

    def test_reset_password_password_mismatch(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.post(
            '/api/core/auth/reset-password/',
            data=json.dumps({
                'uid': uid,
                'token': token,
                'new_password': 'BrandNewPassword2026@',
                'confirm_password': 'DifferentPassword2026@'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('không khớp', response.json()['error'])

    def test_reset_password_short_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.post(
            '/api/core/auth/reset-password/',
            data=json.dumps({
                'uid': uid,
                'token': token,
                'new_password': 'short',
                'confirm_password': 'short'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('8 ký tự', response.json()['error'])

    def test_reset_password_invalid_uid_or_token(self):
        response = self.client.post(
            '/api/core/auth/reset-password/',
            data=json.dumps({
                'uid': 'invalid_uid',
                'token': 'invalid_token',
                'new_password': 'BrandNewPassword2026@',
                'confirm_password': 'BrandNewPassword2026@'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('không hợp lệ', response.json()['error'])

    @override_settings(PASSWORD_RESET_TIMEOUT=60)
    def test_reset_password_expired_token_is_rejected(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token_time = timezone.now().replace(tzinfo=None)
        with patch.object(default_token_generator, '_now', return_value=token_time):
            token = default_token_generator.make_token(self.user)

        with patch.object(
            default_token_generator,
            '_now',
            return_value=token_time + timedelta(seconds=61),
        ):
            response = self.client.post(
                '/api/core/auth/reset-password/',
                data=json.dumps({
                    'uid': uid,
                    'token': token,
                    'new_password': 'BrandNewPassword2026@',
                    'confirm_password': 'BrandNewPassword2026@'
                }),
                content_type='application/json'
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn('không hợp lệ', response.json()['error'])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldSecurePassword123!'))
