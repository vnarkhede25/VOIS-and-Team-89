"""
Centralized Decision Engine for Elderly Monitoring System

Combines ML predictions and rule-based logic to make explainable decisions
about fall detection, health alerts, and emergency responses.

Features:
- Explainable AI decisions
- Multi-factor risk assessment
- Adaptive threshold adjustment
- Context-aware decision making
- Decision logging and audit trail
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from enum import Enum
import time
from datetime import datetime, timedelta
from collections import deque
import json

class DecisionType(Enum):
    """Types of decisions made by the engine."""
    FALL_DETECTED = "fall_detected"
    PRE_FALL_WARNING = "pre_fall_warning"
    HEALTH_ALERT = "health_alert"
    EMERGENCY_RESPONSE = "emergency_response"
    FALSE_POSITIVE = "false_positive"
    NO_ACTION = "no_action"

class UrgencyLevel(Enum):
    """Urgency levels for decisions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DecisionRule:
    """Individual decision rule with explainable logic."""
    
    def __init__(self, name: str, condition: str, weight: float, explanation: str):
        self.name = name
        self.condition = condition
        self.weight = weight
        self.explanation = explanation
        self.last_triggered = False
        self.trigger_count = 0
        
    def evaluate(self, features: Dict[str, Any]) -> Tuple[bool, float, str]:
        """
        Evaluate the rule against current features.
        
        Returns:
            Tuple of (triggered, confidence, reasoning)
        """
        triggered = False
        confidence = 0.0
        reasoning = ""
        
        try:
            # Simple rule evaluation (in production, use more sophisticated rule engine)
            if "accel_magnitude_max" in self.condition:
                threshold = float(self.condition.split(">")[-1].strip())
                accel_max = features.get('accel_magnitude_max', 0)
                triggered = accel_max > threshold
                confidence = min(1.0, accel_max / threshold)
                reasoning = f"Acceleration magnitude {accel_max:.2f} exceeds threshold {threshold}"
                
            elif "jerk_magnitude_max" in self.condition:
                threshold = float(self.condition.split(">")[-1].strip())
                jerk_max = features.get('jerk_magnitude_max', 0)
                triggered = jerk_max > threshold
                confidence = min(1.0, jerk_max / threshold)
                reasoning = f"Jerk magnitude {jerk_max:.2f} exceeds threshold {threshold}"
                
            elif "anomaly_score" in self.condition:
                threshold = float(self.condition.split(">")[-1].strip())
                anomaly_score = features.get('anomaly_score', 0)
                triggered = anomaly_score > threshold
                confidence = min(1.0, anomaly_score / threshold)
                reasoning = f"Anomaly score {anomaly_score:.2f} exceeds threshold {threshold}"
                
            elif "hr_anomaly_detected" in self.condition:
                hr_anomaly = features.get('hr_anomaly_detected', False)
                triggered = hr_anomaly
                confidence = 0.8 if hr_anomaly else 0.0
                reasoning = "Heart rate anomaly detected" if hr_anomaly else "No heart rate anomaly"
                
            elif "spo2_anomaly_detected" in self.condition:
                spo2_anomaly = features.get('spo2_anomaly_detected', False)
                triggered = spo2_anomaly
                confidence = 0.8 if spo2_anomaly else 0.0
                reasoning = "SpO₂ anomaly detected" if spo2_anomaly else "No SpO₂ anomaly"
                
            elif "inactivity_duration" in self.condition:
                threshold = float(self.condition.split(">")[-1].strip())
                inactivity = features.get('inactivity_duration', 0)
                triggered = inactivity > threshold
                confidence = min(1.0, inactivity / threshold)
                reasoning = f"Inactivity duration {inactivity:.1f}s exceeds threshold {threshold}s"
                
        except Exception as e:
            reasoning = f"Rule evaluation error: {str(e)}"
            confidence = 0.0
            triggered = False
        
        if triggered:
            self.trigger_count += 1
            self.last_triggered = True
        else:
            self.last_triggered = False
        
        return triggered, confidence, reasoning

class DecisionEngine:
    """Centralized decision engine combining ML and rule-based approaches."""
    
    def __init__(self):
        # Decision rules
        self.rules = self._initialize_rules()
        
        # Decision history
        self.decision_history = deque(maxlen=1000)
        self.rule_performance = {}
        
        # Adaptive thresholds
        self.false_positive_rate = 0.0
        self.true_positive_rate = 0.0
        self.threshold_adjustment_factor = 1.0
        
        # Context tracking
        self.current_context = {}
        self.recent_decisions = deque(maxlen=10)
        
        # Decision weights
        self.ml_weight = 0.6
        self.rule_weight = 0.4
        
    def _initialize_rules(self) -> List[DecisionRule]:
        """Initialize decision rules."""
        rules = [
            # Fall detection rules
            DecisionRule(
                name="high_impact_fall",
                condition="accel_magnitude_max > 2.5",
                weight=0.25,
                explanation="High acceleration impact indicates potential fall"
            ),
            DecisionRule(
                name="sudden_jerk",
                condition="jerk_magnitude_max > 15.0",
                weight=0.20,
                explanation="Sudden jerk motion indicates fall or stumble"
            ),
            DecisionRule(
                name="prolonged_inactivity",
                condition="inactivity_duration > 5.0",
                weight=0.15,
                explanation="Prolonged inactivity after motion suggests fall"
            ),
            DecisionRule(
                name="orientation_change",
                condition="orientation_stability > 30",
                weight=0.10,
                explanation="Significant orientation change indicates fall"
            ),
            
            # Health anomaly rules
            DecisionRule(
                name="heart_rate_anomaly",
                condition="hr_anomaly_detected == True",
                weight=0.10,
                explanation="Heart rate anomaly indicates physiological stress"
            ),
            DecisionRule(
                name="spo2_anomaly",
                condition="spo2_anomaly_detected == True",
                weight=0.10,
                explanation="Blood oxygen anomaly indicates respiratory distress"
            ),
            DecisionRule(
                name="high_anomaly_score",
                condition="anomaly_score > 1.5",
                weight=0.10,
                explanation="High overall anomaly score indicates health issue"
            )
        ]
        
        return rules
    
    def make_decision(self, features: Dict[str, Any], ml_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a comprehensive decision based on features and ML results.
        
        Args:
            features: Extracted features from sensor data
            ml_results: Results from ML fall detection
            
        Returns:
            Complete decision with explanation and confidence
        """
        decision_start_time = time.time()
        
        # Evaluate all rules
        rule_results = self._evaluate_rules(features)
        
        # Combine with ML results
        combined_score, ml_confidence, rule_confidence = self._combine_evidence(
            ml_results, rule_results
        )
        
        # Make final decision
        decision_type, urgency = self._determine_decision_type(
            combined_score, ml_results, rule_results
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            decision_type, ml_results, rule_results, combined_score
        )
        
        # Create decision object
        decision = {
            "timestamp": decision_start_time,
            "decision_type": decision_type.value,
            "urgency_level": urgency.value,
            "confidence": combined_score,
            "ml_confidence": ml_confidence,
            "rule_confidence": rule_confidence,
            "explanation": explanation,
            "triggered_rules": [r.name for r in rule_results if r.last_triggered],
            "rule_details": [
                {
                    "name": r.name,
                    "triggered": r.last_triggered,
                    "confidence": r.confidence if hasattr(r, 'confidence') else 0.0,
                    "reasoning": r.reasoning if hasattr(r, 'reasoning') else ""
                }
                for r in rule_results
            ],
            "ml_results": ml_results,
            "features_summary": self._summarize_features(features),
            "context": self.current_context.copy(),
            "processing_time": time.time() - decision_start_time
        }
        
        # Store decision
        self.decision_history.append(decision.copy())
        self.recent_decisions.append(decision_type)
        
        # Update context
        self._update_context(decision)
        
        return decision
    
    def _evaluate_rules(self, features: Dict[str, Any]) -> List[DecisionRule]:
        """Evaluate all decision rules."""
        rule_results = []
        
        for rule in self.rules:
            triggered, confidence, reasoning = rule.evaluate(features)
            rule.confidence = confidence
            rule.reasoning = reasoning
            rule_results.append(rule)
        
        return rule_results
    
    def _combine_evidence(self, ml_results: Dict[str, Any], 
                         rule_results: List[DecisionRule]) -> Tuple[float, float, float]:
        """Combine ML and rule-based evidence."""
        # ML confidence
        ml_confidence = ml_results.get("confidence", 0.0)
        
        # Rule-based confidence
        triggered_rules = [r for r in rule_results if r.last_triggered]
        rule_confidence = 0.0
        
        if triggered_rules:
            # Weighted sum of triggered rule confidences
            rule_confidence = sum(
                r.confidence * r.weight for r in triggered_rules
            ) / sum(r.weight for r in triggered_rules)
        
        # Combined score with adaptive weights
        combined_score = (ml_confidence * self.ml_weight + 
                         rule_confidence * self.rule_weight) * self.threshold_adjustment_factor
        
        return min(1.0, combined_score), ml_confidence, rule_confidence
    
    def _determine_decision_type(self, combined_score: float, 
                               ml_results: Dict[str, Any], 
                               rule_results: List[DecisionRule]) -> Tuple[DecisionType, UrgencyLevel]:
        """Determine final decision type and urgency."""
        
        # Check for fall detection
        ml_fall_detected = ml_results.get("final_decision") == "fall_detected"
        high_impact_rules = any(r.name in ["high_impact_fall", "sudden_jerk"] and r.last_triggered 
                               for r in rule_results)
        
        if ml_fall_detected or high_impact_rules:
            if combined_score >= 0.8:
                return DecisionType.EMERGENCY_RESPONSE, UrgencyLevel.CRITICAL
            elif combined_score >= 0.6:
                return DecisionType.FALL_DETECTED, UrgencyLevel.HIGH
            else:
                return DecisionType.PRE_FALL_WARNING, UrgencyLevel.MEDIUM
        
        # Check for health anomalies
        health_anomaly_rules = any(r.name in ["heart_rate_anomaly", "spo2_anomaly", "high_anomaly_score"] 
                                 and r.last_triggered for r in rule_results)
        
        if health_anomaly_rules:
            if combined_score >= 0.7:
                return DecisionType.HEALTH_ALERT, UrgencyLevel.MEDIUM
            else:
                return DecisionType.HEALTH_ALERT, UrgencyLevel.LOW
        
        # Check for pre-fall indicators
        pre_fall_rules = any(r.name in ["prolonged_inactivity", "orientation_change"] 
                            and r.last_triggered for r in rule_results)
        
        if pre_fall_rules and combined_score >= 0.4:
            return DecisionType.PRE_FALL_WARNING, UrgencyLevel.LOW
        
        # No significant indicators
        return DecisionType.NO_ACTION, UrgencyLevel.LOW
    
    def _generate_explanation(self, decision_type: DecisionType, 
                             ml_results: Dict[str, Any], 
                             rule_results: List[DecisionRule], 
                             combined_score: float) -> str:
        """Generate human-readable explanation for the decision."""
        
        explanation_parts = []
        
        # Main decision statement
        if decision_type == DecisionType.EMERGENCY_RESPONSE:
            explanation_parts.append("EMERGENCY: Fall detected with high confidence")
        elif decision_type == DecisionType.FALL_DETECTED:
            explanation_parts.append("Fall detected with moderate-high confidence")
        elif decision_type == DecisionType.PRE_FALL_WARNING:
            explanation_parts.append("Pre-fall warning: Instability detected")
        elif decision_type == DecisionType.HEALTH_ALERT:
            explanation_parts.append("Health anomaly detected")
        else:
            explanation_parts.append("No significant issues detected")
        
        # ML contribution
        ml_confidence = ml_results.get("confidence", 0.0)
        if ml_confidence > 0.5:
            explanation_parts.append(f"ML model indicates {ml_confidence:.1%} confidence")
        
        # Rule contributions
        triggered_rules = [r for r in rule_results if r.last_triggered]
        if triggered_rules:
            rule_names = [r.name.replace("_", " ").title() for r in triggered_rules[:3]]
            explanation_parts.append(f"Rules triggered: {', '.join(rule_names)}")
        
        # Overall confidence
        explanation_parts.append(f"Overall confidence: {combined_score:.1%}")
        
        return ". ".join(explanation_parts)
    
    def _summarize_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of key features for logging."""
        return {
            "accel_magnitude_max": features.get('accel_magnitude_max', 0),
            "jerk_magnitude_max": features.get('jerk_magnitude_max', 0),
            "anomaly_score": features.get('anomaly_score', 0),
            "inactivity_duration": features.get('inactivity_duration', 0),
            "hr_anomaly": features.get('hr_anomaly_detected', False),
            "spo2_anomaly": features.get('spo2_anomaly_detected', False),
            "activity_level": features.get('activity_level', 'unknown')
        }
    
    def _update_context(self, decision: Dict[str, Any]):
        """Update decision context based on current decision."""
        self.current_context["last_decision_time"] = decision["timestamp"]
        self.current_context["last_decision_type"] = decision["decision_type"]
        self.current_context["recent_urgency"] = decision["urgency_level"]
        
        # Update performance metrics
        if decision["decision_type"] in [DecisionType.FALL_DETECTED.value, 
                                         DecisionType.EMERGENCY_RESPONSE.value]:
            self.current_context["fall_alerts_count"] = self.current_context.get("fall_alerts_count", 0) + 1
        
        # Adjust thresholds based on recent decisions
        self._adjust_thresholds()
    
    def _adjust_thresholds(self):
        """Adaptively adjust thresholds based on performance."""
        # Simple adaptive threshold adjustment
        recent_decisions = list(self.recent_decisions)[-5:]
        
        if len(recent_decisions) >= 3:
            # If too many false positives, increase threshold
            false_positive_count = sum(1 for d in recent_decisions 
                                      if d == DecisionType.FALSE_POSITIVE)
            
            if false_positive_count >= 2:
                self.threshold_adjustment_factor *= 1.1  # Increase threshold
                self.threshold_adjustment_factor = min(2.0, self.threshold_adjustment_factor)
            
            # If good performance, slightly decrease threshold
            elif false_positive_count == 0:
                self.threshold_adjustment_factor *= 0.95  # Decrease threshold
                self.threshold_adjustment_factor = max(0.5, self.threshold_adjustment_factor)
    
    def get_decision_history(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent decision history."""
        return list(self.decision_history)[-count:]
    
    def get_rule_performance(self) -> Dict[str, Any]:
        """Get performance statistics for rules."""
        performance = {}
        
        for rule in self.rules:
            performance[rule.name] = {
                "trigger_count": rule.trigger_count,
                "weight": rule.weight,
                "explanation": rule.explanation
            }
        
        return performance
    
    def update_feedback(self, decision_id: str, correct: bool, actual_outcome: str = None):
        """Update decision engine with feedback for learning."""
        # Find the decision
        for decision in self.decision_history:
            if str(decision["timestamp"]) == decision_id:
                decision["feedback"] = {
                    "correct": correct,
                    "actual_outcome": actual_outcome,
                    "feedback_time": time.time()
                }
                
                # Update performance metrics
                if correct:
                    if decision["decision_type"] in [DecisionType.FALL_DETECTED.value, 
                                                     DecisionType.EMERGENCY_RESPONSE.value]:
                        self.true_positive_rate += 0.01
                else:
                    if decision["decision_type"] in [DecisionType.FALL_DETECTED.value, 
                                                     DecisionType.EMERGENCY_RESPONSE.value]:
                        self.false_positive_rate += 0.01
                
                break
    
    def reset_engine(self):
        """Reset decision engine state."""
        self.decision_history.clear()
        self.recent_decisions.clear()
        self.current_context.clear()
        self.threshold_adjustment_factor = 1.0
        
        # Reset rule statistics
        for rule in self.rules:
            rule.trigger_count = 0
            rule.last_triggered = False
        
        print("🔄 Decision engine reset")

# Global decision engine instance
_decision_engine = None

def initialize_decision_engine() -> DecisionEngine:
    """Initialize the global decision engine."""
    global _decision_engine
    _decision_engine = DecisionEngine()
    return _decision_engine

def get_decision_engine() -> DecisionEngine:
    """Get the global decision engine instance."""
    return _decision_engine

def make_decision(features: Dict[str, Any], ml_results: Dict[str, Any]) -> Dict[str, Any]:
    """Make a decision using the global engine."""
    if _decision_engine:
        return _decision_engine.make_decision(features, ml_results)
    return {"decision_type": "engine_not_initialized"}

def update_decision_feedback(decision_id: str, correct: bool, actual_outcome: str = None):
    """Update decision feedback for learning."""
    if _decision_engine:
        _decision_engine.update_feedback(decision_id, correct, actual_outcome)

def reset_decision_engine():
    """Reset the decision engine."""
    if _decision_engine:
        _decision_engine.reset_engine()
