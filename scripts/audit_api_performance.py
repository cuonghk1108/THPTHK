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
from competition.models import CompetitionPeriod

factory = APIRequestFactory()

admin = User.objects.filter(is_superuser=True).first() or User.objects.filter(role=User.ROLE_ADMIN).first()
doan = User.objects.filter(role=User.ROLE_DOAN_TRUONG).first()
gvcn = User.objects.filter(role=User.ROLE_GVCN).first()
student = User.objects.filter(role=User.ROLE_HOC_SINH).first()

users = [('Admin', admin), ('DoanTruong', doan), ('GVCN', gvcn), ('HocSinh', student)]

from core.views import SystemStatsAPIView
from competition.views import CompetitionPeriodViewSet
from conduct.views import ViolationRecordViewSet, StudentFeedbackViewSet, SchoolClassViewSet

endpoints = [
    ('SystemStats', '/api/core/system/stats/', SystemStatsAPIView.as_view(), {}),
    ('CompetitionDashboard', '/api/competition/periods/dashboard/', CompetitionPeriodViewSet.as_view({'get': 'dashboard'}), {}),
    ('CompetitionScores_W7', '/api/competition/periods/1/scores/', CompetitionPeriodViewSet.as_view({'get': 'scores'}), {'pk': 1}),
    ('CompetitionFiltersMeta', '/api/competition/periods/filters-meta/', CompetitionPeriodViewSet.as_view({'get': 'filters_meta'}), {}),
    ('ConductViolations', '/api/conduct/violations/', ViolationRecordViewSet.as_view({'get': 'list'}), {}),
    ('StudentFeedback', '/api/conduct/feedbacks/', StudentFeedbackViewSet.as_view({'get': 'list'}), {}),
    ('SchoolClasses', '/api/conduct/classes/', SchoolClassViewSet.as_view({'get': 'list'}), {}),
]

print("="*80)
print(f"{'Endpoint':<25} | {'User':<12} | {'Time (ms)':<10} | {'Queries':<8} | {'Status':<6} | {'Bytes':<8}")
print("="*80)

audit_results = []

for ep_name, ep_url, ep_view, ep_kwargs in endpoints:
    for u_label, u_obj in users:
        if not u_obj:
            continue
        req = factory.get(ep_url)
        force_authenticate(req, user=u_obj)
        
        with CaptureQueriesContext(connection) as ctx:
            t0 = time.perf_counter()
            try:
                res = ep_view(req, **ep_kwargs)
                res.render() if hasattr(res, 'render') else None
                elapsed_ms = (time.perf_counter() - t0) * 1000
                q_count = len(ctx.captured_queries)
                content_len = len(res.content) if hasattr(res, 'content') else 0
                status_code = res.status_code
            except Exception as e:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                q_count = len(ctx.captured_queries)
                content_len = 0
                status_code = f"ERR: {type(e).__name__}"
        
        print(f"{ep_name:<25} | {u_label:<12} | {elapsed_ms:>8.2f}ms | {q_count:>7} | {status_code!s:<6} | {content_len:>7}")
        audit_results.append({
            'endpoint': ep_name,
            'user': u_label,
            'time_ms': elapsed_ms,
            'queries': q_count,
            'status': status_code,
            'bytes': content_len,
            'query_samples': [q['sql'] for q in ctx.captured_queries[:5]]
        })

print("="*80)
print("AUDIT PROFILING FINISHED")
