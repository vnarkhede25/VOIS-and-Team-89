from collections import deque

class InactivityDetector:
    """
    Detects user inactivity to confirm falls and prevent false alarms.
    
    Safety: Ensures fall confirmation only when user remains still after impact.
    Reason: Real falls result in prolonged inactivity; false alarms show movement.
    """
    
    def __init__(self, window_size=3, tolerance=0.3, min_inactive_samples=2):
        # Window size: 3 samples provides balance between responsiveness and stability
        self.window_size = window_size
        # Tolerance: 0.3g allows small movements while detecting true inactivity
        self.tolerance = tolerance
        # Minimum samples: 2 ensures consistent inactivity before confirmation
        self.min_inactive_samples = min_inactive_samples
        self.magnitude_buffer = deque(maxlen=window_size)
        
    def is_inactive(self, magnitude, prev_magnitude):
        """
        Determine if user is inactive based on acceleration variance.
        
        Safety: Prevents fall confirmation during continued movement.
        Reason: Falls result in stillness; daily movement shows variance.
        """
        self.magnitude_buffer.append(magnitude)
        
        # Need sufficient samples for reliable variance calculation
        if len(self.magnitude_buffer) < self.window_size:
            # Fallback: simple difference check for initial samples
            return abs(magnitude - prev_magnitude) < self.tolerance
        
        # Calculate variance to detect movement patterns
        variance = max(self.magnitude_buffer) - min(self.magnitude_buffer)
        return variance <= self.tolerance

def is_inactive(magnitude, prev_magnitude, tolerance=0.3):
    """
    Convenience function for simple inactivity detection.
    
    Safety: Quick check for immediate inactivity assessment.
    Reason: Used when historical data not available for variance calculation.
    """
    detector = InactivityDetector()
    return detector.is_inactive(magnitude, prev_magnitude)
