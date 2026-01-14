"""
Real-time System Integration Layer

Connects sensor simulation to existing ML logic and provides real-time event detection.
Handles all system logic, alerts, and decision making without hardcoding.
"""

import asyncio
import time
import json
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensors.advanced_sensor_simulator import (
    initialize_sensor_simulator, get_sensor_simulator,
    ActivityState, SensorSimulationMode
)
from detection.feature_extraction import extract_features_from_data
from detection.multi_layer_fall_detection import detect_fall
from detection.decision_engine import make_decision
from alerts.multi_level_alert_system import send_alert, AlertType, AlertLevel

class SystemEvent(Enum):
    """System events that can be detected."""
    FALL_DETECTED = "FALL_DETECTED"
    PANIC_BUTTON = "PANIC_BUTTON"
    HEALTH_ANOMALY = "HEALTH_ANOMALY"
    DEVICE_REMOVED = "DEVICE_REMOVED"
    LOW_BATTERY = "LOW_BATTERY"
    NO_MOVEMENT = "NO_MOVEMENT"
    RECOVERY_DETECTED = "RECOVERY_DETECTED"
    FALSE_ALARM = "FALSE_ALARM"

class SystemState(Enum):
    """Overall system states."""
    NORMAL = "NORMAL"
    ALERT_ACTIVE = "ALERT_ACTIVE"
    EMERGENCY = "EMERGENCY"
    RECOVERY = "RECOVERY"
    MAINTENANCE = "MAINTENANCE"

class RealTimeSystemIntegration:
    """Real-time system integration layer."""
    
    def __init__(self):
        self.simulator = initialize_sensor_simulator("SIMULATION")
        self.current_state = SystemState.NORMAL
        self.last_alert_time = {}
        self.alert_cooldown = {
            SystemEvent.FALL_DETECTED: 30,  # 30 seconds
            SystemEvent.PANIC_BUTTON: 10,  # 10 seconds
            SystemEvent.HEALTH_ANOMALY: 60,  # 1 minute
            SystemEvent.DEVICE_REMOVED: 120,  # 2 minutes
            SystemEvent.LOW_BATTERY: 300,  # 5 minutes
            SystemEvent.NO_MOVEMENT: 180,  # 3 minutes
        }
        
        # Event callbacks
        self.event_callbacks = []
        
        # System metrics
        self.metrics = {
            'total_events': 0,
            'fall_events': 0,
            'panic_events': 0,
            'false_alarms': 0,
            'system_uptime': time.time(),
            'last_event': None,
            'active_alerts': []
        }
        
        # Sensor data history for analysis
        self.sensor_history = []
        self.max_history_size = 1000
        
        # Health thresholds
        self.health_thresholds = {
            'heart_rate_min': 50,
            'heart_rate_max': 120,
            'temperature_min': 35.5,
            'temperature_max': 38.5,
            'spo2_min': 85,
            'spo2_max': 100,
            'battery_min': 20
        }
        
        # Connect to simulator
        self.simulator.add_callback(self._process_sensor_data)
        
    def add_event_callback(self, callback: Callable):
        """Add callback for system events."""
        self.event_callbacks.append(callback)
    
    def remove_event_callback(self, callback: Callable):
        """Remove event callback."""
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)
    
    def _notify_event_callbacks(self, event_data: Dict[str, Any]):
        """Notify all callbacks of system events."""
        for callback in self.event_callbacks:
            try:
                callback(event_data)
            except Exception as e:
                print(f"Event callback error: {e}")
    
    def _is_in_cooldown(self, event: SystemEvent) -> bool:
        """Check if event is in cooldown period."""
        if event not in self.last_alert_time:
            return False
        
        elapsed = time.time() - self.last_alert_time[event]
        return elapsed < self.alert_cooldown[event]
    
    def _update_cooldown(self, event: SystemEvent):
        """Update cooldown timestamp for event."""
        self.last_alert_time[event] = time.time()
    
    def _detect_fall_event(self, sensor_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect fall events using ML logic."""
        try:
            # Extract features from sensor data
            features = extract_features_from_data(sensor_data)
            
            # Use existing ML fall detection
            fall_result = detect_fall(features)
            
            if fall_result and fall_result.get('fall_detected', False):
                confidence = fall_result.get('confidence', 0.0)
                
                # Additional validation based on activity state
                state = sensor_data.get('state', '')
                is_fall_state = any(fall_type in state for fall_type in ['fall', 'collapse'])
                
                if confidence > 0.7 and is_fall_state:
                    return {
                        'event': SystemEvent.FALL_DETECTED,
                        'confidence': confidence,
                        'timestamp': sensor_data['timestamp'],
                        'location': 'Waist Belt',
                        'action_required': True,
                        'details': {
                            'activity_state': state,
                            'acceleration': sensor_data['acceleration'],
                            'gyroscope': sensor_data['gyroscope'],
                            'ml_confidence': confidence
                        }
                    }
                elif confidence > 0.5:
                    # Low confidence - potential false alarm
                    return {
                        'event': SystemEvent.FALSE_ALARM,
                        'confidence': confidence,
                        'timestamp': sensor_data['timestamp'],
                        'location': 'Waist Belt',
                        'action_required': False,
                        'details': {
                            'activity_state': state,
                            'ml_confidence': confidence,
                            'reason': 'Low confidence detection'
                        }
                    }
        
        except Exception as e:
            print(f"Fall detection error: {e}")
        
        return None
    
    def _detect_panic_event(self, sensor_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect panic button events."""
        if sensor_data.get('panic_pressed', False):
            return {
                'event': SystemEvent.PANIC_BUTTON,
                'confidence': 1.0,
                'timestamp': sensor_data['timestamp'],
                'location': 'Waist Belt',
                'action_required': True,
                'details': {
                    'manual_trigger': True,
                    'heart_rate': sensor_data['heart_rate']
                }
            }
        return None
    
    def _detect_health_anomalies(self, sensor_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect health anomalies."""
        heart_rate = sensor_data.get('heart_rate', 0)
        temperature = sensor_data.get('temperature', 0)
        spo2 = sensor_data.get('spo2', 0)
        
        anomalies = []
        
        if heart_rate < self.health_thresholds['heart_rate_min']:
            anomalies.append(f"Low heart rate: {heart_rate}")
        elif heart_rate > self.health_thresholds['heart_rate_max']:
            anomalies.append(f"High heart rate: {heart_rate}")
        
        if temperature < self.health_thresholds['temperature_min']:
            anomalies.append(f"Low temperature: {temperature}°C")
        elif temperature > self.health_thresholds['temperature_max']:
            anomalies.append(f"High temperature: {temperature}°C")
        
        if spo2 < self.health_thresholds['spo2_min']:
            anomalies.append(f"Low SpO2: {spo2}%")
        
        if anomalies:
            return {
                'event': SystemEvent.HEALTH_ANOMALY,
                'confidence': 0.8,
                'timestamp': sensor_data['timestamp'],
                'location': 'Waist Belt',
                'action_required': len(anomalies) > 1,
                'details': {
                    'anomalies': anomalies,
                    'heart_rate': heart_rate,
                    'temperature': temperature,
                    'spo2': spo2
                }
            }
        
        return None
    
    def _detect_device_events(self, sensor_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect device-related events."""
        events = []
        
        # Device removed
        if not sensor_data.get('is_worn', True):
            events.append({
                'event': SystemEvent.DEVICE_REMOVED,
                'confidence': 0.9,
                'timestamp': sensor_data['timestamp'],
                'location': 'Waist Belt',
                'action_required': True,
                'details': {'wear_status': 'not_worn'}
            })
        
        # Low battery
        battery_level = sensor_data.get('battery_level', 100)
        if battery_level < self.health_thresholds['battery_min']:
            events.append({
                'event': SystemEvent.LOW_BATTERY,
                'confidence': 0.95,
                'timestamp': sensor_data['timestamp'],
                'location': 'Waist Belt',
                'action_required': battery_level < 10,
                'details': {'battery_level': battery_level}
            })
        
        # No movement (unconscious)
        state = sensor_data.get('state', '')
        if state == 'no_movement':
            events.append({
                'event': SystemEvent.NO_MOVEMENT,
                'confidence': 0.8,
                'timestamp': sensor_data['timestamp'],
                'location': 'Waist Belt',
                'action_required': True,
                'details': {'activity_state': state}
            })
        
        # Recovery detected
        elif state == 'recovery':
            events.append({
                'event': SystemEvent.RECOVERY_DETECTED,
                'confidence': 0.7,
                'timestamp': sensor_data['timestamp'],
                'location': 'Waist Belt',
                'action_required': False,
                'details': {'activity_state': state}
            })
        
        return events if events else None
    
    def _update_metrics(self, event_data: Dict[str, Any]):
        """Update system metrics."""
        event = event_data.get('event')
        self.metrics['total_events'] += 1
        self.metrics['last_event'] = event_data
        
        if event == SystemEvent.FALL_DETECTED:
            self.metrics['fall_events'] += 1
        elif event == SystemEvent.PANIC_BUTTON:
            self.metrics['panic_events'] += 1
        elif event == SystemEvent.FALSE_ALARM:
            self.metrics['false_alarms'] += 1
        
        # Update active alerts
        if event_data.get('action_required', False):
            self.metrics['active_alerts'].append(event_data)
            # Keep only last 10 active alerts
            self.metrics['active_alerts'] = self.metrics['active_alerts'][-10:]
    
    def _update_system_state(self, event_data: Dict[str, Any]):
        """Update overall system state based on events."""
        event = event_data.get('event')
        action_required = event_data.get('action_required', False)
        
        if event in [SystemEvent.FALL_DETECTED, SystemEvent.PANIC_BUTTON]:
            self.current_state = SystemState.EMERGENCY
        elif action_required and event != SystemEvent.FALSE_ALARM:
            self.current_state = SystemState.ALERT_ACTIVE
        elif event == SystemEvent.RECOVERY_DETECTED:
            self.current_state = SystemState.RECOVERY
        elif not action_required:
            self.current_state = SystemState.NORMAL
    
    def _process_sensor_data(self, sensor_data: Dict[str, Any]):
        """Process incoming sensor data and detect events."""
        try:
            # Store sensor data for history
            self.sensor_history.append(sensor_data.copy())
            if len(self.sensor_history) > self.max_history_size:
                self.sensor_history.pop(0)
            
            # Detect various events
            detected_events = []
            
            # Fall detection
            fall_event = self._detect_fall_event(sensor_data)
            if fall_event:
                detected_events.append(fall_event)
            
            # Panic button
            panic_event = self._detect_panic_event(sensor_data)
            if panic_event:
                detected_events.append(panic_event)
            
            # Health anomalies
            health_event = self._detect_health_anomalies(sensor_data)
            if health_event:
                detected_events.append(health_event)
            
            # Device events
            device_events = self._detect_device_events(sensor_data)
            if device_events:
                detected_events.extend(device_events)
            
            # Process detected events
            for event_data in detected_events:
                event = event_data.get('event')
                
                # Check cooldown
                if self._is_in_cooldown(event):
                    continue
                
                # Update cooldown
                self._update_cooldown(event)
                
                # Update metrics and state
                self._update_metrics(event_data)
                self._update_system_state(event_data)
                
                # Send alert if action required
                if event_data.get('action_required', False):
                    self._send_alert(event_data)
                
                # Notify callbacks
                self._notify_event_callbacks(event_data)
        
        except Exception as e:
            print(f"Sensor data processing error: {e}")
    
    def _send_alert(self, event_data: Dict[str, Any]):
        """Send alert through the alert system."""
        try:
            event = event_data.get('event')
            confidence = event_data.get('confidence', 0.0)
            
            # Determine alert type and level
            if event == SystemEvent.FALL_DETECTED:
                alert_type = AlertType.FALL
                alert_level = AlertLevel.EMERGENCY if confidence > 0.8 else AlertLevel.HIGH
            elif event == SystemEvent.PANIC_BUTTON:
                alert_type = AlertType.MANUAL_EMERGENCY
                alert_level = AlertLevel.EMERGENCY
            elif event == SystemEvent.HEALTH_ANOMALY:
                alert_type = AlertType.HEALTH_ANOMALY
                alert_level = AlertLevel.MEDIUM
            elif event == SystemEvent.DEVICE_REMOVED:
                alert_type = AlertType.DEVICE_REMOVED
                alert_level = AlertLevel.MEDIUM
            elif event == SystemEvent.LOW_BATTERY:
                alert_type = AlertType.LOW_BATTERY
                alert_level = AlertLevel.LOW
            elif event == SystemEvent.NO_MOVEMENT:
                alert_type = AlertType.INACTIVITY
                alert_level = AlertLevel.HIGH
            else:
                return
            
            # Send alert
            send_alert(
                alert_type=alert_type,
                level=alert_level,
                message=event_data.get('details', {}),
                confidence=confidence,
                location=event_data.get('location', 'Unknown'),
                timestamp=event_data.get('timestamp', datetime.now().isoformat())
            )
        
        except Exception as e:
            print(f"Alert sending error: {e}")
    
    def start_system(self):
        """Start the real-time system integration."""
        if not self.simulator.start_simulation():
            return False
        
        print("🚀 Real-time system integration started")
        return True
    
    def stop_system(self):
        """Stop the real-time system integration."""
        self.simulator.stop_simulation()
        print("⏹️ Real-time system integration stopped")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            'state': self.current_state.value,
            'simulation_state': self.simulator.get_current_state().value,
            'metrics': self.metrics.copy(),
            'uptime_seconds': int(time.time() - self.metrics['system_uptime']),
            'active_alerts': len(self.metrics['active_alerts']),
            'last_alert_times': self.last_alert_time.copy()
        }
    
    def get_sensor_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent sensor data history."""
        return self.sensor_history[-limit:]
    
    def force_event(self, event_type: str):
        """Force a specific event for testing."""
        if event_type == "fall_forward":
            self.simulator.force_state(ActivityState.FALL_FORWARD)
        elif event_type == "fall_sideways":
            self.simulator.force_state(ActivityState.FALL_SIDEWAYS)
        elif event_type == "sudden_collapse":
            self.simulator.force_state(ActivityState.SUDDEN_COLLAPSE)
        elif event_type == "panic_button":
            self.simulator.force_state(ActivityState.PANIC_BUTTON)
        elif event_type == "low_battery":
            self.simulator.force_state(ActivityState.LOW_BATTERY)
        elif event_type == "no_movement":
            self.simulator.force_state(ActivityState.NO_MOVEMENT)
        elif event_type == "reset":
            self.simulator.force_state(ActivityState.NORMAL_WALKING)
            self.current_state = SystemState.NORMAL
            self.metrics['active_alerts'] = []

# Global system integration instance
_system_integration = None

def initialize_system_integration() -> RealTimeSystemIntegration:
    """Initialize the global system integration."""
    global _system_integration
    _system_integration = RealTimeSystemIntegration()
    return _system_integration

def get_system_integration() -> Optional[RealTimeSystemIntegration]:
    """Get the global system integration instance."""
    return _system_integration

def start_realtime_system():
    """Start the real-time monitoring system."""
    if _system_integration:
        return _system_integration.start_system()
    return False

def stop_realtime_system():
    """Stop the real-time monitoring system."""
    if _system_integration:
        _system_integration.stop_system()

def get_system_status() -> Optional[Dict[str, Any]]:
    """Get current system status."""
    if _system_integration:
        return _system_integration.get_system_status()
    return None

def force_simulation_event(event_type: str):
    """Force a simulation event for testing."""
    if _system_integration:
        _system_integration.force_event(event_type)
