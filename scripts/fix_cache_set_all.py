import sys

# 1. Fix competition/views.py
with open('competition/views.py', 'rb') as f:
    comp_text = f.read().decode('utf-8').replace('\r\n', '\n')

old_comp_ret = '''        return Response({
            'period': self.get_serializer(period).data,
            'prev_period': {
                'id': previous_period.id,
                'name': previous_period.name,
                'start_date': str(previous_period.start_date),
                'end_date': str(previous_period.end_date)
            } if previous_period else None,
            'summary': {
                'total_classes': total_classes,
                'top_class': top_class,
                'highest_score': highest_score,
                'improved_classes_count': improved_classes,
                'worsened_classes_count': worsened_classes,
                'total_violations_in_period': total_violations,
                'last_updated': last_updated_time,
                'is_locked': period.is_locked,
                'locked_at': period.locked_at.strftime('%d/%m/%Y %H:%M') if period.locked_at else None,
                'locked_by': period.locked_by.full_name if period.locked_by else None
            },
            'period_status': state,
            'scores': serializer.data
        })'''

new_comp_ret = '''        res_data = {
            'period': self.get_serializer(period).data,
            'prev_period': {
                'id': previous_period.id,
                'name': previous_period.name,
                'start_date': str(previous_period.start_date),
                'end_date': str(previous_period.end_date)
            } if previous_period else None,
            'summary': {
                'total_classes': total_classes,
                'top_class': top_class,
                'highest_score': highest_score,
                'improved_classes_count': improved_classes,
                'worsened_classes_count': worsened_classes,
                'total_violations_in_period': total_violations,
                'last_updated': last_updated_time,
                'is_locked': period.is_locked,
                'locked_at': period.locked_at.strftime('%d/%m/%Y %H:%M') if period.locked_at else None,
                'locked_by': period.locked_by.full_name if period.locked_by else None
            },
            'period_status': state,
            'scores': serializer.data
        }
        cache.set(cache_key, res_data, timeout=30)
        return Response(res_data)'''

assert old_comp_ret in comp_text, 'old_comp_ret not found in competition/views.py'
comp_text = comp_text.replace(old_comp_ret, new_comp_ret, 1)

with open('competition/views.py', 'w', encoding='utf-8') as f:
    f.write(comp_text)
print('Successfully added cache.set in competition/views.py scores()!')

# 2. Fix core/views.py
with open('core/views.py', 'rb') as f:
    core_text = f.read().decode('utf-8').replace('\r\n', '\n')

old_gvcn_ret = '''            return Response({
                'scope': 'homeroom',
                'my_class_count': homeroom_classes.count(),
                'my_class_names': list(homeroom_classes.values_list('name', flat=True)),
                'my_class_students': Student.objects.filter(school_class__in=homeroom_classes, status='STUDYING').count(),
                'my_class_violations_pending': violations.filter(status=ViolationRecord.STATUS_PENDING).count(),
                'my_class_violations_verified': violations.filter(status__in=verified_statuses).count(),
                'my_class_alerts': active_alerts.count(),
                'class_score_info': class_score_info,
                'user_role': user.role,
                'user_role_display': user.get_role_display(),
            })'''

new_gvcn_ret = '''            data = {
                'scope': 'homeroom',
                'my_class_count': homeroom_classes.count(),
                'my_class_names': list(homeroom_classes.values_list('name', flat=True)),
                'my_class_students': Student.objects.filter(school_class__in=homeroom_classes, status='STUDYING').count(),
                'my_class_violations_pending': violations.filter(status=ViolationRecord.STATUS_PENDING).count(),
                'my_class_violations_verified': violations.filter(status__in=verified_statuses).count(),
                'my_class_alerts': active_alerts.count(),
                'class_score_info': class_score_info,
                'user_role': user.role,
                'user_role_display': user.get_role_display(),
            }
            cache.set(cache_key, data, timeout=20)
            return Response(data)'''

assert old_gvcn_ret in core_text, 'old_gvcn_ret not found in core/views.py'
core_text = core_text.replace(old_gvcn_ret, new_gvcn_ret, 1)

old_student_ret = '''            return Response({
                'scope': 'student',
                'profile_available': True,
                'student_name': student.full_name,
                'student_code': student.student_code,
                'student_class': student.school_class.name if student.school_class_id else '',
                'my_violations_verified': own_violations.filter(status__in=verified_statuses).count(),
                'my_violations_pending': own_violations.filter(status=ViolationRecord.STATUS_PENDING).count(),
                'class_score_info': class_score_info,
                'user_role': user.role,
                'user_role_display': user.get_role_display(),
            })'''

new_student_ret = '''            data = {
                'scope': 'student',
                'profile_available': True,
                'student_name': student.full_name,
                'student_code': student.student_code,
                'student_class': student.school_class.name if student.school_class_id else '',
                'my_violations_verified': own_violations.filter(status__in=verified_statuses).count(),
                'my_violations_pending': own_violations.filter(status=ViolationRecord.STATUS_PENDING).count(),
                'class_score_info': class_score_info,
                'user_role': user.role,
                'user_role_display': user.get_role_display(),
            }
            cache.set(cache_key, data, timeout=20)
            return Response(data)'''

assert old_student_ret in core_text, 'old_student_ret not found in core/views.py'
core_text = core_text.replace(old_student_ret, new_student_ret, 1)

with open('core/views.py', 'w', encoding='utf-8') as f:
    f.write(core_text)
print('Successfully added cache.set in core/views.py for GVCN and Student!')
