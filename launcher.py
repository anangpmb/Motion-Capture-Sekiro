import os
import sys
import subprocess
import ctypes
import time
import shutil

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def setup_environment():
    try:
        # --- FIX PATH SYSTEM32 ---
        # Mengunci direktori ke lokasi asli file, bukan folder system32
        base_path = os.path.dirname(os.path.abspath(
            sys.executable if getattr(sys, 'frozen', False) else __file__
        ))

        # Guard: kalau base_path mengandung "venv", naik ke parent
        while 'venv' in base_path.split(os.sep):
            base_path = os.path.dirname(base_path)

        os.chdir(base_path)
        print(f"[*] Root Directory: {base_path}")

        venv_dir = os.path.join(base_path, 'venv')

        python_exec = shutil.which("python") or shutil.which("python3")

        if not python_exec:
            print("[ERROR] Python tidak ditemukan di PATH!")
            sys.exit(1)

        print(f"[*] Python ditemukan: {python_exec}")

        # Buat venv pakai subprocess, bukan venv.create()
        import subprocess
        if not os.path.exists(venv_dir):
            subprocess.run([python_exec, "-m", "venv", venv_dir], check=True)
            print("Virtual environment berhasil dibuat!")
           

        python_venv = os.path.join(base_path, 'venv', 'Scripts', 'python.exe')

        # 2. Sinkronisasi Library (Foreground)
        print("[*] Sinkronisasi Library via PIP...")
        libs = ["mediapipe==0.10.14", "opencv-python", "pandas", "scikit-learn", "pydirectinput", "PyQt5", "customtkinter"]
        
        # Menggunakan python -m pip agar lebih stabil
        subprocess.run([python_venv, "-m", "pip", "install", "--upgrade"] + libs, check=True)

        # 3. Jalankan Dashboard
        main_gui = os.path.join(base_path, "main_gui.py")
        if os.path.exists(main_gui):
            print(f"\n[✔] Membuka Dashboard UI...")
            # Popen agar launcher bisa menutup diri sementara GUI tetap jalan
            subprocess.Popen([python_venv, main_gui], creationflags=subprocess.CREATE_NEW_CONSOLE)
            time.sleep(2)
        else:
            print(f"\n[ERROR] File {main_gui} tidak ditemukan!")
            os.system("pause")

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        os.system("pause")

if __name__ == "__main__":
    if is_admin():
        setup_environment()
    else:
        # PEMUTUS LOOP: Cek jika sudah pernah mencoba panggil Admin
        if "--no-loop" not in sys.argv:
            print("[*] Meminta Hak Akses Administrator...")
            
            # Ambil path executable atau script
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]] + ["--no-loop"])
            
            # Menentukan cara panggil (Script vs EXE)
            if getattr(sys, 'frozen', False): # Jika sudah jadi EXE
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
            else: # Jika masih file .py
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        else:
            print("[ERROR] Gagal mendapatkan izin Admin. Klik kanan > Run as Administrator secara manual.")
            os.system("pause")