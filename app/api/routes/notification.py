"""
Notification Routes
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.core.logging import logger
from app.core.dependencies import get_orchestrator, get_auth_user
router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    body: str
    priority: str
    read: bool
    created_at: str
    data: Optional[Dict[str, Any]] = None

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int

@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    unread_only: bool = False,
    orchestrator = Depends(get_orchestrator),
    user = Depends(get_auth_user)
):
    """Get notifications for the current user"""
    
    notification_service = getattr(orchestrator, 'notification_service', None)
    
    if not notification_service:
        # Return mock data if service not available
        return {
            "notifications": [],
            "total": 0,
            "unread_count": 0
        }
    
    try:
        notifications = await notification_service.get_user_notifications(
            user_id=user.id,
            limit=limit,
            unread_only=unread_only
        )
        
        unread_count = await notification_service.get_unread_count(user.id)
        
        return {
            "notifications": notifications,
            "total": len(notifications),
            "unread_count": unread_count
        }
        
    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    request: Request,
    orchestrator = Depends(get_orchestrator),
    user = Depends(get_auth_user)
):
    """Mark a notification as read"""
    
    notification_service = getattr(orchestrator, 'notification_service', None)
    
    if not notification_service:
        return {"success": True, "message": "Mock: marked as read"}
    
    try:
        success = await notification_service.mark_as_read(notification_id, user.id)
        
        if success:
            return {"success": True, "message": "Notification marked as read"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
            
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/read-all")
async def mark_all_as_read(
    request: Request,
    orchestrator = Depends(get_orchestrator),
    user = Depends(get_auth_user)
):
    """Mark all notifications as read"""
    
    notification_service = getattr(orchestrator, 'notification_service', None)
    
    if not notification_service:
        return {"success": True, "message": "Mock: all marked as read"}
    
    try:
        notifications = await notification_service.get_user_notifications(user.id, unread_only=True)
        
        for notification in notifications:
            await notification_service.mark_as_read(notification["id"], user.id)
        
        return {"success": True, "message": f"Marked {len(notifications)} notifications as read"}
        
    except Exception as e:
        logger.error(f"Failed to mark all as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    request: Request,
    orchestrator = Depends(get_orchestrator),
    user = Depends(get_auth_user)
):
    """Delete a notification"""
    
    notification_service = getattr(orchestrator, 'notification_service', None)
    
    if not notification_service:
        return {"success": True, "message": "Mock: deleted"}
    
    try:
        success = await notification_service.delete_notification(notification_id, user.id)
        
        if success:
            return {"success": True, "message": "Notification deleted"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
            
    except Exception as e:
        logger.error(f"Failed to delete notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unread-count")
async def get_unread_count(
    request: Request,
    orchestrator = Depends(get_orchestrator),
    user = Depends(get_auth_user)
):
    """Get unread notification count"""
    
    notification_service = getattr(orchestrator, 'notification_service', None)
    
    if not notification_service:
        return {"count": 0}
    
    try:
        count = await notification_service.get_unread_count(user.id)
        return {"count": count}
        
    except Exception as e:
        logger.error(f"Failed to get unread count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def send_test_notification(
    request: Request,
    title: str = "Test Notification",
    body: str = "This is a test notification",
    orchestrator = Depends(get_orchestrator),
    user = Depends(get_auth_user)
):
    """Send a test notification (for development)"""
    
    notification_service = getattr(orchestrator, 'notification_service', None)
    
    if not notification_service:
        return {
            "success": True,
            "notification": {
                "id": str(uuid.uuid4()),
                "user_id": user.id,
                "type": "test",
                "title": title,
                "body": body,
                "priority": "MEDIUM",
                "read": False,
                "created_at": datetime.utcnow().isoformat()
            }
        }
    
    try:
        notification = await notification_service.send_notification(
            user_id=user.id,
            type="test",
            title=title,
            body=body,
            priority="MEDIUM"
        )
        
        return {"success": True, "notification": notification}
        
    except Exception as e:
        logger.error(f"Failed to send test notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))