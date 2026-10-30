from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SchoolClassViewSet, StudentViewSet, ConductRuleCategoryViewSet,
    ConductRuleViewSet, ViolationRecordViewSet,
    TeacherManagementViewSet, TeacherReflectionViewSet,
    RedStarAssignmentViewSet, RedStarReportViewSet,
    TeacherClassViewSet, StudentFeedbackViewSet,
    violation_email_history_api, violation_email_retry_api,
    violation_email_test_api, violation_email_config_api,
)

router = DefaultRouter()
router.register(r'classes', SchoolClassViewSet, basename='school-class')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'rule-categories', ConductRuleCategoryViewSet, basename='conduct-rule-category')
router.register(r'rules', ConductRuleViewSet, basename='conduct-rule')
router.register(r'violations', ViolationRecordViewSet, basename='violation-record')
router.register(r'teachers', TeacherManagementViewSet, basename='teacher-management')
router.register(r'reflections', TeacherReflectionViewSet, basename='teacher-reflection')
router.register(r'red-star', RedStarAssignmentViewSet, basename='red-star-assignment')
router.register(r'red-star-reports', RedStarReportViewSet, basename='red-star-report')
router.register(r'teacher-classes', TeacherClassViewSet, basename='teacher-class')
router.register(r'feedbacks', StudentFeedbackViewSet, basename='student-feedback')

urlpatterns = [
    # Email notification endpoints (Thông báo vi phạm & minh chứng cho Đoàn trường)
    path('email/config/', violation_email_config_api, name='violation-email-config'),
    path('email/history/', violation_email_history_api, name='violation-email-history'),
    path('email/test/', violation_email_test_api, name='violation-email-test'),
    path('email/<int:notification_id>/retry/', violation_email_retry_api, name='violation-email-retry'),

    path('', include(router.urls)),
]

