import numpy as np
from windowing import sliding_window
from features import extract_features

dummy_data = np.random.randn(1000, 6)
windows = sliding_window(dummy_data)

feature_matrix = np.array([extract_features(w) for w in windows])

print("Windows:", windows.shape)
print("Feature matrix:", feature_matrix.shape)
