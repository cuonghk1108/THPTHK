import os
import sys

BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"

# ==============================================================================
# 1. PATCH core/views.py
# ==============================================================================
views_path = os.path.join(BASE_DIR, "core", "views.py")
with open(views_path, "r", encoding="utf-8") as f:
    views_code = f.read()

# Normalize newlines
views_norm = views_code.replace("\r\n", "\n")

# A. index_view
old_index_snippet = """        # A. Người dùng chưa hoàn thiện hồ sơ (Google mới đăng ký): bắt buộc vào /complete-profile
        if not getattr(user, 'profile_completed', True):
            if normalized_path in protected_routes or normalized_path in {'/login', '/register', '/pending-approval', '/registration-pending'}:
                return redirect('/complete-profile')

        # B. Người dùng đang ở trạng thái PENDING (đã nộp hồ sơ, chờ duyệt)
        elif user.account_status == User.STATUS_PENDING:
            if normalized_path in protected_routes or normalized_path in {'/login', '/register', '/complete-profile'}:
                return redirect('/pending-approval')

        # C. Người dùng bị từ chối hoặc tạm khóa
        elif user.account_status in [User.STATUS_REJECTED, User.STATUS_SUSPENDED, User.STATUS_DISABLED]:
            if normalized_path in protected_routes or normalized_path in {'/login', '/register', '/complete-profile'}:
                return redirect('/pending-approval')

        # D. Người dùng đã được phê duyệt (APPROVED)
        elif is_approved_session:
            if normalized_path in {'/login', '/register', '/complete-profile', '/pending-approval', '/registration-pending'}:
                return redirect('/dashboard')"""

new_index_snippet = """        # 1. TÀI KHOẢN ĐÃ ĐƯỢC PHÊ DUYỆT (APPROVED) HOẶC LÀ ADMIN/SUPERUSER:
        # BỎ QUA HOÀN THIỆN HỒ SƠ VÀ TRANG CHỜ DUYỆT -> VÀO THẲNG DASHBOARD!
        if is_approved_session or user.account_status == User.STATUS_APPROVED or user.is_superuser or user.is_staff:
            if not getattr(user, 'profile_completed', True):
                User.objects.filter(pk=user.pk).update(profile_completed=True)
                user.profile_completed = True
            if normalized_path in {'/login', '/register', '/complete-profile', '/pending-approval', '/registration-pending'}:
                return redirect('/dashboard')

        # 2. Người dùng bị từ chối hoặc tạm khóa
        elif user.account_status in [User.STATUS_REJECTED, User.STATUS_SUSPENDED, User.STATUS_DISABLED]:
            if normalized_path in protected_routes or normalized_path in {'/login', '/register', '/complete-profile'}:
                return redirect('/pending-approval')

        # 3. Người dùng chưa hoàn thiện hồ sơ (Google mới đăng ký lần đầu và CHƯA được phê duyệt): bắt buộc vào /complete-profile
        elif not getattr(user, 'profile_completed', True):
            if normalized_path in protected_routes or normalized_path in {'/login', '/register', '/pending-approval', '/registration-pending'}:
                return redirect('/complete-profile')

        # 4. Người dùng đang ở trạng thái PENDING (đã nộp hồ sơ, chờ duyệt)
        elif user.account_status == User.STATUS_PENDING:
            if normalized_path in protected_routes or normalized_path in {'/login', '/register', '/complete-profile'}:
                return redirect('/pending-approval')"""

if old_index_snippet in views_norm:
    views_norm = views_norm.replace(old_index_snippet, new_index_snippet)
    print("SUCCESS: Updated index_view navigation logic in core/views.py")
else:
    print("WARNING: old_index_snippet not found in core/views.py")

# B. GoogleOAuthCallbackView
old_callback_snippet = """                if user.account_status == User.STATUS_APPROVED:
                    if not user.profile_completed:
                        return redirect('/complete-profile')
                    return redirect('/dashboard')
                elif not user.profile_completed:
                    return redirect('/complete-profile')"""

new_callback_snippet = """                # NẾU TÀI KHOẢN ĐÃ ĐƯỢC PHÊ DUYỆT: BỎ QUA HOÀN THIỆN HỒ SƠ, VÀO THẲNG DASHBOARD
                if user.account_status == User.STATUS_APPROVED or user.is_superuser or user.is_staff:
                    if not user.profile_completed:
                        User.objects.filter(pk=user.pk).update(profile_completed=True)
                        user.profile_completed = True
                    return redirect('/dashboard')
                elif not user.profile_completed:
                    return redirect('/complete-profile')"""

if old_callback_snippet in views_norm:
    views_norm = views_norm.replace(old_callback_snippet, new_callback_snippet)
    print("SUCCESS: Updated GoogleOAuthCallbackView in core/views.py")
else:
    print("WARNING: old_callback_snippet not found in core/views.py")

# C. CompleteProfileAPIView
old_api_snippet = """        user = request.user
        if user.account_status == User.STATUS_APPROVED:
            return Response(
                {'error': 'Tài khoản của bạn đã được Quản trị viên phê duyệt trước đó. Không cần hoàn thiện lại hồ sơ.'},
                status=status.HTTP_400_BAD_REQUEST
            )"""

new_api_snippet = """        user = request.user
        if user.account_status == User.STATUS_APPROVED or user.is_superuser or user.is_staff:
            if not user.profile_completed:
                User.objects.filter(pk=user.pk).update(profile_completed=True)
                user.profile_completed = True
            return Response(
                {
                    'message': 'Tài khoản của bạn đã được Quản trị viên phê duyệt trước đó.',
                    'redirect_url': '/dashboard'
                },
                status=status.HTTP_200_OK
            )"""

if old_api_snippet in views_norm:
    views_norm = views_norm.replace(old_api_snippet, new_api_snippet)
    print("SUCCESS: Updated CompleteProfileAPIView in core/views.py")
else:
    print("WARNING: old_api_snippet not found in core/views.py")

# D. UserManagementViewSet.review (set profile_completed=True on approve)
old_review_approve = """            if action_type == 'approve':
                target_user.account_status = User.STATUS_APPROVED
                target_user.is_active = True"""

new_review_approve = """            if action_type == 'approve':
                target_user.account_status = User.STATUS_APPROVED
                target_user.profile_completed = True
                target_user.is_active = True"""

if old_review_approve in views_norm:
    views_norm = views_norm.replace(old_review_approve, new_review_approve)
    print("SUCCESS: Updated UserManagementViewSet.review in core/views.py")
else:
    print("WARNING: old_review_approve not found in core/views.py")

# E. StudentApprovalViewSet.approve
old_student_approve = """        with transaction.atomic():
            target_user.account_status = User.STATUS_APPROVED
            target_user.is_active = True
            target_user.role = User.ROLE_HOC_SINH"""

new_student_approve = """        with transaction.atomic():
            target_user.account_status = User.STATUS_APPROVED
            target_user.profile_completed = True
            target_user.is_active = True
            target_user.role = User.ROLE_HOC_SINH"""

if old_student_approve in views_norm:
    views_norm = views_norm.replace(old_student_approve, new_student_approve)
    print("SUCCESS: Updated StudentApprovalViewSet.approve in core/views.py")
else:
    print("WARNING: old_student_approve not found in core/views.py")

# F. StudentApprovalViewSet.bulk_approve
old_bulk_approve = """                prev_status = target_user.account_status
                target_user.account_status = User.STATUS_APPROVED
                target_user.is_active = True
                target_user.role = User.ROLE_HOC_SINH"""

new_bulk_approve = """                prev_status = target_user.account_status
                target_user.account_status = User.STATUS_APPROVED
                target_user.profile_completed = True
                target_user.is_active = True
                target_user.role = User.ROLE_HOC_SINH"""

if old_bulk_approve in views_norm:
    views_norm = views_norm.replace(old_bulk_approve, new_bulk_approve)
    print("SUCCESS: Updated StudentApprovalViewSet.bulk_approve in core/views.py")
else:
    print("WARNING: old_bulk_approve not found in core/views.py")

with open(views_path, "w", encoding="utf-8") as f:
    f.write(views_norm)
print("Finished writing core/views.py")

# ==============================================================================
# 2. PATCH core/serializers.py
# ==============================================================================
serializers_path = os.path.join(BASE_DIR, "core", "serializers.py")
with open(serializers_path, "r", encoding="utf-8") as f:
    serializers_code = f.read()

serializers_norm = serializers_code.replace("\r\n", "\n")

old_create_user = """        user = User(
            **validated_data,
            account_status=User.STATUS_APPROVED,
            is_active=True,
            is_staff=False,
            is_superuser=False,"""

new_create_user = """        user = User(
            **validated_data,
            account_status=User.STATUS_APPROVED,
            profile_completed=True,
            is_active=True,
            is_staff=False,
            is_superuser=False,"""

if old_create_user in serializers_norm:
    serializers_norm = serializers_norm.replace(old_create_user, new_create_user)
    print("SUCCESS: Updated UserCreateSerializer in core/serializers.py")
else:
    print("WARNING: old_create_user not found in core/serializers.py")

with open(serializers_path, "w", encoding="utf-8") as f:
    f.write(serializers_norm)
print("Finished writing core/serializers.py")

# ==============================================================================
# 3. PATCH core/middleware.py
# ==============================================================================
middleware_path = os.path.join(BASE_DIR, "core", "middleware.py")
with open(middleware_path, "r", encoding="utf-8") as f:
    middleware_code = f.read()

middleware_norm = middleware_code.replace("\r\n", "\n")

old_middleware_approved = """        # If user is approved, standard role-based access control applies
        from core.models import User
        if user.account_status == User.STATUS_APPROVED:
            return None"""

new_middleware_approved = """        # If user is approved, standard role-based access control applies
        from core.models import User
        if user.account_status == User.STATUS_APPROVED or user.is_superuser or user.is_staff:
            if not getattr(user, 'profile_completed', True):
                User.objects.filter(pk=user.pk).update(profile_completed=True)
                user.profile_completed = True
            return None"""

if old_middleware_approved in middleware_norm:
    middleware_norm = middleware_norm.replace(old_middleware_approved, new_middleware_approved)
    print("SUCCESS: Updated AccountStatusEnforcementMiddleware approved check in core/middleware.py")
else:
    print("WARNING: old_middleware_approved not found in core/middleware.py")

old_middleware_profile = """        # For HTML page routes:
        # If user has not completed profile (e.g. freshly registered via Google)
        if not getattr(user, 'profile_completed', True):
            if request.path.rstrip('/') in {'/complete-profile', '/privacy-policy', '/terms-of-service'}:
                return None
            return redirect('/complete-profile')"""

new_middleware_profile = """        # For HTML page routes:
        # If user has not completed profile (and is NOT approved)
        if not getattr(user, 'profile_completed', True) and user.account_status != User.STATUS_APPROVED:
            if request.path.rstrip('/') in {'/complete-profile', '/privacy-policy', '/terms-of-service'}:
                return None
            return redirect('/complete-profile')"""

if old_middleware_profile in middleware_norm:
    middleware_norm = middleware_norm.replace(old_middleware_profile, new_middleware_profile)
    print("SUCCESS: Updated AccountStatusEnforcementMiddleware HTML redirect in core/middleware.py")
else:
    print("WARNING: old_middleware_profile not found in core/middleware.py")

with open(middleware_path, "w", encoding="utf-8") as f:
    f.write(middleware_norm)
print("Finished writing core/middleware.py")
