import sys
import os
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Xuan Cuong\Desktop\hk-student-hub')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')

import django
django.setup()

from django.test.utils import CaptureQueriesContext
from django.db import connection
from rest_framework.test import APIRequestFactory, force_authenticate
from core.models import User
from core.views import SystemStatsAPIView
from competition.views import CompetitionPeriodViewSet
from conduct.views import ViolationRecordViewSet, StudentFeedbackViewSet, SchoolClassViewSet

factory = APIRequestFactory()

admin = User.objects.filter(is_superuser=True).first() or User.objects.filter(role=User.ROLE_ADMIN).first()
doan = User.objects.filter(role=User.ROLE_DOAN_TRUONG).first()
gvcn = User.objects.filter(role=User.ROLE_GVCN).first()

def test_ep(name, user, view_fn, url, **kwargs):
    req = factory.get(url)
    force_authenticate(req, user=user)
    with CaptureQueriesContext(connection) as ctx:
        t0 = time.perf_counter()
        res = view_fn(req, **kwargs)
        res.render() if hasattr(res, 'render') else None
        dt = (time.perf_counter() - t0) * 1000
    print(f"[{name}] {user.role}: {dt:.2f}ms, {len(ctx.captured_queries)} queries, status {res.status_code}, {len(getattr(res, 'content', b''))} bytes", flush=True)
    return dt, len(ctx.captured_queries)

print("Starting individual API profiling...", flush=True)
test_ep("SystemStats", admin, SystemStatsAPIView.as_view(), '/api/core/system/stats/')
test_ep("SystemStats", doan, SystemStatsAPIView.as_view(), '/api/core/system/stats/')
test_ep("SystemStats", gvcn, SystemStatsAPIView.as_view(), '/api/core/system/stats/')

test_ep("CompDashboard", admin, CompetitionPeriodViewSet.as_view({'get': 'dashboard'}), '/api/competition/periods/dashboard/')
test_ep("CompDashboard", doan, CompetitionPeriodViewSet.as_view({'get': 'dashboard'}), '/api/competition/periods/dashboard/')
test_ep("CompDashboard", gvcn, CompetitionPeriodViewSet.as_view({'get': 'dashboard'}), '/api/competition/periods/dashboard/')

test_ep("CompScoresW7", admin, CompetitionPeriodViewSet.as_view({'get': 'scores'}), '/api/competition/periods/1/scores/', pk=1)
test_ep("CompScoresW7", doan, CompetitionPeriodViewSet.as_view({'get': 'scores'}), '/api/competition/periods/1/scores/', pk=1)
test_ep("CompScoresW7", gvcn, CompetitionPeriodViewSet.as_view({'get': 'scores'}), '/api/competition/periods/1/scores/', pk=1)

test_ep("CompFiltersMeta", admin, CompetitionPeriodViewSet.as_view({'get': 'filters_meta'}), '/api/competition/periods/filters-meta/')

test_ep("ConductViolations", admin, ViolationRecordViewSet.as_view({'get': 'list'}), '/api/conduct/violations/')
test_ep("ConductViolations", doan, ViolationRecordViewSet.as_view({'get': 'list'}), '/api/conduct/violations/')
test_ep("ConductViolations", gvcn, ViolationRecordViewSet.as_view({'get': 'list'}), '/api/conduct/violations/')

test_ep("SchoolClasses", admin, SchoolClassViewSet.as_view({'get': 'list'}), '/api/conduct/classes/')

test_ep("StudentFeedback", admin, StudentFeedbackViewSet.as_view({'get': 'list'}), '/api/conduct/feedbacks/')
test_ep("StudentFeedback", gvcn, StudentFeedbackViewSet.as_view({'get': 'list'}), '/api/conduct/feedbacks/')

print("All tests finished successfully!", flush=True)
