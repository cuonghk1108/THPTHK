import sys
sys.stdout.reconfigure(encoding='utf-8')

p = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\conduct\models.py'
with open(p, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update ViolationRecord.Meta
target1 = """    class Meta:
        ordering = ['-occurred_at']
        verbose_name = 'Bản ghi vi phạm nền nếp'
        verbose_name_plural = 'Danh sách bản ghi vi phạm'"""

replace1 = """    class Meta:
        ordering = ['-occurred_at']
        verbose_name = 'Bản ghi vi phạm nền nếp'
        verbose_name_plural = 'Danh sách bản ghi vi phạm'
        indexes = [
            models.Index(fields=['status', '-occurred_at'], name='idx_vr_status_occ'),
            models.Index(fields=['school_class', '-occurred_at'], name='idx_vr_class_occ'),
            models.Index(fields=['school_class', 'status'], name='idx_vr_class_status'),
            models.Index(fields=['-occurred_at'], name='idx_vr_occurred_at'),
            models.Index(fields=['status'], name='idx_vr_status'),
        ]"""

# 2. Update RedStarReport.Meta
target2 = """    class Meta:
        ordering = ['-incident_time']
        verbose_name = 'Báo cáo nền nếp Sao đỏ'
        verbose_name_plural = 'Danh sách báo cáo nền nếp Sao đỏ'"""

replace2 = """    class Meta:
        ordering = ['-incident_time']
        verbose_name = 'Báo cáo nền nếp Sao đỏ'
        verbose_name_plural = 'Danh sách báo cáo nền nếp Sao đỏ'
        indexes = [
            models.Index(fields=['status', '-incident_time'], name='idx_rsr_status_time'),
            models.Index(fields=['school_class', 'status'], name='idx_rsr_class_status'),
            models.Index(fields=['status'], name='idx_rsr_status'),
        ]"""

assert target1 in text, "target1 not found in conduct/models.py"
assert target2 in text, "target2 not found in conduct/models.py"

text = text.replace(target1, replace1, 1).replace(target2, replace2, 1)

with open(p, 'w', encoding='utf-8') as f:
    f.write(text)

print("[OK] Successfully added indexes to conduct/models.py")
