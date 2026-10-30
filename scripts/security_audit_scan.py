import os
import re
import ast

BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"

def check_sqli():
    print("=== [1. SQL INJECTION AUDIT] ===")
    patterns = [
        r'cursor\.execute\s*\(\s*[f"\'].*?%s',
        r'cursor\.execute\s*\(\s*f["\']',
        r'cursor\.execute\s*\(\s*["\'].*?\.(?:format|%)\b',
        r'\.raw\s*\(\s*f["\']',
        r'\.raw\s*\(\s*["\'].*?\.(?:format|%)\b',
        r'\.extra\s*\(',
    ]
    matches = []
    for root, dirs, files in os.walk(BASE_DIR):
        if any(skip in root for skip in ['.venv', 'staticfiles', '.git', 'node_modules']):
            continue
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                for idx, line in enumerate(lines):
                    for pat in patterns:
                        if re.search(pat, line, re.IGNORECASE):
                            rel_path = os.path.relpath(path, BASE_DIR)
                            matches.append((rel_path, idx + 1, line.strip()))
    if matches:
        for m in matches:
            print(f"  [!] {m[0]}:{m[1]} -> {m[2]}")
    else:
        print("  [OK] No raw cursor.execute/raw/extra SQL injection patterns found in python code.")

def check_xss():
    print("\n=== [2. CROSS-SITE SCRIPTING (XSS) AUDIT] ===")
    # 2.1 Django templates
    template_dir = os.path.join(BASE_DIR, "templates")
    if os.path.exists(template_dir):
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith('.html'):
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines):
                        if '|safe' in line or 'autoescape off' in line:
                            rel = os.path.relpath(path, BASE_DIR)
                            print(f"  [Template |safe] {rel}:{idx+1} -> {line.strip()[:100]}")

    # 2.2 Frontend JS innerHTML unescaped interpolation
    js_files = [os.path.join(BASE_DIR, "static", "app.js"), os.path.join(BASE_DIR, "static", "public.js")]
    for js_path in js_files:
        if os.path.exists(js_path):
            rel = os.path.relpath(js_path, BASE_DIR)
            with open(js_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            # find innerHTML assignments with template literals
            # look for ${...} inside innerHTML that does NOT use escapeHtml
            lines = content.split('\n')
            unescaped_findings = []
            for idx, line in enumerate(lines):
                if '.innerHTML' in line or 'innerHTML =' in line or 'innerHTML+=' in line:
                    # check surrounding 5 lines
                    context = lines[max(0, idx-2):min(len(lines), idx+8)]
                    context_str = " ".join(c.strip() for c in context)
                    # Check if there is ${something} where something doesn't have escapeHtml
                    # or if variables like .notes, .content, .feedback, .description are used without escapeHtml
                    for field in ['notes', 'content', 'comment', 'feedback', 'reason', 'student_name', 'full_name', 'title']:
                        pattern = rf'\${{[^}}]*\b{field}\b[^}}]*}}'
                        for match in re.finditer(pattern, context_str):
                            matched_expr = match.group(0)
                            if 'escapeHtml' not in matched_expr:
                                unescaped_findings.append((idx+1, matched_expr, line.strip()[:80]))
            print(f"  [JS innerHTML scan in {rel}]: Found {len(unescaped_findings)} potential unescaped fields.")
            for uf in unescaped_findings[:15]:
                print(f"    Line {uf[0]}: {uf[1]} (in {uf[2]})")

def check_auth_and_idor():
    print("\n=== [3 & 4. AUTHENTICATION & IDOR/BOLA ACCESS CONTROL AUDIT] ===")
    views_files = []
    for root, dirs, files in os.walk(BASE_DIR):
        if any(skip in root for skip in ['.venv', 'staticfiles', '.git']):
            continue
        for file in files:
            if file == 'views.py':
                views_files.append(os.path.join(root, file))

    for vf in views_files:
        rel = os.path.relpath(vf, BASE_DIR)
        with open(vf, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Check permissions on ViewSets and APIViews
        current_class = None
        for idx, line in enumerate(lines):
            class_match = re.match(r'class\s+([A-Za-z0-9_]+)\s*\((.*?)\):', line)
            if class_match:
                current_class = class_match.group(1)
            
            # Check for permission_classes
            if 'permission_classes' in line and current_class:
                if 'AllowAny' in line:
                    print(f"  [Perm AllowAny] {rel}:{idx+1} in {current_class} -> {line.strip()}")
            
            # Check for missing object permission in update/destroy/partial_update
            if re.match(r'\s*def\s+(?:destroy|update|partial_update)\s*\(', line):
                # inspect next 15 lines
                fn_lines = lines[idx:min(len(lines), idx+20)]
                fn_str = "".join(fn_lines)
                if 'check_object_permissions' not in fn_str and 'get_object' not in fn_str:
                    print(f"  [Potential BOLA] {rel}:{idx+1} {line.strip()} in {current_class} does not check get_object or check_object_permissions")

def check_secrets():
    print("\n=== [5. SENSITIVE DATA & SECRETS AUDIT] ===")
    settings_path = os.path.join(BASE_DIR, "hk_hub_project", "settings.py")
    if os.path.exists(settings_path):
        with open(settings_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        for idx, line in enumerate(lines):
            clean = line.strip()
            if any(k in clean for k in ['SECRET_KEY', 'DEBUG =', 'PASSWORD =', 'API_KEY', 'CLIENT_SECRET']):
                # Don't print full secrets if any, show pattern
                masked = re.sub(r'["\'][a-zA-Z0-9_\-\.]{8,}["\']', '"***REDACTED***"', clean)
                print(f"  {settings_path}:{idx+1} -> {masked}")

if __name__ == '__main__':
    check_sqli()
    check_xss()
    check_auth_and_idor()
    check_secrets()
