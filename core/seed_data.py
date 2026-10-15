from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from core.models import User, AcademicYear, Semester, SystemSetting, AuditLog
from conduct.models import SchoolClass, Student, Teacher, ConductRuleCategory, ConductRule, ViolationRecord, ViolationReviewHistory
from competition.models import ScoreCriterion, CompetitionPeriod, ClassCompetitionScore
from alerts.models import EarlyWarningRule, EarlyWarningAlert, HomeroomIntervention
from counseling.models import CounselingRequest, CounselingPrivateNote


def seed_system_data():
    """
    Khởi tạo dữ liệu nền tảng và dữ liệu mẫu thực nghiệm cho TRƯỜNG THPT HƯƠNG KHÊ – HÀ TĨNH.
    Dữ liệu được đánh dấu là DỮ LIỆU THỬ NGHIỆM PHỤC VỤ NGHIỆM THU.
    """
    # 1. Cấu hình hệ thống & Năm học
    year, _ = AcademicYear.objects.get_or_create(
        name='2026-2027',
        defaults={
            'start_date': date(2026, 9, 5),
            'end_date': date(2027, 5, 30),
            'is_current': True
        }
    )
    semester, _ = Semester.objects.get_or_create(
        academic_year=year,
        semester_number=1,
        defaults={
            'name': 'Học kỳ I',
            'start_date': date(2026, 9, 5),
            'end_date': date(2027, 1, 15),
            'is_current': True
        }
    )

    SystemSetting.objects.get_or_create(
        key='SCHOOL_NAME',
        defaults={'value': 'TRƯỜNG THPT HƯƠNG KHÊ – HÀ TĨNH', 'description': 'Tên trường chính thức'}
    )
    SystemSetting.objects.get_or_create(
        key='APP_SLOGAN',
        defaults={'value': 'Kỷ cương số – Thi đua minh bạch – Đồng hành cùng học sinh', 'description': 'Thông điệp hệ thống'}
    )
    SystemSetting.objects.get_or_create(
        key='DEFAULT_BASE_POINTS',
        defaults={'value': '100.0', 'description': 'Điểm khởi đầu mỗi kỳ thi đua tuần'}
    )

    # 2. Tạo các tài khoản mẫu cho đầy đủ 7 vai trò
    # A. Admin
    admin_user, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'full_name': 'Quản trị viên Hệ thống',
            'email': 'admin@thpthuongkhe.edu.vn',
            'role': User.ROLE_ADMIN,
            'is_staff': True,
            'is_superuser': True,
            'can_verify_violations': True,
            'can_view_counseling': False # Mặc định không xem tư vấn nhạy cảm!
        }
    )
    admin_user.set_password('admin_password_2026')
    admin_user.save()

    # B. Ban Giám hiệu
    bgh_user, _ = User.objects.get_or_create(
        username='bgh.huongkhe',
        defaults={
            'full_name': 'Thầy Phan Thanh Toàn (BGH)',
            'email': 'bgh@thpthuongkhe.edu.vn',
            'role': User.ROLE_BGH,
            'is_staff': True,
            'can_verify_violations': True
        }
    )
    bgh_user.set_password('bgh_password_2026')
    bgh_user.save()

    # C. Đoàn trường
    doan_user, _ = User.objects.get_or_create(
        username='doantruong.hk',
        defaults={
            'full_name': 'Thầy Trần Văn Đoàn (Bí thư Đoàn)',
            'email': 'doantruong@thpthuongkhe.edu.vn',
            'role': User.ROLE_DOAN_TRUONG,
            'is_staff': True,
            'can_verify_violations': True
        }
    )
    doan_user.set_password('doan_password_2026')
    doan_user.save()

    # D. Giáo viên chủ nhiệm
    gvcn_10a1, _ = User.objects.get_or_create(
        username='gvcn.10a1',
        defaults={
            'full_name': 'Cô Nguyễn Thị Mai',
            'email': 'mai.gvcn10a1@thpthuongkhe.edu.vn',
            'role': User.ROLE_GVCN,
            'is_staff': True
        }
    )
    gvcn_10a1.set_password('gvcn_password_2026')
    gvcn_10a1.save()

    gvcn_11a2, _ = User.objects.get_or_create(
        username='gvcn.11a2',
        defaults={
            'full_name': 'Thầy Lê Văn Hùng',
            'email': 'hung.gvcn11a2@thpthuongkhe.edu.vn',
            'role': User.ROLE_GVCN,
            'is_staff': True
        }
    )
    gvcn_11a2.set_password('gvcn_password_2026')
    gvcn_11a2.save()

    # E. Giáo viên bộ môn
    gvbm_user, _ = User.objects.get_or_create(
        username='gvbm.toan',
        defaults={
            'full_name': 'Thầy Võ Hoàng Nam (GV Toán)',
            'email': 'nam.toan@thpthuongkhe.edu.vn',
            'role': User.ROLE_GVBM,
            'is_staff': False
        }
    )
    gvbm_user.set_password('gvbm_password_2026')
    gvbm_user.save()

    # F. Đội Sao đỏ
    saodo_user, _ = User.objects.get_or_create(
        username='saodo.tuan1',
        defaults={
            'full_name': 'Em Hoàng Minh Thắng (Đội trưởng Sao đỏ)',
            'email': 'thang.saodo@thpthuongkhe.edu.vn',
            'role': User.ROLE_SAO_DO,
            'is_staff': False
        }
    )
    saodo_user.set_password('saodo_password_2026')
    saodo_user.save()

    # G. Học sinh
    student_user, _ = User.objects.get_or_create(
        username='hocsinh.nam',
        defaults={
            'full_name': 'Nguyễn Văn Nam',
            'email': 'nam.hk261001@thpthuongkhe.edu.vn',
            'role': User.ROLE_HOC_SINH,
            'is_staff': False
        }
    )
    student_user.set_password('hocsinh_password_2026')
    student_user.save()

    # H. Chuyên viên tư vấn tâm lý (Được cấp quyền chuyên biệt)
    tamly_user, _ = User.objects.get_or_create(
        username='tamly.huongkhe',
        defaults={
            'full_name': 'Cô Đặng Thùy Linh (Tư vấn học đường)',
            'email': 'tamly@thpthuongkhe.edu.vn',
            'role': User.ROLE_CHUYEN_VIEN_TAM_LY,
            'is_staff': True,
            'can_view_counseling': True # Quyền chuyên biệt vào Góc sẻ chia!
        }
    )
    tamly_user.set_password('tamly_password_2026')
    tamly_user.save()

    # 3. Lớp học và Chi đoàn THPT Hương Khê
    classes_data = [
        ('10A1', 10, gvcn_10a1, 42, 'P.101 - Nhà A'),
        ('10A2', 10, None, 40, 'P.102 - Nhà A'),
        ('10A3', 10, None, 41, 'P.103 - Nhà A'),
        ('11A1', 11, None, 39, 'P.201 - Nhà B'),
        ('11A2', 11, gvcn_11a2, 43, 'P.202 - Nhà B'),
        ('11A3', 11, None, 40, 'P.203 - Nhà B'),
        ('12A1', 12, None, 38, 'P.301 - Nhà C'),
        ('12A2', 12, None, 41, 'P.302 - Nhà C'),
        ('12A3', 12, None, 39, 'P.303 - Nhà C'),
    ]
    created_classes = {}
    for name, grade, teacher, cnt, room in classes_data:
        cls_obj, _ = SchoolClass.objects.get_or_create(
            name=name,
            academic_year=year,
            defaults={
                'grade': grade,
                'homeroom_teacher': teacher,
                'student_count': cnt,
                'room_number': room,
                'union_branch_name': f"Chi đoàn {name}"
            }
        )
        created_classes[name] = cls_obj

    # 4. Học sinh mẫu
    s_nam, _ = Student.objects.get_or_create(
        student_code='HK26-1001',
        defaults={
            'user': student_user,
            'full_name': 'Nguyễn Văn Nam',
            'date_of_birth': date(2010, 5, 14),
            'gender': 'M',
            'school_class': created_classes['10A1'],
            'is_union_member': True,
            'is_red_star': False,
            'parent_phone': '0912345678',
            'status': 'STUDYING'
        }
    )
    s_hoa, _ = Student.objects.get_or_create(
        student_code='HK26-1002',
        defaults={
            'full_name': 'Trần Thị Mỹ Hoa',
            'date_of_birth': date(2010, 8, 20),
            'gender': 'F',
            'school_class': created_classes['10A1'],
            'is_union_member': True,
            'is_red_star': True,
            'status': 'STUDYING'
        }
    )
    s_tuan, _ = Student.objects.get_or_create(
        student_code='HK26-1101',
        defaults={
            'full_name': 'Phạm Quốc Tuấn',
            'date_of_birth': date(2009, 3, 11),
            'gender': 'M',
            'school_class': created_classes['11A2'],
            'is_union_member': True,
            'is_red_star': False,
            'status': 'STUDYING'
        }
    )
    s_linh, _ = Student.objects.get_or_create(
        student_code='HK26-1201',
        defaults={
            'full_name': 'Đinh Phương Linh',
            'date_of_birth': date(2008, 11, 2),
            'gender': 'F',
            'school_class': created_classes['12A1'],
            'is_union_member': True,
            'status': 'STUDYING'
        }
    )

    # 5. Danh mục nhóm nội quy và quy định nền nếp
    cat_time, _ = ConductRuleCategory.objects.get_or_create(
        name='Chuyên cần & Giờ giấc',
        defaults={'description': 'Quy định giờ giấc ra vào cổng và lớp học', 'icon': 'clock', 'order': 1}
    )
    cat_attire, _ = ConductRuleCategory.objects.get_or_create(
        name='Nền nếp & Tác phong',
        defaults={'description': 'Đồng phục, thẻ học sinh và tác phong sư phạm', 'icon': 'user-check', 'order': 2}
    )
    cat_discipline, _ = ConductRuleCategory.objects.get_or_create(
        name='Học tập & Kỷ luật lớp học',
        defaults={'description': 'Trật tự, sử dụng thiết bị và chấp hành quy định lớp', 'icon': 'book-open', 'order': 3}
    )
    cat_hygiene, _ = ConductRuleCategory.objects.get_or_create(
        name='Vệ sinh & Môi trường',
        defaults={'description': 'Trực nhật, bảo vệ cảnh quan trường học', 'icon': 'trash-2', 'order': 4}
    )
    cat_safety, _ = ConductRuleCategory.objects.get_or_create(
        name='An toàn học đường & Giao thông',
        defaults={'description': 'Đội mũ bảo hiểm, phòng chống bạo lực và chất cấm', 'icon': 'shield-alert', 'order': 5}
    )

    rules_data = [
        (cat_time, 'VP-01', 'Đi học muộn sau tiếng trống vào học', Decimal('2.00'), 'LOW', 'Có mặt sau 7h00 sáng hoặc 13h30 chiều'),
        (cat_time, 'VP-02', 'Nghỉ học không có giấy xin phép hợp lệ', Decimal('5.00'), 'MEDIUM', 'Không có đơn của phụ huynh'),
        (cat_time, 'VP-03', 'Trốn tiết hoặc tự ý ra khỏi trường trong giờ học', Decimal('5.00'), 'MEDIUM', 'Bỏ tiết ra ngoài cổng trường'),
        (cat_attire, 'VP-04', 'Không mặc đúng đồng phục quy định', Decimal('2.00'), 'LOW', 'Không mặc áo đồng phục hoặc quần tối màu'),
        (cat_attire, 'VP-05', 'Không đeo thẻ học sinh trong giờ học', Decimal('1.00'), 'LOW', 'Thiếu thẻ nhận diện học sinh'),
        (cat_attire, 'VP-06', 'Đầu tóc nhuộm màu nổi bật, tác phong không phù hợp', Decimal('2.00'), 'LOW', 'Nhuộm tóc sáng màu hoặc cạo hình'),
        (cat_discipline, 'VP-07', 'Sử dụng điện thoại di động trong giờ học không phép', Decimal('5.00'), 'MEDIUM', 'Sử dụng máy cho mục đích cá nhân khi chưa được GV cho phép'),
        (cat_discipline, 'VP-08', 'Gây mất trật tự, làm ảnh hưởng giờ học', Decimal('2.00'), 'LOW', 'Nói chuyện riêng, đùa nghịch bị GV nhắc nhở'),
        (cat_discipline, 'VP-09', 'Sử dụng thuốc lá hoặc thuốc lá điện tử', Decimal('10.00'), 'CRITICAL', 'Nghiêm cấm tuyệt đối theo Luật PCTHTL'),
        (cat_hygiene, 'VP-10', 'Không trực nhật hoặc để lớp học bẩn', Decimal('3.00'), 'LOW', 'Chưa lau bảng, quét lớp hoặc đổ rác'),
        (cat_hygiene, 'VP-11', 'Vứt rác bừa bãi trong khuôn viên trường', Decimal('2.00'), 'LOW', 'Xả rác không đúng nơi quy định'),
        (cat_safety, 'VP-12', 'Điều khiển xe máy điện/xe gắn máy không đội mũ bảo hiểm', Decimal('5.00'), 'HIGH', 'Vi phạm ATGT cổng trường'),
    ]
    created_rules = {}
    for cat, code, name, pts, sev, desc in rules_data:
        r_obj, _ = ConductRule.objects.get_or_create(
            code=code,
            defaults={
                'category': cat,
                'name': name,
                'default_points_deducted': pts,
                'severity': sev,
                'description': desc,
                'is_active': True
            }
        )
        created_rules[code] = r_obj

    # 6. Biểu điểm thi đua
    ScoreCriterion.objects.get_or_create(
        academic_year=year,
        name='Quy chế thi đua nền nếp Chi đoàn THPT Hương Khê 2026-2027',
        defaults={
            'initial_base_points': Decimal('100.00'),
            'min_score': Decimal('0.00'),
            'max_score': Decimal('150.00'),
            'is_approved': True,
            'approved_by': bgh_user,
            'effective_from': date(2026, 9, 5),
            'effective_to': date(2027, 5, 30),
            'description': 'Mỗi tuần Chi đoàn khởi điểm 100 điểm. Trừ điểm theo lỗi vi phạm đã xác minh; cộng điểm phong trào Đoàn.'
        }
    )

    # 7. Kỳ thi đua: Tuần 7 (Hiện tại)
    today = timezone.now().date()
    start_week = today - timedelta(days=today.weekday()) # Thứ 2
    end_week = start_week + timedelta(days=6) # Chủ nhật
    period, _ = CompetitionPeriod.objects.get_or_create(
        name='Tuần 7 - Học kỳ I (2026-2027)',
        defaults={
            'period_type': CompetitionPeriod.TYPE_WEEK,
            'week_number': 7,
            'academic_year': year,
            'semester': semester,
            'start_date': start_week,
            'end_date': end_week,
            'is_locked': False,
            'is_published': True
        }
    )

    # 8. Cấu hình quy tắc cảnh báo sớm
    EarlyWarningRule.objects.get_or_create(
        rule_type=EarlyWarningRule.TYPE_STUDENT_LATE,
        defaults={
            'name': 'Học sinh đi học muộn >= 3 lần trong 7 ngày',
            'threshold': 3,
            'time_window_days': 7,
            'is_active': True,
            'suggested_action': 'GVCN gặp riêng học sinh tìm hiểu hoàn cảnh gia đình hoặc liên hệ phụ huynh để phối hợp nhắc nhở.'
        }
    )
    EarlyWarningRule.objects.get_or_create(
        rule_type=EarlyWarningRule.TYPE_STUDENT_REPEAT,
        defaults={
            'name': 'Hành vi vi phạm lặp lại >= 2 lần trong 5 ngày',
            'threshold': 2,
            'time_window_days': 5,
            'is_active': True,
            'suggested_action': 'GVCN phối hợp với cán bộ Đoàn và Ban cán sự lớp để nhắc nhở và có kế hoạch hỗ trợ cụ thể.'
        }
    )

    # 9. Một số bản ghi vi phạm thực tế để thử nghiệm quy trình
    # Record 1: ĐÃ XÁC MINH (Đi muộn 1)
    rec1, _ = ViolationRecord.objects.get_or_create(
        record_code='VP-20261013-0001',
        defaults={
            'school_class': created_classes['10A1'],
            'student': s_nam,
            'student_name_snapshot': s_nam.full_name,
            'rule': created_rules['VP-01'],
            'occurred_at': timezone.now() - timedelta(days=3, hours=2),
            'location': 'Cổng chính trường THPT Hương Khê',
            'description': 'Đến trường lúc 7h15 (muộn 15 phút)',
            'reporter': saodo_user,
            'status': ViolationRecord.STATUS_VERIFIED,
            'points_deducted': Decimal('2.00'),
            'verified_by': doan_user,
            'verified_at': timezone.now() - timedelta(days=2),
            'verification_notes': 'Đã kiểm tra danh sách cổng trường, đúng thực tế.'
        }
    )

    # Record 2: ĐÃ XÁC MINH (Đi muộn 2)
    rec2, _ = ViolationRecord.objects.get_or_create(
        record_code='VP-20261014-0002',
        defaults={
            'school_class': created_classes['10A1'],
            'student': s_nam,
            'student_name_snapshot': s_nam.full_name,
            'rule': created_rules['VP-01'],
            'occurred_at': timezone.now() - timedelta(days=2, hours=1),
            'location': 'Cổng phụ dãy nhà A',
            'description': 'Đến trường muộn 10 phút',
            'reporter': saodo_user,
            'status': ViolationRecord.STATUS_VERIFIED,
            'points_deducted': Decimal('2.00'),
            'verified_by': doan_user,
            'verified_at': timezone.now() - timedelta(days=1),
            'verification_notes': 'Xác nhận vi phạm lần 2.'
        }
    )

    # Record 3: ĐÃ XÁC MINH (Đi muộn 3 -> Kích hoạt cảnh báo sớm)
    rec3, _ = ViolationRecord.objects.get_or_create(
        record_code='VP-20261015-0003',
        defaults={
            'school_class': created_classes['10A1'],
            'student': s_nam,
            'student_name_snapshot': s_nam.full_name,
            'rule': created_rules['VP-01'],
            'occurred_at': timezone.now() - timedelta(hours=5),
            'location': 'Cổng chính',
            'description': 'Đến trường lúc 7h12',
            'reporter': saodo_user,
            'status': ViolationRecord.STATUS_VERIFIED,
            'points_deducted': Decimal('2.00'),
            'verified_by': doan_user,
            'verified_at': timezone.now() - timedelta(hours=3),
            'verification_notes': 'Xác minh đúng thực tế.'
        }
    )

    # Record 4: CHỜ XÁC MINH (Chưa trừ điểm)
    rec4, _ = ViolationRecord.objects.get_or_create(
        record_code='VP-20261015-0004',
        defaults={
            'school_class': created_classes['11A2'],
            'student': s_tuan,
            'student_name_snapshot': s_tuan.full_name,
            'rule': created_rules['VP-07'],
            'occurred_at': timezone.now() - timedelta(hours=2),
            'location': 'Phòng 202 - Dãy B',
            'description': 'Sử dụng điện thoại di động chơi game trong giờ Sinh hoạt',
            'reporter': saodo_user,
            'status': ViolationRecord.STATUS_PENDING,
            'points_deducted': Decimal('0.00'),
            'evidence_notes': 'Sao đỏ trực tại tầng 2 ghi nhận.'
        }
    )

    # Record 5: ĐANG KHIẾU NẠI / GIẢI TRÌNH
    rec5, _ = ViolationRecord.objects.get_or_create(
        record_code='VP-20261015-0005',
        defaults={
            'school_class': created_classes['12A1'],
            'student': s_linh,
            'student_name_snapshot': s_linh.full_name,
            'rule': created_rules['VP-04'],
            'occurred_at': timezone.now() - timedelta(days=1),
            'location': 'Sân trường',
            'description': 'Không mặc áo đồng phục',
            'reporter': saodo_user,
            'status': ViolationRecord.STATUS_APPEALING,
            'points_deducted': Decimal('0.00'),
            'appeal_reason': 'Em bị ướt áo đồng phục do mưa lũ trên đường đi học, đã báo cáo GVCN đầu giờ xin phép mặc áo khoác trắng.',
            'appeal_submitted_by': student_user,
            'appeal_submitted_at': timezone.now() - timedelta(hours=4)
        }
    )

    # 10. Tính toán bảng điểm thi đua
    from competition.services import recalculate_period_scores
    recalculate_period_scores(period)

    # Đoàn trường cộng điểm phong trào cho 12A1
    score_12a1 = ClassCompetitionScore.objects.filter(competition_period=period, school_class=created_classes['12A1']).first()
    if score_12a1:
        score_12a1.bonus_points = Decimal('5.00')
        score_12a1.bonus_notes = "+5đ: Đạt giải Nhất cuộc thi Văn nghệ chào mừng năm học mới"
        score_12a1.calculate_total()
        score_12a1.save()
        recalculate_period_scores(period)

    # 11. Đánh giá cảnh báo sớm cho s_nam
    from alerts.services import evaluate_alerts_for_student
    evaluate_alerts_for_student(s_nam)

    # 12. Tạo một hồ sơ tư vấn tâm lý mẫu trong "Góc sẻ chia" (Bảo mật)
    CounselingRequest.objects.get_or_create(
        tracking_code='GSC-2026-X8F9',
        defaults={
            'student': s_nam,
            'is_anonymous': False,
            'alias_name': '',
            'topic': CounselingRequest.TOPIC_ACADEMIC,
            'content': 'Em cảm thấy rất áp lực trước kỳ thi giữa kỳ và việc gia đình kỳ vọng vào đội tuyển học sinh giỏi. Dạo gần đây em thường xuyên mất ngủ và lo âu.',
            'preferred_channel': CounselingRequest.CHANNEL_IN_PERSON,
            'contact_info': 'Gặp tại phòng tư vấn vào giờ ra chơi thứ Năm',
            'preferred_schedule': 'Thứ Năm lúc 9h30 sáng',
            'status': CounselingRequest.STATUS_SCHEDULED,
            'assigned_counselor': tamly_user,
            'scheduled_meeting': timezone.now() + timedelta(days=1, hours=2)
        }
    )

    print("=> Seed du lieu mau he thong HK Student Hub hoan tat thanh cong!")


def clean_mock_data():
    """Xóa dữ liệu thử nghiệm, đưa hệ thống về trạng thái ban đầu an toàn"""
    ViolationReviewHistory.objects.all().delete()
    ViolationRecord.objects.all().delete()
    ClassCompetitionScore.objects.all().delete()
    CompetitionPeriod.objects.all().delete()
    HomeroomIntervention.objects.all().delete()
    EarlyWarningAlert.objects.all().delete()
    CounselingPrivateNote.objects.all().delete()
    CounselingRequest.objects.all().delete()
    AuditLog.objects.all().delete()
    print("=> Da don sach du lieu thu nghiem an toan.")
