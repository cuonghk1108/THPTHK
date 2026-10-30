import sys
from django.core.management.base import BaseCommand
from competition.services import init_standard_35_weeks_schedule


class Command(BaseCommand):
    help = 'Khởi tạo chuẩn hóa 35 tuần học cho THPT Hương Khê (18 tuần Học kỳ I + 17 tuần Học kỳ II)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Tính toán lại điểm cưỡng bức cho tất cả các kỳ chưa chốt',
        )

    def handle(self, *args, **options):
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        
        self.stdout.write('Đang khởi tạo chuẩn 35 tuần thi đua cho THPT Hương Khê...')
        res = init_standard_35_weeks_schedule(force_recalculate=options.get('force', False))
        self.stdout.write(
            f"Thành công! Đã thiết lập {res['total_weeks']} tuần học "
            f"({res['hk1_weeks']} tuần HK I, {res['hk2_weeks']} tuần HK II). "
            f"Tổng số kỳ: {res['total_periods']}. Lớp học: {res['classes_count']}."
        )
