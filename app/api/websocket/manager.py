"""
WebSocket Connection Manager
Handles real-time communication with clients
"""

import asyncio
import json
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from app.core.logging import logger

class WebSocketManager:
    """Manages WebSocket connections"""
    
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> session_ids
        self.connection_info: Dict[str, Dict] = {}  # connection_id -> info
    
    async def initialize(self):
        """Initialize WebSocket manager"""
        logger.info("WebSocketManager initialized")
    
    async def handle_connection(self, websocket: WebSocket, user_id: str):
        """Handle new WebSocket connection"""
        await websocket.accept()
        
        connection_id = f"{user_id}_{datetime.utcnow().timestamp()}"
        
        # Store connection
        self.active_connections[connection_id] = websocket
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(connection_id)
        
        self.connection_info[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "message_count": 0
        }
        
        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
        
        try:
            # Send welcome message
            await self.send_message(
                connection_id,
                {
                    "type": "connected",
                    "message": "Connected to Elder AI Guardian",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Handle messages
            while True:
                data = await websocket.receive_text()
                await self.handle_message(connection_id, user_id, data)
                
        except WebSocketDisconnect:
            await self.handle_disconnect(connection_id, user_id)
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            await self.handle_disconnect(connection_id, user_id)
    
    async def handle_message(self, connection_id: str, user_id: str, data: str):
        """Handle incoming WebSocket message"""
        try:
            message_data = json.loads(data)
            
            # Update connection info
            if connection_id in self.connection_info:
                self.connection_info[connection_id]["last_activity"] = datetime.utcnow().isoformat()
                self.connection_info[connection_id]["message_count"] += 1
            
            message_type = message_data.get("type", "unknown")
            
            if message_type == "ping":
                await self.send_message(connection_id, {"type": "pong"})
                
            elif message_type == "chat":
                # Process chat message
                if self.orchestrator:
                    response = await self.orchestrator.process_message(
                        user_id=user_id,
                        message=message_data.get("content", ""),
                        metadata=message_data.get("metadata")
                    )
                    
                    await self.send_message(
                        connection_id,
                        {
                            "type": "chat_response",
                            "data": response,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                
            elif message_type == "emergency":
                # Forward to emergency agent
                if self.orchestrator and self.orchestrator.emergency_agent:
                    result = await self.orchestrator.emergency_agent.handle_emergency(
                        user_id=user_id,
                        message=message_data.get("message", "Emergency via WebSocket"),
                        location=message_data.get("location")
                    )
                    
                    await self.send_message(
                        connection_id,
                        {
                            "type": "emergency_response",
                            "data": result,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                
            elif message_type == "sensor_data":
                # Process sensor data (for fall detection)
                if self.orchestrator and self.orchestrator.emergency_agent:
                    result = await self.orchestrator.emergency_agent.detect_fall(
                        message_data.get("sensor_data", [])
                    )
                    
                    if result.get("is_fall"):
                        # Trigger emergency
                        await self.orchestrator.emergency_agent.handle_emergency(
                            user_id=user_id,
                            message="Fall detected via sensors",
                            location=message_data.get("location")
                        )
                        
                        await self.send_message(
                            connection_id,
                            {
                                "type": "fall_detected",
                                "data": result,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )
                
            elif message_type == "typing":
                # Broadcast typing indicator to other sessions
                await self.broadcast_to_user(
                    user_id,
                    {
                        "type": "typing",
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    exclude=[connection_id]
                )
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {data}")
            await self.send_message(
                connection_id,
                {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await self.send_message(
                connection_id,
                {
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    async def send_message(self, connection_id: str, message: dict):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {str(e)}")
    
    async def broadcast_to_user(self, user_id: str, message: dict, exclude: list = None):
        """Broadcast message to all user's connections"""
        if user_id in self.user_sessions:
            for connection_id in self.user_sessions[user_id]:
                if exclude and connection_id in exclude:
                    continue
                await self.send_message(connection_id, message)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connections"""
        for connection_id in list(self.active_connections.keys()):
            await self.send_message(connection_id, message)
    
    async def handle_disconnect(self, connection_id: str, user_id: str):
        """Handle WebSocket disconnection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if user_id in self.user_sessions and connection_id in self.user_sessions[user_id]:
            self.user_sessions[user_id].remove(connection_id)
            
            # Clean up if no more connections
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]
        
        if connection_id in self.connection_info:
            del self.connection_info[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def shutdown(self):
        """Shutdown all connections"""
        logger.info("Shutting down WebSocket connections")
        
        # Send shutdown message
        await self.broadcast_to_all({
            "type": "shutdown",
            "message": "Server is shutting down",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Close all connections
        for connection_id, websocket in list(self.active_connections.items()):
            try:
                await websocket.close()
            except:
                pass
        
        self.active_connections.clear()
        self.user_sessions.clear()
        self.connection_info.clear()
        
        logger.info("WebSocket connections closed")
    
    @property
    def active_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
    
    @property
    def user_count(self) -> int:
        """Get number of connected users"""
        return len(self.user_sessions)
