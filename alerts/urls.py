from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EarlyWarningRuleViewSet, EarlyWarningAlertViewSet

router = DefaultRouter()
router.register(r'rules', EarlyWarningRuleViewSet, basename='early-warning-rule')
router.register(r'alerts', EarlyWarningAlertViewSet, basename='early-warning-alert')

urlpatterns = [
    path('', include(router.urls)),
]
