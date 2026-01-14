"""
Enhanced Main Application for Complete Elderly Monitoring System

Integrates all components:
- Enhanced hardware interface with simulation and real device support
- Multi-layer fall detection (threshold + ML + validation)
- Centralized decision engine with explainable AI
- Multi-level alert system with escalation
- Range and vicinity awareness
- Continuous learning and feedback
- Demo mode with simulated scenarios
"""

import asyncio
import time
import signal
import sys
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Import all system components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensors.enhanced_hardware_interface import (
    initialize_hardware, get_sensor_data
)
from detection.feature_extraction import (
    initialize_feature_extractor, get_feature_extractor, extract_features_from_data
)
from detection.multi_layer_fall_detection import (
    initialize_fall_detector, get_fall_detector, detect_fall
)
from detection.decision_engine import (
    initialize_decision_engine, get_decision_engine, make_decision
)
from alerts.multi_level_alert_system import (
    initialize_alert_system, get_alert_system, send_alert, AlertType, AlertLevel
)
from location.vicinity_awareness import (
    initialize_vicinity_system, get_vicinity_system, update_patient_location
)
from learning.patient_learning_system import (
    initialize_learning_system, get_learning_system, 
    add_patient_learning_data, add_learning_feedback
)
from connection.connection_range_monitor import (
    initialize_connection_monitor, get_connection_monitor,
    start_connection_monitoring, get_connection_status
)
from detection.wearable_detection import (
    initialize_wearable_detection, get_wearable_detection,
    start_wearable_monitoring, get_wear_status
)

# Configuration
DEMO_MODE = True
BACKEND_URL = "http://localhost:5000/api"
PATIENT_ID = "demo_patient"
LOG_LEVEL = logging.INFO

class ElderlyMonitoringSystem:
    """Main application class for the elderly monitoring system."""
    
    def __init__(self):
        self.running = False
        self.demo_mode = DEMO_MODE
        self.backend_url = BACKEND_URL
        self.patient_id = PATIENT_ID
        
        # Component instances
        self.hardware_interface = None
        self.feature_extractor = None
        self.fall_detector = None
        self.decision_engine = None
        self.alert_system = None
        self.vicinity_system = None
        self.learning_system = None
        self.connection_monitor = None
        self.wearable_detection = None
        
        # System state
        self.last_sensor_read = 0
        self.last_feature_extraction = 0
        self.last_decision = 0
        self.sensor_read_interval = 0.1  # 100ms (10 Hz)
        self.feature_extraction_interval = 1.0  # 1 second
        self.decision_interval = 1.0  # 1 second
        
        # Statistics
        self.stats = {
            "sensor_reads": 0,
            "feature_extractions": 0,
            "fall_detections": 0,
            "decisions_made": 0,
            "alerts_sent": 0,
            "system_uptime": 0,
            "errors": 0
        }
        
        # Demo scenarios
        self.demo_scenarios = [
            "normal_activity",
            "walking",
            "sitting", 
            "fall_simulation",
            "health_anomaly",
            "device_offline"
        ]
        self.current_scenario = "normal_activity"
        self.scenario_start_time = 0
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=LOG_LEVEL,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('elderly_monitoring.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Elderly Monitoring System starting up...")
    
    async def initialize(self):
        """Initialize all system components."""
        try:
            self.logger.info("Initializing system components...")
            
            # Initialize hardware interface
            self.hardware_interface = initialize_hardware(
                use_real_hardware=not self.demo_mode,
                serial_port=None  # Auto-detect or use simulation
            )
            
            # Initialize feature extractor
            self.feature_extractor = initialize_feature_extractor(
                window_size=30,
                sampling_rate=10  # 10 Hz
            )
            
            # Initialize fall detector
            self.fall_detector = initialize_fall_detector()
            
            # Initialize decision engine
            self.decision_engine = initialize_decision_engine()
            
            # Initialize alert system
            self.alert_system = initialize_alert_system(
                backend_url=self.backend_url,
                patient_id=self.patient_id
            )
            
            # Initialize vicinity awareness
            self.vicinity_system = initialize_vicinity_system(
                backend_url=self.backend_url,
                patient_id=self.patient_id
            )
            
            # Initialize continuous learning system
            self.learning_system = initialize_learning_system("models/")
            
            # Initialize connection range monitor
            self.connection_monitor = initialize_connection_monitor(
                backend_url=self.backend_url,
                patient_id=self.patient_id
            )
            
            # Initialize wearable detection system
            self.wearable_detection = initialize_wearable_detection(
                backend_url=self.backend_url,
                patient_id=self.patient_id
            )
            
            # Add alert callback
            self.alert_system.add_alert_callback(self.handle_alert_callback)
            
            # Start alert system
            self.alert_system.start()
            
            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize system: {e}")
            return False
    
    async def start(self):
        """Start the main monitoring loop."""
        if not await self.initialize():
            return False
        
        self.running = True
        self.start_time = time.time()
        
        self.logger.info("🎯 Starting main monitoring loop...")
        
        try:
            # Main monitoring loop
            while self.running:
                loop_start = time.time()
                
                # Read sensor data
                await self.read_sensor_data()
                
                # Extract features
                await self.extract_features()
                
                # Process fall detection
                await self.process_fall_detection()
                
                # Make decisions
                await self.make_decisions()
                
                # Update vicinity awareness
                await self.update_vicinity()
                
                # Check connection status
                await self.check_connection_status()
                
                # Check wearable status
                await self.check_wearable_status()
                
                # Process demo scenarios
                if self.demo_mode:
                    await self.process_demo_scenarios()
                
                # Update statistics
                self.update_statistics()
                
                # Maintain loop timing
                loop_duration = time.time() - loop_start
                if loop_duration < self.sensor_read_interval:
                    await asyncio.sleep(self.sensor_read_interval - loop_duration)
        
        except KeyboardInterrupt:
            self.logger.info("⏹️ Received interrupt signal")
        except Exception as e:
            self.logger.error(f"❌ Error in main loop: {e}")
        finally:
            await self.shutdown()
    
    async def read_sensor_data(self):
        """Read data from all sensors."""
        current_time = time.time()
        
        if current_time - self.last_sensor_read >= self.sensor_read_interval:
            try:
                # Get comprehensive sensor data
                sensor_data = get_sensor_data()
                
                if sensor_data:
                    self.stats["sensor_reads"] += 1
                    self.last_sensor_read = current_time
                    
                    # Log sensor data periodically
                    if self.stats["sensor_reads"] % 100 == 0:
                        self.logger.debug(f"📊 Sensor data: {sensor_data}")
                
            except Exception as e:
                self.logger.error(f"❌ Error reading sensor data: {e}")
                self.stats["errors"] += 1
    
    async def extract_features(self):
        """Extract features from sensor data."""
        current_time = time.time()
        
        if current_time - self.last_feature_extraction >= self.feature_extraction_interval:
            try:
                # Get current sensor data
                sensor_data = get_sensor_data()
                
                if sensor_data:
                    # Extract features
                    if hasattr(self.feature_extractor, 'update_data'):
                        features = extract_features_from_data(sensor_data)
                    else:
                        # Direct update method
                        ax = sensor_data.get('ax', 0)
                        ay = sensor_data.get('ay', 0)
                        az = sensor_data.get('az', 0)
                        gx = sensor_data.get('gx', 0)
                        gy = sensor_data.get('gy', 0)
                        gz = sensor_data.get('gz', 0)
                        timestamp = sensor_data.get('timestamp', time.time())
                        
                        self.feature_extractor.update(ax, ay, az, gx, gy, gz, timestamp)
                        features = self.feature_extractor.get_current_features()
                    
                    if features:
                        self.stats["feature_extractions"] += 1
                        self.last_feature_extraction = current_time
                        
                        # Store features for other components
                        if hasattr(features, '__dict__'):
                            self.current_features = features.__dict__
                        elif isinstance(features, dict):
                            self.current_features = features
                        else:
                            self.current_features = {"features": str(features)}
                
            except Exception as e:
                self.logger.error(f"❌ Error extracting features: {e}")
                self.stats["errors"] += 1
    
    async def process_fall_detection(self):
        """Process fall detection using multi-layer approach."""
        try:
            if hasattr(self, 'current_features') and self.current_features:
                # Run multi-layer fall detection
                detection_results = detect_fall(self.current_features)
                
                if detection_results:
                    self.stats["fall_detections"] += 1
                    
                    # Store for decision engine
                    self.current_detection_results = detection_results
                    
                    # Log significant detections
                    if detection_results.get("final_decision") == "fall_detected":
                        self.logger.warning(f"🚨 Fall detected: {detection_results}")
                
        except Exception as e:
            self.logger.error(f"❌ Error in fall detection: {e}")
            self.stats["errors"] += 1
    
    async def make_decisions(self):
        """Make decisions using the centralized decision engine."""
        current_time = time.time()
        
        if current_time - self.last_decision >= self.decision_interval:
            try:
                if (hasattr(self, 'current_features') and self.current_features and
                    hasattr(self, 'current_detection_results')):
                    
                    # Make comprehensive decision
                    decision = make_decision(
                        self.current_features,
                        self.current_detection_results
                    )
                    
                    if decision:
                        self.stats["decisions_made"] += 1
                        self.last_decision = current_time
                        
                        # Store for alert processing
                        self.current_decision = decision
                        
                        # Process decision for alerts
                        await self.process_decision_for_alerts(decision)
                        
                        # Add to learning system
                        if hasattr(self, 'learning_system') and self.learning_system:
                            data_point_id = add_patient_learning_data(
                                self.patient_id,
                                self.current_features,
                                decision.get('decision_type', 'unknown'),
                                decision.get('confidence', 0),
                                None  # Actual outcome to be provided via feedback
                            )
                            self.logger.info(f"📚 Added data point to learning system: {data_point_id}")
                
            except Exception as e:
                self.logger.error(f"❌ Error making decisions: {e}")
                self.stats["errors"] += 1
    
    async def process_decision_for_alerts(self, decision: Dict[str, Any]):
        """Process decision results and trigger appropriate alerts."""
        try:
            decision_type = decision.get("decision_type")
            urgency = decision.get("urgency_level")
            confidence = decision.get("confidence", 0)
            
            # Map decision types to alert types and levels
            alert_mapping = {
                "fall_detected": (AlertType.FALL_DETECTED, AlertLevel.CRITICAL),
                "pre_fall_warning": (AlertType.PRE_FALL_WARNING, AlertLevel.WARNING),
                "health_alert": (AlertType.HEALTH_ANOMALY, AlertLevel.WARNING),
                "emergency_response": (AlertType.EMERGENCY, AlertLevel.EMERGENCY)
            }
            
            if decision_type in alert_mapping and confidence > 0.6:
                alert_type, alert_level = alert_mapping[decision_type]
                
                # Create alert message
                message = f"{decision_type.replace('_', ' ').title()}: {decision.get('explanation', '')}"
                
                # Add metadata
                metadata = {
                    "decision_id": str(decision.get("timestamp")),
                    "confidence": confidence,
                    "urgency": urgency,
                    "fall_type": decision.get("fall_type"),
                    "severity": decision.get("severity"),
                    "triggered_rules": decision.get("triggered_rules", [])
                }
                
                # Send alert
                alert_id = await send_alert(alert_type, alert_level, message, metadata)
                
                if alert_id:
                    self.stats["alerts_sent"] += 1
                    self.logger.info(f"🚨 Alert sent: {alert_type.value} - {message}")
        
        except Exception as e:
            self.logger.error(f"❌ Error processing decision for alerts: {e}")
            self.stats["errors"] += 1
    
    async def update_vicinity(self):
        """Update vicinity awareness system."""
        try:
            # Simulate location updates in demo mode
            if self.demo_mode and time.time() % 30 < 1:  # Every 30 seconds
                # Simulate patient being in home zone
                self.vicinity_system.simulate_location_update("home")
        
        except Exception as e:
            self.logger.error(f"❌ Error updating vicinity: {e}")
            self.stats["errors"] += 1
    
    async def check_connection_status(self):
        """Check WiFi connection status to waist band."""
        try:
            if self.connection_monitor:
                # Get connection status
                status = get_connection_status()
                
                # Log connection issues
                if status.get("current_status") in ["out_of_range", "disconnected"]:
                    self.logger.warning(f"⚠️ Connection issue: {status.get('current_status')}")
                
                # Update statistics
                self.stats["connection_uptime"] = status.get("uptime_percentage", 0)
                self.stats["connection_alerts"] = status.get("active_alerts", 0)
        
        except Exception as e:
            self.logger.error(f"❌ Error checking connection status: {e}")
            self.stats["errors"] += 1
    
    async def check_wearable_status(self):
        """Check if senior citizen is wearing the waist band."""
        try:
            if self.wearable_detection:
                # Get wear status
                status = get_wear_status()
                
                # Log wear status issues
                current_status = status.get("current_status", "unknown")
                if current_status in ["not_worn", "uncertain"]:
                    self.logger.warning(f"👕 Wear status issue: {current_status} (confidence: {status.get('confidence', 0):.2f})")
                
                # Update statistics
                self.stats["wear_status"] = current_status
                self.stats["wear_confidence"] = status.get("confidence", 0)
                self.stats["wear_percentage"] = status.get("wear_percentage_last_hour", 0)
                self.stats["wear_alerts"] = status.get("active_alerts", 0)
        
        except Exception as e:
            self.logger.error(f"❌ Error checking wearable status: {e}")
            self.stats["errors"] += 1
    
    async def process_demo_scenarios(self):
        """Process demo scenarios for testing and demonstration."""
        if not self.demo_mode:
            return
        
        current_time = time.time()
        
        # Change scenario every 60 seconds
        if current_time - self.scenario_start_time > 60:
            # Rotate through scenarios
            current_index = self.demo_scenarios.index(self.current_scenario)
            next_index = (current_index + 1) % len(self.demo_scenarios)
            self.current_scenario = self.demo_scenarios[next_index]
            self.scenario_start_time = current_time
            
            self.logger.info(f"🎭 Demo scenario: {self.current_scenario}")
            
            # Configure hardware for scenario
            await self.configure_demo_scenario(self.current_scenario)
    
    async def configure_demo_scenario(self, scenario: str):
        """Configure hardware simulation for demo scenario."""
        try:
            if self.hardware_interface and hasattr(self.hardware_interface, 'set_simulation_scenario'):
                await self.hardware_interface.set_simulation_scenario(scenario)
        
        except Exception as e:
            self.logger.error(f"❌ Error configuring demo scenario: {e}")
    
    def handle_alert_callback(self, alert):
        """Handle alert callbacks."""
        self.logger.info(f"🔔 Alert callback: {alert.type.value} - {alert.message}")
        
        # Store alert for statistics
        if not hasattr(self, 'recent_alerts'):
            self.recent_alerts = []
        
        self.recent_alerts.append({
            "id": alert.id,
            "type": alert.type.value,
            "level": alert.level.value,
            "timestamp": alert.timestamp,
            "acknowledged": alert.acknowledged
        })
        
        # Keep only recent alerts
        if len(self.recent_alerts) > 50:
            self.recent_alerts = self.recent_alerts[-50:]
    
    def update_statistics(self):
        """Update system statistics."""
        if hasattr(self, 'start_time'):
            self.stats["system_uptime"] = time.time() - self.start_time
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        status = {
            "running": self.running,
            "demo_mode": self.demo_mode,
            "uptime": self.stats["system_uptime"],
            "statistics": self.stats.copy(),
            "components": {
                "hardware": self.hardware_interface.get_status() if self.hardware_interface else "not_initialized",
                "feature_extractor": "initialized" if self.feature_extractor else "not_initialized",
                "fall_detector": "initialized" if self.fall_detector else "not_initialized",
                "decision_engine": "initialized" if self.decision_engine else "not_initialized",
                "alert_system": self.alert_system.get_system_status() if self.alert_system else "not_initialized",
                "vicinity_system": "initialized" if self.vicinity_system else "not_initialized"
            },
            "current_scenario": self.current_scenario if self.demo_mode else "production",
            "recent_alerts": getattr(self, 'recent_alerts', [])[-10:]  # Last 10 alerts
        }
        
        # Add current state if available
        if hasattr(self, 'current_features'):
            status["current_features"] = {
                "accel_magnitude": self.current_features.get('accel_magnitude_mean', 0),
                "anomaly_score": self.current_features.get('anomaly_score', 0),
                "activity_level": self.current_features.get('activity_level', 'unknown')
            }
        
        if hasattr(self, 'current_decision'):
            status["current_decision"] = {
                "type": self.current_decision.get('decision_type', 'unknown'),
                "urgency": self.current_decision.get('urgency_level', 'unknown'),
                "confidence": self.current_decision.get('confidence', 0)
            }
        
        return status
    
    async def shutdown(self):
        """Shutdown the system gracefully."""
        self.logger.info("🛑 Shutting down system...")
        
        self.running = False
        
        # Stop alert system
        if self.alert_system:
            self.alert_system.stop()
        
        # Stop hardware interface
        if self.hardware_interface:
            self.hardware_interface.stop()
        
        # Log final statistics
        self.logger.info(f"📊 Final statistics: {self.stats}")
        
        self.logger.info("✅ System shutdown complete")

# Global system instance
_monitoring_system = None

async def main():
    """Main entry point."""
    global _monitoring_system
    
    # Create and start system
    _monitoring_system = ElderlyMonitoringSystem()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        if _monitoring_system:
            _monitoring_system.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the system
    await _monitoring_system.start()

def get_system_status() -> Dict[str, Any]:
    """Get current system status."""
    if _monitoring_system:
        return _monitoring_system.get_system_status()
    return {"status": "not_running"}

def get_monitoring_system() -> ElderlyMonitoringSystem:
    """Get the global monitoring system instance."""
    return _monitoring_system

if __name__ == "__main__":
    print("🚀 Starting Elderly Monitoring System...")
    print("=" * 50)
    print(f"Demo Mode: {DEMO_MODE}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Patient ID: {PATIENT_ID}")
    print("=" * 50)
    
    # Run the system
    asyncio.run(main())
