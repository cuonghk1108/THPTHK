from datetime import date

from django.test import TestCase

from conduct.models import SchoolClass
from core.models import AcademicYear, User


class PublicAuthRouteTests(TestCase):
    def setUp(self):
        self.year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=date(2026, 9, 5),
            end_date=date(2027, 5, 30),
            is_current=True,
        )
        self.school_class = SchoolClass.objects.create(
            name='10A1', grade=10, academic_year=self.year,
        )
        self.student = User.objects.create_user(
            username='auth_student',
            email='auth.student@example.edu.vn',
            password='StrongAuthPass123!A',
            full_name='Học sinh kiểm thử',
            department_or_class='10A1',
            role=User.ROLE_HOC_SINH,
            requested_role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_APPROVED,
            is_active=True,
        )

    def test_public_home_is_separate_from_private_dashboard(self):
        response = self.client.get('/')
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn('Đăng nhập', html)
        self.assertIn('Đăng ký tài khoản', html)
        self.assertIn('href="/login" class="hk-button hk-button-secondary"', html)
        self.assertIn('href="/register" class="hk-button hk-button-primary"', html)
        self.assertIn('href="#gioi-thieu">Giới thiệu</a>', html)
        self.assertIn('href="#chuc-nang">Các tính năng chính</a>', html)
        self.assertIn('.public-register-short { display: inline !important; }', html)
        self.assertNotIn('.public-actions .public-register-link { display: none; }', html)
        self.assertNotIn('id="tab-dashboard"', html)
        self.assertNotIn('Học sinh kiểm thử', html)

        self.client.force_login(self.student)
        authenticated_home = self.client.get('/')
        authenticated_html = authenticated_home.content.decode()
        self.assertEqual(authenticated_home.status_code, 200)
        self.assertIn('Vào hệ thống', authenticated_html)
        self.assertIn('Học sinh kiểm thử', authenticated_html)
        self.assertIn('id="public-account-avatar-fallback">HS</span>', authenticated_html)
        self.assertIn('Lớp/đơn vị: 10A1', authenticated_html)
        self.assertIn('Học sinh', authenticated_html)
        self.assertIn('Đã phê duyệt', authenticated_html)
        self.assertIn('href="/dashboard">Vào Dashboard</a>', authenticated_html)
        self.assertIn('href="/profile">Hồ sơ cá nhân</a>', authenticated_html)
        self.assertIn('id="public-account-logout"', authenticated_html)
        self.assertNotIn('id="public-guest-actions" class="public-actions">', authenticated_html)
        self.assertNotIn('id="tab-dashboard"', authenticated_html)

    def test_home_reflects_session_after_logout_without_leaking_old_profile(self):
        self.client.force_login(self.student)
        self.assertContains(self.client.get('/'), 'Học sinh kiểm thử')

        logout_response = self.client.post('/api/core/auth/logout/')

        self.assertEqual(logout_response.status_code, 200)
        home = self.client.get('/')
        html = home.content.decode()
        self.assertContains(home, 'Đăng nhập')
        self.assertContains(home, 'Đăng ký tài khoản')
        self.assertNotIn('Học sinh kiểm thử', html)
        self.assertNotIn('10A1', html)
        self.assertIn('id="public-user-account" class="public-account" hidden', html)

    def test_private_routes_redirect_to_login_and_preserve_safe_destination(self):
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/login?next=%2Fdashboard')

        profile = self.client.get('/profile?section=account')
        self.assertEqual(profile.status_code, 302)
        self.assertEqual(profile['Location'], '/login?next=%2Fprofile%3Fsection%3Daccount')

    def test_login_by_email_uses_server_role_and_opens_protected_dashboard(self):
        response = self.client.post(
            '/api/core/auth/login/',
            data={'username': self.student.email, 'password': 'StrongAuthPass123!A'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['role'], User.ROLE_HOC_SINH)
        home = self.client.get('/')
        self.assertContains(home, 'Học sinh kiểm thử')
        self.assertContains(home, 'Vào Dashboard')
        dashboard = self.client.get('/dashboard')
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn('no-store', dashboard['Cache-Control'])

    def test_pending_account_cannot_establish_a_dashboard_session(self):
        pending = User.objects.create_user(
            username='auth_pending',
            email='auth.pending@example.edu.vn',
            password='StrongAuthPass123!A',
            role=User.ROLE_HOC_SINH,
            requested_role=User.ROLE_HOC_SINH,
            account_status=User.STATUS_PENDING,
            is_active=False,
        )

        response = self.client.post(
            '/api/core/auth/login/',
            data={'username': pending.email, 'password': 'StrongAuthPass123!A'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(self.client.get('/dashboard').status_code, 302)

    def test_logout_ends_session_and_private_page_cannot_be_reopened(self):
        self.client.force_login(self.student)
        response = self.client.post('/api/core/auth/logout/')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(self.client.get('/dashboard')['Location'], '/login?next=%2Fdashboard')

    def test_forced_password_change_loads_the_private_shell_and_blocks_other_apis(self):
        self.student.must_change_password = True
        self.student.save(update_fields=['must_change_password'])
        self.client.force_login(self.student)

        dashboard = self.client.get('/dashboard')
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, 'password-change-overlay')
        self.assertEqual(self.client.get('/api/core/users/').status_code, 403)

    def test_registration_rejects_privileged_roles_and_unknown_classes(self):
        for index, role in enumerate(['ADMIN', 'SUPER_ADMIN', 'DOAN_TRUONG', 'GVCN', 'SAO_DO']):
            with self.subTest(role=role):
                username = f'self_select_{index}'
                privileged = self.client.post(
                    '/api/core/auth/register/',
                    data={
                        'full_name': f'Người đăng ký {role}',
                        'username': username,
                        'email': f'self.select.{index}@example.edu.vn',
                        'password': 'StrongAuthPass123!A',
                        'confirm_password': 'StrongAuthPass123!A',
                        'requested_role': role,
                        'department_or_class': 'Trường THPT Hương Khê',
                        'terms_accepted': True,
                    },
                    content_type='application/json',
                )
                self.assertEqual(privileged.status_code, 400)
                self.assertFalse(User.objects.filter(username=username).exists())

        invented_class = self.client.post(
            '/api/core/auth/register/',
            data={
                'full_name': 'Học sinh chọn lớp lạ',
                'username': 'unknown_class_student',
                'email': 'unknown.class@example.edu.vn',
                'password': 'StrongAuthPass123!A',
                'confirm_password': 'StrongAuthPass123!A',
                'requested_role': 'HOC_SINH',
                'grade_level': 10,
                'department_or_class': 'Lớp 10ZZ',
                'terms_accepted': True,
            },
            content_type='application/json',
        )
        self.assertEqual(invented_class.status_code, 400)
        self.assertFalse(SchoolClass.objects.filter(name='10ZZ').exists())

    def test_registration_page_offers_only_non_privileged_roles_and_password_toggle(self):
        response = self.client.get('/register')
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn('data-password-toggle="public-login-password"', self.client.get('/login').content.decode())
        self.assertNotIn('<option value="GVCN">', html)
        self.assertNotIn('<option value="SAO_DO">', html)
        self.assertNotIn('<option value="DOAN_TRUONG">', html)

    def test_student_registration_uses_existing_class_and_waits_for_approval(self):
        response = self.client.post(
            '/api/core/auth/register/',
            data={
                'full_name': 'Học sinh mới',
                'username': 'new_auth_student',
                'email': 'new.auth.student@example.edu.vn',
                'password': 'StrongAuthPass123!A',
                'confirm_password': 'StrongAuthPass123!A',
                'requested_role': 'HOC_SINH',
                'grade_level': 10,
                'class_id': self.school_class.id,
                'terms_accepted': True,
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        created = User.objects.get(username='new_auth_student')
        self.assertEqual(created.account_status, User.STATUS_PENDING)
        self.assertFalse(created.is_active)
        self.assertEqual(self.client.get('/dashboard')['Location'], '/login?next=%2Fdashboard')
