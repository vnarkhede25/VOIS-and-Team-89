import random
import time
import math

def normal_motion():
    """
    Simulates normal standing motion with gravity primarily on Z-axis.
    Device orientation: upright (vertical)
    Gravity vector: (0, 0, 9.8) m/s² in device frame
    """
    # Small random movements around gravity vector
    ax = random.uniform(-0.5, 0.5)  # Minimal X movement
    ay = random.uniform(-0.5, 0.5)  # Minimal Y movement  
    az = random.uniform(9.3, 10.3)  # Strong Z component (gravity)
    return ax, ay, az

def sitting_motion():
    """
    Simulates sitting posture with moderate tilt.
    Device orientation: tilted forward/backward
    Gravity vector distributed between Z and X/Y axes
    """
    # Moderate tilt creates gravity components on multiple axes
    tilt_angle = random.uniform(30, 60)  # degrees from vertical
    tilt_rad = math.radians(tilt_angle)
    
    # Gravity distributed based on tilt angle
    gravity_component = 9.8
    ax = gravity_component * math.sin(tilt_rad) + random.uniform(-0.3, 0.3)
    ay = random.uniform(-0.3, 0.3)
    az = gravity_component * math.cos(tilt_rad) + random.uniform(-0.3, 0.3)
    return ax, ay, az

def lying_motion():
    """
    Simulates lying posture with device horizontal.
    Device orientation: horizontal (flat)
    Gravity vector primarily on X or Y axis
    
    Note: Focus on side-lying positions as face up/down is hard to detect
    and less common with wearable devices.
    """
    # Device is horizontal, gravity acts on X/Y plane
    # Prioritize side positions (more realistic for wearables)
    orientation = random.choice(['side_x', 'side_y', 'side_x', 'side_y', 'face_up', 'face_down'])
    
    if orientation == 'side_x':
        # Gravity on X-axis (device on side, X vertical)
        ax = 9.8 + random.uniform(-0.3, 0.3)
        ay = random.uniform(-0.2, 0.2)
        az = random.uniform(-0.2, 0.2)
    elif orientation == 'side_y':
        # Gravity on Y-axis (device on side, Y vertical)
        ax = random.uniform(-0.2, 0.2)
        ay = 9.8 + random.uniform(-0.3, 0.3)
        az = random.uniform(-0.2, 0.2)
    elif orientation == 'face_up':
        # Device face up, gravity on negative Z-axis (device on back)
        ax = random.uniform(-0.2, 0.2)
        ay = random.uniform(-0.2, 0.2)
        az = -9.8 + random.uniform(-0.3, 0.3)
    else:  # face_down
        # Device face down, gravity on positive Z-axis (device on front)
        ax = random.uniform(-0.2, 0.2)
        ay = random.uniform(-0.2, 0.2)
        az = 9.8 + random.uniform(-0.3, 0.3)
    
    return ax, ay, az

def fall_motion():
    """
    Simulates fall dynamics with high acceleration and orientation changes.
    Fall creates sudden acceleration spikes and orientation changes.
    """
    # High acceleration during impact
    ax = random.uniform(-15, 15)  # High X acceleration
    ay = random.uniform(-15, 15)  # High Y acceleration
    az = random.uniform(15, 25)   # Very high Z acceleration
    return ax, ay, az

def get_motion_data(mode="normal"):
    """
    Get simulated motion data based on mode.
    
    Args:
        mode: "normal" (standing), "sitting", "lying", or "fall"
    
    Returns:
        tuple: (ax, ay, az) acceleration values in m/s²
    """
    if mode == "fall":
        return fall_motion()
    elif mode == "sitting":
        return sitting_motion()
    elif mode == "lying":
        return lying_motion()
    else:
        return normal_motion()

if __name__ == "__main__":
    # Test different postures
    modes = ["normal", "sitting", "lying", "fall"]
    
    while True:
        for mode in modes:
            ax, ay, az = get_motion_data(mode)
            magnitude = math.sqrt(ax**2 + ay**2 + az**2)
            print(f"{mode.upper()}: ax={ax:.2f}, ay={ay:.2f}, az={az:.2f}, mag={magnitude:.2f}")
            time.sleep(2)
