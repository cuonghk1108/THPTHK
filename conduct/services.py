from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.db import IntegrityError, transaction
from core.models import AuditLog, User
from .models import ViolationRecord, ViolationReviewHistory, ConductRule, SchoolClass, Student


def can_user_deduct_directly(user):
    """
    Kiểm tra quyền ghi nhận vi phạm và trừ điểm thi đua trực tiếp:
    - Quản trị viên (ADMIN, SUPER_ADMIN)
    - Người dùng được Admin cấp quyền chuyên biệt: can_verify_violations = True
    LƯU Ý QUAN TRỌNG:
    - Sao đỏ / Trực tuần TUYỆT ĐỐI không có quyền trừ điểm trực tiếp.
    - Học sinh TUYỆT ĐỐI không có quyền trừ điểm trực tiếp.
    - Giáo viên bộ môn (GVBM) TUYỆT ĐỐI không có quyền trừ điểm trực tiếp.
    """
    if not user or not user.is_authenticated:
        return False
    if getattr(user, 'is_admin', False) or getattr(user, 'is_super_admin', False) or user.role in [User.ROLE_ADMIN, User.ROLE_SUPER_ADMIN]:
        return True
    if user.role == User.ROLE_GVBM or getattr(user, 'is_gvbm', False):
        return False
    if getattr(user, 'is_sao_do', False) or getattr(user, 'is_active_red_star', False) or user.role in [User.ROLE_SAO_DO, User.ROLE_HOC_SINH]:
        return False
    if user.role == User.ROLE_DOAN_TRUONG or getattr(user, 'is_doan_truong', False):
        # Đoàn trường có toàn quyền nghiệp vụ nền nếp, xác minh vi phạm và trừ điểm
        return True
    return getattr(user, 'can_verify_violations', False)


def get_class_score_snapshot(school_class, occurred_at=None):
    """
    Lấy điểm thi đua hiện tại của lớp tại thời điểm xảy ra sự việc (ưu tiên kỳ Tuần).
    """
    from competition.models import ClassCompetitionScore
    from competition.services import get_or_create_week_for_date
    if occurred_at is None:
        occurred_at = timezone.now()
    period = get_or_create_week_for_date(occurred_at, school_class.academic_year)
    if period:
        score_obj = ClassCompetitionScore.objects.filter(
            competition_period=period,
            school_class=school_class
        ).first()
        if score_obj:
            return score_obj.total_score, period

    return None, period


def ensure_violation_week_open(school_class, occurred_at):
    from competition.services import get_or_create_week_for_date
    week = get_or_create_week_for_date(occurred_at, school_class.academic_year)
    if not week:
        raise ValueError('Ngày ghi nhận chưa thuộc tuần thi đua đã cấu hình; cần Admin kiểm tra lịch.')
    if week.is_locked:
        raise ValueError('Tuần thi đua đã chốt; cần Admin mở lại trước khi ghi nhận hoặc xác minh dữ liệu.')
    return week


@transaction.atomic
def create_violation_record(reporter, class_id, rule_id, student_id=None, occurred_at=None,
                            location='Khuôn viên trường', description='', evidence_image=None, evidence_notes='',
                            submission_key=None, direct_deduct=None):
    """
    Tạo bản ghi vi phạm nền nếp:
    - Nếu là Admin hoặc người được cấp quyền (hoặc direct_deduct=True):
      + Trạng thái: VERIFIED ngay lập tức, không qua bước chờ duyệt.
      + Trừ điểm thi đua trực tiếp ngay trong giao dịch.
      + Ghi nhận điểm trước và sau khi trừ.
      + Ghi nhận lịch sử thẩm định và AuditLog.
    - Nếu là Sao đỏ / vai trò thông thường (direct_deduct=False / None):
      + Trạng thái: PENDING (Chờ xác minh).
      + Điểm trừ: 0đ cho tới khi được thẩm định.
    """
    if False:
        pass

    is_direct = direct_deduct if direct_deduct is not None else can_user_deduct_directly(reporter)
    if is_direct and not can_user_deduct_directly(reporter):
        raise PermissionError("Tài khoản của bạn chưa được cấp quyền trừ điểm thi đua trực tiếp.")

    # Chống gửi trùng request (Idempotency)
    if submission_key:
        existing = ViolationRecord.objects.filter(reporter=reporter, submission_key=submission_key).first()
        if existing:
            existing._created_now = False
            return existing

    school_class = SchoolClass.objects.get(id=class_id)
    rule = ConductRule.objects.get(id=rule_id)
    student = Student.objects.get(id=student_id) if student_id else None

    if occurred_at is None:
        occurred_at = timezone.now()
    elif occurred_at > timezone.now() + timedelta(minutes=5):
        raise ValueError("Thời gian xảy ra vi phạm không thể ở tương lai. Vui lòng ghi nhận thời gian thực.")

    from competition.services import get_or_create_week_for_date
    competition_week = get_or_create_week_for_date(occurred_at, school_class.academic_year)
    apply_direct_deduction = bool(is_direct and competition_week and not competition_week.is_locked)

    score_before = None
    if apply_direct_deduction:
        score_before, _ = get_class_score_snapshot(school_class, occurred_at)
        initial_status = ViolationRecord.STATUS_VERIFIED
        points_to_deduct = rule.default_points_deducted
        verified_by_user = reporter
        verified_time = timezone.now()
        verification_note = f"{reporter.full_name or reporter.username} ghi nhận vi phạm và trừ điểm trực tiếp."
    else:
        initial_status = ViolationRecord.STATUS_PENDING
        points_to_deduct = Decimal('0.00')
        verified_by_user = None
        verified_time = None
        verification_note = (
            'Chờ xác minh: ngày ghi nhận chưa khớp duy nhất với tuần thi đua đang mở.'
            if is_direct and not apply_direct_deduction else ''
        )

    violation = ViolationRecord(
        school_class=school_class,
        student=student,
        student_name_snapshot=student.full_name if student else f"Tập thể {school_class.name}",
        rule=rule,
        occurred_at=occurred_at,
        location=location,
        description=description,
        reporter=reporter,
        submission_key=submission_key,
        status=initial_status,
        points_deducted=points_to_deduct,
        score_before=score_before,
        evidence_image=evidence_image,
        evidence_notes=evidence_notes,
        verified_by=verified_by_user,
        verified_at=verified_time,
        verification_notes=verification_note,
    )

    try:
        with transaction.atomic():
            violation.save()
    except IntegrityError:
        if not submission_key:
            raise
        existing = ViolationRecord.objects.filter(reporter=reporter, submission_key=submission_key).first()
        if existing is None:
            raise
        existing._created_now = False
        return existing

    violation._created_now = True

    if apply_direct_deduction:
        # Kích hoạt tính lại điểm thi đua tự động ngay trong cùng transaction
        from competition.services import recalculate_score_for_class_at_time
        recalculate_score_for_class_at_time(school_class, violation.occurred_at)

        score_after, _ = get_class_score_snapshot(school_class, violation.occurred_at)
        violation.score_after = score_after
        violation.save(update_fields=['score_after'])

        # Ghi lại lịch sử thẩm định
        ViolationReviewHistory.objects.create(
            violation=violation,
            performed_by=reporter,
            previous_status='NONE',
            new_status=ViolationRecord.STATUS_VERIFIED,
            points_applied=violation.points_deducted,
            score_before=score_before,
            score_after=score_after,
            reason="Xác nhận vi phạm và trừ điểm trực tiếp"
        )

        AuditLog.objects.create(
            user=reporter,
            action='DIRECT_DEDUCT',
            resource_type='VIOLATION',
            resource_id=violation.record_code,
            details=(
                f"Đoàn trường {reporter.username} ghi nhận vi phạm [{rule.code} - {rule.name}] "
                f"và trừ trực tiếp {violation.points_deducted}đ đối với {violation.student_name_snapshot} (Lớp {school_class.name}). "
                f"Điểm lớp: {score_before}đ -> {score_after}đ."
            )
        )

        # Kích hoạt cảnh báo sớm nếu có học sinh
        if violation.student:
            from alerts.services import evaluate_alerts_for_student
            evaluate_alerts_for_student(violation.student)
    else:
        review_context = (
            ' Chờ xác minh và rà soát lịch tuần trước khi tính điểm.'
            if is_direct and not apply_direct_deduction else ''
        )
        AuditLog.objects.create(
            user=reporter,
            action='CREATE',
            resource_type='VIOLATION',
            resource_id=violation.record_code,
            details=f"Ghi nhận vi phạm [{rule.code} - {rule.name}] đối với {violation.student_name_snapshot} (Lớp {school_class.name}).{review_context}"
        )

    # Tự động gửi email thông báo cho Đoàn trường (nhiều tài khoản đủ điều kiện)
    from .email import queue_violation_email
    queue_violation_email(violation)

    return violation


@transaction.atomic
def verify_violation(violation_id, user, new_status, adjusted_points=None, verification_notes='', reason=''):
    """
    Xác minh bản ghi vi phạm do Sao đỏ hoặc GV gửi lên. Chỉ Admin hoặc người được cấp quyền chuyên biệt mới được thực hiện.
    Trạng thái:
    - VERIFIED: Chấp thuận vi phạm, áp dụng điểm trừ mặc định từ rule hoặc adjusted_points
    - REJECTED: Bác bỏ vi phạm (không đủ căn cứ), điểm trừ = 0
    - ADJUSTED: Điều chỉnh mức độ / điểm trừ
    Sau khi xác minh, tự động tính lại điểm thi đua của lớp và kiểm tra cảnh báo sớm.
    """
    violation = ViolationRecord.objects.select_for_update().get(id=violation_id)
    ensure_violation_week_open(violation.school_class, violation.occurred_at)
    old_status = violation.status
    old_points = violation.points_deducted

    score_before, _ = get_class_score_snapshot(violation.school_class, violation.occurred_at)

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
    violation.score_before = score_before
    violation.save()

    # Kích hoạt tính lại điểm thi đua tự động nếu có kỳ thi đua phù hợp
    from competition.services import recalculate_score_for_class_at_time
    recalculate_score_for_class_at_time(violation.school_class, violation.occurred_at)

    score_after, _ = get_class_score_snapshot(violation.school_class, violation.occurred_at)
    violation.score_after = score_after
    violation.save(update_fields=['score_after'])

    # Ghi lại lịch sử thẩm định
    ViolationReviewHistory.objects.create(
        violation=violation,
        performed_by=user,
        previous_status=old_status,
        new_status=new_status,
        points_applied=violation.points_deducted,
        score_before=score_before,
        score_after=score_after,
        reason=reason or verification_notes or f"Chuyển trạng thái sang {new_status}"
    )

    AuditLog.objects.create(
        user=user,
        action='VERIFY',
        resource_type='VIOLATION',
        resource_id=violation.record_code,
        details=f"Xác minh vi phạm {violation.record_code}: {old_status} ({old_points}đ) -> {new_status} ({violation.points_deducted}đ). Điểm lớp: {score_before}đ -> {score_after}đ."
    )

    # Kích hoạt kiểm tra cảnh báo sớm nếu vi phạm được xác minh
    if new_status in [ViolationRecord.STATUS_VERIFIED, ViolationRecord.STATUS_ADJUSTED] and violation.student:
        from alerts.services import evaluate_alerts_for_student
        evaluate_alerts_for_student(violation.student)

    return violation


@transaction.atomic
def adjust_or_undo_violation(violation_id, user, action_type, reason, adjusted_points=None):
    """
    Quy trình điều chỉnh hoặc hoàn tác bản ghi vi phạm đã trừ điểm:
    - action_type == 'undo': Hủy bỏ vi phạm, trả lại điểm đã trừ (status -> REJECTED, points -> 0)
    - action_type == 'adjust': Điều chỉnh số điểm trừ thực tế (status -> ADJUSTED, points -> adjusted_points)
    Ghi nhận lịch sử thẩm định (ViolationReviewHistory), AuditLog và tự động tính lại điểm thi đua.
    """
    if not can_user_deduct_directly(user):
        raise PermissionError("Bạn không có quyền điều chỉnh hoặc hoàn tác bản ghi vi phạm này.")

    if not reason or not str(reason).strip():
        raise ValueError("Vui lòng cung cấp lý do điều chỉnh hoặc hoàn tác cụ thể.")

    violation = ViolationRecord.objects.select_for_update().get(id=violation_id)
    ensure_violation_week_open(violation.school_class, violation.occurred_at)
    old_status = violation.status
    old_points = violation.points_deducted

    score_before, _ = get_class_score_snapshot(violation.school_class, violation.occurred_at)

    if action_type == 'undo':
        new_status = ViolationRecord.STATUS_REJECTED
        new_points = Decimal('0.00')
        history_desc = f"Hoàn tác bản ghi vi phạm: {reason.strip()}"
        audit_action = 'UNDO_VIOLATION'
    elif action_type == 'adjust':
        if adjusted_points is None:
            raise ValueError("Vui lòng cung cấp mức điểm điều chỉnh mới.")
        new_status = ViolationRecord.STATUS_ADJUSTED
        new_points = Decimal(str(adjusted_points))
        history_desc = f"Điều chỉnh điểm trừ từ {old_points}đ sang {new_points}đ: {reason.strip()}"
        audit_action = 'ADJUST_VIOLATION'
    else:
        raise ValueError(f"Hành động không hợp lệ: {action_type}. Chỉ chấp nhận 'undo' hoặc 'adjust'.")

    violation.status = new_status
    violation.points_deducted = new_points
    violation.verified_by = user
    violation.verified_at = timezone.now()
    violation.verification_notes = history_desc
    violation.score_before = score_before
    violation.save()

    # Tính lại điểm thi đua
    from competition.services import recalculate_score_for_class_at_time
    recalculate_score_for_class_at_time(violation.school_class, violation.occurred_at)

    score_after, _ = get_class_score_snapshot(violation.school_class, violation.occurred_at)
    violation.score_after = score_after
    violation.save(update_fields=['score_after'])

    # Ghi nhận lịch sử thẩm định
    ViolationReviewHistory.objects.create(
        violation=violation,
        performed_by=user,
        previous_status=old_status,
        new_status=new_status,
        points_applied=new_points,
        score_before=score_before,
        score_after=score_after,
        reason=history_desc
    )

    # Ghi nhận AuditLog
    AuditLog.objects.create(
        user=user,
        action=audit_action,
        resource_type='VIOLATION',
        resource_id=violation.record_code,
        details=(
            f"{user.username} thực hiện [{audit_action}] trên bản ghi {violation.record_code}: "
            f"{old_status} ({old_points}đ) -> {new_status} ({new_points}đ). "
            f"Điểm lớp: {score_before}đ -> {score_after}đ. Lý do: {reason.strip()}"
        )
    )

    return violation, score_before, score_after


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
