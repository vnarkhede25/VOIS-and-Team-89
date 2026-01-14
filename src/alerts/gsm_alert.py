import requests
from datetime import datetime
from typing import Dict, Optional

class GSMAlertSystem:
    """
    GSM emergency alert system for critical fall detection.
    Sends SMS alerts to emergency contacts and medical services.
    """
    
    def __init__(self, backend_url: str = "http://localhost:5000", patient_id: str = "default"):
        """
        Initialize GSM alert system.
        
        Args:
            backend_url: Backend API URL
            patient_id: Patient identifier
        """
        self.backend_url = backend_url
        self.patient_id = patient_id
        self.emergency_contacts = []
        self.last_emergency_alert = None
        
    def send_emergency_alert(self, alert_type: str, location: Dict = None, medical_info: Dict = None) -> bool:
        """
        Send emergency alert via GSM network.
        
        Args:
            alert_type: Type of emergency (fall, medical, etc.)
            location: Patient location information
            medical_info: Medical information for responders
            
        Returns:
            bool: True if alert sent successfully
        """
        try:
            emergency_data = {
                "patient_id": self.patient_id,
                "alert_type": "emergency",
                "emergency_type": alert_type,
                "timestamp": datetime.now().isoformat(),
                "location": location or {"coordinates": "Unknown"},
                "medical_info": medical_info or {},
                "priority": "critical"
            }
            
            # Send emergency alert to backend
            response = requests.post(
                f"{self.backend_url}/api/emergency",
                json=emergency_data,
                timeout=15
            )
            
            if response.status_code == 200:
                self.last_emergency_alert = datetime.now()
                print(f"🚨 EMERGENCY ALERT SENT: {alert_type}")
                return True
            else:
                print(f"❌ Failed to send emergency alert: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error sending emergency alert: {e}")
            return False
        except Exception as e:
            print(f"❌ Error sending emergency alert: {e}")
            return False
    
    def send_fall_emergency(self, impact_magnitude: float, posture: str, location: Dict = None) -> bool:
        """Send emergency alert for confirmed fall."""
        medical_info = {
            "injury_risk": "high" if impact_magnitude > 20 else "medium",
            "impact_force": impact_magnitude,
            "fall_position": posture,
            "consciousness": "unknown"
        }
        
        return self.send_emergency_alert(
            alert_type="fall",
            location=location,
            medical_info=medical_info
        )
    
    def get_emergency_status(self) -> Dict:
        """Get emergency alert system status."""
        return {
            "last_emergency_alert": self.last_emergency_alert.isoformat() if self.last_emergency_alert else None,
            "emergency_contacts_count": len(self.emergency_contacts),
            "backend_connected": self._test_backend_connection()
        }
    
    def _test_backend_connection(self) -> bool:
        """Test connection to backend API."""
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False

# Global GSM alert instance
_gsm_alert_system = None

def initialize_gsm_alerts(backend_url: str = "http://localhost:5000", patient_id: str = "default") -> GSMAlertSystem:
    """Initialize the global GSM alert system."""
    global _gsm_alert_system
    _gsm_alert_system = GSMAlertSystem(backend_url, patient_id)
    return _gsm_alert_system

def get_gsm_alert_system() -> Optional[GSMAlertSystem]:
    """Get the global GSM alert system instance."""
    return _gsm_alert_system

def send_gsm_alert(alert_type: str, location: Dict = None, medical_info: Dict = None) -> bool:
    """
    Legacy compatibility function for sending GSM alerts.
    
    Args:
        alert_type: Type of emergency alert
        location: Location information
        medical_info: Medical information
        
    Returns:
        bool: True if alert sent successfully
    """
    system = get_gsm_alert_system()
    if system:
        return system.send_emergency_alert(alert_type, location, medical_info)
    else:
        print("⚠️ GSM alert system not initialized")
        return False
