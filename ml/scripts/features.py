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

def extract_features_tiny(window):
    ax, ay, az = window[:, 0], window[:, 1], window[:, 2]
    
    features = [
        np.mean(ax), np.mean(ay), np.mean(az),
        np.std(ax), np.std(ay), np.std(az),
        np.max(ax), np.max(ay), np.max(az),
        np.sum(np.abs(window)) / window.shape[0]  # SMA
    ]
    return np.array(features)

