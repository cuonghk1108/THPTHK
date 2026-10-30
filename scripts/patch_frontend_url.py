# scripts/patch_frontend_url.py
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. settings.py
p_settings = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\hk_hub_project\settings.py'
with open(p_settings, 'r', encoding='utf-8') as f:
    text = f.read()

old_s = "FRONTEND_BASE_URL = os.environ.get('FRONTEND_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')"
new_s = "FRONTEND_BASE_URL = os.environ.get('FRONTEND_BASE_URL', 'https://edumentor.io.vn').rstrip('/')"

if old_s in text:
    text = text.replace(old_s, new_s)
    with open(p_settings, 'w', encoding='utf-8') as f:
        f.write(text)
    print("[OK] Updated settings.py FRONTEND_BASE_URL")
else:
    print("[SKIP] settings.py pattern not found")

# 2. conduct/email.py
p_conduct = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\conduct\email.py'
with open(p_conduct, 'r', encoding='utf-8') as f:
    text = f.read()

old_c = "frontend_base = getattr(settings, 'FRONTEND_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')"
new_c = "frontend_base = getattr(settings, 'FRONTEND_BASE_URL', 'https://edumentor.io.vn').rstrip('/')"

if old_c in text:
    text = text.replace(old_c, new_c)
    with open(p_conduct, 'w', encoding='utf-8') as f:
        f.write(text)
    print("[OK] Updated conduct/email.py FRONTEND_BASE_URL")
else:
    print("[SKIP] conduct/email.py pattern not found")

# 3. core/views.py
p_views = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\core\views.py'
with open(p_views, 'r', encoding='utf-8') as f:
    text = f.read()

old_v = """            frontend_base = getattr(settings, 'FRONTEND_BASE_URL', '').rstrip('/')
            if not frontend_base:
                frontend_base = f"{request.scheme}://{request.get_host()}"
            reset_url = f"{frontend_base}/reset-password?uid={uid}&token={token}\""""

new_v = """            # Xác định frontend_base: Ưu tiên domain edumentor từ request nếu có, hoặc FRONTEND_BASE_URL (https://edumentor.io.vn)
            host = request.get_host()
            if 'edumentor' in host:
                frontend_base = f"https://{host}"
            elif getattr(settings, 'FRONTEND_BASE_URL', ''):
                frontend_base = settings.FRONTEND_BASE_URL.rstrip('/')
            else:
                scheme = 'https' if (request.is_secure() or request.META.get('HTTP_X_FORWARDED_PROTO') == 'https') else request.scheme
                frontend_base = f"{scheme}://{host}"
            reset_url = f"{frontend_base}/reset-password?uid={uid}&token={token}\""""

if old_v in text:
    text = text.replace(old_v, new_v)
    with open(p_views, 'w', encoding='utf-8') as f:
        f.write(text)
    print("[OK] Updated core/views.py reset_url logic")
else:
    print("[SKIP] core/views.py pattern not found")

print("Done patching FRONTEND_BASE_URL!")
