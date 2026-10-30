@echo off
title HK Student Hub - Setup Tunnel edumentor.edu.vn
cd /d "%~dp0"

echo ===============================================================================
echo        THIET LAP CLOUDFLARE TUNNEL CHO EDUMENTOR.EDU.VN
echo        Tai khoan: cuonghk1108@gmail.com
echo ===============================================================================
echo.

if not exist "%USERPROFILE%\.cloudflared\cert.pem" (
    echo [!] Chua tim thay chung chi xac thuc cert.pem.
    echo Vui long truy cap duong dan sau tren trinh duyet va dang nhap bang cuonghk1108@gmail.com:
    echo.
    echo https://dash.cloudflare.com/argotunnel?aud=&callback=https%%3A%%2F%%2Flogin.cloudflareaccess.org%%2F65dQZu3GNJpNv23ZbR6COu-EcFDZAmAxa_LLTsYuviY%%3D
    echo.
    pause
)

echo [*] Da tim thay cert.pem! Dang tao Tunnel hk-student-hub...
.\cloudflared.exe tunnel create hk-student-hub

echo [*] Dang tao ban ghi DNS tu dong cho edumentor.edu.vn...
.\cloudflared.exe tunnel route dns hk-student-hub edumentor.edu.vn
.\cloudflared.exe tunnel route dns hk-student-hub www.edumentor.edu.vn

echo.
echo ===============================================================================
echo  DANG KHOI CHAY TUNNEL CHO EDUMENTOR.EDU.VN...
echo ===============================================================================
.\cloudflared.exe tunnel --config cloudflare\tunnel-config.yml run hk-student-hub
