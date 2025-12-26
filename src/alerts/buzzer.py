class Buzzer:
    def __init__(self):
        self.active = False

    def start(self):
        if not self.active:
            self.active = True
            print("BUZZER ON")

    def stop(self):
        if self.active:
            self.active = False
            print("BUZZER OFF")
