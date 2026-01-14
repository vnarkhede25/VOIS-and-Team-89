"""
Hardware Connection Test Script

Test script to verify hardware prototype connection to the elderly monitoring system.
Tests each sensor individually and then the complete system.

Usage:
    python hardware_connection_test.py [--port COM3] [--baudrate 115200]
"""

import sys
import time
import argparse
import serial.tools.list_ports

# Add project path
sys.path.append('..')

from src.sensors.hardware_interface import RealMPU6050
from src.sensors.enhanced_hardware_interface import RealWearableSensor

def find_serial_ports():
    """Find available serial ports."""
    ports = serial.tools.list_ports.comports()
    print("🔍 Available Serial Ports:")
    for i, port in enumerate(ports):
        print(f"  {i+1}. {port.device} - {port.description}")
    return ports

def test_serial_connection(port, baudrate=115200):
    """Test basic serial connection."""
    print(f"\n🔌 Testing serial connection to {port} at {baudrate} baud...")
    
    try:
        ser = serial.Serial(port, baudrate, timeout=2)
        time.sleep(2)
        
        # Test communication
        ser.write(b"PING\n")
        response = ser.readline().decode().strip()
        
        if response == "PONG":
            print("✅ Serial connection successful!")
            ser.close()
            return True
        else:
            print(f"❌ Unexpected response: {response}")
            ser.close()
            return False
            
    except Exception as e:
        print(f"❌ Serial connection failed: {e}")
        return False

def test_mpu6050(port, baudrate=115200):
    """Test MPU6050 sensor connection."""
    print(f"\n🎯 Testing MPU6050 sensor...")
    
    try:
        sensor = RealMPU6050(port, baudrate)
        
        if sensor.connect():
            print("✅ MPU6050 connected successfully!")
            
            # Test sensor readings
            ax, ay, az = sensor.get_acceleration()
            print(f"📊 Acceleration: X={ax:.3f}, Y={ay:.3f}, Z={az:.3f}")
            
            # Check for reasonable values
            if abs(ax) < 20 and abs(ay) < 20 and abs(az) < 20:
                print("✅ MPU6050 readings look normal")
                return True
            else:
                print("⚠️ MPU6050 readings may be incorrect")
                return False
        else:
            print("❌ Failed to connect to MPU6050")
            return False
            
    except Exception as e:
        print(f"❌ MPU6050 test failed: {e}")
        return False

def test_complete_system(port, baudrate=115200):
    """Test complete hardware system."""
    print(f"\n🛠️ Testing complete hardware system...")
    
    try:
        # Initialize enhanced hardware interface
        from src.sensors.enhanced_hardware_interface import initialize_hardware
        
        hardware = initialize_hardware(
            use_real_hardware=True,
            serial_port=port,
            baudrate=baudrate
        )
        
        print("✅ Hardware interface initialized!")
        
        # Test sensor data collection
        print("\n📊 Testing sensor data collection...")
        for i in range(10):
            sensor_data = hardware.get_sensor_data()
            
            if sensor_data:
                print(f"Sample {i+1}:")
                print(f"  Motion: ax={sensor_data['motion'].get('ax', 0):.2f}, "
                      f"ay={sensor_data['motion'].get('ay', 0):.2f}, "
                      f"az={sensor_data['motion'].get('az', 0):.2f}")
                print(f"  Vitals: HR={sensor_data['vitals'].get('heart_rate', 0)}, "
                      f"Temp={sensor_data['vitals'].get('temperature', 0):.1f}°C")
                print(f"  Battery: {sensor_data['battery'].get('level', 0)}%")
                print(f"  Device: {sensor_data['device_status'].get('worn', False)}")
                print()
            else:
                print(f"Sample {i+1}: No data received")
            
            time.sleep(1)
        
        print("✅ Complete system test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Complete system test failed: {e}")
        return False

def interactive_test(port, baudrate=115200):
    """Interactive test mode."""
    print(f"\n🎮 Interactive test mode - Type commands to send to device:")
    print("Available commands: PING, GET_DATA, CALIBRATE, BUZZER_ON, BUZZER_OFF, STATUS")
    print("Type 'quit' to exit\n")
    
    try:
        ser = serial.Serial(port, baudrate, timeout=2)
        time.sleep(2)
        
        while True:
            command = input(">>> ").strip()
            
            if command.lower() == 'quit':
                break
            elif command:
                ser.write((command + "\n").encode())
                response = ser.readline().decode().strip()
                print(f"Response: {response}")
        
        ser.close()
        print("✅ Interactive test completed")
        
    except Exception as e:
        print(f"❌ Interactive test failed: {e}")

def main():
    parser = argparse.ArgumentParser(description='Test hardware prototype connection')
    parser.add_argument('--port', help='Serial port (e.g., COM3 or /dev/ttyUSB0)')
    parser.add_argument('--baudrate', type=int, default=115200, help='Baud rate (default: 115200)')
    parser.add_argument('--test', choices=['serial', 'mpu6050', 'complete', 'interactive'], 
                       default='complete', help='Test type')
    parser.add_argument('--list-ports', action='store_true', help='List available serial ports')
    
    args = parser.parse_args()
    
    print("🧪 Hardware Prototype Connection Test")
    print("=" * 50)
    
    if args.list_ports:
        find_serial_ports()
        return
    
    # Auto-detect port if not specified
    if not args.port:
        ports = serial.tools.list_ports.comports()
        if ports:
            args.port = ports[0].device
            print(f"📍 Auto-detected port: {args.port}")
        else:
            print("❌ No serial ports found. Please specify --port")
            return
    
    print(f"🔌 Using port: {args.port}")
    print(f"📡 Using baudrate: {args.baudrate}")
    
    # Run selected test
    if args.test == 'serial':
        test_serial_connection(args.port, args.baudrate)
    elif args.test == 'mpu6050':
        test_mpu6050(args.port, args.baudrate)
    elif args.test == 'complete':
        test_complete_system(args.port, args.baudrate)
    elif args.test == 'interactive':
        interactive_test(args.port, args.baudrate)

if __name__ == '__main__':
    main()
