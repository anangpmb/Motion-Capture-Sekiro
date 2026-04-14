import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# 1. Load Data
df = pd.read_csv('data/dataset.csv')
X = df.drop('label', axis=1).values
y = df['label'].values

# 2. Encode Labels (idle, attack, deflect -> 0, 1, 2)
encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)
y_categorical = tf.keras.utils.to_categorical(y_encoded)

# Save encoder classes untuk nanti di app.py
np.save('models/classes.npy', encoder.classes_)

X_train, X_test, y_train, y_test = train_test_split(X, y_categorical, test_size=0.2)

# 3. Build Neural Network Model
model = tf.keras.Sequential([
    tf.keras.layers.Dense(128, activation='relu', input_shape=(X.shape[1],)),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dense(len(encoder.classes_), activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# 4. Training
model.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_test, y_test))

# 5. Save Model
model.save('models/sekiro_model.h5')
print("Model TensorFlow siap digunakan!")