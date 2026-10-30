import os
import sys
import openpyxl
import django
from decimal import Decimal

sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub')
sys.path.insert(0, r'C:\Users\Xuan Cuong\Desktop\hk-student-hub')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')
django.setup()

from conduct.models import ConductRuleCategory, ConductRule, ViolationRecord

# 1. Define the 9 official categories with order and Lucide icons
OFFICIAL_CATEGORIES = [
    {
        'name': 'Tập trung và Ngoại khóa',
        'order': 1,
        'icon': 'users',
        'description': 'Quy định chào cờ đầu tuần, tập thể dục giữa giờ, dân vũ và các buổi sinh hoạt tập trung ngoại khóa'
    },
    {
        'name': 'Sinh hoạt 15 phút',
        'order': 2,
        'icon': 'clock',
        'description': 'Nền nếp sinh hoạt 15 phút đầu giờ học mỗi buổi'
    },
    {
        'name': 'Vệ sinh - Cơ sở vật chất',
        'order': 3,
        'icon': 'sparkles',
        'description': 'Vệ sinh phòng học, hành lang, dụng cụ trực nhật, bảo quản trang thiết bị và rác thải nhựa'
    },
    {
        'name': 'Tác phong - Đồng phục',
        'order': 4,
        'icon': 'user-check',
        'description': 'Đầu tóc, trang phục, phù hiệu, dép, cấm quà vặt và rác thải dùng một lần'
    },
    {
        'name': 'Nề nếp chuyên cần',
        'order': 5,
        'icon': 'calendar-check',
        'description': 'Chuyên cần, đúng giờ, không chậm học, vào lớp đúng hiệu lệnh trống'
    },
    {
        'name': 'An toàn giao thông',
        'order': 6,
        'icon': 'car',
        'description': 'Quy định phương tiện tham gia giao thông, đội mũ bảo hiểm, nhà xe và an toàn cổng trường'
    },
    {
        'name': 'Dụng cụ - Thiết bị',
        'order': 7,
        'icon': 'box',
        'description': 'Chuẩn bị ghế, cờ, thiết bị tập trung và ý thức tiết kiệm điện nước khi ra khỏi phòng'
    },
    {
        'name': 'Phong trào - Hoạt động Đoàn',
        'order': 8,
        'icon': 'flag',
        'description': 'Trực ban tuần, chuẩn bị sự kiện, sinh hoạt Đoàn, nộp bài dự thi và các cuộc vận động phong trào'
    },
    {
        'name': 'Kỷ luật học đường',
        'order': 9,
        'icon': 'alert-triangle',
        'description': 'Kỷ luật, an ninh trường học, quy chế thi cử, cấm điện thoại, chất kích thích và hành vi gây mất đoàn kết'
    },
]

def get_severity(points):
    p = float(points)
    if p <= 3.0:
        return 'LOW'
    elif p <= 5.0:
        return 'MEDIUM'
    elif p <= 10.0:
        return 'HIGH'
    else:
        return 'CRITICAL'

def run_import():
    print("=== BẮT ĐẦU CẬP NHẬT QUY TẮC TRỪ ĐIỂM CHÍNH THỨC ===", flush=True)
    
    # 1. Create or update the 9 official categories
    cat_map = {}
    for cat_data in OFFICIAL_CATEGORIES:
        print(f"Processing category: {cat_data['name']}", flush=True)
        cat_obj, created = ConductRuleCategory.objects.update_or_create(
            name=cat_data['name'],
            defaults={
                'order': cat_data['order'],
                'icon': cat_data['icon'],
                'description': cat_data['description'],
            }
        )
        cat_map[cat_obj.name] = cat_obj
        action = "Tạo mới" if created else "Cập nhật"
        print(f"[{action}] Danh mục {cat_obj.order}: {cat_obj.name} (ID={cat_obj.id})", flush=True)

    # 2. Map old rules VP-01..12 to corresponding new categories and set is_active=False
    old_rule_cat_mapping = {
        'VP-01': 'Nề nếp chuyên cần',
        'VP-02': 'Nề nếp chuyên cần',
        'VP-03': 'Nề nếp chuyên cần',
        'VP-04': 'Tác phong - Đồng phục',
        'VP-05': 'Tác phong - Đồng phục',
        'VP-06': 'Tác phong - Đồng phục',
        'VP-07': 'Kỷ luật học đường',
        'VP-08': 'Kỷ luật học đường',
        'VP-09': 'Kỷ luật học đường',
        'VP-10': 'Vệ sinh - Cơ sở vật chất',
        'VP-11': 'Vệ sinh - Cơ sở vật chất',
        'VP-12': 'An toàn giao thông',
    }

    for vp_code, target_cat_name in old_rule_cat_mapping.items():
        vp_rule = ConductRule.objects.filter(code=vp_code).first()
        if vp_rule:
            vp_rule.is_active = False
            vp_rule.category = cat_map[target_cat_name]
            vp_rule.save()
            print(f"  -> Lưu trữ lịch sử quy định cũ: {vp_code} ({vp_rule.name}) -> is_active=False, Cat={target_cat_name}")

    # Remove old empty categories not in the official 9
    for old_cat in ConductRuleCategory.objects.exclude(name__in=cat_map.keys()):
        rule_count = old_cat.rules.count()
        if rule_count == 0:
            print(f"  -> Xóa danh mục cũ không còn dùng: {old_cat.name} (ID={old_cat.id})")
            old_cat.delete()
        else:
            print(f"  -> CẢNH BÁO: Danh mục cũ {old_cat.name} vẫn còn {rule_count} rules")

    # 3. Read rules from Excel file
    excel_path = r'C:\Users\Xuan Cuong\.gemini\antigravity\brain\5a5dcb7f-ba1d-4f8d-8a94-94f428cd0bbe\.user_uploaded\media_1792913340467_98df7079.xlsx'
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active

    imported_count = 0
    for row in ws.iter_rows(values_only=True):
        if not any(row):
            continue
        code, name, points, cat_name, is_active = row[:5]
        code = str(code).strip()
        name = str(name).strip()
        points = Decimal(str(points))
        cat_name = str(cat_name).strip()
        is_active = bool(is_active)

        if cat_name not in cat_map:
            print(f"LỖI: Không tìm thấy danh mục '{cat_name}' cho mã '{code}'")
            continue

        category = cat_map[cat_name]
        severity = get_severity(points)

        rule_obj, created = ConductRule.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'category': category,
                'default_points_deducted': points,
                'severity': severity,
                'is_active': is_active,
                'description': f"Quy định trừ điểm chính thức THPT Hương Khê: {name} (-{points}đ)",
            }
        )
        action = "Thêm mới" if created else "Cập nhật"
        imported_count += 1
        print(f"  [{action}] {rule_obj.code} - {rule_obj.name[:40]}... | -{rule_obj.default_points_deducted}đ | Mức: {rule_obj.get_severity_display()} | Nhóm: {category.name}")

    print(f"\n=== HOÀN TẤT NHẬP DỮ LIỆU ===")
    print(f"- Tổng số danh mục chính thức: {ConductRuleCategory.objects.count()}")
    print(f"- Tổng số quy tắc đang áp dụng (is_active=True): {ConductRule.objects.filter(is_active=True).count()}")
    print(f"- Tổng số quy tắc lưu trữ lịch sử (is_active=False): {ConductRule.objects.filter(is_active=False).count()}")

if __name__ == '__main__':
    run_import()
