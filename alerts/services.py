from datetime import timedelta
from django.utils import timezone
from django.db.models import Count
from core.models import AuditLog
from conduct.models import ViolationRecord, Student, SchoolClass
from .models import EarlyWarningRule, EarlyWarningAlert, HomeroomIntervention


def evaluate_alerts_for_student(student):
    """
    Rà soát các vi phạm ĐÃ XÁC MINH của học sinh để phát hiện nguy cơ vượt ngưỡng:
    - Đi muộn >= 3 lần trong 7 ngày
    - Một hành vi vi phạm lặp lại nhiều lần
    Chỉ tổng hợp từ dữ liệu ĐÃ ĐƯỢC XÁC MINH.
    """
    now = timezone.now()
    active_rules = EarlyWarningRule.objects.filter(is_active=True)

    for rule in active_rules:
        window_start = now - timedelta(days=rule.time_window_days)

        if rule.rule_type == EarlyWarningRule.TYPE_STUDENT_LATE:
            # Lọc các lỗi đi muộn đã xác minh
            late_records = ViolationRecord.objects.filter(
                student=student,
                occurred_at__gte=window_start,
                status__in=[ViolationRecord.STATUS_VERIFIED, ViolationRecord.STATUS_ADJUSTED]
            ).filter(
                rule__name__icontains='muộn'
            )

            count = late_records.count()
            if count >= rule.threshold:
                details_list = [
                    f"- {rec.occurred_at.strftime('%d/%m/%Y %H:%M')}: {rec.rule.name} tại {rec.location}"
                    for rec in late_records
                ]
                details_text = (
                    f"Học sinh có {count} lần đi học muộn trong vòng {rule.time_window_days} ngày qua (ngưỡng: {rule.threshold} lần).\n"
                    f"Chi tiết các lần vi phạm đã xác minh:\n" + "\n".join(details_list)
                )

                create_or_update_student_alert(
                    rule=rule,
                    student=student,
                    title=f"Lưu ý: Học sinh {student.full_name} đi học muộn {count} lần trong tuần",
                    details=details_text,
                    severity=EarlyWarningAlert.SEVERITY_MEDIUM if count < 5 else EarlyWarningAlert.SEVERITY_HIGH
                )

        elif rule.rule_type == EarlyWarningRule.TYPE_STUDENT_REPEAT:
            # Lọc lỗi bất kỳ lặp lại >= ngưỡng
            repeat_rules = ViolationRecord.objects.filter(
                student=student,
                occurred_at__gte=window_start,
                status__in=[ViolationRecord.STATUS_VERIFIED, ViolationRecord.STATUS_ADJUSTED]
            ).values('rule__name').annotate(cnt=Count('id')).filter(cnt__gte=rule.threshold)

            for item in repeat_rules:
                rule_name = item['rule__name']
                cnt = item['cnt']
                details_text = f"Hành vi [{rule_name}] lặp lại {cnt} lần trong {rule.time_window_days} ngày qua."
                create_or_update_student_alert(
                    rule=rule,
                    student=student,
                    title=f"Cảnh báo: Vi phạm lặp lại [{rule_name}] ({cnt} lần) - {student.full_name}",
                    details=details_text,
                    severity=EarlyWarningAlert.SEVERITY_MEDIUM
                )


def create_or_update_student_alert(rule, student, title, details, severity):
    """Tạo hoặc cập nhật cảnh báo sớm gửi riêng cho GVCN phụ trách lớp"""
    homeroom_teacher = student.school_class.homeroom_teacher

    # Tìm cảnh báo đang mở (NEW hoặc RECEIVED hoặc IN_PROGRESS)
    existing_alert = EarlyWarningAlert.objects.filter(
        rule=rule,
        student=student,
        status__in=[EarlyWarningAlert.STATUS_NEW, EarlyWarningAlert.STATUS_RECEIVED, EarlyWarningAlert.STATUS_IN_PROGRESS]
    ).first()

    if existing_alert:
        existing_alert.details = details
        existing_alert.severity = severity
        existing_alert.save()
        return existing_alert
    else:
        new_alert = EarlyWarningAlert.objects.create(
            rule=rule,
            school_class=student.school_class,
            student=student,
            alert_title=title,
            details=details,
            severity=severity,
            status=EarlyWarningAlert.STATUS_NEW,
            homeroom_teacher=homeroom_teacher
        )
        return new_alert


def record_gvcn_intervention(alert_id, teacher, action_taken, outcome='', status='COMPLETED'):
    """
    GVCN ghi nhận biện pháp hỗ trợ và kết quả theo dõi.
    """
    alert = EarlyWarningAlert.objects.get(id=alert_id)
    
    intervention = HomeroomIntervention.objects.create(
        alert=alert,
        teacher=teacher,
        action_taken=action_taken,
        outcome=outcome,
        status=status
    )

    if status == 'COMPLETED':
        alert.status = EarlyWarningAlert.STATUS_RESOLVED
        alert.resolved_at = timezone.now()
    else:
        alert.status = EarlyWarningAlert.STATUS_IN_PROGRESS
    alert.save()

    AuditLog.objects.create(
        user=teacher,
        action='INTERVENTION',
        resource_type='ALERT',
        resource_id=str(alert.id),
        details=f"GVCN {teacher.username} ghi nhận can thiệp cho cảnh báo: {alert.alert_title}"
    )

    return intervention
