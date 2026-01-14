"""
Range and Vicinity Awareness System

Monitors patient location relative to safe zones and guardian proximity.
Implements geofencing, proximity detection, and location-based alerts.

Features:
- Geofenced safe zones
- Guardian proximity detection
- Location-based risk assessment
- Entry/exit zone monitoring
- Vicinity-based alert prioritization
"""

import asyncio
import time
import math
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from collections import deque
import json
import requests
from dataclasses import dataclass

class LocationType(Enum):
    """Types of location zones."""
    SAFE_ZONE = "safe_zone"
    DANGER_ZONE = "danger_zone"
    MEDICAL_ZONE = "medical_zone"
    RESTRICTED_ZONE = "restricted_zone"
    OUTSIDE = "outside"

class ProximityLevel(Enum):
    """Proximity levels to guardians."""
    VERY_CLOSE = "very_close"      # < 5 meters
    CLOSE = "close"               # 5-20 meters
    NEARBY = "nearby"             # 20-50 meters
    FAR = "far"                   # 50-100 meters
    VERY_FAR = "very_far"         # > 100 meters
    UNKNOWN = "unknown"           # Location unknown

@dataclass
class GeoZone:
    """Geofenced zone definition."""
    id: str
    name: str
    zone_type: LocationType
    center_lat: float
    center_lon: float
    radius_meters: float
    risk_level: float  # 0.0 (safe) to 1.0 (dangerous)
    allowed_hours: Optional[Tuple[int, int]] = None  # (start_hour, end_hour)
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Location:
    """Patient location information."""
    latitude: float
    longitude: float
    accuracy: float  # meters
    timestamp: float
    source: str  # "gps", "wifi", "bluetooth", "estimated"
    indoor: bool = False
    floor: Optional[int] = None

@dataclass
class GuardianLocation:
    """Guardian location information."""
    guardian_id: str
    latitude: float
    longitude: float
    accuracy: float
    timestamp: float
    proximity: ProximityLevel = ProximityLevel.UNKNOWN
    distance_meters: Optional[float] = None

class LocationTracker:
    """Tracks patient and guardian locations."""
    
    def __init__(self):
        self.patient_location: Optional[Location] = None
        self.guardian_locations: Dict[str, GuardianLocation] = {}
        self.location_history: deque = deque(maxlen=1000)
        
        # Location update thresholds
        self.min_movement_threshold = 5.0  # meters
        self.location_timeout = 300  # 5 minutes
        
    def update_patient_location(self, location: Location) -> bool:
        """
        Update patient location.
        
        Returns:
            True if location was significantly updated
        """
        # Check if this is a significant movement
        if self.patient_location:
            distance = self._calculate_distance(
                self.patient_location.latitude, self.patient_location.longitude,
                location.latitude, location.longitude
            )
            
            if distance < self.min_movement_threshold:
                return False  # Not significant movement
        
        self.patient_location = location
        self.location_history.append(location)
        
        print(f"📍 Patient location updated: {location.latitude:.6f}, {location.longitude:.6f}")
        return True
    
    def update_guardian_location(self, guardian_id: str, location: GuardianLocation) -> bool:
        """Update guardian location."""
        # Calculate proximity to patient
        if self.patient_location:
            distance = self._calculate_distance(
                self.patient_location.latitude, self.patient_location.longitude,
                location.latitude, location.longitude
            )
            location.distance_meters = distance
            location.proximity = self._determine_proximity_level(distance)
        
        self.guardian_locations[guardian_id] = location
        
        print(f"👥 Guardian {guardian_id} location updated: {location.proximity.value}")
        return True
    
    def get_current_zone(self, zones: List[GeoZone]) -> Tuple[Optional[GeoZone], float]:
        """
        Get current zone and distance to zone center.
        
        Returns:
            Tuple of (zone, distance_to_center)
        """
        if not self.patient_location:
            return None, float('inf')
        
        closest_zone = None
        min_distance = float('inf')
        
        for zone in zones:
            distance = self._calculate_distance(
                zone.center_lat, zone.center_lon,
                self.patient_location.latitude, self.patient_location.longitude
            )
            
            if distance <= zone.radius_meters:
                if distance < min_distance:
                    min_distance = distance
                    closest_zone = zone
        
        return closest_zone, min_distance
    
    def get_nearest_guardian(self) -> Tuple[Optional[str], Optional[GuardianLocation]]:
        """Get nearest guardian to patient."""
        if not self.patient_location or not self.guardian_locations:
            return None, None
        
        nearest_guardian_id = None
        nearest_guardian = None
        min_distance = float('inf')
        
        for guardian_id, guardian_loc in self.guardian_locations.items():
            if guardian_loc.distance_meters and guardian_loc.distance_meters < min_distance:
                min_distance = guardian_loc.distance_meters
                nearest_guardian_id = guardian_id
                nearest_guardian = guardian_loc
        
        return nearest_guardian_id, nearest_guardian
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS coordinates using Haversine formula."""
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in meters
        r = 6371000
        
        return c * r
    
    def _determine_proximity_level(self, distance: float) -> ProximityLevel:
        """Determine proximity level based on distance."""
        if distance < 5:
            return ProximityLevel.VERY_CLOSE
        elif distance < 20:
            return ProximityLevel.CLOSE
        elif distance < 50:
            return ProximityLevel.NEARBY
        elif distance < 100:
            return ProximityLevel.FAR
        elif distance < 1000:
            return ProximityLevel.VERY_FAR
        else:
            return ProximityLevel.UNKNOWN
    
    def is_location_fresh(self, location_type: str = "patient") -> bool:
        """Check if location data is fresh."""
        current_time = time.time()
        
        if location_type == "patient" and self.patient_location:
            return (current_time - self.patient_location.timestamp) < self.location_timeout
        
        elif location_type == "guardian":
            for guardian_loc in self.guardian_locations.values():
                if (current_time - guardian_loc.timestamp) < self.location_timeout:
                    return True
        
        return False
    
    def get_location_quality(self) -> Dict[str, Any]:
        """Get location data quality metrics."""
        quality = {
            "patient_location_available": self.patient_location is not None,
            "patient_location_fresh": self.is_location_fresh("patient"),
            "guardian_locations_count": len(self.guardian_locations),
            "fresh_guardian_locations": sum(1 for loc in self.guardian_locations.values() 
                                           if self.is_location_fresh_guardian(loc)),
            "location_history_size": len(self.location_history)
        }
        
        if self.patient_location:
            quality["patient_accuracy"] = self.patient_location.accuracy
            quality["patient_source"] = self.patient_location.source
        
        return quality
    
    def is_location_fresh_guardian(self, guardian_loc: GuardianLocation) -> bool:
        """Check if guardian location is fresh."""
        return (time.time() - guardian_loc.timestamp) < self.location_timeout

class ZoneManager:
    """Manages geofenced zones and zone-based rules."""
    
    def __init__(self):
        self.zones: Dict[str, GeoZone] = {}
        self.zone_history: deque = deque(maxlen=500)
        self.current_zone: Optional[GeoZone] = None
        self.zone_entry_time: Optional[float] = None
        
        # Initialize default zones
        self._initialize_default_zones()
    
    def _initialize_default_zones(self):
        """Initialize default safe zones."""
        # Home zone (example coordinates - should be configured per patient)
        home_zone = GeoZone(
            id="home",
            name="Home",
            zone_type=LocationType.SAFE_ZONE,
            center_lat=40.7128,  # NYC coordinates as example
            center_lon=-74.0060,
            radius_meters=50,
            risk_level=0.0
        )
        
        # Medical facility zone
        medical_zone = GeoZone(
            id="hospital",
            name="Hospital",
            zone_type=LocationType.MEDICAL_ZONE,
            center_lat=40.7138,
            center_lon=-74.0050,
            radius_meters=100,
            risk_level=0.1
        )
        
        self.add_zone(home_zone)
        self.add_zone(medical_zone)
    
    def add_zone(self, zone: GeoZone):
        """Add a new zone."""
        self.zones[zone.id] = zone
        print(f"📍 Zone added: {zone.name} ({zone.zone_type.value})")
    
    def remove_zone(self, zone_id: str):
        """Remove a zone."""
        if zone_id in self.zones:
            del self.zones[zone_id]
            print(f"📍 Zone removed: {zone_id}")
    
    def update_current_zone(self, zone: Optional[GeoZone]):
        """Update current zone and track transitions."""
        if zone != self.current_zone:
            # Zone transition detected
            old_zone = self.current_zone
            self.current_zone = zone
            self.zone_entry_time = time.time()
            
            # Log transition
            transition = {
                "timestamp": time.time(),
                "from_zone": old_zone.name if old_zone else "outside",
                "to_zone": zone.name if zone else "outside",
                "zone_type": zone.zone_type.value if zone else "outside"
            }
            
            self.zone_history.append(transition)
            
            print(f"🔄 Zone transition: {transition['from_zone']} → {transition['to_zone']}")
            
            return transition
        
        return None
    
    def get_zone_risk_assessment(self, zone: Optional[GeoZone]) -> Dict[str, Any]:
        """Get risk assessment for current zone."""
        if not zone:
            return {
                "risk_level": 0.5,  # Medium risk for unknown location
                "risk_factors": ["unknown_location"],
                "recommendations": ["locate_patient"]
            }
        
        risk_factors = []
        recommendations = []
        
        # Base risk from zone
        risk_level = zone.risk_level
        
        # Time-based risk
        if zone.allowed_hours:
            current_hour = datetime.now().hour
            start_hour, end_hour = zone.allowed_hours
            
            if not (start_hour <= current_hour <= end_hour):
                risk_level += 0.3
                risk_factors.append("outside_allowed_hours")
                recommendations.append("check_zone_access_time")
        
        # Zone type specific risks
        if zone.zone_type == LocationType.DANGER_ZONE:
            risk_factors.append("danger_zone")
            recommendations.append("immediate_assistance")
        elif zone.zone_type == LocationType.RESTRICTED_ZONE:
            risk_factors.append("restricted_zone")
            recommendations.append("verify_authorization")
        
        return {
            "risk_level": min(1.0, risk_level),
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "zone_name": zone.name,
            "zone_type": zone.zone_type.value
        }
    
    def is_zone_time_restricted(self, zone: GeoZone) -> bool:
        """Check if zone has time restrictions."""
        return zone.allowed_hours is not None
    
    def is_within_allowed_hours(self, zone: GeoZone) -> bool:
        """Check if current time is within zone's allowed hours."""
        if not zone.allowed_hours:
            return True
        
        current_hour = datetime.now().hour
        start_hour, end_hour = zone.allowed_hours
        
        return start_hour <= current_hour <= end_hour

class VicinityAwarenessSystem:
    """Main system for range and vicinity awareness."""
    
    def __init__(self, backend_url: str = "http://localhost:5000/api", 
                 patient_id: str = "demo_patient"):
        self.backend_url = backend_url
        self.patient_id = patient_id
        
        # Components
        self.location_tracker = LocationTracker()
        self.zone_manager = ZoneManager()
        
        # State
        self.current_risk_level = 0.0
        self.last_assessment_time = 0
        self.assessment_interval = 30  # seconds
        
        # Alerts
        self.zone_alerts = deque(maxlen=100)
        self.proximity_alerts = deque(maxlen=100)
        
    def update_patient_location(self, latitude: float, longitude: float, 
                               accuracy: float = 10.0, source: str = "gps") -> Dict[str, Any]:
        """
        Update patient location and assess risk.
        
        Returns:
            Location assessment results
        """
        location = Location(
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            timestamp=time.time(),
            source=source
        )
        
        # Update location
        updated = self.location_tracker.update_patient_location(location)
        
        if updated:
            # Assess location
            assessment = self._assess_location_risk()
            
            # Check zone transitions
            current_zone, distance = self.location_tracker.get_current_zone(
                list(self.zone_manager.zones.values())
            )
            
            transition = self.zone_manager.update_current_zone(current_zone)
            
            if transition:
                self._handle_zone_transition(transition)
            
            return {
                "location_updated": True,
                "assessment": assessment,
                "current_zone": current_zone.name if current_zone else "outside",
                "zone_transition": transition
            }
        
        return {"location_updated": False}
    
    def update_guardian_location(self, guardian_id: str, latitude: float, 
                                longitude: float, accuracy: float = 10.0) -> Dict[str, Any]:
        """Update guardian location."""
        guardian_loc = GuardianLocation(
            guardian_id=guardian_id,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            timestamp=time.time()
        )
        
        updated = self.location_tracker.update_guardian_location(guardian_id, guardian_loc)
        
        if updated:
            # Check proximity alerts
            self._check_proximity_alerts(guardian_loc)
            
            return {
                "guardian_location_updated": True,
                "proximity": guardian_loc.proximity.value,
                "distance": guardian_loc.distance_meters
            }
        
        return {"guardian_location_updated": False}
    
    def _assess_location_risk(self) -> Dict[str, Any]:
        """Assess current location risk."""
        current_zone, distance = self.location_tracker.get_current_zone(
            list(self.zone_manager.zones.values())
        )
        
        # Get zone risk assessment
        zone_assessment = self.zone_manager.get_zone_risk_assessment(current_zone)
        
        # Get nearest guardian
        nearest_guardian_id, nearest_guardian = self.location_tracker.get_nearest_guardian()
        
        # Adjust risk based on guardian proximity
        proximity_adjustment = 0.0
        
        if nearest_guardian:
            if nearest_guardian.proximity == ProximityLevel.VERY_CLOSE:
                proximity_adjustment = -0.3  # Reduce risk significantly
            elif nearest_guardian.proximity == ProximityLevel.CLOSE:
                proximity_adjustment = -0.2
            elif nearest_guardian.proximity == ProximityLevel.NEARBY:
                proximity_adjustment = -0.1
        
        # Calculate final risk
        base_risk = zone_assessment["risk_level"]
        adjusted_risk = max(0.0, min(1.0, base_risk + proximity_adjustment))
        
        self.current_risk_level = adjusted_risk
        self.last_assessment_time = time.time()
        
        return {
            "risk_level": adjusted_risk,
            "base_risk": base_risk,
            "proximity_adjustment": proximity_adjustment,
            "zone_assessment": zone_assessment,
            "nearest_guardian": {
                "id": nearest_guardian_id,
                "proximity": nearest_guardian.proximity.value if nearest_guardian else "unknown",
                "distance": nearest_guardian.distance_meters if nearest_guardian else None
            },
            "location_quality": self.location_tracker.get_location_quality()
        }
    
    def _handle_zone_transition(self, transition: Dict[str, Any]):
        """Handle zone transition events."""
        from_zone = transition["from_zone"]
        to_zone = transition["to_zone"]
        zone_type = transition["zone_type"]
        
        # Create alert for concerning transitions
        if zone_type in ["danger_zone", "restricted_zone"]:
            alert_data = {
                "type": "zone_breach",
                "from_zone": from_zone,
                "to_zone": to_zone,
                "timestamp": transition["timestamp"],
                "urgency": "high" if zone_type == "danger_zone" else "medium"
            }
            
            self.zone_alerts.append(alert_data)
            print(f"🚨 Zone alert: Entered {zone_type}")
        
        elif from_zone == "outside" and zone_type == "safe_zone":
            # Patient returned to safe zone
            alert_data = {
                "type": "zone_return",
                "zone": to_zone,
                "timestamp": transition["timestamp"],
                "urgency": "info"
            }
            
            self.zone_alerts.append(alert_data)
            print(f"✅ Patient returned to safe zone: {to_zone}")
    
    def _check_proximity_alerts(self, guardian_loc: GuardianLocation):
        """Check for proximity-based alerts."""
        # Alert if guardian moves far away from patient in high-risk zone
        current_zone, _ = self.location_tracker.get_current_zone(
            list(self.zone_manager.zones.values())
        )
        
        if current_zone and current_zone.risk_level > 0.5:
            if guardian_loc.proximity in [ProximityLevel.FAR, ProximityLevel.VERY_FAR]:
                alert_data = {
                    "type": "guardian_distant",
                    "guardian_id": guardian_loc.guardian_id,
                    "proximity": guardian_loc.proximity.value,
                    "distance": guardian_loc.distance_meters,
                    "zone": current_zone.name,
                    "timestamp": time.time(),
                    "urgency": "medium"
                }
                
                self.proximity_alerts.append(alert_data)
                print(f"⚠️ Guardian {guardian_loc.guardian_id} is far from patient in {current_zone.name}")
    
    def get_vicinity_status(self) -> Dict[str, Any]:
        """Get comprehensive vicinity status."""
        current_zone, _ = self.location_tracker.get_current_zone(
            list(self.zone_manager.zones.values())
        )
        
        nearest_guardian_id, nearest_guardian = self.location_tracker.get_nearest_guardian()
        
        return {
            "patient_location": {
                "available": self.location_tracker.patient_location is not None,
                "fresh": self.location_tracker.is_location_fresh("patient"),
                "latitude": self.location_tracker.patient_location.latitude if self.location_tracker.patient_location else None,
                "longitude": self.location_tracker.patient_location.longitude if self.location_tracker.patient_location else None,
                "accuracy": self.location_tracker.patient_location.accuracy if self.location_tracker.patient_location else None,
                "source": self.location_tracker.patient_location.source if self.location_tracker.patient_location else None
            },
            "current_zone": {
                "name": current_zone.name if current_zone else "outside",
                "type": current_zone.zone_type.value if current_zone else "outside",
                "risk_level": current_zone.risk_level if current_zone else 0.5
            },
            "guardians": {
                "total": len(self.location_tracker.guardian_locations),
                "nearest": {
                    "id": nearest_guardian_id,
                    "proximity": nearest_guardian.proximity.value if nearest_guardian else "unknown",
                    "distance": nearest_guardian.distance_meters if nearest_guardian else None
                }
            },
            "risk_assessment": {
                "current_risk_level": self.current_risk_level,
                "last_assessment": self.last_assessment_time
            },
            "alerts": {
                "zone_alerts": len(self.zone_alerts),
                "proximity_alerts": len(self.proximity_alerts)
            }
        }
    
    def add_custom_zone(self, zone_id: str, name: str, zone_type: str,
                        latitude: float, longitude: float, radius: float,
                        risk_level: float = 0.0):
        """Add a custom zone."""
        zone = GeoZone(
            id=zone_id,
            name=name,
            zone_type=LocationType(zone_type),
            center_lat=latitude,
            center_lon=longitude,
            radius_meters=radius,
            risk_level=risk_level
        )
        
        self.zone_manager.add_zone(zone)
    
    def simulate_location_update(self, zone_name: str = "home") -> Dict[str, Any]:
        """Simulate location update for testing."""
        if zone_name in self.zone_manager.zones:
            zone = self.zone_manager.zones[zone_name]
            return self.update_patient_location(
                zone.center_lat, zone.center_lon, 5.0, "simulated"
            )
        else:
            # Simulate random location outside zones
            import random
            lat = 40.7128 + random.uniform(-0.01, 0.01)
            lon = -74.0060 + random.uniform(-0.01, 0.01)
            return self.update_patient_location(lat, lon, 10.0, "simulated")

# Global vicinity awareness system instance
_vicinity_system = None

def initialize_vicinity_system(backend_url: str = "http://localhost:5000/api",
                              patient_id: str = "demo_patient") -> VicinityAwarenessSystem:
    """Initialize the global vicinity awareness system."""
    global _vicinity_system
    _vicinity_system = VicinityAwarenessSystem(backend_url, patient_id)
    return _vicinity_system

def get_vicinity_system() -> VicinityAwarenessSystem:
    """Get the global vicinity awareness system instance."""
    return _vicinity_system

def update_patient_location(latitude: float, longitude: float, 
                           accuracy: float = 10.0, source: str = "gps") -> Dict[str, Any]:
    """Update patient location using global system."""
    if _vicinity_system:
        return _vicinity_system.update_patient_location(latitude, longitude, accuracy, source)
    return {"error": "system_not_initialized"}

def update_guardian_location(guardian_id: str, latitude: float, longitude: float,
                           accuracy: float = 10.0) -> Dict[str, Any]:
    """Update guardian location using global system."""
    if _vicinity_system:
        return _vicinity_system.update_guardian_location(guardian_id, latitude, longitude, accuracy)
    return {"error": "system_not_initialized"}

def get_vicinity_status() -> Dict[str, Any]:
    """Get vicinity status using global system."""
    if _vicinity_system:
        return _vicinity_system.get_vicinity_status()
    return {"error": "system_not_initialized"}
