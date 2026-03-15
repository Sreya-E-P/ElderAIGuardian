"""
Family Notification Agent
Sends intelligent notifications to family members based on priority
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from app.core.logging import logger

class FamilyNotificationAgent:
    """Agent specialized in family notifications"""
    
    def __init__(self, 
                 foundry_agent=None,
                 model_router=None,
                 communication_service=None, 
                 db_service=None, 
                 cache_service=None,
                 notification_service=None):
        
        self.foundry_agent = foundry_agent
        self.model_router = model_router
        self.communication_service = communication_service
        self.db_service = db_service
        self.cache_service = cache_service
        self.notification_service = notification_service
        self.notification_history = {}
        
        logger.info("FamilyNotificationAgent initialized")
    
    async def initialize(self):
        """Initialize agent resources"""
        logger.info("FamilyNotificationAgent initialized")
    
    async def send_notification(
        self,
        user_id: str,
        event_type: str,
        data: Dict,
        priority: str = "MEDIUM",
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send notification to family members"""
        
        notification_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        # Get user's family contacts
        contacts = await self._get_family_contacts(user_id)
        
        if not contacts:
            logger.warning(f"No family contacts found for user {user_id}")
            return {
                "status": "no_contacts", 
                "notification_id": notification_id,
                "message": "No family contacts found"
            }
        
        # Determine notification priority if not specified
        if not priority or priority == "AUTO":
            priority = await self._determine_priority(event_type, data)
        
        # Get preferred channels
        if not channels:
            channels = self._get_channels_for_priority(priority)
        
        # Create notification
        notification = {
            "id": notification_id,
            "user_id": user_id,
            "event_type": event_type,
            "data": data,
            "priority": priority,
            "channels": channels,
            "timestamp": timestamp.isoformat(),
            "status": "PENDING",
            "delivery_results": []
        }
        
        # Store in history
        if user_id not in self.notification_history:
            self.notification_history[user_id] = []
        self.notification_history[user_id].append(notification)
        
        # Send to each contact
        delivery_results = []
        successful_contacts = 0
        
        for contact in contacts:
            if contact.get("notifications_enabled", True):
                result = await self._send_to_contact(contact, notification)
                delivery_results.append(result)
                if result.get("success", False):
                    successful_contacts += 1
        
        notification["status"] = "SENT" if successful_contacts > 0 else "FAILED"
        notification["delivery_results"] = delivery_results
        notification["successful_contacts"] = successful_contacts
        notification["total_contacts"] = len(contacts)
        
        # Save to database
        if self.db_service:
            try:
                await self.db_service.save_notification(notification)
            except Exception as e:
                logger.error(f"Failed to save notification: {str(e)}")
        
        return {
            "notification_id": notification_id,
            "status": notification["status"],
            "priority": priority,
            "contacts_notified": successful_contacts,
            "total_contacts": len(contacts),
            "delivery_results": delivery_results,
            "timestamp": timestamp.isoformat()
        }
    
    async def send_bulk_notifications(
        self,
        notifications: List[Dict]
    ) -> List[Dict]:
        """Send multiple notifications"""
        results = []
        for notification in notifications:
            result = await self.send_notification(
                user_id=notification["user_id"],
                event_type=notification["event_type"],
                data=notification["data"],
                priority=notification.get("priority", "MEDIUM")
            )
            results.append(result)
        return results
    
    async def _send_to_contact(self, contact: Dict, notification: Dict) -> Dict:
        """Send notification to a single contact"""
        results = {}
        success = False
        
        for channel in notification["channels"]:
            try:
                if channel == "sms" and contact.get("phone"):
                    result = await self._send_sms(contact, notification)
                    results[channel] = result
                    if result.get("success"):
                        success = True
                
                elif channel == "email" and contact.get("email"):
                    result = await self._send_email(contact, notification)
                    results[channel] = result
                    if result.get("success"):
                        success = True
                
                elif channel == "push" and contact.get("push_token"):
                    result = await self._send_push(contact, notification)
                    results[channel] = result
                    if result.get("success"):
                        success = True
                
                elif channel == "call" and contact.get("phone"):
                    result = await self._send_call(contact, notification)
                    results[channel] = result
                    if result.get("success"):
                        success = True
                
                elif channel == "whatsapp" and contact.get("phone"):
                    result = await self._send_whatsapp(contact, notification)
                    results[channel] = result
                    if result.get("success"):
                        success = True
                
            except Exception as e:
                logger.error(f"Failed to send {channel} to {contact.get('name')}: {str(e)}")
                results[channel] = {"success": False, "error": str(e)}
        
        return {
            "contact_id": contact.get("id"),
            "contact_name": contact.get("name"),
            "success": success,
            "channels": results
        }
    
    async def _send_sms(self, contact: Dict, notification: Dict) -> Dict:
        """Send SMS notification"""
        if not self.communication_service:
            return {"success": False, "error": "Communication service not available"}
        
        try:
            message = self._format_sms_message(notification)
            
            result = await self.communication_service.send_sms(
                to=contact["phone"],
                message=message
            )
            
            return {"success": True, "message_id": result.get("message_id")}
            
        except Exception as e:
            logger.error(f"SMS sending failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _send_email(self, contact: Dict, notification: Dict) -> Dict:
        """Send email notification"""
        if not self.communication_service or not hasattr(self.communication_service, 'send_email'):
            return {"success": False, "error": "Email service not available"}
        
        try:
            subject, body = self._format_email_message(notification)
            
            result = await self.communication_service.send_email(
                to=contact["email"],
                subject=subject,
                body=body
            )
            
            return {"success": True, "message_id": result.get("message_id")}
            
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _send_push(self, contact: Dict, notification: Dict) -> Dict:
        """Send push notification"""
        # In production, would use Firebase Cloud Messaging or similar
        # For hackathon, simulate success
        return {"success": True, "method": "simulated"}
    
    async def _send_call(self, contact: Dict, notification: Dict) -> Dict:
        """Make automated call"""
        if not self.communication_service:
            return {"success": False, "error": "Communication service not available"}
        
        try:
            message = self._format_call_message(notification)
            
            result = await self.communication_service.make_call(
                to=contact["phone"],
                message=message
            )
            
            return {"success": True, "call_id": result.get("call_id")}
            
        except Exception as e:
            logger.error(f"Call failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _send_whatsapp(self, contact: Dict, notification: Dict) -> Dict:
        """Send WhatsApp message"""
        # In production, would use Twilio or similar
        return {"success": False, "error": "WhatsApp not implemented"}
    
    async def _determine_priority(self, event_type: str, data: Dict) -> str:
        """Determine notification priority"""
        
        # Priority mapping
        priority_map = {
            "emergency": "URGENT",
            "fall_detected": "URGENT",
            "scam_alert": "HIGH",
            "missed_medication": "HIGH",
            "low_adherence": "MEDIUM",
            "medication_reminder": "MEDIUM",
            "daily_summary": "LOW",
            "wellness_tip": "LOW",
            "greeting": "LOW",
            "mood_alert": "MEDIUM"
        }
        
        base_priority = priority_map.get(event_type, "MEDIUM")
        
        # Use Foundry for intelligent priority if available
        if self.foundry_agent:
            try:
                prompt = f"""
                Determine notification priority (URGENT/HIGH/MEDIUM/LOW) for:
                Event: {event_type}
                Data: {json.dumps(data)}
                Base priority: {base_priority}
                
                Consider: time of day, user history, severity.
                Return just the priority level.
                """
                
                response = await self.foundry_agent.generate_chat(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=20
                )
                
                priority = response.get("content", "").strip().upper()
                if priority in ["URGENT", "HIGH", "MEDIUM", "LOW"]:
                    return priority
            except Exception as e:
                logger.warning(f"Priority determination failed: {str(e)}")
        
        return base_priority
    
    def _get_channels_for_priority(self, priority: str) -> List[str]:
        """Get notification channels based on priority"""
        if priority == "URGENT":
            return ["sms", "call", "push", "email"]
        elif priority == "HIGH":
            return ["sms", "push", "email"]
        elif priority == "MEDIUM":
            return ["push", "email"]
        else:  # LOW
            return ["push"]
    
    def _format_sms_message(self, notification: Dict) -> str:
        """Format SMS message"""
        event_type = notification["event_type"].replace("_", " ").title()
        
        messages = {
            "emergency": f"🚨 EMERGENCY: {notification['data'].get('message', 'Help needed')}",
            "fall_detected": "🚨 Fall detected! Please check on your loved one immediately.",
            "scam_alert": f"⚠️ Scam Alert: {notification['data'].get('message', 'Suspicious activity')}",
            "missed_medication": f"⚠️ Medication Alert: {notification['data'].get('medication', 'Medication')} was missed",
            "daily_summary": f"📊 Daily Summary for {notification['user_id']}",
            "mood_alert": f"😊 Mood Update: {notification['data'].get('label', 'Update')}"
        }
        
        return messages.get(notification["event_type"], f"Notification: {event_type}")
    
    def _format_email_message(self, notification: Dict) -> tuple:
        """Format email subject and body"""
        event_type = notification["event_type"].replace("_", " ").title()
        
        subject = f"Elder AI Guardian - {event_type}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #4a90e2; padding: 20px; text-align: center; color: white;">
                <h1>Elder AI Guardian</h1>
                <p>Notification from your loved one's guardian system</p>
            </div>
            
            <div style="padding: 20px; background-color: #f9f9f9;">
                <h2 style="color: #333;">{event_type}</h2>
                
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p><strong>Time:</strong> {notification['timestamp']}</p>
                    <p><strong>User:</strong> {notification['user_id']}</p>
                    <p><strong>Priority:</strong> {notification['priority']}</p>
                </div>
                
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3>Details:</h3>
                    <pre style="white-space: pre-wrap; font-family: inherit;">{json.dumps(notification['data'], indent=2)}</pre>
                </div>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    This is an automated message from Elder AI Guardian.<br>
                    Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        return subject, body
    
    def _format_call_message(self, notification: Dict) -> str:
        """Format call message"""
        messages = {
            "emergency": "This is an emergency alert from Elder AI Guardian. Please check on your loved one immediately.",
            "fall_detected": "Fall detected alert from Elder AI Guardian. Please respond immediately.",
            "scam_alert": "Scam alert from Elder AI Guardian. Please contact your loved one."
        }
        
        return messages.get(
            notification["event_type"],
            "This is an automated notification from Elder AI Guardian."
        )
    
    async def _get_family_contacts(self, user_id: str) -> List[Dict]:
        """Get family contacts for user"""
        if self.db_service:
            try:
                contacts = await self.db_service.get_family_contacts(user_id) or []
                
                # Ensure each contact has required fields
                for contact in contacts:
                    if "notifications_enabled" not in contact:
                        contact["notifications_enabled"] = True
                    if "prefer_sms" not in contact:
                        contact["prefer_sms"] = True
                    if "prefer_call" not in contact:
                        contact["prefer_call"] = False
                
                return contacts
            except Exception as e:
                logger.error(f"Failed to get contacts: {str(e)}")
        
        # Return mock contacts for development
        return [
            {
                "id": "contact1",
                "name": "Family Member",
                "relationship": "family",
                "phone": "+1234567890",
                "email": "family@example.com",
                "notifications_enabled": True,
                "prefer_sms": True,
                "prefer_call": False
            }
        ]