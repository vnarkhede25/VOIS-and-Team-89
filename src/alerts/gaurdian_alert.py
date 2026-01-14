import requests
import json
from datetime import datetime
from typing import Dict, Optional

class GuardianAlertSystem:
    """
    Real guardian alert system with backend API integration.
    Sends alerts to guardians via backend API with escalation logic.
    """
    
    def __init__(self, backend_url: str = "http://localhost:5000", patient_id: str = "default"):
        """
        Initialize guardian alert system.
        
        Args:
            backend_url: Backend API URL
            patient_id: Patient identifier
        """
        self.backend_url = backend_url
        self.patient_id = patient_id
        self.last_alert_time = None
        self.alert_count = 0
        
    def send_guardian_alert(self, alert_type: str, severity: str, details: Dict) -> bool:
        """
        Send alert to guardian via backend API.
        
        Args:
            alert_type: Type of alert (fall, instability, inactivity)
            severity: Severity level (low, medium, high, critical)
            details: Additional alert details
            
        Returns:
            bool: True if alert sent successfully
        """
        try:
            alert_data = {
                "patient_id": self.patient_id,
                "alert_type": alert_type,
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
                "details": details,
                "alert_id": f"{self.patient_id}_{int(datetime.now().timestamp())}"
            }
            
            # Send to backend API
            response = requests.post(
                f"{self.backend_url}/api/alerts",
                json=alert_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.last_alert_time = datetime.now()
                self.alert_count += 1
                print(f"✅ Guardian alert sent: {alert_type} ({severity})")
                return True
            else:
                print(f"❌ Failed to send guardian alert: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error sending guardian alert: {e}")
            return False
        except Exception as e:
            print(f"❌ Error sending guardian alert: {e}")
            return False
    
    def send_fall_alert(self, posture: str, impact_magnitude: float) -> bool:
        """Send fall detection alert."""
        return self.send_guardian_alert(
            alert_type="fall",
            severity="critical",
            details={
                "posture": posture,
                "impact_magnitude": impact_magnitude,
                "description": f"Fall detected while {posture} with impact {impact_magnitude:.2f}g"
            }
        )
    
    def send_instability_alert(self, risk_score: float, risk_state: str) -> bool:
        """Send pre-fall instability alert."""
        severity = "high" if risk_score > 0.8 else "medium" if risk_score > 0.6 else "low"
        return self.send_guardian_alert(
            alert_type="instability",
            severity=severity,
            details={
                "risk_score": risk_score,
                "risk_state": risk_state,
                "description": f"Pre-fall instability detected: {risk_state} risk ({risk_score:.2f})"
            }
        )
    
    def send_inactivity_alert(self, duration_minutes: int, posture: str) -> bool:
        """Send prolonged inactivity alert."""
        severity = "medium" if duration_minutes < 60 else "high"
        return self.send_guardian_alert(
            alert_type="inactivity",
            severity=severity,
            details={
                "duration_minutes": duration_minutes,
                "posture": posture,
                "description": f"Prolonged inactivity: {duration_minutes} minutes in {posture} position"
            }
        )
    
    def get_alert_status(self) -> Dict:
        """Get current alert system status."""
        return {
            "last_alert_time": self.last_alert_time.isoformat() if self.last_alert_time else None,
            "alert_count": self.alert_count,
            "backend_connected": self._test_backend_connection()
        }
    
    def _test_backend_connection(self) -> bool:
        """Test connection to backend API."""
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False

# Global guardian alert instance
_guardian_alert_system = None

def initialize_guardian_alerts(backend_url: str = "http://localhost:5000", patient_id: str = "default") -> GuardianAlertSystem:
    """Initialize the global guardian alert system."""
    global _guardian_alert_system
    _guardian_alert_system = GuardianAlertSystem(backend_url, patient_id)
    return _guardian_alert_system

def get_guardian_alert_system() -> Optional[GuardianAlertSystem]:
    """Get the global guardian alert system instance."""
    return _guardian_alert_system

def send_guardian_alert(alert_type: str, severity: str, details: Dict) -> bool:
    """
    Legacy compatibility function for sending guardian alerts.
    
    Args:
        alert_type: Type of alert
        severity: Severity level
        details: Alert details
        
    Returns:
        bool: True if alert sent successfully
    """
    system = get_guardian_alert_system()
    if system:
        return system.send_guardian_alert(alert_type, severity, details)
    else:
        print("⚠️ Guardian alert system not initialized")
        return False
