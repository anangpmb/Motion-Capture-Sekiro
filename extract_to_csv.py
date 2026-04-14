import cv2
import mediapipe as mp
import pandas as pd
import os
import sys

# Konfigurasi
VIDEO_DIR = 'data/videos'
OUTPUT_CSV = 'data/dataset.csv'
mp_holistic = mp.solutions.holistic

def get_header():
    header = ['label']
    for i in range(33): header.extend([f'p_x{i}', f'p_y{i}', f'p_z{i}', f'p_v{i}'])
    for i in range(21): header.extend([f'lh_x{i}', f'lh_y{i}', f'lh_z{i}'])
    for i in range(21): header.extend([f'rh_x{i}', f'rh_y{i}', f'rh_z{i}'])
    return header

def extract_landmarks_from_folder(folder_path, label):
    new_data = []
    videos = [v for v in os.listdir(folder_path) if v.endswith(('.mp4', '.mov', '.avi'))]
    
    if not videos:
        return None

    with mp_holistic.Holistic(static_image_mode=False) as holistic:
        for v_file in videos:
            cap = cv2.VideoCapture(os.path.join(folder_path, v_file))
            print(f"   > Processing: {v_file}")
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = holistic.process(image)
                
                if results.pose_landmarks:
                    row = [label]
                    for lm in results.pose_landmarks.landmark:
                        row.extend([lm.x, lm.y, lm.z, lm.visibility])
                    for hand in [results.left_hand_landmarks, results.right_hand_landmarks]:
                        if hand:
                            for lm in hand.landmark: row.extend([lm.x, lm.y, lm.z])
                        else:
                            row.extend([0] * 63)
                    new_data.append(row)
            cap.release()
    return new_data

def run_selective_extraction():
    if not os.path.exists(VIDEO_DIR):
        print(f"Error: Folder {VIDEO_DIR} tidak ditemukan!")
        return

    # 1. Ambil daftar semua folder pose
    all_folders = [f for f in os.listdir(VIDEO_DIR) if os.path.isdir(os.path.join(VIDEO_DIR, f))]
    all_folders.sort()

    if not all_folders:
        print("Error: Tidak ada folder pose di dalam data/videos!")
        return

    # 2. Tampilkan Menu
    print("\n" + "="*30)
    print(" SEKIRO POSE EXTRACTOR ")
    print("="*30)
    print("0. SEMUA POSE (Full Refresh)")
    for i, folder in enumerate(all_folders, 1):
        print(f"{i}. {folder}")
    print("="*30)
    
    choice = input("Pilih nomor pose (pisahkan dengan koma jika banyak, misal: 1,3,5): ")
    
    # 3. Tentukan folder mana yang akan diproses
    selected_folders = []
    if choice == '0':
        selected_folders = all_folders
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected_folders = [all_folders[i] for i in indices if 0 <= i < len(all_folders)]
        except:
            print("Input tidak valid!")
            return

    if not selected_folders:
        print("Tidak ada pose yang dipilih.")
        return

    print(f"\n[*] Target eksekusi: {', '.join(selected_folders)}")

    # 4. Load Dataset Existing
    if os.path.exists(OUTPUT_CSV):
        df_main = pd.read_csv(OUTPUT_CSV)
    else:
        df_main = pd.DataFrame(columns=get_header())

    # 5. Eksekusi
    for label in selected_folders:
        print(f"\n[!] Update Pose: {label}")
        
        # Hapus data lama untuk pose ini jika ada
        df_main = df_main[df_main['label'] != label]
        
        # Ambil data baru
        folder_path = os.path.join(VIDEO_DIR, label)
        new_rows = extract_landmarks_from_folder(folder_path, label)
        
        if new_rows:
            df_new = pd.DataFrame(new_rows, columns=get_header())
            df_main = pd.concat([df_main, df_new], ignore_index=True)
            print(f"    - Berhasil menambahkan {len(new_rows)} baris.")
        else:
            print(f"    - Warning: Tidak ada video di folder {label}")

    # 6. Simpan
    df_main.to_csv(OUTPUT_CSV, index=False)
    print("\n[✔] Dataset berhasil diperbarui!")

if __name__ == "__main__":
    run_selective_extraction()