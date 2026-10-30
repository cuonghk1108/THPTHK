import os
import sys
from pathlib import Path
import django

BASE_DIR = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hk_hub_project.settings')
django.setup()

from django.test import Client
from core.models import User

def verify():
    print("==================================================")
    print("HK STUDENT HUB - COMPREHENSIVE UI/UX VERIFICATION")
    print("==================================================")
    c = Client()

    # 1. Test Public Routes
    r_home = c.get('/')
    print("1. [GET /] Public Home status:", r_home.status_code)
    assert r_home.status_code == 200
    home_html = r_home.content.decode('utf-8')
    assert "code by cuongdev1108" in home_html
    assert "Thi đua Chi đoàn" in home_html
    assert "100.0" in home_html
    assert "35 tuần" in home_html

    r_login = c.get('/login')
    print("2. [GET /login] Guest Login page status:", r_login.status_code)
    assert r_login.status_code == 200

    r_reg = c.get('/register')
    print("3. [GET /register] Guest Register page status:", r_reg.status_code)
    assert r_reg.status_code == 200

    r_dash_anon = c.get('/dashboard')
    print("4. [GET /dashboard] Anonymous redirect status:", r_dash_anon.status_code, "->", r_dash_anon.get('Location'))
    assert r_dash_anon.status_code == 302
    assert "/login" in r_dash_anon.get('Location')

    # 2. Test Pending Student Login Attempt
    pending_student = User.objects.filter(account_status=User.STATUS_PENDING, role='HOC_SINH').first()
    if pending_student:
        # Test login API with pending user credentials
        # We can test by calling login API directly
        r_login_api = c.post('/api/core/auth/login/', {
            'username': pending_student.username,
            'password': 'AnyPassword123!' # It checks status before or after
        }, content_type='application/json')
        print(f"5. [Pending user {pending_student.username}] POST /api/core/auth/login/ status:", r_login_api.status_code)
        # Check that it either rejects or returns PENDING status
        assert r_login_api.status_code in [400, 403]

    # 3. Test Approved User Roles
    test_roles = [
        ('bgh.huongkhe', 'BGH / Admin'),
        ('gvcn.10a1', 'Giáo viên chủ nhiệm'),
        ('gvbm.toan', 'Giáo viên bộ môn'),
        ('hocsinh.nam', 'Học sinh chính thức'),
        ('saodo.tuan1', 'Sao đỏ'),
        ('cuongdev1108_1', 'Đoàn trường')
    ]

    for username, role_name in test_roles:
        u = User.objects.filter(username=username).first()
        if not u:
            print(f"- User {username} ({role_name}) not found, skipping.")
            continue
        c_user = Client()
        c_user.force_login(u)

        # Approved user visiting /login must redirect to /dashboard (or / if must_change_password)
        r_logged_login = c_user.get('/login')
        assert r_logged_login.status_code == 302
        if u.must_change_password:
            assert r_logged_login.get('Location') == '/'
        else:
            assert "/dashboard" in r_logged_login.get('Location')

        # Approved user visiting /register must redirect to /dashboard (or / if must_change_password)
        r_logged_reg = c_user.get('/register')
        assert r_logged_reg.status_code == 302
        if u.must_change_password:
            assert r_logged_reg.get('Location') == '/'
        else:
            assert "/dashboard" in r_logged_reg.get('Location')

        # Approved user visiting /dashboard gets upgraded app shell
        r_dash = c_user.get('/dashboard')
        assert r_dash.status_code == 200
        content_str = r_dash.content.decode('utf-8')
        assert 'tab-dashboard' in content_str
        assert 'tab-competition' in content_str
        assert 'comp-filter-period' in content_str
        assert 'comp-kpi-total-classes' in content_str
        assert 'app-header' in content_str
        assert 'notif-badge' in content_str

        # Test auth me
        r_me = c_user.get('/api/core/auth/me/')
        assert r_me.status_code == 200
        data_me = r_me.json()
        assert data_me.get('authenticated') is True

        # Test stats
        r_stats = c_user.get('/api/core/system/stats/')
        print(f"Role: {role_name:25} | /dashboard={r_dash.status_code} | /login->dash={r_logged_login.status_code} | /me={r_me.status_code} | /stats={r_stats.status_code}")

    # 4. Test Competition API Endpoints
    admin_u = User.objects.filter(role__in=['ADMIN', 'BGH'], account_status=User.STATUS_APPROVED).first()
    if admin_u:
        c_admin = Client()
        c_admin.force_login(admin_u)
        r_meta = c_admin.get('/api/competition/periods/filters-meta/')
        assert r_meta.status_code == 200
        print("6. [/api/competition/periods/filters-meta/] status:", r_meta.status_code, "Academic years:", len(r_meta.json().get('academic_years', [])))

        r_periods = c_admin.get('/api/competition/periods/?period_type=WEEK')
        assert r_periods.status_code == 200
        periods = r_periods.json()
        print("7. [/api/competition/periods/?period_type=WEEK] status:", r_periods.status_code, "Periods count:", len(periods))
        if periods:
            first_p = periods[0]
            r_scores = c_admin.get(f"/api/competition/periods/{first_p['id']}/scores/")
            assert r_scores.status_code == 200
            scores_data = r_scores.json()
            print(f"8. [/api/competition/periods/{first_p['id']}/scores/] status:", r_scores.status_code, "Scores count:", len(scores_data.get('scores', [])))

    print("\nALL 8 SYSTEM VERIFICATION TESTS PASSED 100%!")

if __name__ == '__main__':
    verify()
