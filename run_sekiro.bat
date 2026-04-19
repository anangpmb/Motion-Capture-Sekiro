@echo off
title Sekiro Mocap App
echo Menghidupkan Virtual Environment...

:: 1. Masuk ke folder venv dan aktifkan
call venv\Scripts\activate

:: 2. Set environment variable jika perlu (opsional)
set PYTHONIOENCODING=utf-8

echo Menjalankan app.py...
echo Tekan Ctrl+C di terminal ini untuk berhenti.

:: 3. Jalankan aplikasi Python
python app.py

:: 4. Jika aplikasi tertutup, venv akan ditutup secara automatik
pause