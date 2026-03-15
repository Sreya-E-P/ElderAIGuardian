"""
Authentication Service with JWT and Refresh Tokens
Uses DatabaseService interface for database operations
"""

import jwt
import bcrypt
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.logging import logger
from app.services.database.base import DatabaseService
from app.services.cache.cache_service import CacheService
from app.models.schemas import User, UserCreate, UserInDB

security = HTTPBearer()


class AuthService:
    """Authentication service with JWT tokens"""
    
    def __init__(
        self,
        db_service: DatabaseService,  # Uses the interface
        cache_service: CacheService,
        secret_key: str
    ):
        self.db = db_service
        self.cache = cache_service
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = getattr(settings, 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 30)
        self.refresh_token_expire_days = getattr(settings, 'JWT_REFRESH_TOKEN_EXPIRE_DAYS', 7)
    
    async def initialize(self):
        """Initialize auth service"""
        logger.info("✅ AuthService initialized")
    
    async def register(self, user_data: UserCreate) -> Dict[str, Any]:
        """Register a new user"""
        # Check if user exists
        existing = await self.db.get_user_by_email(user_data.email)
        if existing:
            raise ValueError("User with this email already exists")
        
        # Hash password
        hashed_password = self._hash_password(user_data.password)
        
        # Create user object
        user_dict = user_data.dict()
        user_dict.pop("password")
        user_dict["hashed_password"] = hashed_password
        
        # Save to database
        user_id = await self.db.create_user(user_dict)
        
        # Get created user
        user_data = await self.db.get_user(user_id)
        user = User(**user_data)
        
        # Generate tokens
        tokens = await self._create_tokens(user_id)
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
            "user": user.dict()
        }
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login user"""
        # Get user
        user_data = await self.db.get_user_by_email(email)
        
        if not user_data:
            raise ValueError("Invalid email or password")
        
        # Check password
        if not self._verify_password(password, user_data["hashed_password"]):
            raise ValueError("Invalid email or password")
        
        # Update last login
        now = datetime.utcnow().isoformat()
        await self.db.update_user(user_data["id"], {"last_login": now})
        
        # Create user object
        user = User(**user_data)
        
        # Generate tokens
        tokens = await self._create_tokens(user_data["id"])
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
            "user": user.dict()
        }
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = jwt.decode(
                refresh_token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            user_id = payload.get("sub")
            token_type = payload.get("type")
            
            if not user_id or token_type != "refresh":
                raise ValueError("Invalid refresh token")
            
            # Check if token is blacklisted
            if await self.cache.get(f"blacklist:{refresh_token}"):
                raise ValueError("Token has been revoked")
            
            # Get user
            user_data = await self.db.get_user(user_id)
            if not user_data:
                raise ValueError("User not found")
            
            # Create user object
            user = User(**user_data)
            
            # Generate new tokens
            tokens = await self._create_tokens(user_id)
            
            # Blacklist old refresh token
            await self.cache.set(
                f"blacklist:{refresh_token}",
                True,
                ttl=self.refresh_token_expire_days * 24 * 3600
            )
            
            return {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60,
                "user": user.dict()
            }
            
        except jwt.PyJWTError:
            raise ValueError("Invalid refresh token")
    
    async def logout(self, token: str):
        """Logout user by blacklisting token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            exp = payload.get("exp")
            if exp:
                ttl = exp - datetime.utcnow().timestamp()
                if ttl > 0:
                    await self.cache.set(
                        f"blacklist:{token}",
                        True,
                        ttl=int(ttl)
                    )
        except:
            pass
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        user_data = await self.db.get_user(user_id)
        if not user_data:
            return None
        
        return User(**user_data)
    
    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ):
        """Change user password"""
        # Get user
        user_data = await self.db.get_user(user_id)
        if not user_data:
            raise ValueError("User not found")
        
        # Verify old password
        if not self._verify_password(old_password, user_data["hashed_password"]):
            raise ValueError("Invalid current password")
        
        # Hash new password
        hashed_password = self._hash_password(new_password)
        
        # Update password
        await self.db.update_user(user_id, {"hashed_password": hashed_password})
    
    async def request_password_reset(self, email: str):
        """Request password reset"""
        user = await self.db.get_user_by_email(email)
        
        if user:
            # Generate reset token
            token = str(uuid.uuid4())
            
            await self.cache.set(
                f"reset:{token}",
                user["id"],
                ttl=24 * 3600
            )
            
            logger.info(f"Password reset requested for {email}")
    
    async def reset_password(self, token: str, new_password: str):
        """Reset password with token"""
        user_id = await self.cache.get(f"reset:{token}")
        if not user_id:
            raise ValueError("Invalid or expired reset token")
        
        # Hash new password
        hashed_password = self._hash_password(new_password)
        
        # Update password
        await self.db.update_user(user_id, {"hashed_password": hashed_password})
        
        # Delete reset token
        await self.cache.delete(f"reset:{token}")
        
        # Delete all sessions for security
        await self.db.delete_user_sessions(user_id)
    
    async def verify_email(self, token: str):
        """Verify email with token"""
        user_id = await self.cache.get(f"verify:{token}")
        if not user_id:
            raise ValueError("Invalid or expired verification token")
        
        await self.db.update_user(user_id, {"is_verified": True})
        await self.cache.delete(f"verify:{token}")
    
    async def resend_verification(self, email: str):
        """Resend verification email"""
        user = await self.db.get_user_by_email(email)
        
        if user:
            # Generate new verification token
            token = str(uuid.uuid4())
            
            await self.cache.set(
                f"verify:{token}",
                user["id"],
                ttl=7 * 24 * 3600
            )
            
            logger.info(f"Verification email resent to {email}")
    
    async def get_active_sessions(self, user_id: str) -> List[Dict]:
        """Get active sessions for user"""
        sessions = await self.db.get_user_sessions(user_id)
        return sessions
    
    async def revoke_session(self, user_id: str, session_id: str):
        """Revoke a specific session"""
        await self.db.delete_session(session_id)
    
    async def revoke_all_sessions(self, user_id: str, current_token: str):
        """Revoke all sessions except current"""
        # Get current session ID from token
        try:
            payload = jwt.decode(
                current_token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            current_session_id = payload.get("session_id")
        except:
            current_session_id = None
        
        await self.db.delete_user_sessions(user_id, current_session_id)
    
    async def verify_token(self, token: str) -> Optional[str]:
        """Verify token and return user ID"""
        try:
            # Check if token is blacklisted
            if await self.cache.get(f"blacklist:{token}"):
                return None
            
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            user_id = payload.get("sub")
            token_type = payload.get("type")
            
            if token_type != "access":
                return None
            
            return user_id
            
        except jwt.PyJWTError:
            return None
    
    async def _create_tokens(self, user_id: str) -> Dict[str, str]:
        """Create access and refresh tokens"""
        now = datetime.utcnow()
        session_id = str(uuid.uuid4())
        
        # Access token
        access_token = jwt.encode(
            {
                "sub": user_id,
                "session_id": session_id,
                "type": "access",
                "iat": now,
                "exp": now + timedelta(minutes=self.access_token_expire_minutes)
            },
            self.secret_key,
            algorithm=self.algorithm
        )
        
        # Refresh token
        refresh_token = jwt.encode(
            {
                "sub": user_id,
                "type": "refresh",
                "iat": now,
                "exp": now + timedelta(days=self.refresh_token_expire_days)
            },
            self.secret_key,
            algorithm=self.algorithm
        )
        
        # Store session
        session_data = {
            "id": session_id,
            "user_id": user_id,
            "token": access_token,
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=self.access_token_expire_minutes)).isoformat(),
            "ip_address": None,
            "user_agent": None
        }
        await self.db.save_session(session_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode(), hashed.encode())


# ============================================================================
# DEPENDENCIES
# ============================================================================

async def get_auth_service(
    db_service = None,
    cache_service = None
):
    """Get auth service instance"""
    from app.main import cosmos_service, cache_service as main_cache_service
    
    db = db_service or cosmos_service
    cache = cache_service or main_cache_service
    
    if not db or not cache:
        raise HTTPException(status_code=503, detail="Auth service dependencies not available")
    
    return AuthService(db, cache, settings.SECRET_KEY)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service = Depends(get_auth_service)
):
    """Get current authenticated user"""
    token = credentials.credentials
    user_id = await auth_service.verify_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await auth_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user