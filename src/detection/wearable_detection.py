"""
Wearable Detection System

Detects whether the senior citizen is actually wearing the waist band device.
Uses multiple sensors and algorithms to determine device wear status.

Features:
- Body contact detection via skin temperature
- Motion pattern analysis for wearing detection
- Device orientation validation
- Heart rate sensor contact detection
- Battery and connection status monitoring
- Alerts when device is not worn
"""

import asyncio
import time
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass
import requests

class WearStatus(Enum):
    """Device wear status."""
    WORN = "worn"
    NOT_WORN = "not_worn"
    UNCERTAIN = "uncertain"
    REMOVED = "removed"

class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class WearAlert:
    """Wear status alert."""
    alert_id: str
    alert_type: str
    alert_level: AlertLevel
    message: str
    timestamp: float
    wear_status: WearStatus
    confidence: float
    resolved: bool = False
    guardian_notified: bool = False

class WearableDetectionSystem:
    """Detects whether the waist band is being worn by the senior."""
    
    def __init__(self, backend_url: str = "http://localhost:5000/api", 
                 patient_id: str = "demo_patient"):
        self.backend_url = backend_url
        self.patient_id = patient_id
        self.logger = logging.getLogger(__name__)
        
        # Wear detection parameters
        self.skin_temp_threshold = 30.0  # °C - minimum skin temperature
        self.heart_rate_threshold = 40   # bpm - minimum heart rate
        self.motion_threshold = 0.1       # g - minimum motion for wearing
        self.orientation_valid_range = [-45, 45]  # degrees for waist orientation
        
        # Detection state
        self.current_wear_status = WearStatus.UNCERTAIN
        self.wear_confidence = 0.0
        self.last_detection_time = 0
        self.detection_interval = 10  # seconds
        self.consecutive_detections = 0
        self.min_consecutive = 3  # Need 3 consecutive detections to change status
        
        # Alert tracking
        self.active_alerts = {}
        self.alert_history = []
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5 minutes between similar alerts
        
        # Historical data for analysis
        self.wear_history = []
        self.temperature_history = []
        self.motion_history = []
        self.heart_rate_history = []
        
        # Sensor data cache
        self.last_sensor_data = {}
        self.last_device_status = {}
        
    async def start_monitoring(self):
        """Start wearable detection monitoring."""
        self.logger.info("👕 Starting wearable detection monitoring...")
        
        while True:
            try:
                await self._check_wear_status()
                await asyncio.sleep(self.detection_interval)
                
            except Exception as e:
                self.logger.error(f"❌ Error in wearable detection: {e}")
                await asyncio.sleep(self.detection_interval)
    
    async def _check_wear_status(self):
        """Check if the device is currently being worn."""
        try:
            # Get current sensor data
            sensor_data = await self._get_sensor_data()
            if not sensor_data:
                self.logger.warning("⚠️ No sensor data available for wear detection")
                return
            
            device_status = await self._get_device_status()
            if not device_status:
                self.logger.warning("⚠️ No device status available for wear detection")
                return
            
            # Perform wear detection analysis
            wear_analysis = self._analyze_wear_status(sensor_data, device_status)
            
            # Update wear status with confidence
            await self._update_wear_status(wear_analysis)
            
            # Store historical data
            self._store_historical_data(sensor_data, device_status, wear_analysis)
            
        except Exception as e:
            self.logger.error(f"❌ Error checking wear status: {e}")
    
    async def _get_sensor_data(self) -> Optional[Dict[str, Any]]:
        """Get current sensor data from hardware interface."""
        try:
            # Import here to avoid circular imports
            from sensors.enhanced_hardware_interface import get_sensor_data
            return get_sensor_data()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get sensor data: {e}")
            return None
    
    async def _get_device_status(self) -> Optional[Dict[str, Any]]:
        """Get current device status."""
        try:
            # Import here to avoid circular imports
            from sensors.enhanced_hardware_interface import get_hardware_interface
            hardware = get_hardware_interface()
            
            if hardware and hasattr(hardware, 'get_device_status'):
                return hardware.get_device_status()
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get device status: {e}")
            return None
    
    def _analyze_wear_status(self, sensor_data: Dict[str, Any], device_status: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sensor data to determine wear status."""
        
        # Initialize analysis results
        analysis = {
            'skin_temp_detected': False,
            'heart_rate_detected': False,
            'motion_detected': False,
            'orientation_valid': False,
            'body_contact_detected': False,
            'overall_confidence': 0.0,
            'wear_status': WearStatus.UNCERTAIN,
            'factors': {}
        }
        
        # 1. Skin Temperature Detection
        skin_temp = sensor_data.get('temperature', 0)
        if skin_temp >= self.skin_temp_threshold:
            analysis['skin_temp_detected'] = True
            analysis['factors']['skin_temperature'] = min(1.0, (skin_temp - self.skin_temp_threshold) / 10.0)
        
        # 2. Heart Rate Detection
        heart_rate = sensor_data.get('heart_rate', 0)
        if heart_rate >= self.heart_rate_threshold and heart_rate <= 200:
            analysis['heart_rate_detected'] = True
            analysis['factors']['heart_rate'] = min(1.0, heart_rate / 100.0)
        
        # 3. Motion Pattern Analysis
        ax, ay, az = sensor_data.get('ax', 0), sensor_data.get('ay', 0), sensor_data.get('az', 0)
        motion_magnitude = np.sqrt(ax**2 + ay**2 + az**2)
        
        # Check for human motion patterns
        if motion_magnitude > self.motion_threshold:
            # Check if motion pattern is human-like
            gx, gy, gz = sensor_data.get('gx', 0), sensor_data.get('gy', 0), sensor_data.get('gz', 0)
            gyro_magnitude = np.sqrt(gx**2 + gy**2 + gz**2)
            
            # Human motion typically has correlated accelerometer and gyroscope
            if gyro_magnitude > 0.1:
                analysis['motion_detected'] = True
                analysis['factors']['motion'] = min(1.0, motion_magnitude / 2.0)
        
        # 4. Device Orientation Validation
        pitch = sensor_data.get('pitch', 0)
        roll = sensor_data.get('roll', 0)
        
        # Waist band should be roughly horizontal when worn
        if (self.orientation_valid_range[0] <= pitch <= self.orientation_valid_range[1] and
            self.orientation_valid_range[0] <= roll <= self.orientation_valid_range[1]):
            analysis['orientation_valid'] = True
            analysis['factors']['orientation'] = 0.8
        
        # 5. Body Contact Detection (if available)
        body_contact = device_status.get('body_contact', False)
        if body_contact:
            analysis['body_contact_detected'] = True
            analysis['factors']['body_contact'] = 0.9
        
        # 6. Device Status Checks
        device_worn = device_status.get('worn', False)
        if device_worn:
            analysis['factors']['device_status'] = 0.7
        
        # Calculate overall confidence
        if analysis['factors']:
            total_confidence = sum(analysis['factors'].values())
            factor_count = len(analysis['factors'])
            analysis['overall_confidence'] = total_confidence / factor_count
        else:
            analysis['overall_confidence'] = 0.0
        
        # Determine wear status
        if analysis['overall_confidence'] >= 0.7:
            analysis['wear_status'] = WearStatus.WORN
        elif analysis['overall_confidence'] <= 0.3:
            analysis['wear_status'] = WearStatus.NOT_WORN
        else:
            analysis['wear_status'] = WearStatus.UNCERTAIN
        
        return analysis
    
    async def _update_wear_status(self, wear_analysis: Dict[str, Any]):
        """Update wear status with confidence and consecutive detection logic."""
        new_status = wear_analysis['wear_status']
        confidence = wear_analysis['overall_confidence']
        
        # Check if this is a consecutive detection
        if new_status == self.current_wear_status:
            self.consecutive_detections += 1
        else:
            self.consecutive_detections = 1
        
        # Only change status after consecutive detections
        if self.consecutive_detections >= self.min_consecutive:
            old_status = self.current_wear_status
            
            # Update status
            self.current_wear_status = new_status
            self.wear_confidence = confidence
            self.last_detection_time = time.time()
            
            # Log status change
            self.logger.info(f"👕 Wear status changed: {old_status.value} → {new_status.value} (confidence: {confidence:.2f})")
            
            # Handle status change alerts
            await self._handle_status_change(old_status, new_status, confidence)
        
        # Store in history
        self.wear_history.append({
            'timestamp': time.time(),
            'status': new_status.value,
            'confidence': confidence,
            'factors': wear_analysis['factors']
        })
        
        # Keep only recent history (last 24 hours)
        cutoff_time = time.time() - (24 * 3600)
        self.wear_history = [entry for entry in self.wear_history if entry['timestamp'] > cutoff_time]
    
    async def _handle_status_change(self, old_status: WearStatus, new_status: WearStatus, confidence: float):
        """Handle wear status change and generate appropriate alerts."""
        
        # Alert when device is removed
        if old_status == WearStatus.WORN and new_status in [WearStatus.NOT_WORN, WearStatus.UNCERTAIN]:
            await self._create_wear_alert(
                alert_type="device_removed",
                alert_level=AlertLevel.WARNING,
                message=f"Senior citizen may have removed the waist band device (confidence: {confidence:.2f})",
                wear_status=new_status,
                confidence=confidence
            )
        
        # Alert when device is put back on
        elif old_status in [WearStatus.NOT_WORN, WearStatus.UNCERTAIN] and new_status == WearStatus.WORN:
            await self._create_wear_alert(
                alert_type="device_worn",
                alert_level=AlertLevel.INFO,
                message=f"Senior citizen has put on the waist band device (confidence: {confidence:.2f})",
                wear_status=new_status,
                confidence=confidence
            )
        
        # Critical alert if device not worn for extended period
        elif new_status == WearStatus.NOT_WORN:
            await self._check_extended_not_worn_period()
    
    async def _check_extended_not_worn_period(self):
        """Check if device has not been worn for extended period."""
        current_time = time.time()
        
        # Find when device was last worn
        last_worn_time = None
        for entry in reversed(self.wear_history):
            if entry['status'] == WearStatus.WORN.value:
                last_worn_time = entry['timestamp']
                break
        
        if last_worn_time:
            not_worn_duration = current_time - last_worn_time
            
            # Critical alert if not worn for more than 2 hours
            if not_worn_duration > (2 * 3600):  # 2 hours
                await self._create_wear_alert(
                    alert_type="extended_not_worn",
                    alert_level=AlertLevel.CRITICAL,
                    message=f"Device has not been worn for {not_worn_duration/3600:.1f} hours - please check on senior",
                    wear_status=WearStatus.NOT_WORN,
                    confidence=0.9
                )
            
            # Warning if not worn for more than 30 minutes
            elif not_worn_duration > (30 * 60):  # 30 minutes
                await self._create_wear_alert(
                    alert_type="extended_not_worn",
                    alert_level=AlertLevel.WARNING,
                    message=f"Device has not been worn for {not_worn_duration/60:.1f} minutes",
                    wear_status=WearStatus.NOT_WORN,
                    confidence=0.7
                )
    
    async def _create_wear_alert(self, alert_type: str, alert_level: AlertLevel, 
                                message: str, wear_status: WearStatus, confidence: float):
        """Create and send wear status alert."""
        try:
            # Check cooldown
            last_time = self.last_alert_time.get(alert_type, 0)
            if time.time() - last_time < self.alert_cooldown:
                return
            
            # Create alert
            alert_id = f"wear_{alert_type}_{int(time.time())}"
            alert = WearAlert(
                alert_id=alert_id,
                alert_type=alert_type,
                alert_level=alert_level,
                message=message,
                timestamp=time.time(),
                wear_status=wear_status,
                confidence=confidence
            )
            
            # Store alert
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            self.last_alert_time[alert_type] = time.time()
            
            # Send alert to backend
            await self._send_alert(alert)
            
            # Notify guardians
            await self._notify_guardians(alert)
            
            self.logger.info(f"🚨 Wear alert sent: {alert_type} - {message}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create wear alert: {e}")
    
    async def _send_alert(self, alert: WearAlert):
        """Send wear alert to backend system."""
        try:
            alert_data = {
                "alert_id": alert.alert_id,
                "patient_id": self.patient_id,
                "alert_type": alert.alert_type,
                "alert_level": alert.alert_level.value,
                "message": alert.message,
                "timestamp": alert.timestamp,
                "source": "wearable_detection",
                "metadata": {
                    "wear_status": alert.wear_status.value,
                    "confidence": alert.confidence,
                    "detection_factors": self._get_latest_factors()
                }
            }
            
            response = requests.post(
                f"{self.backend_url}/alerts",
                json=alert_data,
                timeout=5
            )
            
            if response.status_code != 200:
                self.logger.error(f"❌ Failed to send wear alert: {response.status_code}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send wear alert: {e}")
    
    async def _notify_guardians(self, alert: WearAlert):
        """Notify guardians about wear status issues."""
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
            self.logger.error(f"❌ Failed to notify guardians about wear alert: {e}")
    
    async def _send_guardian_notification(self, guardian: Dict[str, Any], notification: Dict[str, Any]):
        """Send notification to specific guardian."""
        try:
            response = requests.post(
                f"{self.backend_url}/notifications/guardian",
                json=notification,
                timeout=5
            )
            
            if response.status_code == 200:
                self.logger.info(f"📱 Guardian notified about wear status: {guardian.get('name', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to notify guardian about wear status: {e}")
    
    def _store_historical_data(self, sensor_data: Dict[str, Any], device_status: Dict[str, Any], 
                             wear_analysis: Dict[str, Any]):
        """Store historical data for analysis."""
        current_time = time.time()
        
        # Store sensor data
        self.temperature_history.append({
            'timestamp': current_time,
            'value': sensor_data.get('temperature', 0)
        })
        
        # Store motion data
        ax, ay, az = sensor_data.get('ax', 0), sensor_data.get('ay', 0), sensor_data.get('az', 0)
        motion_magnitude = np.sqrt(ax**2 + ay**2 + az**2)
        self.motion_history.append({
            'timestamp': current_time,
            'value': motion_magnitude
        })
        
        # Store heart rate data
        self.heart_rate_history.append({
            'timestamp': current_time,
            'value': sensor_data.get('heart_rate', 0)
        })
        
        # Keep only recent data (last 24 hours)
        cutoff_time = current_time - (24 * 3600)
        
        self.temperature_history = [entry for entry in self.temperature_history if entry['timestamp'] > cutoff_time]
        self.motion_history = [entry for entry in self.motion_history if entry['timestamp'] > cutoff_time]
        self.heart_rate_history = [entry for entry in self.heart_rate_history if entry['timestamp'] > cutoff_time]
    
    def _get_latest_factors(self) -> Dict[str, float]:
        """Get latest detection factors."""
        if self.wear_history:
            return self.wear_history[-1].get('factors', {})
        return {}
    
    def get_wear_status(self) -> Dict[str, Any]:
        """Get current wear status and statistics."""
        current_time = time.time()
        
        # Calculate wear percentage (last hour)
        recent_entries = [
            entry for entry in self.wear_history
            if current_time - entry['timestamp'] < 3600  # Last hour
        ]
        
        if recent_entries:
            worn_count = sum(1 for entry in recent_entries if entry['status'] == WearStatus.WORN.value)
            wear_percentage = (worn_count / len(recent_entries)) * 100
        else:
            wear_percentage = 0
        
        return {
            "current_status": self.current_wear_status.value,
            "confidence": self.wear_confidence,
            "last_detection": self.last_detection_time,
            "time_since_last_detection": current_time - self.last_detection_time,
            "consecutive_detections": self.consecutive_detections,
            "wear_percentage_last_hour": round(wear_percentage, 1),
            "active_alerts": len(self.active_alerts),
            "total_alerts": len(self.alert_history),
            "detection_factors": self._get_latest_factors()
        }
    
    def get_wear_analytics(self) -> Dict[str, Any]:
        """Get wear analytics and insights."""
        if not self.wear_history:
            return {"message": "No wear data available"}
        
        # Calculate statistics
        total_entries = len(self.wear_history)
        worn_entries = [entry for entry in self.wear_history if entry['status'] == WearStatus.WORN.value]
        not_worn_entries = [entry for entry in self.wear_history if entry['status'] == WearStatus.NOT_WORN.value]
        
        wear_percentage = (len(worn_entries) / total_entries) * 100
        
        # Average confidence by status
        worn_confidence = np.mean([entry['confidence'] for entry in worn_entries]) if worn_entries else 0
        not_worn_confidence = np.mean([entry['confidence'] for entry in not_worn_entries]) if not_worn_entries else 0
        
        # Most common detection factors
        all_factors = {}
        for entry in self.wear_history:
            for factor, value in entry.get('factors', {}).items():
                if factor not in all_factors:
                    all_factors[factor] = []
                all_factors[factor].append(value)
        
        avg_factors = {}
        for factor, values in all_factors.items():
            avg_factors[factor] = np.mean(values)
        
        return {
            "overall_wear_percentage": round(wear_percentage, 1),
            "total_detections": total_entries,
            "worn_detections": len(worn_entries),
            "not_worn_detections": len(not_worn_entries),
            "average_confidence_worn": round(worn_confidence, 2),
            "average_confidence_not_worn": round(not_worn_confidence, 2),
            "detection_factors": avg_factors,
            "alert_frequency": len(self.alert_history) / max(1, (time.time() - self.wear_history[0]['timestamp']) / 3600)
        }

# Global wearable detection instance
_wearable_detection = None

def initialize_wearable_detection(backend_url: str = "http://localhost:5000/api", 
                                patient_id: str = "demo_patient") -> WearableDetectionSystem:
    """Initialize the global wearable detection system."""
    global _wearable_detection
    _wearable_detection = WearableDetectionSystem(backend_url, patient_id)
    return _wearable_detection

def get_wearable_detection() -> WearableDetectionSystem:
    """Get the global wearable detection instance."""
    return _wearable_detection

async def start_wearable_monitoring():
    """Start wearable detection monitoring in background."""
    if _wearable_detection:
        await _wearable_detection.start_monitoring()

def get_wear_status() -> Dict[str, Any]:
    """Get current wear status."""
    if _wearable_detection:
        return _wearable_detection.get_wear_status()
    return {"status": "not_initialized"}

def get_wear_analytics() -> Dict[str, Any]:
    """Get wear analytics."""
    if _wearable_detection:
        return _wearable_detection.get_wear_analytics()
    return {"error": "Wearable detection not initialized"}
