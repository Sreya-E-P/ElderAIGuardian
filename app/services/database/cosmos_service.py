"""
Cosmos DB Service for Azure Cosmos DB
ENHANCED with Alert Tracking for Closed-Loop Escalation
FIXED - WITH CROSS-PARTITION QUERIES + ALIAS METHODS
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
import json

from azure.cosmos import CosmosClient, exceptions
from azure.cosmos.partition_key import PartitionKey

from app.core.logging import logger
from app.core.config import settings
from app.services.database.base import DatabaseService


class CosmosService(DatabaseService):
    """Service for Azure Cosmos DB - ENHANCED with alert tracking"""
    
    def __init__(self, client: CosmosClient):
        self.client = client
        self.is_healthy = False
        self.database = None
        self.containers = {}
        
    async def initialize(self):
        """Initialize the Cosmos DB service"""
        try:
            database_name = settings.COSMOS_DB_DATABASE or "elderaidb"
            
            try:
                self.database = self.client.get_database_client(database_name)
                list(self.database.list_containers(max_item_count=1))
                logger.info(f"✅ Connected to existing database: {database_name}")
            except exceptions.CosmosResourceNotFoundError:
                self.database = self.client.create_database(database_name)
                logger.info(f"✅ Created database: {database_name}")
            except Exception as e:
                logger.error(f"❌ Database connection error: {e}")
                raise
            
            container_configs = {
                "users": "/id",
                "sessions": "/user_id",
                "medications": "/user_id",
                "emergencies": "/user_id",
                "emergency_contacts": "/user_id",
                "notifications": "/user_id",
                "wellness": "/user_id",
                "scam_reports": "/user_id",
                "chat_sessions": "/user_id",
                "chat_messages": "/session_id",
                "analytics_events": "/user_id",
                "alerts": "/user_id",
                "audit_logs": "/emergency_id",
                "threat_intel": "/type",
            }
            
            for container_name, partition_key in container_configs.items():
                try:
                    self.containers[container_name] = self.database.get_container_client(container_name)
                    list(self.containers[container_name].query_items(
                        "SELECT TOP 1 * FROM c",
                        max_item_count=1
                    ))
                    logger.info(f"  ✅ Connected to container: {container_name}")
                except exceptions.CosmosResourceNotFoundError:
                    self.containers[container_name] = self.database.create_container(
                        id=container_name,
                        partition_key=PartitionKey(path=partition_key),
                        offer_throughput=settings.COSMOS_DB_THROUGHPUT or 400
                    )
                    logger.info(f"  ✅ Created container: {container_name}")
                except Exception as e:
                    logger.warning(f"  ⚠️ Container {container_name} not accessible: {str(e)}")
            
            self.is_healthy = True
            logger.info("✅ COSMOS DB INITIALIZED")
            logger.info(f"   Database: {database_name}")
            logger.info(f"   Containers: {len(self.containers)}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize CosmosService: {str(e)}")
            raise
    
    # ==================== THREAT INTELLIGENCE ====================
    
    async def save_threat_intel(self, threat_data: Dict[str, Any]) -> str:
        try:
            if "threat_intel" not in self.containers:
                return ""
            if "id" not in threat_data:
                threat_data["id"] = str(uuid.uuid4())
            threat_data["created_at"] = threat_data.get("created_at", datetime.utcnow().isoformat())
            threat_data["updated_at"] = datetime.utcnow().isoformat()
            threat_data["_ts"] = datetime.utcnow().timestamp()
            self.containers["threat_intel"].upsert_item(threat_data)
            return threat_data["id"]
        except Exception as e:
            logger.error(f"❌ Failed to save threat intel: {str(e)}")
            return ""
    
    async def get_recent_threats(self, threat_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            if "threat_intel" not in self.containers:
                return []
            cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
            if threat_type and threat_type != "all":
                query = "SELECT * FROM c WHERE c.type = @type AND c.created_at >= @cutoff ORDER BY c.created_at DESC OFFSET 0 LIMIT @limit"
                parameters = [
                    {"name": "@type", "value": threat_type},
                    {"name": "@cutoff", "value": cutoff},
                    {"name": "@limit", "value": limit}
                ]
            else:
                query = "SELECT * FROM c WHERE c.created_at >= @cutoff ORDER BY c.created_at DESC OFFSET 0 LIMIT @limit"
                parameters = [
                    {"name": "@cutoff", "value": cutoff},
                    {"name": "@limit", "value": limit}
                ]
            items = list(self.containers["threat_intel"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return [dict(item) for item in items]
        except Exception as e:
            logger.error(f"❌ Failed to get threat intel: {str(e)}")
            return []
    
    # ==================== ALERT METHODS ====================
    
    async def save_alert(self, alert_data: Dict[str, Any]) -> str:
        try:
            if "alerts" not in self.containers:
                return ""
            if "id" not in alert_data:
                alert_data["id"] = str(uuid.uuid4())
            alert_data["created_at"] = alert_data.get("created_at", datetime.utcnow().isoformat())
            alert_data["updated_at"] = datetime.utcnow().isoformat()
            alert_data["_ts"] = datetime.utcnow().timestamp()
            alert_data["status"] = alert_data.get("status", "active")
            self.containers["alerts"].upsert_item(alert_data)
            return alert_data["id"]
        except Exception as e:
            logger.error(f"❌ Failed to save alert: {str(e)}")
            return ""
    
    async def get_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        try:
            if "alerts" not in self.containers:
                return None
            query = "SELECT * FROM c WHERE c.id = @id"
            parameters = [{"name": "@id", "value": alert_id}]
            items = list(self.containers["alerts"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return dict(items[0]) if items else None
        except Exception as e:
            logger.error(f"❌ Failed to get alert {alert_id}: {str(e)}")
            return None
    
    async def update_alert(self, alert_id: str, updates: Dict[str, Any]) -> bool:
        try:
            alert = await self.get_alert(alert_id)
            if not alert:
                return False
            alert.update(updates)
            alert["updated_at"] = datetime.utcnow().isoformat()
            alert["_ts"] = datetime.utcnow().timestamp()
            self.containers["alerts"].upsert_item(alert)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update alert {alert_id}: {str(e)}")
            return False
    
    async def get_user_alerts(self, user_id: str, active_only: bool = True, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            if "alerts" not in self.containers:
                return []
            if active_only:
                query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.status = 'active' ORDER BY c._ts DESC OFFSET 0 LIMIT @limit"
            else:
                query = "SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c._ts DESC OFFSET 0 LIMIT @limit"
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@limit", "value": limit}
            ]
            items = list(self.containers["alerts"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return [dict(item) for item in items]
        except Exception as e:
            logger.error(f"❌ Failed to get alerts for user {user_id}: {str(e)}")
            return []
    
    async def get_unconfirmed_alerts(self, older_than_minutes: int = 5) -> List[Dict[str, Any]]:
        try:
            if "alerts" not in self.containers:
                return []
            cutoff_time = (datetime.utcnow() - timedelta(minutes=older_than_minutes)).isoformat()
            query = "SELECT * FROM c WHERE c.status = 'active' AND c.confirmed = false AND c.sent_at <= @cutoff"
            parameters = [{"name": "@cutoff", "value": cutoff_time}]
            items = list(self.containers["alerts"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return [dict(item) for item in items]
        except Exception as e:
            logger.error(f"❌ Failed to get unconfirmed alerts: {str(e)}")
            return []
    
    async def mark_alert_confirmed(self, alert_id: str, confirmed_by: str) -> bool:
        try:
            alert = await self.get_alert(alert_id)
            if not alert:
                return False
            alert["confirmed"] = True
            alert["confirmed_by"] = confirmed_by
            alert["confirmed_at"] = datetime.utcnow().isoformat()
            alert["status"] = "resolved"
            alert["updated_at"] = datetime.utcnow().isoformat()
            alert["_ts"] = datetime.utcnow().timestamp()
            sent_at_str = alert.get("sent_at", alert["created_at"])
            if isinstance(sent_at_str, str):
                sent_at = datetime.fromisoformat(sent_at_str.replace('Z', '+00:00'))
            else:
                sent_at = sent_at_str
            response_time = (datetime.utcnow() - sent_at).total_seconds()
            alert["response_time_seconds"] = response_time
            self.containers["alerts"].upsert_item(alert)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to confirm alert {alert_id}: {str(e)}")
            return False
    
    # ==================== AUDIT LOG ====================
    
    async def log_audit_event(self, event_data: Dict[str, Any]) -> str:
        try:
            if "audit_logs" not in self.containers:
                return ""
            if "id" not in event_data:
                event_data["id"] = str(uuid.uuid4())
            event_data["timestamp"] = event_data.get("timestamp", datetime.utcnow().isoformat())
            event_data["_ts"] = datetime.utcnow().timestamp()
            self.containers["audit_logs"].upsert_item(event_data)
            return event_data["id"]
        except Exception as e:
            logger.error(f"❌ Failed to log audit event: {str(e)}")
            return ""
    
    # ==================== USER METHODS ====================
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            if "users" not in self.containers:
                return None
            try:
                user = self.containers["users"].read_item(item=user_id, partition_key=user_id)
                return dict(user)
            except exceptions.CosmosResourceNotFoundError:
                return None
        except Exception as e:
            logger.error(f"❌ Failed to get user {user_id}: {str(e)}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            if "users" not in self.containers:
                return None
            query = "SELECT * FROM c WHERE c.email = @email"
            parameters = [{"name": "@email", "value": email}]
            items = list(self.containers["users"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return dict(items[0]) if items else None
        except Exception as e:
            logger.error(f"❌ Failed to get user by email {email}: {str(e)}")
            return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        try:
            if "users" not in self.containers:
                raise ValueError("Users container not available")
            if "id" not in user_data:
                user_data["id"] = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            user_data["created_at"] = now
            user_data["updated_at"] = now
            user_data["_ts"] = datetime.utcnow().timestamp()
            self.containers["users"].upsert_item(user_data)
            logger.info(f"✅ Created user: {user_data['id']}")
            return user_data["id"]
        except Exception as e:
            logger.error(f"❌ Failed to create user: {str(e)}")
            raise
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            user.update(updates)
            user["updated_at"] = datetime.utcnow().isoformat()
            user["_ts"] = datetime.utcnow().timestamp()
            self.containers["users"].upsert_item(user)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update user {user_id}: {str(e)}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        try:
            self.containers["users"].delete_item(item=user_id, partition_key=user_id)
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete user {user_id}: {str(e)}")
            return False
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            if "users" not in self.containers:
                return []
            query = "SELECT * FROM c OFFSET @skip LIMIT @limit"
            parameters = [{"name": "@skip", "value": skip}, {"name": "@limit", "value": limit}]
            items = list(self.containers["users"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return [dict(item) for item in items]
        except Exception as e:
            logger.error(f"❌ Failed to get all users: {str(e)}")
            return []
    
    # ==================== SESSION METHODS ====================
    
    async def save_session(self, session_data: Dict[str, Any]) -> str:
        try:
            if "sessions" not in self.containers:
                return ""
            if "id" not in session_data:
                session_data["id"] = str(uuid.uuid4())
            session_data["created_at"] = datetime.utcnow().isoformat()
            session_data["_ts"] = datetime.utcnow().timestamp()
            self.containers["sessions"].upsert_item(session_data)
            return session_data["id"]
        except Exception as e:
            logger.error(f"❌ Failed to save session: {str(e)}")
            return ""
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            if "sessions" not in self.containers:
                return None
            query = "SELECT * FROM c WHERE c.id = @id"
            parameters = [{"name": "@id", "value": session_id}]
            items = list(self.containers["sessions"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return dict(items[0]) if items else None
        except Exception as e:
            logger.error(f"❌ Failed to get session {session_id}: {str(e)}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            self.containers["sessions"].delete_item(
                item=session_id, partition_key=session.get("user_id", "")
            )
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete session {session_id}: {str(e)}")
            return False
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            if "sessions" not in self.containers:
                return []
            query = "SELECT * FROM c WHERE c.user_id = @user_id"
            parameters = [{"name": "@user_id", "value": user_id}]
            items = list(self.containers["sessions"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return [dict(item) for item in items]
        except Exception as e:
            logger.error(f"❌ Failed to get user sessions for {user_id}: {str(e)}")
            return []
    
    async def delete_user_sessions(self, user_id: str, exclude_session_id: Optional[str] = None) -> int:
        try:
            sessions = await self.get_user_sessions(user_id)
            deleted = 0
            for session in sessions:
                if exclude_session_id and session.get("id") == exclude_session_id:
                    continue
                await self.delete_session(session["id"])
                deleted += 1
            return deleted
        except Exception as e:
            logger.error(f"❌ Failed to delete user sessions for {user_id}: {str(e)}")
            return 0
    
    # ==================== MEDICATION METHODS ====================
    
    async def save_medication(self, medication_data: Dict[str, Any]) -> str:
        try:
            if "medications" not in self.containers:
                return ""
            if "id" not in medication_data:
                medication_data["id"] = str(uuid.uuid4())
            medication_data["created_at"] = datetime.utcnow().isoformat()
            medication_data["updated_at"] = medication_data["created_at"]
            medication_data["_ts"] = datetime.utcnow().timestamp()
            self.containers["medications"].upsert_item(medication_data)
            return medication_data["id"]
        except Exception as e:
            logger.error(f"❌ Failed to save medication: {str(e)}")
            return ""
    
    async def get_medication(self, medication_id: str) -> Optional[Dict[str, Any]]:
        try:
            if "medications" not in self.containers:
                return None
            query = "SELECT * FROM c WHERE c.id = @id"
            parameters = [{"name": "@id", "value": medication_id}]
            items = list(self.containers["medications"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return dict(items[0]) if items else None
        except Exception as e:
            logger.error(f"❌ Failed to get medication {medication_id}: {str(e)}")
            return None
    
    async def get_user_medications(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            if "medications" not in self.containers:
                return []
            query = "SELECT * FROM c WHERE c.user_id = @user_id"
            parameters = [{"name": "@user_id", "value": user_id}]
            items = list(self.containers["medications"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return [dict(item) for item in items]
        except Exception as e:
            logger.error(f"❌ Failed to get medications for user {user_id}: {str(e)}")
            return []
    
    async def update_medication(self, medication_id: str, updates: Dict[str, Any]) -> bool:
        try:
            medication = await self.get_medication(medication_id)
            if not medication:
                return False
            medication.update(updates)
            medication["updated_at"] = datetime.utcnow().isoformat()
            medication["_ts"] = datetime.utcnow().timestamp()
            self.containers["medications"].upsert_item(medication)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update medication {medication_id}: {str(e)}")
            return False
    
    async def delete_medication(self, medication_id: str) -> bool:
        try:
            medication = await self.get_medication(medication_id)
            if not medication:
                return False
            self.containers["medications"].delete_item(
                item=medication_id, partition_key=medication.get("user_id", "")
            )
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete medication {medication_id}: {str(e)}")
            return False
    
    # ==================== EMERGENCY METHODS ====================
    
    async def save_emergency(self, emergency_data: Dict[str, Any]) -> str:
        try:
            if "emergencies" not in self.containers:
                return ""
            if "id" not in emergency_data:
                emergency_data["id"] = str(uuid.uuid4())
            emergency_data["created_at"] = datetime.utcnow().isoformat()
            emergency_data["_ts"] = datetime.utcnow().timestamp()
            self.containers["emergencies"].upsert_item(emergency_data)
            return emergency_data["id"]
        except Exception as e:
            logger.error(f"❌ Failed to save emergency: {str(e)}")
            return ""
    
    async def get_emergency(self, emergency_id: str) -> Optional[Dict[str, Any]]:
        try:
            if "emergencies" not in self.containers:
                return None
            query = "SELECT * FROM c WHERE c.id = @id"
            parameters = [{"name": "@id", "value": emergency_id}]
            items = list(self.containers["emergencies"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return dict(items[0]) if items else None
        except Exception as e:
            logger.error(f"❌ Failed to get emergency {emergency_id}: {str(e)}")
            return None
    
    async def get_user_emergencies(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            if "emergencies" not in self.containers:
                return []
            query = "SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c._ts DESC OFFSET 0 LIMIT @limit"
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@limit", "value": limit}
            ]
            items = list(self.containers["emergencies"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return [dict(item) for item in items]
        except Exception as e:
            logger.error(f"❌ Failed to get emergencies for user {user_id}: {str(e)}")
            return []
    
    async def update_emergency(self, emergency_id: str, updates: Dict[str, Any]) -> bool:
        try:
            emergency = await self.get_emergency(emergency_id)
            if not emergency:
                return False
            emergency.update(updates)
            emergency["_ts"] = datetime.utcnow().timestamp()
            self.containers["emergencies"].upsert_item(emergency)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update emergency {emergency_id}: {str(e)}")
            return False
    
    async def get_active_emergencies(self) -> List[Dict[str, Any]]:
        try:
            if "emergencies" not in self.containers:
                return []
            query = "SELECT * FROM c WHERE c.status = 'ACTIVE'"
            items = list(self.containers["emergencies"].query_items(
                query=query, enable_cross_partition_query=True
            ))
            return [dict(item) for item in items]
        except Exception as e:
            logger.error(f"❌ Failed to get active emergencies: {str(e)}")
            return []
    
    # ==================== EMERGENCY CONTACT METHODS ====================
    
    async def save_emergency_contact(self, contact_data: Dict[str, Any]) -> str:
        try:
            if "emergency_contacts" not in self.containers:
                return ""
            if "id" not in contact_data:
                contact_data["id"] = str(uuid.uuid4())
            contact_data["created_at"] = datetime.utcnow().isoformat()
            contact_data["_ts"] = datetime.utcnow().timestamp()
            self.containers["emergency_contacts"].upsert_item(contact_data)
            return contact_data["id"]
        except Exception as e:
            logger.error(f"❌ Failed to save emergency contact: {str(e)}")
            return ""
    
    async def get_emergency_contacts(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            if "emergency_contacts" not in self.containers:
                return []
            query = "SELECT * FROM c WHERE c.user_id = @user_id"
            parameters = [{"name": "@user_id", "value": user_id}]
            items = list(self.containers["emergency_contacts"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return [dict(item) for item in items]
        except Exception as e:
            logger.error(f"❌ Failed to get emergency contacts for user {user_id}: {str(e)}")
            return []
    
    async def get_emergency_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        try:
            if "emergency_contacts" not in self.containers:
                return None
            query = "SELECT * FROM c WHERE c.id = @id"
            parameters = [{"name": "@id", "value": contact_id}]
            items = list(self.containers["emergency_contacts"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return dict(items[0]) if items else None
        except Exception as e:
            logger.error(f"❌ Failed to get emergency contact {contact_id}: {str(e)}")
            return None
    
    async def update_emergency_contact(self, contact_id: str, updates: Dict[str, Any]) -> bool:
        try:
            contact = await self.get_emergency_contact(contact_id)
            if not contact:
                return False
            contact.update(updates)
            contact["updated_at"] = datetime.utcnow().isoformat()
            contact["_ts"] = datetime.utcnow().timestamp()
            self.containers["emergency_contacts"].upsert_item(contact)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update emergency contact {contact_id}: {str(e)}")
            return False
    
    async def delete_emergency_contact(self, contact_id: str) -> bool:
        try:
            contact = await self.get_emergency_contact(contact_id)
            if not contact:
                return False
            self.containers["emergency_contacts"].delete_item(
                item=contact_id, partition_key=contact.get("user_id", "")
            )
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete emergency contact {contact_id}: {str(e)}")
            return False
    
    # ==================== NOTIFICATION METHODS ====================
    
    async def save_notification(self, notification_data: Dict[str, Any]) -> str:
        try:
            if "notifications" not in self.containers:
                return ""
            if "id" not in notification_data:
                notification_data["id"] = str(uuid.uuid4())
            notification_data["created_at"] = datetime.utcnow().isoformat()
            notification_data["read"] = False
            notification_data["_ts"] = datetime.utcnow().timestamp()
            self.containers["notifications"].upsert_item(notification_data)
            return notification_data["id"]
        except Exception as e:
            logger.error(f"❌ Failed to save notification: {str(e)}")
            return ""
    
    async def get_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
        try:
            if "notifications" not in self.containers:
                return None
            query = "SELECT * FROM c WHERE c.id = @id"
            parameters = [{"name": "@id", "value": notification_id}]
            items = list(self.containers["notifications"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return dict(items[0]) if items else None
        except Exception as e:
            logger.error(f"❌ Failed to get notification {notification_id}: {str(e)}")
            return None
    
    async def get_user_notifications(self, user_id: str, unread_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            if "notifications" not in self.containers:
                return []
            if unread_only:
                query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.read = false ORDER BY c._ts DESC OFFSET 0 LIMIT @limit"
            else:
                query = "SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c._ts DESC OFFSET 0 LIMIT @limit"
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@limit", "value": limit}
            ]
            items = list(self.containers["notifications"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return [dict(item) for item in items]
        except Exception as e:
            logger.error(f"❌ Failed to get notifications for user {user_id}: {str(e)}")
            return []
    
    async def mark_notification_read(self, notification_id: str) -> bool:
        try:
            notification = await self.get_notification(notification_id)
            if not notification:
                return False
            notification["read"] = True
            notification["read_at"] = datetime.utcnow().isoformat()
            notification["_ts"] = datetime.utcnow().timestamp()
            self.containers["notifications"].upsert_item(notification)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to mark notification {notification_id} as read: {str(e)}")
            return False
    
    async def mark_all_notifications_read(self, user_id: str) -> int:
        try:
            notifications = await self.get_user_notifications(user_id, unread_only=True)
            marked = 0
            for notification in notifications:
                if await self.mark_notification_read(notification["id"]):
                    marked += 1
            return marked
        except Exception as e:
            logger.error(f"❌ Failed to mark all notifications read for user {user_id}: {str(e)}")
            return 0
    
    async def delete_notification(self, notification_id: str) -> bool:
        try:
            notification = await self.get_notification(notification_id)
            if not notification:
                return False
            self.containers["notifications"].delete_item(
                item=notification_id, partition_key=notification.get("user_id", "")
            )
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete notification {notification_id}: {str(e)}")
            return False
    
    async def get_unread_count(self, user_id: str) -> int:
        try:
            notifications = await self.get_user_notifications(user_id, unread_only=True)
            return len(notifications)
        except Exception as e:
            logger.error(f"❌ Failed to get unread count for user {user_id}: {str(e)}")
            return 0
    
    # ==================== WELLNESS METHODS ====================
    
    async def save_wellness_entry(self, entry_data: Dict[str, Any]) -> str:
        try:
            if "wellness" not in self.containers:
                return ""
            if "id" not in entry_data:
                entry_data["id"] = str(uuid.uuid4())
            entry_data["timestamp"] = entry_data.get("timestamp", datetime.utcnow().isoformat())
            entry_data["_ts"] = datetime.utcnow().timestamp()
            self.containers["wellness"].upsert_item(entry_data)
            return entry_data["id"]
        except Exception as e:
            logger.error(f"❌ Failed to save wellness entry: {str(e)}")
            return ""
    
    async def get_wellness_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        try:
            if "wellness" not in self.containers:
                return None
            query = "SELECT * FROM c WHERE c.id = @id"
            parameters = [{"name": "@id", "value": entry_id}]
            items = list(self.containers["wellness"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return dict(items[0]) if items else None
        except Exception as e:
            logger.error(f"❌ Failed to get wellness entry {entry_id}: {str(e)}")
            return None
    
    async def get_user_wellness_entries(self, user_id: str, entry_type: Optional[str] = None, days: int = 30) -> List[Dict[str, Any]]:
        try:
            if "wellness" not in self.containers:
                return []
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            if entry_type:
                query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.type = @type AND c.timestamp >= @cutoff ORDER BY c.timestamp DESC"
                parameters = [
                    {"name": "@user_id", "value": user_id},
                    {"name": "@type", "value": entry_type},
                    {"name": "@cutoff", "value": cutoff}
                ]
            else:
                query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.timestamp >= @cutoff ORDER BY c.timestamp DESC"
                parameters = [
                    {"name": "@user_id", "value": user_id},
                    {"name": "@cutoff", "value": cutoff}
                ]
            items = list(self.containers["wellness"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return [dict(item) for item in items]
        except Exception as e:
            logger.error(f"❌ Failed to get wellness entries for user {user_id}: {str(e)}")
            return []
    
    # ==================== SCAM REPORT METHODS ====================
    
    async def save_scam_report(self, report_data: Dict[str, Any]) -> str:
        try:
            if "scam_reports" not in self.containers:
                return ""
            if "id" not in report_data:
                report_data["id"] = str(uuid.uuid4())
            report_data["timestamp"] = report_data.get("timestamp", datetime.utcnow().isoformat())
            report_data["_ts"] = datetime.utcnow().timestamp()
            self.containers["scam_reports"].upsert_item(report_data)
            return report_data["id"]
        except Exception as e:
            logger.error(f"❌ Failed to save scam report: {str(e)}")
            return ""
    
    async def get_scam_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        try:
            if "scam_reports" not in self.containers:
                return None
            query = "SELECT * FROM c WHERE c.id = @id"
            parameters = [{"name": "@id", "value": report_id}]
            items = list(self.containers["scam_reports"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return dict(items[0]) if items else None
        except Exception as e:
            logger.error(f"❌ Failed to get scam report {report_id}: {str(e)}")
            return None
    
    async def get_user_scam_reports(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            if "scam_reports" not in self.containers:
                return []
            query = "SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c.timestamp DESC"
            parameters = [{"name": "@user_id", "value": user_id}]
            items = list(self.containers["scam_reports"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return [dict(item) for item in items]
        except Exception as e:
            logger.error(f"❌ Failed to get scam reports for user {user_id}: {str(e)}")
            return []
    
    # ==================== CHAT METHODS ====================
    
    async def save_chat_session(self, session_data: Dict[str, Any]) -> str:
        try:
            if "chat_sessions" not in self.containers:
                return ""
            if "id" not in session_data:
                session_data["id"] = str(uuid.uuid4())
            session_data["created_at"] = datetime.utcnow().isoformat()
            session_data["updated_at"] = session_data["created_at"]
            session_data["_ts"] = datetime.utcnow().timestamp()
            self.containers["chat_sessions"].upsert_item(session_data)
            return session_data["id"]
        except Exception as e:
            logger.error(f"❌ Failed to save chat session: {str(e)}")
            return ""
    
    async def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            if "chat_sessions" not in self.containers:
                return None
            query = "SELECT * FROM c WHERE c.id = @id"
            parameters = [{"name": "@id", "value": session_id}]
            items = list(self.containers["chat_sessions"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return dict(items[0]) if items else None
        except Exception as e:
            logger.error(f"❌ Failed to get chat session {session_id}: {str(e)}")
            return None
    
    async def get_user_chat_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            if "chat_sessions" not in self.containers:
                return []
            query = "SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c._ts DESC"
            parameters = [{"name": "@user_id", "value": user_id}]
            items = list(self.containers["chat_sessions"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return [dict(item) for item in items]
        except Exception as e:
            logger.error(f"❌ Failed to get chat sessions for user {user_id}: {str(e)}")
            return []
    
    async def save_chat_message(self, message_data: Dict[str, Any]) -> str:
        try:
            if "chat_messages" not in self.containers:
                return ""
            if "id" not in message_data:
                message_data["id"] = str(uuid.uuid4())
            message_data["timestamp"] = message_data.get("timestamp", datetime.utcnow().isoformat())
            message_data["_ts"] = datetime.utcnow().timestamp()
            self.containers["chat_messages"].upsert_item(message_data)
            return message_data["id"]
        except Exception as e:
            logger.error(f"❌ Failed to save chat message: {str(e)}")
            return ""
    
    async def get_chat_messages(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            if "chat_messages" not in self.containers:
                return []
            query = "SELECT * FROM c WHERE c.session_id = @session_id ORDER BY c.timestamp ASC OFFSET 0 LIMIT @limit"
            parameters = [
                {"name": "@session_id", "value": session_id},
                {"name": "@limit", "value": limit}
            ]
            items = list(self.containers["chat_messages"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return [dict(item) for item in items]
        except Exception as e:
            logger.error(f"❌ Failed to get chat messages for session {session_id}: {str(e)}")
            return []
    
    # ==================== ANALYTICS METHODS ====================
    
    async def save_analytics_event(self, event_data: Dict[str, Any]) -> str:
        try:
            if "analytics_events" not in self.containers:
                return ""
            if "id" not in event_data:
                event_data["id"] = str(uuid.uuid4())
            event_data["timestamp"] = event_data.get("timestamp", datetime.utcnow().isoformat())
            event_data["_ts"] = datetime.utcnow().timestamp()
            self.containers["analytics_events"].upsert_item(event_data)
            return event_data["id"]
        except Exception as e:
            logger.error(f"❌ Failed to save analytics event: {str(e)}")
            return ""
    
    async def get_user_analytics(self, user_id: str, event_type: Optional[str] = None, days: int = 30) -> List[Dict[str, Any]]:
        try:
            if "analytics_events" not in self.containers:
                return []
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            if event_type:
                query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.event_type = @event_type AND c.timestamp >= @cutoff ORDER BY c.timestamp DESC"
                parameters = [
                    {"name": "@user_id", "value": user_id},
                    {"name": "@event_type", "value": event_type},
                    {"name": "@cutoff", "value": cutoff}
                ]
            else:
                query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.timestamp >= @cutoff ORDER BY c.timestamp DESC"
                parameters = [
                    {"name": "@user_id", "value": user_id},
                    {"name": "@cutoff", "value": cutoff}
                ]
            items = list(self.containers["analytics_events"].query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            ))
            return [dict(item) for item in items]
        except Exception as e:
            logger.error(f"❌ Failed to get analytics for user {user_id}: {str(e)}")
            return []
    
    # ==================== HEALTH CHECK ====================
    
    async def health_check(self) -> bool:
        try:
            if self.database:
                list(self.database.list_containers(max_item_count=1))
                return True
            return self.is_healthy
        except Exception as e:
            logger.error(f"Cosmos DB health check failed: {e}")
            return self.is_healthy
    
    # ==================== ALIAS METHODS ====================
    # These fix 'object has no attribute' errors from agents
    # calling differently-named methods
    
    async def get_wellness_entries(
        self,
        user_id: str,
        entry_type: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Alias for get_user_wellness_entries"""
        return await self.get_user_wellness_entries(
            user_id=user_id, entry_type=entry_type, days=days
        )
    
    async def get_adherence_records(
        self,
        user_id: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Alias — returns medication records for adherence calculation"""
        try:
            return await self.get_user_medications(user_id=user_id)
        except Exception as e:
            logger.error(f"get_adherence_records failed: {e}")
            return []
    
    async def save_wellness_data(
        self,
        user_id: str,
        data: Dict[str, Any]
    ) -> str:
        """Alias for save_wellness_entry"""
        entry = {"user_id": user_id, **data}
        return await self.save_wellness_entry(entry)
    
    async def get_medications(self, user_id: str) -> List[Dict[str, Any]]:
        """Alias for get_user_medications"""
        return await self.get_user_medications(user_id=user_id)
    
    async def get_emergencies(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Alias for get_user_emergencies"""
        return await self.get_user_emergencies(user_id=user_id, limit=limit)
    
    async def get_scam_reports(self, user_id: str) -> List[Dict[str, Any]]:
        """Alias for get_user_scam_reports"""
        return await self.get_user_scam_reports(user_id=user_id)
    
    async def get_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Alias for get_user_notifications"""
        return await self.get_user_notifications(
            user_id=user_id, unread_only=unread_only, limit=limit
        )
    
    # ==================== CLOSE ====================
    
    async def close(self):
        """Close database connection"""
        logger.info("CosmosService closed")