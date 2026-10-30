# scripts/fix_settings_env.py
p = r'C:\Users\Xuan Cuong\Desktop\hk-student-hub\hk_hub_project\settings.py'
with open(p, 'r', encoding='utf-8') as f:
    text = f.read()

target = "load_dotenv(BASE_DIR / '.env.local', override=True)\nload_dotenv(BASE_DIR / '.env', override=True)"
replacement = "load_dotenv(BASE_DIR / '.env', override=True)\nload_dotenv(BASE_DIR / '.env.local', override=True)"

if target in text:
    text = text.replace(target, replacement, 1)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated settings.py (LF)")
else:
    target_crlf = "load_dotenv(BASE_DIR / '.env.local', override=True)\r\nload_dotenv(BASE_DIR / '.env', override=True)"
    replacement_crlf = "load_dotenv(BASE_DIR / '.env', override=True)\r\nload_dotenv(BASE_DIR / '.env.local', override=True)"
    if target_crlf in text:
        text = text.replace(target_crlf, replacement_crlf, 1)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(text)
        print("Updated settings.py (CRLF)")
    else:
        print("Target not found in settings.py")
