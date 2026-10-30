import getpass
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from core.models import User, AuditLog


class Command(BaseCommand):
    help = 'Khoi tao tai khoan Quan tri vien toi cao (Super Admin) an toan cho he thong HK Student Hub'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Ten dang nhap cua Super Admin')
        parser.add_argument('--email', type=str, help='Dia chi email lien he')
        parser.add_argument('--full-name', type=str, help='Ho va ten day du cua quan tri vien')
        parser.add_argument('--password', type=str, help='Mat khau khoi tao (khuyen nghi nhap qua prompt de bao mat)')

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== KHOI TAO QUAN TRI VIEN TOI CAO (SUPER ADMIN) - HK STUDENT HUB ==="))
        
        username = options.get('username')
        while not username:
            val = input("Nhap ten dang nhap Super Admin: ").strip()
            if val:
                username = val
            else:
                self.stdout.write(self.style.WARNING("Ten dang nhap khong duoc de trong."))

        email = options.get('email')
        if not email:
            email = input("Nhap email quan tri (tuy chon, co the bo qua): ").strip()

        full_name = options.get('full_name')
        if not full_name:
            full_name = input("Nhap ho va ten day du (VD: Quan tri vien he thong): ").strip()
            if not full_name:
                full_name = "Quan tri vien he thong"

        # Check existing
        existing_user = User.objects.filter(username__iexact=username).first()

        password = options.get('password')
        while not password:
            pwd1 = getpass.getpass("Nhap mat khau Super Admin (it nhat 8 ky tu): ")
            pwd2 = getpass.getpass("Nhap lai mat khau de xac nhan: ")
            if pwd1 != pwd2:
                self.stdout.write(self.style.ERROR("Mat khau xac nhan khong khop. Vui long thu lai."))
                continue
            try:
                validate_password(pwd1)
                password = pwd1
            except ValidationError as e:
                self.stdout.write(self.style.ERROR(f"Mat khau chua dat tieu chuan bao mat: {', '.join(e.messages)}"))

        if existing_user:
            self.stdout.write(self.style.WARNING(f"Tai khoan '{username}' da ton tai. He thong se nang cap thanh Super Admin..."))
            existing_user.role = User.ROLE_SUPER_ADMIN
            existing_user.account_status = User.STATUS_APPROVED
            existing_user.is_active = True
            existing_user.is_staff = True
            existing_user.is_superuser = True
            existing_user.can_verify_violations = True
            existing_user.can_view_counseling = True
            if email:
                existing_user.email = email
            if full_name:
                existing_user.full_name = full_name
            existing_user.set_password(password)
            existing_user.save()
            super_admin = existing_user
            action_desc = f"Nang cap va cap nhat mat khau cho Super Admin {username}"
        else:
            super_admin = User.objects.create(
                username=username,
                email=email or '',
                full_name=full_name,
                role=User.ROLE_SUPER_ADMIN,
                account_status=User.STATUS_APPROVED,
                is_active=True,
                is_staff=True,
                is_superuser=True,
                can_verify_violations=True,
                can_view_counseling=True,
                must_change_password=False
            )
            super_admin.set_password(password)
            super_admin.save()
            action_desc = f"Khoi tao moi Super Admin {username}"

        AuditLog.objects.create(
            user=super_admin,
            action='BOOTSTRAP_SUPERADMIN',
            resource_type='USER',
            resource_id=str(super_admin.id),
            details=f"Lenh quan tri console: {action_desc}"
        )

        self.stdout.write(self.style.SUCCESS(
            f"\n[THANH CONG] Da thiet lap Super Admin: '{super_admin.username}' ({super_admin.full_name})\n"
            f"Vai tro: {super_admin.role}\n"
            f"Trang thai: {super_admin.account_status}\n"
            f"Quyen han: Quan tri toan quyen, phan quyen va xet duyet tai khoan moi."
        ))
