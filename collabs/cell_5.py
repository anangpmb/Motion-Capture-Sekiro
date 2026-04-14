# Simpan model ke file pickle
model_filename = 'sekiro_classifier.pkl'
with open(model_filename, 'wb') as f:
    pickle.dump(model, f)

# Download ke PC
files.download(model_filename)
print(f"Selesai! File {model_filename} telah di-download. Masukkan ke folder 'assets/models/' di PC Windows.")