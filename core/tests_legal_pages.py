# -*- coding: utf-8 -*-
from django.test import TestCase

from core.models import SystemSetting


class LegalPagesTests(TestCase):
    def setUp(self):
        SystemSetting.objects.update_or_create(
            key='LEGAL_DOC_STATUS',
            defaults={'value': 'Bản dự thảo – chờ nhà trường phê duyệt', 'description': 'Trạng thái pháp lý'},
        )
        SystemSetting.objects.update_or_create(
            key='PRIVACY_POLICY_VERSION',
            defaults={'value': 'v1.0-draft', 'description': 'Phiên bản bảo mật'},
        )
        SystemSetting.objects.update_or_create(
            key='TERMS_OF_SERVICE_VERSION',
            defaults={'value': 'v1.0-draft', 'description': 'Phiên bản điều khoản'},
        )

    def test_privacy_policy_page_renders_draft_status_and_home_link(self):
        response = self.client.get('/privacy-policy')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['show_privacy_policy'])
        self.assertFalse(response.context['show_terms_of_service'])
        self.assertContains(response, 'Chính sách quyền riêng tư')
        self.assertContains(response, 'v1.0-draft')
        self.assertContains(response, 'Bản dự thảo')
        self.assertContains(response, 'href="/"')

    def test_terms_page_renders_draft_status_and_home_link(self):
        response = self.client.get('/terms-of-service')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['show_terms_of_service'])
        self.assertFalse(response.context['show_privacy_policy'])
        self.assertContains(response, 'Điều khoản sử dụng')
        self.assertContains(response, 'v1.0-draft')
        self.assertContains(response, 'Bản dự thảo')
        self.assertContains(response, 'href="/"')

    def test_home_and_registration_link_to_both_legal_pages(self):
        home = self.client.get('/')
        self.assertEqual(home.status_code, 200)
        self.assertContains(home, 'href="/privacy-policy"')
        self.assertContains(home, 'href="/terms-of-service"')

        registration = self.client.get('/register')
        self.assertEqual(registration.status_code, 200)
        self.assertContains(registration, 'id="register-terms"')
        self.assertContains(registration, 'href="/terms-of-service"')
        self.assertContains(registration, 'href="/privacy-policy"')

    def test_public_legal_layout_keeps_focus_mobile_and_reduced_motion_support(self):
        response = self.client.get('/privacy-policy')
        self.assertContains(response, '.legal-layout')
        self.assertContains(response, ':focus-visible')
        self.assertContains(response, '@media (max-width: 620px)')
        self.assertContains(response, '@media (prefers-reduced-motion: reduce)')
