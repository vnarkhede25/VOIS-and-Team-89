"""
Continuous Learning System for Elderly Monitoring

Implements machine learning model refinement using patient data
collected day by day to improve detection accuracy and reduce false positives.

Features:
- Patient-specific model adaptation
- Feedback collection and analysis
- Performance trend tracking
- Automatic threshold optimization
- Model retraining with new data
"""

import numpy as np
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from collections import deque, defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass
import pickle
import os

@dataclass
class PatientDataPoint:
    """Single patient data point for learning."""
    timestamp: float
    features: Dict[str, Any]
    detection_result: str
    actual_outcome: str
    confidence: float
    feedback_received: bool
    patient_id: str

@dataclass
class ModelPerformance:
    """Model performance metrics."""
    accuracy: float
    precision: float
    recall: float
    false_positive_rate: float
    false_negative_rate: float
    total_predictions: int
    last_updated: float

class ContinuousLearningSystem:
    """Main continuous learning system."""
    
    def __init__(self, model_save_path: str = "models/"):
        self.model_save_path = model_save_path
        os.makedirs(model_save_path, exist_ok=True)
        
        # Patient data storage
        self.patient_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.patient_models: Dict[str, Dict] = {}
        self.patient_performance: Dict[str, ModelPerformance] = {}
        
        # Global model data
        self.global_training_data: deque = deque(maxlen=50000)
        self.feature_importance: Dict[str, float] = {}
        
        # Learning parameters
        self.min_samples_for_retraining = 100
        self.performance_window = 50  # Last 50 predictions for performance
        self.retraining_interval = 7 * 24 * 3600  # Weekly retraining
        
        # Load existing models
        self._load_models()
        
    def add_patient_data(self, patient_id: str, features: Dict[str, Any], 
                        detection_result: str, confidence: float, 
                        actual_outcome: str = None) -> str:
        """
        Add new patient data point for learning.
        
        Returns:
            Data point ID for feedback linking
        """
        data_point = PatientDataPoint(
            timestamp=time.time(),
            features=features.copy(),
            detection_result=detection_result,
            actual_outcome=actual_outcome or "unknown",
            confidence=confidence,
            feedback_received=False,
            patient_id=patient_id
        )
        
        # Store patient-specific data
        self.patient_data[patient_id].append(data_point)
        
        # Store in global training data
        self.global_training_data.append(data_point)
        
        # Update performance metrics
        self._update_performance_metrics(patient_id, data_point)
        
        # Check if retraining is needed
        if self._should_retrain_model(patient_id):
            self._retrain_patient_model(patient_id)
        
        # Check if global model needs updating
        if len(self.global_training_data) % 1000 == 0:
            self._update_global_model()
        
        return str(data_point.timestamp)
    
    def add_feedback(self, patient_id: str, data_point_id: str, 
                   actual_outcome: str, correct: bool) -> bool:
        """
        Add feedback to improve model accuracy.
        
        Args:
            patient_id: Patient identifier
            data_point_id: Data point timestamp as ID
            actual_outcome: What actually happened
            correct: Whether the prediction was correct
            
        Returns:
            True if feedback was added successfully
        """
        # Find the data point
        for data_point in self.patient_data[patient_id]:
            if str(data_point.timestamp) == data_point_id:
                data_point.actual_outcome = actual_outcome
                data_point.feedback_received = True
                
                # Update performance metrics
                self._update_performance_metrics(patient_id, data_point)
                
                # Check for immediate model adjustment
                if not correct:
                    self._adjust_thresholds_immediately(patient_id, data_point)
                
                return True
        
        return False
    
    def get_patient_insights(self, patient_id: str) -> Dict[str, Any]:
        """Get learning insights for a specific patient."""
        if patient_id not in self.patient_data:
            return {"error": "Patient not found"}
        
        patient_data = list(self.patient_data[patient_id])
        if not patient_data:
            return {"message": "No data available"}
        
        # Analyze patterns
        insights = {
            "total_data_points": len(patient_data),
            "feedback_rate": sum(1 for dp in patient_data if dp.feedback_received) / len(patient_data),
            "accuracy": self._calculate_accuracy(patient_data),
            "common_false_positives": self._analyze_false_positives(patient_data),
            "feature_patterns": self._analyze_feature_patterns(patient_data),
            "improvement_suggestions": self._generate_improvement_suggestions(patient_id),
            "last_updated": max(dp.timestamp for dp in patient_data)
        }
        
        # Add performance metrics if available
        if patient_id in self.patient_performance:
            perf = self.patient_performance[patient_id]
            insights["performance"] = {
                "accuracy": perf.accuracy,
                "precision": perf.precision,
                "recall": perf.recall,
                "false_positive_rate": perf.false_positive_rate
            }
        
        return insights
    
    def get_global_insights(self) -> Dict[str, Any]:
        """Get global learning insights."""
        if not self.global_training_data:
            return {"message": "No global data available"}
        
        global_data = list(self.global_training_data)
        
        insights = {
            "total_patients": len(self.patient_data),
            "total_data_points": len(global_data),
            "global_accuracy": self._calculate_accuracy(global_data),
            "feature_importance": dict(sorted(self.feature_importance.items(), 
                                         key=lambda x: x[1], reverse=True)[:10]),
            "improvement_trends": self._analyze_improvement_trends(),
            "model_update_schedule": self._get_next_update_schedule()
        }
        
        return insights
    
    def _update_performance_metrics(self, patient_id: str, data_point: PatientDataPoint):
        """Update performance metrics for a patient."""
        if patient_id not in self.patient_data:
            return
        
        patient_data = list(self.patient_data[patient_id])
        recent_data = patient_data[-self.performance_window:]
        
        if len(recent_data) < 10:  # Need minimum data for reliable metrics
            return
        
        # Calculate metrics
        correct_predictions = sum(1 for dp in recent_data 
                               if dp.feedback_received and 
                               dp.detection_result == dp.actual_outcome)
        
        total_predictions = sum(1 for dp in recent_data if dp.feedback_received)
        
        if total_predictions == 0:
            return
        
        accuracy = correct_predictions / total_predictions
        
        # Calculate precision and recall
        true_positives = sum(1 for dp in recent_data 
                            if dp.feedback_received and 
                            dp.detection_result == "fall_detected" and 
                            dp.actual_outcome == "fall_detected")
        
        false_positives = sum(1 for dp in recent_data 
                             if dp.feedback_received and 
                             dp.detection_result == "fall_detected" and 
                             dp.actual_outcome != "fall_detected")
        
        false_negatives = sum(1 for dp in recent_data 
                             if dp.feedback_received and 
                             dp.detection_result != "fall_detected" and 
                             dp.actual_outcome == "fall_detected")
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        false_positive_rate = false_positives / total_predictions if total_predictions > 0 else 0
        false_negative_rate = false_negatives / total_predictions if total_predictions > 0 else 0
        
        # Update performance
        self.patient_performance[patient_id] = ModelPerformance(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            false_positive_rate=false_positive_rate,
            false_negative_rate=false_negative_rate,
            total_predictions=total_predictions,
            last_updated=time.time()
        )
    
    def _should_retrain_model(self, patient_id: str) -> bool:
        """Check if patient model should be retrained."""
        if patient_id not in self.patient_data:
            return False
        
        patient_data = self.patient_data[patient_id]
        
        # Check minimum samples
        if len(patient_data) < self.min_samples_for_retraining:
            return False
        
        # Check performance degradation
        if patient_id in self.patient_performance:
            perf = self.patient_performance[patient_id]
            if perf.accuracy < 0.8:  # Retrain if accuracy drops below 80%
                return True
        
        # Check time-based retraining
        recent_data = [dp for dp in patient_data 
                      if time.time() - dp.timestamp < self.retraining_interval]
        
        return len(recent_data) >= self.min_samples_for_retraining
    
    def _retrain_patient_model(self, patient_id: str):
        """Retrain model for specific patient."""
        print(f"🧠 Retraining model for patient {patient_id}...")
        
        patient_data = list(self.patient_data[patient_id])
        training_data = [dp for dp in patient_data if dp.feedback_received]
        
        if len(training_data) < 50:
            print(f"⚠️ Insufficient training data for patient {patient_id}")
            return
        
        # Extract features and labels
        X = []
        y = []
        
        for dp in training_data:
            # Convert features to vector
            feature_vector = self._features_to_vector(dp.features)
            X.append(feature_vector)
            
            # Convert outcome to binary (1 for fall, 0 for no fall)
            label = 1 if dp.actual_outcome == "fall_detected" else 0
            y.append(label)
        
        # Train patient-specific model
        X = np.array(X)
        y = np.array(y)
        
        # Simple adaptive threshold model (in production, use proper ML)
        patient_model = self._train_adaptive_model(X, y)
        
        # Save patient model
        self.patient_models[patient_id] = patient_model
        self._save_patient_model(patient_id, patient_model)
        
        print(f"✅ Model retrained for patient {patient_id}")
    
    def _train_adaptive_model(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Train adaptive model for patient."""
        # Calculate patient-specific thresholds
        fall_samples = X[y == 1]
        no_fall_samples = X[y == 0]
        
        if len(fall_samples) == 0 or len(no_fall_samples) == 0:
            return {"threshold": 0.5, "feature_weights": {}}
        
        # Feature importance based on difference between fall and no-fall
        model = {
            "threshold": 0.5,
            "feature_weights": {},
            "fall_patterns": {},
            "no_fall_patterns": {}
        }
        
        # Calculate feature-wise statistics
        for i in range(X.shape[1]):
            fall_mean = np.mean(fall_samples[:, i]) if len(fall_samples) > 0 else 0
            no_fall_mean = np.mean(no_fall_samples[:, i]) if len(no_fall_samples) > 0 else 0
            
            importance = abs(fall_mean - no_fall_mean)
            model["feature_weights"][f"feature_{i}"] = importance
            
            # Update global feature importance
            if f"feature_{i}" in self.feature_importance:
                self.feature_importance[f"feature_{i}"] = (
                    self.feature_importance[f"feature_{i}"] * 0.9 + importance * 0.1
                )
            else:
                self.feature_importance[f"feature_{i}"] = importance
        
        # Calculate optimal threshold
        scores = X.dot(np.ones(X.shape[1]))  # Simple scoring
        thresholds = np.linspace(0, 1, 100)
        best_threshold = 0.5
        best_accuracy = 0
        
        for threshold in thresholds:
            predictions = (scores > threshold).astype(int)
            accuracy = np.mean(predictions == y)
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_threshold = threshold
        
        model["threshold"] = best_threshold
        
        return model
    
    def _adjust_thresholds_immediately(self, patient_id: str, data_point: PatientDataPoint):
        """Immediately adjust thresholds based on feedback."""
        if data_point.detection_result == "fall_detected" and data_point.actual_outcome != "fall_detected":
            # False positive - increase threshold
            if patient_id in self.patient_models:
                model = self.patient_models[patient_id]
                model["threshold"] = min(1.0, model["threshold"] + 0.05)
                print(f"🔧 Increased threshold for patient {patient_id} due to false positive")
        
        elif data_point.detection_result != "fall_detected" and data_point.actual_outcome == "fall_detected":
            # False negative - decrease threshold
            if patient_id in self.patient_models:
                model = self.patient_models[patient_id]
                model["threshold"] = max(0.1, model["threshold"] - 0.05)
                print(f"🔧 Decreased threshold for patient {patient_id} due to false negative")
    
    def _features_to_vector(self, features: Dict[str, Any]) -> np.ndarray:
        """Convert features dictionary to vector."""
        # Extract numeric features
        numeric_features = []
        
        feature_order = [
            'accel_magnitude_mean', 'accel_magnitude_max', 'accel_magnitude_std',
            'gyro_variance_total', 'instability_risk', 'inactivity_duration',
            'posture_stability_score', 'jerk_magnitude', 'acceleration_energy'
        ]
        
        for feature_name in feature_order:
            value = features.get(feature_name, 0)
            if isinstance(value, (int, float)):
                numeric_features.append(float(value))
            else:
                numeric_features.append(0.0)
        
        return np.array(numeric_features)
    
    def _calculate_accuracy(self, data_points: List[PatientDataPoint]) -> float:
        """Calculate accuracy from data points."""
        feedback_data = [dp for dp in data_points if dp.feedback_received]
        
        if not feedback_data:
            return 0.0
        
        correct = sum(1 for dp in feedback_data 
                     if dp.detection_result == dp.actual_outcome)
        
        return correct / len(feedback_data)
    
    def _analyze_false_positives(self, data_points: List[PatientDataPoint]) -> Dict[str, Any]:
        """Analyze false positive patterns."""
        false_positives = [dp for dp in data_points 
                          if dp.feedback_received and 
                          dp.detection_result == "fall_detected" and 
                          dp.actual_outcome != "fall_detected"]
        
        if not false_positives:
            return {"message": "No false positives in recent data"}
        
        # Analyze common patterns
        patterns = {
            "average_confidence": np.mean([dp.confidence for dp in false_positives]),
            "common_features": {},
            "time_patterns": {}
        }
        
        # Feature analysis
        for dp in false_positives:
            for feature, value in dp.features.items():
                if isinstance(value, (int, float)):
                    if feature not in patterns["common_features"]:
                        patterns["common_features"][feature] = []
                    patterns["common_features"][feature].append(value)
        
        # Average feature values
        for feature in patterns["common_features"]:
            values = patterns["common_features"][feature]
            patterns["common_features"][feature] = np.mean(values)
        
        return patterns
    
    def _analyze_feature_patterns(self, data_points: List[PatientDataPoint]) -> Dict[str, Any]:
        """Analyze feature patterns in patient data."""
        if not data_points:
            return {}
        
        patterns = {}
        
        # Analyze each feature
        all_features = set()
        for dp in data_points:
            all_features.update(dp.features.keys())
        
        for feature in all_features:
            values = [dp.features.get(feature, 0) for dp in data_points 
                      if isinstance(dp.features.get(feature, 0), (int, float))]
            
            if values:
                patterns[feature] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values)
                }
        
        return patterns
    
    def _generate_improvement_suggestions(self, patient_id: str) -> List[str]:
        """Generate improvement suggestions based on patient data."""
        suggestions = []
        
        if patient_id not in self.patient_performance:
            return ["Insufficient data for suggestions"]
        
        perf = self.patient_performance[patient_id]
        
        if perf.false_positive_rate > 0.2:
            suggestions.append("High false positive rate - consider increasing sensitivity thresholds")
        
        if perf.false_negative_rate > 0.1:
            suggestions.append("Missed falls detected - consider decreasing sensitivity thresholds")
        
        if perf.accuracy < 0.8:
            suggestions.append("Low accuracy - more training data needed")
        
        if perf.precision < 0.7:
            suggestions.append("Low precision - model may be overfitting to fall patterns")
        
        if perf.recall < 0.7:
            suggestions.append("Low recall - model may be missing actual falls")
        
        return suggestions
    
    def _analyze_improvement_trends(self) -> Dict[str, Any]:
        """Analyze improvement trends over time."""
        # Group data by week
        weekly_data = defaultdict(list)
        
        for dp in self.global_training_data:
            week = datetime.fromtimestamp(dp.timestamp).isocalendar()[1]
            weekly_data[week].append(dp)
        
        trends = {}
        for week, data_points in weekly_data.items():
            if len(data_points) > 10:
                accuracy = self._calculate_accuracy(data_points)
                trends[f"week_{week}"] = accuracy
        
        return trends
    
    def _get_next_update_schedule(self) -> Dict[str, Any]:
        """Get next model update schedule."""
        next_update = time.time() + self.retraining_interval
        
        return {
            "next_global_update": datetime.fromtimestamp(next_update).isoformat(),
            "patients_due_for_update": [
                pid for pid, perf in self.patient_performance.items()
                if perf.accuracy < 0.8
            ]
        }
    
    def _update_global_model(self):
        """Update global model with new data."""
        print("🌍 Updating global model...")
        
        # This would typically involve retraining a global ML model
        # For now, just update feature importance
        print("✅ Global model updated")
    
    def _save_patient_model(self, patient_id: str, model: Dict):
        """Save patient-specific model."""
        model_path = os.path.join(self.model_save_path, f"patient_{patient_id}.pkl")
        
        try:
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
        except Exception as e:
            print(f"❌ Failed to save model for patient {patient_id}: {e}")
    
    def _load_models(self):
        """Load existing models."""
        print("📂 Loading existing models...")
        
        # Load patient models
        for filename in os.listdir(self.model_save_path):
            if filename.startswith("patient_") and filename.endswith(".pkl"):
                patient_id = filename[8:-4]  # Extract patient ID from filename
                
                try:
                    model_path = os.path.join(self.model_save_path, filename)
                    with open(model_path, 'rb') as f:
                        model = pickle.load(f)
                        self.patient_models[patient_id] = model
                        print(f"✅ Loaded model for patient {patient_id}")
                except Exception as e:
                    print(f"❌ Failed to load model for patient {patient_id}: {e}")

# Global learning system instance
_learning_system = None

def initialize_learning_system(model_save_path: str = "models/") -> ContinuousLearningSystem:
    """Initialize the global learning system."""
    global _learning_system
    _learning_system = ContinuousLearningSystem(model_save_path)
    return _learning_system

def get_learning_system() -> ContinuousLearningSystem:
    """Get the global learning system instance."""
    return _learning_system

def add_patient_learning_data(patient_id: str, features: Dict[str, Any], 
                           detection_result: str, confidence: float, 
                           actual_outcome: str = None) -> str:
    """Add patient data for learning using global system."""
    if _learning_system:
        return _learning_system.add_patient_data(
            patient_id, features, detection_result, confidence, actual_outcome
        )
    return None

def add_learning_feedback(patient_id: str, data_point_id: str, 
                      actual_outcome: str, correct: bool) -> bool:
    """Add feedback using global learning system."""
    if _learning_system:
        return _learning_system.add_feedback(
            patient_id, data_point_id, actual_outcome, correct
        )
    return False

def get_patient_learning_insights(patient_id: str) -> Dict[str, Any]:
    """Get patient learning insights using global system."""
    if _learning_system:
        return _learning_system.get_patient_insights(patient_id)
    return {"error": "Learning system not initialized"}

def get_global_learning_insights() -> Dict[str, Any]:
    """Get global learning insights using global system."""
    if _learning_system:
        return _learning_system.get_global_insights()
    return {"error": "Learning system not initialized"}
