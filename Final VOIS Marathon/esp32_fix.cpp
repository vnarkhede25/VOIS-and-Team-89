// Add these functions to your ESP32 code

void notifyServerOfFall() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ WiFi not connected - cannot notify server");
    return;
  }

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

  HTTPClient http;
  http.begin("http://192.168.43.167:5001/send-prefall-sms");
  http.addHeader("Content-Type", "application/json");
  
  String prefallPayload = "{\"elderly_name\":\"" + deviceId + "\",\"location\":\"Home\"}";
  int response = http.POST(prefallPayload);
  
  Serial.print("⚠️ Prefall notification response: ");
  Serial.println(response);
  
  http.end();
}

// Then in your loop() function, replace the fall detection part:

// When FALL_DETECTED:
if (currentState == FALL_DETECTED) {
  fallTime = millis();
  
  // Send SMS via GSM (existing)
  sendEmergencySMS(currentState, heartRate, spo2, bodyTemp, beltWorn, accMagG);
  
  // NEW: Also notify server for Twilio SMS/calls
  notifyServerOfFall();
}

// When PREFALL:
if (currentState == PREFALL) {
  // NEW: Notify server for prefall SMS
  notifyServerOfPrefall();
}
