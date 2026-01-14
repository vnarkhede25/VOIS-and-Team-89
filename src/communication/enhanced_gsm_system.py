"""
Enhanced GSM Communication System

Provides two-way GSM communication between guardians and senior citizens.
Enables guardians to contact seniors even from long distances via SMS and voice calls.

Features:
- Two-way SMS communication
- Voice call capabilities
- Emergency SMS gateway
- Location sharing via SMS
- Health status updates via SMS
- Remote device control via SMS
- SMS command processing
"""

import asyncio
import time
import logging
import re
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass
import requests

class MessageType(Enum):
    """Types of GSM messages."""
    EMERGENCY_ALERT = "emergency_alert"
    GUARDIAN_SMS = "guardian_sms"
    SENIOR_SMS = "senior_sms"
    VOICE_CALL = "voice_call"
    LOCATION_SHARE = "location_share"
    HEALTH_UPDATE = "health_update"
    DEVICE_CONTROL = "device_control"
    STATUS_REQUEST = "status_request"

class CallPriority(Enum):
    """Voice call priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EMERGENCY = "emergency"

@dataclass
class GSMMessage:
    """GSM message structure."""
    message_id: str
    message_type: MessageType
    sender: str
    recipient: str
    content: str
    timestamp: float
    priority: CallPriority = CallPriority.NORMAL
    delivered: bool = False
    read: bool = False

@dataclass
class VoiceCall:
    """Voice call structure."""
    call_id: str
    caller: str
    recipient: str
    timestamp: float
    duration: float
    priority: CallPriority
    answered: bool = False
    connected: bool = False

class EnhancedGSMSystem:
    """Enhanced GSM system for two-way communication."""
    
    def __init__(self, backend_url: str = "http://localhost:5000/api", 
                 patient_id: str = "demo_patient"):
        self.backend_url = backend_url
        self.patient_id = patient_id
        self.logger = logging.getLogger(__name__)
        
        # GSM configuration
        self.sim_card_number = "+1234567890"  # SIM card number
        self.gsm_modem_port = "/dev/ttyUSB3"  # GSM modem port
        self.gsm_baudrate = 115200
        self.sms_gateway_api = "https://api.sms-gateway.com/send"
        
        # Contact management
        self.guardian_contacts = []
        self.emergency_contacts = []
        self.senior_phone_number = None
        
        # Message queues
        self.outgoing_messages = []
        self.incoming_messages = []
        self.missed_calls = []
        
        # Call management
        self.active_calls = {}
        self.call_history = []
        self.auto_answer_enabled = True
        
        # Command processing
        self.sms_commands = {
            'STATUS': self._handle_status_command,
            'LOCATION': self._handle_location_command,
            'HEALTH': self._handle_health_command,
            'CALL': self._handle_call_command,
            'ALERT': self._handle_alert_command,
            'HELP': self._handle_help_command,
            'BATTERY': self._handle_battery_command,
            'SILENCE': self._handle_silence_command,
            'TEST': self._handle_test_command
        }
        
        # Rate limiting
        self.last_sms_time = {}
        self.sms_rate_limit = 30  # seconds between SMS to same recipient
        self.call_rate_limit = 60  # seconds between calls
        
        # Emergency features
        self.emergency_mode = False
        self.emergency_keywords = [
            "emergency", "help", "fall", "urgent", "critical",
            "911", "ambulance", "hospital", "can't breathe"
        ]
        
    async def start_monitoring(self):
        """Start GSM system monitoring."""
        self.logger.info("📱 Starting enhanced GSM communication system...")
        
        # Start background tasks
        await asyncio.gather([
            self._monitor_incoming_messages(),
            self._monitor_incoming_calls(),
            self._process_outgoing_messages(),
            self._check_emergency_conditions()
        ])
    
    async def _monitor_incoming_messages(self):
        """Monitor incoming SMS messages."""
        while True:
            try:
                # Check for new messages from backend
                messages = await self._fetch_incoming_messages()
                
                for message in messages:
                    await self._process_incoming_message(message)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"❌ Error monitoring incoming messages: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_incoming_calls(self):
        """Monitor incoming voice calls."""
        while True:
            try:
                # Check for incoming calls from backend
                calls = await self._fetch_incoming_calls()
                
                for call in calls:
                    await self._process_incoming_call(call)
                
                await asyncio.sleep(3)  # Check every 3 seconds
                
            except Exception as e:
                self.logger.error(f"❌ Error monitoring incoming calls: {e}")
                await asyncio.sleep(3)
    
    async def _process_outgoing_messages(self):
        """Process outgoing message queue."""
        while True:
            try:
                if self.outgoing_messages:
                    message = self.outgoing_messages.pop(0)
                    await self._send_sms_message(message)
                
                await asyncio.sleep(2)  # Process every 2 seconds
                
            except Exception as e:
                self.logger.error(f"❌ Error processing outgoing messages: {e}")
                await asyncio.sleep(2)
    
    async def send_guardian_sms(self, guardian_id: str, message: str, 
                              priority: CallPriority = CallPriority.NORMAL) -> bool:
        """Send SMS from guardian to senior citizen."""
        try:
            # Get guardian contact info
            guardian = await self._get_guardian_contact(guardian_id)
            if not guardian:
                self.logger.error(f"❌ Guardian {guardian_id} not found")
                return False
            
            # Check rate limiting
            if not self._check_rate_limit(guardian['phone'], 'sms'):
                self.logger.warning(f"⚠️ SMS rate limit exceeded for {guardian['phone']}")
                return False
            
            # Create message
            sms_message = GSMMessage(
                message_id=f"guardian_sms_{int(time.time())}",
                message_type=MessageType.GUARDIAN_SMS,
                sender=guardian['phone'],
                recipient=self.senior_phone_number,
                content=message,
                timestamp=time.time(),
                priority=priority
            )
            
            # Add to queue
            self.outgoing_messages.append(sms_message)
            
            self.logger.info(f"📱 Guardian SMS queued: {guardian['name']} → Senior: {message[:50]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send guardian SMS: {e}")
            return False
    
    async def initiate_voice_call(self, guardian_id: str, 
                              priority: CallPriority = CallPriority.NORMAL) -> bool:
        """Initiate voice call from guardian to senior citizen."""
        try:
            # Get guardian contact info
            guardian = await self._get_guardian_contact(guardian_id)
            if not guardian:
                self.logger.error(f"❌ Guardian {guardian_id} not found")
                return False
            
            # Check rate limiting
            if not self._check_rate_limit(guardian['phone'], 'call'):
                self.logger.warning(f"⚠️ Call rate limit exceeded for {guardian['phone']}")
                return False
            
            # Create call record
            voice_call = VoiceCall(
                call_id=f"guardian_call_{int(time.time())}",
                caller=guardian['phone'],
                recipient=self.senior_phone_number,
                timestamp=time.time(),
                duration=0,
                priority=priority
            )
            
            # Initiate call via GSM modem
            success = await self._initiate_gsm_call(voice_call)
            
            if success:
                self.call_history.append(voice_call)
                self.logger.info(f"📞 Guardian call initiated: {guardian['name']} → Senior")
                return True
            else:
                self.logger.error(f"❌ Failed to initiate guardian call")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to initiate voice call: {e}")
            return False
    
    async def send_emergency_alert(self, alert_type: str, location: Dict = None, 
                               medical_info: Dict = None) -> bool:
        """Send emergency alert to all contacts."""
        try:
            emergency_message = f"🚨 EMERGENCY: {alert_type}"
            if location:
                emergency_message += f" | Location: {location.get('address', 'Unknown')}"
            if medical_info:
                emergency_message += f" | Medical: {medical_info.get('conditions', 'None')}"
            
            # Send to all guardians
            for guardian in self.guardian_contacts:
                await self.send_guardian_sms(
                    guardian['id'], 
                    emergency_message,
                    CallPriority.EMERGENCY
                )
            
            # Send to emergency services
            await self._send_emergency_services_alert(alert_type, location, medical_info)
            
            # Set emergency mode
            self.emergency_mode = True
            
            self.logger.info(f"🚨 Emergency alert sent: {alert_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send emergency alert: {e}")
            return False
    
    async def _process_incoming_message(self, message: Dict[str, Any]):
        """Process incoming SMS message."""
        try:
            content = message.get('content', '').strip().upper()
            sender = message.get('sender', '')
            
            # Check for emergency keywords
            if any(keyword in content for keyword in self.emergency_keywords):
                await self._handle_emergency_sms(content, sender)
                return
            
            # Check for commands
            command_found = False
            for command, handler in self.sms_commands.items():
                if content.startswith(command):
                    await handler(content, sender)
                    command_found = True
                    break
            
            # If no command, treat as regular message
            if not command_found:
                await self._handle_regular_message(content, sender)
                
        except Exception as e:
            self.logger.error(f"❌ Error processing incoming message: {e}")
    
    async def _process_incoming_call(self, call: Dict[str, Any]):
        """Process incoming voice call."""
        try:
            caller = call.get('caller', '')
            priority = self._determine_call_priority(caller)
            
            # Auto-answer for guardians in emergency mode
            if self.emergency_mode and self._is_guardian_number(caller):
                await self._auto_answer_call(call, priority)
            else:
                # Log missed call
                missed_call = VoiceCall(
                    call_id=f"missed_{int(time.time())}",
                    caller=caller,
                    recipient=self.senior_phone_number,
                    timestamp=time.time(),
                    duration=0,
                    priority=priority,
                    answered=False
                )
                self.missed_calls.append(missed_call)
                
                # Notify guardians of missed call
                await self._notify_missed_call(missed_call)
                
        except Exception as e:
            self.logger.error(f"❌ Error processing incoming call: {e}")
    
    async def _handle_status_command(self, content: str, sender: str):
        """Handle STATUS command via SMS."""
        try:
            # Get current system status
            from src.main_enhanced import get_system_status
            status = get_system_status()
            
            status_message = (
                f"📊 STATUS:\n"
                f"Device: {status.get('device_status', 'Unknown')}\n"
                f"Battery: {status.get('battery_level', 0)}%\n"
                f"Wear: {status.get('wear_status', 'Unknown')}\n"
                f"Location: {status.get('location', 'Unknown')}\n"
                f"Last Update: {datetime.now().strftime('%H:%M')}"
            )
            
            await self._send_reply_sms(sender, status_message)
            
        except Exception as e:
            self.logger.error(f"❌ Error handling STATUS command: {e}")
    
    async def _handle_location_command(self, content: str, sender: str):
        """Handle LOCATION command via SMS."""
        try:
            # Get current location
            location = await self._get_current_location()
            
            if location:
                location_message = (
                    f"📍 LOCATION:\n"
                    f"Address: {location.get('address', 'Unknown')}\n"
                    f"Coordinates: {location.get('lat', 0)}, {location.get('lon', 0)}\n"
                    f"Accuracy: {location.get('accuracy', 0)}m\n"
                    f"Time: {datetime.now().strftime('%H:%M')}"
                )
            else:
                location_message = "📍 Location currently unavailable"
            
            await self._send_reply_sms(sender, location_message)
            
        except Exception as e:
            self.logger.error(f"❌ Error handling LOCATION command: {e}")
    
    async def _handle_health_command(self, content: str, sender: str):
        """Handle HEALTH command via SMS."""
        try:
            # Get current health status
            health_data = await self._get_health_status()
            
            health_message = (
                f"❤️ HEALTH:\n"
                f"Heart Rate: {health_data.get('heart_rate', 'Unknown')} bpm\n"
                f"Temperature: {health_data.get('temperature', 'Unknown')}°C\n"
                f"Activity: {health_data.get('activity_level', 'Unknown')}\n"
                f"Last Fall: {health_data.get('last_fall', 'None')}\n"
                f"Time: {datetime.now().strftime('%H:%M')}"
            )
            
            await self._send_reply_sms(sender, health_message)
            
        except Exception as e:
            self.logger.error(f"❌ Error handling HEALTH command: {e}")
    
    async def _handle_call_command(self, content: str, sender: str):
        """Handle CALL command via SMS."""
        try:
            # Extract phone number from command
            match = re.search(r'CALL\s+(\+?\d+)', content)
            if match:
                phone_number = match.group(1)
                
                # Initiate call
                call = VoiceCall(
                    call_id=f"command_call_{int(time.time())}",
                    caller=self.senior_phone_number,
                    recipient=phone_number,
                    timestamp=time.time(),
                    duration=0,
                    priority=CallPriority.NORMAL
                )
                
                success = await self._initiate_gsm_call(call)
                
                if success:
                    await self._send_reply_sms(sender, f"📞 Calling {phone_number}...")
                else:
                    await self._send_reply_sms(sender, "❌ Failed to initiate call")
            else:
                await self._send_reply_sms(sender, "📞 Usage: CALL <phone_number>")
                
        except Exception as e:
            self.logger.error(f"❌ Error handling CALL command: {e}")
    
    async def _handle_alert_command(self, content: str, sender: str):
        """Handle ALERT command via SMS."""
        try:
            # Extract alert message
            alert_message = content.replace('ALERT', '').strip()
            
            if alert_message:
                # Send alert to all guardians
                for guardian in self.guardian_contacts:
                    await self.send_guardian_sms(
                        guardian['id'],
                        f"⚠️ ALERT from Senior: {alert_message}",
                        CallPriority.HIGH
                    )
                
                await self._send_reply_sms(sender, "✅ Alert sent to guardians")
            else:
                await self._send_reply_sms(sender, "⚠️ Usage: ALERT <message>")
                
        except Exception as e:
            self.logger.error(f"❌ Error handling ALERT command: {e}")
    
    async def _handle_help_command(self, content: str, sender: str):
        """Handle HELP command via SMS."""
        try:
            help_message = (
                "📱 AVAILABLE COMMANDS:\n"
                "STATUS - Get device status\n"
                "LOCATION - Get current location\n"
                "HEALTH - Get health status\n"
                "CALL <number> - Make call\n"
                "ALERT <message> - Send alert\n"
                "BATTERY - Get battery level\n"
                "SILENCE - Silence alerts\n"
                "TEST - Test system"
            )
            
            await self._send_reply_sms(sender, help_message)
            
        except Exception as e:
            self.logger.error(f"❌ Error handling HELP command: {e}")
    
    async def _handle_emergency_sms(self, content: str, sender: str):
        """Handle emergency SMS."""
        try:
            # Send emergency alert
            await self.send_emergency_alert(
                alert_type="Emergency SMS",
                location={"source": "SMS", "sender": sender},
                medical_info={"message": content}
            )
            
            # Acknowledge receipt
            await self._send_reply_sms(sender, "🚨 Emergency received! Help is on the way.")
            
        except Exception as e:
            self.logger.error(f"❌ Error handling emergency SMS: {e}")
    
    async def _send_reply_sms(self, recipient: str, message: str):
        """Send reply SMS message."""
        try:
            reply_message = GSMMessage(
                message_id=f"reply_{int(time.time())}",
                message_type=MessageType.SENIOR_SMS,
                sender=self.senior_phone_number,
                recipient=recipient,
                content=message,
                timestamp=time.time()
            )
            
            self.outgoing_messages.append(reply_message)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send reply SMS: {e}")
    
    def _check_rate_limit(self, recipient: str, message_type: str) -> bool:
        """Check if rate limit allows sending to recipient."""
        current_time = time.time()
        last_time = self.last_sms_time.get(recipient, 0)
        
        if message_type == 'sms':
            limit = self.sms_rate_limit
        elif message_type == 'call':
            limit = self.call_rate_limit
        else:
            return True
        
        if current_time - last_time < limit:
            return False
        
        self.last_sms_time[recipient] = current_time
        return True
    
    def _is_guardian_number(self, phone_number: str) -> bool:
        """Check if phone number belongs to a guardian."""
        return any(guardian['phone'] == phone_number for guardian in self.guardian_contacts)
    
    def _determine_call_priority(self, caller: str) -> CallPriority:
        """Determine call priority based on caller."""
        if self._is_guardian_number(caller):
            return CallPriority.HIGH
        elif caller in self.emergency_contacts:
            return CallPriority.EMERGENCY
        else:
            return CallPriority.NORMAL
    
    # Placeholder methods for actual implementation
    async def _fetch_incoming_messages(self) -> List[Dict[str, Any]]:
        """Fetch incoming messages from backend/GSM modem."""
        # This would interface with actual GSM modem or SMS gateway
        return []
    
    async def _fetch_incoming_calls(self) -> List[Dict[str, Any]]:
        """Fetch incoming calls from backend/GSM modem."""
        # This would interface with actual GSM modem
        return []
    
    async def _send_sms_message(self, message: GSMMessage) -> bool:
        """Send SMS message via GSM modem or gateway."""
        try:
            # This would interface with actual GSM modem or SMS gateway API
            print(f"📱 Sending SMS: {message.sender} → {message.recipient}: {message.content}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to send SMS: {e}")
            return False
    
    async def _initiate_gsm_call(self, call: VoiceCall) -> bool:
        """Initiate voice call via GSM modem."""
        try:
            # This would interface with actual GSM modem
            print(f"📞 Initiating call: {call.caller} → {call.recipient}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initiate call: {e}")
            return False
    
    async def _get_guardian_contact(self, guardian_id: str) -> Optional[Dict[str, Any]]:
        """Get guardian contact information."""
        try:
            response = requests.get(f"{self.backend_url}/guardians/{guardian_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            self.logger.error(f"❌ Failed to get guardian contact: {e}")
            return None
    
    async def _get_current_location(self) -> Optional[Dict[str, Any]]:
        """Get current location from GPS/vicinity system."""
        try:
            response = requests.get(f"{self.backend_url}/patients/{self.patient_id}/location")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            self.logger.error(f"❌ Failed to get location: {e}")
            return None
    
    async def _get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        try:
            response = requests.get(f"{self.backend_url}/patients/{self.patient_id}/health")
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            self.logger.error(f"❌ Failed to get health status: {e}")
            return {}
    
    async def _send_emergency_services_alert(self, alert_type: str, location: Dict = None, 
                                       medical_info: Dict = None):
        """Send alert to emergency services."""
        try:
            emergency_data = {
                "patient_id": self.patient_id,
                "alert_type": alert_type,
                "location": location,
                "medical_info": medical_info,
                "timestamp": datetime.now().isoformat(),
                "priority": "emergency"
            }
            
            response = requests.post(
                f"{self.backend_url}/emergency",
                json=emergency_data
            )
            
            if response.status_code == 200:
                self.logger.info("🚨 Emergency services notified")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to notify emergency services: {e}")
    
    async def _notify_missed_call(self, call: VoiceCall):
        """Notify guardians about missed call."""
        try:
            notification_data = {
                "type": "missed_call",
                "caller": call.caller,
                "timestamp": call.timestamp,
                "priority": call.priority.value
            }
            
            for guardian in self.guardian_contacts:
                await self.send_guardian_sms(
                    guardian['id'],
                    f"📞 Missed call from {call.caller}",
                    call.priority
                )
                
        except Exception as e:
            self.logger.error(f"❌ Failed to notify about missed call: {e}")
    
    async def _check_emergency_conditions(self):
        """Check for emergency conditions."""
        while True:
            try:
                # Check if emergency mode should be deactivated
                if self.emergency_mode:
                    # Deactivate after 30 minutes unless renewed
                    if time.time() - self.last_emergency_alert > 1800:
                        self.emergency_mode = False
                        self.logger.info("✅ Emergency mode deactivated")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"❌ Error checking emergency conditions: {e}")
                await asyncio.sleep(60)

# Global GSM system instance
_gsm_system = None

def initialize_enhanced_gsm(backend_url: str = "http://localhost:5000/api", 
                            patient_id: str = "demo_patient") -> EnhancedGSMSystem:
    """Initialize enhanced GSM system."""
    global _gsm_system
    _gsm_system = EnhancedGSMSystem(backend_url, patient_id)
    return _gsm_system

def get_gsm_system() -> EnhancedGSMSystem:
    """Get global GSM system instance."""
    return _gsm_system

async def start_gsm_monitoring():
    """Start GSM system monitoring."""
    if _gsm_system:
        await _gsm_system.start_monitoring()

async def send_guardian_sms(guardian_id: str, message: str, 
                           priority: CallPriority = CallPriority.NORMAL) -> bool:
    """Send SMS from guardian to senior."""
    if _gsm_system:
        return await _gsm_system.send_guardian_sms(guardian_id, message, priority)
    return False

async def initiate_guardian_call(guardian_id: str, 
                              priority: CallPriority = CallPriority.NORMAL) -> bool:
    """Initiate call from guardian to senior."""
    if _gsm_system:
        return await _gsm_system.initiate_voice_call(guardian_id, priority)
    return False

async def send_emergency_alert(alert_type: str, location: Dict = None, 
                           medical_info: Dict = None) -> bool:
    """Send emergency alert via GSM."""
    if _gsm_system:
        return await _gsm_system.send_emergency_alert(alert_type, location, medical_info)
    return False
