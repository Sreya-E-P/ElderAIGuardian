"""
Users Routes for managing user profiles and settings
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from app.core.logging import logger
from app.core.dependencies import get_orchestrator, get_auth_user
from app.models.schemas import User, UserCreate

router = APIRouter(prefix="/api/users", tags=["Users"])

class UserProfileUpdate(BaseModel):
    """User profile update model"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    emergency_contacts: Optional[List[Dict[str, Any]]] = None
    medical_conditions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None

class UserPreferences(BaseModel):
    """User preferences model"""
    theme: Optional[str] = "light"
    language: Optional[str] = "en"
    notifications_enabled: Optional[bool] = True
    email_notifications: Optional[bool] = True
    sms_notifications: Optional[bool] = True
    push_notifications: Optional[bool] = True
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
    medication_reminders: Optional[bool] = True
    wellness_reminders: Optional[bool] = True
    scam_alerts: Optional[bool] = True

class UserResponse(BaseModel):
    """User response model"""
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    emergency_contacts: List[Dict[str, Any]] = []
    medical_conditions: List[str] = []
    allergies: List[str] = []
    preferences: Dict[str, Any] = {}
    is_active: bool
    is_verified: bool
    role: str
    created_at: str
    updated_at: str
    last_login: Optional[str] = None

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    request: Request,
    user = Depends(get_auth_user)
):
    """Get current user profile"""
    return user

@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    request: Request,
    profile_update: UserProfileUpdate,
    user = Depends(get_auth_user),
    orchestrator = Depends(get_orchestrator)
):
    """Update current user profile"""
    
    auth_service = getattr(orchestrator, 'auth_service', None)
    
    if not auth_service:
        # Mock update for development
        updated_user = user.copy()
        update_dict = profile_update.dict(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(updated_user, key, value)
        updated_user.updated_at = datetime.utcnow().isoformat()
        return updated_user
    
    try:
        updated_user = await auth_service.update_user(user.id, profile_update.dict(exclude_unset=True))
        return updated_user
        
    except Exception as e:
        logger.error(f"Failed to update user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me/preferences", response_model=UserPreferences)
async def get_user_preferences(
    request: Request,
    user = Depends(get_auth_user),
    orchestrator = Depends(get_orchestrator)
):
    """Get user preferences"""
    
    auth_service = getattr(orchestrator, 'auth_service', None)
    
    if not auth_service:
        # Mock preferences for development
        return UserPreferences()
    
    try:
        preferences = await auth_service.get_user_preferences(user.id)
        return UserPreferences(**preferences)
        
    except Exception as e:
        logger.error(f"Failed to get user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/me/preferences", response_model=UserPreferences)
async def update_user_preferences(
    request: Request,
    preferences: UserPreferences,
    user = Depends(get_auth_user),
    orchestrator = Depends(get_orchestrator)
):
    """Update user preferences"""
    
    auth_service = getattr(orchestrator, 'auth_service', None)
    
    if not auth_service:
        # Mock update for development
        return preferences
    
    try:
        updated = await auth_service.update_user_preferences(user.id, preferences.dict())
        return UserPreferences(**updated)
        
    except Exception as e:
        logger.error(f"Failed to update user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(
    user_id: str,
    request: Request,
    orchestrator = Depends(get_orchestrator),
    current_user = Depends(get_auth_user)
):
    """Get user profile by ID (admin only)"""
    
    # Check if user is admin or same user
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this user")
    
    auth_service = getattr(orchestrator, 'auth_service', None)
    
    if not auth_service:
        # Mock response for development
        if user_id == "dev_user" or user_id == current_user.id:
            return current_user
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        user = await auth_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
        
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[UserResponse])
async def list_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    orchestrator = Depends(get_orchestrator),
    current_user = Depends(get_auth_user)
):
    """List all users (admin only)"""
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to list users")
    
    auth_service = getattr(orchestrator, 'auth_service', None)
    
    if not auth_service:
        # Mock list for development
        return [current_user]
    
    try:
        users = await auth_service.list_users(skip=skip, limit=limit)
        return users
        
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    orchestrator = Depends(get_orchestrator),
    current_user = Depends(get_auth_user)
):
    """Delete user account (admin or self only)"""
    
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")
    
    auth_service = getattr(orchestrator, 'auth_service', None)
    
    if not auth_service:
        # Mock delete for development
        return {"message": f"User {user_id} deleted successfully"}
    
    try:
        await auth_service.delete_user(user_id)
        return {"message": f"User {user_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    request: Request,
    orchestrator = Depends(get_orchestrator),
    current_user = Depends(get_auth_user)
):
    """Deactivate user account (admin only)"""
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to deactivate users")
    
    auth_service = getattr(orchestrator, 'auth_service', None)
    
    if not auth_service:
        # Mock deactivate for development
        return {"message": f"User {user_id} deactivated successfully"}
    
    try:
        await auth_service.deactivate_user(user_id)
        return {"message": f"User {user_id} deactivated successfully"}
        
    except Exception as e:
        logger.error(f"Failed to deactivate user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/activate")
async def activate_user(
    user_id: str,
    request: Request,
    orchestrator = Depends(get_orchestrator),
    current_user = Depends(get_auth_user)
):
    """Activate user account (admin only)"""
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to activate users")
    
    auth_service = getattr(orchestrator, 'auth_service', None)
    
    if not auth_service:
        # Mock activate for development
        return {"message": f"User {user_id} activated successfully"}
    
    try:
        await auth_service.activate_user(user_id)
        return {"message": f"User {user_id} activated successfully"}
        
    except Exception as e:
        logger.error(f"Failed to activate user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    request: Request,
    days: int = 7,
    orchestrator = Depends(get_orchestrator),
    current_user = Depends(get_auth_user)
):
    """Get user activity history (admin or self only)"""
    
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this user's activity")
    
    # This would typically come from analytics service
    # Mock response for development
    return {
        "user_id": user_id,
        "period_days": days,
        "activity": {
            "chats": 15,
            "medication_checks": 8,
            "scam_checks": 3,
            "emergency_alerts": 0,
            "wellness_entries": 5
        },
        "last_active": datetime.utcnow().isoformat()
    }