import os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

# 1. Patch conduct/models.py
path_conduct = r'conduct/models.py'
with open(path_conduct, 'r', encoding='utf-8') as f:
    text = f.read()

# Add monitor to SchoolClass if not present
if "monitor = models.ForeignKey(" not in text:
    old_cls_field = "union_branch_name = models.CharField(max_length=100, blank=True, verbose_name='Tên Chi đoàn')"
    new_cls_field = "union_branch_name = models.CharField(max_length=100, blank=True, verbose_name='Tên Chi đoàn')\n    monitor = models.ForeignKey('Student', on_delete=models.SET_NULL, null=True, blank=True, related_name='monitored_classes', verbose_name='Lớp trưởng')"
    assert old_cls_field in text, "old_cls_field not found"
    text = text.replace(old_cls_field, new_cls_field, 1)
    print("Added monitor field to SchoolClass.")

# Add is_class_monitor to Student if not present
if "is_class_monitor = models.BooleanField(" not in text:
    old_stu_field = "is_red_star = models.BooleanField(default=False, verbose_name='Thành viên Đội Sao đỏ')"
    new_stu_field = "is_red_star = models.BooleanField(default=False, verbose_name='Thành viên Đội Sao đỏ')\n    is_class_monitor = models.BooleanField(default=False, db_index=True, verbose_name='Lớp trưởng')"
    assert old_stu_field in text, "old_stu_field not found"
    text = text.replace(old_stu_field, new_stu_field, 1)
    print("Added is_class_monitor field to Student.")

with open(path_conduct, 'w', encoding='utf-8') as f:
    f.write(text)

# 2. Patch core/models.py
path_core = r'core/models.py'
with open(path_core, 'r', encoding='utf-8') as f:
    core_text = f.read()

if "def is_class_monitor(self):" not in core_text:
    old_prop = """    @property
    def is_student(self):
        return self.role == self.ROLE_HOC_SINH"""
    new_prop = """    @property
    def is_student(self):
        return self.role == self.ROLE_HOC_SINH

    @property
    def is_class_monitor(self):
        if hasattr(self, 'student_profile') and self.student_profile:
            return bool(getattr(self.student_profile, 'is_class_monitor', False) or (self.student_profile.school_class and self.student_profile.school_class.monitor_id == self.student_profile.id))
        return False"""
    assert old_prop in core_text, "old_prop not found"
    core_text = core_text.replace(old_prop, new_prop, 1)
    print("Added is_class_monitor property to User.")

with open(path_core, 'w', encoding='utf-8') as f:
    f.write(core_text)

print("Both models patched successfully.")
