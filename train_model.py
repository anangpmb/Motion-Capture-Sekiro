import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

def train():
    print("Membaca dataset...")
    df = pd.read_csv('data/dataset.csv')
    
    X = df.drop('label', axis=1)
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Melatih model Random Forest...")
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    print(f"Akurasi Model: {accuracy_score(y_test, y_pred) * 100:.2f}%")
    
    # Simpan Model
    os.makedirs('assets/models', exist_ok=True)
    with open('assets/models/sekiro_classifier.pkl', 'wb') as f:
        pickle.dump(model, f)
    print("Model disimpan di assets/models/sekiro_classifier.pkl")

if __name__ == "__main__":
    import os
    train()