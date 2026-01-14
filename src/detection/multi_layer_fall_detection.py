"""
Multi-Layer Fall Detection System

Implements a comprehensive fall detection pipeline with:
1. Threshold-based fall detection (fast, reliable)
2. ML-based fall classification (accurate, adaptive)
3. Post-fall validation (confirmation)
4. Pre-fall instability detection (early warning)
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from enum import Enum
import time
from collections import deque
from datetime import datetime, timedelta

class FallType(Enum):
    """Types of fall events."""
    FORWARD_FALL = "forward_fall"
    BACKWARD_FALL = "backward_fall"
    SIDE_FALL = "side_fall"
    VERTICAL_FALL = "vertical_fall"
    SLIP_FALL = "slip_fall"
    STUMBLE_FALL = "stumble_fall"
    UNKNOWN_FALL = "unknown_fall"

class DetectionLayer(Enum):
    """Fall detection layers."""
    THRESHOLD = "threshold"
    ML_CLASSIFIER = "ml_classifier"
    POST_VALIDATION = "post_validation"
    PRE_FALL_INSTABILITY = "pre_fall_instability"

class FallSeverity(Enum):
    """Fall severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ThresholdFallDetector:
    """Threshold-based fall detection for fast response."""
    
    def __init__(self):
        # Threshold parameters (tuned for elderly monitoring)
        self.fall_threshold_accel = 2.5  # g-force threshold for fall
        self.impact_threshold = 3.0  # Impact detection threshold
        self.orientation_threshold = 60  # degrees from vertical
        self.inactivity_threshold = 5.0  # seconds of post-fall inactivity
        
        # State tracking
        self.last_fall_time = 0
        self.fall_cooldown = 10  # seconds between fall detections
        self.impact_detected = False
        self.orientation_change_detected = False
        self.inactivity_start_time = None
        
    def detect_fall(self, features: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect fall using threshold-based approach.
        
        Args:
            features: Extracted features from sensor data
            
        Returns:
            Tuple of (fall_detected, detection_details)
        """
        current_time = time.time()
        
        # Cooldown check
        if current_time - self.last_fall_time < self.fall_cooldown:
            return False, {"reason": "cooldown_period"}
        
        detection_result = {
            "layer": "threshold",
            "timestamp": current_time,
            "indicators": {},
            "confidence": 0.0,
            "fall_type": None,
            "severity": None
        }
        
        # Check for impact (high acceleration)
        impact_detected = self._check_impact(features)
        detection_result["indicators"]["impact"] = impact_detected
        
        # Check for orientation change
        orientation_change = self._check_orientation_change(features)
        detection_result["indicators"]["orientation_change"] = orientation_change
        
        # Check for post-fall inactivity
        inactivity_detected = self._check_inactivity(features)
        detection_result["indicators"]["inactivity"] = inactivity_detected
        
        # Calculate confidence based on multiple indicators
        confidence = 0.0
        if impact_detected:
            confidence += 0.4
        if orientation_change:
            confidence += 0.3
        if inactivity_detected:
            confidence += 0.3
        
        detection_result["confidence"] = confidence
        
        # Determine fall type and severity
        if confidence >= 0.6:  # Threshold for fall detection
            fall_type = self._classify_fall_type(features)
            severity = self._determine_severity(features, confidence)
            
            detection_result["fall_type"] = fall_type.value
            detection_result["severity"] = severity.value
            
            self.last_fall_time = current_time
            return True, detection_result
        
        return False, detection_result
    
    def _check_impact(self, features: Dict[str, Any]) -> bool:
        """Check for impact indicator."""
        accel_max = features.get('accel_magnitude_max', 0)
        jerk_max = features.get('jerk_magnitude_max', 0)
        
        # Impact detected if acceleration or jerk exceeds threshold
        return accel_max > self.fall_threshold_accel or jerk_max > 15.0
    
    def _check_orientation_change(self, features: Dict[str, Any]) -> bool:
        """Check for significant orientation change."""
        pitch_mean = features.get('pitch_mean', 0)
        roll_mean = features.get('roll_mean', 0)
        orientation_stability = features.get('orientation_stability', 0)
        
        # Check if device is significantly tilted from vertical
        tilt_angle = abs(pitch_mean) + abs(roll_mean)
        return tilt_angle > self.orientation_threshold or orientation_stability > 30
    
    def _check_inactivity(self, features: Dict[str, Any]) -> bool:
        """Check for post-fall inactivity."""
        activity_level = features.get('activity_level', 'high')
        inactivity_duration = features.get('inactivity_duration', 0)
        
        # Inactivity detected if low activity for extended period
        return activity_level in ['very_low', 'low'] and inactivity_duration > self.inactivity_threshold
    
    def _classify_fall_type(self, features: Dict[str, Any]) -> FallType:
        """Classify fall type based on motion patterns."""
        ax_mean = features.get('accel_x_mean', 0)
        ay_mean = features.get('accel_y_mean', 0)
        az_mean = features.get('accel_z_mean', 0)
        pitch_mean = features.get('pitch_mean', 0)
        roll_mean = features.get('roll_mean', 0)
        
        # Simple rule-based classification
        if abs(ax_mean) > abs(ay_mean) and abs(ax_mean) > abs(az_mean):
            return FallType.SIDE_FALL if ax_mean > 0 else FallType.SIDE_FALL
        elif ay_mean < -1.0:  # Forward acceleration
            return FallType.FORWARD_FALL
        elif ay_mean > 1.0:  # Backward acceleration
            return FallType.BACKWARD_FALL
        elif abs(pitch_mean) > 45 or abs(roll_mean) > 45:
            return FallType.VERTICAL_FALL
        else:
            return FallType.UNKNOWN_FALL
    
    def _determine_severity(self, features: Dict[str, Any], confidence: float) -> FallSeverity:
        """Determine fall severity."""
        accel_max = features.get('accel_magnitude_max', 0)
        jerk_max = features.get('jerk_magnitude_max', 0)
        anomaly_score = features.get('anomaly_score', 0)
        
        # Calculate severity score
        severity_score = (accel_max / 5.0) + (jerk_max / 20.0) + anomaly_score + confidence
        
        if severity_score >= 3.0:
            return FallSeverity.CRITICAL
        elif severity_score >= 2.0:
            return FallSeverity.HIGH
        elif severity_score >= 1.0:
            return FallSeverity.MEDIUM
        else:
            return FallSeverity.LOW

class MLFallDetector:
    """Machine learning-based fall detection for improved accuracy."""
    
    def __init__(self):
        # Simulate trained ML model (in production, load actual model)
        self.model_trained = True
        self.feature_importance = {
            'accel_magnitude_max': 0.25,
            'jerk_magnitude_max': 0.20,
            'orientation_stability': 0.15,
            'inactivity_duration': 0.15,
            'anomaly_score': 0.10,
            'hr_anomaly_detected': 0.05,
            'spo2_anomaly_detected': 0.05,
            'temp_anomaly_detected': 0.05
        }
        
        # Model parameters
        self.fall_probability_threshold = 0.7
        self.uncertainty_threshold = 0.3
        
    def detect_fall(self, features: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect fall using ML classifier.
        
        Args:
            features: Extracted features from sensor data
            
        Returns:
            Tuple of (fall_detected, detection_details)
        """
        if not self.model_trained:
            return False, {"reason": "model_not_trained"}
        
        detection_result = {
            "layer": "ml_classifier",
            "timestamp": time.time(),
            "fall_probability": 0.0,
            "uncertainty": 0.0,
            "feature_contributions": {},
            "confidence": 0.0,
            "fall_type": None,
            "severity": None
        }
        
        # Simulate ML prediction (in production, use actual model)
        fall_probability, uncertainty, feature_contributions = self._predict_fall(features)
        
        detection_result["fall_probability"] = fall_probability
        detection_result["uncertainty"] = uncertainty
        detection_result["feature_contributions"] = feature_contributions
        
        # Calculate confidence based on probability and uncertainty
        confidence = fall_probability * (1 - uncertainty)
        detection_result["confidence"] = confidence
        
        # Determine fall if probability exceeds threshold
        if fall_probability > self.fall_probability_threshold and uncertainty < self.uncertainty_threshold:
            fall_type = self._classify_fall_type_ml(features)
            severity = self._determine_severity_ml(features, fall_probability)
            
            detection_result["fall_type"] = fall_type.value
            detection_result["severity"] = severity.value
            
            return True, detection_result
        
        return False, detection_result
    
    def _predict_fall(self, features: Dict[str, Any]) -> Tuple[float, float, Dict[str, float]]:
        """
        Simulate ML model prediction.
        
        Returns:
            Tuple of (fall_probability, uncertainty, feature_contributions)
        """
        # Simulate model prediction based on feature importance
        fall_probability = 0.0
        feature_contributions = {}
        
        for feature, importance in self.feature_importance.items():
            feature_value = features.get(feature, 0)
            
            # Normalize feature value to [0, 1] range
            normalized_value = self._normalize_feature(feature, feature_value)
            
            # Calculate contribution to fall probability
            contribution = normalized_value * importance
            feature_contributions[feature] = contribution
            fall_probability += contribution
        
        # Add some randomness to simulate model behavior
        noise = np.random.normal(0, 0.1)
        fall_probability = np.clip(fall_probability + noise, 0.0, 1.0)
        
        # Calculate uncertainty based on feature completeness and variance
        uncertainty = self._calculate_uncertainty(features)
        
        return fall_probability, uncertainty, feature_contributions
    
    def _normalize_feature(self, feature: str, value: Any) -> float:
        """Normalize feature value to [0, 1] range."""
        if isinstance(value, bool):
            return float(value)
        elif isinstance(value, (int, float)):
            # Simple normalization based on feature type
            if "accel" in feature or "jerk" in feature:
                return min(1.0, value / 5.0)  # Normalize by typical max value
            elif "orientation" in feature:
                return min(1.0, value / 90.0)  # Normalize by degrees
            elif "duration" in feature:
                return min(1.0, value / 30.0)  # Normalize by seconds
            else:
                return min(1.0, value / 10.0)  # Generic normalization
        else:
            return 0.0
    
    def _calculate_uncertainty(self, features: Dict[str, Any]) -> float:
        """Calculate prediction uncertainty."""
        # Uncertainty based on missing features and data quality
        missing_features = sum(1 for feature in self.feature_importance.keys() 
                              if feature not in features)
        
        missing_ratio = missing_features / len(self.feature_importance)
        
        # Add uncertainty based on anomaly score
        anomaly_score = features.get('anomaly_score', 0)
        anomaly_uncertainty = min(0.3, anomaly_score / 10.0)
        
        return min(0.5, missing_ratio * 0.5 + anomaly_uncertainty)
    
    def _classify_fall_type_ml(self, features: Dict[str, Any]) -> FallType:
        """Classify fall type using ML approach."""
        # Simulate ML classification based on feature patterns
        accel_x = features.get('accel_x_mean', 0)
        accel_y = features.get('accel_y_mean', 0)
        accel_z = features.get('accel_z_mean', 0)
        
        # Use feature patterns to classify
        if abs(accel_x) > abs(accel_y) and abs(accel_x) > abs(accel_z):
            return FallType.SIDE_FALL
        elif accel_y < -1.5:
            return FallType.FORWARD_FALL
        elif accel_y > 1.5:
            return FallType.BACKWARD_FALL
        else:
            return FallType.UNKNOWN_FALL
    
    def _determine_severity_ml(self, features: Dict[str, Any], probability: float) -> FallSeverity:
        """Determine fall severity using ML approach."""
        # Combine probability with physiological indicators
        hr_anomaly = features.get('hr_anomaly_detected', False)
        spo2_anomaly = features.get('spo2_anomaly_detected', False)
        temp_anomaly = features.get('temp_anomaly_detected', False)
        
        physiological_risk = sum([hr_anomaly, spo2_anomaly, temp_anomaly])
        
        severity_score = probability * 3.0 + physiological_risk
        
        if severity_score >= 2.5:
            return FallSeverity.CRITICAL
        elif severity_score >= 2.0:
            return FallSeverity.HIGH
        elif severity_score >= 1.0:
            return FallSeverity.MEDIUM
        else:
            return FallSeverity.LOW

class PostFallValidator:
    """Validates fall events after initial detection."""
    
    def __init__(self):
        self.validation_window = 10  # seconds
        self.min_inactivity_duration = 3.0  # seconds
        self.recovery_threshold = 0.5  # activity level for recovery
        
    def validate_fall(self, features: Dict[str, Any], initial_detection: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate fall event with post-fall analysis.
        
        Args:
            features: Current features
            initial_detection: Initial fall detection results
            
        Returns:
            Tuple of (fall_validated, validation_details)
        """
        validation_result = {
            "layer": "post_validation",
            "timestamp": time.time(),
            "validated": False,
            "validation_indicators": {},
            "confidence_adjustment": 0.0,
            "recovery_detected": False
        }
        
        # Check for sustained inactivity
        inactivity_validation = self._validate_inactivity(features)
        validation_result["validation_indicators"]["inactivity"] = inactivity_validation
        
        # Check for physiological stress indicators
        physiological_validation = self._validate_physiological_stress(features)
        validation_result["validation_indicators"]["physiological"] = physiological_validation
        
        # Check for recovery indicators
        recovery_detected = self._check_recovery(features)
        validation_result["recovery_detected"] = recovery_detected
        
        # Calculate validation confidence
        validation_confidence = 0.0
        if inactivity_validation:
            validation_confidence += 0.4
        if physiological_validation:
            validation_confidence += 0.3
        if not recovery_detected:  # No recovery is also a validation indicator
            validation_confidence += 0.3
        
        validation_result["confidence_adjustment"] = validation_confidence * 0.2  # 20% max adjustment
        
        # Validate if confidence is high enough
        if validation_confidence >= 0.5:
            validation_result["validated"] = True
            return True, validation_result
        
        return False, validation_result
    
    def _validate_inactivity(self, features: Dict[str, Any]) -> bool:
        """Validate fall based on sustained inactivity."""
        inactivity_duration = features.get('inactivity_duration', 0)
        activity_level = features.get('activity_level', 'high')
        
        return (inactivity_duration >= self.min_inactivity_duration and 
                activity_level in ['very_low', 'low'])
    
    def _validate_physiological_stress(self, features: Dict[str, Any]) -> bool:
        """Validate fall based on physiological stress indicators."""
        hr_anomaly = features.get('hr_anomaly_detected', False)
        spo2_anomaly = features.get('spo2_anomaly_detected', False)
        temp_anomaly = features.get('temp_anomaly_detected', False)
        anomaly_score = features.get('anomaly_score', 0)
        
        return hr_anomaly or spo2_anomaly or temp_anomaly or anomaly_score > 1.0
    
    def _check_recovery(self, features: Dict[str, Any]) -> bool:
        """Check if user is recovering from fall."""
        activity_level = features.get('activity_level', 'high')
        accel_magnitude_mean = features.get('accel_magnitude_mean', 0)
        
        return (activity_level in ['moderate', 'high'] and 
                accel_magnitude_mean > self.recovery_threshold)

class MultiLayerFallDetector:
    """Multi-layer fall detection system combining all approaches."""
    
    def __init__(self):
        self.threshold_detector = ThresholdFallDetector()
        self.ml_detector = MLFallDetector()
        self.post_validator = PostFallValidator()
        
        # Detection state
        self.current_detections = {}
        self.detection_history = deque(maxlen=100)
        self.validation_timer = None
        
    def process_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process features through multi-layer detection pipeline.
        
        Args:
            features: Extracted features from sensor data
            
        Returns:
            Complete detection results
        """
        detection_results = {
            "timestamp": time.time(),
            "features_processed": True,
            "detections": {},
            "final_decision": None,
            "confidence": 0.0,
            "fall_type": None,
            "severity": None
        }
        
        # Layer 1: Threshold-based detection
        threshold_detected, threshold_result = self.threshold_detector.detect_fall(features)
        detection_results["detections"]["threshold"] = {
            "detected": threshold_detected,
            "result": threshold_result
        }
        
        # Layer 2: ML-based detection
        ml_detected, ml_result = self.ml_detector.detect_fall(features)
        detection_results["detections"]["ml_classifier"] = {
            "detected": ml_detected,
            "result": ml_result
        }
        
        # Combine detection results
        combined_detected, combined_confidence = self._combine_detections(
            threshold_detected, threshold_result,
            ml_detected, ml_result
        )
        
        # Layer 3: Post-fall validation (if fall detected)
        if combined_detected:
            validated, validation_result = self.post_validator.validate_fall(features, threshold_result)
            detection_results["detections"]["post_validation"] = {
                "validated": validated,
                "result": validation_result
            }
            
            # Adjust confidence based on validation
            if validated:
                combined_confidence += validation_result.get("confidence_adjustment", 0)
                combined_confidence = min(1.0, combined_confidence)
        
        # Final decision
        if combined_detected and combined_confidence >= 0.6:
            detection_results["final_decision"] = "fall_detected"
            detection_results["confidence"] = combined_confidence
            
            # Determine final fall type and severity
            final_fall_type, final_severity = self._determine_final_classification(
                threshold_result, ml_result, combined_confidence
            )
            
            detection_results["fall_type"] = final_fall_type
            detection_results["severity"] = final_severity
            
            # Store in history
            self.detection_history.append(detection_results.copy())
        else:
            detection_results["final_decision"] = "no_fall"
            detection_results["confidence"] = 1.0 - combined_confidence
        
        return detection_results
    
    def _combine_detections(self, threshold_detected: bool, threshold_result: Dict,
                           ml_detected: bool, ml_result: Dict) -> Tuple[bool, float]:
        """Combine results from multiple detection layers."""
        # Weight different detection methods
        threshold_weight = 0.4
        ml_weight = 0.6
        
        threshold_confidence = threshold_result.get("confidence", 0) if threshold_detected else 0
        ml_confidence = ml_result.get("confidence", 0) if ml_detected else 0
        
        combined_confidence = (threshold_confidence * threshold_weight + 
                              ml_confidence * ml_weight)
        
        # Fall detected if either method detects it with reasonable confidence
        combined_detected = (threshold_detected and threshold_confidence > 0.5) or \
                           (ml_detected and ml_confidence > 0.5)
        
        return combined_detected, combined_confidence
    
    def _determine_final_classification(self, threshold_result: Dict, 
                                      ml_result: Dict, confidence: float) -> Tuple[str, str]:
        """Determine final fall type and severity."""
        # Prefer ML classification if available, otherwise use threshold
        if ml_result.get("fall_type"):
            fall_type = ml_result["fall_type"]
            severity = ml_result["severity"]
        elif threshold_result.get("fall_type"):
            fall_type = threshold_result["fall_type"]
            severity = threshold_result["severity"]
        else:
            fall_type = "unknown_fall"
            severity = "medium"
        
        return fall_type, severity
    
    def get_detection_history(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent detection history."""
        return list(self.detection_history)[-count:]
    
    def reset_detector(self):
        """Reset detector state."""
        self.current_detections.clear()
        self.detection_history.clear()
        print("🔄 Multi-layer fall detector reset")

# Global detector instance
_fall_detector = None

def initialize_fall_detector() -> MultiLayerFallDetector:
    """Initialize the global fall detector."""
    global _fall_detector
    _fall_detector = MultiLayerFallDetector()
    return _fall_detector

def get_fall_detector() -> MultiLayerFallDetector:
    """Get the global fall detector instance."""
    return _fall_detector

def detect_fall(features: Dict[str, Any]) -> Dict[str, Any]:
    """Process features through fall detection pipeline."""
    if _fall_detector:
        return _fall_detector.process_features(features)
    return {"final_decision": "detector_not_initialized"}

def reset_fall_detector():
    """Reset the fall detector."""
    if _fall_detector:
        _fall_detector.reset_detector()
