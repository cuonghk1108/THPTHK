from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SchoolClassViewSet, StudentViewSet, ConductRuleCategoryViewSet,
    ConductRuleViewSet, ViolationRecordViewSet
)

router = DefaultRouter()
router.register(r'classes', SchoolClassViewSet, basename='school-class')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'rule-categories', ConductRuleCategoryViewSet, basename='conduct-rule-category')
router.register(r'rules', ConductRuleViewSet, basename='conduct-rule')
router.register(r'violations', ViolationRecordViewSet, basename='violation-record')

urlpatterns = [
    path('', include(router.urls)),
]
