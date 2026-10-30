import os, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'core/serializers.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

if "is_class_monitor = serializers.BooleanField" not in text:
    old_f = "    is_student = serializers.BooleanField(read_only=True)"
    new_f = "    is_student = serializers.BooleanField(read_only=True)\n    is_class_monitor = serializers.BooleanField(read_only=True)"
    text = text.replace(old_f, new_f, 1)

    old_meta = "'is_gvcn', 'is_gvbm', 'is_student',"
    new_meta = "'is_gvcn', 'is_gvbm', 'is_student', 'is_class_monitor',"
    text = text.replace(old_meta, new_meta, 1)

    old_ro = "'is_gvcn', 'is_gvbm', 'is_student', 'permissions',"
    new_ro = "'is_gvcn', 'is_gvbm', 'is_student', 'is_class_monitor', 'permissions',"
    text = text.replace(old_ro, new_ro, 1)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Patched core/serializers.py with is_class_monitor.")
else:
    print("core/serializers.py already has is_class_monitor.")
