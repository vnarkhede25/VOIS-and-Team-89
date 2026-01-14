from collections import deque

class FallDetector:
    """
    Fall detection using smoothed magnitude and threshold-based logic.
    
    Safety: Reduces false alarms by smoothing sensor noise and requiring sustained spikes.
    Reason: Real falls produce high acceleration; daily activities may briefly exceed thresholds.
    """
    
    def __init__(self, window_size=5, spike_threshold=18, recovery_threshold=12):
        # Window size: 5 samples smooths noise while maintaining responsiveness
        self.window_size = window_size
        # Spike threshold: 18g distinguishes falls from normal activities (walking ~2-3g)
        self.spike_threshold = spike_threshold
        # Recovery threshold: 12g confirms when motion returns to normal levels
        self.recovery_threshold = recovery_threshold
        self.magnitude_buffer = deque(maxlen=window_size)
        
    def get_smoothed_magnitude(self, magnitude):
        """
        Calculate smoothed magnitude to reduce sensor noise impact.
        
        Safety: Prevents false triggers from sensor spikes or brief impacts.
        Reason: Moving average filters out noise while preserving genuine fall signals.
        """
        self.magnitude_buffer.append(magnitude)
        if len(self.magnitude_buffer) < self.window_size:
            # Not enough data for smoothing - return raw value
            return magnitude
        # Moving average smooths transient spikes while detecting sustained falls
        return sum(self.magnitude_buffer) / len(self.magnitude_buffer)
    
    def detect_fall(self, magnitude):
        """
        Detect fall based on smoothed magnitude threshold.
        
        Safety: Requires sustained high acceleration to trigger fall detection.
        Reason: Falls produce prolonged high acceleration; brief spikes are usually noise.
        """
        smoothed_magnitude = self.get_smoothed_magnitude(magnitude)
        return smoothed_magnitude > self.spike_threshold
    
    def is_in_post_fall_state(self, magnitude):
        """
        Check if system is in post-fall recovery state.
        
        Safety: Prevents repeated fall alarms during recovery period.
        Reason: After a fall, user may be moving slowly; system should allow recovery.
        """
        smoothed_magnitude = self.get_smoothed_magnitude(magnitude)
        return smoothed_magnitude < self.recovery_threshold

def detect_fall(magnitude, threshold=15):
    """
    Convenience function for simple threshold-based fall detection.
    
    Safety: Quick check when smoothing not available or needed.
    Reason: Used for initial testing or when computational resources are limited.
    """
    detector = FallDetector()
    return detector.detect_fall(magnitude)
