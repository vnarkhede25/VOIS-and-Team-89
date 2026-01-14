import math
import numpy as np
from collections import deque
from detection.motion_analysis import calculate_magnitude

class PreFallInstabilityDetector:
    """
    Detects pre-fall instability patterns using motion analysis.
    
    Physics-based approach:
    - Variance: Measures motion irregularity and unpredictability
    - Jerk: Rate of acceleration change (derivative of acceleration)
    - Motion inconsistency: Compares current motion with historical patterns
    
    High values indicate loss of balance and increased fall risk.
    """
    
    def __init__(self, window_size=10, history_size=50):
        # Window for real-time analysis (last N samples)
        self.window_size = window_size
        self.accel_window = deque(maxlen=window_size)
        self.magnitude_window = deque(maxlen=window_size)
        
        # Historical baseline for normal motion patterns
        self.history_size = history_size
        self.baseline_magnitudes = deque(maxlen=history_size)
        self.baseline_variance = 0.0
        
        # Risk scoring parameters
        self.variance_weight = 0.3
        self.jerk_weight = 0.4
        self.inconsistency_weight = 0.3
        
        # Thresholds for risk assessment
        self.variance_threshold = 2.0
        self.jerk_threshold = 5.0
        self.inconsistency_threshold = 1.5
        
        # Previous values for jerk calculation
        self.prev_ax, self.prev_ay, self.prev_az = 0.0, 0.0, 0.0
        self.prev_magnitude = 0.0
        
    def update(self, ax, ay, az):
        """
        Update detector with new acceleration data.
        
        Args:
            ax, ay, az: Current acceleration values in m/s²
            
        Returns:
            float: Risk score between 0 (stable) and 1 (high risk)
        """
        # Calculate current magnitude
        magnitude = calculate_magnitude(ax, ay, az)
        
        # Store current values
        self.accel_window.append((ax, ay, az))
        self.magnitude_window.append(magnitude)
        
        # Update baseline with stable periods
        if len(self.magnitude_window) >= self.window_size:
            current_variance = self._calculate_variance()
            if current_variance < 0.5:  # Stable motion
                self.baseline_magnitudes.extend(self.magnitude_window)
        
        # Calculate risk factors
        variance_risk = self._calculate_variance_risk()
        jerk_risk = self._calculate_jerk_risk(ax, ay, az, magnitude)
        inconsistency_risk = self._calculate_inconsistency_risk(magnitude)
        
        # Combine risk factors with weighted average
        total_risk = (
            self.variance_weight * variance_risk +
            self.jerk_weight * jerk_risk +
            self.inconsistency_weight * inconsistency_risk
        )
        
        # Update previous values for next iteration
        self.prev_ax, self.prev_ay, self.prev_az = ax, ay, az
        self.prev_magnitude = magnitude
        
        # Clamp to [0, 1] range
        return max(0.0, min(1.0, total_risk))
    
    def _calculate_variance(self):
        """
        Calculate variance of acceleration magnitudes in current window.
        
        High variance indicates irregular, unpredictable motion patterns
        commonly seen before falls (stumbling, loss of balance).
        """
        if len(self.magnitude_window) < 2:
            return 0.0
        
        magnitudes = list(self.magnitude_window)
        mean = sum(magnitudes) / len(magnitudes)
        variance = sum((m - mean) ** 2 for m in magnitudes) / len(magnitudes)
        
        return variance
    
    def _calculate_variance_risk(self):
        """
        Convert variance to risk score (0-1).
        
        Normal walking: variance < 0.5
        Unstable motion: variance 0.5-2.0
        Pre-fall: variance > 2.0
        """
        variance = self._calculate_variance()
        
        # Normalize using sigmoid-like function
        if variance <= self.variance_threshold:
            return variance / self.variance_threshold * 0.5
        else:
            # Exponential growth for high variance
            return 0.5 + 0.5 * (1 - math.exp(-(variance - self.variance_threshold) / 2.0))
    
    def _calculate_jerk_risk(self, ax, ay, az, magnitude):
        """
        Calculate jerk (rate of acceleration change).
        
        Jerk = derivative of acceleration
        High jerk indicates sudden, uncontrolled movements
        typical of loss of balance scenarios.
        """
        if len(self.accel_window) < 2:
            return 0.0
        
        # Calculate jerk for each axis
        dt = 0.1  # Assume 100ms sampling interval
        jerk_x = abs(ax - self.prev_ax) / dt
        jerk_y = abs(ay - self.prev_ay) / dt
        jerk_z = abs(az - self.prev_az) / dt
        
        # Magnitude jerk
        jerk_magnitude = math.sqrt(jerk_x**2 + jerk_y**2 + jerk_z**2)
        
        # Normalize to risk score
        if jerk_magnitude <= self.jerk_threshold:
            return jerk_magnitude / self.jerk_threshold * 0.5
        else:
            return 0.5 + 0.5 * (1 - math.exp(-(jerk_magnitude - self.jerk_threshold) / 3.0))
    
    def _calculate_inconsistency_risk(self, magnitude):
        """
        Calculate motion inconsistency compared to historical baseline.
        
        Compares current motion patterns with established normal patterns.
        Sudden deviations from baseline indicate instability.
        """
        if len(self.baseline_magnitudes) < 10:
            return 0.0  # Insufficient baseline data
        
        # Calculate baseline statistics
        baseline = list(self.baseline_magnitudes)
        baseline_mean = sum(baseline) / len(baseline)
        baseline_std = math.sqrt(sum((m - baseline_mean) ** 2 for m in baseline) / len(baseline))
        
        if baseline_std < 0.1:  # Avoid division by very small numbers
            baseline_std = 0.1
        
        # Calculate z-score of current magnitude
        z_score = abs(magnitude - baseline_mean) / baseline_std
        
        # Convert z-score to risk (0-1)
        # z-score > 3 is highly unusual (99.7% confidence)
        if z_score <= self.inconsistency_threshold:
            return z_score / self.inconsistency_threshold * 0.5
        else:
            return 0.5 + 0.5 * (1 - math.exp(-(z_score - self.inconsistency_threshold) / 2.0))
    
    def get_risk_level(self, risk_score):
        """
        Convert numeric risk score to descriptive level.
        
        Args:
            risk_score: Risk score between 0 and 1
            
        Returns:
            str: Risk level description
        """
        if risk_score < 0.2:
            return "LOW"
        elif risk_score < 0.5:
            return "MODERATE"
        elif risk_score < 0.8:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def reset_baseline(self):
        """Reset baseline motion patterns (useful after position changes)."""
        self.baseline_magnitudes.clear()

def detect_instability(ax, ay, az):
    """
    Legacy function for backward compatibility.
    
    Args:
        ax, ay, az: Acceleration values
        
    Returns:
        float: Risk score between 0 and 1
    """
    detector = PreFallInstabilityDetector()
    return detector.update(ax, ay, az)
