import cv2
import mediapipe as mp
import numpy as np
import time
import pydirectinput
import json
import os
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage
from .movements import SekiroMovementController

# Optimasi pydirectinput
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
        self.last_action_time = {}  # Untuk menyimpan waktu terakhir setiap pose ditekan
        
        # State Management
        self.active_holds = set() # Mengganti current_hold_key agar bisa multi-hold
        self.active_wasd = set()
        self.last_pose = "idle"

    def load_dynamic_mapping(self):
        """Membaca konfigurasi dari UI Pose Manager"""
        try:
            if os.path.exists("mapping.json"):
                with open("mapping.json", "r") as f:
                    return json.load(f)["poses"]
        except Exception as e:
            print(f"Error loading mapping: {e}")
        return []

    def run(self):
        cap = cv2.VideoCapture(0)
        
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
                    # 1. Jalur Manual: WASD via Tangan Kiri
                    # self.shandle_manual_movement(results) //disable karena pake controller
                    
                    # 2. Jalur AI: Aksi via Tangan Kanan (Dinamis)
                    if results.right_hand_landmarks:
                        label, confidence = self.controller.get_predicted_movement(results)
                        self.execute_dynamic_action(label, confidence)
                        self.gesture_detected_signal.emit(label, confidence)
                    else:
                        self.gesture_detected_signal.emit("No Hand", 0.0)
                        self.release_all_holds()

                self.draw_landmarks(frame, results)
                self.update_gui_image(frame)

        cap.release()
        self.release_all_keys()

    def handle_manual_movement(self, results):
        """Joystick Tangan Kiri"""
        l_wrist = results.pose_landmarks.landmark[16]
        l_shoulder = results.pose_landmarks.landmark[12]
        
        target_keys = set()
        dy = l_shoulder.y - l_wrist.y
        dx = l_wrist.x - l_shoulder.x

        if dy > 0.1: target_keys.add('w')
        elif -0.4 < dy < -0.25: target_keys.add('s') 
        
        if dx < -0.15: target_keys.add('a')
        elif dx > 0.15: target_keys.add('d')

        for k in ['w', 'a', 's', 'd']:
            if k in target_keys and k not in self.active_wasd:
                pydirectinput.keyDown(k)
                self.active_wasd.add(k)
            elif k not in target_keys and k in self.active_wasd:
                pydirectinput.keyUp(k)
                self.active_wasd.remove(k)
    
   
    def execute_dynamic_action(self, label, confidence):
        """Logika Baru: Menggunakan Mapping dari JSON"""
        mappings = self.load_dynamic_mapping()
        threshold = 0.75 # Threshold standar AI
        TAP_COOLDOWN = 0.3
        current_time = time.time()
        if confidence < threshold or label == "idle":
            self.release_all_holds()
            self.last_pose = "idle"
            return

        # Cari mapping yang sesuai dengan label dari AI
        target = next((p for p in mappings if p["name"] == label), None)

        if target:
            key = target["key"]
            action_type = target["type"]

            if action_type == "tap":
                # Cegah spamming jika pose masih sama (opsional)
                last_press = self.last_action_time.get(label, 0)
            
                if (current_time - last_press) > TAP_COOLDOWN:
                    pydirectinput.press(key)
                    self.last_action_time[label] = current_time # Update waktu tekan terakhir
                    print(f"[ACTION] Tap (Cooldown Mode): {key}")
            
            elif action_type == "hold":
                if key not in self.active_holds:
                    pydirectinput.keyDown(key)
                    self.active_holds.add(key)
                    print(f"[ACTION] Holding: {key}")
        
        # Lepas tombol hold jika pose berubah ke aksi lain yang bukan hold
        if self.last_pose != label:
            current_keys = {p["key"] for p in mappings if p["name"] == label}
            for held_key in list(self.active_holds):
                if held_key not in current_keys:
                    pydirectinput.keyUp(held_key)
                    self.active_holds.discard(held_key)

        self.last_pose = label

    def release_all_holds(self):
        for key in list(self.active_holds):
            pydirectinput.keyUp(key)
            self.active_holds.discard(key)

    def release_all_keys(self):
        for k in list(self.active_wasd): pydirectinput.keyUp(k)
        self.release_all_holds()

    def draw_landmarks(self, frame, results):
        self.mp_drawing.draw_landmarks(frame, results.pose_landmarks, self.mp_holistic.POSE_CONNECTIONS)
        if results.right_hand_landmarks:
            self.mp_drawing.draw_landmarks(frame, results.right_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS)
        if results.left_hand_landmarks:
            self.mp_drawing.draw_landmarks(frame, results.left_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS)

    def update_gui_image(self, frame):
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        # Konversi ke RGB untuk QImage
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.change_pixmap_signal.emit(qt_img.scaled(640, 480, Qt.KeepAspectRatio))

    def stop(self):
        self._run_flag = False
        self.wait()