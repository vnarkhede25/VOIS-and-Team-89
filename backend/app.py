from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os

# Import SilverCare modules
from SilverCare.backend.fall_detection import fall_detection_bp
from SilverCare.backend.guardian_auth import guardian_auth_bp
from SilverCare.backend.elderly_management import elderly_management_bp
from SilverCare.backend.medicine_management import medicine_bp
from SilverCare.backend.suggestions_management import suggestions_bp

app = Flask(__name__)
CORS(app)

# Register SilverCare blueprints
app.register_blueprint(fall_detection_bp, url_prefix='/silvercare')
app.register_blueprint(guardian_auth_bp, url_prefix='/silvercare')
app.register_blueprint(elderly_management_bp, url_prefix='/silvercare')
app.register_blueprint(medicine_bp, url_prefix='/silvercare')
app.register_blueprint(suggestions_bp, url_prefix='/silvercare')

# In-memory data storage (simple for demo)
patients_db = {}
alerts_db = []
emergency_alerts = []

class PatientManager:
    """Manages patient registration and status tracking."""
    
    def __init__(self):
        self.patients = {}
    
    def register_patient(self, patient_data):
        """Register a new patient."""
        patient_id = patient_data.get('patient_id', f"patient_{len(self.patients) + 1}")
        
        patient = {
            'patient_id': patient_id,
            'name': patient_data.get('name', 'Unknown'),
            'age': patient_data.get('age', 0),
            'medical_info': patient_data.get('medical_info', {}),
            'emergency_contacts': patient_data.get('emergency_contacts', []),
            'guardians': patient_data.get('guardians', []),
            'registered_at': datetime.now().isoformat(),
            'status': 'active',
            'last_seen': datetime.now().isoformat(),
            'device_status': 'online'
        }
        
        self.patients[patient_id] = patient
        return patient
    
    def get_patient(self, patient_id):
        """Get patient information."""
        return self.patients.get(patient_id)
    
    def update_patient_status(self, patient_id, status_data):
        """Update patient status."""
        if patient_id in self.patients:
            self.patients[patient_id].update(status_data)
            self.patients[patient_id]['last_seen'] = datetime.now().isoformat()
            return self.patients[patient_id]
        return None
    
    def get_all_patients(self):
        """Get all patients."""
        return list(self.patients.values())

class AlertManager:
    """Manages alerts and emergency notifications."""
    
    def __init__(self):
        self.alerts = []
        self.emergency_alerts = []
    
    def create_alert(self, alert_data):
        """Create a new alert."""
        alert = {
            'alert_id': alert_data.get('alert_id', f"alert_{len(self.alerts) + 1}"),
            'patient_id': alert_data.get('patient_id'),
            'alert_type': alert_data.get('alert_type'),
            'severity': alert_data.get('severity'),
            'timestamp': alert_data.get('timestamp', datetime.now().isoformat()),
            'details': alert_data.get('details', {}),
            'status': 'active',
            'acknowledged': False
        }
        
        self.alerts.append(alert)
        return alert
    
    def create_emergency_alert(self, emergency_data):
        """Create emergency alert."""
        emergency = {
            'emergency_id': f"emergency_{len(self.emergency_alerts) + 1}",
            'patient_id': emergency_data.get('patient_id'),
            'emergency_type': emergency_data.get('emergency_type'),
            'timestamp': emergency_data.get('timestamp', datetime.now().isoformat()),
            'location': emergency_data.get('location', {}),
            'medical_info': emergency_data.get('medical_info', {}),
            'priority': emergency_data.get('priority', 'critical'),
            'status': 'active',
            'responders_notified': False
        }
        
        self.emergency_alerts.append(emergency)
        return emergency
    
    def get_patient_alerts(self, patient_id, limit=50):
        """Get alerts for a specific patient."""
        patient_alerts = [alert for alert in self.alerts if alert['patient_id'] == patient_id]
        return sorted(patient_alerts, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_recent_alerts(self, hours=24, limit=100):
        """Get recent alerts."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [
            alert for alert in self.alerts 
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]
        return sorted(recent_alerts, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def acknowledge_alert(self, alert_id):
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert['alert_id'] == alert_id:
                alert['acknowledged'] = True
                alert['status'] = 'acknowledged'
                return alert
        return None

# Initialize managers
patient_manager = PatientManager()
alert_manager = AlertManager()

# API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/patients/register', methods=['POST'])
def register_patient():
    """Register a new patient."""
    try:
        patient_data = request.get_json()
        patient = patient_manager.register_patient(patient_data)
        return jsonify({
            'success': True,
            'patient': patient,
            'message': 'Patient registered successfully'
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/patients/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Get patient information."""
    patient = patient_manager.get_patient(patient_id)
    if patient:
        return jsonify({
            'success': True,
            'patient': patient
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Patient not found'
        }), 404

@app.route('/api/patients/<patient_id>/status', methods=['PUT'])
def update_patient_status(patient_id):
    """Update patient status."""
    try:
        status_data = request.get_json()
        patient = patient_manager.update_patient_status(patient_id, status_data)
        if patient:
            return jsonify({
                'success': True,
                'patient': patient
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Patient not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/patients', methods=['GET'])
def get_all_patients():
    """Get all patients."""
    patients = patient_manager.get_all_patients()
    return jsonify({
        'success': True,
        'patients': patients,
        'count': len(patients)
    })

@app.route('/api/alerts', methods=['POST'])
def create_alert():
    """Create a new alert."""
    try:
        alert_data = request.get_json()
        alert = alert_manager.create_alert(alert_data)
        return jsonify({
            'success': True,
            'alert': alert,
            'message': 'Alert created successfully'
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/emergency', methods=['POST'])
def create_emergency_alert():
    """Create emergency alert."""
    try:
        emergency_data = request.get_json()
        emergency = alert_manager.create_emergency_alert(emergency_data)
        return jsonify({
            'success': True,
            'emergency': emergency,
            'message': 'Emergency alert created successfully'
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/patients/<patient_id>/alerts', methods=['GET'])
def get_patient_alerts(patient_id):
    """Get alerts for a specific patient."""
    limit = request.args.get('limit', 50, type=int)
    alerts = alert_manager.get_patient_alerts(patient_id, limit)
    return jsonify({
        'success': True,
        'alerts': alerts,
        'count': len(alerts)
    })

@app.route('/api/alerts/recent', methods=['GET'])
def get_recent_alerts():
    """Get recent alerts."""
    hours = request.args.get('hours', 24, type=int)
    limit = request.args.get('limit', 100, type=int)
    alerts = alert_manager.get_recent_alerts(hours, limit)
    return jsonify({
        'success': True,
        'alerts': alerts,
        'count': len(alerts)
    })

@app.route('/api/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert."""
    alert = alert_manager.acknowledge_alert(alert_id)
    if alert:
        return jsonify({
            'success': True,
            'alert': alert,
            'message': 'Alert acknowledged successfully'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Alert not found'
        }), 404

@app.route('/api/dashboard/<patient_id>', methods=['GET'])
def get_patient_dashboard(patient_id):
    """Get patient dashboard data."""
    try:
        patient = patient_manager.get_patient(patient_id)
        if not patient:
            return jsonify({
                'success': False,
                'error': 'Patient not found'
            }), 404
        
        recent_alerts = alert_manager.get_patient_alerts(patient_id, 10)
        
        return jsonify({
            'success': True,
            'patient': patient,
            'recent_alerts': recent_alerts,
            'alert_count': len(recent_alerts),
            'critical_alerts': len([a for a in recent_alerts if a['severity'] == 'critical'])
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route("/chat", methods=["POST"])
def chat():
    """Legacy chat endpoint - simple fallback response."""
    print("--- MESSAGE RECEIVED ---")
    data = request.get_json()
    user_message = data.get("message", "")
    print(f"User said: {user_message}")
    
    # Simple fallback response
    responses = [
        "I'm here to help you! How are you feeling today?",
        "That's interesting. Tell me more about how you're doing.",
        "I'm listening. What would you like to talk about?",
        "Thank you for sharing that. How can I support you?",
        "I care about you. Is there anything specific you need?"
    ]
    
    import random
    reply = random.choice(responses)
    
    return jsonify({"reply": reply})

if __name__ == "__main__":
    print("🚀 Starting SilverCare Backend Server...")
    print("📊 Available endpoints:")
    print("  GET  /api/health - Health check")
    print("  POST /api/patients/register - Register patient")
    print("  GET  /api/patients/<id> - Get patient info")
    print("  PUT  /api/patients/<id>/status - Update patient status")
    print("  GET  /api/patients - Get all patients")
    print("  POST /api/alerts - Create alert")
    print("  POST /api/emergency - Create emergency alert")
    print("  GET  /api/patients/<id>/alerts - Get patient alerts")
    print("  GET  /api/alerts/recent - Get recent alerts")
    print("  POST /api/alerts/<id>/acknowledge - Acknowledge alert")
    print("  GET  /api/dashboard/<id> - Get patient dashboard")
    print("  POST /chat - Legacy chat endpoint")
    print()
    
    app.run(port=5000, debug=True)