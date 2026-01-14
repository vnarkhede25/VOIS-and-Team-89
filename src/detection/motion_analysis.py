import math

def calculate_magnitude(ax, ay, az):
    """
    Calculate 3D acceleration magnitude using Euclidean norm.
    
    Safety: Provides single metric for fall detection regardless of device orientation.
    Reason: Falls produce high magnitude regardless of which axis experiences impact.
    """
    magnitude = math.sqrt(ax**2 + ay**2 + az**2)
    return magnitude
