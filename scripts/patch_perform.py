p = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\competition\views.py'
with open(p, 'r', encoding='utf-8') as f:
    text = f.read()

old1 = '''        if not (user.is_admin or user.is_bgh):
            raise permissions.PermissionDenied("Chỉ Quản trị viên hoặc BGH mới có quyền tạo kỳ thi đua.")'''
new1 = '''        if not (user.is_admin or user.is_bgh or user.is_doan_truong):
            raise permissions.PermissionDenied("Chỉ Quản trị viên, BGH hoặc Đoàn trường mới có quyền tạo kỳ thi đua.")'''

old2 = '''        if not (user.is_admin or user.is_bgh):
            raise permissions.PermissionDenied("Bạn không có quyền chỉnh sửa kỳ thi đua.")'''
new2 = '''        if not (user.is_admin or user.is_bgh or user.is_doan_truong):
            raise permissions.PermissionDenied("Bạn không có quyền chỉnh sửa kỳ thi đua.")'''

assert old1 in text, "old1 not found"
assert old2 in text, "old2 not found"

text = text.replace(old1, new1, 1).replace(old2, new2, 1)

with open(p, 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated perform_create and perform_update successfully!")
