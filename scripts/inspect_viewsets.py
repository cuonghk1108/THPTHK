import os
import sys

BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"
sys.path.insert(0, BASE_DIR)
sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')
import django
django.setup()

import conduct.views as cv

viewsets = [
    cv.SchoolClassViewSet,
    cv.StudentViewSet,
    cv.ConductRuleCategoryViewSet,
    cv.ConductRuleViewSet,
    cv.ViolationRecordViewSet,
    cv.TeacherManagementViewSet,
    cv.TeacherReflectionViewSet,
    cv.RedStarAssignmentViewSet,
    cv.RedStarReportViewSet,
    cv.TeacherClassViewSet,
    cv.StudentFeedbackViewSet
]

print("=== VIEWSETS AND THEIR METHODS ===")
for vs in viewsets:
    print(f"\n[{vs.__name__}] (Base: {[b.__name__ for b in vs.__bases__]})")
    print(f"  permission_classes: {getattr(vs, 'permission_classes', None)}")
    own_methods = [name for name, func in vs.__dict__.items() if callable(func)]
    print(f"  Defined methods: {own_methods}")
