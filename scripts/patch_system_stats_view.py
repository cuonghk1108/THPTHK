import sys

sys.stdout.reconfigure(encoding='utf-8')

p = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\core\views.py'
with open(p, 'rb') as f:
    raw = f.read()

is_crlf = b'\r\n' in raw
text = raw.decode('utf-8').replace('\r\n', '\n')

old_part1 = """            data = {
                'scope': 'school',
                'violations_today': ViolationRecord.objects.filter(occurred_at__date=today).count(),
                'violations_pending': ViolationRecord.objects.filter(status=ViolationRecord.STATUS_PENDING).count(),
                'violations_verified_week': ViolationRecord.objects.filter(
                    status__in=verified_statuses,
                    **current_week_filter,
                ).count(),
                'violations_breakdown': {
                    'pending': ViolationRecord.objects.filter(status=ViolationRecord.STATUS_PENDING).count(),
                    'verified': ViolationRecord.objects.filter(status__in=verified_statuses).count(),
                    'rejected': ViolationRecord.objects.filter(status=ViolationRecord.STATUS_REJECTED).count(),
                    'appealed': ViolationRecord.objects.filter(status=ViolationRecord.STATUS_APPEALING).count(),
                },
                'red_star_stats': {
                    'pending': RedStarReport.objects.filter(status=RedStarReport.STATUS_PENDING).count(),
                    'verified': RedStarReport.objects.filter(status=RedStarReport.STATUS_VERIFIED).count(),
                    'rejected': RedStarReport.objects.filter(status=RedStarReport.STATUS_REJECTED).count(),
                    'active_reporters': RedStarAssignment.objects.filter(status=RedStarAssignment.STATUS_ACTIVE).values('student').distinct().count(),
                },
                'alerts_active': EarlyWarningAlert.objects.filter(status__in=active_alert_statuses).count(),
                'total_classes': SchoolClass.objects.filter(is_active=True).count(),
                'total_students': Student.objects.filter(status='STUDYING').count(),
                'total_teachers': total_teachers,
                'pending_accounts': pending_accounts,
                'average_score': round(float(average_score), 1) if average_score is not None else None,
                'current_week': current_period.display_week_label if hasattr(current_period, 'display_week_label') else (current_period.name if current_period else None),
                'current_week_number': current_period.week_number if current_period else 7,
                'current_semester': current_semester_period.name if current_semester_period else (current_period.semester.name if current_period and current_period.semester else 'Học kỳ I'),
                'current_semester_number': current_period.semester.semester_number if (current_period and current_period.semester_id) else (current_semester_period.semester.semester_number if current_semester_period and current_semester_period.semester_id else 1),
                'current_week_status': get_period_status(current_period)['display'] if current_period else None,
                'user_role': user.role,
                'user_role_display': user.get_role_display(),
            }
            return Response(data)"""

new_part1 = """            # Tối ưu: Gom các truy vấn count thành aggregate có điều kiện
            v_agg = ViolationRecord.objects.aggregate(
                today=Count('id', filter=Q(occurred_at__date=today)),
                pending=Count('id', filter=Q(status=ViolationRecord.STATUS_PENDING)),
                verified=Count('id', filter=Q(status__in=verified_statuses)),
                rejected=Count('id', filter=Q(status=ViolationRecord.STATUS_REJECTED)),
                appealed=Count('id', filter=Q(status=ViolationRecord.STATUS_APPEALING)),
                verified_week=Count('id', filter=Q(status__in=verified_statuses, **current_week_filter)),
            )

            rs_agg = RedStarReport.objects.aggregate(
                pending=Count('id', filter=Q(status=RedStarReport.STATUS_PENDING)),
                verified=Count('id', filter=Q(status=RedStarReport.STATUS_VERIFIED)),
                rejected=Count('id', filter=Q(status=RedStarReport.STATUS_REJECTED)),
            )

            u_agg = User.objects.aggregate(
                teachers=Count('id', filter=Q(role__in=[User.ROLE_GVCN, User.ROLE_GVBM], account_status=User.STATUS_APPROVED)),
                pending=Count('id', filter=Q(account_status=User.STATUS_PENDING)),
            )

            active_reporters = RedStarAssignment.objects.filter(status=RedStarAssignment.STATUS_ACTIVE).values('student').distinct().count()
            alerts_count = EarlyWarningAlert.objects.filter(status__in=active_alert_statuses).count()
            classes_count = SchoolClass.objects.filter(is_active=True).count()
            students_count = Student.objects.filter(status='STUDYING').count()

            data = {
                'scope': 'school',
                'violations_today': v_agg['today'],
                'violations_pending': v_agg['pending'],
                'violations_verified_week': v_agg['verified_week'],
                'violations_breakdown': {
                    'pending': v_agg['pending'],
                    'verified': v_agg['verified'],
                    'rejected': v_agg['rejected'],
                    'appealed': v_agg['appealed'],
                },
                'red_star_stats': {
                    'pending': rs_agg['pending'],
                    'verified': rs_agg['verified'],
                    'rejected': rs_agg['rejected'],
                    'active_reporters': active_reporters,
                },
                'alerts_active': alerts_count,
                'total_classes': classes_count,
                'total_students': students_count,
                'total_teachers': u_agg['teachers'],
                'pending_accounts': u_agg['pending'],
                'average_score': round(float(average_score), 1) if average_score is not None else None,
                'current_week': current_period.display_week_label if hasattr(current_period, 'display_week_label') else (current_period.name if current_period else None),
                'current_week_number': current_period.week_number if current_period else 7,
                'current_semester': current_semester_period.name if current_semester_period else (current_period.semester.name if current_period and current_period.semester else 'Học kỳ I'),
                'current_semester_number': current_period.semester.semester_number if (current_period and current_period.semester_id) else (current_semester_period.semester.semester_number if current_semester_period and current_semester_period.semester_id else 1),
                'current_week_status': get_period_status(current_period)['display'] if current_period else None,
                'user_role': user.role,
                'user_role_display': user.get_role_display(),
            }
            cache.set(cache_key, data, timeout=20)
            return Response(data)"""

# Add cache lookup at beginning of get(self, request)
old_get_head = """    def get(self, request):
        from conduct.models import Student, ViolationRecord, SchoolClass
        from competition.models import ClassCompetitionScore, CompetitionPeriod
        from alerts.models import EarlyWarningAlert
        user = request.user"""

new_get_head = """    def get(self, request):
        from conduct.models import Student, ViolationRecord, SchoolClass
        from competition.models import ClassCompetitionScore, CompetitionPeriod
        from alerts.models import EarlyWarningAlert
        from django.core.cache import cache
        from django.db.models import Count, Q, Avg
        user = request.user
        if not user.is_active or user.account_status != User.STATUS_APPROVED:
            return Response({'error': 'Tài khoản chưa được kích hoạt.'}, status=status.HTTP_403_FORBIDDEN)

        cache_key = f"sys_stats_{user.id}_{user.role}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)"""

old_auth_check = """        if not user.is_active or user.account_status != User.STATUS_APPROVED:
            return Response({'error': 'Tài khoản chưa được kích hoạt.'}, status=status.HTTP_403_FORBIDDEN)"""

assert old_get_head in text, "old_get_head not found"
text = text.replace(old_get_head, new_get_head, 1)

# Remove the duplicated auth check right after
text = text.replace(new_get_head + "\n" + old_auth_check, new_get_head, 1)

assert old_part1 in text, "old_part1 not found"
text = text.replace(old_part1, new_part1, 1)

if is_crlf:
    text = text.replace('\n', '\r\n')

with open(p, 'wb') as f:
    f.write(text.encode('utf-8'))

print("[OK] Optimized SystemStatsAPIView successfully!")
