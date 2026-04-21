import cv2
import mediapipe as mp
import pandas as pd
import os

# --- KONFIGURASI ---
VIDEO_DIR = 'data/videos'
OUTPUT_CSV = 'data/dataset.csv'

# Inisialisasi MediaPipe
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def get_header():
    header = ['label']
    # Pose: 33 landmarks * 4 (x, y, z, visibility)
    for i in range(33): header.extend([f'p_x{i}', f'p_y{i}', f'p_z{i}', f'p_v{i}'])
    # Left Hand: 21 landmarks * 3 (x, y, z)
    for i in range(21): header.extend([f'lh_x{i}', f'lh_y{i}', f'lh_z{i}'])
    # Right Hand: 21 landmarks * 3 (x, y, z)
    for i in range(21): header.extend([f'rh_x{i}', f'rh_y{i}', f'rh_z{i}'])
    return header

def initialize_csv():
    """Membuat file CSV baru dengan header lengkap jika belum ada."""
    if not os.path.exists('data'):
        os.makedirs('data')
    df = pd.DataFrame(columns=get_header())
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"[SYSTEM] File {OUTPUT_CSV} berhasil diinisialisasi.")

def extract_landmarks_from_folder(folder_path, label):
    new_data = []
    videos = [v for v in os.listdir(folder_path) if v.endswith(('.mp4', '.mov', '.avi'))]
    
    if not videos:
        return None

    # Menggunakan min_detection_confidence lebih tinggi agar data lebih bersih
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        for v_file in videos:
            cap = cv2.VideoCapture(os.path.join(folder_path, v_file))
            print(f"   > Processing: {v_file}")
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                
                # Pemrosesan MediaPipe
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = holistic.process(image)
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                # --- LOGIKA VISUALISASI (SKELETON) ---
                # 1. Gambar Pose (Badan)
                if results.pose_landmarks:
                    mp_drawing.draw_landmarks(
                        image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
                        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
                
                # 2. Gambar Tangan Kanan & Cek Status (RH: OK/LOST)
                rh_status = "RH: LOST"
                status_color = (0, 0, 255) # Merah jika tidak terdeteksi

                if results.right_hand_landmarks:
                    rh_status = "RH: OK"
                    status_color = (0, 255, 0) # Hijau jika oke
                    mp_drawing.draw_landmarks(
                        image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style())

                # UI Overlay di Jendela Preview
                cv2.rectangle(image, (0, 0), (280, 90), (0, 0, 0), -1) # Kotak hitam background info
                cv2.putText(image, f"Label: {label}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(image, rh_status, (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 3)

                # Tampilkan Jendela Preview
                cv2.imshow('Mocap Extraction Debug', image)
                
                # --- DATA PACKING ---
                if results.pose_landmarks:
                    row = [label]
                    # Pose (132 values)
                    for lm in results.pose_landmarks.landmark:
                        row.extend([lm.x, lm.y, lm.z, lm.visibility])
                    # Hands (63 + 63 values)
                    for hand in [results.left_hand_landmarks, results.right_hand_landmarks]:
                        if hand:
                            for lm in hand.landmark: row.extend([lm.x, lm.y, lm.z])
                        else:
                            row.extend([0] * 63)
                    new_data.append(row)

                # Tekan 'q' untuk membatalkan ekstraksi video ini
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\n[!] Ekstraksi dihentikan paksa oleh user.")
                    cap.release()
                    cv2.destroyAllWindows()
                    return new_data

            cap.release()
    cv2.destroyAllWindows()
    return new_data

def run_selective_extraction():
    if not os.path.exists(VIDEO_DIR):
        print(f"Error: Folder {VIDEO_DIR} tidak ditemukan!")
        return

    # Cek file CSV di awal
    if not os.path.exists(OUTPUT_CSV) or os.stat(OUTPUT_CSV).st_size == 0:
        initialize_csv()

    all_folders = sorted([f for f in os.listdir(VIDEO_DIR) if os.path.isdir(os.path.join(VIDEO_DIR, f))])
    if not all_folders:
        print("Error: Tidak ada folder pose di data/videos!"); return

    # Tampilkan Menu Selektif
    print("\n" + "="*35)
    print("   SEKIRO POSE EXTRACTOR (DEBUG)   ")
    print("="*35)
    print("0. SEMUA POSE (Full Refresh)")
    for i, folder in enumerate(all_folders, 1):
        print(f"{i}. {folder}")
    print("="*35)
    
    choice = input("Pilih nomor pose (misal: 1,3): ")
    
    selected_folders = all_folders if choice == '0' else []
    if choice != '0':
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected_folders = [all_folders[i] for i in indices if 0 <= i < len(all_folders)]
        except:
            print("Input tidak valid!"); return

    if not selected_folders: return

    # Load data lama
    df_main = pd.read_csv(OUTPUT_CSV)

    for label in selected_folders:
        print(f"\n[!] Update Pose: {label}")
        # Hapus data lama hanya untuk label yang dipilih agar tidak duplikat
        df_main = df_main[df_main['label'] != label]
        
        folder_path = os.path.join(VIDEO_DIR, label)
        new_rows = extract_landmarks_from_folder(folder_path, label)
        
        if new_rows:
            df_new = pd.DataFrame(new_rows, columns=get_header())
            df_main = pd.concat([df_main, df_new], ignore_index=True)
            print(f"    - Berhasil menambah {len(new_rows)} baris.")

    # Simpan kembali
    df_main.to_csv(OUTPUT_CSV, index=False)
    print("\n[✔] Dataset Berhasil Diperbarui!")

if __name__ == "__main__":
    run_selective_extraction()