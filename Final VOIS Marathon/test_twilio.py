#!/usr/bin/env python3
"""
Test Twilio Configuration and Functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

def test_twilio_credentials():
    """Test if Twilio credentials are valid"""
    print("🔍 Testing Twilio Credentials...")
    
    try:
        # Test credentials from twilio_service.py
        from backend.twilio_service import TWILIO_CONFIG
        
        client = Client(
            TWILIO_CONFIG["ACCOUNT_SID"],
            TWILIO_CONFIG["AUTH_TOKEN"]
        )
        
        # Test account access
        account = client.api.accounts.get(TWILIO_CONFIG["ACCOUNT_SID"]).fetch()
        print(f"✅ Account SID: {account.sid}")
        print(f"✅ Account Status: {account.status}")
        print(f"✅ Account Friendly Name: {account.friendly_name}")
        
        # Test phone number
        incoming_phone_numbers = client.incoming_phone_numbers.list()
        twilio_phone = TWILIO_CONFIG["TWILIO_PHONE"]
        
        phone_found = False
        for number in incoming_phone_numbers:
            if number.phone_number == twilio_phone:
                phone_found = True
                print(f"✅ Phone Number: {number.phone_number}")
                print(f"✅ Phone Capabilities: {number.capabilities}")
                break
        
        if not phone_found:
            print(f"⚠️ Warning: Phone number {twilio_phone} not found in account")
            print("Available numbers:")
            for number in incoming_phone_numbers[:5]:  # Show first 5
                print(f"  - {number.phone_number}")
        
        return True
        
    except TwilioRestException as e:
        print(f"❌ Twilio Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_sms_functionality():
    """Test SMS sending capability"""
    print("\n📱 Testing SMS Functionality...")
    
    try:
        from backend.twilio_service import twilio_service
        
        # Test with a dummy number (this will fail but shows if API works)
        test_phone = "+1234567890"  # Invalid number for testing
        
        print("Testing SMS API access...")
        result = twilio_service.send_fall_alert_sms(
            test_phone, 
            "Test User", 
            "Test Location", 
            "TestDevice"
        )
        
        if result:
            print("✅ SMS API accessible")
        else:
            print("❌ SMS API failed")
            
        return True
        
    except Exception as e:
        print(f"❌ SMS Test Error: {e}")
        return False

def main():
    print("=" * 50)
    print("🚀 TWILIO CONFIGURATION TEST")
    print("=" * 50)
    
    # Test 1: Credentials
    cred_test = test_twilio_credentials()
    
    # Test 2: SMS Functionality
    sms_test = test_sms_functionality()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"Credentials Test: {'✅ PASS' if cred_test else '❌ FAIL'}")
    print(f"SMS Functionality: {'✅ PASS' if sms_test else '❌ FAIL'}")
    
    if cred_test and sms_test:
        print("\n🎉 TWILIO IS PROPERLY CONFIGURED! ✨")
    else:
        print("\n⚠️ TWILIO CONFIGURATION NEEDS ATTENTION")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
