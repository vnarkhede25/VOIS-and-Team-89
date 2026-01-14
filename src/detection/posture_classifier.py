"""
Posture Classification for Elderly Monitoring

Classifies patient posture based on accelerometer and gyroscope data.
Supports detection of standing, sitting, lying down, and fall positions.
"""

import numpy as np
from enum import Enum
from typing import Tuple

class Posture(Enum):
    """Posture states."""
    STANDING = "standing"
    SITTING = "sitting"
    LYING = "lying"
    FALLING = "falling"
    UNKNOWN = "unknown"

class PostureClassifier:
    """Classifies patient posture from sensor data."""
    
    def __init__(self):
        # Thresholds for posture classification
        self.gravity_threshold = 9.0  # m/s²
        self.standing_threshold = 8.0
        self.sitting_threshold = 6.0
        self.lying_threshold = 4.0
        
        # Motion variance thresholds
        self.motion_threshold = 0.5
        self.fall_threshold = 15.0
        
    def classify_posture(self, ax: float, ay: float, az: float, 
                       gx: float = 0, gy: float = 0, gz: float = 0) -> Posture:
        """
        Classify posture from sensor data.
        
        Args:
            ax, ay, az: Acceleration values
            gx, gy, gz: Gyroscope values (optional)
            
        Returns:
            Posture classification
        """
        # Calculate magnitude
        magnitude = np.sqrt(ax**2 + ay**2 + az**2)
        
        # Calculate total motion
        motion_magnitude = np.sqrt(gx**2 + gy**2 + gz**2)
        
        # Check for fall (high motion and unusual orientation)
        if motion_magnitude > self.fall_threshold:
            return Posture.FALLING
        
        # Classify based on acceleration magnitude and orientation
        if magnitude >= self.standing_threshold:
            return Posture.STANDING
        elif magnitude >= self.sitting_threshold:
            return Posture.SITTING
        elif magnitude >= self.lying_threshold:
            return Posture.LYING
        else:
            return Posture.UNKNOWN
