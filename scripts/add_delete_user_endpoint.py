import sys

with open('core/views.py', 'rb') as f:
    text = f.read().decode('utf-8').replace('\r\n', '\n')

old_methods = "    http_method_names = ['get', 'post', 'head', 'options']"
new_methods = "    http_method_names = ['get', 'post', 'delete', 'head', 'options']"

assert old_methods in text, 'old_methods not found'
text = text.replace(old_methods, new_methods, 1)

destroy_method = '''    def destroy(self, request, *args, **kwargs):
        """Xóa vĩnh viễn tài khoản bởi Quản trị viên (Admin / Super Admin)."""
        if not (request.user.is_admin or request.user.is_super_admin or request.user.is_superuser):
            return Response(
                {'error': 'Chỉ có Quản trị viên hệ thống (Admin) mới có quyền xóa tài khoản.'},
                status=status.HTTP_403_FORBIDDEN
            )

        target_user = self.get_object()

        # Không thể tự xóa chính mình
        if target_user.id == request.user.id:
            return Response(
                {'error': 'Bạn không thể tự xóa tài khoản của chính mình.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Quản trị viên thường không được xóa Super Admin
        if (target_user.is_super_admin or target_user.is_superuser) and not request.user.is_super_admin and not request.user.is_superuser:
            return Response(
                {'error': 'Chỉ có Quản trị viên tối cao (Super Admin) mới có quyền xóa tài khoản Super Admin khác.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Không được xóa Super Admin duy nhất còn lại
        if target_user.is_super_admin or target_user.is_superuser:
            super_admin_count = User.objects.filter(
                Q(role=User.ROLE_SUPER_ADMIN) | Q(is_superuser=True),
                account_status=User.STATUS_APPROVED,
                is_active=True
            ).count()
            if super_admin_count <= 1:
                return Response(
                    {'error': 'Không thể xóa Quản trị viên tối cao (Super Admin) duy nhất của hệ thống.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        username = target_user.username
        full_name = target_user.full_name or username
        role_display = target_user.get_role_display()

        with transaction.atomic():
            AuditLog.objects.create(
                user=request.user,
                action='DELETE_USER',
                resource_type='USER',
                resource_id=str(target_user.id),
                details=f"Quản trị viên {request.user.full_name or request.user.username} đã xóa vĩnh viễn tài khoản {username} ({role_display}).",
                ip_address=request.META.get('REMOTE_ADDR'),
            )
            target_user.delete()

        return Response({
            'message': f'Đã xóa vĩnh viễn tài khoản {username} ({full_name}) thành công.'
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):'''

old_create = '    def create(self, request, *args, **kwargs):'
assert old_create in text, 'old_create not found'
text = text.replace(old_create, destroy_method, 1)

with open('core/views.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Successfully added destroy method in UserManagementViewSet in core/views.py!')
