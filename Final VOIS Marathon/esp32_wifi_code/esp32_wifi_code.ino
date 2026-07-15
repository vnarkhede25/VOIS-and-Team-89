//FINAL CODE - WiFi + GSM ENABLED
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include "MAX30105.h"
#include <OneWire.h>
#include <DallasTemperature.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ---------- GSM MODULE ADDITIONS ----------
#include <HardwareSerial.h>

// GSM Configuration - UPDATED WITH YOUR PINS
#define GSM_TX_PIN 23    // GSM TX → ESP32 GPIO23 (ESP32 RXD)
#define GSM_RX_PIN 5     // GSM RX → ESP32 GPIO5 (ESP32 TXD)
// NO PWR PIN - GSM is powered directly by battery via TP4056
HardwareSerial gsmSerial(1);  // Use UART1 for GSM

// Emergency phone number (change this to your guardian's number)
const char* EMERGENCY_PHONE = "+919822976719";  // Updated to latest guardian

// GSM states
enum GsmState {
  GSM_INITIALIZING,
  GSM_READY,
  GSM_ERROR
};
GsmState gsmStatus = GSM_INITIALIZING;
unsigned long lastGsmAttempt = 0;
const unsigned long GSM_RETRY_INTERVAL = 30000;  // Retry every 30 seconds

// SMS tracking
bool smsSent = false;
unsigned long lastSmsTime = 0;
const unsigned long SMS_COOLDOWN = 60000;  // 1 minute between SMS alerts

// ---------- WiFi CONFIGURATION ----------
const char* ssid = "...";
const char* password = "43214321";
const char* serverURL = "http://192.168.43.167:5001/api/sensor-data";

// ---------- PINS ----------
#define TEMP_PIN 4
#define BUZZER_PIN 18
#define BUTTON_PIN 19

// Device ID
String deviceId = "isha_amit";

// ---------- OBJECTS ----------
Adafruit_MPU6050 mpu;
MAX30105 maxSensor;
OneWire oneWire(TEMP_PIN);
DallasTemperature tempSensor(&oneWire);

// ---------- ULTRA-SENSITIVE THRESHOLDS ----------
#define INSTABILITY_THRESHOLD 1.05    // Very sensitive - slight instability
#define SUDDEN_THRESHOLD 1.15        // Very sensitive - quick movement
#define FALL_THRESHOLD 1.3           // Very sensitive - any fall-like motion
#define STABILITY_TIME 200           // Quick confirmation (200ms)
#define FALL_CONFIRM_TIME 100        // Very quick confirmation (100ms)

#define IR_WORN_THRESHOLD 4500
#define TEMP_WORN_THRESHOLD 26.0

#define HR_LOW 50
#define HR_HIGH 135
#define SPO2_LOW 90

// ---------- STATES ----------
enum SystemState {
  NORMAL,
  PREFALL,
  SUDDEN_MOVEMENT,
  FALL_DETECTED
};

SystemState currentState = NORMAL;
SystemState lastState = NORMAL;

// ---------- VARIABLES ----------
bool beltWorn = false;
float heartRate = 0;
float spo2 = 0;
unsigned long fallTime = 0;
unsigned long lastSendTime = 0;
const unsigned long SEND_INTERVAL = 1000;

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  // No GSM_PWR_PIN setup needed - GSM powered directly by battery

  Wire.begin(21, 22);

  Serial.println("=== SENIOR SAFETY BELT SYSTEM START ===");

  // Initialize GSM Serial with YOUR PIN CONFIGURATION
  gsmSerial.begin(9600, SERIAL_8N1, GSM_RX_PIN, GSM_TX_PIN);
  Serial.println("GSM Serial: RX=GPIO5, TX=GPIO23");
  Serial.println("GSM Power: Battery via TP4056 (always ON)");
 
  // Start GSM module
  initializeGSM();

  // ========== WiFi Connection ==========
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
 
  int wifiAttempts = 0;
  while (WiFi.status() != WL_CONNECTED && wifiAttempts < 20) {
    delay(500);
    Serial.print(".");
    wifiAttempts++;
  }
 
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ WiFi Failed - Will use GSM as fallback");
  }

  // ========== Sensors Initialization ==========
  if (!mpu.begin()) {
    Serial.println("❌ MPU6050 NOT FOUND");
    while (1);
  }

  if (!maxSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("❌ MAX30102 NOT FOUND");
    while (1);
  }

  maxSensor.setup();
  tempSensor.begin();

  Serial.println("✅ ALL SENSORS INITIALIZED");
  Serial.println("=====================================");
}

// ========== GSM FUNCTIONS ==========

void initializeGSM() {
  Serial.println("🔄 Initializing GSM Module...");
 
  // No power control needed - GSM is always powered by battery via TP4056
  gsmStatus = GSM_INITIALIZING;
 
  // Send AT commands to initialize
  sendGSMCommand("AT");
  delay(1000);
 
  sendGSMCommand("ATE0");  // Echo off
  delay(1000);
 
  sendGSMCommand("AT+CPIN?");  // Check SIM status
  delay(2000);
 
  sendGSMCommand("AT+CSQ");    // Check signal quality
  delay(1000);
 
  sendGSMCommand("AT+CREG?");  // Check network registration
  delay(1000);
 
  // Check if GSM is responding
  if (checkGSMResponse("OK", 5000)) {
    gsmStatus = GSM_READY;
    Serial.println("✅ GSM Module Ready");
  } else {
    gsmStatus = GSM_ERROR;
    Serial.println("❌ GSM Module Failed - Check connections");
  }
}

void sendGSMCommand(const char* cmd) {
  Serial.print("GSM >> ");
  Serial.println(cmd);
  gsmSerial.println(cmd);
}

bool checkGSMResponse(const char* expected, unsigned long timeout) {
  unsigned long startTime = millis();
  String response = "";
 
  while (millis() - startTime < timeout) {
    while (gsmSerial.available()) {
      char c = gsmSerial.read();
      response += c;
      if (response.indexOf(expected) != -1) {
        Serial.print("GSM << ");
        Serial.println(response);
        return true;
      }
    }
  }
 
  Serial.print("GSM << (Timeout) ");
  Serial.println(response);
  return false;
}

void sendEmergencySMS(SystemState state, float hr, float oxygen, float temp, bool worn, float acc) {
  if (gsmStatus != GSM_READY) {
    Serial.println("⚠️ GSM not ready - cannot send SMS");
    return;
  }
 
  unsigned long currentTime = millis();
  if (currentTime - lastSmsTime < SMS_COOLDOWN && smsSent) {
    return;  // Respect cooldown period
  }
 
  String message = "🚨 SENIOR ALERT 🚨\n";
  message += "Person: " + deviceId + "\n";
  message += "Status: " + getStateName(state) + "\n";
 
  if (state == FALL_DETECTED) {
    message += "EMERGENCY: FALL DETECTED!\n";
  } else if (state == PREFALL) {
    message += "WARNING: Instability detected\n";
  }
 
  message += "Heart Rate: " + String(hr, 0) + " BPM\n";
  message += "SpO2: " + String(oxygen, 0) + "%\n";
  message += "Temp: " + String(temp, 1) + "°C\n";
  message += "Belt: " + String(worn ? "Worn" : "Not Worn") + "\n";
  message += "Acc: " + String(acc, 2) + "G\n";
  message += "WiFi: " + String(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected") + "\n";
  message += "Time: " + String(millis() / 1000) + "s";
 
  Serial.println("📱 Sending Emergency SMS...");
 
  // Set SMS text mode
  sendGSMCommand("AT+CMGF=1");
  delay(1000);
 
  // Set recipient number
  String cmd = "AT+CMGS=\"" + String(EMERGENCY_PHONE) + "\"";
  sendGSMCommand(cmd.c_str());
  delay(1000);
 
  // Send message content
  gsmSerial.print(message);
  delay(100);
  gsmSerial.write(26);  // Ctrl+Z to send
  delay(100);
 
  if (checkGSMResponse("+CMGS:", 10000)) {
    Serial.println("✅ Emergency SMS sent via GSM");
    smsSent = true;
    lastSmsTime = currentTime;
  } else {
    Serial.println("❌ Failed to send SMS via GSM");
  }
}

void checkAndManageGSM() {
  unsigned long currentTime = millis();
 
  // Try to reinitialize GSM if it's in error state and enough time has passed
  if (gsmStatus == GSM_ERROR) {
    if (currentTime - lastGsmAttempt > GSM_RETRY_INTERVAL) {
      Serial.println("🔄 Attempting to reconnect GSM...");
      initializeGSM();
      lastGsmAttempt = currentTime;
    }
  }
 
  // If WiFi is down and GSM is ready, we can use it as fallback
  if (WiFi.status() != WL_CONNECTED && gsmStatus == GSM_READY) {
    Serial.println("⚠️ WiFi disconnected - GSM fallback active");
  }
}

// ========== SERVER NOTIFICATION FUNCTIONS ==========

void notifyServerOfFall() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ WiFi not connected - cannot notify server");
    return;
  }

  Serial.println("🚨 Notifying server of fall detection...");
  
  // 1. Call detect-fall endpoint
  HTTPClient http;
  http.begin("http://192.168.43.167:5001/detect-fall");
  http.addHeader("Content-Type", "application/json");
  
  String fallPayload = "{\"device_id\":\"vois_belt\",\"confidence\":0.95}";
  int response1 = http.POST(fallPayload);
  
  Serial.print("🚨 Fall detection response: ");
  Serial.println(response1);
  
  http.end();

  // 2. Call notify-guardian-fall endpoint  
  http.begin("http://192.168.43.167:5001/notify-guardian-fall");
  http.addHeader("Content-Type", "application/json");
  
  String notifyPayload = "{\"elderly_name\":\"" + deviceId + "\",\"location\":\"Home\"}";
  int response2 = http.POST(notifyPayload);
  
  Serial.print("📱 Guardian notification response: ");
  Serial.println(response2);
  
  http.end();
}

void notifyServerOfPrefall() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ WiFi not connected - cannot notify server");
    return;
  }

  Serial.println("⚠️ Notifying server of prefall...");
  
  HTTPClient http;
  http.begin("http://192.168.43.167:5001/send-prefall-sms");
  http.addHeader("Content-Type", "application/json");
  
  String prefallPayload = "{\"elderly_name\":\"" + deviceId + "\",\"location\":\"Home\"}";
  int response = http.POST(prefallPayload);
  
  Serial.print("⚠️ Prefall notification response: ");
  Serial.println(response);
  
  http.end();
}

// ========== EXISTING FUNCTIONS (UNCHANGED) ==========

void sendDataToServer(SystemState state, float hr, float oxygen, float temp, bool worn, float acc) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ WiFi not connected - skipping server send");
   
    // Send emergency alerts via GSM if WiFi is down
    if (state == FALL_DETECTED || state == PREFALL) {
      sendEmergencySMS(state, hr, oxygen, temp, worn, acc);
    }
    return;
  }

  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<256> doc;
  doc["state"] = (int)state;
  doc["stateName"] = getStateName(state);
  doc["heartRate"] = hr;
  doc["spo2"] = oxygen;
  doc["temperature"] = temp;
  doc["beltWorn"] = worn;
  doc["acceleration"] = acc;
  doc["deviceId"] = deviceId;
  doc["timestamp"] = millis();

  String payload;
  serializeJson(doc, payload);

  Serial.print("📤 Sending to server: ");
  Serial.println(payload);

  int httpResponseCode = http.POST(payload);

  if (httpResponseCode > 0) {
    Serial.print("✅ Server Response: ");
    Serial.println(httpResponseCode);
    String response = http.getString();
    Serial.println(response);
  } else {
    Serial.print("❌ HTTP Error: ");
    Serial.println(httpResponseCode);
   
    // If server send fails, also send SMS via GSM for emergency states
    if (state == FALL_DETECTED || state == PREFALL) {
      sendEmergencySMS(state, hr, oxygen, temp, worn, acc);
    }
  }

  http.end();
}

String getStateName(SystemState state) {
  switch(state) {
    case NORMAL: return "NORMAL";
    case PREFALL: return "PREFALL";
    case SUDDEN_MOVEMENT: return "SUDDEN_MOVEMENT";
    case FALL_DETECTED: return "FALL_DETECTED";
    default: return "UNKNOWN";
  }
}

void loop() {
  // ---------- GSM Management ----------
  checkAndManageGSM();
 
  // ---------- MPU6050 ----------
  sensors_event_t acc, gyro, temp;
  mpu.getEvent(&acc, &gyro, &temp);

  float ax = acc.acceleration.x;
  float ay = acc.acceleration.y;
  float az = acc.acceleration.z;
  float accMag = sqrt(ax * ax + ay * ay + az * az);
  float accMagG = accMag / 9.8;

  // ---------- MAX30102 ----------
  long irValue = maxSensor.getIR();
  long redValue = maxSensor.getRed();

  heartRate = map(irValue, 5000, 50000, 60, 110);
  spo2 = map(redValue, 5000, 50000, 88, 98);

  // ---------- TEMPERATURE ----------
  tempSensor.requestTemperatures();
  float bodyTemp = tempSensor.getTempCByIndex(0);

  // ---------- BELT WORN ----------
  beltWorn = (irValue > IR_WORN_THRESHOLD && bodyTemp > TEMP_WORN_THRESHOLD);

  bool vitalsAbnormal =
    (heartRate < HR_LOW || heartRate > HR_HIGH || spo2 < SPO2_LOW);

  // ---------- PERFECT DECISION TREE ----------
  static unsigned long instabilityStartTime = 0;
  static unsigned long suddenMovementStartTime = 0;
  static bool instabilityConfirmed = false;
  static bool suddenMovementConfirmed = false;
  
  // Reset flags when returning to normal
  if (accMagG <= INSTABILITY_THRESHOLD) {
    instabilityStartTime = 0;
    instabilityConfirmed = false;
  }
  
  if (accMagG <= SUDDEN_THRESHOLD) {
    suddenMovementStartTime = 0;
    suddenMovementConfirmed = false;
  }

  // STATE PERSISTENCE
  if (currentState == FALL_DETECTED) {
    goto STATE_OUTPUT;
  }

  // FALL DETECTION - Highest Priority
  if (accMagG > FALL_THRESHOLD && beltWorn) {
    currentState = FALL_DETECTED;
    fallTime = millis();
    sendEmergencySMS(currentState, heartRate, spo2, bodyTemp, beltWorn, accMagG);
  }
  
  // PREFALL DETECTION - Medium Priority
  else if (accMagG > INSTABILITY_THRESHOLD && 
           accMagG <= SUDDEN_THRESHOLD && 
           beltWorn && 
           vitalsAbnormal) {
    
    if (!instabilityConfirmed) {
      if (instabilityStartTime == 0) {
        instabilityStartTime = millis();
      } else if (millis() - instabilityStartTime >= STABILITY_TIME) {
        instabilityConfirmed = true;
        currentState = PREFALL;
      }
    }
  }
  
  // SUDDEN MOVEMENT - Lower Priority
  else if (accMagG > SUDDEN_THRESHOLD && 
           accMagG <= FALL_THRESHOLD) {
    
    if (!suddenMovementConfirmed) {
      if (suddenMovementStartTime == 0) {
        suddenMovementStartTime = millis();
      } else if (millis() - suddenMovementStartTime >= FALL_CONFIRM_TIME) {
        suddenMovementConfirmed = true;
        currentState = SUDDEN_MOVEMENT;
      }
    }
  }
  
  // NORMAL STATE
  else {
    currentState = NORMAL;
  }

  // ---------- SERIAL MONITOR OUTPUT ----------
  Serial.println("\n================ SYSTEM STATUS ================");
  Serial.print("Acceleration (G): "); Serial.println(accMagG);
  Serial.print("GSM Status: ");
  switch(gsmStatus) {
    case GSM_INITIALIZING: Serial.println("INITIALIZING"); break;
    case GSM_READY: Serial.println("READY"); break;
    case GSM_ERROR: Serial.println("ERROR"); break;
  }

  Serial.print("IR Value: "); Serial.println(irValue);
  Serial.print("RED Value: "); Serial.println(redValue);

  Serial.print("Heart Rate (BPM): "); Serial.println(heartRate);
  Serial.print("SpO2 (%): "); Serial.println(spo2);

  Serial.print("Body Temperature (°C): "); Serial.println(bodyTemp);
  Serial.print("Belt Worn: "); Serial.println(beltWorn ? "YES" : "NO");

  Serial.print("FINAL STATE: ");
  STATE_OUTPUT:
  switch (currentState) {
    case NORMAL:
      Serial.println("✅ NORMAL");
      digitalWrite(BUZZER_PIN, LOW);
      break;

    case PREFALL:
      Serial.println("⚠️ PRE-FALL (INSTABILITY + ABNORMAL VITALS)");
      Serial.println("ACTION: Voice Prompt → 'Are you okay?'");
      digitalWrite(BUZZER_PIN, LOW);
      
      // NEW: Notify server for prefall SMS
      notifyServerOfPrefall();
      break;

    case SUDDEN_MOVEMENT:
      Serial.println("⚠️ SUDDEN MOVEMENT (MOTION ONLY)");
      digitalWrite(BUZZER_PIN, LOW);
      break;

    case FALL_DETECTED:
      Serial.println("🚨 FALL CONFIRMED");
      Serial.println("ACTION: CALL GUARDIAN");
      Serial.println("ACTION: SEND EMERGENCY SMS");
      digitalWrite(BUZZER_PIN, HIGH);
      
      // EXISTING: Send GSM SMS
      sendEmergencySMS(currentState, heartRate, spo2, bodyTemp, beltWorn, accMagG);
      
      // NEW: Also notify server for Twilio SMS/calls
      notifyServerOfFall();
      break;
  }

  // ---------- USER OVERRIDE ----------
  if (digitalRead(BUTTON_PIN) == LOW) {
    Serial.println("USER RESPONSE: I'M OK");
    digitalWrite(BUZZER_PIN, LOW);
    currentState = NORMAL;
    smsSent = false;  // Reset SMS flag when user confirms they're OK
  }

  // ---------- SEND DATA TO SERVER (throttled) ----------
  unsigned long currentTime = millis();
  if (currentTime - lastSendTime >= SEND_INTERVAL) {
    sendDataToServer(currentState, heartRate, spo2, bodyTemp, beltWorn, accMagG);
    lastSendTime = currentTime;
  }

  Serial.println("==============================================");
  delay(500);
}