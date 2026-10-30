import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\core\views.py', 'r', encoding='utf-8') as f:
    views = f.read()

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\templates\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

with open(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\static\app.js', 'r', encoding='utf-8') as f:
    app = f.read()

import re
print("--- SEARCH IN VIEWS ---")
for m in re.finditer(r'(class\s+\w*Profile\w*|def\s+profile|def\s+change_password|change-password|update-profile)', views):
    idx = m.start()
    print("Views match:", m.group(0), "at", idx)
    print(views[idx:idx+500])
    print("="*40)

print("\n--- SEARCH IN HTML FOR PROFILE ---")
pos = html.find('id="profile-form"')
if pos != -1:
    print(html[pos-100:pos+1500])
else:
    print("profile-form not found in HTML!")

pos_tab = html.find('id="tab-profile"')
if pos_tab != -1:
    print("tab-profile at", pos_tab)
    print(html[pos_tab:pos_tab+1000])

print("\n--- SEARCH IN APP.JS FOR PROFILE ---")
for m in re.finditer(r'(saveProfileChanges|loadProfile|changePassword|updateProfile)', app):
    idx = m.start()
    print("JS match:", m.group(0), "at", idx)
    print(app[idx:idx+400])
    print("="*40)
