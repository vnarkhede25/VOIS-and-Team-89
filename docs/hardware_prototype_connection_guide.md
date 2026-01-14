# 🔌 **HARDWARE PROTOTYPE CONNECTION GUIDE**

## 📋 **Connecting Your Hardware Prototype to the Project**

This guide will help you connect your physical hardware prototype with all wires to the elderly monitoring system.

## 🛠️ **Hardware Components Needed**

### **Required Sensors & Components:**
- **ESP32 Development Board** (main microcontroller)
- **MPU6050** (6-axis IMU sensor - accelerometer + gyroscope)
- **MAX30102** (Heart rate & SpO₂ sensor)
- **DS18B20** (Temperature sensor)
- **Buzzer** (Local alert system)
- **SIM800L** (GSM module for SMS/calls)
- **Li-ion Battery** (3.7V, 1000mAh+)
- **Charging Circuit** (USB-C charging)
- **Waist band enclosure** (comfortable wearable housing)

## 🔌 **Wiring Connections**

### **1. ESP32 to MPU6050 (IMU Sensor)**
```
ESP32 Pin    →    MPU6050 Pin    →    Purpose
3V3          →    VCC           →    Power (3.3V)
GND           →    GND           →    Ground
GPIO22        →    SDA           →    I2C Data
GPIO21        →    SCL           →    I2C Clock
```

### **2. ESP32 to MAX30102 (Heart Rate Sensor)**
```
ESP32 Pin    →    MAX30102 Pin   →    Purpose
3V3          →    VIN           →    Power (3.3V)
GND           →    GND           →    Ground
GPIO23        →    SDA           →    I2C Data
GPIO22        →    SCL           →    I2C Clock
```

### **3. ESP32 to DS18B20 (Temperature Sensor)**
```
ESP32 Pin    →    DS18B20 Pin    →    Purpose
3V3          →    VDD            →    Power (3.3V)
GND           →    GND            →    Ground
GPIO4         →    DQ             →    Data (with 4.7kΩ pull-up)
```

### **4. ESP32 to Buzzer (Local Alerts)**
```
ESP32 Pin    →    Buzzer Pin     →    Purpose
GPIO2         →    Positive (+)    →    Alert output
GND           →    Negative (-)   →    Ground
```

### **5. ESP32 to SIM800L (GSM Module)**
```
ESP32 Pin    →    SIM800L Pin    →    Purpose
5V            →    VBAT           →    Power (5V)
GND           →    GND            →    Ground
GPIO16        →    TXD            →    ESP32 RX
GPIO17        →    RXD            →    ESP32 TX
GPIO15        →    RST            →    Reset
```

### **6. ESP32 to Battery & Charging**
```
ESP32 Pin    →    Battery Pin     →    Purpose
GPIO34        →    Battery (+)     →    Voltage monitoring
GND           →    Battery (-)     →    Ground
USB 5V        →    Charging IC     →    Battery charging
```

## 🔧 **Complete Wiring Diagram**

```
                    ┌─────────────────────────────────────┐
                    │            ESP32                │
                    │                                 │
                    │  3V3  GND  GPIO22 GPIO21       │
                    │   │    │    │     │           │
                    │   └────┼────┼─────┼─────┐     │
                    │        │    │     │     │     │
┌───────────┐   │    ┌───▼───┐ ┌───▼───┐ │     │
│ MPU6050   │───┼──►│ VCC GND │ │ SDA SCL │─┼─────┤
│ (IMU)      │   │    └─────────┘ └─────────┘ │     │
└───────────┘   │                              │     │
                    │    ┌─────────────────────────┐ │     │
                    │    │ MAX30102               │ │     │
                    │    │ (Heart Rate)           │ │     │
                    │    │ VCC GND SDA SCL       │ │     │
                    │    └─────────────────────────┘ │     │
                    │                              │     │
                    │    ┌─────────────────────────┐ │     │
                    │    │ DS18B20               │ │     │
                    │    │ (Temperature)           │ │     │
                    │    │ VDD GND DQ             │ │     │
                    │    └─────────────────────────┘ │     │
                    │                              │     │
                    │    ┌─────────────────────────┐ │     │
                    │    │ Buzzer                 │ │     │
                    │    │ (+) (-)                │ │     │
                    │    └─────────────────────────┘ │     │
                    │                              │     │
                    │    ┌─────────────────────────┐ │     │
                    │    │ SIM800L                │ │     │
                    │    │ GSM Module              │ │     │
                    │    │ VBAT GND TXD RXD RST   │ │     │
                    │    └─────────────────────────┘ │     │
                    └─────────────────────────────────────┘
```

## 💻 **Software Setup**

### **1. Install ESP32 Arduino Code**
```cpp
// Upload this code to your ESP32
#include <Wire.h>
#include <MPU6050.h>
#include <MAX30105.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <SoftwareSerial.h>

// Pin definitions
#define MPU6050_SDA 22
#define MPU6050_SCL 21
#define MAX30102_SDA 23
#define MAX30102_SCL 22
#define DS18B20_PIN 4
#define BUZZER_PIN 2
#define SIM800_TX 16
#define SIM800_RX 17
#define BATTERY_PIN 34

// Sensor objects
MPU6050 mpu6050(Wire);
MAX30105 particleSensor;
OneWire oneWire(DS18B20_PIN);
DallasTemperature tempSensor(&oneWire);
SoftwareSerial sim800(SIM800_TX, SIM800_RX);

void setup() {
    Serial.begin(115200);
    Wire.begin();
    
    // Initialize sensors
    mpu6050.begin();
    particleSensor.begin(Wire, 0x57);
    tempSensor.begin();
    sim800.begin(9600);
    
    pinMode(BUZZER_PIN, OUTPUT);
    pinMode(BATTERY_PIN, INPUT);
    
    Serial.println("ESP32 Fall Detection System Ready");
}

void loop() {
    // Read sensors
    float ax, ay, az, gx, gy, gz;
    mpu6050.getMotion(&ax, &ay, &az, &gx, &gy, &gz);
    
    int heartRate = particleSensor.getIR();
    float temperature = tempSensor.getTempCByIndex(0);
    int battery = analogRead(BATTERY_PIN);
    
    // Send data via serial
    Serial.printf("ACC:%.2f,%.2f,%.2f\n", ax, ay, az);
    Serial.printf("GYR:%.2f,%.2f,%.2f\n", gx, gy, gz);
    Serial.printf("HR:%d\n", heartRate);
    Serial.printf("TEMP:%.2f\n", temperature);
    Serial.printf("BATT:%d\n", battery);
    
    // Handle commands from Python
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        handleCommand(command);
    }
    
    delay(100);
}

void handleCommand(String command) {
    if (command == "PING") {
        Serial.println("PONG");
    } else if (command == "GET_DATA") {
        // Data already sent in main loop
    } else if (command == "CALIBRATE") {
        calibrateSensors();
        Serial.println("CALIBRATED");
    }
}
```

### **2. Configure Python System**
```python
# In your system, set use_real_hardware=True
from src.sensors.enhanced_hardware_interface import initialize_hardware

# Connect to your hardware
hardware = initialize_hardware(
    use_real_hardware=True,
    serial_port="/dev/ttyUSB0",  # Windows: "COM3"
    baudrate=115200
)

# Test connection
if hardware.is_connected():
    print("✅ Hardware prototype connected successfully!")
else:
    print("❌ Failed to connect to hardware")
```

## 🔧 **Connection Steps**

### **Step 1: Physical Wiring**
1. **Power off ESP32** before connecting wires
2. **Connect MPU6050** to I2C pins (GPIO22/21)
3. **Connect MAX30102** to I2C pins (GPIO23/22)
4. **Connect DS18B20** to GPIO4 with pull-up resistor
5. **Connect buzzer** to GPIO2 and ground
6. **Connect SIM800L** to GPIO16/17 and 5V power
7. **Connect battery** to GPIO34 for monitoring
8. **Double-check all connections** before powering on

### **Step 2: Software Upload**
1. **Install Arduino IDE** with ESP32 board support
2. **Copy the Arduino code** above
3. **Select ESP32 board** and correct COM port
4. **Upload code** to ESP32
5. **Verify serial output** shows "System Ready"

### **Step 3: Python Connection**
1. **Install required Python packages**:
   ```bash
   pip install pyserial numpy
   ```

2. **Update configuration** in your system:
   ```python
   # Set to use real hardware
   use_real_hardware = True
   serial_port = "/dev/ttyUSB0"  # Linux/Mac
   # serial_port = "COM3"  # Windows
   baudrate = 115200
   ```

3. **Run the system**:
   ```bash
   python src/main_enhanced.py
   ```

## 🔍 **Testing the Connection**

### **1. Hardware Test**
```python
# Test individual components
from src.sensors.hardware_interface import RealMPU6050

# Create sensor instance
sensor = RealMPU6050(port="/dev/ttyUSB0")

# Connect and test
if sensor.connect():
    print("✅ MPU6050 connected")
    ax, ay, az = sensor.get_acceleration()
    print(f"Acceleration: X={ax:.2f}, Y={ay:.2f}, Z={az:.2f}")
else:
    print("❌ Failed to connect to MPU6050")
```

### **2. Full System Test**
```python
# Test complete system
from src.sensors.enhanced_hardware_interface import initialize_hardware, get_sensor_data

# Initialize hardware
hardware = initialize_hardware(use_real_hardware=True)

# Get sensor data
sensor_data = get_sensor_data()
print("Sensor Data:", sensor_data)

# Should see real data from your prototype
```

## 🛠️ **Troubleshooting**

### **Common Issues & Solutions:**

#### **❌ "Device not found"**
- **Check USB cable** connection
- **Install drivers** for CP2102/CH340 USB-to-Serial
- **Try different USB port**
- **Check Device Manager** for COM port number

#### **❌ "No sensor data"**
- **Verify I2C connections** (SDA/SCL not swapped)
- **Check pull-up resistors** on I2C lines (4.7kΩ)
- **Ensure 3.3V power** to sensors
- **Check ground connections**

#### **❌ "GSM not working"**
- **Verify 5V power** to SIM800L
- **Insert SIM card** properly
- **Check antenna connection**
- **Verify TX/RX wiring** (cross-connected)

#### **❌ "Random values"**
- **Calibrate sensors** first
- **Check power supply stability**
- **Verify sensor addresses** with I2C scanner
- **Ensure proper grounding**

## 📊 **Expected Data Output**

### **When Connected Successfully:**
```python
{
    'motion': {
        'ax': 0.12, 'ay': 0.08, 'az': 9.81,
        'gx': 0.01, 'gy': 0.02, 'gz': 0.00
    },
    'vitals': {
        'heart_rate': 72,
        'temperature': 36.8,
        'spo2': 98
    },
    'battery': {
        'level': 85,
        'voltage': 3.7,
        'charging': False
    },
    'device_status': {
        'worn': True,
        'connected': True,
        'sensors_ok': True
    }
}
```

## 🎯 **Next Steps**

### **1. Test Each Sensor Individually**
- Verify MPU6050 accelerometer data
- Check MAX30102 heart rate readings
- Confirm DS18B20 temperature values
- Test buzzer alert output
- Verify GSM module communication

### **2. Integration Testing**
- Run full system with hardware
- Test fall detection with real movements
- Verify alert generation and delivery
- Check data logging and storage

### **3. Wearable Testing**
- Mount prototype in waist band
- Test with actual human movements
- Verify comfort and fit
- Check battery life and charging

---

## 🎉 **CONNECTION COMPLETE!**

**Your hardware prototype is now ready to connect to the elderly monitoring system!**

### **✅ What You Need:**
1. **Wire all components** as shown in the diagram
2. **Upload Arduino code** to ESP32
3. **Configure Python** to use real hardware
4. **Run the system** and test connections

### **🔌 Key Points:**
- **Double-check wiring** before powering on
- **Use correct serial port** for your system
- **Test each sensor** individually first
- **Calibrate sensors** for accurate readings

Your **physical hardware prototype** will now provide **real sensor data** to the monitoring system! 🛠️📡✨
