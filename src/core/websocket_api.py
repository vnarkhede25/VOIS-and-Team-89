"""
Real-time WebSocket API for Live Dashboard Updates

Provides WebSocket endpoints for real-time sensor data, events, and system status.
All frontend dashboards connect here for live updates without page reloads.
"""

import asyncio
import json
import time
from typing import Dict, Any, Set
from datetime import datetime
import websockets
import threading

from ..core.realtime_system_integration import get_system_integration, initialize_system_integration

class WebSocketManager:
    """Manages WebSocket connections and broadcasts."""
    
    def __init__(self):
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.system_integration = initialize_system_integration()
        self.is_running = False
        
        # Connect to system events
        self.system_integration.add_event_callback(self._broadcast_event)
        
    async def register_client(self, websocket, path):
        """Register a new WebSocket client."""
        self.clients.add(websocket)
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}_{int(time.time())}"
        
        print(f"🔗 Client connected: {client_id}")
        
        try:
            # Send initial system status
            await self._send_system_status(websocket)
            
            # Send recent sensor data
            await self._send_recent_sensor_data(websocket)
            
            # Keep connection alive and handle messages
            async for message in websocket:
                await self._handle_client_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            print(f"❌ Client disconnected: {client_id}")
        except Exception as e:
            print(f"❌ Client error: {client_id} - {e}")
        finally:
            self.clients.discard(websocket)
    
    async def _handle_client_message(self, websocket, message):
        """Handle incoming messages from clients."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'get_status':
                await self._send_system_status(websocket)
            elif message_type == 'force_event':
                event_type = data.get('event')
                self.system_integration.force_event(event_type)
            elif message_type == 'get_history':
                limit = data.get('limit', 50)
                await self._send_sensor_history(websocket, limit)
            elif message_type == 'ping':
                await websocket.send(json.dumps({'type': 'pong'}))
                
        except Exception as e:
            print(f"Message handling error: {e}")
    
    async def _send_system_status(self, websocket):
        """Send current system status to client."""
        try:
            status = self.system_integration.get_system_status()
            await websocket.send(json.dumps({
                'type': 'system_status',
                'data': status,
                'timestamp': datetime.now().isoformat()
            }))
        except Exception as e:
            print(f"Status send error: {e}")
    
    async def _send_recent_sensor_data(self, websocket):
        """Send recent sensor data to client."""
        try:
            sensor_data = self.system_integration.get_sensor_data()
            await websocket.send(json.dumps({
                'type': 'sensor_data',
                'data': sensor_data,
                'timestamp': datetime.now().isoformat()
            }))
        except Exception as e:
            print(f"Sensor data send error: {e}")
    
    async def _send_sensor_history(self, websocket, limit: int):
        """Send sensor history to client."""
        try:
            history = self.system_integration.get_sensor_history(limit)
            await websocket.send(json.dumps({
                'type': 'sensor_history',
                'data': history,
                'timestamp': datetime.now().isoformat()
            }))
        except Exception as e:
            print(f"History send error: {e}")
    
    async def _broadcast_event(self, event_data: Dict[str, Any]):
        """Broadcast system event to all connected clients."""
        if not self.clients:
            return
        
        message = json.dumps({
            'type': 'system_event',
            'data': event_data,
            'timestamp': datetime.now().isoformat()
        })
        
        # Send to all clients
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                print(f"Broadcast error: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected_clients
    
    async def _broadcast_sensor_data(self, sensor_data: Dict[str, Any]):
        """Broadcast sensor data to all connected clients."""
        if not self.clients:
            return
        
        message = json.dumps({
            'type': 'sensor_data',
            'data': sensor_data,
            'timestamp': datetime.now().isoformat()
        })
        
        # Send to all clients
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                print(f"Sensor broadcast error: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected_clients
    
    async def start_server(self, host='localhost', port=8765):
        """Start the WebSocket server."""
        print(f"🚀 Starting WebSocket server on ws://{host}:{port}")
        
        # Start the real-time system
        self.system_integration.start_system()
        
        # Start WebSocket server
        self.is_running = True
        async with websockets.serve(self.register_client, host, port):
            print(f"✅ WebSocket server running on ws://{host}:{port}")
            await asyncio.Future()  # Run forever
    
    def stop_server(self):
        """Stop the WebSocket server."""
        self.is_running = False
        self.system_integration.stop_system()
        print("⏹️ WebSocket server stopped")

# Global WebSocket manager
_websocket_manager = None

def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager."""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager

async def start_websocket_server(host='localhost', port=8765):
    """Start the WebSocket server."""
    manager = get_websocket_manager()
    await manager.start_server(host, port)

def stop_websocket_server():
    """Stop the WebSocket server."""
    manager = get_websocket_manager()
    manager.stop_server()

# Sensor data callback for broadcasting
def sensor_data_callback(sensor_data: Dict[str, Any]):
    """Callback for sensor data updates."""
    manager = get_websocket_manager()
    if manager.is_running:
        # Run broadcast in asyncio event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager._broadcast_sensor_data(sensor_data))
        except:
            pass

# Connect sensor data callback to system
def setup_sensor_broadcast():
    """Setup sensor data broadcasting."""
    system_integration = get_system_integration()
    if system_integration:
        simulator = system_integration.simulator
        simulator.add_callback(sensor_data_callback)
