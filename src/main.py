from sensors.mpu6050_simulator import get_motion_data
from detection.motion_analysis import calculate_magnitude
import time

while True:
    ax, ay, az = get_motion_data()
    magnitude = calculate_magnitude(ax, ay, az)

    print(f"AX:{ax:.2f} AY:{ay:.2f} AZ:{az:.2f} | MAG:{magnitude:.2f}")
    time.sleep(1)
