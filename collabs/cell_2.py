uploaded = files.upload()
filename = list(uploaded.keys())[0]
df = pd.read_csv(filename)
print(f"Dataset {filename} berhasil di-upload. Total data: {len(df)} frame.")