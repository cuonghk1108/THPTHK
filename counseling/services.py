import re
from django.utils import timezone
from core.models import AuditLog
from .models import CounselingRequest, CounselingPrivateNote


CRITICAL_SAFETY_KEYWORDS = [
    r'tự tử', r'tự hại', r'muốn chết', r'cắt tay', r'kết liễu', r'không muốn sống',
    r'bị đánh hội đồng', r'đe dọa tính mạng', r'đe dọa giết', r'lạm dụng'
]


def check_for_safety_alerts(text):
    """Quét từ khóa nguy cơ an toàn để ưu tiên hỗ trợ khẩn cấp (không chuẩn đoán bệnh)"""
    lower_text = text.lower()
    for pattern in CRITICAL_SAFETY_KEYWORDS:
        if re.search(pattern, lower_text):
            return True
    return False


def submit_counseling_request(topic, content, preferred_channel='IN_PERSON', contact_info='',
                              preferred_schedule='', is_anonymous=False, alias_name='', student=None):
    """
    Gửi đề nghị hỗ trợ qua 'Góc sẻ chia'.
    Hoàn toàn tách biệt khỏi hệ thống thi đua và kỷ luật.
    """
    is_urgent = check_for_safety_alerts(content)
    safety_notes = "Nội dung có thể liên quan đến nguy cơ an toàn học đường/bản thân. Cần cán bộ chuyên môn ưu tiên liên hệ trực tiếp." if is_urgent else ""

    request_obj = CounselingRequest.objects.create(
        student=None if is_anonymous else student,
        is_anonymous=is_anonymous,
        alias_name=alias_name or ("Học sinh giấu tên" if is_anonymous else ""),
        topic=topic,
        content=content,
        preferred_channel=preferred_channel,
        contact_info=contact_info,
        preferred_schedule=preferred_schedule,
        status=CounselingRequest.STATUS_NEW,
        is_urgent_safety=is_urgent,
        safety_notes=safety_notes
    )

    # Không ghi chi tiết nội dung tâm sự vào AuditLog để bảo đảm tính riêng tư
    AuditLog.objects.create(
        user=student.user if (student and student.user) else None,
        action='CREATE',
        resource_type='COUNSELING_REQUEST',
        resource_id=request_obj.tracking_code,
        details=f"Đề nghị tư vấn tâm lý mới: Mã {request_obj.tracking_code} (Chủ đề: {request_obj.get_topic_display()})"
    )

    return request_obj


def update_counseling_status(request_id, counselor, new_status, scheduled_meeting=None):
    """
    Cán bộ tư vấn tâm lý tiếp nhận và cập nhật tiến trình hỗ trợ.
    """
    req = CounselingRequest.objects.get(id=request_id)
    req.status = new_status
    req.assigned_counselor = counselor
    if scheduled_meeting:
        req.scheduled_meeting = scheduled_meeting
    req.save()

    AuditLog.objects.create(
        user=counselor,
        action='UPDATE_STATUS',
        resource_type='COUNSELING_REQUEST',
        resource_id=req.tracking_code,
        details=f"Cán bộ {counselor.username} cập nhật trạng thái hồ sơ {req.tracking_code} sang {new_status}"
    )
    return req


def add_counseling_private_note(request_id, counselor, note_content, recommendation=''):
    """
    Lưu ghi chép chuyên môn riêng tư của tư vấn viên.
    Tuyệt đối không công khai cho học sinh khác hoặc giáo viên thông thường.
    """
    req = CounselingRequest.objects.get(id=request_id)
    note = CounselingPrivateNote.objects.create(
        request=req,
        counselor=counselor,
        note_content=note_content,
        recommendation=recommendation
    )
    return note
