from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from conduct.models import SchoolClass, Student, ConductRuleCategory, ConductRule, ViolationRecord, AcademicYear

User = get_user_model()


class ConductRulesTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin_test',
            password='Password123@Admin',
            email='admin_test@huongkhe.edu.vn',
            role='ADMIN',
            account_status=User.STATUS_APPROVED,
            full_name='Admin Quản Trị'
        )
        self.client.force_authenticate(user=self.admin)

        self.ay = AcademicYear.objects.create(
            name='2025-2026',
            start_date='2025-09-05',
            end_date='2026-05-31',
            is_current=True
        )

        # Create the 9 official categories
        self.cat1 = ConductRuleCategory.objects.create(name='Tập trung và Ngoại khóa', order=1, icon='users')
        self.cat2 = ConductRuleCategory.objects.create(name='Sinh hoạt 15 phút', order=2, icon='clock')
        self.cat3 = ConductRuleCategory.objects.create(name='Vệ sinh - Cơ sở vật chất', order=3, icon='sparkles')
        self.cat4 = ConductRuleCategory.objects.create(name='Tác phong - Đồng phục', order=4, icon='user-check')
        self.cat5 = ConductRuleCategory.objects.create(name='Nề nếp chuyên cần', order=5, icon='calendar-check')
        self.cat6 = ConductRuleCategory.objects.create(name='An toàn giao thông', order=6, icon='car')
        self.cat7 = ConductRuleCategory.objects.create(name='Dụng cụ - Thiết bị', order=7, icon='box')
        self.cat8 = ConductRuleCategory.objects.create(name='Phong trào - Hoạt động Đoàn', order=8, icon='flag')
        self.cat9 = ConductRuleCategory.objects.create(name='Kỷ luật học đường', order=9, icon='alert-triangle')

        # Create sample rules
        self.rule_tt01 = ConductRule.objects.create(
            code='TT01',
            name='Tập trung muộn sau 05 phút kể từ khi có trống chào cờ/tập trung',
            category=self.cat1,
            default_points_deducted=Decimal('5.00'),
            severity='MEDIUM',
            is_active=True
        )
        self.rule_sh02 = ConductRule.objects.create(
            code='SH02',
            name='Sinh hoạt 15 phút đối phó, không có chất lượng',
            category=self.cat2,
            default_points_deducted=Decimal('3.00'),
            severity='LOW',
            is_active=True
        )
        self.rule_gt01 = ConductRule.objects.create(
            code='GT01',
            name='Đi xe máy >50cc hoặc đi và để xe xung quanh ngoài trường',
            category=self.cat6,
            default_points_deducted=Decimal('15.00'),
            severity='CRITICAL',
            is_active=True
        )
        self.rule_kl10 = ConductRule.objects.create(
            code='KL10',
            name='Gây gổ đánh nhau, gây mất đoàn kết',
            category=self.cat9,
            default_points_deducted=Decimal('20.00'),
            severity='CRITICAL',
            is_active=True
        )

        # Historical inactive rule
        self.rule_old_vp01 = ConductRule.objects.create(
            code='VP-01',
            name='Đi học muộn (cũ)',
            category=self.cat5,
            default_points_deducted=Decimal('2.00'),
            severity='LOW',
            is_active=False
        )

        self.school_class = SchoolClass.objects.create(
            name='10A1',
            grade=10,
            academic_year=self.ay,
            class_order=1
        )
        self.student = Student.objects.create(
            student_code='HS1001',
            full_name='Trần Minh Tuấn',
            date_of_birth='2009-01-01',
            school_class=self.school_class
        )

    def test_01_categories_ordered(self):
        """Kiểm tra danh mục trả về đúng thứ tự order 1 đến 9"""
        response = self.client.get('/api/conduct/rule-categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cats = response.data.get('results', response.data)
        self.assertEqual(len(cats), 9)
        orders = [c['order'] for c in cats]
        self.assertEqual(orders, sorted(orders))

    def test_02_rules_default_filter_active_only(self):
        """Mặc định API /rules/ chỉ trả về các quy tắc is_active=True"""
        response = self.client.get('/api/conduct/rules/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rules = response.data.get('results', response.data)
        # Should contain TT01, SH02, GT01, KL10 but NOT VP-01
        codes = [r['code'] for r in rules]
        self.assertIn('TT01', codes)
        self.assertIn('KL10', codes)
        self.assertNotIn('VP-01', codes)

    def test_03_rules_all_includes_historical(self):
        """Khi truyền all=true hoặc is_active=false, API trả về cả quy tắc lịch sử"""
        response = self.client.get('/api/conduct/rules/?all=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rules = response.data.get('results', response.data)
        codes = [r['code'] for r in rules]
        self.assertIn('VP-01', codes)
        self.assertIn('TT01', codes)

    def test_04_preview_deduction_endpoint(self):
        """Kiểm tra tính năng xem trước số điểm trừ cho quy tắc mới"""
        url = f'/api/conduct/violations/preview-deduction/?class_id={self.school_class.id}&rule_id={self.rule_kl10.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['rule_code'], 'KL10')
        self.assertEqual(data['points_to_deduct'], 20.0)
        self.assertEqual(data['current_score'], 100.0)
        self.assertEqual(data['projected_score'], 80.0)

    def test_05_create_violation_with_official_rule(self):
        """Tạo bản ghi vi phạm với quy tắc mới thành công và chuyển trạng thái chờ xác minh"""
        payload = {
            'class_id': self.school_class.id,
            'rule': self.rule_gt01.id,
            'student_id': self.student.id,
            'location': 'Cổng trường THPT Hương Khê',
            'description': 'Đi xe máy 110cc không có GPLX'
        }
        response = self.client.post('/api/conduct/violations/', data=payload, format='multipart')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        v_record = ViolationRecord.objects.get(rule=self.rule_gt01)
        self.assertEqual(v_record.student, self.student)
        self.assertEqual(v_record.status, ViolationRecord.STATUS_PENDING)
        self.assertEqual(v_record.rule.default_points_deducted, Decimal('15.00'))
