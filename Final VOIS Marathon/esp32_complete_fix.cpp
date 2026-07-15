// COMPLETE FIX FOR ESP32 - Add these functions to your existing code

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

// REPLACE THIS PART IN YOUR loop() FUNCTION:

// In the FALL_DETECTED case:
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

// In the PREFALL case:
case PREFALL:
  Serial.println("⚠️ PRE-FALL (INSTABILITY + ABNORMAL VITALS)");
  Serial.println("ACTION: Voice Prompt → 'Are you okay?'");
  digitalWrite(BUZZER_PIN, LOW);
  
  // NEW: Notify server for prefall SMS
  notifyServerOfPrefall();
  break;
