from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import AcademicYear
from conduct.models import SchoolClass
from competition.models import CompetitionPeriod, ClassCompetitionScore
from decimal import Decimal


class Command(BaseCommand):
    help = 'Khởi tạo chính xác và đầy đủ 64 lớp học cho Trường THPT Hương Khê'

    def handle(self, *args, **options):
        year = AcademicYear.objects.filter(is_current=True).first()
        if not year:
            year, _ = AcademicYear.objects.get_or_create(
                name='2026-2027',
                defaults={
                    'start_date': '2026-09-05',
                    'end_date': '2027-05-30',
                    'is_current': True
                }
            )

        # 64 classes definition
        # Khối 10: 22 lớp (10A1 -> 10A22)
        # Khối 11: 21 lớp (11A1 -> 11A21)
        # Khối 12: 21 lớp (12A1 -> 12A21)
        target_classes = []
        for i in range(1, 23):
            target_classes.append((f"10A{i}", 10))
        for i in range(1, 22):
            target_classes.append((f"11A{i}", 11))
        for i in range(1, 22):
            target_classes.append((f"12A{i}", 12))

        self.stdout.write(f"Bat dau khoi tao/dong bo {len(target_classes)} lop hoc...")

        created_count = 0
        existing_count = 0

        with transaction.atomic():
            for name, grade in target_classes:
                cls_obj, created = SchoolClass.objects.get_or_create(
                    name=name,
                    academic_year=year,
                    defaults={
                        'grade': grade,
                        'student_count': 40,
                        'is_active': True,
                        'union_branch_name': f"Chi đoàn {name}",
                        'room_number': f"Phòng học {name}"
                    }
                )
                if created:
                    created_count += 1
                else:
                    existing_count += 1
                    # Ensure grade and is_active are set correctly
                    if cls_obj.grade != grade or not cls_obj.is_active:
                        cls_obj.grade = grade
                        cls_obj.is_active = True
                        cls_obj.save(update_fields=['grade', 'is_active'])

            total_now = SchoolClass.objects.filter(academic_year=year, is_active=True).count()
            self.stdout.write(self.style.SUCCESS(
                f"Hoan thanh: Tao moi {created_count} lop, Da co san {existing_count} lop. "
                f"Tong so lop hoat dong nam {year.name}: {total_now}/64"
            ))

            # Ensure all active competition periods have score records for all classes
            for period in CompetitionPeriod.objects.filter(academic_year=year):
                for cls_obj in SchoolClass.objects.filter(academic_year=year, is_active=True):
                    ClassCompetitionScore.objects.get_or_create(
                        competition_period=period,
                        school_class=cls_obj,
                        defaults={
                            'base_points': Decimal('100.00'),
                            'total_score': Decimal('100.00'),
                        }
                    )
