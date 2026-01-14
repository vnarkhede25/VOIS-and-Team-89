"""
Pre-Fall Instability Detection for Elderly Monitoring

Detects patterns that may precede falls, including:
- Increased jerk (sudden acceleration changes)
- Gait irregularity
- Loss of balance indicators
- Physiological stress patterns
"""

import numpy as np
from collections import deque
from typing import Dict, Any, Optional
import time
import math

class PreFallInstabilityDetector:
    """Detects pre-fall instability patterns."""
    
    def __init__(self, window_size: int = 50, 
                 jerk_threshold: float = 10.0,
                 variance_threshold: float = 2.0,
                 instability_threshold: float = 0.7):
        """
        Initialize pre-fall instability detector.
        
        Args:
            window_size: Number of samples to analyze
            jerk_threshold: Threshold for jerk magnitude
            variance_threshold: Threshold for motion variance
            instability_threshold: Threshold for overall instability risk
        """
        self.window_size = window_size
        self.jerk_threshold = jerk_threshold
        self.variance_threshold = variance_threshold
        self.instability_threshold = instability_threshold
        
        # Data buffers
        self.accel_buffer = deque(maxlen=window_size)
        self.timestamp_buffer = deque(maxlen=window_size)
        
        # Previous values for jerk calculation
        self.prev_ax = 0.0
        self.prev_ay = 0.0
        self.prev_az = 0.0
        self.prev_timestamp = 0.0
        
        # Instability metrics
        self.jerk_history = deque(maxlen=10)
        self.variance_history = deque(maxlen=10)
        
    def update(self, ax: float, ay: float, az: float, 
               timestamp: Optional[float] = None) -> float:
        """
        Update instability detector with new acceleration data.
        
        Args:
            ax, ay, z: Current acceleration values
            timestamp: Current timestamp (defaults to current time)
            
        Returns:
            Instability risk score (0.0 to 1.0)
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Add to buffer
        self.accel_buffer.append((ax, ay, az))
        self.timestamp_buffer.append(timestamp)
        
        # Calculate jerk if we have previous data
        if self.prev_timestamp > 0:
            dt = timestamp - self.prev_timestamp
            if dt > 0:
                jerk_x = (ax - self.prev_ax) / dt
                jerk_y = (ay - self.prev_ay) / dt
                jerk_z = (az - self.prev_az) / dt
                jerk_magnitude = math.sqrt(jerk_x**2 + jerk_y**2 + jerk_z**2)
            else:
                jerk_magnitude = 0.0
        else:
            jerk_magnitude = 0.0
        
        # Update previous values
        self.prev_ax, self.prev_ay, self.prev_az = ax, ay, az
        self.prev_timestamp = timestamp
        
        # Store jerk
        self.jerk_history.append(jerk_magnitude)
        
        # Check if we have enough data for analysis
        if len(self.accel_buffer) < self.window_size:
            return 0.0
        
        # Calculate instability metrics
        instability_score = self._calculate_instability_score()
        
        return instability_score
    
    def _calculate_instability_score(self) -> float:
        """Calculate overall instability score."""
        # Convert buffer to numpy array
        accel_data = np.array(list(self.accel_buffer))
        
        # Calculate variance for each axis
        variance_x = np.var(accel_data[:, 0])
        variance_y = np.var(accel_data[:, 1])
        variance_z = np.var(accel_data[:, 2])
        total_variance = variance_x + variance_y + variance_z
        
        # Store variance
        self.variance_history.append(total_variance)
        
        # Calculate average jerk
        avg_jerk = np.mean(list(self.jerk_history)) if self.jerk_history else 0.0
        
        # Calculate average variance
        avg_variance = np.mean(list(self.variance_history)) if self.variance_history else 0.0
        
        # Normalize metrics
        jerk_score = min(1.0, avg_jerk / self.jerk_threshold)
        variance_score = min(1.0, avg_variance / self.variance_threshold)
        
        # Combine scores (weighted average)
        instability_score = 0.6 * jerk_score + 0.4 * variance_score
        
        return instability_score
    
    def is_unstable(self) -> bool:
        """Check if current state indicates instability."""
        if not self.jerk_history or not self.variance_history:
            return False
        
        recent_instability = self._calculate_instability_score()
        return recent_instability > self.instability_threshold
    
    def get_instability_trend(self) -> str:
        """Get trend of instability over time."""
        if len(self.jerk_history) < 3:
            return "insufficient_data"
        
        recent_jerk = list(self.jerk_history)[-3:]
        if recent_jerk[-1] > recent_jerk[0] * 1.2:
            return "increasing"
        elif recent_jerk[-1] < recent_jerk[0] * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def reset(self):
        """Reset detector state."""
        self.accel_buffer.clear()
        self.timestamp_buffer.clear()
        self.jerk_history.clear()
        self.variance_history.clear()
        
        self.prev_ax = self.prev_ay = self.prev_az = 0.0
        self.prev_timestamp = 0.0
