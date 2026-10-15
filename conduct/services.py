from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from core.models import AuditLog, User
from .models import ViolationRecord, ViolationReviewHistory, ConductRule, SchoolClass, Student


def create_violation_record(reporter, class_id, rule_id, student_id=None, occurred_at=None,
                            location='Khuôn viên trường', description='', evidence_image=None, evidence_notes=''):
    """
    Tạo bản ghi vi phạm nền nếp nhanh (tối ưu cho Đội Sao đỏ hoặc GV).
    Mặc định trạng thái là PENDING (Chờ xác minh).
    KHÔNG tự động trừ điểm khi chưa xác minh!
    """
    school_class = SchoolClass.objects.get(id=class_id)
    rule = ConductRule.objects.get(id=rule_id)
    student = Student.objects.get(id=student_id) if student_id else None

    if occurred_at is None:
        occurred_at = timezone.now()

    violation = ViolationRecord(
        school_class=school_class,
        student=student,
        student_name_snapshot=student.full_name if student else f"Tập thể {school_class.name}",
        rule=rule,
        occurred_at=occurred_at,
        location=location,
        description=description,
        reporter=reporter,
        status=ViolationRecord.STATUS_PENDING,
        points_deducted=Decimal('0.00'),  # 0 điểm cho tới khi xác minh!
        evidence_image=evidence_image,
        evidence_notes=evidence_notes,
    )
    violation.save()

    AuditLog.objects.create(
        user=reporter,
        action='CREATE',
        resource_type='VIOLATION',
        resource_id=violation.record_code,
        details=f"Ghi nhận vi phạm [{rule.code} - {rule.name}] đối với {violation.student_name_snapshot} (Lớp {school_class.name})"
    )

    return violation


@transaction.atomic
def verify_violation(violation_id, user, new_status, adjusted_points=None, verification_notes='', reason=''):
    """
    Xác minh bản ghi vi phạm. Chỉ Đoàn trường hoặc Quản trị viên mới có quyền thực hiện.
    Trạng thái:
    - VERIFIED: Chấp thuận vi phạm, áp dụng điểm trừ mặc định từ rule hoặc adjusted_points
    - REJECTED: Bác bỏ vi phạm (không đủ căn cứ), điểm trừ = 0
    - ADJUSTED: Điều chỉnh mức độ / điểm trừ
    Sau khi xác minh, tự động tính lại điểm thi đua của lớp và kiểm tra cảnh báo sớm.
    """
    violation = ViolationRecord.objects.select_for_update().get(id=violation_id)
    old_status = violation.status

    if new_status in [ViolationRecord.STATUS_VERIFIED, ViolationRecord.STATUS_ADJUSTED]:
        if adjusted_points is not None:
            violation.points_deducted = Decimal(str(adjusted_points))
        else:
            violation.points_deducted = violation.rule.default_points_deducted
    else:
        # Nếu REJECTED hoặc PENDING
        violation.points_deducted = Decimal('0.00')

    violation.status = new_status
    violation.verified_by = user
    violation.verified_at = timezone.now()
    if verification_notes:
        violation.verification_notes = verification_notes
    violation.save()

    # Ghi lại lịch sử thẩm định
    ViolationReviewHistory.objects.create(
        violation=violation,
        performed_by=user,
        previous_status=old_status,
        new_status=new_status,
        points_applied=violation.points_deducted,
        reason=reason or verification_notes or f"Chuyển trạng thái sang {new_status}"
    )

    AuditLog.objects.create(
        user=user,
        action='VERIFY',
        resource_type='VIOLATION',
        resource_id=violation.record_code,
        details=f"Xác minh vi phạm {violation.record_code}: {old_status} -> {new_status}, trừ {violation.points_deducted}đ"
    )

    # Kích hoạt tính lại điểm thi đua tự động nếu có kỳ thi đua phù hợp
    from competition.services import recalculate_score_for_class_at_time
    recalculate_score_for_class_at_time(violation.school_class, violation.occurred_at)

    # Kích hoạt kiểm tra cảnh báo sớm nếu vi phạm được xác minh
    if new_status in [ViolationRecord.STATUS_VERIFIED, ViolationRecord.STATUS_ADJUSTED] and violation.student:
        from alerts.services import evaluate_alerts_for_student
        evaluate_alerts_for_student(violation.student)

    return violation


def submit_violation_appeal(violation_id, user, reason):
    """
    Học sinh hoặc GVCN gửi yêu cầu giải trình / khiếu nại đối với bản ghi vi phạm.
    """
    violation = ViolationRecord.objects.get(id=violation_id)
    violation.status = ViolationRecord.STATUS_APPEALING
    violation.appeal_reason = reason
    violation.appeal_submitted_by = user
    violation.appeal_submitted_at = timezone.now()
    violation.save()

    ViolationReviewHistory.objects.create(
        violation=violation,
        performed_by=user,
        previous_status=violation.status,
        new_status=ViolationRecord.STATUS_APPEALING,
        points_applied=violation.points_deducted,
        reason=f"Yêu cầu giải trình/khiếu nại từ {user.full_name or user.username}: {reason}"
    )

    AuditLog.objects.create(
        user=user,
        action='APPEAL',
        resource_type='VIOLATION',
        resource_id=violation.record_code,
        details=f"Gửi khiếu nại vi phạm {violation.record_code}: {reason}"
    )

    return violation
