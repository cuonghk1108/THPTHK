# -*- coding: utf-8 -*-
import os
import sys
import json
import django

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Xuan Cuong\Desktop\hk-student-hub')
os.environ['DJANGO_SETTINGS_MODULE'] = 'hk_hub_project.settings'
django.setup()

from django.test import RequestFactory
from django.utils import timezone
from core.models import User, Notification, ApprovalLog, AuditLog
from conduct.models import SchoolClass, Student, Teacher, TeacherClassAssignment
from core.views import ProfileAPIView, UserManagementViewSet, ChangePasswordAPIView
from rest_framework.test import force_authenticate

def run_tests():
    print("==================================================")
    print("BAT DAU KIEM TRA TOAN DIEN PROFILE VA DOI LOP")
    print("==================================================")

    rf = RequestFactory()

    # 0. Setup test data
    c10a1, _ = SchoolClass.objects.get_or_create(name='10A1', defaults={'grade': 10, 'academic_year': '2026-2027'})
    c10a2, _ = SchoolClass.objects.get_or_create(name='10A2', defaults={'grade': 10, 'academic_year': '2026-2027'})
    c10a3, _ = SchoolClass.objects.get_or_create(name='10A3', defaults={'grade': 10, 'academic_year': '2026-2027'})
    c11a1, _ = SchoolClass.objects.get_or_create(name='11A1', defaults={'grade': 11, 'academic_year': '2026-2027'})
    c12a1, _ = SchoolClass.objects.get_or_create(name='12A1', defaults={'grade': 12, 'academic_year': '2026-2027'})

    # Admin user
    admin_user, _ = User.objects.get_or_create(
        username='admin_test_profile',
        defaults={
            'role': User.ROLE_ADMIN,
            'account_status': User.STATUS_APPROVED,
            'full_name': 'Quản Trị Viên Test',
            'email': 'admin_test_profile@huongkhe.edu.vn',
            'is_staff': True
        }
    )
    admin_user.set_password('Admin@123456')
    admin_user.save()

    # Other user for email collision
    other_user, _ = User.objects.get_or_create(
        username='other_user_test',
        defaults={
            'role': User.ROLE_HOC_SINH,
            'account_status': User.STATUS_APPROVED,
            'full_name': 'Người Dùng Khác',
            'email': 'existing_taken@huongkhe.edu.vn'
        }
    )

    # Test Student
    student_user, _ = User.objects.get_or_create(
        username='hs_test_profile',
        defaults={
            'role': User.ROLE_HOC_SINH,
            'account_status': User.STATUS_APPROVED,
            'full_name': 'Học Sinh Test',
            'email': 'hs_test@huongkhe.edu.vn',
            'department_or_class': '10A1'
        }
    )
    student_user.set_password('Student@123')
    student_user.department_or_class = '10A1'
    student_user.verification_info = ''
    student_user.save()

    student_prof, _ = Student.objects.get_or_create(
        user=student_user,
        defaults={
            'student_code': 'HK10-TEST-001',
            'full_name': 'Học Sinh Test',
            'date_of_birth': timezone.now().date(),
            'gender': 'M',
            'school_class': c10a1,
            'status': 'STUDYING'
        }
    )
    student_prof.school_class = c10a1
    student_prof.save()

    # Test Teacher
    teacher_user, _ = User.objects.get_or_create(
        username='gv_test_profile',
        defaults={
            'role': User.ROLE_GVBM,
            'account_status': User.STATUS_APPROVED,
            'full_name': 'Giáo Viên Test',
            'email': 'gv_test@huongkhe.edu.vn',
            'department_or_class': '10A1'
        }
    )
    teacher_user.set_password('Teacher@123')
    teacher_user.save()

    teacher_prof, _ = Teacher.objects.get_or_create(
        user=teacher_user,
        defaults={
            'teacher_code': 'GV-TEST-001',
            'full_name': 'Giáo Viên Test',
            'subject': 'Toán',
            'phone': '0912345678'
        }
    )

    profile_view = ProfileAPIView.as_view()
    user_mgmt_view = UserManagementViewSet.as_view({'post': 'review_class_change'})

    # ----------------------------------------------------
    # TEST 1: DOI EMAIL & CHECK TRUNG LAP
    # ----------------------------------------------------
    print("\n--- TEST 1: Đổi Email & Kiểm tra trùng lặp ---")
    # 1.1 Thử đổi sang email đã tồn tại của người khác
    req = rf.patch('/api/core/auth/profile/', data=json.dumps({'email': 'existing_taken@huongkhe.edu.vn'}), content_type='application/json')
    force_authenticate(req, user=student_user)
    resp = profile_view(req)
    assert resp.status_code == 400, f"Expected 400 on duplicate email, got {resp.status_code}: {resp.data}"
    print("[PASS] Chan email trung lap thanh cong (HTTP 400).")

    # 1.2 Đổi sang email hợp lệ mới
    req = rf.patch('/api/core/auth/profile/', data=json.dumps({'email': 'hs_new_email@huongkhe.edu.vn'}), content_type='application/json')
    force_authenticate(req, user=student_user)
    resp = profile_view(req)
    assert resp.status_code == 200, f"Expected 200 on valid email update, got {resp.status_code}: {resp.data}"
    student_user.refresh_from_db()
    assert student_user.email == 'hs_new_email@huongkhe.edu.vn', f"Email not updated in DB: {student_user.email}"
    print("[PASS] Doi email nguoi dung thanh cong va dong bo vao DB.")

    # ----------------------------------------------------
    # TEST 2: DOI MAT KHAU
    # ----------------------------------------------------
    print("\n--- TEST 2: Đổi Mật Khẩu qua Profile ---")
    # 2.1 Mật khẩu hiện tại sai
    req = rf.patch('/api/core/auth/profile/', data=json.dumps({
        'current_password': 'WRONG_PASSWORD',
        'new_password': 'NewPassword@2026',
        'confirm_password': 'NewPassword@2026'
    }), content_type='application/json')
    force_authenticate(req, user=student_user)
    resp = profile_view(req)
    assert resp.status_code == 400, f"Expected 400 on wrong password, got {resp.status_code}: {resp.data}"
    print("[PASS] Chan mat khau cu khong chinh xac (HTTP 400).")

    # 2.2 Mật khẩu xác nhận không khớp
    req = rf.patch('/api/core/auth/profile/', data=json.dumps({
        'current_password': 'Student@123',
        'new_password': 'NewPassword@2026',
        'confirm_password': 'DIFFERENT_CONFIRM'
    }), content_type='application/json')
    force_authenticate(req, user=student_user)
    resp = profile_view(req)
    assert resp.status_code == 400, f"Expected 400 on mismatch password, got {resp.status_code}: {resp.data}"
    print("[PASS] Chan mat khau xac nhan khong khop (HTTP 400).")

    # 2.3 Đổi mật khẩu hợp lệ
    req = rf.patch('/api/core/auth/profile/', data=json.dumps({
        'current_password': 'Student@123',
        'new_password': 'NewPassword@2026',
        'confirm_password': 'NewPassword@2026'
    }), content_type='application/json')
    force_authenticate(req, user=student_user)
    resp = profile_view(req)
    assert resp.status_code == 200, f"Expected 200 on valid password change, got {resp.status_code}: {resp.data}"
    student_user.refresh_from_db()
    assert student_user.check_password('NewPassword@2026'), "Password was not updated in DB!"
    print("[PASS] Doi mat khau thanh cong va xac thuc mat khau moi thanh cong.")

    # ----------------------------------------------------
    # TEST 3: HOC SINH XIN DOI LOP (BAT BUOC ADMIN DUYET)
    # ----------------------------------------------------
    print("\n--- TEST 3: Học Sinh Xin Đổi Lớp (Bắt buộc Admin duyệt) ---")
    # Học sinh đang ở 10A1, xin chuyển sang 10A2
    req = rf.patch('/api/core/auth/profile/', data=json.dumps({
        'target_class_name': '10A2',
        'class_change_reason': 'Xin chuyển ban KHTN'
    }), content_type='application/json')
    force_authenticate(req, user=student_user)
    resp = profile_view(req)
    assert resp.status_code == 200, f"Expected 200 on student class change request, got {resp.status_code}: {resp.data}"

    student_user.refresh_from_db()
    student_prof.refresh_from_db()

    # Kiem tra: Lop thuc te cua hoc sinh van chua duoc doi (van la 10A1)
    assert student_user.department_or_class == '10A1', f"User class should remain 10A1, but is {student_user.department_or_class}"
    assert student_prof.school_class.name == '10A1', f"Student model school_class should remain 10A1, but is {student_prof.school_class.name}"

    # Kiem tra: pending_class_change da duoc luu vao verification_info
    v_data = json.loads(student_user.verification_info)
    pending = v_data.get('pending_class_change')
    assert pending is not None, "pending_class_change was not stored in verification_info!"
    assert pending['target_class_name'] == '10A2', f"Target class expected 10A2, got {pending['target_class_name']}"
    assert pending['previous_class'] == '10A1', f"Previous class expected 10A1, got {pending['previous_class']}"

    # Kiem tra: Thong bao da duoc tao cho Admin
    notif = Notification.objects.filter(recipient=admin_user, notification_type=Notification.TYPE_SYSTEM).last()
    assert notif is not None and '10A2' in notif.message, f"Notification to admin missing or incorrect: {notif}"
    print("[PASS] Hoc sinh xin doi lop: Lop chua bi doi truc tiep, trang thai cho duyet da duoc ghi nhan va Admin nhan duoc thong bao.")

    # ----------------------------------------------------
    # TEST 4: ADMIN PHE DUYET DOI LOP CHO HOC SINH
    # ----------------------------------------------------
    print("\n--- TEST 4: Admin Phê Duyệt Chuyển Lớp ---")
    req = rf.post(f'/api/core/users/{student_user.id}/review-class-change/', data=json.dumps({
        'action': 'approve',
        'reason': 'Chấp thuận nguyện vọng chuyển ban'
    }), content_type='application/json')
    force_authenticate(req, user=admin_user)
    resp = user_mgmt_view(req, pk=student_user.id)
    assert resp.status_code == 200, f"Expected 200 on admin approve, got {resp.status_code}: {resp.data}"

    student_user.refresh_from_db()
    student_prof.refresh_from_db()

    # Kiem tra: Lop hoc thuc te da duoc cap nhat sang 10A2 ca o User va Student profile
    assert student_user.department_or_class == '10A2', f"User class should now be 10A2, but is {student_user.department_or_class}"
    assert student_prof.school_class.name == '10A2', f"Student model school_class should now be 10A2, but is {student_prof.school_class.name}"

    # Kiem tra: pending_class_change da duoc xoa sach
    v_data = json.loads(student_user.verification_info or '{}')
    assert 'pending_class_change' not in v_data, "pending_class_change should be removed after approval!"

    # Kiem tra: Hoc sinh nhan duoc thong bao phe duyet
    notif_stu = Notification.objects.filter(recipient=student_user, notification_type=Notification.TYPE_APPROVAL).last()
    assert notif_stu is not None and '10A2' in notif_stu.message, "Student did not receive approval notification!"
    print("[PASS] Admin phe duyet chuyen lop: Lop cua hoc sinh da duoc cap nhat nhat quan tren toan he thong.")

    # ----------------------------------------------------
    # TEST 5: ADMIN TU CHOI DOI LOP
    # ----------------------------------------------------
    print("\n--- TEST 5: Admin Từ Chối Chuyển Lớp ---")
    # Học sinh gửi tiếp yêu cầu chuyển sang 10A3
    req = rf.patch('/api/core/auth/profile/', data=json.dumps({
        'target_class_name': '10A3',
        'class_change_reason': 'Muốn học cùng bạn'
    }), content_type='application/json')
    force_authenticate(req, user=student_user)
    profile_view(req)

    student_user.refresh_from_db()
    assert 'pending_class_change' in json.loads(student_user.verification_info)

    # Admin từ chối
    req = rf.post(f'/api/core/users/{student_user.id}/review-class-change/', data=json.dumps({
        'action': 'reject',
        'reason': 'Lớp 10A3 đã đủ chỉ tiêu sĩ số'
    }), content_type='application/json')
    force_authenticate(req, user=admin_user)
    resp = user_mgmt_view(req, pk=student_user.id)
    assert resp.status_code == 200, f"Expected 200 on admin reject, got {resp.status_code}: {resp.data}"

    student_user.refresh_from_db()
    student_prof.refresh_from_db()

    # Lớp vẫn là 10A2 (không thay đổi)
    assert student_user.department_or_class == '10A2'
    assert student_prof.school_class.name == '10A2'

    # pending_class_change đã bị xóa
    v_data = json.loads(student_user.verification_info or '{}')
    assert 'pending_class_change' not in v_data
    print("[PASS] Admin tu choi chuyen lop: Lop giu nguyen 10A2, pending request da duoc don dep.")

    # ----------------------------------------------------
    # TEST 6: GIAO VIEN DOI LOP (KHONG CAN ADMIN CAN THIEP)
    # ----------------------------------------------------
    print("\n--- TEST 6: Giáo Viên Đổi Lớp (Không cần Admin can thiệp) ---")
    # Giáo viên chọn dạy các lớp 10A1, 10A2, 11A1 môn Toán
    req = rf.patch('/api/core/auth/profile/', data=json.dumps({
        'teaching_classes': ['10A1', '10A2', '11A1'],
        'subject': 'Toán Tin'
    }), content_type='application/json')
    force_authenticate(req, user=teacher_user)
    resp = profile_view(req)
    assert resp.status_code == 200, f"Expected 200 on teacher class update, got {resp.status_code}: {resp.data}"

    teacher_user.refresh_from_db()
    teacher_prof.refresh_from_db()

    # Kiem tra cac phan cong giang day da duoc kich hoat ngay lap tuc
    active_assns = list(TeacherClassAssignment.objects.filter(teacher=teacher_user, is_active=True).values_list('school_class__name', flat=True))
    assert set(active_assns) == {'10A1', '10A2', '11A1'}, f"Teacher assignments mismatch: {active_assns}"
    assert teacher_prof.subject == 'Toán Tin', f"Teacher subject mismatch: {teacher_prof.subject}"
    print("[PASS] Giao vien tu cap nhat lop: 3 lop (10A1, 10A2, 11A1) da duoc phan cong ngay lap tuc ma KHONG can Admin can thiep.")

    # Giáo viên đổi tiếp: Bỏ lớp 10A1, thêm lớp 12A1
    req = rf.patch('/api/core/auth/profile/', data=json.dumps({
        'teaching_classes': ['10A2', '11A1', '12A1'],
        'subject': 'Toán Tin'
    }), content_type='application/json')
    force_authenticate(req, user=teacher_user)
    resp = profile_view(req)
    assert resp.status_code == 200

    active_assns = list(TeacherClassAssignment.objects.filter(teacher=teacher_user, is_active=True).values_list('school_class__name', flat=True))
    assert set(active_assns) == {'10A2', '11A1', '12A1'}, f"Teacher assignments after update mismatch: {active_assns}"

    # Kiem tra lop 10A1 da bi deactivate
    assn_10a1 = TeacherClassAssignment.objects.filter(teacher=teacher_user, school_class=c10a1).first()
    assert assn_10a1 is not None and assn_10a1.is_active is False, "10A1 assignment should be inactive!"
    print("[PASS] Giao vien cap nhat bo/them lop: Thay doi phan cong ap dung ngay lap tuc, khong ton tai do tre.")

    # ----------------------------------------------------
    # TEST 7: HOC SINH HUY YEU CAU DOI LOP
    # ----------------------------------------------------
    print("\n--- TEST 7: Học Sinh Tự Hủy Yêu Cầu Đổi Lớp ---")
    req = rf.patch('/api/core/auth/profile/', data=json.dumps({
        'target_class_name': '10A3',
        'class_change_reason': 'Nguyện vọng tạm thời'
    }), content_type='application/json')
    force_authenticate(req, user=student_user)
    profile_view(req)

    student_user.refresh_from_db()
    assert 'pending_class_change' in json.loads(student_user.verification_info)

    # Học sinh tự hủy
    req = rf.patch('/api/core/auth/profile/', data=json.dumps({
        'cancel_class_change': True
    }), content_type='application/json')
    force_authenticate(req, user=student_user)
    resp = profile_view(req)
    assert resp.status_code == 200

    student_user.refresh_from_db()
    v_data = json.loads(student_user.verification_info or '{}')
    assert 'pending_class_change' not in v_data, "pending_class_change should be cleared upon cancel!"
    print("[PASS] Hoc sinh tu huy yeu cau doi lop thanh cong.")

    print("\n==================================================")
    print("TAT CA CAC TEST DA HOAN THANH XUAT SAC VA PASS 100%!")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
