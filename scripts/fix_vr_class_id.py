import os, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'conduct/serializers.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

target = "class_name = serializers.CharField(source='school_class.name', read_only=True)"
replacement = "class_name = serializers.CharField(source='school_class.name', read_only=True)\n    class_id = serializers.IntegerField(source='school_class_id', read_only=True)"

assert target in text, "target not found"
text = text.replace(target, replacement, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Added class_id to ViolationRecordSerializer.")
