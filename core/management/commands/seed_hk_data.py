from django.core.management.base import BaseCommand, CommandError
from core.seed_data import clean_mock_data, seed_production_demo_data, seed_system_data


class Command(BaseCommand):
    help = 'Khoi tao hoac dat lai du lieu mau cho he thong HK Student Hub - THPT Huong Khe'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Xoa sach du lieu thu nghiem',
        )
        parser.add_argument(
            '--production-safe',
            action='store_true',
            help='Tạo bộ dữ liệu minh họa đã ẩn danh và một tài khoản quản trị bootstrap.',
        )

    def handle(self, *args, **options):
        if options['clean'] and options['production_safe']:
            raise CommandError('Không thể dùng đồng thời --clean và --production-safe.')

        if options['clean']:
            self.stdout.write(self.style.WARNING('Dang don dep du lieu thu nghiem...'))
            clean_mock_data()
            self.stdout.write(self.style.SUCCESS('Don dep hoan tat!'))
        elif options['production_safe']:
            temporary_password = seed_production_demo_data()
            self.stdout.write(self.style.SUCCESS('Đã tạo dữ liệu production minh họa đã ẩn danh.'))
            self.stdout.write(self.style.WARNING(
                'Mật khẩu bootstrap admin (chỉ hiển thị lần này): '
                + temporary_password
            ))
        else:
            self.stdout.write(self.style.NOTICE('Dang khoi tao du lieu mau cho HK Student Hub...'))
            seed_system_data()
            self.stdout.write(self.style.SUCCESS('Khoi tao du lieu thanh cong!'))
