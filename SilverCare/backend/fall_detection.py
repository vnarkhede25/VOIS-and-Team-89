
from flask import Blueprint, request, jsonify
from twilio_service import twilio_service
from utils.auth import get_guardian

# Create Blueprint for fall detection routes
fall_detection_bp = Blueprint('fall_detection', __name__)

# Store fall detection state
fall_detected = False


@fall_detection_bp.route("/detect-fall", methods=["POST"])
def detect_fall():
    """Endpoint for hardware belt to report a fall detection.
    
    Expected JSON payload:
    {
        "device_id": "belt_001",
        "timestamp": "2026-01-05T10:30:00Z",
        "confidence": 0.95
    }
    """
    global fall_detected
    
    try:
        data = request.get_json()
        device_id = data.get("device_id", "unknown")
        confidence = data.get("confidence", 1.0)
        
        print(f"[FALL DETECTED] Device: {device_id}, Confidence: {confidence}")
        fall_detected = True
        
        return jsonify({
            "status": "success",
            "message": "Fall detected and alert triggered",
            "device_id": device_id
        }), 200
    except Exception as e:
        print(f"Error processing fall detection: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@fall_detection_bp.route("/fall-status", methods=["GET"])
def get_fall_status():
    """Check if a fall has been detected."""
    global fall_detected
    return jsonify({"fall_detected": fall_detected}), 200


@fall_detection_bp.route("/clear-fall", methods=["POST"])
def clear_fall():
    """Clear the fall detection flag after user confirms safe or guardian is contacted."""
    global fall_detected
    fall_detected = False
    return jsonify({"status": "fall_cleared"}), 200


@fall_detection_bp.route("/notify-guardian-fall", methods=["POST"])
def notify_guardian_fall():
    """Notify guardian that a fall has been detected.
    This is called immediately when fall is detected.
    
    Expected JSON payload:
    {
        "elderly_name": "John",
        "device_id": "belt_001",
        "location": "Home"
    }
    """
    try:
        data = request.get_json()
        elderly_name = data.get("elderly_name", "User")
        device_id = data.get("device_id", "unknown")
        location = data.get("location", "Unknown location")
        
        print(f"[GUARDIAN ALERT] Fall detected for {elderly_name}")
        print(f"[GUARDIAN ALERT] Device: {device_id}, Location: {location}")
        
        # Send SMS alert to guardian
        try:
            # Find guardian linked to this elderly person
            # For now, we'll use a simple approach - in production, you'd get this from elderly data
            sms_success = twilio_service.send_fall_alert_sms(
                guardian_phone="+919322757538",  # Default to Isha's number for testing
                elderly_name=elderly_name,
                location=location,
                device_id=device_id
            )
            
            if sms_success:
                print(f"[SMS] ✅ Fall alert SMS sent to guardian")
            else:
                print(f"[SMS] ❌ Failed to send fall alert SMS")
                
        except Exception as sms_error:
            print(f"[SMS] Error sending SMS: {sms_error}")
        
        return jsonify({
            "status": "success",
            "message": "Guardian notified of potential fall",
            "elderly_name": elderly_name
        }), 200
    except Exception as e:
        print(f"Error notifying guardian: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@fall_detection_bp.route("/notify-guardian-no-response", methods=["POST"])
def notify_guardian_no_response():
    """Notify guardian with SOUND ALERT that elderly didn't respond to fall alert.
    This is called after 10 seconds if elderly hasn't responded.
    
    Expected JSON payload:
    {
        "elderly_name": "John",
        "device_id": "belt_001",
        "location": "Home"
    }
    """
    try:
        data = request.get_json()
        elderly_name = data.get("elderly_name", "User")
        device_id = data.get("device_id", "unknown")
        location = data.get("location", "Unknown location")
        
        print(f"[GUARDIAN URGENT ALERT] {elderly_name} DID NOT RESPOND TO FALL ALERT!")
        print(f"[GUARDIAN URGENT ALERT] Device: {device_id}, Location: {location}")
        
        # Send URGENT SMS alert to guardian
        try:
            sms_success = twilio_service.send_urgent_alert_sms(
                guardian_phone="+919322757538",  # Default to Isha's number for testing
                elderly_name=elderly_name,
                location=location,
                device_id=device_id
            )
            
            if sms_success:
                print(f"[SMS] ✅ URGENT alert SMS sent to guardian")
            else:
                print(f"[SMS] ❌ Failed to send urgent alert SMS")
                
        except Exception as sms_error:
            print(f"[SMS] Error sending urgent SMS: {sms_error}")
        
        return jsonify({
            "status": "success",
            "message": "Guardian notified with urgent sound alert",
            "elderly_name": elderly_name
        }), 200
    except Exception as e:
        print(f"Error sending urgent alert to guardian: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@fall_detection_bp.route("/notify-guardian-safe", methods=["POST"])
def notify_guardian_safe():
    """Notify guardian that elderly person confirmed they are safe.
    
    Expected JSON payload:
    {
        "elderly_name": "John",
        "device_id": "belt_001"
    }
    """
    try:
        data = request.get_json()
        elderly_name = data.get("elderly_name", "User")
        device_id = data.get("device_id", "unknown")
        
        print(f"[GUARDIAN INFO] {elderly_name} confirmed they are safe (Fall was false alarm)")
        print(f"[GUARDIAN INFO] Device: {device_id}")
        
        # TODO: Send info notification to guardian
        # Example: Send SMS/Email confirming false alarm
        # from twilio.rest import Client
        # client = Client(account_sid, auth_token)
        # message = client.messages.create(
        #     body=f"All clear: {elderly_name} confirmed they are safe.",
        #     from_="+1234567890",
        #     to="+guardian_number"
        # )
        
        return jsonify({
            "status": "success",
            "message": "Guardian notified - false alarm",
            "elderly_name": elderly_name
        }), 200
    except Exception as e:
        print(f"Error notifying guardian (safe): {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@fall_detection_bp.route("/emergency-call", methods=["POST"])
def emergency_call():
    """Make an emergency phone call to guardian
    
    Called when elderly clicks "Need Help Now" button
    
    Expected JSON:
    {
        "elderly_id": "john_guardian_harsh",
        "elderly_name": "Harsh",
        "guardian_username": "john_guardian",
        "location": "Home"
    }
    """
    try:
        data = request.get_json()
        elderly_name = data.get("elderly_name", "User")
        guardian_username = data.get("guardian_username", "")
        location = data.get("location", "Unknown location")
        
        # Get guardian info to fetch phone number
        guardian = get_guardian(guardian_username)
        
        if not guardian:
            return jsonify({
                "status": "error",
                "message": "Guardian not found"
            }), 404
        
        guardian_phone = guardian.get("phone")
        
        if not guardian_phone:
            return jsonify({
                "status": "error",
                "message": "Guardian phone number not found"
            }), 400
        
        print(f"[EMERGENCY CALL] Initiating call to {guardian_username}")
        print(f"[EMERGENCY CALL] Guardian: {guardian.get('name')}")
        print(f"[EMERGENCY CALL] Phone: {guardian_phone}")
        print(f"[EMERGENCY CALL] Elderly: {elderly_name}")
        print(f"[EMERGENCY CALL] Location: {location}")
        
        # Make the actual call using Twilio
        call_success = twilio_service.make_emergency_call(
            guardian_phone=guardian_phone,
            elderly_name=elderly_name,
            location=location
        )
        
        if call_success:
            return jsonify({
                "status": "success",
                "message": "Emergency call initiated to guardian",
                "guardian_phone": guardian_phone,
                "guardian_name": guardian.get("name")
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to initiate emergency call"
            }), 500
            
    except Exception as e:
        print(f"Error making emergency call: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@fall_detection_bp.route("/urgent-call-no-response", methods=["POST"])
def urgent_call_no_response():
    """Make URGENT call with SIREN when elderly doesn't respond
    
    Called after 10 seconds if elderly hasn't clicked anything
    
    Expected JSON:
    {
        "elderly_id": "john_guardian_harsh",
        "elderly_name": "Harsh",
        "guardian_username": "john_guardian",
        "location": "Home"
    }
    """
    try:
        data = request.get_json()
        elderly_name = data.get("elderly_name", "User")
        guardian_username = data.get("guardian_username", "")
        location = data.get("location", "Unknown location")
        
        # Get guardian info
        guardian = get_guardian(guardian_username)
        
        if not guardian:
            return jsonify({
                "status": "error",
                "message": "Guardian not found"
            }), 404
        
        guardian_phone = guardian.get("phone")
        
        if not guardian_phone:
            return jsonify({
                "status": "error",
                "message": "Guardian phone number not found"
            }), 400
        
        print(f"[URGENT CALL] 🚨 Making URGENT call with SIREN!")
        print(f"[URGENT CALL] Guardian: {guardian.get('name')}")
        print(f"[URGENT CALL] Phone: {guardian_phone}")
        print(f"[URGENT CALL] Elderly did not respond: {elderly_name}")
        
        # Make the urgent call with siren
        call_success = twilio_service.make_no_response_alert_call(
            guardian_phone=guardian_phone,
            elderly_name=elderly_name,
            location=location
        )
        
        if call_success:
            return jsonify({
                "status": "success",
                "message": "URGENT call with siren initiated",
                "guardian_phone": guardian_phone,
                "alert_type": "NO_RESPONSE"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to initiate urgent call"
            }), 500
            
    except Exception as e:
        print(f"Error making urgent call: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
