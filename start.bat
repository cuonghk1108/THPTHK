@echo off
title HK Student Hub - THPT Huong Khe
cd /d "%~dp0"

echo ===============================================================================
echo        TRUONG THPT HUONG KHE - HA TINH
echo        HK STUDENT HUB - HE THONG QUAN LY NEN NEP VA THI DUA DOAN TRUONG
echo        "Ky cuong so - Thi dua minh bach - Dong hanh cung hoc sinh"
echo ===============================================================================
echo.

:: 1. Kiem tra moi truong Python
set "PYTHON_EXE="
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    echo [*] Dang su dung moi truong ao: .venv\Scripts\python.exe
) else (
    set "PYTHON_EXE=python"
    echo [*] Dang su dung Python he thong: python
)

echo.
:: 2. Giai phong cong 8000 neu co tien trinh cu dang chiem giu
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: 3. Kiem tra va cap nhat Database (Migrations & Seed)
echo [*] Dang kiem tra va cap nhat co so du lieu (Database Migrations)...
"%PYTHON_EXE%" manage.py migrate --noinput
if errorlevel 1 (
    echo [!] Canh bao: Co loi khi chay migrate.
) else (
    echo [OK] Co so du lieu da san sang.
)
"%PYTHON_EXE%" manage.py seed_hk_data >nul 2>&1

echo.
:: 4. Khoi chay SMS Worker xu ly tin nhan ngam
echo [*] Dang khoi dong SMS Worker xu ly thong bao...
start "HK Student Hub - SMS Worker" /min cmd /c "title HK Student Hub - SMS Worker && \"%PYTHON_EXE%\" manage.py process_sms_queue --loop"
echo [*] Dang khoi dong Email Worker gui email nen...
start "HK Student Hub - Email Worker" /min cmd /c "title HK Student Hub - Email Worker && \"%PYTHON_EXE%\" manage.py process_email_queue --loop"

echo.
:: 5. Hen gio tu dong mo trinh duyet sau 3 giay
echo [*] Dang mo trinh duyet tai: http://127.0.0.1:8000/
start "" /b cmd /c "ping 127.0.0.1 -n 3 >nul && start http://127.0.0.1:8000/"

echo.
echo ===============================================================================
echo  HE THONG DA KHOI CHAY THANH CONG!
echo  - Trang chu Web App: http://127.0.0.1:8000/
echo  - Trang Dang ky:     http://127.0.0.1:8000/register
echo  - Trang Quan tri:    http://127.0.0.1:8000/admin/users
echo.
echo  Tai khoan Quan tri vien:
echo    + Super Admin: superadmin_hk / super_secure_pass_2026
echo    + Admin:       admin / admin_password_2026
echo.
echo  [Nhan Ctrl + C de dung may chu]
echo ===============================================================================
echo.

:: 6. Chay Django Web Server
"%PYTHON_EXE%" manage.py runserver 127.0.0.1:8000

:: Don dep worker khi tat server
taskkill /FI "WINDOWTITLE eq HK Student Hub - SMS Worker*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq HK Student Hub - Email Worker*" /F >nul 2>&1
echo.
echo [*] Da dung he thong.
pause
