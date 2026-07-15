#!/usr/bin/env python3
"""
Test script for fall detection alerts
"""
import requests
import json
import time

API_BASE = "http://localhost:5001"

def test_sensor_data(state_name, elderly_name="Isha"):
    """Send sensor data to test fall detection"""
    data = {
        "deviceId": "isha_amit",
        "stateName": state_name,
        "heartRate": 72,
        "spo2": 98,
        "temperature": 36.5,
        "beltWorn": True,
        "elderlyName": elderly_name,
        "location": "Living Room"
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/sensor-data", json=data)
        print(f"📡 Sent {state_name} data: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Sensor data sent successfully")
        else:
            print(f"❌ Failed to send sensor data: {response.text}")
    except Exception as e:
        print(f"❌ Error sending sensor data: {e}")

def test_sms_endpoints():
    """Test SMS endpoints directly"""
    # Note: Use a verified Twilio number for actual testing
    # For demo purposes, we'll use the mock functionality
    guardian_phone = "+15017122661"  # Twilio's verified demo number
    
    # Test prefall SMS
    print("\n--- Testing Prefall SMS ---")
    data = {
        "guardian_phone": guardian_phone,
        "elderly_name": "Isha",
        "location": "Living Room",
        "device_id": "isha_amit"
    }
    
    try:
        response = requests.post(f"{API_BASE}/send-prefall-sms", json=data)
        result = response.json()
        print(f"📱 Prefall SMS: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Prefall SMS sent successfully!")
        else:
            print(f"⚠️ Expected behavior for trial account: {result.get('message', 'No message')}")
            print("💡 Note: Twilio trial accounts can only send to verified numbers")
    except Exception as e:
        print(f"❌ Error testing prefall SMS: {e}")
    
    # Test fall alert (SMS + Call)
    print("\n--- Testing Fall Alert (SMS + Call) ---")
    try:
        response = requests.post(f"{API_BASE}/send-fall-alert", json=data)
        result = response.json()
        print(f"🚨 Fall Alert: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Fall alert sent successfully!")
        else:
            print(f"⚠️ Expected behavior for trial account: {result.get('message', 'No message')}")
            print("💡 Note: Twilio trial accounts can only call verified numbers")
    except Exception as e:
        print(f"❌ Error testing fall alert: {e}")

def main():
    print("🧪 Testing SilverCare Fall Detection System")
    print("=" * 50)
    
    # Test normal state
    print("\n1. Testing NORMAL state...")
    test_sensor_data("NORMAL")
    time.sleep(2)
    
    # Test prefall state
    print("\n2. Testing PREFALL state...")
    test_sensor_data("PREFALL")
    time.sleep(3)
    
    # Test fall detected state
    print("\n3. Testing FALL_DETECTED state...")
    test_sensor_data("FALL_DETECTED")
    time.sleep(3)
    
    # Test SMS endpoints directly
    print("\n4. Testing SMS endpoints...")
    test_sms_endpoints()
    
    print("\n✅ Test completed!")
    print("Check the guardian dashboard at http://localhost:8080/guardian-dashboard.html")
    print("Make sure you're logged in as a guardian to see the alerts.")

if __name__ == "__main__":
    main()
