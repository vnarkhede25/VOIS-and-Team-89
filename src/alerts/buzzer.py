class Buzzer:
    """
    Simple buzzer simulation for fall detection alerts.
    Provides visual and audio feedback for demonstration.
    """
    
    def __init__(self):
        self.active = False
        self.pulse_count = 0

    def start(self):
        """Start continuous buzzer sound."""
        if not self.active:
            self.active = True
            print("🔊 BUZZER ON - Continuous alert")

    def stop(self):
        """Stop buzzer sound."""
        if self.active:
            self.active = False
            self.pulse_count = 0
            print("🔇 BUZZER OFF")

    def pulse(self, count=1, interval=0.5):
        """
        Create multiple short pulses of sound.
        
        Args:
            count: Number of pulses to generate
            interval: Time between pulses in seconds
        """
        for i in range(count):
            self.pulse_count += 1
            print(f"🔊 BUZZER PULSE #{self.pulse_count}")
            
            # In real hardware, this would create physical pulses
            # For simulation, we just log each pulse
            
            # Add delay between pulses if multiple
            if i < count - 1:
                import time
                time.sleep(interval)
        
    def is_active(self) -> bool:
        """Check if buzzer is currently active."""
        return self.active
    
    def get_status(self) -> dict:
        """Get current buzzer status."""
        return {
            'active': self.active,
            'pulse_count': self.pulse_count
        }
