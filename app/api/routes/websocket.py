"""
WebSocket Routes for real-time communication
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from typing import Dict
from datetime import datetime

from app.core.logging import logger

router = APIRouter()

active_connections: Dict[str, WebSocket] = {}
connection_sessions: Dict[str, str] = {}

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    connection_id = f"conn_{len(active_connections) + 1}"
    active_connections[connection_id] = websocket
    connection_sessions[connection_id] = user_id
    
    logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
    
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Elder AI Guardian",
            "connection_id": connection_id,
            "hero_technologies": {
                "foundry": True,
                "mcp": True,
                "agent_framework": True,
                "devops": True,
                "cosmos_db": True,
                "live_alerts": True
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type", "unknown")
            
            if message_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message_type == "mcp_tools":
                await websocket.send_json({
                    "type": "mcp_tools",
                    "data": {
                        "tools": [
                            {"name": "search_scam_database", "description": "Search scam threat database"},
                            {"name": "send_emergency_alert", "description": "Send emergency alert"},
                            {"name": "get_medication_info", "description": "Get medication information"},
                            {"name": "check_wellness_status", "description": "Check wellness status"},
                            {"name": "notify_family", "description": "Notify family members"},
                            {"name": "get_health_records", "description": "Get health records"},
                            {"name": "schedule_reminder", "description": "Schedule medication reminder"},
                            {"name": "analyze_threat", "description": "Analyze security threat"},
                            {"name": "get_emergency_contacts", "description": "Get emergency contacts"}
                        ],
                        "count": 9
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })

            elif message_type == "echo":
                await websocket.send_json({
                    "type": "echo",
                    "data": data.get("data", {}),
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message_type == "broadcast":
                await broadcast_to_user(user_id, {
                    "type": "broadcast",
                    "data": data.get("data", {}),
                    "from": connection_id,
                    "timestamp": datetime.utcnow().isoformat()
                }, exclude=[connection_id])
            
            else:
                await websocket.send_json({
                    "type": "response",
                    "original_type": message_type,
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id} for user {user_id}")
        if connection_id in active_connections:
            del active_connections[connection_id]
        if connection_id in connection_sessions:
            del connection_sessions[connection_id]
    
    except Exception as e:
        logger.error(f"WebSocket error for {user_id}: {str(e)}")
        if connection_id in active_connections:
            del active_connections[connection_id]
        if connection_id in connection_sessions:
            del connection_sessions[connection_id]


async def broadcast_to_user(user_id: str, message: dict, exclude: list = None):
    if exclude is None:
        exclude = []
    for conn_id, ws in active_connections.items():
        if conn_id not in exclude and connection_sessions.get(conn_id) == user_id:
            try:
                await ws.send_json(message)
            except:
                pass


@router.get("/connections")
async def get_connections(request: Request):
    return {
        "total_connections": len(active_connections),
        "unique_users": len(set(connection_sessions.values())),
    }


@router.post("/broadcast")
async def broadcast_message(request: Request, data: dict):
    message = {
        "type": "broadcast",
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    sent_count = 0
    for conn_id, ws in active_connections.items():
        try:
            await ws.send_json(message)
            sent_count += 1
        except:
            pass
    return {"success": True, "sent_count": sent_count}