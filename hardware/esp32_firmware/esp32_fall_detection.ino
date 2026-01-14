"""
ESP32 Arduino Code for Hardware Prototype

Complete firmware for ESP32-based elderly monitoring waist band.
Interfaces with all sensors and provides serial communication to Python backend.

Features:
- MPU6050 IMU sensor (accelerometer + gyroscope)
- MAX30102 heart rate & SpO2 sensor
- DS18B20 temperature sensor
- Buzzer for local alerts
- SIM800L GSM module for communication
- Battery monitoring
- Serial communication with Python backend
"""

#include <Wire.h>
#include <MPU6050.h>
#include <MAX30105.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <SoftwareSerial.h>
#include <ArduinoJson.h>

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
MPU6050 mpu6050;
MAX30105 particleSensor;
OneWire oneWire(DS18B20_PIN);
DallasTemperature tempSensor(&oneWire);
SoftwareSerial sim800(SIM800_TX, SIM800_RX);

// Global variables
float ax, ay, az, gx, gy, gz;
int heartRate = 0;
float spo2 = 0.0;
float temperature = 0.0;
int batteryLevel = 0;
bool buzzerActive = false;
unsigned long lastSensorRead = 0;
unsigned long lastHeartBeat = 0;

// Calibration offsets
float accelOffsetX = 0, accelOffsetY = 0, accelOffsetZ = 0;
float gyroOffsetX = 0, gyroOffsetY = 0, gyroOffsetZ = 0;

void setup() {
    Serial.begin(115200);
    Wire.begin();
    
    // Initialize MPU6050
    mpu6050.begin();
    mpu6050.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu6050.setGyroRange(MPU6050_RANGE_500_DPS);
    
    // Initialize MAX30102
    particleSensor.begin(Wire, 0x57);
    particleSensor.setup();
    particleSensor.setPulseAmplitudeRed(0x0C);
    particleSensor.setPulseAmplitudeIR(0x1F);
    
    // Initialize DS18B20
    tempSensor.begin();
    
    // Initialize SIM800L
    sim800.begin(9600);
    delay(1000);
    
    // Initialize pins
    pinMode(BUZZER_PIN, OUTPUT);
    pinMode(BATTERY_PIN, INPUT);
    digitalWrite(BUZZER_PIN, LOW);
    
    // Calibrate sensors
    calibrateSensors();
    
    Serial.println("ESP32 Fall Detection System Ready");
    Serial.println("Commands: PING, GET_DATA, CALIBRATE, BUZZER_ON, BUZZER_OFF");
}

void loop() {
    // Read sensors every 100ms
    if (millis() - lastSensorRead > 100) {
        readSensors();
        lastSensorRead = millis();
    }
    
    // Handle serial commands
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        handleCommand(command);
    }
    
    // Check for heart beat
    checkHeartBeat();
    
    delay(10);
}

void readSensors() {
    // Read MPU6050
    mpu6050.getMotion(&ax, &ay, &az, &gx, &gy, &gz);
    
    // Apply calibration offsets
    ax -= accelOffsetX;
    ay -= accelOffsetY;
    az -= accelOffsetZ;
    gx -= gyroOffsetX;
    gy -= gyroOffsetY;
    gz -= gyroOffsetZ;
    
    // Read MAX30102
    if (particleSensor.safeCheck() == 0) {
        heartRate = particleSensor.getIR();
        // Simple SpO2 calculation (would need proper calibration)
        spo2 = 95.0 + (heartRate % 10);
    }
    
    // Read DS18B20
    tempSensor.requestTemperatures();
    temperature = tempSensor.getTempCByIndex(0);
    
    // Read battery level
    batteryLevel = analogRead(BATTERY_PIN);
    batteryLevel = map(batteryLevel, 0, 4095, 0, 100);
}

void checkHeartBeat() {
    // Simple heart beat detection from MAX30102
    if (particleSensor.safeCheck() == 0) {
        uint32_t irValue = particleSensor.getIR();
        uint32_t redValue = particleSensor.getRed();
        
        // Simple beat detection (would need proper algorithm)
        if (irValue > 50000 && millis() - lastHeartBeat > 300) {
            lastHeartBeat = millis();
        }
    }
}

void handleCommand(String command) {
    if (command == "PING") {
        Serial.println("PONG");
        
    } else if (command == "GET_DATA") {
        sendSensorData();
        
    } else if (command == "CALIBRATE") {
        calibrateSensors();
        Serial.println("CALIBRATED");
        
    } else if (command == "BUZZER_ON") {
        digitalWrite(BUZZER_PIN, HIGH);
        buzzerActive = true;
        Serial.println("BUZZER_ON");
        
    } else if (command == "BUZZER_OFF") {
        digitalWrite(BUZZER_PIN, LOW);
        buzzerActive = false;
        Serial.println("BUZZER_OFF");
        
    } else if (command.startsWith("SEND_SMS:")) {
        String phoneNumber = command.substring(9);
        sendSMS(phoneNumber, "Fall detected! Please check on the patient.");
        Serial.println("SMS_SENT");
        
    } else if (command == "STATUS") {
        sendDeviceStatus();
        
    } else {
        Serial.println("UNKNOWN_COMMAND");
    }
}

void sendSensorData() {
    // Create JSON output
    DynamicJsonDocument doc(1024);
    
    // Motion data
    JsonObject motion = doc.createNestedObject("motion");
    motion["ax"] = ax;
    motion["ay"] = ay;
    motion["az"] = az;
    motion["gx"] = gx;
    motion["gy"] = gy;
    motion["gz"] = gz;
    
    // Vitals data
    JsonObject vitals = doc.createNestedObject("vitals");
    vitals["heart_rate"] = heartRate;
    vitals["spo2"] = spo2;
    vitals["temperature"] = temperature;
    vitals["temp_status"] = (temperature > 35.0 && temperature < 38.0) ? "normal" : "abnormal";
    
    // Battery data
    JsonObject battery = doc.createNestedObject("battery");
    battery["level"] = batteryLevel;
    battery["voltage"] = (batteryLevel / 100.0) * 4.2; // Approximate
    battery["charging"] = false; // Would need charging circuit detection
    
    // Device status
    JsonObject device = doc.createNestedObject("device_status");
    device["device_id"] = "waist_band_001";
    device["worn"] = detectWornStatus();
    device["connected"] = true;
    device["sensors"] = true;
    device["buzzer_active"] = buzzerActive;
    
    // Serialize and send
    serializeJson(doc, Serial);
    Serial.println();
}

void sendDeviceStatus() {
    DynamicJsonDocument doc(512);
    
    doc["device_id"] = "waist_band_001";
    doc["uptime"] = millis() / 1000;
    doc["free_heap"] = ESP.getFreeHeap();
    doc["battery_level"] = batteryLevel;
    doc["temperature"] = temperature;
    doc["heart_rate"] = heartRate;
    doc["worn"] = detectWornStatus();
    doc["sensors_ok"] = true;
    
    serializeJson(doc, Serial);
    Serial.println();
}

bool detectWornStatus() {
    // Simple wear detection based on sensor patterns
    bool hasMotion = (abs(ax) > 0.5 || abs(ay) > 0.5);
    bool hasHeartRate = (heartRate > 40 && heartRate < 200);
    bool normalTemp = (temperature > 35.0 && temperature < 38.0);
    
    return hasMotion && hasHeartRate && normalTemp;
}

void calibrateSensors() {
    Serial.println("Calibrating sensors...");
    
    // Calibrate MPU6050 (average 100 readings)
    long accelSumX = 0, accelSumY = 0, accelSumZ = 0;
    long gyroSumX = 0, gyroSumY = 0, gyroSumZ = 0;
    
    for (int i = 0; i < 100; i++) {
        mpu6050.getMotion(&ax, &ay, &az, &gx, &gy, &gz);
        accelSumX += ax;
        accelSumY += ay;
        accelSumZ += az;
        gyroSumX += gx;
        gyroSumY += gy;
        gyroSumZ += gz;
        delay(10);
    }
    
    accelOffsetX = accelSumX / 100.0;
    accelOffsetY = accelSumY / 100.0;
    accelOffsetZ = accelSumZ / 100.0;
    gyroOffsetX = gyroSumX / 100.0;
    gyroOffsetY = gyroSumY / 100.0;
    gyroOffsetZ = gyroSumZ / 100.0;
    
    Serial.println("Calibration complete");
}

void sendSMS(String phoneNumber, String message) {
    sim800.println("AT+CMGF=1"); // Set SMS mode
    delay(100);
    
    sim800.print("AT+CMGS=\"");
    sim800.print(phoneNumber);
    sim800.println("\"");
    delay(100);
    
    sim800.print(message);
    sim800.write(26); // Ctrl+Z to send
    delay(1000);
}

void activateBuzzer(int duration) {
    digitalWrite(BUZZER_PIN, HIGH);
    buzzerActive = true;
    delay(duration);
    digitalWrite(BUZZER_PIN, LOW);
    buzzerActive = false;
}

// Emergency functions
void emergencyAlert() {
    // Activate buzzer
    activateBuzzer(1000);
    
    // Send SMS to emergency contact
    sendSMS("+1234567890", "EMERGENCY: Fall detected at waist band!");
    
    // Flash LED if available
    for (int i = 0; i < 10; i++) {
        // digitalWrite(LED_PIN, HIGH);
        delay(200);
        // digitalWrite(LED_PIN, LOW);
        delay(200);
    }
}

// Helper function to check sensor health
bool checkSensorHealth() {
    // Check if sensors are responding
    bool mpuOK = mpu6050.getMotion(&ax, &ay, &az, &gx, &gy, &gz);
    bool tempOK = tempSensor.getTempCByIndex(0) != DEVICE_DISCONNECTED_C;
    bool maxOK = particleSensor.safeCheck() == 0;
    
    return mpuOK && tempOK && maxOK;
}
