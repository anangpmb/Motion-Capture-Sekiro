import customtkinter as ctk
import json
import subprocess
import threading
import sys
import os
import ctypes

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class PoseManager(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Pose & Mapping Editor")
        self.geometry("600x550")
        self.config_path = "mapping.json"
        self.data = self.load_config()

        ctk.CTkLabel(self, text="POSE MANAGEMENT", font=("Arial", 18, "bold")).pack(pady=10)

        # Form Input
        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.pack(pady=10, padx=20, fill="x")

        self.entry_name = ctk.CTkEntry(self.form_frame, placeholder_text="Nama Pose (ex: attack)", width=150)
        self.entry_name.grid(row=0, column=0, padx=5, pady=5)

        self.entry_key = ctk.CTkEntry(self.form_frame, placeholder_text="Tombol (ex: r1)", width=100)
        self.entry_key.grid(row=0, column=1, padx=5, pady=5)

        self.type_var = ctk.StringVar(value="tap")
        self.combo_type = ctk.CTkComboBox(self.form_frame, values=["tap", "hold"], variable=self.type_var, width=100)
        self.combo_type.grid(row=0, column=2, padx=5, pady=5)

        self.btn_add = ctk.CTkButton(self.form_frame, text="Tambah Mapping", command=self.add_pose)
        self.btn_add.grid(row=1, column=0, columnspan=3, pady=10, sticky="ew", padx=5)

        # List Pose
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Daftar Mapping & Folder")
        self.list_frame.pack(pady=10, padx=20, fill="both", expand=True)
        self.render_list()

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {"poses": []}

    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.data, f, indent=4)
        for p in self.data["poses"]:
            os.makedirs(p["folder"], exist_ok=True)

    def add_pose(self):
        name = self.entry_name.get().lower().strip()
        key = self.entry_key.get().lower().strip()
        if name and key:
            new_pose = {
                "name": name,
                "key": key,
                "type": self.type_var.get(),
                "folder": os.path.join("data", "videos", name)
            }
            self.data["poses"].append(new_pose)
            self.save_config()
            self.render_list()
            self.entry_name.delete(0, 'end')
            self.entry_key.delete(0, 'end')

    def delete_pose(self, index):
        self.data.get("poses", []).pop(index)
        self.save_config()
        self.render_list()

    def render_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        for i, pose in enumerate(self.data.get("poses", [])):
            item = ctk.CTkFrame(self.list_frame)
            item.pack(fill="x", pady=2, padx=5)
            info = f"{pose['name'].upper()} -> Key: {pose['key']} ({pose['type']})"
            ctk.CTkLabel(item, text=info).pack(side="left", padx=10)
            ctk.CTkButton(item, text="X", width=30, fg_color="#e74c3c", command=lambda idx=i: self.delete_pose(idx)).pack(side="right", padx=5)

class SekiroDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SHINOBI MOCAP SYSTEM - ADMIN MODE")
        self.geometry("500x550")

        self.header = ctk.CTkLabel(self, text="SEKIRO HYBRID CONTROLLER", font=("Orbitron", 22, "bold"))
        self.header.pack(pady=20)

        # Admin Status
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        status_text = "STATUS: ADMIN ACTIVE" if is_admin else "STATUS: PLEASE RUN AS ADMIN"
        status_color = "#2ecc71" if is_admin else "#e74c3c"
        ctk.CTkLabel(self, text=status_text, text_color=status_color, font=("Arial", 12, "bold")).pack()

        # Tombol-tombol Utama
        self.btn_mapping = ctk.CTkButton(self, text="MANAGE POSES & MAPPING", height=45, width=300, 
                                         fg_color="#8e44ad", command=self.open_mapping)
        self.btn_mapping.pack(pady=15)

        self.btn_run = ctk.CTkButton(self, text="START MOCAP APP", height=50, width=300, 
                                     fg_color="#2980b9", command=self.start_mocap)
        self.btn_run.pack(pady=10)

        self.btn_export = ctk.CTkButton(self, text="EXPORT VIDEO TO CSV", height=40, width=300, command=self.start_export)
        self.btn_export.pack(pady=10)

        self.btn_train = ctk.CTkButton(self, text="TRAIN AI MODEL", height=40, width=300, command=self.start_training)
        self.btn_train.pack(pady=10)

        self.footer = ctk.CTkLabel(self, text="Tangan Kanan: Aksi | Tangan Kiri: Controller", font=("Arial", 10, "italic"))
        self.footer.pack(side="bottom", pady=15)

    def open_mapping(self):
        PoseManager(self)

    def start_mocap(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        venv_python = os.path.join(base_path, 'venv', 'Scripts', 'python.exe')
        if os.path.exists(venv_python):
            subprocess.Popen([venv_python, "app.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            print("Error: Venv tidak ditemukan!")

    def start_export(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        venv_python = os.path.join(base_path, 'venv', 'Scripts', 'python.exe')
        subprocess.Popen(['start', 'cmd', '/k', venv_python, 'extract_to_csv.py'], shell=True)

    def start_training(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        venv_python = os.path.join(base_path, 'venv', 'Scripts', 'python.exe')
        subprocess.Popen(['start', 'cmd', '/k', venv_python, 'train_model.py'], shell=True)

if __name__ == "__main__":
    if ctypes.windll.shell32.IsUserAnAdmin():
        app = SekiroDashboard()
        app.mainloop()
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{sys.argv[0]}"', None, 1)