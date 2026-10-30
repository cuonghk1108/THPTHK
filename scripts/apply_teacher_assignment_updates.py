import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"

# 1. Update conduct/views.py
conduct_views_path = os.path.join(BASE_DIR, "conduct", "views.py")
with open(conduct_views_path, "r", encoding="utf-8") as f:
    cv_content = f.read()

target_cv = """        # 1. GVCN
        hr_teacher = sclass.homeroom_teacher
        hr_data = None
        if hr_teacher:
            hr_assign = HomeroomAssignment.objects.filter(school_class=sclass, teacher=hr_teacher, is_active=True).first()
            hr_subj = ''
            if hasattr(hr_teacher, 'teacher_profile') and hr_teacher.teacher_profile:
                hr_subj = hr_teacher.teacher_profile.subject
            hr_data = {
                'id': hr_teacher.id,
                'full_name': hr_teacher.full_name or hr_teacher.username,
                'username': hr_teacher.username,
                'phone': hr_teacher.phone or '',
                'subject': hr_subj,
                'start_date': str(hr_assign.start_date) if hr_assign else None,
                'notes': hr_assign.notes if hr_assign else ''
            }

        # 2. GVBM
        active_tcas = TeacherClassAssignment.objects.filter(
            school_class=sclass, is_active=True
        ).select_related('teacher', 'teacher__teacher_profile').order_by('subject', 'teacher__full_name')

        subject_teachers_data = []
        for tca in active_tcas:
            t = tca.teacher
            subject_teachers_data.append({
                'assignment_id': tca.id,
                'teacher_id': t.id,
                'full_name': t.full_name or t.username,
                'username': t.username,
                'phone': t.phone or '',
                'subject': tca.subject,
                'start_date': str(tca.start_date),
                'is_active': tca.is_active
            })"""

replacement_cv = """        # 1. GVCN
        SUBJECT_MAP = {
            'TOAN': 'Toán học', 'VAN': 'Ngữ văn', 'ANH': 'Tiếng Anh',
            'LY': 'Vật lý', 'HOA': 'Hóa học', 'SINH': 'Sinh học',
            'SU': 'Lịch sử', 'DIA': 'Địa lý', 'GDCD': 'GDCD/GDKT&PL',
            'TIN': 'Tin học', 'CN': 'Công nghệ', 'TD': 'Giáo dục thể chất',
            'QP': 'Giáo dục QP-AN', 'AM_NHAC': 'Âm nhạc', 'MY_THUAT': 'Mỹ thuật',
            'HDTN': 'Hoạt động trải nghiệm'
        }
        hr_teacher = sclass.homeroom_teacher
        hr_data = None
        if hr_teacher:
            hr_assign = HomeroomAssignment.objects.filter(school_class=sclass, teacher=hr_teacher, is_active=True).first()
            hr_subj = ''
            if hasattr(hr_teacher, 'teacher_profile') and hr_teacher.teacher_profile:
                hr_subj = hr_teacher.teacher_profile.subject
            hr_data = {
                'id': hr_teacher.id,
                'full_name': hr_teacher.full_name or hr_teacher.username,
                'username': hr_teacher.username,
                'email': hr_teacher.email or '',
                'phone': hr_teacher.phone or '',
                'subject': hr_subj,
                'subject_display': SUBJECT_MAP.get(hr_subj, hr_subj),
                'start_date': str(hr_assign.start_date) if hr_assign else None,
                'notes': hr_assign.notes if hr_assign else ''
            }

        # 2. GVBM
        active_tcas = TeacherClassAssignment.objects.filter(
            school_class=sclass, is_active=True
        ).select_related('teacher', 'teacher__teacher_profile').order_by('subject', 'teacher__full_name')

        subject_teachers_data = []
        for tca in active_tcas:
            t = tca.teacher
            subject_teachers_data.append({
                'assignment_id': tca.id,
                'teacher_id': t.id,
                'teacher_name': t.full_name or t.username,
                'full_name': t.full_name or t.username,
                'teacher_username': t.username,
                'username': t.username,
                'teacher_email': t.email or '',
                'email': t.email or '',
                'teacher_phone': t.phone or '',
                'phone': t.phone or '',
                'subject': tca.subject,
                'subject_display': SUBJECT_MAP.get(tca.subject, tca.subject),
                'start_date': str(tca.start_date),
                'assigned_at': str(tca.start_date),
                'is_active': tca.is_active
            })"""

# Normalize line endings for replacement
norm_cv = cv_content.replace("\r\n", "\n")
norm_target_cv = target_cv.replace("\r\n", "\n")
norm_replacement_cv = replacement_cv.replace("\r\n", "\n")

if norm_target_cv in norm_cv:
    norm_cv = norm_cv.replace(norm_target_cv, norm_replacement_cv)
    # Write back
    with open(conduct_views_path, "w", encoding="utf-8") as f:
        f.write(norm_cv)
    print("SUCCESS: conduct/views.py updated.")
else:
    print("WARNING: target_cv not found in conduct/views.py. Checking if already updated...")
    if "SUBJECT_MAP" in norm_cv and "assigned_teachers" in norm_cv:
        print("INFO: conduct/views.py already contains updated assigned_teachers.")
    else:
        print("ERROR: Could not locate target in conduct/views.py")
