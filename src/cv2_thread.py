import cv2
import mediapipe as mp
import numpy as np
import time
import pydirectinput
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage
from .movements import SekiroMovementController, get_movement_cooldown

# Optimasi pydirectinput agar tidak ada delay antar input
pydirectinput.PAUSE = 0.01 

class Cv2Thread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    gesture_detected_signal = pyqtSignal(str, float)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.controller = SekiroMovementController()
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        
        # State Management
        self.last_label = "idle"
        self.current_hold_key = None
        self.current_movement_key = None # Untuk melacak gerakan dasar yang sedang ditahan

    def run(self):
        cap = cv2.VideoCapture(0)
        with self.mp_holistic.Holistic(min_detection_confidence=0.7, min_tracking_confidence=0.7) as holistic:
            while self._run_flag:
                ret, frame = cap.read()
                if not ret: break

                frame = cv2.flip(frame, 1)
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = holistic.process(image)

                if results.pose_landmarks:
                    # # 1. Handle Kamera (Nose Tracking)
                    self.handle_camera(results)

                    # Ambil prediksi dari Model AI (Isyarat Tangan)
                    label, confidence = self.controller.get_predicted_movement(results)
                    self.gesture_detected_signal.emit(label, confidence)
                    
                    # Tangani semua input game (Gerakan & Aksi)
                    self.handle_game_input(label, confidence)

                # Visualisasi
                self.draw_landmarks(frame, results)
                self.update_gui_image(frame)

        cap.release()
        self.release_all_keys()

    # ========================================================
    # GAME INPUT LOGIC (AI GESTURES - TAP vs HOLD)
    # ========================================================
    def handle_game_input(self, label, confidence):
        current_time = time.time() * 1000
        
        # 1. Klasifikasi Aksi Berdasarkan Nama Label Kamu
        # Aksi Gerakan Dasar (WASD) - Ditangani sebagai tombol yang ditahan
        MOVEMENT_ACTIONS = {
            "move_forward": 'w',
            "move_backward": 's',
            "move_left": 'a',
            "move_right": 'd'
        }

        # Aksi Tempur & UI - Ditangani sebagai "Tap" atau "Hold"
        # Deflect & Crouch masuk kategori HOLD agar bisa menahan tangkisan/merunduk
        HOLD_ACTIONS = ["deflect", "crouch"] 
        
        # Aksi lainnya masuk kategori TAP (Hanya tereksekusi sekali saat pose berganti)
        TAP_ACTIONS = [
            "attack", "jump", "dash", "grapple", 
            "prosthetic", "use_item", "interact", "lock_on", "pause", "combat_art"
        ]

        # Mapping Tombol untuk Aksi Hold
        key_map = {
            "deflect": 'k',
            "crouch": 'q',
            "attack": 'j',
            "deflect": 'k',
            "jump": 'space',
            "dash": 'shift',
            "grapple": 'f',
            "prosthetic": 'o',
            "use_item": 'r',
            "interact": 'e',
            "lock_on": 'v',
            "pause": 'esc'
        }

        if confidence > 0.85:
            # --- TANGANI GERAKAN DASAR (WASD) ---
            if label in MOVEMENT_ACTIONS:
                if self.current_movement_key != MOVEMENT_ACTIONS[label]:
                    self.release_movement_hold() # Lepas gerakan sebelumnya jika ada
                    pydirectinput.keyDown(MOVEMENT_ACTIONS[label])
                    self.current_movement_key = MOVEMENT_ACTIONS[label]
                    print(f"[MOVE] Menahan {label} ({MOVEMENT_ACTIONS[label]})")
            else:
                self.release_movement_hold() # Lepas jika kembali ke idle atau aksi tempur

            # --- TANGANI AKSI TEMPUR (TAP vs HOLD) ---
            # A. LOGIKA UNTUK HOLD (DEFLECT/GUARD & CROUCH)
            if label in HOLD_ACTIONS:
                if self.current_hold_key != key_map[label]:
                    self.release_action_hold() # Lepas hold sebelumnya jika ada
                    pydirectinput.keyDown(key_map[label])
                    self.current_hold_key = key_map[label]
                    print(f"[HOLD] Menahan {label} ({key_map[label]})")

            # B. LOGIKA UNTUK TAP (ATTACK, JUMP, DLL)
            elif label in TAP_ACTIONS:
                # Cek apakah gerakan baru (agar tidak spam jika pose ditahan)
                if label != self.last_label:
                    self.release_action_hold()
                    
                    key_to_press = key_map.get(label)
                    if key_to_press:
                        pydirectinput.keyDown(key_to_press)
                        time.sleep(0.05)  # Tahan selama 50ms (setara ~3 frame game)
                        pydirectinput.keyUp(key_to_press)

                    if label == "combat_art":
                        # Logika khusus L1 + R1
                        # pydirectinput.keyDown('j')
                        # pydirectinput.press('k')
                        # pydirectinput.keyUp('j')
                        combo_keys = ['k', 'j']
                        for key in combo_keys:
                            pydirectinput.keyDown(key)
                        
                        time.sleep(1.5) # Durasi penekanan
                        
                        for key in reversed(combo_keys):
                            pydirectinput.keyUp(key)
                    
                    print(f"[TAP] Eksekusi Aksi: {label}")
                    self.last_action_time = current_time

            # C. LOGIKA JIKA KEMBALI KE IDLE
            elif label == "idle":
                self.release_action_hold()

            # Simpan label sekarang untuk pengecekan frame berikutnya
            self.last_label = label

        else:
            # Jika AI tidak yakin, lepas semua tombol tahan demi keamanan
            self.release_all_keys()
            self.last_label = "idle"

    # --- FUNGSI PEMBANTU ---
    def release_action_hold(self):
        if self.current_hold_key:
            pydirectinput.keyUp(self.current_hold_key)
            print(f"[RELEASE] Lepas tombol aksi: {self.current_hold_key}")
            self.current_hold_key = None

    def release_movement_hold(self):
        if self.current_movement_key:
            pydirectinput.keyUp(self.current_movement_key)
            print(f"[RELEASE] Lepas tombol gerakan: {self.current_movement_key}")
            self.current_movement_key = None

    def release_all_keys(self):
        self.release_action_hold()
        self.release_movement_hold()

    def draw_landmarks(self, frame, results):
        self.mp_drawing.draw_landmarks(frame, results.pose_landmarks, self.mp_holistic.POSE_CONNECTIONS)
        self.mp_drawing.draw_landmarks(frame, results.left_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS)
        self.mp_drawing.draw_landmarks(frame, results.right_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS)

    def update_gui_image(self, frame):
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_BGR888)
        self.change_pixmap_signal.emit(qt_img.scaled(640, 480, Qt.KeepAspectRatio))

    # ========================================================
    # 1. CAMERA LOGIC (HEURISTIC - NO AI NEEDED)
    # ========================================================
    def handle_camera(self, results):
        nose = results.pose_landmarks.landmark[0]
        # Ambil titik telinga untuk menentukan "tengah wajah"
        l_ear = results.pose_landmarks.landmark[7]
        r_ear = results.pose_landmarks.landmark[8]
        face_center_x = (l_ear.x + r_ear.x) / 2
        
        # Hitung deviasi hidung dari tengah wajah
        diff_x = nose.x - face_center_x
        
        sensitivity = 1500 # Sesuaikan kenyamanan
        if abs(diff_x) > 0.1: # Deadzone agar kamera tidak goyang terus
            move_x = int(diff_x * sensitivity)
            pydirectinput.moveRel(move_x, 0)

    def stop(self):
        self._run_flag = False
        self.wait()