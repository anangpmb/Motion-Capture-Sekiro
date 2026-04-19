import cv2
import mediapipe as mp
import numpy as np
import time
import pydirectinput
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage
from .movements import SekiroMovementController

# Memberikan waktu bagi game engine untuk memproses input
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
        self.active_wasd = set()

    def run(self):
        cap = cv2.VideoCapture(0)
        
        # Pengaturan agar tracker tangan lebih sensitif
        with self.mp_holistic.Holistic(
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5,
            model_complexity=1 
        ) as holistic:
            
            while self._run_flag:
                ret, frame = cap.read()
                if not ret: break

                frame = cv2.flip(frame, 1)
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = holistic.process(image)

                if results.pose_landmarks:
                    # 1. Jalur Manual: WASD via Tangan Kiri (Heuristic)
                    # self.handle_manual_movement(results)
                    
                    # 2. Jalur AI: Aksi via Tangan Kanan (Gesture Detection)
                    # Pastikan tangan kanan terdeteksi sebelum memanggil model
                    if results.right_hand_landmarks:
                        label, confidence = self.controller.get_predicted_movement(results)
                        self.handle_combat_actions(label, confidence, results)
                        self.gesture_detected_signal.emit(label, confidence)
                    else:
                        self.gesture_detected_signal.emit("No Hand", 0.0)
                        self.release_action_hold()

                self.draw_landmarks(frame, results)
                self.update_gui_image(frame)

        cap.release()
        self.release_all_keys()

    def handle_manual_movement(self, results):
        """Logika Joystick Tangan Kiri (Tidak merusak dataset tangan kanan)"""
        l_wrist = results.pose_landmarks.landmark[16]
        l_shoulder = results.pose_landmarks.landmark[12]
        
        target_keys = set()
        dy = l_shoulder.y - l_wrist.y
        dx = l_wrist.x - l_shoulder.x

        # Threshold pergerakan (Sesuaikan posisi duduk/berdiri)
        if dy > 0.1: target_keys.add('w')
        elif -0.4 < dy < -0.25: target_keys.add('s') # Standby area (Pinggang)
        
        if dx < -0.15: target_keys.add('a')
        elif dx > 0.15: target_keys.add('d')


        for k in ['w', 'a', 's', 'd']:
            if k in target_keys and k not in self.active_wasd:
                pydirectinput.keyDown(k)
                self.active_wasd.add(k)
            elif k not in target_keys and k in self.active_wasd:
                pydirectinput.keyUp(k)
                self.active_wasd.remove(k)

    def handle_combat_actions(self, label, confidence, results):
        """Logika Aksi Tempur berdasarkan hasil Sampling Tangan Kanan"""
        # 1. Tentukan ambang batas (Threshold)
        # Jika tracker tangan kanan aktif dan stabil, turunkan threshold ke 0.70
        # Jika tidak stabil atau terhalang, tetap di 0.85
        right_hand_visible = results.right_hand_landmarks is not None
        threshold = 0.70 if right_hand_visible else 0.85
        print(f"[ACTION] EXECUTE {label} (Conf: {confidence:.2f})")
        if confidence < threshold:
            self.last_label = f"{label} Not Executed ({confidence:.2f})"
            # Jika kembali ke posisi netral atau confidence drop, lepas tombol hold
            if label == "idle" or confidence < 0.5:
                self.release_action_hold()
            return
        
        if label == "combat_art":
            if self.current_hold_key != 'combat_art':
                self.release_action_hold()
                # Tekan keduanya bersamaan
                pydirectinput.keyDown('k')
                pydirectinput.keyDown('j')
                self.current_hold_key = 'combat_art'
                print(f"[ACTION] EXECUTE COMBAT ART! (Conf: {confidence:.2f})")

        # Aksi Tahan (Contoh: Menahan L1/K untuk Deflect)
        if label == "deflect":
            if self.current_hold_key != 'k':
                self.release_action_hold()
                pydirectinput.keyDown('k')
                self.current_hold_key = 'k'
        
        elif label == "run":
            self.release_action_hold()
            if self.current_hold_key != 'run':
                self.release_action_hold()
                pydirectinput.keyDown('shift')
                self.current_hold_key = 'run'
        
        
        # Aksi Sekali Tekan (Contoh: Attack, Jump, Dash)
        elif label != "idle":
            self.release_action_hold()
            
            mapping = {
                "attack": 'j', "jump": 'space', "dash": 'shift', 
                "prosthetic": 'o', "use_item": 'r', "lock_on_target": 'm',
                "grappler" : "f", "interact" : "e", "pause" : "esc"
            }

            key = mapping.get(label)
            if key:
                pydirectinput.keyDown(key)
                time.sleep(0.05) # Delay wajib untuk Sekiro
                pydirectinput.keyUp(key)

        elif label == "idle":
            self.release_action_hold()

        self.last_label = label

    def release_action_hold(self):
        if self.current_hold_key == 'combat_art':
            pydirectinput.keyUp('k')
            pydirectinput.keyUp('j')
            self.current_hold_key = None
        elif self.current_hold_key == 'run':
            pydirectinput.keyUp('shift')
            self.current_hold_key = None
        elif self.current_hold_key:
            pydirectinput.keyUp(self.current_hold_key)
            self.current_hold_key = None

    def release_all_keys(self):
        for k in list(self.active_wasd): pydirectinput.keyUp(k)
        self.release_action_hold()

    def draw_landmarks(self, frame, results):
        """Visualisasi lengkap untuk memantau tracker jari"""
        # Gambar Pose
        self.mp_drawing.draw_landmarks(frame, results.pose_landmarks, self.mp_holistic.POSE_CONNECTIONS)
        # Gambar Tangan Kanan (Prioritas Sampling)
        if results.right_hand_landmarks:
            self.mp_drawing.draw_landmarks(frame, results.right_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS)
        # Gambar Tangan Kiri
        if results.left_hand_landmarks:
            self.mp_drawing.draw_landmarks(frame, results.left_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS)

    def update_gui_image(self, frame):
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_BGR888)
        self.change_pixmap_signal.emit(qt_img.scaled(640, 480, Qt.KeepAspectRatio))

    def stop(self):
        self._run_flag = False
        self.wait()