class RangeMonitor:
    def __init__(self):
        self.connected = True
        self.disconnect_timer = 0

    def update(self, connected):
        if connected:
            self.disconnect_timer = 0
            self.connected = True
        else:
            self.disconnect_timer += 1
            self.connected = False

        if self.disconnect_timer > 5:
            return "OUT_OF_RANGE"

        return "IN_RANGE"
