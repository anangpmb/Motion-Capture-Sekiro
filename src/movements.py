import pickle
import numpy as np
import os
from typing import Tuple, Optional

# --- Konfigurasi Model ---
MODEL_PATH = "assets/models/sekiro_classifier.pkl"

class SekiroMovementController:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model = None
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        """Memuat model Random Forest dari file .pkl"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print(f"[*] Model {self.model_path} berhasil dimuat.")
            except Exception as e:
                print(f"[!] Gagal memuat model: {e}")
        else:
            print(f"[!] Model tidak ditemukan di {self.model_path}. Pastikan sudah menjalankan training.")

    def _flatten_landmarks(self, results) -> np.ndarray:
        """
        Mengubah hasil MediaPipe Holistic menjadi array flat (258 fitur).
        Urutan: Pose (33*4) -> Left Hand (21*3) -> Right Hand (21*3)
        """
        row = []
        
        # 1. Pose Landmarks (33 titik * 4: x, y, z, visibility)
        if results.pose_landmarks:
            for lm in results.pose_landmarks.landmark:
                row.extend([lm.x, lm.y, lm.z, lm.visibility])
        else:
            row.extend([0] * (33 * 4))

        # 2. Hand Landmarks (21 titik * 3: x, y, z)
        for hand in [results.left_hand_landmarks, results.right_hand_landmarks]:
            if hand:
                for lm in hand.landmark:
                    row.extend([lm.x, lm.y, lm.z])
            else:
                row.extend([0] * (21 * 3))
        
        return np.array([row])

    def get_predicted_movement(self, results) -> Tuple[str, float]:
        """
        Melakukan prediksi berdasarkan frame saat ini.
        Returns: (label_gerakan, confidence_score)
        """
        if self.model is None:
            return "idle", 0.0

        input_data = self._flatten_landmarks(results)
        
        # Prediksi label dan probabilitas
        prediction = self.model.predict(input_data)[0]
        probabilities = self.model.predict_proba(input_data)[0]
        confidence = np.max(probabilities)

        return prediction, confidence

# --- Konfigurasi Cooldown & Grouping (Sesuai Struktur Lama) ---
# Durasi dalam milidetik (ms)
GESTURE_GROUPS = [
    {
        # Aksi Tempur Cepat
        "group": (
            "sekiro_attack",
            "sekiro_deflect",
            "sekiro_combat_art",
            "sekiro_prosthetic",
            "sekiro_grapple",
            "sekiro_use_item",
        ),
        "duration": 700,
    },
    {
        # Navigasi & Gerakan Dasar
        "group": (
            "sekiro_jump",
            "sekiro_crouch",
            "sekiro_dash",
        ),
        "duration": 500,
    },
    {
        # UI & Interaksi
        "group": (
            "sekiro_lock_on",
            "sekiro_pause",
            "sekiro_interact",
        ),
        "duration": 1000,
    }
]

def get_movement_cooldown(label: str) -> int:
    """Mencari durasi cooldown berdasarkan group label"""
    for group_info in GESTURE_GROUPS:
        if label in group_info["group"]:
            return group_info["duration"]
    return 300 # Default cooldown jika tidak ada di group