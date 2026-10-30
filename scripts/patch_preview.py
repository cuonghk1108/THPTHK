with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\conduct\views.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        current_score, period = get_class_score_snapshot(school_class)

        deduct_points = rule.default_points_deducted

        projected_score = max(Decimal('0.00'), current_score - deduct_points)"""

replacement = """        current_score, period = get_class_score_snapshot(school_class)
        if current_score is None:
            current_score = Decimal('100.00')

        deduct_points = rule.default_points_deducted

        projected_score = max(Decimal('0.00'), current_score - deduct_points)"""

content_norm = content.replace('\r\n', '\n')
target_norm = target.replace('\r\n', '\n')
replacement_norm = replacement.replace('\r\n', '\n')

assert target_norm in content_norm, "Target not found in views.py"
new_content = content_norm.replace(target_norm, replacement_norm, 1)

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\conduct\views.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(new_content.replace('\n', '\r\n'))

print("Updated conduct/views.py preview_deduction successfully!")
