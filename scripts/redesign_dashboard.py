import os
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Xuan Cuong\Desktop\hk-student-hub")
INDEX_PATH = BASE_DIR / "templates" / "index.html"
APP_JS_PATH = BASE_DIR / "static" / "app.js"

with open(INDEX_PATH, 'r', encoding='utf-8') as f:
    index_text = f.read()

# 1. Check CSS target
css_start = index_text.find("/* ===== MODERN EDTECH DASHBOARD DESIGN SYSTEM ===== */")
css_end = index_text.find("/* ===== MODERN SCHOOL PORTAL & EDTECH DESIGN SYSTEM ===== */")
print("CSS start:", css_start, "end:", css_end)

# 2. Check TAB 1 target
tab_start = index_text.find("<!-- TAB 1: DASHBOARD -->")
tab_end = index_text.find("<section id=\"tab-student-approvals\"")
print("TAB start:", tab_start, "end:", tab_end)
if tab_start != -1 and tab_end != -1:
    print("TAB 1 Content:")
    print(index_text[tab_start:tab_end])

# 3. Check App.js target
with open(APP_JS_PATH, 'r', encoding='utf-8') as f:
    app_text = f.read()

app_start = app_text.find("// 1. DASHBOARD MODULE – MODERN EDTECH & CLEAN ACADEMIC SAAS")
app_end = app_text.find("// 2. CONDUCT & VIOLATIONS MODULE")
print("App start:", app_start, "end:", app_end)
