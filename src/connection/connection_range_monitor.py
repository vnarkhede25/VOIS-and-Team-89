"""
Connection Range Alert System

Monitors WiFi connection between waist band and senior citizen website/app.
Generates alerts when senior citizen goes out of range or connection is lost.

Features:
- WiFi connection monitoring
- Range detection and alerts
- Connection lost notifications
- Automatic reconnection attempts
- Guardian notifications when out of range
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass
import requests

class ConnectionStatus(Enum):
    """WiFi connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    OUT_OF_RANGE = "out_of_range"
    RECONNECTING = "reconnecting"
    UNKNOWN = "unknown"

class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class ConnectionAlert:
    """Connection range alert."""
    alert_id: str
    alert_type: str
    alert_level: AlertLevel
    message: str
    timestamp: float
    duration: float
    resolved: bool = False
    guardian_notified: bool = False

class ConnectionRangeMonitor:
    """Monitors WiFi connection range and generates alerts."""
    
    def __init__(self, backend_url: str = "http://localhost:5000/api", 
                 patient_id: str = "demo_patient"):
        self.backend_url = backend_url
        self.patient_id = patient_id
        self.logger = logging.getLogger(__name__)
        
        # Connection monitoring
        self.connection_status = ConnectionStatus.UNKNOWN
        self.last_ping_time = 0
        self.ping_interval = 5  # seconds
        self.connection_timeout = 15  # seconds
        self.max_range_meters = 50  # WiFi range estimate
        
        # Alert tracking
        self.active_alerts = {}
        self.alert_history = []
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5 minutes between similar alerts
        
        # Statistics
        self.connection_events = []
        self.range_violations = []
        self.disconnection_durations = []
        
        # Reconnection attempts
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_interval = 10  # seconds
        
    async def start_monitoring(self):
        """Start connection range monitoring."""
        self.logger.info("📡 Starting connection range monitoring...")
        
        while True:
            try:
                await self._check_connection_status()
                await asyncio.sleep(self.ping_interval)
                
            except Exception as e:
                self.logger.error(f"❌ Error in connection monitoring: {e}")
                await asyncio.sleep(self.ping_interval)
    
    async def _check_connection_status(self):
        """Check current WiFi connection status."""
        current_time = time.time()
        
        # Try to ping the waist band device
        is_connected = await self._ping_device()
        
        # Update connection status
        if is_connected:
            if self.connection_status != ConnectionStatus.CONNECTED:
                await self._handle_connection_reestablished()
            self.connection_status = ConnectionStatus.CONNECTED
            self.last_ping_time = current_time
            self.reconnect_attempts = 0
            
        else:
            time_since_last_ping = current_time - self.last_ping_time
            
            if self.connection_status == ConnectionStatus.CONNECTED:
                # Just disconnected
                if time_since_last_ping < self.connection_timeout:
                    self.connection_status = ConnectionStatus.OUT_OF_RANGE
                    await self._handle_out_of_range()
                else:
                    self.connection_status = ConnectionStatus.DISCONNECTED
                    await self._handle_connection_lost()
                    
            elif self.connection_status == ConnectionStatus.OUT_OF_RANGE:
                # Still out of range
                if time_since_last_ping >= self.connection_timeout:
                    self.connection_status = ConnectionStatus.DISCONNECTED
                    await self._handle_connection_lost()
                    
            elif self.connection_status == ConnectionStatus.DISCONNECTED:
                # Try to reconnect
                await self._attempt_reconnection()
        
        # Log connection event
        self._log_connection_event(current_time, is_connected)
    
    async def _ping_device(self):
        """Ping the waist band device to check connectivity."""
        try:
            # Try to connect to device web server
            response = requests.get(
                "http://192.168.4.1/api/status",
                timeout=3
            )
            return response.status_code == 200
            
        except requests.exceptions.RequestException:
            return False
    
    async def _handle_out_of_range(self):
        """Handle when senior goes out of WiFi range."""
        self.logger.warning("⚠️ Senior citizen went out of WiFi range")
        
        # Create out of range alert
        alert_id = f"out_of_range_{int(time.time())}"
        alert = ConnectionAlert(
            alert_id=alert_id,
            alert_type="out_of_range",
            alert_level=AlertLevel.WARNING,
            message="Senior citizen has moved out of WiFi range of waist band",
            timestamp=time.time(),
            duration=0
        )
        
        self.active_alerts[alert_id] = alert
        await self._send_alert(alert)
        
        # Notify guardians
        await self._notify_guardians(alert)
    
    async def _handle_connection_lost(self):
        """Handle when connection is completely lost."""
        self.logger.error("❌ Connection to waist band lost")
        
        # Create connection lost alert
        alert_id = f"connection_lost_{int(time.time())}"
        alert = ConnectionAlert(
            alert_id=alert_id,
            alert_type="connection_lost",
            alert_level=AlertLevel.CRITICAL,
            message="Connection to waist band device lost - possible device issue",
            timestamp=time.time(),
            duration=0
        )
        
        self.active_alerts[alert_id] = alert
        await self._send_alert(alert)
        
        # Notify guardians with higher priority
        await self._notify_guardians(alert)
        
        # Record disconnection duration
        self.disconnection_durations.append({
            "start_time": time.time(),
            "end_time": None,
            "resolved": False
        })
    
    async def _handle_connection_reestablished(self):
        """Handle when connection is reestablished."""
        self.logger.info("✅ Connection to waist band reestablished")
        
        # Resolve active alerts
        for alert_id, alert in self.active_alerts.items():
            if not alert.resolved:
                alert.resolved = True
                alert.duration = time.time() - alert.timestamp
                
                # Create resolved alert
                resolved_alert = ConnectionAlert(
                    alert_id=f"resolved_{alert_id}",
                    alert_type="connection_resolved",
                    alert_level=AlertLevel.INFO,
                    message=f"Connection restored after {alert.duration:.1f} seconds",
                    timestamp=time.time(),
                    duration=0
                )
                
                await self._send_alert(resolved_alert)
        
        # Update disconnection duration
        if self.disconnection_durations:
            last_disconnect = self.disconnection_durations[-1]
            if not last_disconnect["resolved"]:
                last_disconnect["end_time"] = time.time()
                last_disconnect["resolved"] = True
                last_disconnect["duration"] = last_disconnect["end_time"] - last_disconnect["start_time"]
        
        # Clear active alerts
        self.active_alerts.clear()
    
    async def _attempt_reconnection(self):
        """Attempt to reconnect to the device."""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.logger.error(f"❌ Max reconnection attempts ({self.max_reconnect_attempts}) reached")
            return
        
        self.connection_status = ConnectionStatus.RECONNECTING
        self.reconnect_attempts += 1
        
        self.logger.info(f"🔄 Attempting reconnection ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
        
        # Wait before attempting reconnection
        await asyncio.sleep(self.reconnect_interval)
        
        # The next ping cycle will check if reconnection was successful
    
    async def _send_alert(self, alert: ConnectionAlert):
        """Send alert to backend system."""
        try:
            # Check cooldown
            last_time = self.last_alert_time.get(alert.alert_type, 0)
            if time.time() - last_time < self.alert_cooldown:
                return
            
            # Send to backend
            alert_data = {
                "alert_id": alert.alert_id,
                "patient_id": self.patient_id,
                "alert_type": alert.alert_type,
                "alert_level": alert.alert_level.value,
                "message": alert.message,
                "timestamp": alert.timestamp,
                "source": "connection_monitor",
                "metadata": {
                    "connection_status": self.connection_status.value,
                    "reconnect_attempts": self.reconnect_attempts
                }
            }
            
            response = requests.post(
                f"{self.backend_url}/alerts",
                json=alert_data,
                timeout=5
            )
            
            if response.status_code == 200:
                self.last_alert_time[alert.alert_type] = time.time()
                self.alert_history.append(alert)
                self.logger.info(f"🚨 Connection alert sent: {alert.alert_type}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send connection alert: {e}")
    
    async def _notify_guardians(self, alert: ConnectionAlert):
        """Notify guardians about connection issues."""
        try:
            # Get guardian contacts from backend
            response = requests.get(
                f"{self.backend_url}/patients/{self.patient_id}/guardians",
                timeout=5
            )
            
            if response.status_code == 200:
                guardians = response.json().get("guardians", [])
                
                for guardian in guardians:
                    notification_data = {
                        "guardian_id": guardian.get("id"),
                        "patient_id": self.patient_id,
                        "alert_type": alert.alert_type,
                        "alert_level": alert.alert_level.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp,
                        "requires_action": alert.alert_level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]
                    }
                    
                    # Send notification
                    await self._send_guardian_notification(guardian, notification_data)
                    
                alert.guardian_notified = True
                
        except Exception as e:
            self.logger.error(f"❌ Failed to notify guardians: {e}")
    
    async def _send_guardian_notification(self, guardian: Dict[str, Any], notification: Dict[str, Any]):
        """Send notification to specific guardian."""
        try:
            # Send via backend notification system
            response = requests.post(
                f"{self.backend_url}/notifications/guardian",
                json=notification,
                timeout=5
            )
            
            if response.status_code == 200:
                self.logger.info(f"📱 Guardian notified: {guardian.get('name', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to notify guardian: {e}")
    
    def _log_connection_event(self, timestamp: float, connected: bool):
        """Log connection event for analytics."""
        self.connection_events.append({
            "timestamp": timestamp,
            "connected": connected,
            "status": self.connection_status.value
        })
        
        # Keep only recent events (last 24 hours)
        cutoff_time = timestamp - (24 * 3600)
        self.connection_events = [
            event for event in self.connection_events 
            if event["timestamp"] > cutoff_time
        ]
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status and statistics."""
        current_time = time.time()
        
        # Calculate uptime percentage
        recent_events = [
            event for event in self.connection_events
            if current_time - event["timestamp"] < 3600  # Last hour
        ]
        
        if recent_events:
            connected_count = sum(1 for event in recent_events if event["connected"])
            uptime_percentage = (connected_count / len(recent_events)) * 100
        else:
            uptime_percentage = 0
        
        return {
            "current_status": self.connection_status.value,
            "last_ping": self.last_ping_time,
            "time_since_last_ping": current_time - self.last_ping_time,
            "reconnect_attempts": self.reconnect_attempts,
            "active_alerts": len(self.active_alerts),
            "uptime_percentage": round(uptime_percentage, 1),
            "total_alerts": len(self.alert_history),
            "recent_disconnections": len([
                d for d in self.disconnection_durations 
                if not d["resolved"] or (current_time - d["start_time"]) < 3600
            ])
        }
    
    def get_connection_analytics(self) -> Dict[str, Any]:
        """Get connection analytics and insights."""
        current_time = time.time()
        
        # Calculate statistics
        total_events = len(self.connection_events)
        if total_events == 0:
            return {"message": "No connection data available"}
        
        # Connection quality metrics
        connected_events = [e for e in self.connection_events if e["connected"]]
        connection_quality = (len(connected_events) / total_events) * 100
        
        # Average disconnection duration
        resolved_disconnections = [
            d for d in self.disconnection_durations 
            if d["resolved"] and d["duration"] is not None
        ]
        
        if resolved_disconnections:
            avg_disconnect_duration = sum(d["duration"] for d in resolved_disconnections) / len(resolved_disconnections)
        else:
            avg_disconnect_duration = 0
        
        # Most common disconnection times
        disconnect_hours = []
        for event in self.connection_events:
            if not event["connected"]:
                hour = datetime.fromtimestamp(event["timestamp"]).hour
                disconnect_hours.append(hour)
        
        if disconnect_hours:
            from collections import Counter
            most_common_hour = Counter(disconnect_hours).most_common(1)[0][0]
        else:
            most_common_hour = None
        
        return {
            "connection_quality": round(connection_quality, 1),
            "total_disconnections": len(self.disconnection_durations),
            "average_disconnect_duration": round(avg_disconnect_duration, 1),
            "most_common_disconnect_hour": most_common_hour,
            "alert_frequency": len(self.alert_history) / max(1, (current_time - min(e["timestamp"] for e in self.connection_events)) / 3600),
            "reconnect_success_rate": (
                len([d for d in self.disconnection_durations if d["resolved"]]) / 
                max(1, len(self.disconnection_durations))
            ) * 100
        }

# Global connection monitor instance
_connection_monitor = None

def initialize_connection_monitor(backend_url: str = "http://localhost:5000/api", 
                                patient_id: str = "demo_patient") -> ConnectionRangeMonitor:
    """Initialize the global connection monitor."""
    global _connection_monitor
    _connection_monitor = ConnectionRangeMonitor(backend_url, patient_id)
    return _connection_monitor

def get_connection_monitor() -> ConnectionRangeMonitor:
    """Get the global connection monitor instance."""
    return _connection_monitor

async def start_connection_monitoring():
    """Start connection monitoring in background."""
    if _connection_monitor:
        await _connection_monitor.start_monitoring()

def get_connection_status() -> Dict[str, Any]:
    """Get current connection status."""
    if _connection_monitor:
        return _connection_monitor.get_connection_status()
    return {"status": "not_initialized"}

def get_connection_analytics() -> Dict[str, Any]:
    """Get connection analytics."""
    if _connection_monitor:
        return _connection_monitor.get_connection_analytics()
    return {"error": "Connection monitor not initialized"}
