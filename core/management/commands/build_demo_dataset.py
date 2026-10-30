from datetime import date
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from alerts.models import EarlyWarningAlert, HomeroomIntervention
from competition.models import ClassCompetitionScore
from conduct.models import (
    Student,
    Teacher,
    ViolationRecord,
    ViolationReviewHistory,
)
from counseling.models import CounselingPrivateNote, CounselingRequest
from core.models import AuditLog, User
from core.seed_data import _seed_system_data


class Command(BaseCommand):
    help = 'Build the sanitized, static SQLite dataset packaged for demo deployments.'

    def handle(self, *args, **options):
        if connection.vendor != 'sqlite':
            raise CommandError('Chỉ được tạo bộ dữ liệu mẫu trên SQLite riêng.')

        database_path = Path(connection.settings_dict['NAME']).resolve()
        expected_path = (settings.BASE_DIR / 'sample_data' / 'demo.sqlite3').resolve()
        if database_path != expected_path:
            raise CommandError(f'DB_NAME phải trỏ tới {expected_path}.')

        project_models = [
            model for model in apps.get_models()
            if model._meta.app_label in {
                'core', 'conduct', 'competition', 'alerts', 'counseling'
            }
            and not model._meta.auto_created
        ]
        populated = [model.__name__ for model in project_models if model.objects.exists()]
        if populated:
            raise CommandError(
                'Từ chối ghi đè bộ dữ liệu; các bảng đã có dữ liệu: '
                + ', '.join(populated)
            )

        with transaction.atomic():
            _seed_system_data()
            self._anonymize()

        self.stdout.write(self.style.SUCCESS('Sanitized SQLite demo dataset created.'))

    @staticmethod
    def _anonymize():
        labels = {
            User.ROLE_ADMIN: 'Quản trị viên mẫu',
            User.ROLE_BGH: 'Ban Giám hiệu mẫu',
            User.ROLE_DOAN_TRUONG: 'Cán bộ Đoàn mẫu',
            User.ROLE_SAO_DO: 'Thành viên Sao đỏ mẫu',
            User.ROLE_GVCN: 'Giáo viên chủ nhiệm mẫu',
            User.ROLE_GVBM: 'Giáo viên bộ môn mẫu',
            User.ROLE_HOC_SINH: 'Học sinh mẫu',
            User.ROLE_CHUYEN_VIEN_TAM_LY: 'Chuyên viên tư vấn mẫu',
        }
        role_counts = {}
        for user in User.objects.order_by('id'):
            role_counts[user.role] = role_counts.get(user.role, 0) + 1
            label = labels.get(user.role, 'Người dùng mẫu')
            suffix = role_counts[user.role]
            user.full_name = label if suffix == 1 else f'{label} {suffix}'
            user.email = f'sample-user-{user.pk}@example.invalid'
            user.phone = ''
            user.is_active = True
            user.save(update_fields=['full_name', 'email', 'phone', 'is_active'])

        for index, student in enumerate(Student.objects.order_by('id'), start=1):
            student.student_code = f'SAMPLE-{index:04d}'
            student.full_name = f'Học sinh mẫu {index}'
            student.date_of_birth = date(2009, 1, 1)
            student.parent_name = ''
            student.parent_phone = ''
            student.address = ''
            student.save(update_fields=[
                'student_code', 'full_name', 'date_of_birth',
                'parent_name', 'parent_phone', 'address',
            ])

        for index, teacher in enumerate(Teacher.objects.order_by('id'), start=1):
            teacher.teacher_code = f'SAMPLE-T-{index:04d}'
            teacher.full_name = f'Giáo viên mẫu {index}'
            teacher.subject = 'Môn học mẫu'
            teacher.phone = ''
            teacher.save(update_fields=['teacher_code', 'full_name', 'subject', 'phone'])

        # Do not package private counseling or account/incident audit records.
        CounselingPrivateNote.objects.all().delete()
        CounselingRequest.objects.all().delete()
        AuditLog.objects.all().delete()
        ViolationReviewHistory.objects.all().delete()

        ViolationRecord.objects.all().update(
            student_name_snapshot='Học sinh mẫu',
            location='Khu vực mẫu',
            description='Bản ghi vi phạm minh họa đã ẩn danh.',
            evidence_notes='',
            verification_notes='',
            appeal_reason='',
            evidence_image='',
        )
        EarlyWarningAlert.objects.all().update(
            alert_title='Cảnh báo mẫu',
            details='Dữ liệu cảnh báo minh họa đã được ẩn danh.',
        )
        HomeroomIntervention.objects.all().update(
            action_taken='Biện pháp hỗ trợ minh họa.',
            outcome='Kết quả minh họa.',
        )
        ClassCompetitionScore.objects.all().update(
            bonus_notes='',
            notes='Dữ liệu điểm thi đua minh họa.',
        )
