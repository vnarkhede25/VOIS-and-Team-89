class AlertController:
    """
    Human-friendly alert controller with comfort and dignity constraints.
    
    Features:
    - Buzzer alerts for immediate fall detection
    - User cancellation window to prevent false alarms
    - Alert escalation management
    - Graceful alert reset and recovery
    - Comfort constraints (sleep suppression, sitting transitions)
    - Rate limiting for respectful notifications
    """
    
    def __init__(self, buzzer):
        """
        Initialize alert controller.
        
        Args:
            buzzer: Buzzer instance for audible alerts
        """
        self.buzzer = buzzer
        self.alert_sent = False
        self.timer = 0
        self.cancellation_window = 10  # Time window for user cancellation
        self.escalation_threshold = 15  # Timer for automatic escalation
        self.last_alert_time = None
        self.alert_history = []
        self.alert_active = False
        self.current_state = "NORMAL"  # Track current system state
        
        # Comfort and dignity constraints
        self.sleep_suppression_enabled = True
        self.sitting_transition_filter_enabled = True
        self.rate_limit_enabled = True
        
        # Rate limiting
        self.min_alert_interval = 30  # Minimum seconds between alerts
        self.last_notification_time = None
        
        # Sleep detection
        self.sleep_posture_threshold = 0.8  # Confidence threshold for sleep posture
        self.impact_detection_threshold = 15.0  # Acceleration threshold for impact
        
        # Sitting transition detection
        self.sitting_transition_window = 2.0  # Time window for sitting transitions
        self.last_sitting_transition = None
        
    def handle(self, state, user_response=None, posture=None, acceleration_magnitude=None):
        """
        Handle alert states with comfort and dignity constraints.
        
        Args:
            state: Current system state
            user_response: User input for cancellation (optional)
            posture: Current posture (for comfort constraints)
            acceleration_magnitude: Current acceleration magnitude (for impact detection)
        """
        current_time = self._get_current_time()
        self.current_state = state  # Track current state
        
        # Apply comfort and dignity constraints
        if self._should_suppress_alert(state, posture, acceleration_magnitude, current_time):
            self._log_suppressed_alert(state, posture, acceleration_magnitude)
            return
        
        # State-based alert handling
        if state == "ALERT":
            self._handle_alert_state(current_time, user_response)
        elif state == "PRE_FALL_WARNING":
            self._handle_pre_fall_warning(current_time, user_response)
        elif state in ["HIGH_RISK", "MONITORING"]:
            self._handle_monitoring_state(current_time, user_response)
        else:
            self._reset_alert_system()
    
    def _should_suppress_alert(self, state, posture, acceleration_magnitude, current_time):
        """
        Determine if alert should be suppressed based on comfort constraints.
        
        Returns:
            bool: True if alert should be suppressed
        """
        # Rate limiting check
        if self.rate_limit_enabled and self._is_rate_limited(current_time):
            return True
        
        # Sleep posture suppression
        if self.sleep_suppression_enabled and self._should_suppress_for_sleep(state, posture, acceleration_magnitude):
            return True
        
        # Sitting transition filtering
        if self.sitting_transition_filter_enabled and self._should_suppress_for_sitting_transition(state, posture, current_time):
            return True
        
        return False
    
    def _is_rate_limited(self, current_time):
        """
        Check if alert should be rate limited.
        
        Returns:
            bool: True if rate limited
        """
        if self.last_notification_time is None:
            return False
        
        # Simple time-based rate limiting
        time_diff = self._get_time_difference(current_time, self.last_notification_time)
        return time_diff < self.min_alert_interval
    
    def _should_suppress_for_sleep(self, state, posture, acceleration_magnitude):
        """
        Check if alert should be suppressed during sleep.
        
        Returns:
            bool: True if should suppress for sleep
        """
        # Only suppress alerts during sleep posture
        if posture != "lying":
            return False
        
        # Allow alerts for high-impact events (potential falls)
        if acceleration_magnitude and acceleration_magnitude > self.impact_detection_threshold:
            print(f"💤 Sleep posture detected but impact detected: {acceleration_magnitude:.1f} - Alert allowed")
            return False
        
        # Suppress non-impact alerts during sleep
        if state in ["PRE_FALL_WARNING", "HIGH_RISK", "MONITORING"]:
            print(f"💤 Sleep posture detected - Suppressing {state} alert for comfort")
            return True
        
        return False
    
    def _should_suppress_for_sitting_transition(self, state, posture, current_time):
        """
        Check if alert should be suppressed during sitting transitions.
        
        Returns:
            bool: True if should suppress for sitting transition
        """
        # Only apply to pre-fall warnings (most common false positive)
        if state != "PRE_FALL_WARNING":
            return False
        
        # Check if this is a sitting transition
        if posture == "sitting":
            if self.last_sitting_transition is None:
                self.last_sitting_transition = current_time
                return False
            
            # Check if within transition window
            time_diff = self._get_time_difference(current_time, self.last_sitting_transition)
            if time_diff < self.sitting_transition_window:
                print(f"🪑 Sitting transition detected - Suppressing alert for dignity")
                return True
        
        return False
    
    def _log_suppressed_alert(self, state, posture, acceleration_magnitude):
        """
        Log suppressed alerts for monitoring and debugging.
        """
        suppression_reason = []
        
        if self.rate_limit_enabled and self._is_rate_limited(self._get_current_time()):
            suppression_reason.append("rate_limited")
        
        if self.sleep_suppression_enabled and self._should_suppress_for_sleep(state, posture, acceleration_magnitude):
            suppression_reason.append("sleep_suppression")
        
        if self.sitting_transition_filter_enabled and self._should_suppress_for_sitting_transition(state, posture, self._get_current_time()):
            suppression_reason.append("sitting_transition")
        
        print(f"🔕 Alert suppressed: {state} - Reason: {', '.join(suppression_reason)}")
        
        # Log to history for analysis
        self.alert_history.append({
            'time': self._get_current_time(),
            'type': 'suppressed',
            'state': state,
            'posture': posture,
            'acceleration': acceleration_magnitude,
            'reason': suppression_reason
        })
    
    def _get_time_difference(self, current_time, previous_time):
        """
        Calculate time difference between two timestamps.
        
        Returns:
            float: Time difference in seconds
        """
        # Simple placeholder for time difference calculation
        # In real implementation, this would parse actual timestamps
        return 0.0
    
    def _handle_alert_state(self, current_time, user_response):
        """
        Handle active alert state with user interaction.
        """
        if not self.alert_active:
            # Start alert sequence
            self._start_alert_sequence(current_time)
            
            # Check for immediate user cancellation
            if user_response == "cancel":
                self._cancel_alert()
                return
            
            # Continue alert escalation
            self._escalate_alert(current_time)
        else:
            # Continue existing alert
            self.timer += 1
            
            # Check for user cancellation during alert
            if user_response == "cancel":
                self._cancel_alert()
                return
            
            # Continue escalation
            self._escalate_alert(current_time)
    
    def _escalate_alert(self, current_time):
        """
        Handle alert escalation with proper timing.
        """
        if self.timer >= self.cancellation_window and not self.alert_sent:
            # Escalate to external alerts after cancellation window
            self.alert_history.append({
                'time': current_time,
                'type': 'escalated',
                'state': self._get_current_state()
            })
            
            print(f"🚨 ALERT ESCALATED - External notifications sent")
            
            # Send external alerts (placeholder)
            self._send_external_alerts()
            self.alert_sent = True
    
    def _send_external_alerts(self):
        """
        Send external alerts to guardians and emergency services.
        """
        # Placeholder for external alert integration
        try:
            from alerts.guardian_alert import send_guardian_alert
            send_guardian_alert()
            print("📱 Guardian alert sent")
        except ImportError:
            print("⚠️ Guardian alert system not available")
        
        try:
            from alerts.gsm_alert import send_gsm_alert
            send_gsm_alert()
            print("📞 GSM alert sent")
        except ImportError:
            print("⚠️ GSM alert system not available")
    
    def _handle_pre_fall_warning(self, current_time, user_response):
        """
        Handle pre-fall warning with gentle alerts.
        """
        if not self.alert_active:
            # Start alert sequence
            self._start_alert_sequence(current_time)
            
            # Gentle warning for pre-fall state
            self.buzzer.pulse(1, 0.5)  # Short pulse
            print("⚠️  PRE-FALL WARNING DETECTED - User can cancel")
            
            # Check for user cancellation
            if user_response == "cancel":
                self._cancel_alert()
                return
            
            # Continue monitoring
            self.timer += 1
            if self.timer >= 5:  # Escalate to full alert
                self._escalate_to_full_alert(current_time)
        else:
            # Continue existing pre-fall warning
            self.timer += 1
            
            # Check for user cancellation
            if user_response == "cancel":
                self._cancel_alert()
                return
            
            # Escalate after threshold
            if self.timer >= 5:
                self._escalate_to_full_alert(current_time)
    
    def _handle_monitoring_state(self, current_time, user_response):
        """
        Handle monitoring state with periodic status updates.
        """
        if not self.alert_active:
            self._start_alert_sequence(current_time)
            
            # Periodic status updates without alarm
            if self.timer % 3 == 0:  # Every 3 seconds
                print(f"📊 Monitoring high-risk activity - Time: {self.timer}s")
            
            self.timer += 1
            
            # Check for user cancellation
            if user_response == "cancel":
                self._cancel_alert()
                return
            
            # Auto-escalation after threshold
            if self.timer >= self.escalation_threshold:
                self._escalate_to_full_alert(current_time)
    
    def _start_alert_sequence(self, current_time):
        """
        Start alert sequence and record alert history.
        """
        self.alert_active = True
        self.last_alert_time = current_time
        self.last_notification_time = current_time  # Track for rate limiting
        self.alert_history.append({
            'time': current_time,
            'type': 'started',
            'state': self._get_current_state()
        })
        
        print(f"🚨 ALERT ACTIVATED - Type: {self._get_current_state()}")
        print(f"⏰ Cancellation window: {self.cancellation_window}s")
        print("📱 Press 'cancel' to stop alert")
        
        # Start buzzer based on alert type
        if self._get_current_state() == "ALERT":
            self.buzzer.start()
        elif self._get_current_state() == "PRE_FALL_WARNING":
            self.buzzer.pulse(1, 0.5)  # Gentle warning
        elif self._get_current_state() in ["HIGH_RISK", "MONITORING"]:
            self.buzzer.pulse(2, 0.3)  # Slow pulse
    
    def _escalate_to_full_alert(self, current_time):
        """
        Escalate to full alert with stronger notifications.
        """
        self.alert_history.append({
            'time': current_time,
            'type': 'escalated',
            'state': self._get_current_state()
        })
        
        print(f"🚨 ALERT ESCALATED - Full alert activated")
        self.buzzer.start()  # Continuous alert
        
        # Reset monitoring timer
        self.timer = 0
    
    def _cancel_alert(self):
        """
        Handle user cancellation with graceful shutdown.
        """
        if self.alert_active:
            self.alert_history.append({
                'time': self._get_current_time(),
                'type': 'cancelled',
                'state': self._get_current_state()
            })
            
            print("✅ Alert cancelled by user")
            self._reset_alert_system()
    
    def _reset_alert_system(self):
        """
        Reset alert system to ready state.
        """
        self.alert_active = False
        self.timer = 0
        self.buzzer.stop()
        self.last_alert_time = None
        
        print("🔄 Alert system reset - Ready for next detection")
    
    def _get_current_state(self):
        """
        Get current system state for logging.
        """
        return self.current_state
    
    def get_alert_status(self):
        """
        Get comprehensive alert status for monitoring.
        
        Returns:
            dict: Current alert system status
        """
        return {
            'active': self.alert_active,
            'timer': self.timer,
            'cancellation_window': self.cancellation_window,
            'escalation_threshold': self.escalation_threshold,
            'last_alert_time': self.last_alert_time,
            'alert_count': len([a for a in self.alert_history if a['type'] in ['started', 'escalated']]),
            'alert_history': self.alert_history[-5:],  # Last 5 alerts
            'current_state': self._get_current_state()
        }
    
    def get_alert_history(self):
        """
        Get complete alert history for analysis.
        
        Returns:
            list: All alert events in chronological order
        """
        return self.alert_history
    
    def configure_comfort_constraints(self, 
                                  sleep_suppression=None, 
                                  sitting_transition_filter=None,
                                  rate_limit=None,
                                  min_alert_interval=None):
        """
        Configure comfort and dignity constraints.
        
        Args:
            sleep_suppression: Enable/disable sleep suppression
            sitting_transition_filter: Enable/disable sitting transition filter
            rate_limit: Enable/disable rate limiting
            min_alert_interval: Minimum seconds between alerts
        """
        if sleep_suppression is not None:
            self.sleep_suppression_enabled = sleep_suppression
            print(f"💤 Sleep suppression: {'ENABLED' if sleep_suppression else 'DISABLED'}")
        
        if sitting_transition_filter is not None:
            self.sitting_transition_filter_enabled = sitting_transition_filter
            print(f"🪑 Sitting transition filter: {'ENABLED' if sitting_transition_filter else 'DISABLED'}")
        
        if rate_limit is not None:
            self.rate_limit_enabled = rate_limit
            print(f"⏱️ Rate limiting: {'ENABLED' if rate_limit else 'DISABLED'}")
        
        if min_alert_interval is not None:
            self.min_alert_interval = min_alert_interval
            print(f"⏰ Minimum alert interval: {min_alert_interval}s")
    
    def get_comfort_status(self):
        """
        Get current comfort constraint status.
        
        Returns:
            dict: Current comfort constraint settings
        """
        return {
            'sleep_suppression_enabled': self.sleep_suppression_enabled,
            'sitting_transition_filter_enabled': self.sitting_transition_filter_enabled,
            'rate_limit_enabled': self.rate_limit_enabled,
            'min_alert_interval': self.min_alert_interval,
            'sleep_posture_threshold': self.sleep_posture_threshold,
            'impact_detection_threshold': self.impact_detection_threshold,
            'sitting_transition_window': self.sitting_transition_window
        }
    
    def get_suppression_stats(self):
        """
        Get statistics about suppressed alerts.
        
        Returns:
            dict: Suppression statistics
        """
        suppressed_alerts = [a for a in self.alert_history if a['type'] == 'suppressed']
        total_alerts = len(self.alert_history)
        
        if total_alerts == 0:
            return {
                'total_suppressed': 0,
                'suppression_rate': 0.0,
                'suppression_reasons': {}
            }
        
        suppression_reasons = {}
        for alert in suppressed_alerts:
            for reason in alert.get('reason', []):
                suppression_reasons[reason] = suppression_reasons.get(reason, 0) + 1
        
        return {
            'total_suppressed': len(suppressed_alerts),
            'suppression_rate': len(suppressed_alerts) / total_alerts,
            'suppression_reasons': suppression_reasons
        }
    
    def _get_current_time(self):
        """
        Get current time for logging.
        """
        # This would integrate with the main system clock
        # For now, return a placeholder
        return "2023-03-09 14:30:00"
