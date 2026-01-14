"""
Complete System Test Script

Comprehensive test script for all 18+ features of the elderly monitoring system.
Tests each feature individually and provides detailed results.

Usage:
    python complete_system_test.py [--feature all] [--verbose]
"""

import sys
import time
import requests
import json
import argparse
from datetime import datetime

# Add project path
sys.path.append('.')

class SystemTester:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.base_url = "http://localhost:5000"
        self.gsm_url = "http://localhost:5002"
        self.test_results = {}
        
    def log(self, message, level="INFO"):
        """Log test messages."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] {level}:"
        print(f"{prefix} {message}")
        
    def test_feature(self, feature_name, test_func):
        """Test a specific feature."""
        self.log(f"Testing {feature_name}...", "TEST")
        try:
            result = test_func()
            self.test_results[feature_name] = {
                "status": "PASS" if result else "FAIL",
                "timestamp": datetime.now().isoformat()
            }
            self.log(f"{feature_name}: {'✅ PASS' if result else '❌ FAIL'}")
            return result
        except Exception as e:
            self.test_results[feature_name] = {
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.log(f"{feature_name}: ❌ ERROR - {e}", "ERROR")
            return False
    
    def test_backend_services(self):
        """Test backend API services."""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_gsm_services(self):
        """Test GSM communication services."""
        try:
            response = requests.get(f"{self.gsm_url}/api/gsm/status", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_fall_detection(self):
        """Test fall detection system."""
        try:
            # Test fall detection API
            response = requests.post(
                f"{self.base_url}/api/fall/detect",
                json={
                    "acceleration": [0.1, 0.2, 15.0],
                    "gyroscope": [0.0, 0.0, 0.0],
                    "timestamp": datetime.now().isoformat()
                },
                timeout=5
            )
            return response.status_code in [200, 201]
        except:
            return False
    
    def test_sensor_monitoring(self):
        """Test real-time sensor monitoring."""
        try:
            response = requests.get(f"{self.base_url}/api/sensors/current", timeout=5)
            if response.status_code == 200:
                data = response.json()
                required_fields = ['motion', 'vitals', 'battery', 'device_status']
                return all(field in data for field in required_fields)
            return False
        except:
            return False
    
    def test_alert_system(self):
        """Test guardian alert system."""
        try:
            response = requests.post(
                f"{self.base_url}/api/alerts/test",
                json={
                    "type": "test_alert",
                    "message": "Test alert from system test",
                    "priority": "low"
                },
                timeout=5
            )
            return response.status_code in [200, 201]
        except:
            return False
    
    def test_learning_system(self):
        """Test continuous learning system."""
        try:
            # Test learning data submission
            response = requests.post(
                f"{self.base_url}/api/learning/data",
                json={
                    "patient_id": "test_patient",
                    "features": [1.2, 0.8, 9.8, 0.1, 0.2, 0.0],
                    "detection_result": "normal",
                    "timestamp": datetime.now().isoformat()
                },
                timeout=5
            )
            return response.status_code in [200, 201]
        except:
            return False
    
    def test_wearable_detection(self):
        """Test wearable detection system."""
        try:
            response = requests.get(f"{self.base_url}/api/wearable/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return 'status' in data and 'confidence' in data
            return False
        except:
            return False
    
    def test_connection_monitoring(self):
        """Test connection range monitoring."""
        try:
            response = requests.get(f"{self.base_url}/api/connection/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return 'connected' in data
            return False
        except:
            return False
    
    def test_gsm_communication(self):
        """Test GSM communication system."""
        try:
            # Test SMS sending
            response = requests.post(
                f"{self.gsm_url}/api/gsm/sms/send",
                json={
                    "guardian_id": "test_guardian",
                    "message": "Test message from system test",
                    "priority": "normal"
                },
                timeout=5
            )
            return response.status_code in [200, 201]
        except:
            return False
    
    def test_location_monitoring(self):
        """Test location monitoring system."""
        try:
            response = requests.get(f"{self.base_url}/api/location/current", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return 'latitude' in data or 'address' in data
            return False
        except:
            return False
    
    def test_health_monitoring(self):
        """Test health monitoring system."""
        try:
            response = requests.get(f"{self.base_url}/api/health/current", timeout=5)
            if response.status_code == 200:
                data = response.json()
                required_fields = ['heart_rate', 'temperature', 'spo2']
                return any(field in data for field in required_fields)
            return False
        except:
            return False
    
    def test_battery_management(self):
        """Test battery management system."""
        try:
            response = requests.get(f"{self.base_url}/api/battery/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return 'level' in data or 'percentage' in data
            return False
        except:
            return False
    
    def test_multi_level_alerts(self):
        """Test multi-level alert system."""
        try:
            # Test different alert levels
            priorities = ["low", "medium", "high", "emergency"]
            results = []
            
            for priority in priorities:
                response = requests.post(
                    f"{self.base_url}/api/alerts/send",
                    json={
                        "type": "test_alert",
                        "message": f"Test {priority} priority alert",
                        "priority": priority
                    },
                    timeout=5
                )
                results.append(response.status_code in [200, 201])
            
            return all(results)
        except:
            return False
    
    def test_data_logging(self):
        """Test data logging system."""
        try:
            # Check if log file exists and is being written
            import os
            log_file = "elderly_monitoring.log"
            if os.path.exists(log_file):
                # Check if log file has recent entries
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    return len(lines) > 0
            return False
        except:
            return False
    
    def test_real_time_dashboard(self):
        """Test real-time dashboard functionality."""
        try:
            # Test dashboard data endpoint
            response = requests.get(f"{self.base_url}/api/dashboard/realtime", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return isinstance(data, dict)
            return False
        except:
            return False
    
    def test_historical_analysis(self):
        """Test historical data analysis."""
        try:
            response = requests.get(f"{self.base_url}/api/analytics/historical", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return 'data' in data or 'analytics' in data
            return False
        except:
            return False
    
    def test_user_management(self):
        """Test user management system."""
        try:
            response = requests.get(f"{self.base_url}/api/users/profile", timeout=5)
            return response.status_code in [200, 401]  # 401 is ok (not authenticated)
        except:
            return False
    
    def test_system_configuration(self):
        """Test system configuration."""
        try:
            response = requests.get(f"{self.base_url}/api/config/settings", timeout=5)
            return response.status_code in [200, 401]
        except:
            return False
    
    def test_emergency_response(self):
        """Test emergency response system."""
        try:
            response = requests.post(
                f"{self.base_url}/api/emergency/test",
                json={
                    "type": "test_emergency",
                    "location": {"latitude": 0, "longitude": 0},
                    "medical_info": {"conditions": ["None"]}
                },
                timeout=5
            )
            return response.status_code in [200, 201]
        except:
            return False
    
    def test_system_health(self):
        """Test system health monitoring."""
        try:
            response = requests.get(f"{self.base_url}/api/system/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return 'status' in data or 'health' in data
            return False
        except:
            return False
    
    def test_advanced_analytics(self):
        """Test advanced analytics features."""
        try:
            response = requests.get(f"{self.base_url}/api/analytics/advanced", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return 'insights' in data or 'metrics' in data
            return False
        except:
            return False
    
    def run_all_tests(self):
        """Run all feature tests."""
        self.log("🧪 Starting Complete System Test Suite", "INFO")
        self.log("=" * 50, "INFO")
        
        # Define all features to test
        features = [
            ("Backend Services", self.test_backend_services),
            ("GSM Services", self.test_gsm_services),
            ("Fall Detection", self.test_fall_detection),
            ("Sensor Monitoring", self.test_sensor_monitoring),
            ("Alert System", self.test_alert_system),
            ("Learning System", self.test_learning_system),
            ("Wearable Detection", self.test_wearable_detection),
            ("Connection Monitoring", self.test_connection_monitoring),
            ("GSM Communication", self.test_gsm_communication),
            ("Location Monitoring", self.test_location_monitoring),
            ("Health Monitoring", self.test_health_monitoring),
            ("Battery Management", self.test_battery_management),
            ("Multi-level Alerts", self.test_multi_level_alerts),
            ("Data Logging", self.test_data_logging),
            ("Real-time Dashboard", self.test_real_time_dashboard),
            ("Historical Analysis", self.test_historical_analysis),
            ("User Management", self.test_user_management),
            ("System Configuration", self.test_system_configuration),
            ("Emergency Response", self.test_emergency_response),
            ("System Health", self.test_system_health),
            ("Advanced Analytics", self.test_advanced_analytics),
        ]
        
        # Run all tests
        passed = 0
        failed = 0
        errors = 0
        
        for feature_name, test_func in features:
            result = self.test_feature(feature_name, test_func)
            if result:
                passed += 1
            else:
                status = self.test_results[feature_name]["status"]
                if status == "ERROR":
                    errors += 1
                else:
                    failed += 1
            time.sleep(0.5)  # Small delay between tests
        
        # Print summary
        self.log("=" * 50, "INFO")
        self.log("🎯 TEST SUMMARY", "INFO")
        self.log(f"✅ Passed: {passed}", "INFO")
        self.log(f"❌ Failed: {failed}", "INFO")
        self.log(f"💥 Errors: {errors}", "INFO")
        self.log(f"📊 Total: {passed + failed + errors}", "INFO")
        
        success_rate = (passed / (passed + failed + errors)) * 100 if (passed + failed + errors) > 0 else 0
        self.log(f"📈 Success Rate: {success_rate:.1f}%", "INFO")
        
        # Print detailed results if verbose
        if self.verbose:
            self.log("\n📋 DETAILED RESULTS:", "INFO")
            for feature, result in self.test_results.items():
                status = result["status"]
                if status == "ERROR":
                    self.log(f"  {feature}: {status} - {result.get('error', 'Unknown error')}", "ERROR")
                else:
                    self.log(f"  {feature}: {status}", "INFO")
        
        return success_rate >= 80  # Consider successful if 80%+ tests pass

def main():
    parser = argparse.ArgumentParser(description='Complete system test suite')
    parser.add_argument('--feature', choices=['all', 'backend', 'gsm', 'core'], 
                       default='all', help='Feature to test')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--output', help='Output results to file')
    
    args = parser.parse_args()
    
    tester = SystemTester(verbose=args.verbose)
    
    if args.feature == 'all':
        success = tester.run_all_tests()
    elif args.feature == 'backend':
        success = tester.test_feature("Backend Services", tester.test_backend_services)
    elif args.feature == 'gsm':
        success = tester.test_feature("GSM Services", tester.test_gsm_services)
    else:
        print("Invalid feature selection")
        return
    
    # Save results to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(tester.test_results, f, indent=2)
        print(f"Results saved to {args.output}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
