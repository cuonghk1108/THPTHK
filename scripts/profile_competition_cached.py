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

factory = APIRequestFactory()

admin = User.objects.filter(is_superuser=True).first() or User.objects.filter(role=User.ROLE_ADMIN).first()
doan = User.objects.filter(role=User.ROLE_DOAN_TRUONG).first()
gvcn = User.objects.filter(role=User.ROLE_GVCN).first()
student = User.objects.filter(role=User.ROLE_HOC_SINH).first()

users = [('Admin', admin), ('DoanTruong', doan), ('GVCN', gvcn), ('HocSinh', student)]

from core.views import SystemStatsAPIView
from competition.views import CompetitionPeriodViewSet

endpoints = [
    ('SystemStats', '/api/core/system/stats/', SystemStatsAPIView.as_view(), {}),
    ('CompetitionDashboard', '/api/competition/periods/dashboard/', CompetitionPeriodViewSet.as_view({'get': 'dashboard'}), {}),
    ('CompetitionScores_W7', '/api/competition/periods/1/scores/', CompetitionPeriodViewSet.as_view({'get': 'scores'}), {'pk': 1}),
    ('CompetitionFiltersMeta', '/api/competition/periods/filters-meta/', CompetitionPeriodViewSet.as_view({'get': 'filters_meta'}), {}),
]

print("="*105, flush=True)
print(f"{'Endpoint':<25} | {'User':<12} | {'Uncached Time (Q)':<18} | {'Cached Time (Q)':<18} | {'Speedup':<12}", flush=True)
print("="*105, flush=True)

for ep_name, ep_url, ep_view, ep_kwargs in endpoints:
    for u_label, u_obj in users:
        if not u_obj:
            continue
        req = factory.get(ep_url)
        force_authenticate(req, user=u_obj)
        
        # 1. First Call: Cache Miss
        with CaptureQueriesContext(connection) as ctx1:
            t0 = time.perf_counter()
            res1 = ep_view(req, **ep_kwargs)
            res1.render() if hasattr(res1, 'render') else None
            time_miss = (time.perf_counter() - t0) * 1000
            q_miss = len(ctx1.captured_queries)
            
        # 2. Second Call: Cache Hit
        with CaptureQueriesContext(connection) as ctx2:
            t1 = time.perf_counter()
            res2 = ep_view(req, **ep_kwargs)
            res2.render() if hasattr(res2, 'render') else None
            time_hit = (time.perf_counter() - t1) * 1000
            q_hit = len(ctx2.captured_queries)

        speedup = f"{time_miss / max(time_hit, 0.01):,.0f}x"
        miss_str = f"{time_miss:>7.2f}ms ({q_miss}q)"
        hit_str = f"{time_hit:>7.2f}ms ({q_hit}q)"
        
        print(f"{ep_name:<25} | {u_label:<12} | {miss_str:<18} | {hit_str:<18} | {speedup:>10}", flush=True)

print("="*105, flush=True)
print("EMPIRICAL BENCHMARK COMPLETED", flush=True)
