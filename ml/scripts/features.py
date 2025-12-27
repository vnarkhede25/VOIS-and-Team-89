import numpy as np

def extract_features(window):
    features = []
    features.extend(np.mean(window, axis=0))
    features.extend(np.std(window, axis=0))
    features.extend(np.max(window, axis=0))
    features.extend(np.min(window, axis=0))
        
    sma = np.sum(np.abs(window)) / window.shape[0]
    features.append(sma)

    return np.array(features)
