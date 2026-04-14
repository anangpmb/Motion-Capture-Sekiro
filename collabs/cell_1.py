import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from google.colab import files
import pickle
import os

print("Library siap. Kita akan menggunakan Random Forest untuk model Sekiro.")