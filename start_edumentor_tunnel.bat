@echo off
title HK Student Hub - Cloudflare Tunnel (edumentor.io.vn)
cd /d "%~dp0"

echo ===============================================================================
echo        TRUONG THPT HUONG KHE - HA TINH
echo        HK STUDENT HUB - CLOUDFLARE EDGE TUNNEL (EDUMENTOR.IO.VN)
echo        Tunnel ID: 720711cc-b3e9-41f4-bb39-865c353ea504
echo ===============================================================================
echo.

:: 1. Xac dinh trinh thuc thi Python
set "PYTHON_EXE="
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

:: 2. Kiem tra may chu Django cong 8000
netstat -aon | findstr :8000 | findstr LISTENING >nul
if errorlevel 1 (
    echo [*] Dang khoi dong may chu HK Student Hub tai cong 8000...
    start "HK Student Hub - Web Server" /min cmd /c "title HK Student Hub - Web Server && \"%PYTHON_EXE%\" manage.py runserver 127.0.0.1:8000"
    ping 127.0.0.1 -n 4 >nul
) else (
    echo [OK] May chu HK Student Hub dang hoat dong tren cong 8000.
)

echo [*] Dang ket noi Cloudflare Edge cho edumentor.io.vn...
.\cloudflared.exe tunnel --url http://127.0.0.1:8000 run --token eyJhIjoiMTc5YTQyMWU2ZDM0NGZiN2Q1YjQzNTJjMDJhNzJiMmEiLCJ0IjoiNzIwNzExY2MtYjNlOS00MWY0LWJiMzktODY1YzM1M2VhNTA0IiwicyI6ImM5bkVIOXNoRGc5bFRQNDlmdWpmR2xZVjFxbXVDbjJNRGF6eExwazJCcUk9In0=
