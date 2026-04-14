import pickle
import numpy as np
import pydirectinput

class SekiroAI:
    def __init__(self, model_path='assets/models/sekiro_classifier.pkl'):
        # Load model .pkl yang di-download dari Colab
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

    def predict_action(self, landmarks_array):
        """
        landmarks_array: list koordinat (flatten) yang sama urutannya dengan CSV
        """
        # Prediksi label (misal: "attack", "idle")
        prediction = self.model.predict([landmarks_array])[0]
        
        # Ambil probabilitas (kepastian) model
        probs = self.model.predict_proba([landmarks_array])[0]
        confidence = np.max(probs)

        if confidence > 0.80: # Hanya eksekusi jika yakin > 80%
            if prediction == "attack":
                pydirectinput.press('j') # Keybind Attack di Sekiro PC
            elif prediction == "deflect":
                pydirectinput.press('k') # Keybind Deflect di Sekiro PC
            return prediction, confidence
            
        return "idle", confidence