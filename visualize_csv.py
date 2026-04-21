import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide", page_title="Sekiro Pose 3D Inspector")

st.title("🥷 Sekiro Pose 3D Reconstructor")
st.markdown("Script ini memvisualisasikan koordinat mentah dari CSV menjadi bentuk kerangka 3D.")

# 1. Load Dataset
try:
    df = pd.read_csv('data/dataset.csv')
    st.sidebar.success(f"Dataset Loaded: {len(df)} frames")
except Exception as e:
    st.error(f"Gagal memuat CSV: {e}")
    st.stop()

# 2. Sidebar Filters
target_label = st.sidebar.selectbox("Pilih Label Pose:", df['label'].unique())
filtered_df = df[df['label'] == target_label].reset_index(drop=True)
frame_idx = st.sidebar.slider("Pilih Index Frame:", 0, len(filtered_df)-1, 0)

sample = filtered_df.iloc[frame_idx]

# 3. Fungsi untuk Mengambil Koordinat
def get_coords(prefix, count):
    x = [sample[f'{prefix}_x{i}'] for i in range(count)]
    y = [sample[f'{prefix}_y{i}'] for i in range(count)]
    z = [sample[f'{prefix}_z{i}'] for i in range(count)]
    return x, y, z

# Ambil data Pose (33 titik) dan Hands (21 titik per tangan)
p_x, p_y, p_z = get_coords('p', 33)
lh_x, lh_y, lh_z = get_coords('lh', 21)
rh_x, rh_y, rh_z = get_coords('rh', 21)

# 4. Membangun Visualisasi 3D dengan Plotly
fig = go.Figure()

# --- Plot Titik-Titik (Landmarks) ---
fig.add_trace(go.Scatter3d(x=p_x, y=p_y, z=p_z, mode='markers', marker=dict(size=4, color='blue'), name='Pose'))
fig.add_trace(go.Scatter3d(x=lh_x, y=lh_y, z=lh_z, mode='markers', marker=dict(size=3, color='red'), name='Left Hand'))
fig.add_trace(go.Scatter3d(x=rh_x, y=rh_y, z=rh_z, mode='markers', marker=dict(size=3, color='green'), name='Right Hand'))

# --- Plot Garis Penghubung (Sederhana untuk Tangan) ---
def add_hand_connections(x, y, z, color, name):
    # Koneksi jari standar (0-1-2-3-4, 0-5-6-7-8, dst)
    connections = [[0,1,2,3,4], [0,5,6,7,8], [5,9,13,17], [9,10,11,12], [13,14,15,16], [17,18,19,20], [0,17]]
    for conn in connections:
        cx = [x[i] for i in conn]
        cy = [y[i] for i in conn]
        cz = [z[i] for i in conn]
        fig.add_trace(go.Scatter3d(x=cx, y=cy, z=cz, mode='lines', line=dict(color=color, width=2), showlegend=False))

add_hand_connections(lh_x, lh_y, lh_z, 'red', 'LH Connect')
add_hand_connections(rh_x, rh_y, rh_z, 'green', 'RH Connect')

# Setting Tampilan (Penting: Sumbu Y dibalik agar sesuai orientasi kamera)
fig.update_layout(
    scene=dict(
        xaxis_title='X', yaxis_title='Z', zaxis_title='Y',
        yaxis_autorange="reversed",
        zaxis_autorange="reversed",
        aspectmode='data'
    ),
    margin=dict(l=0, r=0, b=0, t=30),
    height=700
)

st.plotly_chart(fig, use_container_width=True)

# 5. Informasi Koordinat Mentah
with st.expander("Lihat Data Mentah Baris Ini"):
    st.write(sample)