# -*- coding: utf-8 -*-
import os
import shutil

src_root = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub'
dst_root = r'C:\Users\Xuan Cuong\.gemini\antigravity\scratch\hk-student-hub'

files_to_sync = [
    r'conduct\models.py',
    r'conduct\migrations\0018_studentfeedback_studentfeedbackreply_and_more.py',
    r'conduct\migrations\0019_alter_schoolclass_options_schoolclass_class_order.py',
    r'conduct\migrations\0020_redstarreport_idx_rsr_status_time_and_more.py',
    r'conduct\serializers.py',
    r'conduct\views.py',
    r'conduct\urls.py',
    r'conduct\test_teacher_classes_and_feedback.py',
    r'competition\services.py',
    r'competition\views.py',
    r'reports\services.py',
    r'core\cache_utils.py',
    r'core\signals.py',
    r'core\apps.py',
    r'core\serializers.py',
    r'core\views.py',
    r'core\middleware.py',
    r'hk_hub_project\settings.py',
    r'templates\index.html',
    r'static\app.js',
    r'static\public.js',
]

if os.path.exists(dst_root):
    for rel_path in files_to_sync:
        src = os.path.join(src_root, rel_path)
        dst = os.path.join(dst_root, rel_path)
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            print(f'Synced: {rel_path}')
        else:
            print(f'Not found: {src}')
else:
    print(f'Destination scratch does not exist: {dst_root}')
