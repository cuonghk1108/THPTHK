import os

files = [
    os.path.join(r'C:\Users\Xuan Cuong\Desktop\hk-student-hub', 'hk_hub_project', 'settings.py'),
    os.path.join(r'C:\Users\Xuan Cuong\.gemini\antigravity\scratch\hk-student-hub', 'hk_hub_project', 'settings.py')
]

for path in files:
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        new_lines = []
        for line in lines:
            if 'GOOGLE_OAUTH_CLIENT_ID =' in line:
                new_lines.append("GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '').strip()\n")
            elif 'GOOGLE_OAUTH_CLIENT_SECRET =' in line:
                new_lines.append("GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '').strip()\n")
            else:
                new_lines.append(line)
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("Updated:", path)
