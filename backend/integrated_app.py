from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
CORS(app)

# In-memory data storage (simple for demo)
patients_db = {}
alerts_db = []
emergency_alerts = []
guardians_db = {}
elderly_db = {}
medicines_db = {}

# ========================================
# SILVERCARE INTEGRATED BACKEND
# ========================================

class PatientManager:
    """Enhanced patient management with SilverCare features"""
    
    def __init__(self):
        self.patients = {}
    
    def register_patient(self, patient_data):
        """Register a new patient with enhanced features."""
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
            'device_status': 'online',
            # SilverCare enhanced fields
            'risk_assessment': patient_data.get('risk_assessment', {}),
            'mobility': patient_data.get('mobility', 'independent'),
            'medical_conditions': patient_data.get('medical_conditions', []),
            'medications': patient_data.get('medications', ''),
            'location': patient_data.get('location', 'Home'),
            'device_id': patient_data.get('device_id', f"device_{patient_id}"),
            'language': patient_data.get('language', 'english')
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

class GuardianManager:
    """Guardian management system"""
    
    def __init__(self):
        self.guardians = {}
    
    def register_guardian(self, guardian_data):
        """Register a new guardian."""
        guardian_id = guardian_data.get('email', f"guardian_{len(self.guardians) + 1}")
        
        guardian = {
            'guardian_id': guardian_id,
            'name': guardian_data.get('name', ''),
            'email': guardian_data.get('email', ''),
            'phone': guardian_data.get('phone', ''),
            'password': guardian_data.get('password', ''),
            'registered_at': datetime.now().isoformat(),
            'elderly_patients': guardian_data.get('elderly_patients', []),
            'notifications': guardian_data.get('notifications', True)
        }
        
        self.guardians[guardian_id] = guardian
        return guardian
    
    def authenticate_guardian(self, email, password):
        """Authenticate guardian login."""
        for guardian in self.guardians.values():
            if guardian['email'] == email and guardian['password'] == password:
                return guardian
        return None
    
    def get_guardian_patients(self, guardian_id):
        """Get all patients linked to guardian."""
        guardian = self.guardians.get(guardian_id)
        if guardian:
            return [patient_manager.get_patient(pid) for pid in guardian['elderly_patients']]
        return []

class MedicineManager:
    """Medicine management system"""
    
    def __init__(self):
        self.medicines = {}
    
    def add_medicine(self, medicine_data):
        """Add medicine for patient."""
        patient_id = medicine_data.get('patient_id')
        if patient_id not in self.medicines:
            self.medicines[patient_id] = []
        
        medicine = {
            'medicine_id': f"med_{len(self.medicines[patient_id]) + 1}",
            'name': medicine_data.get('name', ''),
            'dosage': medicine_data.get('dosage', ''),
            'time': medicine_data.get('time', ''),
            'frequency': medicine_data.get('frequency', ''),
            'notes': medicine_data.get('notes', ''),
            'added_at': datetime.now().isoformat(),
            'taken': False
        }
        
        self.medicines[patient_id].append(medicine)
        return medicine
    
    def get_patient_medicines(self, patient_id):
        """Get all medicines for patient."""
        return self.medicines.get(patient_id, [])
    
    def confirm_medicine(self, patient_id, medicine_id):
        """Mark medicine as taken."""
        if patient_id in self.medicines:
            for medicine in self.medicines[patient_id]:
                if medicine['medicine_id'] == medicine_id:
                    medicine['taken'] = True
                    medicine['taken_at'] = datetime.now().isoformat()
                    return medicine
        return None

class AlertManager:
    """Enhanced alert management with SilverCare features"""
    
    def __init__(self):
        self.alerts = []
        self.emergency_alerts = []
    
    def create_alert(self, alert_data):
        """Create a new alert with enhanced features."""
        alert = {
            'alert_id': alert_data.get('alert_id', f"alert_{len(self.alerts) + 1}"),
            'patient_id': alert_data.get('patient_id'),
            'alert_type': alert_data.get('alert_type'),
            'severity': alert_data.get('severity'),
            'timestamp': alert_data.get('timestamp', datetime.now().isoformat()),
            'details': alert_data.get('details', {}),
            'status': 'active',
            'acknowledged': False,
            # SilverCare enhanced fields
            'device_id': alert_data.get('device_id'),
            'confidence': alert_data.get('confidence', 1.0),
            'location': alert_data.get('location', {}),
            'guardian_notified': False,
            'emergency_services_notified': False
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
            'responders_notified': False,
            'guardian_notified': False,
            'emergency_services_notified': False
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
guardian_manager = GuardianManager()
medicine_manager = MedicineManager()
alert_manager = AlertManager()

# ========================================
# ENHANCED API ENDPOINTS
# ========================================

# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'features': ['patient_management', 'guardian_auth', 'medicine_management', 'fall_detection', 'alerts', 'health_monitoring', 'voice_assistant']
    })

# ========================================
# HEALTH MONITORING ENDPOINTS
# ========================================

@app.route('/api/health/vitals/<patient_id>', methods=['GET'])
def get_patient_vitals(patient_id):
    """Get patient health vitals."""
    try:
        # Simulated vitals data
        vitals = {
            'heart_rate': {
                'value': 72,
                'unit': 'bpm',
                'timestamp': datetime.now().isoformat(),
                'status': 'normal'
            },
            'blood_pressure': {
                'systolic': 120,
                'diastolic': 80,
                'unit': 'mmHg',
                'timestamp': datetime.now().isoformat(),
                'status': 'normal'
            },
            'temperature': {
                'value': 98.6,
                'unit': '°F',
                'timestamp': datetime.now().isoformat(),
                'status': 'normal'
            },
            'steps': {
                'value': 3245,
                'unit': 'steps',
                'timestamp': datetime.now().isoformat(),
                'status': 'active'
            },
            'sleep_quality': {
                'value': 85,
                'unit': 'percent',
                'timestamp': datetime.now().isoformat(),
                'status': 'good'
            },
            'stress_level': {
                'value': 25,
                'unit': 'percent',
                'timestamp': datetime.now().isoformat(),
                'status': 'low'
            }
        }
        
        return jsonify({
            'success': True,
            'patient_id': patient_id,
            'vitals': vitals,
            'last_updated': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/activity/<patient_id>', methods=['GET'])
def get_patient_activity(patient_id):
    """Get patient activity data."""
    try:
        time_range = request.args.get('range', 'today')
        
        # Simulated activity data
        activities = {
            'today': {
                'steps': 3245,
                'active_minutes': 45,
                'calories': 180,
                'distance': 2.1
            },
            'week': {
                'steps': 22715,
                'active_minutes': 315,
                'calories': 1260,
                'distance': 14.7
            },
            'month': {
                'steps': 90860,
                'active_minutes': 1260,
                'calories': 5040,
                'distance': 58.8
            }
        }
        
        return jsonify({
            'success': True,
            'patient_id': patient_id,
            'time_range': time_range,
            'activity': activities.get(time_range, activities['today']),
            'last_updated': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========================================
# GUARDIAN AUTHENTICATION
# ========================================

@app.route('/api/guardians/register', methods=['POST'])
def register_guardian():
    """Register a new guardian."""
    try:
        guardian_data = request.get_json()
        guardian = guardian_manager.register_guardian(guardian_data)
        return jsonify({
            'success': True,
            'guardian': guardian,
            'message': 'Guardian registered successfully'
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/guardians/login', methods=['POST'])
def login_guardian():
    """Guardian login endpoint."""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        guardian = guardian_manager.authenticate_guardian(email, password)
        if guardian:
            return jsonify({
                'success': True,
                'guardian': guardian,
                'message': 'Login successful'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid credentials'
            }), 401
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# ========================================
# PATIENT MANAGEMENT (Enhanced)
# ========================================

@app.route('/api/patients/register', methods=['POST'])
def register_patient():
    """Register a new patient with enhanced features."""
    try:
        patient_data = request.get_json()
        patient = patient_manager.register_patient(patient_data)
        
        # Link to guardian if specified
        guardian_email = patient_data.get('guardian_email')
        if guardian_email:
            for guardian_id, guardian in guardian_manager.guardians.items():
                if guardian['email'] == guardian_email:
                    guardian['elderly_patients'].append(patient['patient_id'])
                    break
        
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
        # Add medicines to patient data
        patient['medicines'] = medicine_manager.get_patient_medicines(patient_id)
        return jsonify({
            'success': True,
            'patient': patient
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Patient not found'
        }), 404

@app.route('/api/patients', methods=['GET'])
def get_all_patients():
    """Get all patients."""
    patients = patient_manager.get_all_patients()
    return jsonify({
        'success': True,
        'patients': patients,
        'count': len(patients)
    })

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

# ========================================
# MEDICINE MANAGEMENT
# ========================================

@app.route('/api/medicines/add', methods=['POST'])
def add_medicine():
    """Add medicine for patient."""
    try:
        medicine_data = request.get_json()
        medicine = medicine_manager.add_medicine(medicine_data)
        return jsonify({
            'success': True,
            'medicine': medicine,
            'message': 'Medicine added successfully'
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/medicines/<patient_id>', methods=['GET'])
def get_medicines(patient_id):
    """Get all medicines for patient."""
    medicines = medicine_manager.get_patient_medicines(patient_id)
    return jsonify({
        'success': True,
        'medicines': medicines,
        'count': len(medicines)
    })

@app.route('/api/medicines/confirm', methods=['POST'])
def confirm_medicine():
    """Mark medicine as taken."""
    try:
        data = request.get_json()
        patient_id = data.get('patient_id')
        medicine_id = data.get('medicine_id')
        
        medicine = medicine_manager.confirm_medicine(patient_id, medicine_id)
        if medicine:
            return jsonify({
                'success': True,
                'medicine': medicine,
                'message': 'Medicine confirmed as taken'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Medicine not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# ========================================
# FALL DETECTION (SilverCare Integration)
# ========================================

@app.route('/api/fall/detect', methods=['POST'])
def detect_fall():
    """Enhanced fall detection endpoint."""
    try:
        data = request.get_json()
        device_id = data.get("device_id", "unknown")
        confidence = data.get("confidence", 1.0)
        patient_id = data.get("patient_id")
        
        print(f"[FALL DETECTED] Device: {device_id}, Patient: {patient_id}, Confidence: {confidence}")
        
        # Create alert
        alert_data = {
            'alert_type': 'fall',
            'severity': 'critical',
            'details': {
                'detection_method': 'hardware_sensors',
                'confidence': confidence,
                'device_id': device_id
            },
            'device_id': device_id,
            'patient_id': patient_id,
            'confidence': confidence
        }
        
        alert = alert_manager.create_alert(alert_data)
        
        # Create emergency alert
        emergency_data = {
            'patient_id': patient_id,
            'emergency_type': 'fall_detected',
            'location': data.get('location', {}),
            'medical_info': data.get('medical_info', {})
        }
        
        alert_manager.create_emergency_alert(emergency_data)
        
        return jsonify({
            'status': 'success',
            'message': 'Fall detected and alert triggered',
            'alert': alert,
            'device_id': device_id
        }), 200
    except Exception as e:
        print(f"Error processing fall detection: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/fall/status', methods=['GET'])
def get_fall_status():
    """Get fall detection status."""
    recent_alerts = alert_manager.get_recent_alerts(hours=1)
    active_falls = [alert for alert in recent_alerts if alert['alert_type'] == 'fall' and alert['status'] == 'active']
    
    return jsonify({
        'status': 'success',
        'active_falls': len(active_falls),
        'recent_falls': len(recent_alerts),
        'last_fall': recent_alerts[0] if recent_alerts else None
    })

# ========================================
# ALERTS (Enhanced)
# ========================================

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

@app.route('/api/dashboard/<patient_id>', methods=['GET'])
def get_patient_dashboard(patient_id):
    """Get comprehensive patient dashboard."""
    try:
        patient = patient_manager.get_patient(patient_id)
        if not patient:
            return jsonify({
                'success': False,
                'error': 'Patient not found'
            }), 404
        
        recent_alerts = alert_manager.get_patient_alerts(patient_id, 10)
        medicines = medicine_manager.get_patient_medicines(patient_id)
        
        return jsonify({
            'success': True,
            'patient': patient,
            'recent_alerts': recent_alerts,
            'medicines': medicines,
            'alert_count': len(recent_alerts),
            'critical_alerts': len([a for a in recent_alerts if a['severity'] == 'critical']),
            'pending_medicines': len([m for m in medicines if not m['taken']])
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========================================
# LEGACY CHAT ENDPOINT
# ========================================

@app.route("/chat", methods=["POST"])
def chat():
    """Enhanced chat endpoint with context awareness."""
    print("--- MESSAGE RECEIVED ---")
    data = request.get_json()
    user_message = data.get("message", "")
    print(f"User said: {user_message}")
    
    # Enhanced responses based on context
    if "medicine" in user_message.lower():
        responses = [
            "I can help you manage your medicines. Check your medicine reminders in the app.",
            "Your medicines are listed in your profile. Have you taken them today?",
            "I can remind you about your medicines. What would you like to know?"
        ]
    elif "fall" in user_message.lower() or "help" in user_message.lower():
        responses = [
            "I'm here to help! If you've fallen, I've already notified your guardian.",
            "Don't worry, help is on the way. Your guardian has been notified.",
            "I'm monitoring your safety. Your emergency contacts have been alerted if needed."
        ]
    elif "guardian" in user_message.lower():
        responses = [
            "Your guardian is monitoring your safety and will be alerted if needed.",
            "I can connect you with your guardian if you need assistance.",
            "Your guardian cares about your safety and will be notified of any issues."
        ]
    else:
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

# ========================================
# MAIN APPLICATION STARTUP
# ========================================

if __name__ == "__main__":
    print("🚀 Starting Enhanced SilverCare Backend Server...")
    print("📊 Available endpoints:")
    print("  Health & System:")
    print("    GET  /api/health - Health check")
    print("  Guardian Management:")
    print("    POST /api/guardians/register - Register guardian")
    print("    POST /api/guardians/login - Guardian login")
    print("  Patient Management:")
    print("    POST /api/patients/register - Register patient")
    print("    GET  /api/patients/<id> - Get patient info")
    print("    PUT  /api/patients/<id>/status - Update patient status")
    print("    GET  /api/patients - Get all patients")
    print("  Medicine Management:")
    print("    POST /api/medicines/add - Add medicine")
    print("    GET  /api/medicines/<id> - Get patient medicines")
    print("    POST /api/medicines/confirm - Confirm medicine taken")
    print("  Fall Detection:")
    print("    POST /api/fall/detect - Hardware fall detection")
    print("    GET  /api/fall/status - Get fall status")
    print("  Alerts & Monitoring:")
    print("    POST /api/alerts - Create alert")
    print("    GET  /api/alerts/recent - Get recent alerts")
    print("    POST /api/alerts/<id>/acknowledge - Acknowledge alert")
    print("    GET  /api/patients/<id>/alerts - Get patient alerts")
    print("    GET  /api/dashboard/<id> - Get patient dashboard")
    print("  Chat:")
    print("    POST /chat - Enhanced chat endpoint")
    print()
    
    app.run(port=5000, debug=True)
