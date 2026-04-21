import warnings
import sys
import os
import pydirectinput
import json

warnings.filterwarnings("ignore", category=UserWarning)

# 2. Sembunyikan log internal dari Google/MediaPipe (absl)
os.environ['ABSL_LOGGING_LEVEL'] = '3' 
# 0 = All logs, 1 = Info, 2 = Warning, 3 = Error only

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
from src.cv2_thread import Cv2Thread

class SekiroMotionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MotionMap: Sekiro Shadows Die Twice - AI Edition")
        self.resize(800, 600)
        self.setStyleSheet("background-color: #1a1a1a; color: white;")

        # UI Elements
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        
        self.status_label = QLabel("Status: Ready")
        self.status_label.setFont(QFont("Arial", 14, QFont.Bold))
        
        self.gesture_label = QLabel("Detected: None")
        self.gesture_label.setFont(QFont("Courier", 18))
        self.gesture_label.setStyleSheet("color: #00ff00;")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        
        info_layout = QHBoxLayout()
        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.gesture_label)
        
        layout.addLayout(info_layout)
        self.setLayout(layout)

        # Inisialisasi Thread Kamera & AI
        self.thread = Cv2Thread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.gesture_detected_signal.connect(self.update_status)
        self.thread.start()

    def update_image(self, cv_img):
        """Update tampilan kamera di jendela aplikasi"""
        qt_img = QPixmap.fromImage(cv_img)
        self.image_label.setPixmap(qt_img)

    def update_status(self, label, confidence):
        """Update teks deteksi di bawah video"""
        if label != "idle" and confidence > 0.8:
            self.gesture_label.setText(f"Action: {label.upper()} ({confidence*100:.1f}%)")
        else:
            self.gesture_label.setText("Status: Idle")

    def closeEvent(self, event):
        """Pastikan thread berhenti saat aplikasi ditutup"""
        self.thread.stop()
        event.accept()

if __name__ == "__main__":
    # Pastikan pydirectinput punya akses admin jika diperlukan oleh game
    app = QApplication(sys.argv)
    a = SekiroMotionApp()
    a.show()
    sys.exit(app.exec_())