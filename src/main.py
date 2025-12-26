from sensors.mpu6050_simulator import get_motion_data
from detection.motion_analysis import calculate_magnitude
from detection.threshold_fall import detect_fall
from detection.posture_detection import detect_posture
from detection.inactivity import is_inactive
from decision_engine.state_machine import FallStateMachine
from alerts.buzzer import Buzzer
from alerts.alert_controller import AlertController
import time

mode = "fall" 

fsm = FallStateMachine()
buzzer = Buzzer()
alerts = AlertController(buzzer)

prev_magnitude = 0

while True:
    ax, ay, az = get_motion_data(mode)
    magnitude = calculate_magnitude(ax, ay, az)

    spike = detect_fall(magnitude)
    posture = detect_posture(az)
    inactive = is_inactive(magnitude, prev_magnitude)

    state = fsm.update(spike, posture, inactive)

    alerts.handle(state)

    print(
        f"MAG:{magnitude:.2f} | "
        f"POSTURE:{posture} | "
        f"STATE:{state}"
    )

    prev_magnitude = magnitude
    time.sleep(1)
