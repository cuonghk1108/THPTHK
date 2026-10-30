import logging
from html import escape

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


def build_password_reset_email(user, reset_url):
    """
    Tạo nội dung email HTML và Plain Text hướng dẫn đặt lại mật khẩu
    theo quy chuẩn nhận diện thương hiệu của HK Student Hub - Trường THPT Hương Khê.
    """
    subject = "[HK Student Hub] Hướng dẫn đặt lại mật khẩu"
    recipient_name = user.full_name or user.username
    html_recipient_name = escape(recipient_name)
    html_reset_url = escape(reset_url, quote=True)

    text_content = (
        f"Xin chào {recipient_name},\n\n"
        "Hệ thống HK Student Hub đã nhận được yêu cầu đặt lại mật khẩu cho tài khoản của bạn.\n\n"
        "Để tạo mật khẩu mới, vui lòng truy cập liên kết bên dưới:\n"
        f"{reset_url}\n\n"
        "Liên kết có thời hạn sử dụng và chỉ được dùng một lần theo quy trình bảo mật của hệ thống.\n"
        "Nếu bạn không thực hiện yêu cầu này, hãy bỏ qua email. Mật khẩu hiện tại của bạn sẽ không thay đổi.\n\n"
        "Trân trọng,\n\n"
        "HK Student Hub\n"
        "Trường THPT Hương Khê – Hà Tĩnh\n"
    )

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(subject)}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f7fb; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f4f7fb; padding: 40px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 10px 25px rgba(22, 58, 112, 0.08);">
          
          <!-- Header -->
          <tr>
            <td style="background-color: #163A70; padding: 28px 32px; text-align: left;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                  <td>
                    <div style="font-size: 11px; font-weight: 800; color: #93c5fd; letter-spacing: 0.1em; text-transform: uppercase;">TRƯỜNG THPT HƯƠNG KHÊ – HÀ TĨNH</div>
                    <div style="font-size: 22px; font-weight: 900; color: #ffffff; margin-top: 4px; letter-spacing: -0.02em;">HK Student Hub</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding: 36px 32px 28px 32px;">
              <h1 style="font-size: 20px; font-weight: 800; color: #163A70; margin-top: 0; margin-bottom: 16px;">Hướng dẫn đặt lại mật khẩu</h1>
              
              <p style="font-size: 14px; line-height: 1.6; color: #334155; margin-bottom: 16px;">
                Xin chào <strong>{html_recipient_name}</strong>,
              </p>
              
              <p style="font-size: 14px; line-height: 1.6; color: #334155; margin-bottom: 24px;">
                Hệ thống HK Student Hub đã nhận được yêu cầu đặt lại mật khẩu cho tài khoản của bạn. Để tạo mật khẩu mới, vui lòng nhấn vào nút bên dưới:
              </p>

              <!-- CTA Button -->
              <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 28px 0;">
                <tr>
                  <td align="center" style="border-radius: 12px; background-color: #2563EB;">
                    <a href="{html_reset_url}" target="_blank" style="font-size: 14px; font-weight: 800; color: #ffffff; text-decoration: none; padding: 14px 28px; display: inline-block; border-radius: 12px; letter-spacing: 0.02em;">
                      ĐẶT LẠI MẬT KHẨU
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Notice Box -->
              <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #2563EB; border-radius: 8px; padding: 14px 16px; margin: 24px 0;">
                <p style="font-size: 12px; line-height: 1.6; color: #475569; margin: 0;">
                  <strong>Lưu ý bảo mật:</strong> Liên kết có thời hạn sử dụng và chỉ được dùng một lần theo quy trình bảo mật của hệ thống. Nếu bạn không thực hiện yêu cầu này, hãy bỏ qua email. Mật khẩu hiện tại của bạn sẽ không thay đổi.
                </p>
              </div>

              <p style="font-size: 12px; line-height: 1.6; color: #64748b; margin-top: 24px; word-break: break-all;">
                Nếu nút trên không hoạt động, bạn có thể sao chép và dán liên kết sau vào trình duyệt:<br>
                <a href="{html_reset_url}" style="color: #2563EB; text-decoration: underline;">{html_reset_url}</a>
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #f8fafc; padding: 24px 32px; border-top: 1px solid #e2e8f0; text-align: center;">
              <p style="font-size: 13px; font-weight: 700; color: #163A70; margin: 0 0 4px 0;">
                HK Student Hub · Trường THPT Hương Khê – Hà Tĩnh
              </p>
              <p style="font-size: 11px; color: #64748b; margin: 0; font-style: italic;">
                “Kỷ cương số – Thi đua minh bạch – Đồng hành cùng học sinh”
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
    return subject, text_content, html_content


def send_password_reset_email(user, reset_url):
    """
    Gửi email hướng dẫn đặt lại mật khẩu cho người dùng.
    """
    if (
        settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend'
        and not settings.SMTP_EMAIL_CONFIGURED
    ):
        raise ImproperlyConfigured('Gmail SMTP sender and App Password are not configured.')

    subject, text_content, html_content = build_password_reset_email(user, reset_url)
    from_email = settings.DEFAULT_FROM_EMAIL

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=[user.email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)
    logger.info(f"Đã gửi email đặt lại mật khẩu đến: {user.email}")
    return True
