import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"

# ==============================================================================
# 1. UPDATE core/middleware.py
# ==============================================================================
middleware_path = os.path.join(BASE_DIR, "core", "middleware.py")
with open(middleware_path, "r", encoding="utf-8") as f:
    mw = f.read()

mw_norm = mw.replace("\r\n", "\n")
target_mw = """    auth_paths = {
        '/api/core/auth/login/',
        '/api/core/auth/logout/',
        '/api/core/auth/register/',
        '/api/core/auth/forgot-password/',"""

replacement_mw = """    auth_paths = {
        '/api/core/auth/login/',
        '/api/core/auth/logout/',
        '/api/core/auth/register/',
        '/api/core/auth/complete-profile/',
        '/api/core/auth/forgot-password/',"""

if target_mw in mw_norm:
    mw_norm = mw_norm.replace(target_mw, replacement_mw)
    with open(middleware_path, "w", encoding="utf-8") as f:
        f.write(mw_norm)
    print("SUCCESS: Updated core/middleware.py auth_paths")
else:
    print("INFO: core/middleware.py already has complete-profile or different")


# ==============================================================================
# 2. UPDATE core/serializers.py
# ==============================================================================
serializers_path = os.path.join(BASE_DIR, "core", "serializers.py")
with open(serializers_path, "r", encoding="utf-8") as f:
    ser = f.read()

ser_norm = ser.replace("\r\n", "\n")
old_ser_target = """        elif role_type == self.ROLE_TYPE_TEACHER:
            if not attrs.get('phone'):
                raise serializers.ValidationError({'phone': 'Giáo viên bắt buộc phải cung cấp số điện thoại liên lạc.'})
            if not attrs.get('subject'):
                raise serializers.ValidationError({'subject': 'Vui lòng chọn tổ chuyên môn / bộ môn giảng dạy.'})
            if not attrs.get('teacher_type'):
                raise serializers.ValidationError({'teacher_type': 'Vui lòng chọn loại giáo viên (Bộ môn hoặc Chủ nhiệm).'})
            if attrs.get('teacher_type') == 'gvcn' and not attrs.get('homeroom_class'):
                raise serializers.ValidationError({'homeroom_class': 'Giáo viên chủ nhiệm cần chọn lớp được phân công phụ trách.'})
        return attrs"""

new_ser_target = """        elif role_type == self.ROLE_TYPE_TEACHER:
            if not attrs.get('phone'):
                raise serializers.ValidationError({'phone': 'Giáo viên bắt buộc phải cung cấp số điện thoại liên lạc.'})
            if not attrs.get('subject') and not attrs.get('subjects'):
                raise serializers.ValidationError({'subject': 'Vui lòng chọn môn giảng dạy trong danh sách.'})
            if not attrs.get('subject') and attrs.get('subjects'):
                attrs['subject'] = ", ".join(attrs['subjects'])
            if not attrs.get('teacher_type'):
                attrs['teacher_type'] = 'gvbm'
        return attrs"""

if old_ser_target in ser_norm:
    ser_norm = ser_norm.replace(old_ser_target, new_ser_target)
    with open(serializers_path, "w", encoding="utf-8") as f:
        f.write(ser_norm)
    print("SUCCESS: Updated core/serializers.py CompleteProfileSerializer validation")
else:
    print("INFO: core/serializers.py already updated or target not found")

print("Done part 1.")
