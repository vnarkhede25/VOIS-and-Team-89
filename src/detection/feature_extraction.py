import math
import numpy as np
"""
Feature Extraction Layer for Elderly Monitoring System

Extracts meaningful features from raw sensor data for:
- Motion analysis (acceleration, gyroscope, jerk, orientation)
- Vitals analysis (heart rate trends, SpO₂ drops, temperature)
- Temporal features (sliding window statistics)
- Physiological anomalies detection

All features are designed to be shared by:
- Threshold-based fall detection
- ML-based classification
- Pre-fall instability detection
- Decision engine
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from collections import deque
import math
import time
from datetime import datetime, timedelta
from dataclasses import dataclass

# Import required classifiers
from .posture_classifier import PostureClassifier
from .inactivity_detector import InactivityDetector
from .pre_fall_instability import PreFallInstabilityDetector

@dataclass
class FeatureVector:
    """
    Structured feature vector for fall detection ML.
    
    Contains all extracted features in a clean, organized format
    suitable for machine learning model training and inference.
    """
    # Basic sensor data
    timestamp: float
    ax: float
    ay: float
    az: float
    gx: float  # Gyroscope X (simulated)
    gy: float  # Gyroscope Y (simulated)
    gz: float  # Gyroscope Z (simulated)
    
    # Acceleration magnitude statistics
    magnitude_mean: float
    magnitude_std: float
    magnitude_min: float
    magnitude_max: float
    magnitude_range: float
    
    # Gyroscope variance
    gyro_variance_x: float
    gyro_variance_y: float
    gyro_variance_z: float
    gyro_variance_total: float
    
    # Posture transitions
    current_posture: str
    posture_transition_count: int
    posture_stability_score: float
    time_in_current_posture: float
    
    # Inactivity metrics
    inactivity_duration: float
    inactivity_ratio: float
    activity_level: str
    
    # Pre-fall instability
    instability_risk: float
    instability_trend: float
    risk_level: str
    
    # Derived features
    jerk_magnitude: float
    acceleration_energy: float
    motion_smoothness: float
    
    def to_dict(self) -> Dict:
        """Convert feature vector to dictionary format."""
        return {
            'timestamp': self.timestamp,
            'acceleration': {
                'ax': self.ax, 'ay': self.ay, 'az': self.az,
                'magnitude': {
                    'mean': self.magnitude_mean,
                    'std': self.magnitude_std,
                    'min': self.magnitude_min,
                    'max': self.magnitude_max,
                    'range': self.magnitude_range
                }
            },
            'gyroscope': {
                'gx': self.gx, 'gy': self.gy, 'gz': self.gz,
                'variance': {
                    'x': self.gyro_variance_x,
                    'y': self.gyro_variance_y,
                    'z': self.gyro_variance_z,
                    'total': self.gyro_variance_total
                }
            },
            'posture': {
                'current': self.current_posture,
                'transition_count': self.posture_transition_count,
                'stability_score': self.posture_stability_score,
                'time_in_posture': self.time_in_current_posture
            },
            'inactivity': {
                'duration': self.inactivity_duration,
                'ratio': self.inactivity_ratio,
                'activity_level': self.activity_level
            },
            'instability': {
                'risk_score': self.instability_risk,
                'trend': self.instability_trend,
                'risk_level': self.risk_level
            },
            'derived': {
                'jerk_magnitude': self.jerk_magnitude,
                'acceleration_energy': self.acceleration_energy,
                'motion_smoothness': self.motion_smoothness
            }
        }
    
    def to_flat_array(self) -> np.ndarray:
        """Convert feature vector to flat numpy array for ML models."""
        features = [
            # Basic acceleration
            self.ax, self.ay, self.az,
            
            # Magnitude statistics
            self.magnitude_mean, self.magnitude_std, self.magnitude_min, 
            self.magnitude_max, self.magnitude_range,
            
            # Gyroscope variance
            self.gyro_variance_x, self.gyro_variance_y, self.gyro_variance_z, self.gyro_variance_total,
            
            # Posture features
            self.posture_transition_count, self.posture_stability_score, self.time_in_current_posture,
            
            # Inactivity features
            self.inactivity_duration, self.inactivity_ratio,
            
            # Instability features
            self.instability_risk, self.instability_trend,
            
            # Derived features
            self.jerk_magnitude, self.acceleration_energy, self.motion_smoothness
        ]
        return np.array(features)

class FeatureExtractor:
    """
    Comprehensive feature extraction pipeline for fall detection ML.
    
    Extracts statistical, temporal, and behavioral features from sensor data
    to create rich feature vectors for machine learning models.
    """
    
    def __init__(self, window_size=50, posture_window=10):
        # Window sizes for feature calculation
        self.window_size = window_size
        self.posture_window = posture_window
        
        # Data buffers
        self.accel_buffer = deque(maxlen=window_size)
        self.gyro_buffer = deque(maxlen=window_size)
        self.magnitude_buffer = deque(maxlen=window_size)
        
        # Posture tracking
        self.posture_history = deque(maxlen=posture_window)
        self.posture_transition_times = deque(maxlen=20)
        self.current_posture_start_time = 0.0
        
        # Inactivity tracking
        self.inactivity_start_time = None
        self.inactivity_periods = []
        
        # Feature extractors
        self.posture_classifier = PostureClassifier()
        self.inactivity_detector = InactivityDetector()
        self.instability_detector = PreFallInstabilityDetector()
        
        # Previous values for derived features
        self.prev_ax, self.prev_ay, self.prev_az = 0.0, 0.0, 0.0
        self.prev_gx, self.prev_gy, self.prev_gz = 0.0, 0.0, 0.0
        self.prev_magnitude = 0.0
        
        # Timestamp tracking
        self.start_time = 0.0
        self.sample_count = 0
    
    def update_data(self, sensor_data: Dict[str, Any]):
        """
        Update feature extractor with new sensor data dictionary.
        
        Args:
            sensor_data: Dictionary containing sensor readings
        """
        # Extract values from sensor data
        ax = sensor_data.get('ax', 0)
        ay = sensor_data.get('ay', 0) 
        az = sensor_data.get('az', 0)
        gx = sensor_data.get('gx', 0)
        gy = sensor_data.get('gy', 0)
        gz = sensor_data.get('gz', 0)
        timestamp = sensor_data.get('timestamp', time.time())
        
        # Call existing update method
        self.update(ax, ay, az, gx, gy, gz, timestamp)
    
    def update(self, ax, ay, az, gx=None, gy=None, gz=None, timestamp=None):
        """
        Update feature extractor with new sensor data.
        
        Args:
            ax, ay, az: Acceleration values in m/s²
            gx, gy, gz: Gyroscope values in rad/s (optional, will simulate if None)
            timestamp: Timestamp in seconds (optional, will use sample count if None)
            
        Returns:
            FeatureVector: Complete feature vector for current time step
        """
        # Handle timestamp
        if timestamp is None:
            timestamp = self.sample_count * 0.1  # Assume 100ms sampling
        if self.start_time == 0.0:
            self.start_time = timestamp
        
        # Simulate gyroscope data if not provided
        if gx is None or gy is None or gz is None:
            gx, gy, gz = self._simulate_gyroscope(ax, ay, az)
        
        # Store sensor data
        self.accel_buffer.append((ax, ay, az))
        self.gyro_buffer.append((gx, gy, gz))
        
        magnitude = math.sqrt(ax**2 + ay**2 + az**2)
        self.magnitude_buffer.append(magnitude)
        
        # Update feature extractors
        instability_risk = self.instability_detector.update(ax, ay, az)
        posture_obj = self.posture_classifier.classify_posture(ax, ay, az)
        current_posture = posture_obj.value if hasattr(posture_obj, 'value') else str(posture_obj)
        inactive = self.inactivity_detector.update(magnitude, timestamp)
        
        # Track posture transitions
        self._track_posture_transitions(current_posture, timestamp)
        
        # Track inactivity
        self._track_inactivity(inactive, timestamp)
        
        # Extract features
        features = self._extract_features(
            ax, ay, az, gx, gy, gz, magnitude, 
            current_posture, inactive, instability_risk, timestamp
        )
        
        # Update previous values
        self.prev_ax, self.prev_ay, self.prev_az = ax, ay, az
        self.prev_gx, self.prev_gy, self.prev_gz = gx, gy, gz
        self.prev_magnitude = magnitude
        self.sample_count += 1
        
        return features
    
    def _simulate_gyroscope(self, ax, ay, az):
        """
        Simulate gyroscope data based on acceleration changes.
        
        In real implementation, this would use actual gyroscope readings.
        This simulation provides reasonable angular velocity estimates.
        """
        # Calculate angular velocity from acceleration changes
        dt = 0.1  # Sampling interval
        
        # Simple differentiation to estimate angular velocity
        dax = ax - self.prev_ax
        day = ay - self.prev_ay
        daz = az - self.prev_az
        
        # Convert to angular velocity (simplified model)
        gx = dax / dt * 0.1
        gy = day / dt * 0.1
        gz = daz / dt * 0.1
        
        # Add some noise for realism
        gx += np.random.normal(0, 0.05)
        gy += np.random.normal(0, 0.05)
        gz += np.random.normal(0, 0.05)
        
        return gx, gy, gz
    
    def _track_posture_transitions(self, current_posture, timestamp):
        """Track posture changes and calculate stability metrics."""
        self.posture_history.append(current_posture)
        
        # Initialize stability score
        stability_score = 1.0
        
        # Check for posture transition
        if len(self.posture_history) > 1:
            prev_posture = self.posture_history[-2]
            if prev_posture != current_posture:
                self.posture_transition_times.append(timestamp)
                self.current_posture_start_time = timestamp
            else:
                # Update stability score based on consistency
                if len(self.posture_history) >= self.posture_window:
                    recent_postures = list(self.posture_history)[-self.posture_window:]
                    unique_postures = len(set(recent_postures))
                    # Stability score: higher when posture is consistent
                    stability_score = (self.posture_window - unique_postures + 1) / self.posture_window
                else:
                    stability_score = 1.0
        else:
            self.current_posture_start_time = timestamp
            stability_score = 1.0
        
        return stability_score
    
    def _track_inactivity(self, inactive, timestamp):
        """Track inactivity periods and duration."""
        if inactive:
            if self.inactivity_start_time is None:
                self.inactivity_start_time = timestamp
            else:
                # Still inactive, continue tracking
                pass
        else:
            if self.inactivity_start_time is not None:
                # Inactivity period ended
                duration = timestamp - self.inactivity_start_time
                self.inactivity_periods.append(duration)
                self.inactivity_start_time = None
    
    def _extract_features(self, ax, ay, az, gx, gy, gz, magnitude, 
                        current_posture, inactive, instability_risk, timestamp):
        """Extract all features from current and historical data."""
        
        # 1. Acceleration magnitude statistics
        if len(self.magnitude_buffer) >= 2:
            magnitudes = list(self.magnitude_buffer)
            magnitude_mean = np.mean(magnitudes)
            magnitude_std = np.std(magnitudes)
            magnitude_min = np.min(magnitudes)
            magnitude_max = np.max(magnitudes)
            magnitude_range = magnitude_max - magnitude_min
        elif len(self.magnitude_buffer) == 1:
            magnitudes = list(self.magnitude_buffer)
            magnitude_mean = magnitudes[0]
            magnitude_std = 0.0
            magnitude_min = magnitudes[0]
            magnitude_max = magnitudes[0]
            magnitude_range = 0.0
        else:
            magnitude_mean = magnitude_std = magnitude_min = magnitude_max = magnitude_range = magnitude
        
        # 2. Gyroscope variance
        if len(self.gyro_buffer) >= 2:
            gyro_data = np.array(list(self.gyro_buffer))
            gyro_variance_x = np.var(gyro_data[:, 0])
            gyro_variance_y = np.var(gyro_data[:, 1])
            gyro_variance_z = np.var(gyro_data[:, 2])
            gyro_variance_total = np.var(gyro_data)
        else:
            gyro_variance_x = gyro_variance_y = gyro_variance_z = gyro_variance_total = 0.0
        
        # 3. Posture transition features
        posture_transition_count = len(self.posture_transition_times)
        if len(self.posture_history) >= self.posture_window:
            recent_postures = list(self.posture_history)[-self.posture_window:]
            unique_postures = len(set(recent_postures))
            posture_stability_score = (self.posture_window - unique_postures + 1) / self.posture_window
        else:
            posture_stability_score = 1.0
        
        time_in_current_posture = timestamp - self.current_posture_start_time
        
        # 4. Inactivity features
        if self.inactivity_start_time is not None:
            inactivity_duration = timestamp - self.inactivity_start_time
        else:
            inactivity_duration = 0.0
        
        total_samples = len(self.magnitude_buffer)
        if total_samples > 0:
            # Calculate inactivity ratio from recent history
            recent_inactive = sum(1 for i in range(min(10, total_samples)) 
                               if i < len(self.inactivity_periods) and self.inactivity_periods[-(i+1)] > 1.0)
            inactivity_ratio = recent_inactive / min(10, total_samples)
        else:
            inactivity_ratio = 0.0
        
        if inactivity_duration > 2.0:
            activity_level = "SEDENTARY"
        elif inactivity_duration > 0.5:
            activity_level = "LOW"
        else:
            activity_level = "ACTIVE"
        
        # 5. Pre-fall instability features
        risk_level = instability_risk
        
        # Calculate instability trend (direction of risk change)
        if len(self.magnitude_buffer) >= 5:
            recent_magnitudes = list(self.magnitude_buffer)[-5:]
            recent_variance = np.var(recent_magnitudes)
            older_magnitudes = list(self.magnitude_buffer)[-10:-5] if len(self.magnitude_buffer) >= 10 else []
            if older_magnitudes:
                older_variance = np.var(older_magnitudes)
                instability_trend = recent_variance - older_variance
            else:
                instability_trend = 0.0
        else:
            instability_trend = 0.0
        
        # 6. Derived features
        dt = 0.1
        jerk_magnitude = math.sqrt(
            ((ax - self.prev_ax) / dt) ** 2 +
            ((ay - self.prev_ay) / dt) ** 2 +
            ((az - self.prev_az) / dt) ** 2
        )
        
        # Acceleration energy (signal power)
        if len(self.magnitude_buffer) >= 2:
            acceleration_energy = np.sum(np.array(list(self.magnitude_buffer)) ** 2) / len(self.magnitude_buffer)
        else:
            acceleration_energy = magnitude ** 2
        
        # Motion smoothness (inverse of variance)
        motion_smoothness = 1.0 / (1.0 + magnitude_std) if magnitude_std > 0 else 1.0
        
        return FeatureVector(
            # Basic sensor data
            timestamp=timestamp,
            ax=ax, ay=ay, az=az,
            gx=gx, gy=gy, gz=gz,
            
            # Acceleration magnitude statistics
            magnitude_mean=magnitude_mean,
            magnitude_std=magnitude_std,
            magnitude_min=magnitude_min,
            magnitude_max=magnitude_max,
            magnitude_range=magnitude_range,
            
            # Gyroscope variance
            gyro_variance_x=gyro_variance_x,
            gyro_variance_y=gyro_variance_y,
            gyro_variance_z=gyro_variance_z,
            gyro_variance_total=gyro_variance_total,
            
            # Posture transitions
            current_posture=current_posture,
            posture_transition_count=posture_transition_count,
            posture_stability_score=posture_stability_score,
            time_in_current_posture=time_in_current_posture,
            
            # Inactivity duration
            inactivity_duration=inactivity_duration,
            inactivity_ratio=inactivity_ratio,
            activity_level=activity_level,
            
            # Pre-fall instability
            instability_risk=instability_risk,
            instability_trend=instability_trend,
            risk_level=risk_level,
            
            # Derived features
            jerk_magnitude=jerk_magnitude,
            acceleration_energy=acceleration_energy,
            motion_smoothness=motion_smoothness
        )
    
    def get_current_features(self) -> Optional[Dict[str, Any]]:
        """Get current extracted features."""
        if len(self.magnitude_buffer) < 10:
            return None
        
        # Get latest sensor data
        if self.accel_buffer and self.gyro_buffer:
            ax, ay, az = self.accel_buffer[-1]
            gx, gy, gz = self.gyro_buffer[-1]
            magnitude = self.magnitude_buffer[-1]
            
            # Extract features
            features = self._extract_features(
                ax, ay, az, gx, gy, gz, magnitude,
                instability_risk=self.instability_detector.update(ax, ay, az),
                current_posture=str(self.posture_classifier.classify_posture(ax, ay, az)),
                inactive=self.inactivity_detector.update(magnitude, time.time()),
                timestamp=time.time()
            )
            
            return features
        
        return None
    
    def get_feature_names(self) -> List[str]:
        """Get list of all feature names for ML model training."""
        return [
            'ax', 'ay', 'az',
            'magnitude_mean', 'magnitude_std', 'magnitude_min', 'magnitude_max', 'magnitude_range',
            'gyro_variance_x', 'gyro_variance_y', 'gyro_variance_z', 'gyro_variance_total',
            'posture_transition_count', 'posture_stability_score', 'time_in_current_posture',
            'inactivity_duration', 'inactivity_ratio',
            'instability_risk', 'instability_trend',
            'jerk_magnitude', 'acceleration_energy', 'motion_smoothness'
        ]
    
    def reset(self):
        """Reset all buffers and tracking variables."""
        self.accel_buffer.clear()
        self.gyro_buffer.clear()
        self.magnitude_buffer.clear()
        self.posture_history.clear()
        self.posture_transition_times.clear()
        self.inactivity_periods.clear()
        self.inactivity_start_time = None
        self.current_posture_start_time = 0.0
        self.prev_ax = self.prev_ay = self.prev_az = 0.0
        self.prev_gx = self.prev_gy = self.prev_gz = 0.0
        self.prev_magnitude = 0.0
        self.start_time = 0.0
        self.sample_count = 0
        
        # Reset feature extractors
        self.instability_detector = PreFallInstabilityDetector()
        self.posture_classifier = PostureClassifier()
        self.inactivity_detector = InactivityDetector()

# Global feature extractor instance
_feature_extractor = None

def initialize_feature_extractor(window_size: int = 30, sampling_rate: int = 100):
    """Initialize the global feature extractor."""
    global _feature_extractor
    _feature_extractor = FeatureExtractor(window_size, sampling_rate)
    return _feature_extractor

def get_feature_extractor() -> FeatureExtractor:
    """Get the global feature extractor instance."""
    return _feature_extractor

def extract_features_from_data(sensor_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract features from sensor data."""
    if _feature_extractor:
        _feature_extractor.update_data(sensor_data)
        return _feature_extractor.get_current_features()
    return None

def get_feature_vector() -> Optional[np.ndarray]:
    """Get feature vector for ML models."""
    if _feature_extractor:
        return _feature_extractor.get_feature_vector()
    return None

def reset_feature_extractor():
    """Reset the feature extractor."""
    if _feature_extractor:
        _feature_extractor.reset_features()

# Convenience function for backward compatibility
def extract_features(ax, ay, az, gx=None, gy=None, gz=None, timestamp=None):
    """
    Convenience function for single-sample feature extraction.
    
    Args:
        ax, ay, az: Acceleration values
        gx, gy, gz: Gyroscope values (optional)
        timestamp: Timestamp (optional)
        
    Returns:
        FeatureVector: Extracted features
    """
    extractor = FeatureExtractor()
    return extractor.update(ax, ay, az, gx, gy, gz, timestamp)
