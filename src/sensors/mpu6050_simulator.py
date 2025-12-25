import random
import time

def get_motion_data():
    ax = random.uniform(-2, 2)
    ay = random.uniform(-2, 2)
    az = random.uniform(8, 12) 
    return ax, ay, az

if __name__ == "__main__":
    while True:
        print(get_motion_data())
        time.sleep(1)
