# -*- coding: utf-8 -*-
import logging
import uuid
from datetime import timedelta
from html import escape

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.validators import validate_email, ValidationError
from django.db import transaction, models
from django.utils import timezone

from core.models import User, AuditLog, Notification
from .models import ViolationEmailNotification

logger = logging.getLogger(__name__)


def get_eligible_union_recipients():
    """
    Lấy danh sách các tài khoản người dùng thuộc Đoàn trường đủ điều kiện nhận email:
    - Có vai trò Đoàn trường (role == User.ROLE_DOAN_TRUONG) hoặc được cấp quyền xác minh (can_verify_violations=True).
    - Trạng thái tài khoản đã được Admin phê duyệt (account_status == User.STATUS_APPROVED).
    - Đang hoạt động (is_active=True).
    - Có địa chỉ email hợp lệ (không rỗng và đúng định dạng).
    - Loại bỏ trùng lặp địa chỉ email.
    """
    candidates = User.objects.filter(
        models.Q(role=User.ROLE_DOAN_TRUONG) | models.Q(can_verify_violations=True),
        account_status=User.STATUS_APPROVED,
        is_active=True,
    ).exclude(email='').exclude(email__isnull=True).order_by('id')

    valid_recipients = []
    seen_emails = set()

    for user in candidates:
        email = (user.email or '').strip().lower()
        if not email or email in seen_emails:
            continue
        try:
            validate_email(email)
            seen_emails.add(email)
            valid_recipients.append(user)
        except ValidationError:
            logger.warning("Bỏ qua email không hợp lệ của người dùng Đoàn trường %s: %s", user.username, user.email)

    return valid_recipients


def get_school_union_notification_email():
    """
    Lấy địa chỉ email Đoàn trường đại diện từ danh sách tài khoản Đoàn trường hợp lệ.
    """
    recipients = get_eligible_union_recipients()
    if recipients:
        return recipients[0].email
    return ""


def build_violation_email_content(violation, detail_url):
    """
    Soạn thảo tiêu đề, nội dung văn bản thuần và HTML email thông báo vi phạm
    gửi đến các tài khoản Đoàn trường theo đúng quy chuẩn của HK Student Hub.
    """
    subject = "[HK Student Hub] Thông báo ghi nhận vi phạm và trừ điểm thi đua"

    class_name = violation.school_class.name if violation.school_class else "Toàn trường"
    student_name = (
        violation.student.full_name
        if violation.student
        else (violation.student_name_snapshot or f"Tập thể lớp {class_name}")
    )
    rule_name = violation.rule.name if violation.rule else "N/A"
    rule_code = violation.rule.code if violation.rule else ""
    reporter_name = (
        violation.reporter.full_name or violation.reporter.username
        if violation.reporter else "Hệ thống"
    )
    reporter_role = violation.reporter.get_role_display() if violation.reporter else ""

    occurred_time_str = (
        timezone.localtime(violation.occurred_at).strftime("%d/%m/%Y %H:%M")
        if violation.occurred_at else "N/A"
    )
    created_time_str = (
        timezone.localtime(violation.created_at).strftime("%d/%m/%Y %H:%M")
        if violation.created_at else timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
    )

    points_str = f"-{float(violation.points_deducted):.2f}đ" if violation.points_deducted > 0 else "0.00đ"

    score_snapshot_str = ""
    if violation.score_after is not None:
        if violation.score_before is not None:
            score_snapshot_str = f"{float(violation.score_before):.2f}đ ➔ {float(violation.score_after):.2f}đ"
        else:
            score_snapshot_str = f"{float(violation.score_after):.2f}đ"

    # Trạng thái minh chứng
    has_evidence = bool(violation.evidence_image)
    if has_evidence:
        evidence_status_text = "Có minh chứng đính kèm (Lưu trữ bảo mật trong hệ thống)"
        if violation.evidence_notes:
            evidence_status_text += f" – Ghi chú: {violation.evidence_notes}"
    else:
        evidence_status_text = "Không có minh chứng đính kèm"

    if violation.status == 'VERIFIED':
        status_text = "Đã tiếp nhận thành công (Trừ điểm thi đua trực tiếp)."
        status_color = "#15803d"
    elif violation.status == 'PENDING':
        status_text = "Đã tiếp nhận – Đang chờ xác minh."
        status_color = "#b45309"
    elif violation.status == 'ADJUSTED':
        status_text = "Đã điều chỉnh điểm vi phạm."
        status_color = "#7e22ce"
    else:
        status_text = violation.get_status_display()
        status_color = "#163A70"

    text_content = (
        "Kính gửi Ban Chấp hành Đoàn trường,\n\n"
        "Hệ thống HK Student Hub – Trường THPT Hương Khê vừa tiếp nhận một bản ghi vi phạm và trừ điểm thi đua mới.\n\n"
        "THÔNG TIN CHI TIẾT:\n"
        f"- Hệ thống: HK Student Hub\n"
        "- Đơn vị: Trường THPT Hương Khê – Hà Tĩnh\n"
        f"- Mã bản ghi: {violation.record_code}\n"
        f"- Thời gian xảy ra: {occurred_time_str}\n"
        f"- Thời gian tiếp nhận: {created_time_str}\n"
        f"- Học sinh vi phạm: {student_name}\n"
        f"- Lớp: {class_name}\n"
        f"- Nội dung vi phạm: {rule_name} [{rule_code}]\n"
        f"- Mô tả sự việc: {violation.description or 'Không có mô tả chi tiết'}\n"
        f"- Điểm bị trừ: {points_str}\n"
    )
    if score_snapshot_str:
        text_content += f"- Điểm thi đua của Chi đoàn sau khi trừ: {score_snapshot_str}\n"

    text_content += (
        f"- Người thực hiện ghi nhận: {reporter_name} ({reporter_role})\n"
        f"- Trạng thái minh chứng: {evidence_status_text}\n"
        f"- Trạng thái xử lý: {status_text}\n\n"
        "ĐƯỜNG DẪN XEM CHI TIẾT VÀ MINH CHỨNG (Yêu cầu đăng nhập tài khoản có thẩm quyền):\n"
        f"{detail_url}\n\n"
        "* Lời nhắc: Vui lòng đăng nhập vào hệ thống HK Student Hub bằng tài khoản Đoàn trường để kiểm tra chi tiết bản ghi và minh chứng bảo mật.\n\n"
        "Trân trọng,\n"
        "HK Student Hub\n"
        "Trường THPT Hương Khê – Hà Tĩnh\n"
        "“Kỷ cương số – Thi đua minh bạch – Đồng hành cùng học sinh”\n"
    )

    html_values = {
        'subject': escape(subject),
        'record_code': escape(violation.record_code),
        'student_name': escape(student_name),
        'class_name': escape(class_name),
        'rule_name': escape(rule_name),
        'rule_code': escape(rule_code),
        'occurred_time': escape(occurred_time_str),
        'created_time': escape(created_time_str),
        'reporter_name': escape(reporter_name),
        'reporter_role': escape(reporter_role),
        'description': escape(violation.description or 'Không có mô tả chi tiết'),
        'points': escape(points_str),
        'score_snapshot': escape(score_snapshot_str),
        'evidence_status': escape(evidence_status_text),
        'status_text': escape(status_text),
        'detail_url': escape(detail_url, quote=True),
    }

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html_values['subject']}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f7fb; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f4f7fb; padding: 30px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 620px; background-color: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 10px 25px rgba(22, 58, 112, 0.08);">
          
          <!-- Header -->
          <tr>
            <td style="background-color: #163A70; padding: 26px 32px; text-align: left;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                  <td>
                    <div style="font-size: 11px; font-weight: 800; color: #93c5fd; letter-spacing: 0.1em; text-transform: uppercase;">TRƯỜNG THPT HƯƠNG KHÊ – HÀ TĨNH</div>
                    <div style="font-size: 20px; font-weight: 900; color: #ffffff; margin-top: 4px;">HK Student Hub · Thông báo Đoàn trường</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding: 32px 32px 24px 32px;">
              <h2 style="font-size: 18px; font-weight: 800; color: #163A70; margin-top: 0; margin-bottom: 12px;">Kính gửi Ban Chấp hành Đoàn trường,</h2>
              <p style="font-size: 14px; line-height: 1.6; color: #334155; margin-bottom: 20px;">
                Hệ thống <strong>HK Student Hub</strong> vừa tiếp nhận một bản ghi vi phạm nền nếp và cập nhật điểm thi đua mới. Chi tiết sự việc như sau:
              </p>

              <!-- Violation Data Table -->
              <table role="presentation" width="100%" style="border-collapse: collapse; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; margin-bottom: 24px;">
                <tr>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 700; color: #64748b; width: 38%; border-bottom: 1px solid #e2e8f0;">Mã bản ghi vi phạm:</td>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 800; color: #163A70; border-bottom: 1px solid #e2e8f0; font-family: monospace;">{html_values['record_code']}</td>
                </tr>
                <tr>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 700; color: #64748b; border-bottom: 1px solid #e2e8f0;">Học sinh vi phạm:</td>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 700; color: #0f172a; border-bottom: 1px solid #e2e8f0;">{html_values['student_name']}</td>
                </tr>
                <tr>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 700; color: #64748b; border-bottom: 1px solid #e2e8f0;">Chi đoàn / Lớp:</td>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 700; color: #163A70; border-bottom: 1px solid #e2e8f0;">Lớp {html_values['class_name']}</td>
                </tr>
                <tr>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 700; color: #64748b; border-bottom: 1px solid #e2e8f0;">Lỗi vi phạm:</td>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 700; color: #e11d48; border-bottom: 1px solid #e2e8f0;">{html_values['rule_name']} <span style="font-size: 11px; color: #64748b; font-weight: normal;">[{html_values['rule_code']}]</span></td>
                </tr>
                <tr>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 700; color: #64748b; border-bottom: 1px solid #e2e8f0;">Thời gian xảy ra:</td>
                  <td style="padding: 10px 16px; font-size: 13px; color: #334155; border-bottom: 1px solid #e2e8f0;">{html_values['occurred_time']}</td>
                </tr>
                <tr>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 700; color: #64748b; border-bottom: 1px solid #e2e8f0;">Thời gian tiếp nhận:</td>
                  <td style="padding: 10px 16px; font-size: 13px; color: #334155; border-bottom: 1px solid #e2e8f0;">{html_values['created_time']}</td>
                </tr>
                <tr>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 700; color: #64748b; border-bottom: 1px solid #e2e8f0;">Người ghi nhận:</td>
                  <td style="padding: 10px 16px; font-size: 13px; color: #334155; border-bottom: 1px solid #e2e8f0;">{html_values['reporter_name']} <span style="font-size: 11px; color: #64748b;">({html_values['reporter_role']})</span></td>
                </tr>
                <tr>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 700; color: #64748b; border-bottom: 1px solid #e2e8f0;">Mô tả sự việc:</td>
                  <td style="padding: 10px 16px; font-size: 13px; color: #475569; border-bottom: 1px solid #e2e8f0; font-style: italic;">{html_values['description']}</td>
                </tr>
                <tr>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 700; color: #64748b; border-bottom: 1px solid #e2e8f0;">Điểm bị trừ:</td>
                  <td style="padding: 10px 16px; font-size: 14px; font-weight: 800; color: #e11d48; border-bottom: 1px solid #e2e8f0;">{html_values['points']}</td>
                </tr>"""

    if score_snapshot_str:
        html_content += f"""
                <tr>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 700; color: #64748b; border-bottom: 1px solid #e2e8f0;">Điểm thi đua lớp:</td>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 800; color: #163A70; border-bottom: 1px solid #e2e8f0;">{html_values['score_snapshot']}</td>
                </tr>"""

    html_content += f"""
                <tr>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 700; color: #64748b; border-bottom: 1px solid #e2e8f0;">Trạng thái minh chứng:</td>
                  <td style="padding: 10px 16px; font-size: 13px; color: #334155; border-bottom: 1px solid #e2e8f0;">{html_values['evidence_status']}</td>
                </tr>
                <tr>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 700; color: #64748b;">Trạng thái xử lý:</td>
                  <td style="padding: 10px 16px; font-size: 13px; font-weight: 800; color: {status_color};">{html_values['status_text']}</td>
                </tr>
              </table>

              <!-- CTA Button -->
              <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 24px 0 20px 0;">
                <tr>
                  <td align="center" style="border-radius: 12px; background-color: #163A70;">
                    <a href="{html_values['detail_url']}" target="_blank" style="font-size: 13px; font-weight: 800; color: #ffffff; text-decoration: none; padding: 13px 26px; display: inline-block; border-radius: 12px; letter-spacing: 0.02em;">
                      XEM CHI TIẾT VI PHẠM & MINH CHỨNG
                    </a>
                  </td>
                </tr>
              </table>

              <p style="font-size: 12px; line-height: 1.6; color: #64748b; margin: 0;">
                * <strong>Lời nhắc:</strong> Vui lòng đăng nhập vào hệ thống HK Student Hub bằng tài khoản Đoàn trường để kiểm tra chi tiết bản ghi và minh chứng bảo mật.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #f8fafc; padding: 20px 32px; border-top: 1px solid #e2e8f0; text-align: center;">
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


from concurrent.futures import ThreadPoolExecutor

_email_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="hk_email_worker")

def dispatch_email_async(notification_id):
    """
    Kích hoạt gửi email bất đồng bộ qua thread pool để không làm treo giao diện
    và kiểm soát tài nguyên tránh thread exhaustion dưới tải cao (bounded concurrency).
    Trong môi trường kiểm thử (test suite), bỏ qua để tối ưu tốc độ test.
    """
    import sys
    is_testing = 'test' in sys.argv or getattr(settings, 'IS_TESTING', False)
    if is_testing:
        return

    _email_executor.submit(send_violation_email, notification_id)


def queue_violation_email(violation):
    """
    Tạo bản ghi hàng đợi outbox (ViolationEmailNotification) cho tất cả tài khoản Đoàn trường đủ điều kiện:
    - Có vai trò Đoàn trường hoặc được phân quyền xác minh vi phạm.
    - Đã được Admin phê duyệt (STATUS_APPROVED) và đang hoạt động (is_active=True).
    - Có email hợp lệ.
    Nếu không có tài khoản nào hợp lệ, ghi nhận lỗi rõ ràng và tạo Notification cho Admin; không giả lập thành công.
    Chống gửi trùng cho cùng địa chỉ trong cùng một sự kiện vi phạm.
    """
    recipients = get_eligible_union_recipients()
    frontend_base = getattr(settings, 'FRONTEND_BASE_URL', 'https://edumentor.io.vn').rstrip('/')
    detail_url = f"{frontend_base}/?tab=conduct&violation={violation.record_code}"

    subject, text_content, html_content = build_violation_email_content(violation, detail_url)

    if not recipients:
        error_msg = 'Hệ thống không tìm thấy tài khoản Đoàn trường nào đủ điều kiện (đã phê duyệt, đang hoạt động và có email hợp lệ) để nhận thông báo.'
        logger.warning(
            "Không gửi email thông báo cho vi phạm %s: %s",
            violation.record_code,
            error_msg,
        )
        email_notif = ViolationEmailNotification.objects.create(
            violation=violation,
            recipient_user=None,
            recipient_email='',
            status=ViolationEmailNotification.STATUS_SKIPPED,
            subject=subject,
            body_text=text_content,
            body_html=html_content,
            idempotency_key=uuid.uuid4(),
            last_error=error_msg,
        )

        # Thông báo cảnh báo cho tất cả Quản trị viên hệ thống
        admin_users = User.objects.filter(
            models.Q(role__in=[User.ROLE_ADMIN, User.ROLE_SUPER_ADMIN]) | models.Q(is_superuser=True),
            account_status=User.STATUS_APPROVED,
            is_active=True,
        ).distinct()
        for adm in admin_users:
            Notification.objects.create(
                recipient=adm,
                notification_type=Notification.TYPE_CONDUCT,
                title=f"Cảnh báo Email: Chưa có tài khoản Đoàn trường ({violation.record_code})",
                message=(
                    f"Bản ghi vi phạm {violation.record_code} đã được lưu thành công nhưng chưa thể gửi email "
                    f"thông báo do hệ thống chưa có tài khoản Đoàn trường nào được duyệt có email hợp lệ. "
                    f"Vui lòng vào trang Quản trị để duyệt tài khoản hoặc cập nhật email cho cán bộ Đoàn trường."
                ),
                link=f"/?tab=conduct&violation={violation.record_code}"
            )

        return [email_notif]

    notifications = []
    created_ids = []

    for user in recipients:
        user_email = (user.email or '').strip().lower()
        # Chống gửi trùng email cho cùng một địa chỉ trong cùng một sự kiện vi phạm
        existing = ViolationEmailNotification.objects.filter(
            violation=violation,
            recipient_email=user_email
        ).first()

        if existing:
            notifications.append(existing)
            continue

        email_notif = ViolationEmailNotification.objects.create(
            violation=violation,
            recipient_user=user,
            recipient_email=user_email,
            status=ViolationEmailNotification.STATUS_PENDING,
            subject=subject,
            body_text=text_content,
            body_html=html_content,
            idempotency_key=uuid.uuid4(),
        )
        notifications.append(email_notif)
        created_ids.append(email_notif.id)

    # Sau khi database transaction commit thành công, kích hoạt gửi
    if created_ids:
        def _dispatch_all():
            for nid in created_ids:
                dispatch_email_async(nid)

        transaction.on_commit(_dispatch_all)

    return notifications


def send_violation_email(notification_id):
    """
    Gửi một email đang chờ trong outbox.
    Lỗi SMTP được ghi nhận an toàn, kích hoạt retry có giới hạn (exponential backoff);
    tuyệt đối không ảnh hưởng đến bản ghi vi phạm hay làm trừ điểm lần thứ hai.
    """
    with transaction.atomic():
        notif = (
            ViolationEmailNotification.objects.select_for_update()
            .filter(id=notification_id)
            .first()
        )
        if notif is None:
            return False
        if notif.status == ViolationEmailNotification.STATUS_SENT:
            return True
        if notif.status != ViolationEmailNotification.STATUS_PENDING:
            return False
        if notif.next_attempt_at and notif.next_attempt_at > timezone.now():
            return False
        if not notif.recipient_email:
            notif.status = ViolationEmailNotification.STATUS_SKIPPED
            notif.last_error = 'Chưa có địa chỉ email Đoàn trường hợp lệ.'
            notif.save(update_fields=['status', 'last_error', 'updated_at'])
            return False

        notif.status = ViolationEmailNotification.STATUS_SENDING
        notif.attempt_count += 1
        notif.last_attempt_at = timezone.now()
        notif.save(update_fields=['status', 'attempt_count', 'last_attempt_at', 'updated_at'])

    from_email = settings.DEFAULT_FROM_EMAIL

    try:
        msg = EmailMultiAlternatives(
            subject=notif.subject,
            body=notif.body_text,
            from_email=from_email,
            to=[notif.recipient_email],
        )
        if notif.body_html:
            msg.attach_alternative(notif.body_html, "text/html")
        msg.send(fail_silently=False)

        notif.status = ViolationEmailNotification.STATUS_SENT
        notif.sent_at = timezone.now()
        notif.last_error = ''
        notif.save(update_fields=['status', 'sent_at', 'last_error', 'updated_at'])
        logger.info("SMTP accepted violation email notification id=%s to %s", notif.id, notif.recipient_email)
        return True
    except Exception as e:
        error_message = str(e)
        for secret in (settings.EMAIL_HOST_PASSWORD, settings.EMAIL_HOST_USER):
            if secret:
                error_message = error_message.replace(secret, '[redacted]')
        error_msg = f'{type(e).__name__}: {error_message[:400]}'
        can_retry = notif.attempt_count <= notif.max_retries
        notif.status = (
            ViolationEmailNotification.STATUS_PENDING
            if can_retry else ViolationEmailNotification.STATUS_FAILED
        )
        if can_retry:
            retry_seconds = min(3600, 60 * (2 ** (notif.attempt_count - 1)))
            notif.next_attempt_at = timezone.now() + timedelta(seconds=retry_seconds)
        notif.last_error = error_msg
        notif.save(update_fields=['status', 'next_attempt_at', 'last_error', 'updated_at'])
        logger.error(
            "SMTP delivery failed for violation email id=%s to %s (%s)",
            notif.id,
            notif.recipient_email,
            type(e).__name__,
        )
        return False


def send_test_union_email(recipient_email=None, requested_by=None):
    """
    Gửi email kiểm thử cấu hình SMTP đến địa chỉ Đoàn trường hoặc địa chỉ được chỉ định.
    """
    target_email = recipient_email
    if not target_email:
        eligible = get_eligible_union_recipients()
        if eligible:
            target_email = eligible[0].email
    target_email = (target_email or '').strip()

    if not target_email:
        return False, 'Không tìm thấy địa chỉ email Đoàn trường hợp lệ nào để gửi thử.', None

    html_recipient_email = escape(target_email)
    requester_name = (
        requested_by.full_name or requested_by.username
        if requested_by else 'Quản trị viên'
    )
    html_requester_name = escape(requester_name)
    subject = "[HK Student Hub] Kiểm tra kết nối cấu hình Email Đoàn trường"
    text_content = (
        "Xin chào Quản trị viên và Ban Chấp hành Đoàn trường,\n\n"
        "Đây là email kiểm tra kết nối từ hệ thống HK Student Hub – Trường THPT Hương Khê.\n"
        "Nếu bạn nhận được email này, cấu hình gửi email thông báo vi phạm và trừ điểm đã hoạt động chính xác!\n\n"
        "Trân trọng,\n"
        "HK Student Hub\n"
        "Trường THPT Hương Khê – Hà Tĩnh\n"
    )
    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head><meta charset="UTF-8"><title>{escape(subject)}</title></head>
<body style="font-family: sans-serif; background-color: #f4f7fb; padding: 30px 15px;">
  <div style="max-width: 560px; margin: 0 auto; background: #fff; border-radius: 14px; border: 1px solid #e2e8f0; padding: 28px;">
    <h2 style="color: #163A70; margin-top: 0;">Kiểm tra kết nối Email Đoàn trường</h2>
    <p style="color: #334155; font-size: 14px; line-height: 1.6;">
      Hệ thống <strong>HK Student Hub – Trường THPT Hương Khê</strong> đã gửi thành công email kiểm thử đến địa chỉ <strong>{html_recipient_email}</strong>.
    </p>
    <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 12px; margin: 20px 0; color: #065f46; font-size: 13px; font-weight: 600;">
      ✓ Kết nối SMTP và địa chỉ nhận email đã được xác minh thành công!
    </div>
    <p style="color: #64748b; font-size: 12px; margin-bottom: 0;">
      Yêu cầu thực hiện bởi: {html_requester_name} vào lúc {timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M:%S')}.
    </p>
  </div>
</body>
</html>"""

    notif = ViolationEmailNotification.objects.create(
        violation=None,
        recipient_user=None,
        recipient_email=target_email,
        is_test=True,
        status=ViolationEmailNotification.STATUS_PENDING,
        subject=subject,
        body_text=text_content,
        body_html=html_content,
        idempotency_key=uuid.uuid4(),
    )
    notif.status = ViolationEmailNotification.STATUS_SENDING
    notif.attempt_count = 1
    notif.last_attempt_at = timezone.now()
    notif.save(update_fields=['status', 'attempt_count', 'last_attempt_at', 'updated_at'])

    success = False
    try:
        with get_connection(
            backend=settings.EMAIL_BACKEND,
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            use_ssl=settings.EMAIL_USE_SSL,
            timeout=settings.EMAIL_TIMEOUT,
        ) as connection:
            connection.open()
            message = EmailMultiAlternatives(
                subject=notif.subject,
                body=notif.body_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[notif.recipient_email],
                connection=connection,
            )
            message.attach_alternative(notif.body_html, 'text/html')
            message.send(fail_silently=False)
        notif.status = ViolationEmailNotification.STATUS_SENT
        notif.sent_at = timezone.now()
        notif.last_error = ''
        notif.save(update_fields=['status', 'sent_at', 'last_error', 'updated_at'])
        logger.info("SMTP accepted test email notification id=%s", notif.id)
        success = True
    except Exception as e:
        safe_error = str(e)
        for secret in (settings.EMAIL_HOST_PASSWORD, settings.EMAIL_HOST_USER):
            if secret:
                safe_error = safe_error.replace(secret, '[redacted]')
        notif.status = ViolationEmailNotification.STATUS_FAILED
        notif.last_error = f'{type(e).__name__}: {safe_error[:400]}'
        notif.save(update_fields=['status', 'last_error', 'updated_at'])
        logger.error("SMTP test email failed (%s)", type(e).__name__)

    notif.refresh_from_db()
    message = (
        'SMTP đã chấp nhận email kiểm thử; trạng thái này không xác nhận thư đã vào hộp thư người nhận.'
        if success else
        f'Không gửi được email kiểm thử: {notif.last_error}'
    )
    if requested_by:
        AuditLog.objects.create(
            user=requested_by,
            action='SEND_TEST_EMAIL',
            resource_type='SYSTEM',
            resource_id=str(notif.id),
            details=f"Gửi email kiểm thử tới {target_email}. Kết quả: {'Thành công' if success else 'Thất bại'}"
        )
    return success, message, notif


def send_reflection_notification_email(reflection):
    """
    Gửi email thông báo cho GVCN phụ trách lớp khi có phản ánh mới từ GVBM.
    Đảm bảo nếu lỗi gửi email thì KHÔNG làm mất phản ánh hay ném ngoại lệ.
    """
    homeroom_teacher = reflection.school_class.homeroom_teacher
    if not homeroom_teacher or not homeroom_teacher.email:
        return False

    try:
        validate_email(homeroom_teacher.email)
    except ValidationError:
        return False

    subject = f"[HK Student Hub] Phản ánh nền nếp mới - Lớp {reflection.school_class.name} ({reflection.reflection_code})"
    target_name = reflection.student_name_snapshot or f"Tập thể {reflection.school_class.name}"
    teacher_name = reflection.teacher.full_name or reflection.teacher.username
    occurred_str = timezone.localtime(reflection.occurred_at).strftime('%H:%M ngày %d/%m/%Y')

    body_text = (
        f"Kính gửi Thầy/Cô {homeroom_teacher.full_name or homeroom_teacher.username},\n\n"
        f"Giáo viên bộ môn {teacher_name} vừa gửi phản ánh mới liên quan đến lớp {reflection.school_class.name}.\n\n"
        f"- Mã phản ánh: {reflection.reflection_code}\n"
        f"- Đối tượng: {target_name}\n"
        f"- Loại phản ánh: {reflection.get_reflection_type_display()}\n"
        f"- Thời gian xảy ra: {occurred_str}\n"
        f"- Mức độ: {reflection.get_urgency_display()}\n"
        f"- Nội dung: {reflection.content}\n\n"
        f"Vui lòng đăng nhập hệ thống HK Student Hub để xem chi tiết và xử lý theo quy chế thi đua.\n\n"
        f"Trân trọng,\nHK Student Hub - THPT Hương Khê\n"
    )

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=body_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[homeroom_teacher.email],
        )
        message.send(fail_silently=True)
        return True
    except Exception as exc:
        logger.warning("Không thể gửi email thông báo phản ánh tới GVCN %s: %s", homeroom_teacher.email, exc)
        return False

