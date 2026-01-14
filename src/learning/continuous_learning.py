import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics

@dataclass
class FallEvent:
    """Represents a fall detection event."""
    timestamp: str
    event_type: str  # 'fall_detected', 'false_alarm', 'alert_cancelled'
    acceleration_magnitude: float
    posture: str
    instability_risk: float
    ml_confidence: float
    user_response: Optional[str]  # 'cancelled', 'confirmed', 'no_response'
    context: Dict[str, Any]

@dataclass
class DailyActivity:
    """Represents daily activity summary."""
    date: str
    total_steps: int
    active_hours: float
    inactive_hours: float
    posture_transitions: int
    average_instability_risk: float
    peak_acceleration: float
    fall_events: int
    false_alarms: int

@dataclass
class PatientProfile:
    """Represents patient profile with learned statistics."""
    patient_id: str
    created_date: str
    last_updated: str
    total_days_monitored: int
    fall_history: List[FallEvent]
    daily_activities: List[DailyActivity]
    personalized_thresholds: Dict[str, float]
    risk_factors: Dict[str, float]
    activity_patterns: Dict[str, Any]

class ContinuousLearningPipeline:
    """
    Backend-side continuous learning pipeline for fall detection.
    
    Features:
    - Store fall events, false alarms, and daily activity summaries
    - Update patient profile statistics over time
    - Generate personalized thresholds
    - No automatic model retraining
    """
    
    def __init__(self, patient_id: str):
        """
        Initialize the continuous learning pipeline.
        
        Args:
            patient_id: Unique patient identifier
        """
        self.patient_id = patient_id
        self.patient_profile = self._load_or_create_profile(patient_id)
        
        # Learning parameters
        self.learning_window_days = 30  # Days to consider for learning
        self.min_events_for_learning = 10  # Minimum events for threshold adaptation
        self.threshold_adaptation_rate = 0.1  # How quickly thresholds adapt
        
        # Event buffers for real-time processing
        self.event_buffer = deque(maxlen=100)  # Recent events for quick analysis
        self.daily_activity_buffer = {}  # Current day's activity tracking
        
        # Default thresholds (will be personalized over time)
        self.default_thresholds = {
            'fall_detection_threshold': 15.0,
            'instability_risk_threshold': 0.7,
            'inactivity_threshold': 30.0,
            'posture_transition_threshold': 5,
            'acceleration_variance_threshold': 2.0
        }
    
    def process_fall_event(self, event_data: Dict[str, Any]) -> str:
        """
        Process a fall detection event and update learning.
        
        Args:
            event_data: Dictionary containing event information
            
        Returns:
            str: Event ID for tracking
        """
        # Create fall event
        event_id = f"fall_{int(time.time())}"
        fall_event = FallEvent(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            event_type=event_data.get('event_type', 'fall_detected'),
            acceleration_magnitude=event_data.get('acceleration_magnitude', 0.0),
            posture=event_data.get('posture', 'unknown'),
            instability_risk=event_data.get('instability_risk', 0.0),
            ml_confidence=event_data.get('ml_confidence', 0.0),
            user_response=event_data.get('user_response'),
            context=event_data.get('context', {})
        )
        
        # Store event
        self._store_fall_event(fall_event)
        self.event_buffer.append(fall_event)
        
        # Update learning
        self._update_learning_from_event(fall_event)
        
        # Generate updated thresholds if enough data
        if self._should_update_thresholds():
            self._generate_personalized_thresholds()
        
        print(f"📊 Processed fall event: {event_id}")
        return event_id
    
    def process_false_alarm(self, alarm_data: Dict[str, Any]) -> str:
        """
        Process a false alarm event for learning.
        
        Args:
            alarm_data: Dictionary containing false alarm information
            
        Returns:
            str: Event ID for tracking
        """
        event_id = f"false_{int(time.time())}"
        false_event = FallEvent(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            event_type='false_alarm',
            acceleration_magnitude=alarm_data.get('acceleration_magnitude', 0.0),
            posture=alarm_data.get('posture', 'unknown'),
            instability_risk=alarm_data.get('instability_risk', 0.0),
            ml_confidence=alarm_data.get('ml_confidence', 0.0),
            user_response='cancelled',
            context=alarm_data.get('context', {})
        )
        
        # Store false alarm
        self._store_fall_event(false_event)
        self.event_buffer.append(false_event)
        
        # Update learning to reduce false positives
        self._update_learning_from_false_alarm(false_event)
        
        print(f"📊 Processed false alarm: {event_id}")
        return event_id
    
    def update_daily_activity(self, activity_data: Dict[str, Any]):
        """
        Update daily activity summary.
        
        Args:
            activity_data: Dictionary containing activity information
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Initialize today's activity if not exists
        if today not in self.daily_activity_buffer:
            self.daily_activity_buffer[today] = {
                'steps': 0,
                'active_time': 0.0,
                'inactive_time': 0.0,
                'posture_transitions': 0,
                'instability_samples': [],
                'acceleration_peaks': [],
                'fall_events': 0,
                'false_alarms': 0
            }
        
        # Update today's activity
        daily_activity = self.daily_activity_buffer[today]
        daily_activity['steps'] += activity_data.get('steps', 0)
        daily_activity['active_time'] += activity_data.get('active_time', 0.0)
        daily_activity['inactive_time'] += activity_data.get('inactive_time', 0.0)
        daily_activity['posture_transitions'] += activity_data.get('posture_transitions', 0)
        
        # Add instability samples
        if 'instability_risk' in activity_data:
            daily_activity['instability_samples'].append(activity_data['instability_risk'])
        
        # Add acceleration peaks
        if 'acceleration_magnitude' in activity_data:
            daily_activity['acceleration_peaks'].append(activity_data['acceleration_magnitude'])
        
        # Update event counts
        if activity_data.get('is_fall_event', False):
            daily_activity['fall_events'] += 1
        elif activity_data.get('is_false_alarm', False):
            daily_activity['false_alarms'] += 1
        
        print(f"📊 Updated daily activity for {today}")
    
    def finalize_daily_summary(self, date: Optional[str] = None):
        """
        Finalize daily activity summary and store it.
        
        Args:
            date: Date to finalize (default: today)
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if date not in self.daily_activity_buffer:
            print(f"⚠️ No activity data for {date}")
            return
        
        daily_data = self.daily_activity_buffer[date]
        
        # Calculate statistics
        avg_instability = 0.0
        if daily_data['instability_samples']:
            avg_instability = statistics.mean(daily_data['instability_samples'])
        
        peak_acceleration = 0.0
        if daily_data['acceleration_peaks']:
            peak_acceleration = max(daily_data['acceleration_peaks'])
        
        # Create daily activity summary
        daily_activity = DailyActivity(
            date=date,
            total_steps=daily_data['steps'],
            active_hours=daily_data['active_time'],
            inactive_hours=daily_data['inactive_time'],
            posture_transitions=daily_data['posture_transitions'],
            average_instability_risk=avg_instability,
            peak_acceleration=peak_acceleration,
            fall_events=daily_data['fall_events'],
            false_alarms=daily_data['false_alarms']
        )
        
        # Store daily activity
        self._store_daily_activity(daily_activity)
        
        # Remove from buffer
        del self.daily_activity_buffer[date]
        
        # Update learning from daily pattern
        self._update_learning_from_daily_activity(daily_activity)
        
        print(f"📊 Finalized daily summary for {date}")
    
    def get_patient_profile(self) -> PatientProfile:
        """
        Get current patient profile.
        
        Returns:
            PatientProfile: Current patient profile
        """
        return self.patient_profile
    
    def get_personalized_thresholds(self) -> Dict[str, float]:
        """
        Get current personalized thresholds.
        
        Returns:
            Dict: Personalized threshold values
        """
        if not self.patient_profile.personalized_thresholds:
            return self.default_thresholds.copy()
        
        return self.patient_profile.personalized_thresholds.copy()
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """
        Get learning pipeline statistics.
        
        Returns:
            Dict: Learning statistics and metrics
        """
        recent_events = list(self.event_buffer)[-50:]  # Last 50 events
        
        # Calculate event statistics
        total_events = len(self.patient_profile.fall_history)
        false_alarms = len([e for e in self.patient_profile.fall_history if e.event_type == 'false_alarm'])
        confirmed_falls = len([e for e in self.patient_profile.fall_history if e.event_type == 'fall_detected'])
        
        false_positive_rate = 0.0
        if total_events > 0:
            false_positive_rate = false_alarms / total_events
        
        # Calculate daily activity statistics
        recent_daily = self.patient_profile.daily_activities[-30:]  # Last 30 days
        avg_daily_instability = 0.0
        avg_daily_steps = 0.0
        
        if recent_daily:
            avg_daily_instability = statistics.mean([d.average_instability_risk for d in recent_daily])
            avg_daily_steps = statistics.mean([d.total_steps for d in recent_daily])
        
        return {
            'total_events_processed': total_events,
            'false_positive_rate': false_positive_rate,
            'confirmed_falls': confirmed_falls,
            'false_alarms': false_alarms,
            'days_monitored': self.patient_profile.total_days_monitored,
            'thresholds_adapted': len(self.patient_profile.personalized_thresholds) > 0,
            'avg_daily_instability': avg_daily_instability,
            'avg_daily_steps': avg_daily_steps,
            'learning_window_days': self.learning_window_days,
            'buffer_size': len(self.event_buffer)
        }
    
    def _load_or_create_profile(self, patient_id: str) -> PatientProfile:
        """Load existing profile or create new one."""
        # In real implementation, this would load from database
        # For now, create a new profile
        return PatientProfile(
            patient_id=patient_id,
            created_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_days_monitored=0,
            fall_history=[],
            daily_activities=[],
            personalized_thresholds={},
            risk_factors={},
            activity_patterns={}
        )
    
    def _store_fall_event(self, event: FallEvent):
        """Store fall event to profile."""
        self.patient_profile.fall_history.append(event)
        self.patient_profile.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Keep history manageable
        if len(self.patient_profile.fall_history) > 1000:
            self.patient_profile.fall_history = self.patient_profile.fall_history[-500:]
    
    def _store_daily_activity(self, activity: DailyActivity):
        """Store daily activity to profile."""
        self.patient_profile.daily_activities.append(activity)
        self.patient_profile.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Keep history manageable
        if len(self.patient_profile.daily_activities) > 365:
            self.patient_profile.daily_activities = self.patient_profile.daily_activities[-365:]
        
        # Update monitored days
        self.patient_profile.total_days_monitored = len(self.patient_profile.daily_activities)
    
    def _update_learning_from_event(self, event: FallEvent):
        """Update learning from a single event."""
        # Update risk factors
        if event.acceleration_magnitude > 0:
            current_avg = self.patient_profile.risk_factors.get('avg_acceleration', 0.0)
            count = self.patient_profile.risk_factors.get('acceleration_count', 0)
            new_avg = (current_avg * count + event.acceleration_magnitude) / (count + 1)
            self.patient_profile.risk_factors['avg_acceleration'] = new_avg
            self.patient_profile.risk_factors['acceleration_count'] = count + 1
        
        # Update instability patterns
        if event.instability_risk > 0:
            current_avg = self.patient_profile.risk_factors.get('avg_instability', 0.0)
            count = self.patient_profile.risk_factors.get('instability_count', 0)
            new_avg = (current_avg * count + event.instability_risk) / (count + 1)
            self.patient_profile.risk_factors['avg_instability'] = new_avg
            self.patient_profile.risk_factors['instability_count'] = count + 1
    
    def _update_learning_from_false_alarm(self, event: FallEvent):
        """Update learning to reduce false positives."""
        # Increase threshold that caused false alarm
        current_threshold = self.patient_profile.personalized_thresholds.get('fall_detection_threshold', 
                                                                       self.default_thresholds['fall_detection_threshold'])
        
        # Adapt threshold upward slightly
        new_threshold = current_threshold * (1 + self.threshold_adaptation_rate)
        self.patient_profile.personalized_thresholds['fall_detection_threshold'] = new_threshold
        
        print(f"📈 Adapted fall threshold: {current_threshold:.2f} -> {new_threshold:.2f}")
    
    def _update_learning_from_daily_activity(self, activity: DailyActivity):
        """Update learning from daily activity patterns."""
        # Update activity patterns
        patterns = self.patient_profile.activity_patterns
        
        # Average daily instability
        if 'avg_daily_instability' not in patterns:
            patterns['avg_daily_instability'] = []
        patterns['avg_daily_instability'].append(activity.average_instability_risk)
        
        # Average daily steps
        if 'avg_daily_steps' not in patterns:
            patterns['avg_daily_steps'] = []
        patterns['avg_daily_steps'].append(activity.total_steps)
        
        # Peak acceleration patterns
        if 'peak_acceleration_patterns' not in patterns:
            patterns['peak_acceleration_patterns'] = []
        patterns['peak_acceleration_patterns'].append(activity.peak_acceleration)
        
        # Keep patterns manageable
        for key in patterns:
            if len(patterns[key]) > 90:
                patterns[key] = patterns[key][-30:]
    
    def _should_update_thresholds(self) -> bool:
        """Determine if thresholds should be updated."""
        total_events = len(self.patient_profile.fall_history)
        
        # Need minimum events for learning
        if total_events < self.min_events_for_learning:
            return False
        
        # Check if we have enough recent data
        recent_events = [e for e in self.patient_profile.fall_history 
                       if self._is_recent_event(e.timestamp)]
        
        return len(recent_events) >= self.min_events_for_learning // 2
    
    def _generate_personalized_thresholds(self):
        """Generate personalized thresholds based on learned patterns."""
        if not self.patient_profile.fall_history:
            return
        
        # Analyze recent events
        recent_events = [e for e in self.patient_profile.fall_history 
                       if self._is_recent_event(e.timestamp)]
        
        if not recent_events:
            return
        
        # Calculate statistics
        accelerations = [e.acceleration_magnitude for e in recent_events if e.acceleration_magnitude > 0]
        instabilities = [e.instability_risk for e in recent_events if e.instability_risk > 0]
        
        # Generate personalized thresholds
        if accelerations:
            # Fall detection threshold (slightly above average)
            avg_acceleration = statistics.mean(accelerations)
            std_acceleration = statistics.stdev(accelerations) if len(accelerations) > 1 else 1.0
            personalized_fall_threshold = avg_acceleration + (0.5 * std_acceleration)
            self.patient_profile.personalized_thresholds['fall_detection_threshold'] = personalized_fall_threshold
        
        if instabilities:
            # Instability risk threshold
            avg_instability = statistics.mean(instabilities)
            std_instability = statistics.stdev(instabilities) if len(instabilities) > 1 else 0.1
            personalized_instability_threshold = avg_instability + (0.3 * std_instability)
            self.patient_profile.personalized_thresholds['instability_risk_threshold'] = min(personalized_instability_threshold, 0.9)
        
        # Update other thresholds based on activity patterns
        self._update_activity_based_thresholds()
        
        print(f"🎯 Generated personalized thresholds for patient {self.patient_id}")
    
    def _update_activity_based_thresholds(self):
        """Update thresholds based on activity patterns."""
        patterns = self.patient_profile.activity_patterns
        
        # Inactivity threshold based on average inactive time
        if 'avg_daily_instability' in patterns and patterns['avg_daily_instability']:
            avg_inactive = statistics.mean([d.inactive_hours for d in self.patient_profile.daily_activities[-7:]])
            if avg_inactive > 0:
                personalized_inactivity = avg_inactive * 1.2  # 20% above average
                self.patient_profile.personalized_thresholds['inactivity_threshold'] = personalized_inactivity
        
        # Posture transition threshold based on patterns
        if 'avg_daily_steps' in patterns and patterns['avg_daily_steps']:
            avg_transitions = statistics.mean([d.posture_transitions for d in self.patient_profile.daily_activities[-7:]])
            if avg_transitions > 0:
                personalized_transitions = avg_transitions * 1.5  # 50% above average
                self.patient_profile.personalized_thresholds['posture_transition_threshold'] = personalized_transitions
    
    def _is_recent_event(self, timestamp: str) -> bool:
        """Check if event is within learning window."""
        try:
            event_date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            cutoff_date = datetime.now() - timedelta(days=self.learning_window_days)
            return event_date > cutoff_date
        except:
            return False
    
    def export_profile_data(self) -> Dict[str, Any]:
        """
        Export patient profile data for analysis.
        
        Returns:
            Dict: Complete profile data
        """
        return {
            'patient_id': self.patient_profile.patient_id,
            'profile': asdict(self.patient_profile),
            'learning_stats': self.get_learning_statistics(),
            'current_thresholds': self.get_personalized_thresholds(),
            'export_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# Convenience functions for easy integration
def create_learning_pipeline(patient_id: str) -> ContinuousLearningPipeline:
    """
    Create a continuous learning pipeline instance.
    
    Args:
        patient_id: Unique patient identifier
        
    Returns:
        ContinuousLearningPipeline: Configured learning pipeline
    """
    return ContinuousLearningPipeline(patient_id)

def get_learning_summary(pipeline: ContinuousLearningPipeline) -> Dict[str, Any]:
    """
    Get learning pipeline summary.
    
    Args:
        pipeline: Learning pipeline instance
        
    Returns:
        Dict: Learning summary
    """
    return pipeline.get_learning_statistics()
