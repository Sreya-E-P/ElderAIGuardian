"""
Authentication Routes
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.logging import logger
from app.core.config import settings
from app.services.auth.auth_service import AuthService, get_auth_service
from app.models.schemas import User, UserCreate, UserLogin, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user"""
    try:
        result = await auth_service.register(user_data)
        return TokenResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user"""
    try:
        result = await auth_service.login(credentials.email, credentials.password)
        return TokenResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token"""
    try:
        result = await auth_service.refresh_token(refresh_token)
        return TokenResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

@router.post("/logout")
async def logout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout user"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token:
        await auth_service.logout(token)
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=User)
async def get_current_user(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current user information"""
    # Safely get user_id from request.state
    user_id = getattr(request.state, "user_id", None)
    
    # For development, return a mock user if no user_id
    if settings.APP_ENV == "development" and not user_id:
        return User(
            id="dev_user",
            email="dev@example.com",
            first_name="Dev",
            last_name="User",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await auth_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.post("/change-password")
async def change_password(
    request: Request,
    old_password: str,
    new_password: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change user password"""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        await auth_service.change_password(user_id, old_password, new_password)
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Password change failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Password change failed")

@router.post("/reset-password-request")
async def request_password_reset(
    email: EmailStr,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Request password reset"""
    try:
        await auth_service.request_password_reset(email)
        return {"message": "Password reset email sent if account exists"}
    except Exception as e:
        logger.error(f"Password reset request failed: {str(e)}")
        # Always return success to prevent email enumeration
        return {"message": "Password reset email sent if account exists"}

@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Reset password with token"""
    try:
        await auth_service.reset_password(token, new_password)
        return {"message": "Password reset successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Password reset failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Password reset failed")

@router.post("/verify-email")
async def verify_email(
    token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Verify email address"""
    try:
        await auth_service.verify_email(token)
        return {"message": "Email verified successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Email verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Email verification failed")

@router.post("/resend-verification")
async def resend_verification(
    email: EmailStr,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Resend verification email"""
    try:
        await auth_service.resend_verification(email)
        return {"message": "Verification email sent"}
    except Exception as e:
        logger.error(f"Resend verification failed: {str(e)}")
        return {"message": "Verification email sent if account exists"}

@router.get("/sessions")
async def get_active_sessions(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get active sessions for user"""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    sessions = await auth_service.get_active_sessions(user_id)
    return {"sessions": sessions}

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Revoke a specific session"""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    await auth_service.revoke_session(user_id, session_id)
    return {"message": "Session revoked successfully"}

@router.delete("/sessions")
async def revoke_all_sessions(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Revoke all sessions except current"""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    current_token = request.headers.get("Authorization", "").replace("Bearer ", "")
    await auth_service.revoke_all_sessions(user_id, current_token)
    return {"message": "All other sessions revoked successfully"}