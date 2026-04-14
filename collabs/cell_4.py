# Membuat model Random Forest
# n_estimators=100 berarti kita membuat 100 pohon keputusan untuk voting
model = RandomForestClassifier(n_estimators=100, random_state=42)

# Proses belajar
print("Sedang melatih model... (ini akan sangat cepat)")
model.fit(X_train, y_train)

# Cek Akurasi
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\nAKURASI MODEL: {accuracy * 100:.2f}%")
print("\nLaporan Detail:")
print(classification_report(y_test, y_pred))