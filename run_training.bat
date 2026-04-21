@echo off
title Sekiro Model Trainer
echo [INFO] Mengaktifkan Virtual Environment...
call venv\Scripts\activate

echo [INFO] Melatih Model AI (Random Forest)...
:: Ganti 'train.py' dengan nama file script training kamu jika berbeda
python train_model.py

echo.
echo [DONE] Model .pkl baru telah dibuat!
echo [INFO] Kamu sekarang bisa menjalankan run_sekiro.bat untuk bermain.
pause