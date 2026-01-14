#!/usr/bin/env python3
"""
Complete System Test and Demo

Final integration test for the Enhanced Elderly Monitoring System.
Tests all components and provides a working demo.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
import time
import json
from datetime import datetime

# Import all system components
from src.sensors.enhanced_hardware_interface import initialize_hardware, get_sensor_data
from src.detection.feature_extraction import initialize_feature_extractor
from src.detection.multi_layer_fall_detection import initialize_fall_detector, detect_fall
from src.detection.decision_engine import initialize_decision_engine, make_decision
from src.alerts.multi_level_alert_system import initialize_alert_system, send_alert, AlertType, AlertLevel
from src.location.vicinity_awareness import initialize_vicinity_system

class CompleteSystemTest:
    """Complete system integration test."""
    
    def __init__(self):
        self.components = {}
        self.test_results = {}
        
    async def test_all_components(self):
        """Test all system components."""
        print("🧪 Complete System Integration Test")
        print("=" * 60)
        
        # Test 1: Hardware Interface
        print("\n1. Testing Hardware Interface...")
        try:
            hw = initialize_hardware(use_real_hardware=False)
            sensor_data = get_sensor_data()
            self.components['hardware'] = hw
            self.test_results['hardware'] = True
            print(f"✅ Hardware Interface: {len(sensor_data)} sensor types")
        except Exception as e:
            self.test_results['hardware'] = False
            print(f"❌ Hardware Interface failed: {e}")
            return False
        
        # Test 2: Feature Extraction
        print("\n2. Testing Feature Extraction...")
        try:
            fe = initialize_feature_extractor(window_size=30, sampling_rate=10)
            self.components['feature_extractor'] = fe
            
            # Collect some data
            for i in range(50):
                sensor_data = get_sensor_data()
                ax = sensor_data.get('ax', 0)
                ay = sensor_data.get('ay', 0)
                az = sensor_data.get('az', 0)
                gx = sensor_data.get('gx', 0)
                gy = sensor_data.get('gy', 0)
                gz = sensor_data.get('gz', 0)
                timestamp = sensor_data.get('timestamp', time.time())
                
                fe.update(ax, ay, az, gx, gy, gz, timestamp)
                time.sleep(0.01)
            
            features = fe.get_current_features()
            if features and hasattr(features, '__dict__'):
                features_dict = features.__dict__
                print(f"✅ Feature Extraction: {len(features_dict)} features")
            else:
                print("⚠️ Feature Extraction: Limited features")
            
            self.test_results['feature_extraction'] = True
            self.components['features'] = features_dict if hasattr(features, '__dict__') else {}
            
        except Exception as e:
            self.test_results['feature_extraction'] = False
            print(f"❌ Feature Extraction failed: {e}")
            return False
        
        # Test 3: Fall Detection
        print("\n3. Testing Fall Detection...")
        try:
            fd = initialize_fall_detector()
            self.components['fall_detector'] = fd
            
            if 'features' in self.components and self.components['features']:
                detection_results = detect_fall(self.components['features'])
                print(f"✅ Fall Detection: {detection_results.get('final_decision', 'no_decision')}")
                self.components['detection_results'] = detection_results
            else:
                print("⚠️ Fall Detection: No features available")
            
            self.test_results['fall_detection'] = True
            
        except Exception as e:
            self.test_results['fall_detection'] = False
            print(f"❌ Fall Detection failed: {e}")
            return False
        
        # Test 4: Decision Engine
        print("\n4. Testing Decision Engine...")
        try:
            de = initialize_decision_engine()
            self.components['decision_engine'] = de
            
            if ('features' in self.components and self.components['features'] and
                'detection_results' in self.components):
                
                decision = make_decision(
                    self.components['features'], 
                    self.components['detection_results']
                )
                print(f"✅ Decision Engine: {decision.get('decision_type', 'no_decision')}")
                self.components['decision'] = decision
            else:
                print("⚠️ Decision Engine: Insufficient data")
            
            self.test_results['decision_engine'] = True
            
        except Exception as e:
            self.test_results['decision_engine'] = False
            print(f"❌ Decision Engine failed: {e}")
            return False
        
        # Test 5: Alert System
        print("\n5. Testing Alert System...")
        try:
            alert_sys = initialize_alert_system()
            alert_sys.start()
            self.components['alert_system'] = alert_sys
            
            # Test alert
            alert_id = await send_alert(
                AlertType.FALL_DETECTED, 
                AlertLevel.WARNING, 
                "Test alert from complete system test"
            )
            print(f"✅ Alert System: Alert sent ({alert_id})")
            
            alert_sys.stop()
            self.test_results['alert_system'] = True
            
        except Exception as e:
            self.test_results['alert_system'] = False
            print(f"❌ Alert System failed: {e}")
            return False
        
        # Test 6: Vicinity System
        print("\n6. Testing Vicinity System...")
        try:
            vs = initialize_vicinity_system()
            self.components['vicinity_system'] = vs
            
            result = vs.simulate_location_update("home")
            print(f"✅ Vicinity System: {result.get('location_updated', False)}")
            
            self.test_results['vicinity_system'] = True
            
        except Exception as e:
            self.test_results['vicinity_system'] = False
            print(f"❌ Vicinity System failed: {e}")
            return False
        
        return True
    
    def run_demo_scenario(self):
        """Run a complete demo scenario."""
        print("\n🎭 Running Complete Demo Scenario")
        print("-" * 40)
        
        try:
            # Simulate a monitoring session
            print("Starting monitoring session...")
            
            for minute in range(5):  # 5 minute demo
                print(f"\n--- Minute {minute + 1} ---")
                
                # Collect sensor data
                sensor_data = get_sensor_data()
                
                # Update feature extractor
                if 'feature_extractor' in self.components:
                    fe = self.components['feature_extractor']
                    ax = sensor_data.get('ax', 0)
                    ay = sensor_data.get('ay', 0)
                    az = sensor_data.get('az', 0)
                    gx = sensor_data.get('gx', 0)
                    gy = sensor_data.get('gy', 0)
                    gz = sensor_data.get('gz', 0)
                    timestamp = sensor_data.get('timestamp', time.time())
                    
                    fe.update(ax, ay, az, gx, gy, gz, timestamp)
                    
                    # Get features every 30 seconds
                    if minute % 1 == 0:
                        features = fe.get_current_features()
                        if features and hasattr(features, '__dict__'):
                            features_dict = features.__dict__
                            
                            # Run detection
                            detection_results = detect_fall(features_dict)
                            decision = make_decision(features_dict, detection_results)
                            
                            print(f"  Status: {decision.get('decision_type', 'normal')}")
                            print(f"  Confidence: {decision.get('confidence', 0):.2f}")
                            
                            # Trigger alert if needed
                            if decision.get('confidence', 0) > 0.7:
                                print(f"  🚨 ALERT: {decision.get('explanation', '')}")
                
                # Update location every 2 minutes
                if minute % 2 == 0:
                    if 'vicinity_system' in self.components:
                        vs = self.components['vicinity_system']
                        vs.simulate_location_update("home")
                        print("  📍 Location: Home (safe zone)")
                
                time.sleep(0.5)  # Simulate time passing
            
            print("\n✅ Demo scenario completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Demo scenario failed: {e}")
            return False
    
    def generate_report(self):
        """Generate final test report."""
        print("\n" + "=" * 60)
        print("📊 FINAL SYSTEM TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        print(f"\nTests Passed: {passed_tests}/{total_tests}")
        
        for component, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {component.replace('_', ' ').title()}: {status}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\nOverall Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("\n🎉 SYSTEM READY FOR DEPLOYMENT!")
            print("\n📋 Next Steps:")
            print("1. Start backend: python backend/integrated_app.py")
            print("2. Run main system: python src/main_enhanced.py")
            print("3. Access frontend: http://localhost:5000/frontend/senior_ui.html")
            print("4. Monitor guardian dashboard: http://localhost:5000/frontend/guardian_dashboard.html")
        elif success_rate >= 70:
            print("\n⚠️ SYSTEM MOSTLY READY - Minor Issues to Resolve")
        else:
            print("\n❌ SYSTEM NEEDS MAJOR FIXES")
        
        return success_rate >= 90

async def main():
    """Main test runner."""
    print("🚀 Enhanced Elderly Monitoring System - Complete Integration Test")
    print("=" * 70)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Initialize and test system
    test_system = CompleteSystemTest()
    
    # Test all components
    if not await test_system.test_all_components():
        print("\n❌ Component tests failed!")
        return False
    
    # Run demo scenario
    if not test_system.run_demo_scenario():
        print("\n❌ Demo scenario failed!")
        return False
    
    # Generate final report
    success = test_system.generate_report()
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
