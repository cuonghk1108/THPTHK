# scripts/patch_forgot_password.py
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

# 1. Update core/serializers.py
serializers_path = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\core\serializers.py'
with open(serializers_path, 'r', encoding='utf-8') as f:
    ser_content = f.read()

old_ser = """class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        return value.strip().lower()"""

new_ser = """class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)

    def validate_email(self, value):
        val = value.strip().lower()
        if not val:
            raise serializers.ValidationError("Vui lòng nhập địa chỉ email hoặc tên đăng nhập.")
        return val"""

if old_ser in ser_content:
    ser_content = ser_content.replace(old_ser, new_ser, 1)
    with open(serializers_path, 'w', encoding='utf-8') as f:
        f.write(ser_content)
    print("[OK] Updated core/serializers.py")
else:
    print("[SKIP] core/serializers.py pattern not matched")

# 2. Update core/views.py
views_path = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\core\views.py'
with open(views_path, 'r', encoding='utf-8') as f:
    views_content = f.read()

old_views = """        user = User.objects.filter(
            email__iexact=email,
            is_active=True,
            account_status=User.STATUS_APPROVED
        ).first()

        neutral_message = (
            "Nếu địa chỉ email hợp lệ và đủ điều kiện khôi phục, bạn sẽ nhận được "
            "email hướng dẫn đặt lại mật khẩu. Vui lòng kiểm tra hộp thư đến và thư rác."
        )

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            frontend_base = getattr(settings, 'FRONTEND_BASE_URL', '').rstrip('/')
            if not frontend_base:
                frontend_base = f"{request.scheme}://{request.get_host()}"
            reset_url = f"{frontend_base}/reset-password?uid={uid}&token={token}"

            try:
                send_password_reset_email(user, reset_url)
                AuditLog.objects.create(
                    user=user,
                    action='FORGOT_PASSWORD_REQUEST',
                    resource_type='USER',
                    resource_id=str(user.id),
                    details=f"Yêu cầu đặt lại mật khẩu cho tài khoản {user.username} qua email {email}.",
                    ip_address=ip_address
                )
            except Exception as e:
                logger.error("Gửi email đặt lại mật khẩu thất bại (%s).", type(e).__name__)
                AuditLog.objects.create(
                    user=user,
                    action='FORGOT_PASSWORD_REQUEST_FAILED',
                    resource_type='USER',
                    resource_id=str(user.id),
                    details=f"Gửi email đặt lại mật khẩu thất bại ({type(e).__name__}).",
                    ip_address=ip_address
                )
        else:
            AuditLog.objects.create(
                user=None,
                action='FORGOT_PASSWORD_REQUEST',
                resource_type='USER',
                details=f"Yêu cầu đặt lại mật khẩu từ IP {ip_address} cho email không tồn tại hoặc chưa duyệt.",
                ip_address=ip_address
            )

        return Response({'message': neutral_message}, status=status.HTTP_200_OK)"""

new_views = """        # Hỗ trợ tìm kiếm theo cả email hoặc tên đăng nhập
        user = User.objects.filter(
            Q(email__iexact=email) | Q(username__iexact=email),
            is_active=True,
            account_status=User.STATUS_APPROVED
        ).first()

        neutral_message = (
            "Nếu địa chỉ email hợp lệ và đủ điều kiện khôi phục, bạn sẽ nhận được "
            "email hướng dẫn đặt lại mật khẩu. Vui lòng kiểm tra hộp thư đến và thư rác."
        )

        if user and user.email:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            frontend_base = getattr(settings, 'FRONTEND_BASE_URL', '').rstrip('/')
            if not frontend_base:
                frontend_base = f"{request.scheme}://{request.get_host()}"
            reset_url = f"{frontend_base}/reset-password?uid={uid}&token={token}"

            try:
                send_password_reset_email(user, reset_url)
                AuditLog.objects.create(
                    user=user,
                    action='FORGOT_PASSWORD_REQUEST',
                    resource_type='USER',
                    resource_id=str(user.id),
                    details=f"Yêu cầu đặt lại mật khẩu cho tài khoản {user.username} qua email {user.email}.",
                    ip_address=ip_address
                )
            except Exception as e:
                logger.error("Gửi email đặt lại mật khẩu thất bại (%s: %s).", type(e).__name__, str(e))
                AuditLog.objects.create(
                    user=user,
                    action='FORGOT_PASSWORD_REQUEST_FAILED',
                    resource_type='USER',
                    resource_id=str(user.id),
                    details=f"Gửi email đặt lại mật khẩu thất bại ({type(e).__name__}).",
                    ip_address=ip_address
                )
                if settings.DEBUG:
                    return Response(
                        {
                            'error': f'Lỗi kết nối máy chủ gửi thư ({type(e).__name__}). Trong môi trường phát triển (DEBUG), bạn có thể truy cập liên kết đặt lại bên dưới.',
                            'debug_reset_url': reset_url
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                return Response(
                    {'error': 'Hệ thống gửi email thông báo tạm thời gặp sự cố kết nối. Vui lòng liên hệ Quản trị viên nhà trường hoặc thử lại sau.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
        else:
            AuditLog.objects.create(
                user=None,
                action='FORGOT_PASSWORD_REQUEST',
                resource_type='USER',
                details=f"Yêu cầu đặt lại mật khẩu từ IP {ip_address} cho tài khoản/email không tồn tại hoặc chưa duyệt: {email}.",
                ip_address=ip_address
            )

        return Response({'message': neutral_message}, status=status.HTTP_200_OK)"""

if old_views in views_content:
    views_content = views_content.replace(old_views, new_views, 1)
    with open(views_path, 'w', encoding='utf-8') as f:
        f.write(views_content)
    print("[OK] Updated core/views.py")
else:
    print("[SKIP] core/views.py pattern not matched")

# 3. Update templates/index.html
html_path = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\templates\index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

old_html = """          <div class="auth-card-head">
            <h2>Khôi phục mật khẩu</h2>
            <p class="auth-card-intro">Nhập email đã đăng ký. Nếu đủ điều kiện, hướng dẫn sẽ được gửi đến hộp thư của bạn.</p>
          </div>
          <form id="public-forgot-form" class="auth-form" novalidate>{% csrf_token %}
            <div id="public-forgot-message" class="auth-success" role="status" hidden></div>
            <div id="public-forgot-error" class="auth-error" role="alert" hidden></div>
            <div class="auth-field">
              <label for="public-forgot-email">Email tài khoản <span style="color:#ef4444;">*</span></label>
              <input id="public-forgot-email" name="email" type="email" autocomplete="email" placeholder="email@example.com" required>
            </div>"""

# Match taking into account double newlines if any
pattern_html = re.compile(
    r'<div class="auth-card-head">\s*'
    r'<h2>Khôi phục mật khẩu</h2>\s*'
    r'<p class="auth-card-intro">Nhập email đã đăng ký\. Nếu đủ điều kiện, hướng dẫn sẽ được gửi đến hộp thư của bạn\.</p>\s*'
    r'</div>\s*'
    r'<form id="public-forgot-form" class="auth-form" novalidate>\{% csrf_token %\}\s*'
    r'<div id="public-forgot-message" class="auth-success" role="status" hidden></div>\s*'
    r'<div id="public-forgot-error" class="auth-error" role="alert" hidden></div>\s*'
    r'<div class="auth-field">\s*'
    r'<label for="public-forgot-email">Email tài khoản <span style="color:#ef4444;">\*</span></label>\s*'
    r'<input id="public-forgot-email" name="email" type="email" autocomplete="email" placeholder="email@example\.com" required>'
)

new_html_block = """          <div class="auth-card-head">
            <h2>Khôi phục mật khẩu</h2>
            <p class="auth-card-intro">Nhập email đã đăng ký hoặc tên đăng nhập. Nếu tài khoản hợp lệ, liên kết đặt lại sẽ được gửi đến hộp thư của bạn.</p>
          </div>
          <form id="public-forgot-form" class="auth-form" novalidate>{% csrf_token %}
            <div id="public-forgot-message" class="auth-success" role="status" hidden></div>
            <div id="public-forgot-error" class="auth-error" role="alert" hidden></div>
            <div class="auth-field">
              <label for="public-forgot-email">Email hoặc Tên đăng nhập <span style="color:#ef4444;">*</span></label>
              <input id="public-forgot-email" name="email" type="text" autocomplete="username" placeholder="Nhập email hoặc tên đăng nhập..." required>
            </div>"""

if pattern_html.search(html_content):
    html_content = pattern_html.sub(new_html_block, html_content, count=1)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("[OK] Updated templates/index.html")
else:
    print("[SKIP] templates/index.html pattern not matched")

# 4. Update static/public.js
public_js_path = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\public.js'
with open(public_js_path, 'r', encoding='utf-8') as f:
    js_content = f.read()

old_js = """          const { response, data } = await request('/api/core/auth/forgot-password/', { email }, form);
          if (!response.ok) throw new Error(errorText(data));
          setMessage('public-forgot-message', data.message || 'Nếu địa chỉ email đủ điều kiện, hướng dẫn sẽ được gửi đến hộp thư của bạn.');"""

new_js = """          const { response, data } = await request('/api/core/auth/forgot-password/', { email }, form);
          if (!response.ok) {
            let errMsg = errorText(data);
            if (data && data.debug_reset_url) {
              errMsg += `<br><a href="${data.debug_reset_url}" style="color:#2563EB; font-weight:700; text-decoration:underline; margin-top:8px; display:inline-block;">👉 Nhấn vào đây để đặt lại mật khẩu ngay (Chế độ phát triển)</a>`;
              const errEl = document.getElementById('public-forgot-error');
              if (errEl) {
                errEl.innerHTML = errMsg;
                errEl.hidden = false;
                return;
              }
            }
            throw new Error(errMsg);
          }
          setMessage('public-forgot-message', data.message || 'Nếu thông tin tài khoản hợp lệ, hướng dẫn sẽ được gửi đến hộp thư của bạn.');"""

if old_js in js_content:
    js_content = js_content.replace(old_js, new_js, 1)
    with open(public_js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print("[OK] Updated static/public.js")
else:
    print("[SKIP] static/public.js pattern not matched")

print("Patch forgot password completed!")
