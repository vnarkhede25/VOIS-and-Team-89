from sensors.hardware_interface import initialize_hardware, get_hardware_manager
from sensors.mpu6050_simulator import get_motion_data
from detection.motion_analysis import calculate_magnitude
from detection.threshold_fall import FallDetector
from detection.posture_detection import PostureClassifier, Posture
from detection.inactivity import InactivityDetector
from detection.prefall_instability import PreFallInstabilityDetector
from decision_engine.state_machine import FallStateMachine
from alerts.buzzer import Buzzer
from alerts.alert_controller import AlertController
from alerts.gaurdian_alert import initialize_guardian_alerts
from alerts.gsm_alert import initialize_gsm_alerts
from decision_engine.range_monitor import RangeMonitor
from decision_engine.comfort_rules import ComfortRules
import time
import argparse
import sys

# Global configuration
DEMO_MODE = False
BACKEND_URL = "http://localhost:5000"
PATIENT_ID = "demo_patient"

def initialize_system(use_real_hardware=False, backend_url=BACKEND_URL, patient_id=PATIENT_ID):
    """
    Initialize the complete fall detection system.
    
    Args:
        use_real_hardware: Whether to use real sensor or simulation
        backend_url: Backend API URL
        patient_id: Patient identifier
    """
    print("🚀 Initializing SilverCare Fall Detection System...")
    
    # Initialize hardware
    hardware_manager = initialize_hardware(use_real_hardware)
    print(f"📡 Hardware: {hardware_manager.get_sensor_type()}")
    
    # Initialize alert systems
    guardian_alerts = initialize_guardian_alerts(backend_url, patient_id)
    gsm_alerts = initialize_gsm_alerts(backend_url, patient_id)
    print(f"📡 Alert Systems: Guardian + GSM Emergency")
    
    # Initialize detection components
    fsm = FallStateMachine()
    fall_detector = FallDetector()
    posture_classifier = PostureClassifier()
    inactivity_detector = InactivityDetector()
    instability_detector = PreFallInstabilityDetector()
    buzzer = Buzzer()
    alerts = AlertController(buzzer)
    range_monitor = RangeMonitor()
    comfort = ComfortRules()
    
    print("✅ System initialized successfully")
    return {
        'hardware': hardware_manager,
        'fsm': fsm,
        'fall_detector': fall_detector,
        'posture_classifier': posture_classifier,
        'inactivity_detector': inactivity_detector,
        'instability_detector': instability_detector,
        'alerts': alerts,
        'range_monitor': range_monitor,
        'comfort': comfort,
        'guardian_alerts': guardian_alerts,
        'gsm_alerts': gsm_alerts
    }

def run_demo_mode(components):
    """
    Run system in demo mode with automatic fall simulation.
    
    Args:
        components: System components dictionary
    """
    print("🎮 Running in DEMO MODE")
    print("📋 Demo sequence: Normal → Normal → Normal → Fall → Lying → Lying")
    print("🔄 Each phase lasts 10 seconds")
    print("-" * 50)
    
    hardware = components['hardware']
    hardware.set_simulation_mode("demo")
    
    cycle_count = 0
    while cycle_count < 60:  # Run for 1 minute
        cycle_count += 1
        
        # Get sensor data
        ax, ay, az = hardware.get_acceleration()
        magnitude = calculate_magnitude(ax, ay, az)
        
        # Run detection pipeline
        spike = components['fall_detector'].detect_fall(magnitude)
        post_fall_state = components['fall_detector'].is_in_post_fall_state(magnitude)
        posture_obj = components['posture_classifier'].classify_posture(ax, ay, az)
        posture = posture_obj.value if posture_obj != Posture.UNKNOWN else "unknown"
        confidence = components['posture_classifier'].get_confidence(ax, ay, az)
        inactive = components['inactivity_detector'].is_inactive(magnitude, 0)
        instability_risk = components['instability_detector'].update(ax, ay, az)
        range_state = components['range_monitor'].update(True)
        
        # Update state machine
        state = components['fsm'].update(spike, posture, inactive, post_fall_state, instability_risk)
        risk_status = components['fsm'].get_risk_status()
        
        # Handle alerts
        components['alerts'].handle(state)
        components['comfort'].update()
        
        # Send remote alerts if needed
        if state == "ALERT":
            if components['comfort'].can_alert():
                # Send guardian alert
                components['guardian_alerts'].send_fall_alert(posture, magnitude)
                
                # Send emergency alert for critical falls
                if magnitude > 20:
                    components['gsm_alerts'].send_fall_emergency(magnitude, posture)
        
        # Display status
        print(
            f"CYCLE:{cycle_count:02d} | "
            f"MAG:{magnitude:6.2f} | "
            f"POSTURE:{posture:8s}({confidence:.2f}) | "
            f"RISK:{instability_risk:.2f}({risk_status['risk_state']:8s}) | "
            f"STATE:{state:15s}"
        )
        
        time.sleep(1)
    
    print("\n🎯 Demo completed! System is ready for production use.")

def run_normal_mode(components):
    """
    Run system in normal mode with real-time monitoring.
    
    Args:
        components: System components dictionary
    """
    print("🔄 Running in NORMAL MODE")
    print("📡 Monitoring sensor data in real-time...")
    print("🛑 Press Ctrl+C to stop")
    print("-" * 50)
    
    prev_magnitude = 0
    
    try:
        while True:
            # Get sensor data
            ax, ay, az = components['hardware'].get_acceleration()
            magnitude = calculate_magnitude(ax, ay, az)
            
            # Run detection pipeline
            spike = components['fall_detector'].detect_fall(magnitude)
            post_fall_state = components['fall_detector'].is_in_post_fall_state(magnitude)
            posture_obj = components['posture_classifier'].classify_posture(ax, ay, az)
            posture = posture_obj.value if posture_obj != Posture.UNKNOWN else "unknown"
            confidence = components['posture_classifier'].get_confidence(ax, ay, az)
            inactive = components['inactivity_detector'].is_inactive(magnitude, prev_magnitude)
            instability_risk = components['instability_detector'].update(ax, ay, az)
            range_state = components['range_monitor'].update(True)
            
            # Update state machine
            state = components['fsm'].update(spike, posture, inactive, post_fall_state, instability_risk)
            risk_status = components['fsm'].get_risk_status()
            
            # Handle alerts
            components['alerts'].handle(state)
            components['comfort'].update()
            
            # Send remote alerts for critical events
            if state == "ALERT":
                if components['comfort'].can_alert():
                    components['guardian_alerts'].send_fall_alert(posture, magnitude)
                    
                    if magnitude > 20:
                        components['gsm_alerts'].send_fall_emergency(magnitude, posture)
            elif state == "PRE_FALL_WARNING":
                if instability_risk > 0.8:
                    components['guardian_alerts'].send_instability_alert(instability_risk, risk_status['risk_state'])
            
            # Display status
            print(
                f"MAG:{magnitude:6.2f} | "
                f"POSTURE:{posture:8s}({confidence:.2f}) | "
                f"RISK:{instability_risk:.2f}({risk_status['risk_state']:8s}) | "
                f"STATE:{state:15s}"
            )
            
            prev_magnitude = magnitude
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 System stopped by user")
    except Exception as e:
        print(f"\n❌ System error: {e}")

def main():
    """Main entry point for the SilverCare Fall Detection System."""
    parser = argparse.ArgumentParser(description='SilverCare Fall Detection System')
    parser.add_argument('--demo', action='store_true', help='Run in demo mode with simulated falls')
    parser.add_argument('--hardware', action='store_true', help='Use real hardware instead of simulation')
    parser.add_argument('--backend', default=BACKEND_URL, help=f'Backend API URL (default: {BACKEND_URL})')
    parser.add_argument('--patient', default=PATIENT_ID, help=f'Patient ID (default: {PATIENT_ID})')
    
    args = parser.parse_args()
    
    print("🛡️  SilverCare Fall Detection System")
    print("=" * 50)
    
    # Initialize system
    try:
        components = initialize_system(
            use_real_hardware=args.hardware,
            backend_url=args.backend,
            patient_id=args.patient
        )
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        sys.exit(1)
    
    # Run appropriate mode
    try:
        if args.demo:
            run_demo_mode(components)
        else:
            run_normal_mode(components)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Runtime error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()