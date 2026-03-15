"""
Notification Service for sending alerts via multiple channels
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from app.core.logging import logger


class NotificationService:
    """
    Service for sending notifications via multiple channels
    Supports SMS, email, push notifications, and calls
    """
    
    def __init__(self, communication_service=None, db_service=None, cache_service=None):
        self.communication = communication_service
        self.db = db_service
        self.cache = cache_service
        self.is_healthy = False
        self.notification_history = {}
        
    async def initialize(self):
        """Initialize the notification service"""
        self.is_healthy = True
        logger.info("✅ Notification Service initialized")
    
    async def send_notification(
        self,
        user_id: str,
        type: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        priority: str = "MEDIUM"
    ) -> Dict[str, Any]:
        """
        Send a notification to a user
        """
        notification_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        notification = {
            "id": notification_id,
            "user_id": user_id,
            "type": type,
            "title": title,
            "body": body,
            "data": data or {},
            "priority": priority,
            "status": "sent",
            "created_at": timestamp,
            "read": False
        }
        
        # Store in history
        if user_id not in self.notification_history:
            self.notification_history[user_id] = []
        self.notification_history[user_id].append(notification)
        
        logger.info(f"📨 Sent {priority} notification to {user_id}: {title}")
        
        return notification
    
    async def send_sms(self, to: str, message: str) -> Dict:
        """Send SMS notification"""
        if self.communication:
            return await self.communication.send_sms(to, message)
        
        logger.info(f"[SIMULATED] SMS to {to}: {message[:50]}...")
        return {"success": True, "message_id": str(uuid.uuid4())}
    
    async def send_email(self, to: str, subject: str, body: str) -> Dict:
        """Send email notification"""
        if self.communication and hasattr(self.communication, 'send_email'):
            return await self.communication.send_email(to, subject, body)
        
        logger.info(f"[SIMULATED] Email to {to}: {subject}")
        return {"success": True, "message_id": str(uuid.uuid4())}
    
    async def send_push(self, user_id: str, title: str, body: str, data: Dict = None) -> Dict:
        """Send push notification"""
        logger.info(f"[SIMULATED] Push to {user_id}: {title}")
        return {"success": True, "notification_id": str(uuid.uuid4())}
    
    async def send_emergency_alert(
        self,
        user_id: str,
        emergency: Dict,
        contacts: List[Dict]
    ) -> Dict[str, Any]:
        """
        Send emergency alert to multiple contacts
        """
        results = {
            "sms": [],
            "calls": [],
            "email": []
        }
        
        for contact in contacts:
            phone = contact.get("phone")
            email = contact.get("email")
            name = contact.get("name", "Family Member")
            
            # Format message
            message = f"🚨 EMERGENCY: {user_id} needs help. Type: {emergency.get('type', 'Unknown')}"
            
            # Send SMS
            if phone and contact.get("notify_sms", True):
                sms_result = await self.send_sms(phone, message)
                results["sms"].append({
                    "contact": name,
                    **sms_result
                })
            
            # Make call for critical emergencies
            if phone and emergency.get("severity") == "CRITICAL" and contact.get("notify_call", True):
                call_result = await self.send_call(
                    phone,
                    f"This is an emergency alert for {user_id}. Please check immediately."
                )
                results["calls"].append({
                    "contact": name,
                    **call_result
                })
            
            # Send email
            if email and contact.get("notify_email", True):
                email_result = await self.send_email(
                    to=email,
                    subject=f"🚨 EMERGENCY: {user_id}",
                    body=f"""
                    Emergency Alert from Elder AI Guardian
                    
                    User: {user_id}
                    Type: {emergency.get('type', 'Unknown')}
                    Severity: {emergency.get('severity', 'Unknown')}
                    Time: {emergency.get('timestamp', datetime.utcnow().isoformat())}
                    Location: {emergency.get('location', 'Unknown')}
                    
                    Please respond immediately.
                    """
                )
                results["email"].append({
                    "contact": name,
                    **email_result
                })
        
        return {
            "emergency_id": emergency.get("id"),
            "notifications_sent": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def send_call(self, to: str, message: str) -> Dict:
        """Make an automated call"""
        if self.communication and hasattr(self.communication, 'make_call'):
            return await self.communication.make_call(to, message)
        
        logger.info(f"[SIMULATED] Call to {to}: {message[:50]}...")
        return {"success": True, "call_id": str(uuid.uuid4())}
    
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        if user_id in self.notification_history:
            for notification in self.notification_history[user_id]:
                if notification["id"] == notification_id:
                    notification["read"] = True
                    notification["read_at"] = datetime.utcnow().isoformat()
                    return True
        return False
    
    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Dict]:
        """Get notifications for a user"""
        notifications = self.notification_history.get(user_id, [])
        
        if unread_only:
            notifications = [n for n in notifications if not n.get("read", False)]
        
        # Sort by created_at desc and limit
        notifications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return notifications[:limit]
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get unread notification count for a user"""
        notifications = self.notification_history.get(user_id, [])
        return len([n for n in notifications if not n.get("read", False)])
    
    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete a notification"""
        if user_id in self.notification_history:
            initial_count = len(self.notification_history[user_id])
            self.notification_history[user_id] = [
                n for n in self.notification_history[user_id]
                if n["id"] != notification_id
            ]
            return len(self.notification_history[user_id]) < initial_count
        return False
    
    async def health_check(self) -> bool:
        """Check if service is healthy"""
        return self.is_healthy