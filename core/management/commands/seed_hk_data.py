import sys
from django.core.management.base import BaseCommand
from core.seed_data import seed_system_data, clean_mock_data


class Command(BaseCommand):
    help = 'Khoi tao hoac dat lai du lieu mau cho he thong HK Student Hub - THPT Huong Khe'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Xoa sach du lieu thu nghiem',
        )

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write(self.style.WARNING('Dang don dep du lieu thu nghiem...'))
            clean_mock_data()
            self.stdout.write(self.style.SUCCESS('Don dep hoan tat!'))
        else:
            self.stdout.write(self.style.NOTICE('Dang khoi tao du lieu mau cho HK Student Hub...'))
            seed_system_data()
            self.stdout.write(self.style.SUCCESS('Khoi tao du lieu thanh cong!'))
