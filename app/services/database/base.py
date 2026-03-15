"""
Base database interface for services
All database services must implement this interface
"""

from typing import Optional, List, Dict, Any, Union
from abc import ABC, abstractmethod


class DatabaseService(ABC):
    """Abstract base class for database services"""
    
    # ==================== User Methods ====================
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user"""
        pass
    
    @abstractmethod
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user"""
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        pass
    
    @abstractmethod
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all users (admin only)"""
        pass
    
    # ==================== Session Methods ====================
    
    @abstractmethod
    async def save_session(self, session_data: Dict[str, Any]) -> str:
        """Save a session"""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        pass
    
    @abstractmethod
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user"""
        pass
    
    @abstractmethod
    async def delete_user_sessions(self, user_id: str, exclude_session_id: Optional[str] = None) -> int:
        """Delete all sessions for a user"""
        pass
    
    # ==================== Medication Methods ====================
    
    @abstractmethod
    async def save_medication(self, medication_data: Dict[str, Any]) -> str:
        """Save a medication"""
        pass
    
    @abstractmethod
    async def get_medication(self, medication_id: str) -> Optional[Dict[str, Any]]:
        """Get a medication by ID"""
        pass
    
    @abstractmethod
    async def get_user_medications(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all medications for a user"""
        pass
    
    @abstractmethod
    async def update_medication(self, medication_id: str, updates: Dict[str, Any]) -> bool:
        """Update a medication"""
        pass
    
    @abstractmethod
    async def delete_medication(self, medication_id: str) -> bool:
        """Delete a medication"""
        pass
    
    # ==================== Emergency Methods ====================
    
    @abstractmethod
    async def save_emergency(self, emergency_data: Dict[str, Any]) -> str:
        """Save an emergency"""
        pass
    
    @abstractmethod
    async def get_emergency(self, emergency_id: str) -> Optional[Dict[str, Any]]:
        """Get an emergency by ID"""
        pass
    
    @abstractmethod
    async def get_user_emergencies(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get emergencies for a user"""
        pass
    
    @abstractmethod
    async def update_emergency(self, emergency_id: str, updates: Dict[str, Any]) -> bool:
        """Update an emergency"""
        pass
    
    @abstractmethod
    async def get_active_emergencies(self) -> List[Dict[str, Any]]:
        """Get all active emergencies"""
        pass
    
    # ==================== Emergency Contact Methods ====================
    
    @abstractmethod
    async def save_emergency_contact(self, contact_data: Dict[str, Any]) -> str:
        """Save an emergency contact"""
        pass
    
    @abstractmethod
    async def get_emergency_contacts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get emergency contacts for a user"""
        pass
    
    @abstractmethod
    async def get_emergency_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Get an emergency contact by ID"""
        pass
    
    @abstractmethod
    async def update_emergency_contact(self, contact_id: str, updates: Dict[str, Any]) -> bool:
        """Update an emergency contact"""
        pass
    
    @abstractmethod
    async def delete_emergency_contact(self, contact_id: str) -> bool:
        """Delete an emergency contact"""
        pass
    
    # ==================== Notification Methods ====================
    
    @abstractmethod
    async def save_notification(self, notification_data: Dict[str, Any]) -> str:
        """Save a notification"""
        pass
    
    @abstractmethod
    async def get_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Get a notification by ID"""
        pass
    
    @abstractmethod
    async def get_user_notifications(self, user_id: str, unread_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        pass
    
    @abstractmethod
    async def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read"""
        pass
    
    @abstractmethod
    async def mark_all_notifications_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        pass
    
    @abstractmethod
    async def delete_notification(self, notification_id: str) -> bool:
        """Delete a notification"""
        pass
    
    @abstractmethod
    async def get_unread_count(self, user_id: str) -> int:
        """Get unread notification count for a user"""
        pass
    
    # ==================== Wellness Methods ====================
    
    @abstractmethod
    async def save_wellness_entry(self, entry_data: Dict[str, Any]) -> str:
        """Save a wellness entry"""
        pass
    
    @abstractmethod
    async def get_wellness_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get a wellness entry by ID"""
        pass
    
    @abstractmethod
    async def get_user_wellness_entries(self, user_id: str, entry_type: Optional[str] = None, days: int = 30) -> List[Dict[str, Any]]:
        """Get wellness entries for a user"""
        pass
    
    # ==================== Scam Report Methods ====================
    
    @abstractmethod
    async def save_scam_report(self, report_data: Dict[str, Any]) -> str:
        """Save a scam report"""
        pass
    
    @abstractmethod
    async def get_scam_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get a scam report by ID"""
        pass
    
    @abstractmethod
    async def get_user_scam_reports(self, user_id: str) -> List[Dict[str, Any]]:
        """Get scam reports for a user"""
        pass
    
    # ==================== Chat Methods ====================
    
    @abstractmethod
    async def save_chat_session(self, session_data: Dict[str, Any]) -> str:
        """Save a chat session"""
        pass
    
    @abstractmethod
    async def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a chat session by ID"""
        pass
    
    @abstractmethod
    async def get_user_chat_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get chat sessions for a user"""
        pass
    
    @abstractmethod
    async def save_chat_message(self, message_data: Dict[str, Any]) -> str:
        """Save a chat message"""
        pass
    
    @abstractmethod
    async def get_chat_messages(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat messages for a session"""
        pass
    
    # ==================== Analytics Methods ====================
    
    @abstractmethod
    async def save_analytics_event(self, event_data: Dict[str, Any]) -> str:
        """Save an analytics event"""
        pass
    
    @abstractmethod
    async def get_user_analytics(self, user_id: str, event_type: Optional[str] = None, days: int = 30) -> List[Dict[str, Any]]:
        """Get analytics for a user"""
        pass
    
    # ==================== Health Check ====================
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if database is healthy"""
        pass
    
    @abstractmethod
    async def close(self):
        """Close database connection"""
        pass