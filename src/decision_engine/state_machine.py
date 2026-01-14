class FallStateMachine:
    """
    State machine for fall detection with pre-fall instability integration.
    
    Safety: Ensures proper fall confirmation and prevents false alarms.
    Reason: Multi-stage detection reduces false positives while maintaining responsiveness.
    """
    
    def __init__(self):
        self.state = "NORMAL"
        # Fall timer: Counts time in POSSIBLE_FALL state for confirmation
        self.fall_timer = 0
        # Confirmation window: 5 samples ensures fall is sustained, not momentary
        self.confirmation_window = 5
        # Inactivity window: 3 samples confirms user is still after impact
        self.min_inactivity_window = 3
        self.inactivity_count = 0
        
        # Pre-fall instability tracking
        self.instability_timer = 0
        self.risk_state = "LOW"  # LOW, MEDIUM, HIGH
        self.risk_state_timer = 0
        
        # Risk thresholds for state transitions
        # Low: 0.3 - Normal daily activities
        # Medium: 0.6 - Unusual but not dangerous movements
        # High: 0.8 - Pre-fall patterns detected
        self.low_risk_threshold = 0.3
        self.medium_risk_threshold = 0.6
        self.high_risk_threshold = 0.8
        
        # Risk state persistence (avoid rapid state changes)
        # Safety: Prevents oscillation between risk states due to sensor noise
        self.risk_persistence_window = 2  # Consecutive readings needed
        
    def update(self, spike, posture, inactive, post_fall_state=False, instability_risk=0.0):
        """
        Update state machine with fall detection and pre-fall instability data.
        
        Safety: Prioritizes confirmed falls while monitoring pre-fall patterns.
        Reason: Falls require immediate response; pre-fall states allow early intervention.
        
        Args:
            spike: Fall spike detected
            posture: Current posture (standing/sitting/lying)
            inactive: Inactivity state
            post_fall_state: Post-fall recovery state
            instability_risk: Pre-fall risk score (0-1)
            
        Returns:
            str: Current state
        """
        # Update risk state based on instability score
        self._update_risk_state(instability_risk)
        
        if self.state == "NORMAL":
            if spike:
                # Fall detection takes priority over instability
                # Safety: Immediate fall detection prevents delayed response
                self.state = "POSSIBLE_FALL"
                self.fall_timer = 0
                self.inactivity_count = 0
            elif self.risk_state == "HIGH":
                # High risk triggers pre-fall warning
                # Safety: Early warning allows user to prepare or prevent fall
                self.state = "PRE_FALL_WARNING"
            elif self.risk_state == "MEDIUM":
                # Medium risk enters monitoring state
                # Safety: Monitoring tracks concerning patterns without alarming
                self.state = "MONITORING"

        elif self.state == "MONITORING":
            if spike:
                # Fall detection takes priority
                self.state = "POSSIBLE_FALL"
                self.fall_timer = 0
                self.inactivity_count = 0
            elif self.risk_state == "LOW":
                # Risk subsided, return to normal
                self.state = "NORMAL"
            elif self.risk_state == "HIGH":
                # Escalate to pre-fall warning
                self.state = "PRE_FALL_WARNING"

        elif self.state == "PRE_FALL_WARNING":
            if spike:
                # Fall detected during high risk - high confidence
                self.state = "POSSIBLE_FALL"
                self.fall_timer = 0
                self.inactivity_count = 0
            elif self.risk_state == "LOW":
                # Risk significantly reduced
                self.state = "NORMAL"
            elif self.risk_state == "MEDIUM":
                # Risk reduced but still elevated
                self.state = "MONITORING"

        elif self.state == "POSSIBLE_FALL":
            self.fall_timer += 1
            
            if posture == "lying" and inactive:
                self.inactivity_count += 1
                if self.inactivity_count >= self.min_inactivity_window:
                    self.state = "CONFIRMED_FALL"
            elif post_fall_state and self.fall_timer >= 2:
                self.state = "CONFIRMED_FALL"
            elif self.fall_timer > self.confirmation_window:
                self.state = "NORMAL"
                self.inactivity_count = 0

        elif self.state == "CONFIRMED_FALL":
            self.state = "ALERT"

        elif self.state == "ALERT":
            if self.fall_timer > self.confirmation_window + 10:
                self.state = "NORMAL"
                self.fall_timer = 0
                self.inactivity_count = 0
                self.risk_state_timer = 0

        return self.state
    
    def _update_risk_state(self, instability_risk):
        """
        Update risk state based on current instability score.
        
        Args:
            instability_risk: Current risk score (0-1)
        """
        # Determine current risk level
        if instability_risk < self.low_risk_threshold:
            current_risk_level = "LOW"
        elif instability_risk < self.medium_risk_threshold:
            current_risk_level = "MEDIUM"
        elif instability_risk < self.high_risk_threshold:
            current_risk_level = "HIGH"
        else:
            current_risk_level = "CRITICAL"
        
        # Update risk state with persistence
        if current_risk_level == self.risk_state:
            self.risk_state_timer += 1
        else:
            # Risk level changed, reset timer
            self.risk_state_timer = 1
            
            # Change state immediately if new level is higher
            if (current_risk_level == "MEDIUM" and self.risk_state == "LOW") or \
               (current_risk_level == "HIGH" and self.risk_state in ["LOW", "MEDIUM"]) or \
               (current_risk_level == "CRITICAL"):
                self.risk_state = current_risk_level
                self.risk_state_timer = 1
            elif self.risk_state_timer >= self.risk_persistence_window:
                # Allow downward state changes with persistence
                self.risk_state = current_risk_level
                self.risk_state_timer = 1
            else:
                # Keep previous state until persistence is met
                pass
    
    def get_risk_status(self):
        """
        Get current risk status for monitoring.
        
        Returns:
            dict: Risk status information
        """
        return {
            'risk_state': self.risk_state,
            'risk_timer': self.risk_state_timer,
            'thresholds': {
                'low': self.low_risk_threshold,
                'medium': self.medium_risk_threshold,
                'high': self.high_risk_threshold
            }
        }
    
    def get_instability_status(self):
        """
        Get current instability status for monitoring.
        
        Returns:
            dict: Instability status information
        """
        return {
            'risk_state': self.risk_state,
            'risk_timer': self.risk_state_timer,
            'active': self.risk_state != "LOW"
        }
