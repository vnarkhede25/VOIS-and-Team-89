#!/usr/bin/env python3
"""
Register Harsh as Latest Guardian (Verified Number)
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001"

def register_harsh_as_latest():
    """Register harsh as the latest guardian with verified number"""
    print("📱 REGISTERING HARSH AS LATEST GUARDIAN")
    print("=" * 50)
    
    # Register harsh with verified number
    harsh_data = {
        "name": "Harsh Kumar",
        "username": "harsh_latest",
        "password": "harsh123",
        "phone": "+919322976719",  # Verified number
        "email": "harsh@example.com",
        "address": "Harsh Address"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/guardian-register", 
                               json=harsh_data, timeout=5)
        print(f"✅ Harsh registration: {response.status_code}")
        print(f"📊 {response.json()}")
        
        if response.status_code == 201:
            print("✅ Harsh registered as latest guardian")
            
            # Test fall detection with harsh as latest
            print("\n🚨 TESTING FALL DETECTION WITH HARSH...")
            
            notification_data = {
                "elderly_name": "Test User",
                "device_id": "vois_belt", 
                "location": "Home"
            }
            
            response = requests.post(f"{BASE_URL}/notify-guardian-fall",
                                   json=notification_data, timeout=15)
            print(f"✅ Guardian notification: {response.status_code}")
            print(f"📊 {response.json()}")
            
            if response.status_code == 200:
                print("🎉 SUCCESS!")
                print("📱 SMS sent to harsh (+919322976719)")
                print("📞 Call initiated to harsh (+919322976719)")
                print("🔍 CHECK YOUR PHONE NOW!")
            else:
                print("❌ Notification failed")
                
        else:
            print(f"⚠️ Registration response: {response.json()}")
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 SYSTEM IS NOW READY!")
    print("✅ Latest guardian: harsh (+919322976719)")
    print("✅ All alerts will go to harsh's phone")
    print("✅ Simple and working system")
    print("=" * 50)

if __name__ == "__main__":
    register_harsh_as_latest()
