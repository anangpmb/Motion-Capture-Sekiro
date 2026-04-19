@echo off
:: Cek apakah sudah running sebagai Admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [✔] Administrator Access Confirmed.
) else (
    echo [!] Meminta Hak Akses Administrator...
    powershell -Command "Start-Process '%0' -Verb RunAs"
    exit /b
)

:: Jalankan launcher menggunakan Python utama di PC kamu
:: Ganti 'python' dengan path lengkap jika python tidak ada di PATH
python launcher.py
pause