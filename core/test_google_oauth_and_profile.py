import json
from datetime import date
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone
from django.conf import settings

from conduct.models import SchoolClass, Student
from core.models import User, AcademicYear, AuditLog, ApprovalLog


def make_mock_http_response(data_dict):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(data_dict).encode('utf-8')
    mock_resp.__enter__.return_value = mock_resp
    return mock_resp


class GoogleOAuthAndProfileTests(TestCase):
    def setUp(self):
        self.year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=date(2026, 9, 5),
            end_date=date(2027, 5, 30),
            is_current=True,
        )
        self.class_10a1 = SchoolClass.objects.create(
            name='10A1', grade=10, academic_year=self.year, is_active=True
        )
        self.class_11a2 = SchoolClass.objects.create(
            name='11A2', grade=11, academic_year=self.year, is_active=True
        )
        self.admin = User.objects.create_superuser(
            username='system_admin',
            email='admin@huongkhe.edu.vn',
            password='AdminPassword123!',
            full_name='Quản trị viên hệ thống',
            role=User.ROLE_ADMIN,
            account_status=User.STATUS_APPROVED,
            profile_completed=True,
            is_active=True,
        )

    def test_01_google_login_missing_config_returns_error_redirect(self):
        """Khi chưa cấu hình Google Client ID, truy cập đăng nhập Google trả về thông báo lỗi."""
        with patch.object(settings, 'GOOGLE_OAUTH_CLIENT_ID', ''):
            response = self.client.get('/api/core/auth/google/')
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login?error=google_not_configured', response['Location'])

    def test_02_google_login_with_config_redirects_to_google_consent(self):
        """Khi đã cấu hình, đăng nhập Google chuyển hướng đến accounts.google.com với state an toàn."""
        with patch.object(settings, 'GOOGLE_OAUTH_CLIENT_ID', 'test-client-id.apps.googleusercontent.com'), \
             patch.object(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', 'test-client-secret'):
            response = self.client.get('/api/core/auth/google/')
            self.assertEqual(response.status_code, 302)
            self.assertIn('https://accounts.google.com/o/oauth2/v2/auth', response['Location'])
            self.assertIn('client_id=test-client-id.apps.googleusercontent.com', response['Location'])
            self.assertIn('scope=openid+email+profile', response['Location'])
            self.assertTrue(bool(self.client.session.get('google_oauth_state')))

    def test_03_google_callback_user_cancelled_redirects_to_login(self):
        """Người dùng bấm hủy trên màn hình Google thì chuyển hướng về /login với lỗi phù hợp."""
        response = self.client.get('/api/core/auth/google/callback/?error=access_denied')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login?error=google_cancelled', response['Location'])

    def test_04_google_callback_state_mismatch_fails_securely(self):
        """Lỗi CSRF state mismatch bị từ chối an toàn."""
        session = self.client.session
        session['google_oauth_state'] = 'correct-state-token'
        session.save()

        response = self.client.get('/api/core/auth/google/callback/?code=some_code&state=wrong-state-token')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login?error=google_state_mismatch', response['Location'])

    @patch('urllib.request.urlopen')
    def test_05_new_google_user_created_as_pending_and_redirected_to_complete_profile(self, mock_urlopen):
        """Người dùng Google đăng ký lần đầu: tạo tài khoản PENDING, profile_completed=False, chuyển đến /complete-profile."""
        session = self.client.session
        session['google_oauth_state'] = 'valid-test-state'
        session.save()

        token_mock = make_mock_http_response({'access_token': 'mock-access-token'})
        userinfo_mock = make_mock_http_response({
            'sub': 'google-uid-10001',
            'email': 'student.new@gmail.com',
            'name': 'Nguyễn Văn Google',
            'picture': 'https://lh3.googleusercontent.com/a/photo123',
        })
        mock_urlopen.side_effect = [token_mock, userinfo_mock]

        with patch.object(settings, 'GOOGLE_OAUTH_CLIENT_ID', 'test-client-id'), \
             patch.object(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', 'test-client-secret'):
            response = self.client.get('/api/core/auth/google/callback/?code=mock-code&state=valid-test-state')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response['Location'], '/complete-profile')

        user = User.objects.get(google_id='google-uid-10001')
        self.assertEqual(user.email, 'student.new@gmail.com')
        self.assertEqual(user.account_status, User.STATUS_PENDING)
        self.assertFalse(user.profile_completed)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.role, User.ROLE_HOC_SINH)

    def test_06_complete_profile_as_student_submits_pending_and_creates_student_record(self):
        """Người dùng Google hoàn thiện hồ sơ chọn Học sinh: cập nhật thông tin, tạo bản ghi Student, trạng thái PENDING."""
        user = User.objects.create(
            username='google_student_1',
            email='hocsinh.test@huongkhe.edu.vn',
            full_name='Trần Học Sinh',
            google_id='google-sub-20002',
            account_status=User.STATUS_PENDING,
            profile_completed=False,
            role=User.ROLE_HOC_SINH,
            is_active=True,
        )
        self.client.force_login(user)

        payload = {
            'role_type': 'student',
            'full_name': 'Trần Học Sinh Chuẩn',
            'grade': 10,
            'class_name': '10A1',
            'dob': '2010-05-15',
            'gender': 'Nam',
            'phone': '0912345678',
            'student_code': 'HS10A105',
        }
        res = self.client.post('/api/core/auth/complete-profile/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()['success'])
        self.assertEqual(res.json()['redirect_url'], '/pending-approval')

        user.refresh_from_db()
        self.assertTrue(user.profile_completed)
        self.assertEqual(user.account_status, User.STATUS_PENDING)
        self.assertEqual(user.requested_role, User.ROLE_HOC_SINH)
        self.assertEqual(user.department_or_class, '10A1')
        self.assertIsNotNone(user.submitted_at)

        student = Student.objects.get(user=user)
        self.assertEqual(student.full_name, 'Trần Học Sinh Chuẩn')
        self.assertEqual(student.school_class, self.class_10a1)
        self.assertEqual(student.student_code, 'HS10A105')
        self.assertTrue(ApprovalLog.objects.filter(user=user, new_status=User.STATUS_PENDING).exists())

    def test_07_complete_profile_as_teacher_submits_pending_with_correct_requested_role(self):
        """Người dùng Google hoàn thiện hồ sơ chọn Giáo viên chủ nhiệm: requested_role=GVCN, trạng thái PENDING."""
        user = User.objects.create(
            username='google_teacher_1',
            email='giaovien.test@huongkhe.edu.vn',
            full_name='Thầy Giáo Test',
            google_id='google-sub-30003',
            account_status=User.STATUS_PENDING,
            profile_completed=False,
            role=User.ROLE_HOC_SINH,
            is_active=True,
        )
        self.client.force_login(user)

        payload = {
            'role_type': 'teacher',
            'full_name': 'Nguyễn Văn Giáo Viên',
            'phone': '0987654321',
            'subject': 'Toán học',
            'teacher_type': 'gvcn',
            'homeroom_class': '11A2',
            'teacher_code': 'GV-TOAN01',
        }
        res = self.client.post('/api/core/auth/complete-profile/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)

        user.refresh_from_db()
        self.assertTrue(user.profile_completed)
        self.assertEqual(user.account_status, User.STATUS_PENDING)
        self.assertEqual(user.requested_role, User.ROLE_GVCN)
        self.assertEqual(user.department_or_class, '11A2')

    def test_08_pending_account_cannot_access_dashboard_via_direct_url(self):
        """Tài khoản PENDING gõ trực tiếp /dashboard bị chuyển hướng sang /pending-approval."""
        pending_user = User.objects.create(
            username='pending_user_8',
            email='pending8@example.com',
            account_status=User.STATUS_PENDING,
            profile_completed=True,
            is_active=True,
        )
        self.client.force_login(pending_user)

        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/pending-approval', res['Location'])

    def test_09_pending_account_cannot_call_internal_business_apis(self):
        """Tài khoản PENDING gọi trực tiếp API nội bộ bị chặn 403 Forbidden."""
        pending_user = User.objects.create(
            username='pending_user_9',
            email='pending9@example.com',
            account_status=User.STATUS_PENDING,
            profile_completed=True,
            is_active=True,
        )
        self.client.force_login(pending_user)

        res = self.client.get('/api/conduct/violations/')
        self.assertEqual(res.status_code, 403)
        self.assertIn('error', res.json())

    @patch('urllib.request.urlopen')
    def test_10_logout_and_google_login_again_resumes_pending_status(self, mock_urlopen):
        """Tài khoản đang PENDING đăng xuất rồi đăng nhập lại bằng Google vẫn giữ trạng thái chờ duyệt."""
        User.objects.create(
            username='google_pending_10',
            email='pending10@gmail.com',
            google_id='google-sub-40004',
            account_status=User.STATUS_PENDING,
            profile_completed=True,
            is_active=True,
        )

        session = self.client.session
        session['google_oauth_state'] = 'test-state-10'
        session.save()

        token_mock = make_mock_http_response({'access_token': 'token-10'})
        userinfo_mock = make_mock_http_response({'sub': 'google-sub-40004', 'email': 'pending10@gmail.com'})
        mock_urlopen.side_effect = [token_mock, userinfo_mock]

        with patch.object(settings, 'GOOGLE_OAUTH_CLIENT_ID', 'test-client-id'), \
             patch.object(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', 'test-client-secret'):
            res = self.client.get('/api/core/auth/google/callback/?code=code-10&state=test-state-10')
            self.assertEqual(res.status_code, 302)
            self.assertEqual(res['Location'], '/pending-approval')

    def test_11_admin_approves_account_grants_access_to_dashboard(self):
        """Quản trị viên phê duyệt tài khoản PENDING -> APPROVED -> người dùng vào được Dashboard."""
        user = User.objects.create(
            username='user_to_approve',
            email='approve.me@example.com',
            account_status=User.STATUS_PENDING,
            requested_role=User.ROLE_HOC_SINH,
            department_or_class='10A1',
            profile_completed=True,
            is_active=True,
        )

        self.client.force_login(self.admin)
        review_payload = {
            'action': 'approve',
            'assigned_role': User.ROLE_HOC_SINH,
            'department_or_class': '10A1',
        }
        review_res = self.client.post(
            f'/api/core/users/{user.id}/review/',
            data=json.dumps(review_payload),
            content_type='application/json'
        )
        self.assertEqual(review_res.status_code, 200)

        user.refresh_from_db()
        self.assertEqual(user.account_status, User.STATUS_APPROVED)
        self.assertEqual(user.role, User.ROLE_HOC_SINH)

        self.client.force_login(user)
        dash_res = self.client.get('/dashboard')
        self.assertEqual(dash_res.status_code, 200)

    def test_12_admin_rejects_account_blocks_dashboard_and_shows_reason(self):
        """Quản trị viên từ chối tài khoản PENDING -> REJECTED -> chặn truy cập và hiển thị lý do."""
        user = User.objects.create(
            username='user_to_reject',
            email='reject.me@example.com',
            account_status=User.STATUS_PENDING,
            profile_completed=True,
            is_active=True,
        )

        self.client.force_login(self.admin)
        review_payload = {
            'action': 'reject',
            'reason': 'Thông tin lớp học không trùng khớp với danh sách nộp từ GVCN.',
        }
        review_res = self.client.post(
            f'/api/core/users/{user.id}/review/',
            data=json.dumps(review_payload),
            content_type='application/json'
        )
        self.assertEqual(review_res.status_code, 200)

        user.refresh_from_db()
        self.assertEqual(user.account_status, User.STATUS_REJECTED)
        self.assertIn('không trùng khớp', user.rejection_reason)

        self.client.force_login(user)
        dash_res = self.client.get('/dashboard')
        self.assertEqual(dash_res.status_code, 302)
        self.assertIn('/pending-approval', dash_res['Location'])

        pending_page = self.client.get('/pending-approval')
        self.assertEqual(pending_page.status_code, 200)
        self.assertContains(pending_page, 'Hồ sơ đăng ký bị từ chối')
        self.assertContains(pending_page, 'không trùng khớp với danh sách nộp từ GVCN')

    def test_13_suspended_account_is_blocked_from_internal_pages(self):
        """Tài khoản bị tạm khóa (SUSPENDED) bị chặn khỏi Dashboard và API nội bộ."""
        user = User.objects.create(
            username='suspended_user',
            email='suspended@example.com',
            account_status=User.STATUS_SUSPENDED,
            profile_completed=True,
            is_active=True,
        )
        self.client.force_login(user)

        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/pending-approval', res['Location'])

        api_res = self.client.get('/api/conduct/violations/')
        self.assertEqual(api_res.status_code, 403)

    @patch('urllib.request.urlopen')
    def test_14_approved_google_user_logs_in_directly_to_dashboard(self, mock_urlopen):
        """Tài khoản Google đã APPROVED khi đăng nhập lại được vào thẳng Dashboard, không trùng bản ghi."""
        User.objects.create(
            username='google_approved_user',
            email='approved.google@huongkhe.edu.vn',
            google_id='google-sub-50005',
            account_status=User.STATUS_APPROVED,
            profile_completed=True,
            role=User.ROLE_HOC_SINH,
            is_active=True,
        )
        count_before = User.objects.count()

        session = self.client.session
        session['google_oauth_state'] = 'test-state-approved'
        session.save()

        token_mock = make_mock_http_response({'access_token': 'token-approved'})
        userinfo_mock = make_mock_http_response({'sub': 'google-sub-50005', 'email': 'approved.google@huongkhe.edu.vn'})
        mock_urlopen.side_effect = [token_mock, userinfo_mock]

        with patch.object(settings, 'GOOGLE_OAUTH_CLIENT_ID', 'test-client-id'), \
             patch.object(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', 'test-client-secret'):
            res = self.client.get('/api/core/auth/google/callback/?code=code-appr&state=test-state-approved')
            self.assertEqual(res.status_code, 302)
            self.assertEqual(res['Location'], '/dashboard')

        self.assertEqual(User.objects.count(), count_before)

    @patch('urllib.request.urlopen')
    def test_15_incomplete_profile_resumes_to_complete_profile_on_next_login(self, mock_urlopen):
        """Nếu người dùng đóng trình duyệt khi chưa gửi hồ sơ, đăng nhập lại sẽ tiếp tục ở /complete-profile."""
        User.objects.create(
            username='google_incomplete_user',
            email='incomplete@gmail.com',
            google_id='google-sub-60006',
            account_status=User.STATUS_PENDING,
            profile_completed=False,
            is_active=True,
        )
        session = self.client.session
        session['google_oauth_state'] = 'test-state-incomplete'
        session.save()

        token_mock = make_mock_http_response({'access_token': 'token-inc'})
        userinfo_mock = make_mock_http_response({'sub': 'google-sub-60006', 'email': 'incomplete@gmail.com'})
        mock_urlopen.side_effect = [token_mock, userinfo_mock]

        with patch.object(settings, 'GOOGLE_OAUTH_CLIENT_ID', 'test-client-id'), \
             patch.object(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', 'test-client-secret'):
            res = self.client.get('/api/core/auth/google/callback/?code=code-inc&state=test-state-incomplete')
            self.assertEqual(res.status_code, 302)
            self.assertEqual(res['Location'], '/complete-profile')

    def test_16_duplicate_profile_submissions_are_idempotent(self):
        """Bấm nút gửi hồ sơ nhiều lần cập nhật cùng một tài khoản và không tạo bản ghi trùng lặp."""
        user = User.objects.create(
            username='google_idempotent_user',
            email='idempotent@example.com',
            google_id='google-sub-70007',
            account_status=User.STATUS_PENDING,
            profile_completed=False,
            is_active=True,
        )
        self.client.force_login(user)

        payload = {
            'role_type': 'student',
            'full_name': 'Học Sinh Lặp',
            'grade': 10,
            'class_name': '10A1',
        }
        res1 = self.client.post('/api/core/auth/complete-profile/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res1.status_code, 200)

        count_users = User.objects.count()
        count_students = Student.objects.count()

        res2 = self.client.post('/api/core/auth/complete-profile/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res2.status_code, 200)

        self.assertEqual(User.objects.count(), count_users)
        self.assertEqual(Student.objects.count(), count_students)

    @patch('urllib.request.urlopen')
    def test_17_email_collision_with_password_account_is_handled_safely(self, mock_urlopen):
        """Khi tài khoản đã tồn tại trong database, đăng nhập bằng Google sẽ tự động liên kết Google ID và chấp nhận (accept) đăng nhập ngay."""
        existing_user = User.objects.create_user(
            username='local_password_user',
            email='shared.email@huongkhe.edu.vn',
            password='OldSecurePass123!',
            role=User.ROLE_GVCN,
            account_status=User.STATUS_APPROVED,
            profile_completed=True,
            is_active=True,
        )
        count_before = User.objects.count()

        session = self.client.session
        session['google_oauth_state'] = 'test-state-collision'
        session.save()

        token_mock = make_mock_http_response({'access_token': 'token-collision'})
        userinfo_mock = make_mock_http_response({
            'sub': 'google-new-sub-999',
            'email': 'shared.email@huongkhe.edu.vn',
            'name': 'Thầy Nguyễn Văn A',
            'picture': 'https://example.com/avatar.jpg'
        })
        mock_urlopen.side_effect = [token_mock, userinfo_mock]

        with patch.object(settings, 'GOOGLE_OAUTH_CLIENT_ID', 'test-client-id'), \
             patch.object(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', 'test-client-secret'):
            res = self.client.get('/api/core/auth/google/callback/?code=code-col&state=test-state-collision')
            self.assertEqual(res.status_code, 302)
            # Tài khoản đã tồn tại và đã duyệt -> chuyển hướng thẳng vào dashboard
            self.assertEqual(res['Location'], '/dashboard')

        # Không tạo tài khoản trùng lặp mới
        self.assertEqual(User.objects.count(), count_before)
        updated_user = User.objects.get(email='shared.email@huongkhe.edu.vn')
        # Google ID đã được liên kết thành công
        self.assertEqual(updated_user.google_id, 'google-new-sub-999')
        self.assertEqual(updated_user.google_avatar_url, 'https://example.com/avatar.jpg')
        self.assertEqual(updated_user.role, User.ROLE_GVCN)

    def test_18_complete_profile_cannot_self_assign_admin_or_privileged_roles(self):
        """Người dùng không thể tự chọn vai trò Admin, Đoàn trường hoặc Sao đỏ tại màn hình hoàn thiện hồ sơ."""
        user = User.objects.create(
            username='google_exploit_user',
            email='exploit@gmail.com',
            google_id='google-sub-80008',
            account_status=User.STATUS_PENDING,
            profile_completed=False,
            is_active=True,
        )
        self.client.force_login(user)

        payload = {
            'role_type': 'admin',
            'full_name': 'Hacker Thử Nghiệm',
        }
        res = self.client.post('/api/core/auth/complete-profile/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 400)

        user.refresh_from_db()
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.account_status, User.STATUS_PENDING)

    def test_19_traditional_username_password_login_works_normally(self):
        """Đăng nhập bằng tên đăng nhập/mật khẩu truyền thống vẫn hoạt động trơn tru."""
        User.objects.create_user(
            username='traditional_student',
            email='trad.student@huongkhe.edu.vn',
            password='StrongPassword123!',
            role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED,
            profile_completed=True,
            is_active=True,
        )
        res = self.client.post(
            '/api/core/auth/login/',
            data={'username': 'traditional_student', 'password': 'StrongPassword123!'},
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn('user', res.json())
        self.assertEqual(res.json()['user']['username'], 'traditional_student')

    def test_20_page_renders_google_button_and_complete_profile_template(self):
        """Trang /login và /register có nút Google, trang /complete-profile và /pending-approval hiển thị đúng giao diện."""
        login_res = self.client.get('/login')
        self.assertEqual(login_res.status_code, 200)
        self.assertContains(login_res, 'Tiếp tục với Google')

        register_res = self.client.get('/register')
        self.assertEqual(register_res.status_code, 200)
        self.assertContains(register_res, 'Đăng ký bằng Google')

        incomplete_user = User.objects.create(
            username='incomplete_ui_user',
            email='incomplete.ui@gmail.com',
            full_name='Hồ Sơ Chưa Xong',
            account_status=User.STATUS_PENDING,
            profile_completed=False,
            is_active=True,
        )
        self.client.force_login(incomplete_user)
        profile_page = self.client.get('/complete-profile')
        self.assertEqual(profile_page.status_code, 200)
        self.assertContains(profile_page, 'Hoàn thiện hồ sơ đăng ký')
        self.assertContains(profile_page, 'incomplete.ui@gmail.com')
        self.assertContains(profile_page, 'Học sinh')
        self.assertContains(profile_page, 'Giáo viên')
        self.assertContains(profile_page, 'Quản trị viên phê duyệt')

        pending_ui_user = User.objects.create(
            username='pending_ui_user',
            email='pending.ui@gmail.com',
            full_name='Chờ Phê Duyệt UI',
            account_status=User.STATUS_PENDING,
            requested_role=User.ROLE_HOC_SINH,
            department_or_class='10A1',
            profile_completed=True,
            submitted_at=timezone.now(),
            is_active=True,
        )
        self.client.force_login(pending_ui_user)
        pending_page = self.client.get('/pending-approval')
        self.assertEqual(pending_page.status_code, 200)
        self.assertContains(pending_page, 'Hồ sơ đang chờ Quản trị viên phê duyệt')
        self.assertContains(pending_page, 'Chờ Phê Duyệt UI')
        self.assertContains(pending_page, 'pending.ui@gmail.com')
        self.assertContains(pending_page, '10A1')
        self.assertContains(pending_page, 'Bạn chưa thể sử dụng Dashboard và các chức năng nội bộ cho đến khi tài khoản được duyệt.')
