#!/usr/bin/env python3
"""
Trigger Real Fall Alert Test
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001"

def trigger_real_fall_alert():
    """Trigger a real fall alert to test SMS/call"""
    print("🚨 TRIGGERING REAL FALL ALERT")
    print("=" * 50)
    print("📱 This will send REAL SMS and make REAL calls to harsh (+919322976719)")
    print("⏰ Starting in 3 seconds...")
    time.sleep(3)
    
    # Step 1: Detect fall
    print("\n1️⃣ DETECTING FALL...")
    fall_data = {
        "device_id": "vois_belt",
        "timestamp": "2026-02-26T18:45:00Z",
        "confidence": 0.95
    }
    
    try:
        response = requests.post(f"{BASE_URL}/detect-fall", 
                               json=fall_data, timeout=5)
        print(f"✅ Fall detected: {response.status_code}")
        print(f"📊 {response.json()}")
    except Exception as e:
        print(f"❌ Fall detection error: {e}")
        return
    
    # Step 2: Notify guardian (this sends SMS and makes call)
    print("\n2️⃣ NOTIFYING GUARDIAN...")
    print("📞 Sending SMS + Call to harsh (+919322976719)")
    
    notification_data = {
        "elderly_name": "nayana",
        "device_id": "vois_belt", 
        "location": "Home"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/notify-guardian-fall",
                               json=notification_data, timeout=15)
        print(f"✅ Guardian notification: {response.status_code}")
        print(f"📊 {response.json()}")
        
        if response.status_code == 200:
            print("\n🎉 FALL ALERT TRIGGERED SUCCESSFULLY!")
            print("📱 SMS sent to: +919322976719")
            print("📞 Call initiated to: +919322976719")
            print("👤 Elderly: nayana")
            print("📍 Location: Home")
            print("🔧 Device: vois_belt")
            print("\n⏰ You should receive:")
            print("   1. SMS: '🚨 SILVERCARE ALERT: Fall detected for nayana...'")
            print("   2. CALL: Automated voice message about emergency")
            
        else:
            print("❌ Guardian notification failed")
            
    except Exception as e:
        print(f"❌ Guardian notification error: {e}")
    
    print("\n" + "=" * 50)
    print("🔍 CHECK YOUR PHONE NOW!")
    print("📱 You should have received SMS and call")
    print("=" * 50)

if __name__ == "__main__":
    trigger_real_fall_alert()
