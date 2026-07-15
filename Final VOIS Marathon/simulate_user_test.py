#!/usr/bin/env python3
"""
Simulate User Testing from Their Side
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001"

def simulate_user_test():
    """Simulate exactly what user does when testing"""
    print("👤 SIMULATING USER TEST (YOUR SIDE)")
    print("=" * 50)
    
    # Step 1: Check current setup
    print("\n1️⃣ CHECKING CURRENT SETUP...")
    
    with open('backend/data/elderly.json', 'r') as f:
        elderly_data = json.load(f)
    
    device_info = elderly_data.get("vois_belt", {})
    current_user = device_info.get("current_user")
    print(f"📱 Device: vois_belt")
    print(f"👤 Current user: {current_user}")
    
    if current_user and current_user in elderly_data:
        elderly_info = elderly_data[current_user]
        guardian_username = elderly_info.get("guardian_username")
        print(f"👥 Guardian: {guardian_username}")
        
        with open('backend/data/guardians.json', 'r') as f:
            guardians_data = json.load(f)
        
        if guardian_username in guardians_data:
            guardian_info = guardians_data[guardian_username]
            guardian_phone = guardian_info.get("phone")
            print(f"📞 Guardian phone: {guardian_phone}")
            
            print(f"\n📊 CURRENT MAPPING:")
            print(f"   Device: vois_belt")
            print(f"   Elderly: {elderly_info.get('name')} ({current_user})")
            print(f"   Guardian: {guardian_info.get('name')} ({guardian_username})")
            print(f"   Phone: {guardian_phone}")
    
    # Step 2: Simulate user's fall detection test
    print("\n2️⃣ SIMULATING YOUR FALL DETECTION TEST...")
    
    # This is what your ESP32/hardware sends
    fall_data = {
        "device_id": "vois_belt",
        "timestamp": "2026-02-26T19:50:00Z",
        "confidence": 0.95
    }
    
    print("📤 Sending fall detection (like your hardware does)...")
    
    try:
        response = requests.post(f"{BASE_URL}/detect-fall", 
                               json=fall_data, timeout=5)
        print(f"✅ Fall detection response: {response.status_code}")
        print(f"📊 {response.json()}")
        
        if response.status_code == 200:
            print("✅ Fall detected successfully")
        else:
            print("❌ Fall detection failed")
            return
            
    except Exception as e:
        print(f"❌ Fall detection error: {e}")
        return
    
    # Step 3: Simulate user's guardian notification test
    print("\n3️⃣ SIMULATING YOUR GUARDIAN NOTIFICATION TEST...")
    
    # This is what your frontend/system sends
    notification_data = {
        "elderly_name": elderly_info.get("name", "Unknown"),
        "device_id": "vois_belt", 
        "location": elderly_info.get("location", "Unknown")
    }
    
    print("📤 Sending guardian notification (like your system does)...")
    
    try:
        response = requests.post(f"{BASE_URL}/notify-guardian-fall",
                               json=notification_data, timeout=15)
        print(f"✅ Guardian notification response: {response.status_code}")
        print(f"📊 {response.json()}")
        
        if response.status_code == 200:
            print("🎉 NOTIFICATION SENT SUCCESSFULLY!")
            print(f"📱 SMS sent to: {guardian_phone}")
            print(f"📞 Call initiated to: {guardian_phone}")
            print("🔍 CHECK YOUR PHONE NOW!")
        else:
            print("❌ Guardian notification failed")
            
    except Exception as e:
        print(f"❌ Guardian notification error: {e}")
    
    # Step 4: Check if there are any issues
    print("\n4️⃣ CHECKING FOR POTENTIAL ISSUES...")
    
    # Check server logs simulation
    print("🔍 What should happen in server logs:")
    print("   [GUARDIAN ALERT] Fall detected for nayana")
    print("   [GUARDIAN ALERT] Device: vois_belt, Location: Home")
    print("   [DEBUG] Device vois_belt current_user: harsh_nayana")
    print("   [DEBUG] Found elderly harsh_nayana, guardian: harsh")
    print("   [DEBUG] Guardian phone: +919322976719")
    print("   [SMS] ✅ Fall alert SMS sent!")
    print("   [TWILIO] ✅ Emergency call initiated!")
    
    # Check if phone is verified
    if guardian_phone == "+919322976719":
        print("\n✅ PHONE NUMBER IS VERIFIED - Should work!")
    else:
        print(f"\n⚠️ PHONE NUMBER {guardian_phone} might not be verified")
    
    print("\n" + "=" * 50)
    print("🎯 TROUBLESHOOTING:")
    print("1. Check if server is running on port 5001")
    print("2. Check if you're using correct endpoints")
    print("3. Check if phone number is verified")
    print("4. Check server logs for any errors")
    print("=" * 50)

if __name__ == "__main__":
    simulate_user_test()
