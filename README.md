# SilverCare - Elderly Fall Detection System

A comprehensive fall detection system designed for senior citizens, featuring real-time monitoring, human-friendly alerts, and continuous learning capabilities.

## 🎯 Problem Statement

Falls among elderly adults (65+) are a major public health concern:
- **1 in 4** older adults fall each year
- Falls are the **leading cause of injury** in this age group
- **95% of hip fractures** are caused by falls
- **Fear of falling** leads to reduced activity and social isolation
- **Response time is critical** - medical attention within the "golden hour" significantly improves outcomes

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Required packages: `numpy`, `flask`, `flask-cors`, `requests`

### Installation
```bash
# Clone the repository
git clone https://github.com/your-repo/vois-and-team-89.git
cd vois-and-team-89

# Install dependencies
pip install -r requirements.txt
```

### Running the System

#### 1. Start the Backend Server
```bash
cd backend
python app.py
```
The backend will start on `http://localhost:5000` with the following endpoints:
- `GET /api/health` - Health check
- `POST /api/patients/register` - Register patient
- `POST /api/alerts` - Create alert
- `GET /api/dashboard/<patient_id>` - Patient dashboard

#### 2. Start the Fall Detection System

**Demo Mode (Recommended for first run):**
```bash
cd src
python main.py --demo
```
This runs a 1-minute demo with automatic fall simulation.

**Normal Mode:**
```bash
cd src
python main.py
```
This runs real-time monitoring with simulated sensor data.

**With Real Hardware:**
```bash
cd src
python main.py --hardware
```
This uses real MPU6050 sensor via USB connection.

#### 3. Open the Web Interfaces

**Guardian Dashboard:**
Open `frontend/guardian_dashboard.html` in your browser
- View patient status and alerts
- Acknowledge alerts
- Monitor multiple patients

**Senior Citizen UI:**
Open `frontend/senior_ui.html` in your browser
- Device status monitoring
- Alert cancellation
- Demo controls for testing

**Companion Chatbot:**
Open `frontend/test.html` in your browser
- Senior-friendly chat interface
- Voice synthesis support

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MPU6050      │    │   Feature       │    │   Decision      │
│   Sensor        │───▶│   Extraction    │───▶│   Engine        │
│   (ax, ay, az)  │    │   (22 features) │    │   (State Machine)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Hardware      │    │   Alert         │    │   Backend       │
│   Abstraction   │───▶│   Controller    │───▶│   APIs          │
│   Layer         │    │   (Local+Remote)│    │   (Storage)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Hardware Integration

### Current Setup (Simulation)
- Uses simulated MPU6050 sensor data
- No physical hardware required
- Perfect for development and testing

### Production Setup (Real Hardware)
**Required Hardware:**
- ESP32 microcontroller with WiFi + Bluetooth
- MPU6050 6-axis IMU sensor
- Rechargeable battery (24+ hour life)
- Buzzer/vibration motor for local alerts

**Connection Steps:**
1. Connect MPU6050 to ESP32 (I2C)
2. Flash ESP32 with provided firmware
3. Connect ESP32 to computer via USB
4. Run system with `--hardware` flag

**ESP32 Firmware (to be implemented):**
```cpp
// Pseudo-code for ESP32
void setup() {
  Serial.begin(115200);
  mpu6050.initialize();
}

void loop() {
  if (Serial.available() && Serial.readString() == "GET_DATA") {
    ax, ay, az = mpu6050.getAcceleration();
    Serial.println("ACC:" + String(ax) + "," + String(ay) + "," + String(az));
  }
}
```

## 🎮 Demo Mode Features

The demo mode provides a complete product demonstration:

### Automatic Demo Sequence
1. **Normal State** (30 seconds) - System monitors normal movement
2. **Fall Detection** (10 seconds) - Simulated fall with impact
3. **Post-Fall State** (20 seconds) - Lying posture detection

### Manual Demo Controls
In the Senior UI, use the demo controls to:
- **Normal** - Simulate normal standing
- **Sitting** - Simulate sitting posture
- **Unstable** - Simulate pre-fall instability
- **Fall** - Trigger immediate fall simulation

### Alert Testing
- Guardian alerts appear in dashboard
- Emergency alerts for critical falls
- Real-time status updates

## 📊 Key Features

### 🎯 Advanced Detection Algorithms
- **Multi-stage fall detection**: Spike detection → Inactivity confirmation → Posture verification
- **Pre-fall instability detection**: Identifies dangerous movement patterns before falls occur
- **3D posture classification**: Uses gravity vector analysis for accurate orientation detection
- **Noise-resistant smoothing**: Moving average filters prevent false triggers from sensor spikes
- **Comfort-aware alerts**: Suppresses alarms during sleep and normal sitting transitions

### 🤖 Human-Centric Interaction
- **Senior-friendly chatbot**: Simple language, adaptive tone, wellbeing questions
- **Comfort constraints**: Sleep suppression, sitting transition filtering, rate limiting
- **User cancellation**: 10-second window to prevent false alarms
- **Dignity preservation**: Avoids embarrassing alerts during normal activities

### 📈 Real-time Monitoring
- **Guardian dashboard**: Live patient status and alert history
- **Senior UI**: Device status and alert management
- **Backend APIs**: Patient registration, alert management, status tracking
- **Data persistence**: In-memory storage with easy database integration

## 🔧 Configuration

### Detection Thresholds
```python
# Fall detection thresholds
SPIKE_THRESHOLD = 18.0          # g-force for fall detection
RECOVERY_THRESHOLD = 12.0        # g-force for post-fall recovery
INACTIVITY_TOLERANCE = 0.3        # g-force variance for inactivity

# Risk thresholds
LOW_RISK = 0.3                   # Normal daily activities
MEDIUM_RISK = 0.6                 # Unusual movement
HIGH_RISK = 0.8                   # Pre-fall patterns
```

### Alert Configuration
```python
# Comfort constraints
SLEEP_SUPPRESSION = True           # Suppress alerts during sleep
SITTING_FILTER = True            # Filter sitting transitions
RATE_LIMITING = True              # Prevent alert fatigue
MIN_ALERT_INTERVAL = 30           # Seconds between alerts
```

## 🛠️ Development

### Project Structure
```
vois-and-team-89/
├── src/                    # Core detection system
│   ├── sensors/            # Hardware abstraction layer
│   ├── detection/         # ML and detection algorithms
│   ├── decision_engine/    # State machine and rules
│   ├── alerts/            # Alert management
│   └── main.py           # Main entry point
├── backend/               # Flask API server
├── frontend/             # Web interfaces
├── ml/                   # ML models and data
└── data/                 # Training data
```

### Running Tests
```bash
# Test individual components
python src/detection/test_fall_detection.py
python src/decision_engine/test_state_machine.py
python src/alerts/test_alert_controller.py

# Test feature extraction
python src/detection/test_feature_extraction.py

# Test ML inference
python src/detection/test_tinyml_inference.py
```

## 📱 API Reference

### Patient Management
```bash
# Register patient
curl -X POST http://localhost:5000/api/patients/register \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "user123", "name": "John Doe", "age": 75}'

# Get patient info
curl http://localhost:5000/api/patients/user123

# Update patient status
curl -X PUT http://localhost:5000/api/patients/user123/status \
  -H "Content-Type: application/json" \
  -d '{"status": "active", "device_status": "online"}'
```

### Alert Management
```bash
# Create alert
curl -X POST http://localhost:5000/api/alerts \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "user123", "alert_type": "fall", "severity": "critical"}'

# Get patient alerts
curl http://localhost:5000/api/patients/user123/alerts

# Get recent alerts
curl http://localhost:5000/api/alerts/recent?hours=24

# Acknowledge alert
curl -X POST http://localhost:5000/api/alerts/alert123/acknowledge
```

## 🔮 Future Development

### Phase 1: Production Ready (Current ✅)
- [x] Core detection algorithms
- [x] Human-friendly interface
- [x] Learning pipeline
- [x] Comprehensive testing
- [x] Hardware abstraction layer
- [x] Backend APIs
- [x] Web interfaces

### Phase 2: Enhanced Features
- [ ] Mobile application development
- [ ] Cloud platform integration
- [ ] Multi-patient support
- [ ] Advanced analytics dashboard

### Phase 3: Advanced Intelligence
- [ ] Machine learning model training
- [ ] Predictive analytics
- [ ] Behavioral pattern recognition
- [ ] Emergency response automation

## 🏆 Safety & Compliance

### Safety Mechanisms
- **Redundant detection**: Multiple criteria must be met before fall confirmation
- **False alarm prevention**: Temporal validation and user cancellation options
- **Fail-safe default**: System defaults to safe state on errors
- **Privacy protection**: Local processing with optional cloud sync

### Medical Device Considerations
- **IEC 60601-1**: Basic safety requirements for medical electrical equipment
- **FDA Class II**: Medical device classification for fall detection systems
- **HIPAA Compliance**: Patient data protection and privacy standards
- **ISO 13485**: Quality management system for medical devices

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Team
- **Project Lead**: VOIS and Team 89
- **Technical Lead**: Fall Detection System Architecture
- **UI/UX Lead**: Senior-Friendly Interface Design
- **Testing Lead**: Comprehensive Validation Framework

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🎯 Demo Instructions for Judges

### Quick Demo (5 minutes)
1. **Start Backend**: `cd backend && python app.py`
2. **Start Detection System**: `cd src && python main.py --demo`
3. **Open Guardian Dashboard**: Open `frontend/guardian_dashboard.html`
4. **Open Senior UI**: Open `frontend/senior_ui.html`
5. **Watch Demo**: The system will automatically simulate a fall after 30 seconds

### Interactive Demo (10 minutes)
1. Follow Quick Demo steps 1-3
2. In Senior UI, use manual demo controls:
   - Click "Normal" → See safe status
   - Click "Unstable" → See pre-fall warning
   - Click "Fall" → See full alert sequence
3. Observe alerts appearing in Guardian Dashboard
4. Try acknowledging alerts in the dashboard

### Production Demo
To connect real hardware:
1. Replace `--demo` with `--hardware` flag
2. Connect ESP32 via USB
3. System will use real sensor data

---

**Note**: This is a demonstration system designed for educational and prototype purposes. For production use, ensure proper medical device certification and regulatory compliance.