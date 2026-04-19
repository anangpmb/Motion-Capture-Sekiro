@echo off
title Sekiro CSV Exporter
echo [INFO] Mengaktifkan Virtual Environment...
call venv\Scripts\activate

echo [INFO] Memulai Ekstraksi Video ke CSV...
echo [TIPS] Pastikan folder videos/ sudah terisi rekaman terbaru.
python extract_to_csv.py

echo.
echo [DONE] Ekstraksi selesai. Periksa data/dataset.csv
pause