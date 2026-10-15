from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CounselingSubmitAPIView, CounselingTrackAPIView, CounselingRequestViewSet

router = DefaultRouter()
router.register(r'requests', CounselingRequestViewSet, basename='counseling-request')

urlpatterns = [
    path('submit/', CounselingSubmitAPIView.as_view(), name='counseling-submit'),
    path('track/<str:tracking_code>/', CounselingTrackAPIView.as_view(), name='counseling-track'),
    path('', include(router.urls)),
]
