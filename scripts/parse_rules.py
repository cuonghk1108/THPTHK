import openpyxl
import sys
sys.stdout.reconfigure(encoding='utf-8')

wb = openpyxl.load_workbook(r'C:\Users\Xuan Cuong\.gemini\antigravity\brain\5a5dcb7f-ba1d-4f8d-8a94-94f428cd0bbe\.user_uploaded\media_1792913340467_98df7079.xlsx')
ws = wb.active

categories = {}
rules = []

for row in ws.iter_rows(values_only=True):
    if not any(row):
        continue
    code, name, points, cat_name, is_active = row[:5]
    if cat_name not in categories:
        categories[cat_name] = []
    categories[cat_name].append({
        'code': code.strip() if code else '',
        'name': name.strip() if name else '',
        'points': float(points) if points is not None else 0.0,
        'is_active': bool(is_active)
    })
    rules.append((code, name, points, cat_name, is_active))

print(f"Total categories found: {len(categories)}")
for c, r_list in categories.items():
    print(f"\nCategory: {c} ({len(r_list)} rules)")
    for r in r_list:
        print(f"  [{r['code']}] {r['name']} -> -{r['points']}đ")
