import math
from enum import Enum
from collections import deque

class Posture(Enum):
    """Clean enum for posture states"""
    STANDING = "standing"
    SITTING = "sitting"
    LYING = "lying"
    UNKNOWN = "unknown"

class PostureClassifier:
    """
    Advanced posture classification using 3D gravity vector analysis.
    
    Safety: Accurate posture detection improves fall detection and user comfort.
    Reason: Different postures have distinct gravity signatures that can be reliably detected.
    """
    
    def __init__(self, window_size=5):
        # Window size: 5 samples provides stable average while maintaining responsiveness
        self.window_size = window_size
        self.accel_buffer = deque(maxlen=window_size)
        
    def classify_posture(self, ax, ay, az):
        """
        Classify posture using 3D gravity vector analysis.
        
        Safety: Uses multiple orientation cues for robust classification.
        Reason: Single-axis methods fail when device orientation changes.
        
        Physics reasoning:
        - Gravity always points downward (0, 0, -9.8 m/s²) in world frame
        - MPU6050 measures acceleration in device frame
        - Device orientation changes how gravity appears in sensor readings
        """
        self.accel_buffer.append((ax, ay, az))
        
        if len(self.accel_buffer) < self.window_size:
            return Posture.UNKNOWN
            
        # Calculate average acceleration to reduce noise
        avg_ax = sum(a[0] for a in self.accel_buffer) / len(self.accel_buffer)
        avg_ay = sum(a[1] for a in self.accel_buffer) / len(self.accel_buffer)
        avg_az = sum(a[2] for a in self.accel_buffer) / len(self.accel_buffer)
        
        # Calculate gravity vector magnitude (should be ~9.8 m/s² when stationary)
        gravity_magnitude = math.sqrt(avg_ax**2 + avg_ay**2 + avg_az**2)
        
        # Normalize to unit vector for direction analysis
        if gravity_magnitude > 0:
            gx = avg_ax / gravity_magnitude
            gy = avg_ay / gravity_magnitude
            gz = avg_az / gravity_magnitude
        else:
            return Posture.UNKNOWN
            
        # Calculate angle with vertical axis (Z-axis in world frame)
        # When device is upright, gravity aligns with device Z-axis
        # Use absolute value since gravity direction (up/down) doesn't matter for orientation
        vertical_angle = math.degrees(math.acos(min(1.0, abs(gz))))
        
        # Calculate tilt angle from horizontal plane
        # Helps distinguish sitting vs lying positions
        horizontal_magnitude = math.sqrt(gx**2 + gy**2)
        tilt_angle = math.degrees(math.atan2(horizontal_magnitude, abs(gz)))
        
        # Posture classification logic based on device orientation
        # Key insight: Need to consider both vertical angle AND gravity distribution
        
        # Calculate horizontal component ratio
        horizontal_ratio = horizontal_magnitude / (horizontal_magnitude + abs(gz)) if (horizontal_magnitude + abs(gz)) > 0 else 0
        
        if vertical_angle < 20 and horizontal_ratio < 0.25:
            # Device mostly vertical with very low horizontal component -> standing
            # Safety: Standing position has clear vertical gravity signature
            return Posture.STANDING
        elif vertical_angle < 50 and horizontal_ratio < 0.6:
            # Device moderately tilted -> sitting
            # Safety: Sitting shows moderate tilt with some horizontal component
            return Posture.SITTING
        else:
            # Device mostly horizontal or high horizontal component -> lying
            # Safety: Lying position shows gravity distributed across horizontal plane
            return Posture.LYING
    
    def get_confidence(self, ax, ay, az):
        """
        Calculate confidence score for posture classification.
        
        Safety: Low confidence indicates unstable posture or poor sensor data.
        Reason: Consistent readings produce reliable classification.
        """
        if len(self.accel_buffer) < self.window_size:
            return 0.0
            
        # Lower variance = higher confidence
        magnitudes = [math.sqrt(a[0]**2 + a[1]**2 + a[2]**2) for a in self.accel_buffer]
        variance = sum((m - sum(magnitudes)/len(magnitudes))**2 for m in magnitudes) / len(magnitudes)
        
        # Convert variance to confidence (0-1 scale)
        # Safety: High variance may indicate movement or sensor issues
        confidence = max(0, 1 - variance / 4.0)
        return confidence

def detect_posture(az):
    """
    Legacy function for backward compatibility.
    
    Safety: Simple Z-axis threshold as fallback when 3D analysis unavailable.
    Reason: Used when computational resources are limited or for quick testing.
    """
    if az < 3:
        return "lying"
    elif az < 7:
        return "sitting"
    else:
        return "standing"
