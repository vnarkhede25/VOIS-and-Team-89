#!/usr/bin/env python3
"""
Debug SMS/Call Issue - Step by Step Troubleshooting
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001"

def debug_sms_call_issue():
    """Debug why SMS/calls are not being received"""
    print("🔍 DEBUGGING SMS/CALL ISSUE")
    print("=" * 50)
    
    # Step 1: Check current device mapping
    print("\n1️⃣ CHECKING CURRENT DEVICE MAPPING...")
    
    with open('backend/data/elderly.json', 'r') as f:
        elderly_data = json.load(f)
    
    if "vois_belt" in elderly_data:
        device_info = elderly_data["vois_belt"]
        current_user = device_info.get("current_user")
        print(f"📱 Device: vois_belt")
        print(f"👤 Current user: {current_user}")
        
        if current_user and current_user in elderly_data:
            elderly_info = elderly_data[current_user]
            guardian_username = elderly_info.get("guardian_username")
            print(f"👥 Guardian username: {guardian_username}")
            
            # Step 2: Check guardian info
            print("\n2️⃣ CHECKING GUARDIAN INFO...")
            
            with open('backend/data/guardians.json', 'r') as f:
                guardians_data = json.load(f)
            
            if guardian_username in guardians_data:
                guardian_info = guardians_data[guardian_username]
                guardian_phone = guardian_info.get("phone")
                guardian_name = guardian_info.get("name")
                print(f"👤 Guardian name: {guardian_name}")
                print(f"📞 Guardian phone: {guardian_phone}")
                
                if guardian_phone:
                    # Step 3: Test direct Twilio SMS
                    print("\n3️⃣ TESTING DIRECT TWILIO SMS...")
                    
                    try:
                        from backend.twilio_service import twilio_service
                        
                        print(f"📱 Sending test SMS to {guardian_phone}...")
                        result = twilio_service.send_fall_alert_sms(
                            guardian_phone=guardian_phone,
                            elderly_name="DEBUG TEST",
                            location="DEBUG LOCATION",
                            device_id="vois_belt"
                        )
                        
                        if result:
                            print("✅ Direct Twilio SMS sent successfully")
                        else:
                            print("❌ Direct Twilio SMS failed")
                            
                    except Exception as e:
                        print(f"❌ Direct Twilio SMS error: {e}")
                    
                    # Step 4: Test direct Twilio Call
                    print("\n4️⃣ TESTING DIRECT TWILIO CALL...")
                    
                    try:
                        print(f"📞 Making test call to {guardian_phone}...")
                        result = twilio_service.make_emergency_call(
                            guardian_phone=guardian_phone,
                            elderly_name="DEBUG TEST",
                            location="DEBUG LOCATION"
                        )
                        
                        if result:
                            print("✅ Direct Twilio call initiated successfully")
                        else:
                            print("❌ Direct Twilio call failed")
                            
                    except Exception as e:
                        print(f"❌ Direct Twilio call error: {e}")
                    
                    # Step 5: Test via API endpoints
                    print("\n5️⃣ TESTING VIA API ENDPOINTS...")
                    
                    # Test fall detection
                    fall_data = {
                        "device_id": "vois_belt",
                        "timestamp": "2026-02-26T19:45:00Z",
                        "confidence": 0.95
                    }
                    
                    try:
                        response = requests.post(f"{BASE_URL}/detect-fall", 
                                               json=fall_data, timeout=5)
                        print(f"✅ Fall detection API: {response.status_code}")
                        print(f"📊 {response.json()}")
                    except Exception as e:
                        print(f"❌ Fall detection API error: {e}")
                    
                    # Test guardian notification
                    notification_data = {
                        "elderly_name": elderly_info.get("name", "Unknown"),
                        "device_id": "vois_belt", 
                        "location": elderly_info.get("location", "Unknown")
                    }
                    
                    try:
                        response = requests.post(f"{BASE_URL}/notify-guardian-fall",
                                               json=notification_data, timeout=15)
                        print(f"✅ Guardian notification API: {response.status_code}")
                        print(f"📊 {response.json()}")
                        
                        if response.status_code == 200:
                            print("🎉 API notification sent successfully")
                            print("📱 Check your phone for SMS/call")
                        else:
                            print("❌ API notification failed")
                            
                    except Exception as e:
                        print(f"❌ Guardian notification API error: {e}")
                    
                    # Step 6: Check Twilio configuration
                    print("\n6️⃣ CHECKING TWILIO CONFIGURATION...")
                    
                    try:
                        from backend.twilio_config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
                        
                        print(f"🔑 Account SID: {TWILIO_ACCOUNT_SID[:10]}...")
                        print(f"📞 Twilio Phone: {TWILIO_PHONE_NUMBER}")
                        
                        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
                            print("✅ Twilio configuration appears complete")
                        else:
                            print("❌ Twilio configuration incomplete")
                            
                    except Exception as e:
                        print(f"❌ Twilio config error: {e}")
                    
                else:
                    print("❌ Guardian phone not found")
            else:
                print("❌ Guardian not found in guardians.json")
        else:
            print("❌ Current user not found in elderly data")
    else:
        print("❌ vois_belt device not found")
    
    print("\n" + "=" * 50)
    print("🔍 DEBUGGING COMPLETE")
    print("📱 If you still don't receive SMS/call, check:")
    print("   1. Phone number format (+91 required)")
    print("   2. Twilio account balance")
    print("   3. Phone number is not blocked")
    print("   4. Network connectivity")
    print("=" * 50)

if __name__ == "__main__":
    debug_sms_call_issue()
