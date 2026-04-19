import customtkinter as ctk
import subprocess
import threading
import sys
import os
import ctypes

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SekiroDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SHINOBI MOCAP SYSTEM - ADMIN MODE")
        self.geometry("500x450")

        self.header = ctk.CTkLabel(self, text="SEKIRO HYBRID CONTROLLER", font=("Orbitron", 24, "bold"))
        self.header.pack(pady=20)

        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        status_text = "STATUS: ADMIN ACTIVE" if is_admin else "STATUS: PLEASE RUN AS ADMIN"
        status_color = "#2ecc71" if is_admin else "#e74c3c"
        self.status_label = ctk.CTkLabel(self, text=status_text, text_color=status_color, font=("Arial", 12, "bold"))
        self.status_label.pack(pady=5)

        self.btn_run = ctk.CTkButton(self, text="START MOCAP APP", height=50, width=300, 
                                     fg_color="#2980b9", hover_color="#3498db",
                                     command=self.start_mocap)
        self.btn_run.pack(pady=15)

        self.btn_export = ctk.CTkButton(self, text="EXPORT VIDEO TO CSV (MENU)", height=40, width=300,
                                        command=self.start_export)
        self.btn_export.pack(pady=10)

        self.btn_train = ctk.CTkButton(self, text="TRAIN AI MODEL", height=40, width=300,
                                       command=self.start_training)
        self.btn_train.pack(pady=10)

        self.footer = ctk.CTkLabel(self, text="Tangan Kanan: Aksi | Tangan Kiri: Controller", font=("Arial", 10, "italic"))
        self.footer.pack(side="bottom", pady=20)

    def start_mocap(self):
        # Ambil path absolut ke venv python
        base_path = os.path.dirname(os.path.abspath(__file__))
        venv_python = os.path.join(base_path, 'venv', 'Scripts', 'python.exe')
        
        if os.path.exists(venv_python):
            # Gunakan subprocess.Popen agar GUI tidak membeku (freeze)
            subprocess.Popen([venv_python, "app.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            print("Error: Venv tidak ditemukan!")

    def start_export(self):
        venv_python = os.path.join(os.getcwd(), 'venv', 'Scripts', 'python.exe')
        # Gunakan venv python agar library mediapipe/pyqt terdeteksi
        subprocess.Popen(['start', 'cmd', '/k', venv_python, 'extract_to_csv.py'], shell=True)

    def start_training(self):
        venv_python = os.path.join(os.getcwd(), 'venv', 'Scripts', 'python.exe')
        subprocess.Popen(['start', 'cmd', '/k', venv_python, 'train_model.py'], shell=True)

if __name__ == "__main__":
    if ctypes.windll.shell32.IsUserAnAdmin():
        app = SekiroDashboard()
        app.mainloop()
    else:
        # Re-run script dengan Admin privilege jika belum admin
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)