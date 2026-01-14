"""
Multi-Level Alert System with Escalation

Implements comprehensive alerting with:
- Local buzzer alerts
- Remote guardian notifications
- Escalation protocols
- Alert rate limiting
- Multi-channel communication
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum
from datetime import datetime, timedelta
from collections import deque
import json
import requests
from dataclasses import dataclass

class AlertType(Enum):
    """Types of alerts."""
    FALL_DETECTED = "fall_detected"
    PRE_FALL_WARNING = "pre_fall_warning"
    HEALTH_ANOMALY = "health_anomaly"
    DEVICE_OFFLINE = "device_offline"
    BATTERY_LOW = "battery_low"
    MEDICATION_MISSED = "medication_missed"
    EMERGENCY = "emergency"

class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertChannel(Enum):
    """Alert delivery channels."""
    LOCAL_BUZZER = "local_buzzer"
    MOBILE_NOTIFICATION = "mobile_notification"
    EMAIL = "email"
    SMS = "sms"
    WEB_SOCKET = "web_socket"
    VOICE_CALL = "voice_call"

@dataclass
class Alert:
    """Alert data structure."""
    id: str
    type: AlertType
    level: AlertLevel
    message: str
    patient_id: str
    timestamp: float
    acknowledged: bool = False
    escalated: bool = False
    channels_used: List[AlertChannel] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.channels_used is None:
            self.channels_used = []
        if self.metadata is None:
            self.metadata = {}

class AlertRateLimiter:
    """Rate limiting for alerts to prevent spam."""
    
    def __init__(self, max_alerts_per_minute: int = 5, max_alerts_per_hour: int = 50):
        self.max_per_minute = max_alerts_per_minute
        self.max_per_hour = max_alerts_per_hour
        
        self.minute_alerts = deque(maxlen=max_alerts_per_minute)
        self.hour_alerts = deque(maxlen=max_alerts_per_hour)
        
    def can_send_alert(self, alert_type: AlertType) -> Tuple[bool, str]:
        """
        Check if alert can be sent based on rate limits.
        
        Returns:
            Tuple of (can_send, reason)
        """
        current_time = time.time()
        
        # Clean old alerts
        self._clean_old_alerts(current_time)
        
        # Check minute limit
        if len(self.minute_alerts) >= self.max_per_minute:
            return False, f"Rate limit exceeded: {self.max_per_minute} alerts per minute"
        
        # Check hour limit
        if len(self.hour_alerts) >= self.max_per_hour:
            return False, f"Rate limit exceeded: {self.max_per_hour} alerts per hour"
        
        # Emergency alerts bypass rate limits
        if alert_type == AlertType.EMERGENCY:
            return True, "Emergency alert bypasses rate limits"
        
        return True, "Rate limits OK"
    
    def record_alert(self, alert_type: AlertType):
        """Record an alert for rate limiting."""
        current_time = time.time()
        
        self.minute_alerts.append((current_time, alert_type))
        self.hour_alerts.append((current_time, alert_type))
    
    def _clean_old_alerts(self, current_time: float):
        """Remove alerts older than time windows."""
        # Clean minute window (60 seconds)
        while (self.minute_alerts and 
               current_time - self.minute_alerts[0][0] > 60):
            self.minute_alerts.popleft()
        
        # Clean hour window (3600 seconds)
        while (self.hour_alerts and 
               current_time - self.hour_alerts[0][0] > 3600):
            self.hour_alerts.popleft()

class AlertChannelHandler:
    """Handles alert delivery through different channels."""
    
    def __init__(self, backend_url: str = "http://localhost:5000/api"):
        self.backend_url = backend_url
        self.connected_guardians = {}
        self.websocket_connections = {}
        
    async def send_local_buzzer(self, alert: Alert, pattern: str = "emergency") -> bool:
        """Send local buzzer alert."""
        try:
            # Import buzzer from hardware interface
            from ..sensors.enhanced_hardware_interface import get_buzzer
            buzzer = get_buzzer()
            
            if buzzer:
                # Different patterns for different alert types
                if alert.level == AlertLevel.EMERGENCY:
                    buzzer.pulse(count=5, interval=0.2)
                elif alert.level == AlertLevel.CRITICAL:
                    buzzer.pulse(count=3, interval=0.5)
                elif alert.level == AlertLevel.WARNING:
                    buzzer.pulse(count=2, interval=1.0)
                else:
                    buzzer.pulse(count=1, interval=1.5)
                
                print(f"🔊 Local buzzer alert sent: {alert.message}")
                return True
            else:
                print("⚠️ Buzzer not available")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send buzzer alert: {e}")
            return False
    
    async def send_mobile_notification(self, alert: Alert, guardian_contacts: List[str]) -> bool:
        """Send mobile notification to guardians."""
        try:
            # Send to backend for mobile push notifications
            payload = {
                "alert_id": alert.id,
                "type": alert.type.value,
                "level": alert.level.value,
                "message": alert.message,
                "patient_id": alert.patient_id,
                "timestamp": alert.timestamp,
                "channels": ["mobile"]
            }
            
            response = requests.post(
                f"{self.backend_url}/alerts/mobile",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"📱 Mobile notification sent to {len(guardian_contacts)} guardians")
                return True
            else:
                print(f"⚠️ Mobile notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send mobile notification: {e}")
            return False
    
    async def send_email_alert(self, alert: Alert, guardian_emails: List[str]) -> bool:
        """Send email alert to guardians."""
        try:
            payload = {
                "alert_id": alert.id,
                "type": alert.type.value,
                "level": alert.level.value,
                "message": alert.message,
                "patient_id": alert.patient_id,
                "timestamp": alert.timestamp,
                "recipients": guardian_emails,
                "channels": ["email"]
            }
            
            response = requests.post(
                f"{self.backend_url}/alerts/email",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                print(f"📧 Email alert sent to {len(guardian_emails)} recipients")
                return True
            else:
                print(f"⚠️ Email alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send email alert: {e}")
            return False
    
    async def send_sms_alert(self, alert: Alert, guardian_phones: List[str]) -> bool:
        """Send SMS alert to guardians."""
        try:
            payload = {
                "alert_id": alert.id,
                "type": alert.type.value,
                "level": alert.level.value,
                "message": alert.message,
                "patient_id": alert.patient_id,
                "timestamp": alert.timestamp,
                "recipients": guardian_phones,
                "channels": ["sms"]
            }
            
            response = requests.post(
                f"{self.backend_url}/alerts/sms",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                print(f"📱 SMS alert sent to {len(guardian_phones)} recipients")
                return True
            else:
                print(f"⚠️ SMS alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send SMS alert: {e}")
            return False
    
    async def send_websocket_alert(self, alert: Alert) -> bool:
        """Send real-time alert via WebSocket."""
        try:
            payload = {
                "type": "alert",
                "data": {
                    "id": alert.id,
                    "alert_type": alert.type.value,
                    "level": alert.level.value,
                    "message": alert.message,
                    "patient_id": alert.patient_id,
                    "timestamp": alert.timestamp,
                    "metadata": alert.metadata
                }
            }
            
            # Send to backend WebSocket broadcast
            response = requests.post(
                f"{self.backend_url}/alerts/websocket",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"🌐 WebSocket alert broadcasted")
                return True
            else:
                print(f"⚠️ WebSocket alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send WebSocket alert: {e}")
            return False
    
    def register_guardian(self, guardian_id: str, contacts: Dict[str, List[str]]):
        """Register guardian contact information."""
        self.connected_guardians[guardian_id] = contacts
        print(f"👥 Guardian {guardian_id} registered with {len(contacts)} contact methods")

class AlertEscalationManager:
    """Manages alert escalation protocols."""
    
    def __init__(self):
        self.escalation_rules = self._initialize_escalation_rules()
        self.escalation_history = deque(maxlen=100)
        
    def _initialize_escalation_rules(self) -> Dict[AlertType, List[Dict]]:
        """Initialize escalation rules for different alert types."""
        return {
            AlertType.FALL_DETECTED: [
                {
                    "delay": 0,  # Immediate
                    "channels": [AlertChannel.LOCAL_BUZZER, AlertChannel.MOBILE_NOTIFICATION],
                    "condition": None
                },
                {
                    "delay": 60,  # 1 minute
                    "channels": [AlertChannel.EMAIL, AlertChannel.WEB_SOCKET],
                    "condition": "not_acknowledged"
                },
                {
                    "delay": 300,  # 5 minutes
                    "channels": [AlertChannel.SMS],
                    "condition": "not_acknowledged"
                },
                {
                    "delay": 600,  # 10 minutes
                    "channels": [AlertChannel.VOICE_CALL],
                    "condition": "not_acknowledged"
                }
            ],
            AlertType.EMERGENCY: [
                {
                    "delay": 0,  # Immediate
                    "channels": [AlertChannel.LOCAL_BUZZER, AlertChannel.MOBILE_NOTIFICATION, 
                                AlertChannel.SMS, AlertChannel.EMAIL, AlertChannel.WEB_SOCKET],
                    "condition": None
                },
                {
                    "delay": 30,  # 30 seconds
                    "channels": [AlertChannel.VOICE_CALL],
                    "condition": "not_acknowledged"
                }
            ],
            AlertType.HEALTH_ANOMALY: [
                {
                    "delay": 0,
                    "channels": [AlertChannel.MOBILE_NOTIFICATION, AlertChannel.WEB_SOCKET],
                    "condition": None
                },
                {
                    "delay": 300,  # 5 minutes
                    "channels": [AlertChannel.EMAIL],
                    "condition": "not_acknowledged"
                }
            ],
            AlertType.PRE_FALL_WARNING: [
                {
                    "delay": 0,
                    "channels": [AlertChannel.LOCAL_BUZZER, AlertChannel.MOBILE_NOTIFICATION],
                    "condition": None
                }
            ]
        }
    
    def get_escalation_plan(self, alert: Alert) -> List[Dict]:
        """Get escalation plan for an alert."""
        return self.escalation_rules.get(alert.type, [])
    
    def should_escalate(self, alert: Alert, escalation_step: Dict) -> bool:
        """Check if alert should be escalated to next level."""
        condition = escalation_step.get("condition")
        
        if condition is None:
            return True
        elif condition == "not_acknowledged":
            return not alert.acknowledged
        elif condition == "not_escalated":
            return not alert.escalated
        
        return False

class MultiLevelAlertSystem:
    """Main alert system coordinating all alerting functionality."""
    
    def __init__(self, backend_url: str = "http://localhost:5000/api", patient_id: str = "demo_patient"):
        self.backend_url = backend_url
        self.patient_id = patient_id
        
        # Components
        self.rate_limiter = AlertRateLimiter()
        self.channel_handler = AlertChannelHandler(backend_url)
        self.escalation_manager = AlertEscalationManager()
        
        # State
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.escalation_timers = {}
        
        # Callbacks
        self.alert_callbacks = []
        
        # Background tasks
        self.running = False
        self.background_tasks = []
        
    def start(self):
        """Start the alert system."""
        self.running = True
        print("🚨 Multi-level alert system started")
        
    def stop(self):
        """Stop the alert system."""
        self.running = False
        
        # Cancel all background tasks
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
        
        print("🛑 Multi-level alert system stopped")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add callback function for alert events."""
        self.alert_callbacks.append(callback)
    
    async def send_alert(self, alert_type: AlertType, level: AlertLevel, 
                        message: str, metadata: Dict[str, Any] = None) -> str:
        """
        Send an alert through the multi-level system.
        
        Returns:
            Alert ID
        """
        # Check rate limits
        can_send, reason = self.rate_limiter.can_send_alert(alert_type)
        if not can_send:
            print(f"⚠️ Alert rate limited: {reason}")
            return None
        
        # Create alert
        alert_id = f"{alert_type.value}_{int(time.time())}"
        alert = Alert(
            id=alert_id,
            type=alert_type,
            level=level,
            message=message,
            patient_id=self.patient_id,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        # Record for rate limiting
        self.rate_limiter.record_alert(alert_type)
        
        # Store decision
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Store alert for statistics
        if not hasattr(self, 'recent_alerts'):
            self.recent_alerts = []
        
        self.recent_alerts.append({
            "id": alert.id,
            "type": alert.type.value,
            "level": alert.level.value,
            "timestamp": alert.timestamp,
            "acknowledged": alert.acknowledged
        })
        
        # Keep only recent alerts
        if len(self.recent_alerts) > 50:
            self.recent_alerts = self.recent_alerts[-50:]
        
        # Start escalation process
        await self._start_escalation(alert)
        
        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"❌ Alert callback error: {e}")
        
        print(f"🚨 Alert sent: {alert_type.value} - {message}")
        return alert_id
    
    async def _start_escalation(self, alert: Alert):
        """Start escalation process for an alert."""
        escalation_plan = self.escalation_manager.get_escalation_plan(alert)
        
        for i, step in enumerate(escalation_plan):
            # Schedule escalation step
            delay = step.get("delay", 0)
            
            if delay == 0:
                # Immediate escalation
                await self._execute_escalation_step(alert, step)
            else:
                # Scheduled escalation
                task = asyncio.create_task(
                    self._scheduled_escalation(alert, step, delay)
                )
                self.background_tasks.append(task)
    
    async def _scheduled_escalation(self, alert: Alert, step: Dict, delay: float):
        """Execute scheduled escalation step."""
        await asyncio.sleep(delay)
        
        # Check if alert still exists and needs escalation
        if alert.id in self.active_alerts:
            if self.escalation_manager.should_escalate(alert, step):
                await self._execute_escalation_step(alert, step)
    
    async def _execute_escalation_step(self, alert: Alert, step: Dict):
        """Execute a single escalation step."""
        channels = step.get("channels", [])
        
        # Get guardian contacts
        guardian_contacts = await self._get_guardian_contacts()
        
        # Send through each channel
        for channel in channels:
            try:
                success = False
                
                if channel == AlertChannel.LOCAL_BUZZER:
                    success = await self.channel_handler.send_local_buzzer(alert)
                elif channel == AlertChannel.MOBILE_NOTIFICATION:
                    success = await self.channel_handler.send_mobile_notification(
                        alert, guardian_contacts.get("mobile", [])
                    )
                elif channel == AlertChannel.EMAIL:
                    success = await self.channel_handler.send_email_alert(
                        alert, guardian_contacts.get("email", [])
                    )
                elif channel == AlertChannel.SMS:
                    success = await self.channel_handler.send_sms_alert(
                        alert, guardian_contacts.get("phone", [])
                    )
                elif channel == AlertChannel.WEB_SOCKET:
                    success = await self.channel_handler.send_websocket_alert(alert)
                elif channel == AlertChannel.VOICE_CALL:
                    success = await self._initiate_voice_call(alert, guardian_contacts.get("phone", []))
                
                if success:
                    alert.channels_used.append(channel)
                    print(f"✅ Alert sent via {channel.value}")
                else:
                    print(f"❌ Failed to send alert via {channel.value}")
                    
            except Exception as e:
                print(f"❌ Error sending alert via {channel.value}: {e}")
        
        # Mark as escalated if this is not the first step
        if step.get("delay", 0) > 0:
            alert.escalated = True
    
    async def _get_guardian_contacts(self) -> Dict[str, List[str]]:
        """Get guardian contact information."""
        try:
            response = requests.get(
                f"{self.backend_url}/patients/{self.patient_id}/guardians",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "email": [g.get("email", "") for g in data.get("guardians", []) if g.get("email")],
                    "phone": [g.get("phone", "") for g in data.get("guardians", []) if g.get("phone")],
                    "mobile": [g.get("mobile", "") for g in data.get("guardians", []) if g.get("mobile")]
                }
        except Exception as e:
            print(f"⚠️ Failed to get guardian contacts: {e}")
        
        # Fallback contacts
        return {
            "email": ["guardian@example.com"],
            "phone": ["+1234567890"],
            "mobile": ["+1234567890"]
        }
    
    async def _initiate_voice_call(self, alert: Alert, phone_numbers: List[str]) -> bool:
        """Initiate emergency voice call."""
        try:
            payload = {
                "alert_id": alert.id,
                "message": f"Emergency alert for patient {alert.patient_id}: {alert.message}",
                "recipients": phone_numbers
            }
            
            response = requests.post(
                f"{self.backend_url}/alerts/voice",
                json=payload,
                timeout=20
            )
            
            if response.status_code == 200:
                print(f"📞 Voice call initiated to {len(phone_numbers)} numbers")
                return True
            else:
                print(f"⚠️ Voice call failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to initiate voice call: {e}")
            return False
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "guardian") -> bool:
        """Acknowledge an alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.acknowledged = True
            alert.metadata["acknowledged_by"] = acknowledged_by
            alert.metadata["acknowledged_time"] = time.time()
            
            # Cancel pending escalations
            self._cancel_pending_escalations(alert_id)
            
            print(f"✅ Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
        
        return False
    
    def _cancel_pending_escalations(self, alert_id: str):
        """Cancel pending escalation tasks for an alert."""
        if alert_id in self.escalation_timers:
            timer = self.escalation_timers[alert_id]
            if not timer.done():
                timer.cancel()
            del self.escalation_timers[alert_id]
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, count: int = 50) -> List[Alert]:
        """Get alert history."""
        return list(self.alert_history)[-count:]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get alert system status."""
        return {
            "running": self.running,
            "active_alerts": len(self.active_alerts),
            "total_alerts": len(self.alert_history),
            "rate_limits": {
                "per_minute": len(self.rate_limiter.minute_alerts),
                "per_hour": len(self.rate_limiter.hour_alerts)
            },
            "connected_guardians": len(self.channel_handler.connected_guardians),
            "background_tasks": len(self.background_tasks)
        }

# Global alert system instance
_alert_system = None

def initialize_alert_system(backend_url: str = "http://localhost:5000/api", 
                          patient_id: str = "demo_patient") -> MultiLevelAlertSystem:
    """Initialize the global alert system."""
    global _alert_system
    _alert_system = MultiLevelAlertSystem(backend_url, patient_id)
    return _alert_system

def get_alert_system() -> MultiLevelAlertSystem:
    """Get the global alert system instance."""
    return _alert_system

async def send_alert(alert_type: AlertType, level: AlertLevel, 
                    message: str, metadata: Dict[str, Any] = None) -> str:
    """Send an alert using the global system."""
    if _alert_system:
        return await _alert_system.send_alert(alert_type, level, message, metadata)
    return None

def acknowledge_alert(alert_id: str, acknowledged_by: str = "guardian") -> bool:
    """Acknowledge an alert using the global system."""
    if _alert_system:
        return _alert_system.acknowledge_alert(alert_id, acknowledged_by)
    return False

def get_alert_status() -> Dict[str, Any]:
    """Get alert system status."""
    if _alert_system:
        return _alert_system.get_system_status()
    return {"status": "not_initialized"}
