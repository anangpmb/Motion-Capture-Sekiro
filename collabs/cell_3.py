# 1. Pisahkan Fitur (X) dan Label (y)
X = df.drop('label', axis=1)
y = df['label']

# 2. Split data (80% training, 20% testing)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"Data latih: {X_train.shape[0]} frame")
print(f"Data uji: {X_test.shape[0]} frame")