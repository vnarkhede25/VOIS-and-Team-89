#!/usr/bin/env python3
"""
Test with Verified Number (harsh's number)
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001"

def test_with_verified_number():
    """Test SMS/call with verified number"""
    print("📱 TESTING WITH VERIFIED NUMBER")
    print("=" * 50)
    
    # Change device mapping to use harsh's elderly
    print("\n1️⃣ UPDATING DEVICE TO HARSH'S ELDERLY...")
    
    with open('backend/data/elderly.json', 'r') as f:
        elderly_data = json.load(f)
    
    # Update vois_belt to use harsh's elderly
    elderly_data["vois_belt"]["current_user"] = "harsh_nayana"
    
    with open('backend/data/elderly.json', 'w') as f:
        json.dump(elderly_data, f, indent=2)
    
    print("✅ Device updated to use harsh_nayana")
    
    # Test with verified number
    print("\n2️⃣ TESTING WITH VERIFIED NUMBER (+919322976719)...")
    
    try:
        from backend.twilio_service import twilio_service
        
        print("📱 Sending SMS to verified number...")
        result = twilio_service.send_fall_alert_sms(
            guardian_phone="+919322976719",
            elderly_name="nayana",
            location="Home",
            device_id="vois_belt"
        )
        
        if result:
            print("✅ SMS sent to verified number successfully")
        else:
            print("❌ SMS to verified number failed")
            
        print("📞 Making call to verified number...")
        result = twilio_service.make_emergency_call(
            guardian_phone="+919322976719",
            elderly_name="nayana",
            location="Home"
        )
        
        if result:
            print("✅ Call initiated to verified number successfully")
        else:
            print("❌ Call to verified number failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test via API
    print("\n3️⃣ TESTING VIA API WITH VERIFIED NUMBER...")
    
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
            print("🎉 SUCCESS! Check your phone (+919322976719)")
            print("📱 You should receive SMS and call now")
        else:
            print("❌ API notification failed")
            
    except Exception as e:
        print(f"❌ API error: {e}")
    
    print("\n" + "=" * 50)
    print("📊 ISSUE IDENTIFIED:")
    print("❌ TRIAL ACCOUNT LIMITATION:")
    print("   - Can only send SMS/calls to VERIFIED numbers")
    print("   - +919322976719 is verified (should work)")
    print("   - +919988776655 is not verified (won't work)")
    print("\n✅ SOLUTION:")
    print("   1. Use verified numbers for testing")
    print("   2. Upgrade to paid Twilio account")
    print("   3. Verify more phone numbers at twilio.com")
    print("=" * 50)

if __name__ == "__main__":
    test_with_verified_number()
