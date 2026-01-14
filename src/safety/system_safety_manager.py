"""
System States and Safety Logic Manager

Implements comprehensive safety logic, alert cooldowns, false positive suppression,
multi-step confirmation logic, recovery after fall, and battery-aware alert throttling.
"""

import time
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import json

class SafetyState(Enum):
    """System safety states."""
    NORMAL = "NORMAL"
    ALERT_PENDING = "ALERT_PENDING"
    ALERT_CONFIRMED = "ALERT_CONFIRMED"
    EMERGENCY_ACTIVE = "EMERGENCY_ACTIVE"
    RECOVERY_MODE = "RECOVERY_MODE"
    MAINTENANCE = "MAINTENANCE"
    BATTERY_SAVE = "BATTERY_SAVE"

class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"

@dataclass
class SafetyRule:
    """Safety rule configuration."""
    name: str
    condition: str
    severity: AlertSeverity
    cooldown_seconds: int
    confirmation_required: bool
    auto_escalate: bool
    battery_threshold: float  # Minimum battery level to trigger
    max_false_alarms: int
    suppression_window: int  # Seconds to suppress similar alerts

@dataclass
class AlertEvent:
    """Alert event data."""
    id: str
    type: str
    severity: AlertSeverity
    timestamp: datetime
    confidence: float
    details: Dict[str, Any]
    confirmed: bool = False
    acknowledged: bool = False
    resolved: bool = False
    false_positive: bool = False

class SystemStateManager:
    """Manages system states and safety logic."""
    
    def __init__(self):
        self.current_state = SafetyState.NORMAL
        self.state_start_time = time.time()
        self.active_alerts: Dict[str, AlertEvent] = {}
        self.alert_history: List[AlertEvent] = []
        self.safety_rules: Dict[str, SafetyRule] = {}
        self.cooldown_timers: Dict[str, float] = {}
        self.suppression_windows: Dict[str, List[datetime]] = {}
        self.false_positive_counts: Dict[str, int] = {}
        
        # Safety thresholds
        self.battery_thresholds = {
            'normal': 50.0,
            'reduced': 20.0,
            'critical': 10.0
        }
        
        # State transition rules
        self.state_transitions = {
            SafetyState.NORMAL: [
                SafetyState.ALERT_PENDING,
                SafetyState.BATTERY_SAVE,
                SafetyState.MAINTENANCE
            ],
            SafetyState.ALERT_PENDING: [
                SafetyState.NORMAL,
                SafetyState.ALERT_CONFIRMED,
                SafetyState.EMERGENCY_ACTIVE
            ],
            SafetyState.ALERT_CONFIRMED: [
                SafetyState.NORMAL,
                SafetyState.RECOVERY_MODE,
                SafetyState.EMERGENCY_ACTIVE
            ],
            SafetyState.EMERGENCY_ACTIVE: [
                SafetyState.RECOVERY_MODE,
                SafetyState.NORMAL
            ],
            SafetyState.RECOVERY_MODE: [
                SafetyState.NORMAL,
                SafetyState.ALERT_PENDING
            ],
            SafetyState.MAINTENANCE: [
                SafetyState.NORMAL
            ],
            SafetyState.BATTERY_SAVE: [
                SafetyState.NORMAL,
                SafetyState.MAINTENANCE
            ]
        }
        
        # Callbacks for state changes and alerts
        self.state_change_callbacks: List[Callable] = []
        self.alert_callbacks: List[Callable] = []
        
        # Initialize safety rules
        self._initialize_safety_rules()
        
        # Background monitoring thread
        self.monitoring_thread = None
        self.is_monitoring = False
        
    def _initialize_safety_rules(self):
        """Initialize default safety rules."""
        rules = {
            'fall_detection': SafetyRule(
                name='Fall Detection',
                condition='acceleration_magnitude > 15.0 and confidence > 0.7',
                severity=AlertSeverity.EMERGENCY,
                cooldown_seconds=30,
                confirmation_required=False,
                auto_escalate=True,
                battery_threshold=10.0,
                max_false_alarms=3,
                suppression_window=10
            ),
            'panic_button': SafetyRule(
                name='Panic Button',
                condition='panic_pressed == True',
                severity=AlertSeverity.EMERGENCY,
                cooldown_seconds=10,
                confirmation_required=False,
                auto_escalate=True,
                battery_threshold=5.0,
                max_false_alarms=0,
                suppression_window=5
            ),
            'health_anomaly': SafetyRule(
                name='Health Anomaly',
                condition='heart_rate_out_of_range or temperature_out_of_range or spo2_low',
                severity=AlertSeverity.HIGH,
                cooldown_seconds=60,
                confirmation_required=True,
                auto_escalate=False,
                battery_threshold=20.0,
                max_false_alarms=5,
                suppression_window=30
            ),
            'device_removed': SafetyRule(
                name='Device Removed',
                condition='is_worn == False',
                severity=AlertSeverity.MEDIUM,
                cooldown_seconds=120,
                confirmation_required=True,
                auto_escalate=False,
                battery_threshold=15.0,
                max_false_alarms=10,
                suppression_window=60
            ),
            'low_battery': SafetyRule(
                name='Low Battery',
                condition='battery_level < 20',
                severity=AlertSeverity.MEDIUM,
                cooldown_seconds=300,
                confirmation_required=False,
                auto_escalate=True,
                battery_threshold=0.0,
                max_false_alarms=0,
                suppression_window=300
            ),
            'no_movement': SafetyRule(
                name='No Movement',
                condition='no_movement_duration > 300',
                severity=AlertSeverity.HIGH,
                cooldown_seconds=180,
                confirmation_required=True,
                auto_escalate=True,
                battery_threshold=15.0,
                max_false_alarms=3,
                suppression_window=120
            ),
            'connection_lost': SafetyRule(
                name='Connection Lost',
                condition='device_connected == False',
                severity=AlertSeverity.MEDIUM,
                cooldown_seconds=60,
                confirmation_required=False,
                auto_escalate=False,
                battery_threshold=10.0,
                max_false_alarms=5,
                suppression_window=30
            )
        }
        
        self.safety_rules = rules
    
    def add_state_change_callback(self, callback: Callable):
        """Add callback for state changes."""
        self.state_change_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable):
        """Add callback for alert events."""
        self.alert_callbacks.append(callback)
    
    def _notify_state_change(self, old_state: SafetyState, new_state: SafetyState):
        """Notify callbacks of state change."""
        for callback in self.state_change_callbacks:
            try:
                callback({
                    'old_state': old_state.value,
                    'new_state': new_state.value,
                    'timestamp': datetime.now().isoformat(),
                    'reason': self._get_state_change_reason(old_state, new_state)
                })
            except Exception as e:
                print(f"State change callback error: {e}")
    
    def _notify_alert(self, alert_event: AlertEvent):
        """Notify callbacks of alert event."""
        for callback in self.alert_callbacks:
            try:
                callback(alert_event.__dict__)
            except Exception as e:
                print(f"Alert callback error: {e}")
    
    def _get_state_change_reason(self, old_state: SafetyState, new_state: SafetyState) -> str:
        """Get reason for state change."""
        reasons = {
            (SafetyState.NORMAL, SafetyState.ALERT_PENDING): "Alert detected, awaiting confirmation",
            (SafetyState.ALERT_PENDING, SafetyState.ALERT_CONFIRMED): "Alert confirmed by system or user",
            (SafetyState.ALERT_CONFIRMED, SafetyState.EMERGENCY_ACTIVE): "Emergency conditions met",
            (SafetyState.EMERGENCY_ACTIVE, SafetyState.RECOVERY_MODE): "Emergency resolved, entering recovery",
            (SafetyState.RECOVERY_MODE, SafetyState.NORMAL): "Recovery completed",
            (SafetyState.NORMAL, SafetyState.BATTERY_SAVE): "Low battery detected",
            (SafetyState.BATTERY_SAVE, SafetyState.NORMAL): "Battery level restored"
        }
        return reasons.get((old_state, new_state), "System state transition")
    
    def can_transition_to(self, new_state: SafetyState) -> bool:
        """Check if transition to new state is allowed."""
        return new_state in self.state_transitions.get(self.current_state, [])
    
    def transition_to_state(self, new_state: SafetyState, reason: str = "") -> bool:
        """Transition to new state if allowed."""
        if not self.can_transition_to(new_state):
            print(f"Cannot transition from {self.current_state.value} to {new_state.value}")
            return False
        
        old_state = self.current_state
        self.current_state = new_state
        self.state_start_time = time.time()
        
        print(f"State transition: {old_state.value} → {new_state.value}")
        if reason:
            print(f"Reason: {reason}")
        
        self._notify_state_change(old_state, new_state)
        return True
    
    def is_in_cooldown(self, alert_type: str) -> bool:
        """Check if alert type is in cooldown period."""
        if alert_type not in self.cooldown_timers:
            return False
        
        elapsed = time.time() - self.cooldown_timers[alert_type]
        rule = self.safety_rules.get(alert_type)
        
        if rule:
            return elapsed < rule.cooldown_seconds
        
        return False
    
    def set_cooldown(self, alert_type: str):
        """Set cooldown for alert type."""
        self.cooldown_timers[alert_type] = time.time()
    
    def is_suppressed(self, alert_type: str) -> bool:
        """Check if alert type is currently suppressed."""
        if alert_type not in self.suppression_windows:
            return False
        
        rule = self.safety_rules.get(alert_type)
        if not rule:
            return False
        
        # Remove old suppression entries
        now = datetime.now()
        cutoff = now - timedelta(seconds=rule.suppression_window)
        
        self.suppression_windows[alert_type] = [
            timestamp for timestamp in self.suppression_windows[alert_type]
            if timestamp > cutoff
        ]
        
        # Check if still suppressed
        return len(self.suppression_windows[alert_type]) > 0
    
    def suppress_alert(self, alert_type: str):
        """Add alert type to suppression window."""
        if alert_type not in self.suppression_windows:
            self.suppression_windows[alert_type] = []
        
        self.suppression_windows[alert_type].append(datetime.now())
    
    def check_false_positive_limit(self, alert_type: str) -> bool:
        """Check if false positive limit exceeded."""
        rule = self.safety_rules.get(alert_type)
        if not rule:
            return False
        
        return self.false_positive_counts.get(alert_type, 0) >= rule.max_false_alarms
    
    def increment_false_positive(self, alert_type: str):
        """Increment false positive count."""
        self.false_positive_counts[alert_type] = self.false_positive_counts.get(alert_type, 0) + 1
        print(f"False positive count for {alert_type}: {self.false_positive_counts[alert_type]}")
    
    def check_battery_threshold(self, alert_type: str, battery_level: float) -> bool:
        """Check if battery level meets threshold for alert."""
        rule = self.safety_rules.get(alert_type)
        if not rule:
            return True
        
        return battery_level >= rule.battery_threshold
    
    def evaluate_sensor_data(self, sensor_data: Dict[str, Any]) -> List[AlertEvent]:
        """Evaluate sensor data against safety rules."""
        alerts = []
        
        for rule_name, rule in self.safety_rules.items():
            # Skip if in cooldown
            if self.is_in_cooldown(rule_name):
                continue
            
            # Skip if suppressed
            if self.is_suppressed(rule_name):
                continue
            
            # Check false positive limit
            if self.check_false_positive_limit(rule_name):
                continue
            
            # Check battery threshold
            battery_level = sensor_data.get('battery_level', 100)
            if not self.check_battery_threshold(rule_name, battery_level):
                continue
            
            # Evaluate rule condition
            if self._evaluate_rule_condition(rule.condition, sensor_data):
                alert = self._create_alert(rule_name, rule, sensor_data)
                alerts.append(alert)
                
                # Set cooldown
                self.set_cooldown(rule_name)
        
        return alerts
    
    def _evaluate_rule_condition(self, condition: str, sensor_data: Dict[str, Any]) -> bool:
        """Evaluate rule condition against sensor data."""
        try:
            # Simple condition evaluation (in production, use a proper expression parser)
            if 'acceleration_magnitude > 15.0' in condition:
                acc = sensor_data.get('acceleration', {})
                magnitude = (acc.get('x', 0)**2 + acc.get('y', 0)**2 + acc.get('z', 0)**2)**0.5
                return magnitude > 15.0
            
            elif 'panic_pressed == True' in condition:
                return sensor_data.get('panic_pressed', False)
            
            elif 'is_worn == False' in condition:
                return not sensor_data.get('is_worn', True)
            
            elif 'battery_level < 20' in condition:
                return sensor_data.get('battery_level', 100) < 20
            
            elif 'device_connected == False' in condition:
                return not sensor_data.get('device_connected', True)
            
            # Health conditions
            elif 'heart_rate_out_of_range' in condition:
                hr = sensor_data.get('heart_rate', 72)
                return hr < 50 or hr > 120
            
            elif 'temperature_out_of_range' in condition:
                temp = sensor_data.get('temperature', 36.8)
                return temp < 35.5 or temp > 38.5
            
            elif 'spo2_low' in condition:
                spo2 = sensor_data.get('spo2', 98)
                return spo2 < 90
            
            # No movement condition
            elif 'no_movement_duration > 300' in condition:
                # This would need to track movement over time
                return sensor_data.get('state') == 'no_movement'
            
            return False
            
        except Exception as e:
            print(f"Error evaluating condition: {e}")
            return False
    
    def _create_alert(self, rule_name: str, rule: SafetyRule, sensor_data: Dict[str, Any]) -> AlertEvent:
        """Create alert event from rule and sensor data."""
        alert_id = f"{rule_name}_{int(time.time())}"
        
        alert = AlertEvent(
            id=alert_id,
            type=rule_name,
            severity=rule.severity,
            timestamp=datetime.now(),
            confidence=self._calculate_confidence(rule_name, sensor_data),
            details={
                'rule_name': rule.name,
                'sensor_data': sensor_data,
                'condition_met': True,
                'requires_confirmation': rule.confirmation_required,
                'auto_escalate': rule.auto_escalate
            }
        )
        
        return alert
    
    def _calculate_confidence(self, rule_name: str, sensor_data: Dict[str, Any]) -> float:
        """Calculate confidence score for alert."""
        base_confidence = 0.8
        
        # Adjust confidence based on sensor data quality
        if rule_name == 'fall_detection':
            acc = sensor_data.get('acceleration', {})
            magnitude = (acc.get('x', 0)**2 + acc.get('y', 0)**2 + acc.get('z', 0)**2)**0.5
            if magnitude > 20:
                base_confidence = 0.95
            elif magnitude > 17:
                base_confidence = 0.85
            else:
                base_confidence = 0.75
        
        elif rule_name == 'panic_button':
            base_confidence = 1.0  # Manual trigger is always confident
        
        elif rule_name == 'health_anomaly':
            # Multiple health anomalies increase confidence
            anomalies = 0
            hr = sensor_data.get('heart_rate', 72)
            temp = sensor_data.get('temperature', 36.8)
            spo2 = sensor_data.get('spo2', 98)
            
            if hr < 50 or hr > 120:
                anomalies += 1
            if temp < 35.5 or temp > 38.5:
                anomalies += 1
            if spo2 < 90:
                anomalies += 1
            
            base_confidence = 0.6 + (anomalies * 0.15)
        
        return min(1.0, max(0.0, base_confidence))
    
    def process_alert(self, alert: AlertEvent) -> bool:
        """Process alert through safety logic."""
        # Check if we should handle this alert
        if not self._should_handle_alert(alert):
            return False
        
        # Add to active alerts
        self.active_alerts[alert.id] = alert
        self.alert_history.append(alert)
        
        # Keep history manageable
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-500:]
        
        # Update system state based on alert
        self._update_state_for_alert(alert)
        
        # Notify callbacks
        self._notify_alert(alert)
        
        # Start monitoring if not already running
        if not self.is_monitoring:
            self.start_monitoring()
        
        return True
    
    def _should_handle_alert(self, alert: AlertEvent) -> bool:
        """Determine if alert should be handled."""
        rule = self.safety_rules.get(alert.type)
        if not rule:
            return False
        
        # Check if similar alert is already active
        for active_alert in self.active_alerts.values():
            if active_alert.type == alert.type and not active_alert.resolved:
                return False
        
        return True
    
    def _update_state_for_alert(self, alert: AlertEvent):
        """Update system state based on alert."""
        if alert.severity in [AlertSeverity.EMERGENCY, AlertSeverity.CRITICAL]:
            if self.current_state in [SafetyState.NORMAL, SafetyState.ALERT_PENDING]:
                self.transition_to_state(SafetyState.EMERGENCY_ACTIVE, f"Emergency alert: {alert.type}")
        elif alert.severity == AlertSeverity.HIGH:
            if self.current_state == SafetyState.NORMAL:
                self.transition_to_state(SafetyState.ALERT_PENDING, f"High severity alert: {alert.type}")
        elif alert.severity == AlertSeverity.MEDIUM:
            if self.current_state == SafetyState.NORMAL:
                # Don't automatically transition for medium alerts
                pass
    
    def confirm_alert(self, alert_id: str, confirmed: bool = True) -> bool:
        """Confirm or reject alert."""
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.confirmed = confirmed
        
        if not confirmed:
            # Mark as false positive
            alert.false_positive = True
            self.increment_false_positive(alert.type)
            self.suppress_alert(alert.type)
        
        # Update state if confirmed
        if confirmed and self.current_state == SafetyState.ALERT_PENDING:
            self.transition_to_state(SafetyState.ALERT_CONFIRMED, f"Alert confirmed: {alert.type}")
        
        return True
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge alert."""
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.acknowledged = True
        
        return True
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve alert."""
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.resolved = True
        
        # Remove from active alerts
        del self.active_alerts[alert_id]
        
        # Update state if no more active alerts
        if not self.active_alerts and self.current_state in [SafetyState.ALERT_PENDING, SafetyState.ALERT_CONFIRMED]:
            self.transition_to_state(SafetyState.RECOVERY_MODE, "All alerts resolved")
        
        return True
    
    def start_monitoring(self):
        """Start background monitoring."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        print("Safety monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        print("Safety monitoring stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop."""
        while self.is_monitoring:
            try:
                # Check battery level and adjust state
                self._monitor_battery_level()
                
                # Check for auto-escalation
                self._check_auto_escalation()
                
                # Check recovery conditions
                self._check_recovery_conditions()
                
                # Sleep for monitoring interval
                time.sleep(10)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(5)
    
    def _monitor_battery_level(self):
        """Monitor battery level and adjust system state."""
        # This would get actual battery level from sensor data
        # For now, just check if we should enter battery save mode
        if self.current_state == SafetyState.NORMAL and len(self.active_alerts) == 0:
            # Simulate battery check - in real implementation, get from sensor data
            pass
    
    def _check_auto_escalation(self):
        """Check for auto-escalation conditions."""
        for alert in self.active_alerts.values():
            if not alert.acknowledged and not alert.resolved:
                rule = self.safety_rules.get(alert.type)
                if rule and rule.auto_escalate:
                    # Check if alert has been active for too long without acknowledgment
                    elapsed = (datetime.now() - alert.timestamp).total_seconds()
                    if elapsed > 300:  # 5 minutes
                        # Escalate to emergency
                        if self.current_state != SafetyState.EMERGENCY_ACTIVE:
                            self.transition_to_state(SafetyState.EMERGENCY_ACTIVE, f"Auto-escalated alert: {alert.type}")
    
    def _check_recovery_conditions(self):
        """Check if system can exit recovery mode."""
        if self.current_state == SafetyState.RECOVERY_MODE:
            # Check if enough time has passed in recovery
            elapsed = time.time() - self.state_start_time
            if elapsed > 300:  # 5 minutes in recovery
                if not self.active_alerts:
                    self.transition_to_state(SafetyState.NORMAL, "Recovery period completed")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            'current_state': self.current_state.value,
            'state_duration': int(time.time() - self.state_start_time),
            'active_alerts': len(self.active_alerts),
            'total_alerts': len(self.alert_history),
            'false_positive_counts': self.false_positive_counts,
            'cooldown_timers': {k: int(time.time() - v) for k, v in self.cooldown_timers.items()},
            'suppression_windows': {k: len(v) for k, v in self.suppression_windows.items()},
            'battery_thresholds': self.battery_thresholds
        }

# Global state manager instance
_state_manager = None

def initialize_state_manager() -> SystemStateManager:
    """Initialize the global state manager."""
    global _state_manager
    _state_manager = SystemStateManager()
    return _state_manager

def get_state_manager() -> Optional[SystemStateManager]:
    """Get the global state manager instance."""
    return _state_manager

def process_sensor_data_safety(sensor_data: Dict[str, Any]) -> List[AlertEvent]:
    """Process sensor data through safety logic."""
    if _state_manager:
        alerts = _state_manager.evaluate_sensor_data(sensor_data)
        for alert in alerts:
            _state_manager.process_alert(alert)
        return alerts
    return []

def confirm_alert_safety(alert_id: str, confirmed: bool = True) -> bool:
    """Confirm alert through safety logic."""
    if _state_manager:
        return _state_manager.confirm_alert(alert_id, confirmed)
    return False

def acknowledge_alert_safety(alert_id: str) -> bool:
    """Acknowledge alert through safety logic."""
    if _state_manager:
        return _state_manager.acknowledge_alert(alert_id)
    return False

def resolve_alert_safety(alert_id: str) -> bool:
    """Resolve alert through safety logic."""
    if _state_manager:
        return _state_manager.resolve_alert(alert_id)
    return False

def get_safety_status() -> Optional[Dict[str, Any]]:
    """Get safety system status."""
    if _state_manager:
        return _state_manager.get_system_status()
    return None
