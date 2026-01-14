"""
Inactivity Detection for Elderly Monitoring

Detects periods of inactivity and prolonged stillness
that may indicate falls, health issues, or need for assistance.
"""

import numpy as np
from collections import deque
from typing import Optional
import time

class InactivityDetector:
    """Detects inactivity periods from sensor data."""
    
    def __init__(self, inactivity_threshold: float = 0.5, 
                 window_size: int = 30, 
                 prolonged_threshold: float = 300.0):
        """
        Initialize inactivity detector.
        
        Args:
            inactivity_threshold: Threshold below which motion is considered inactive
            window_size: Number of samples to analyze
            prolonged_threshold: Seconds to consider inactivity prolonged
        """
        self.inactivity_threshold = inactivity_threshold
        self.window_size = window_size
        self.prolonged_threshold = prolonged_threshold
        
        # Data buffers
        self.magnitude_buffer = deque(maxlen=window_size)
        self.timestamp_buffer = deque(maxlen=window_size)
        
        # State tracking
        self.inactivity_start_time = None
        self.is_inactive = False
        self.inactivity_duration = 0.0
        
    def update(self, acceleration_magnitude: float, timestamp: Optional[float] = None) -> bool:
        """
        Update inactivity detector with new sensor data.
        
        Args:
            acceleration_magnitude: Current acceleration magnitude
            timestamp: Current timestamp (defaults to current time)
            
        Returns:
            True if currently inactive, False otherwise
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Add to buffers
        self.magnitude_buffer.append(acceleration_magnitude)
        self.timestamp_buffer.append(timestamp)
        
        # Check if we have enough data
        if len(self.magnitude_buffer) < self.window_size:
            return False
        
        # Calculate average magnitude over window
        avg_magnitude = np.mean(self.magnitude_buffer)
        
        # Determine if inactive
        currently_inactive = avg_magnitude < self.inactivity_threshold
        
        # Track inactivity periods
        if currently_inactive and not self.is_inactive:
            # Start of inactivity period
            self.inactivity_start_time = timestamp
            self.is_inactive = True
        elif not currently_inactive and self.is_inactive:
            # End of inactivity period
            self.inactivity_duration = timestamp - self.inactivity_start_time
            self.is_inactive = False
            self.inactivity_start_time = None
        elif currently_inactive and self.is_inactive:
            # Continue inactivity
            self.inactivity_duration = timestamp - self.inactivity_start_time
        
        return self.is_inactive
    
    def is_inactive_long(self) -> bool:
        """Check if inactivity is prolonged."""
        return self.is_inactive and self.inactivity_duration > self.prolonged_threshold
    
    def get_inactivity_duration(self) -> float:
        """Get current inactivity duration in seconds."""
        return self.inactivity_duration
    
    def reset(self):
        """Reset detector state."""
        self.magnitude_buffer.clear()
        self.timestamp_buffer.clear()
        self.inactivity_start_time = None
        self.is_inactive = False
        self.inactivity_duration = 0.0
