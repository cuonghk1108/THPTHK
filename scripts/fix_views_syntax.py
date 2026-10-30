import os, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'conduct/views.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

bad = "qs = qs.filter(school_class__in=homeroom_classes)        elif user.is_student:"
good = "qs = qs.filter(school_class__in=homeroom_classes)\n\n        elif user.is_student:"
assert bad in text, "bad string not found"
text = text.replace(bad, good, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Fixed syntax in conduct/views.py!")
