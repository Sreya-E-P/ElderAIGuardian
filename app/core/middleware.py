"""
Custom Middleware for FastAPI
"""

import time
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict
import hashlib

from app.core.logging import logger
from app.core.config import settings

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Generate request ID
        request_id = hashlib.md5(f"{request.url.path}{time.time()}".encode()).hexdigest()[:8]
        
        # Log request
        logger.info(f"Request {request_id}: {request.method} {request.url.path}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log response
            process_time = (time.time() - start_time) * 1000
            logger.info(f"Response {request_id}: {response.status_code} - {process_time:.2f}ms")
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-MS"] = str(int(process_time))
            
            return response
            
        except Exception as e:
            logger.error(f"Request {request_id} failed: {str(e)}")
            raise

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for certain paths
        if request.url.path in ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        
        # Clean old requests
        now = time.time()
        if client_ip in self.requests:
            self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < 60]
        else:
            self.requests[client_ip] = []
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Add request
        self.requests[client_ip].append(now)
        
        return await call_next(request)

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public paths
        public_paths = ["/", "/health", "/docs", "/redoc", "/openapi.json", "/api/auth/login", "/api/auth/register"]
        
        if request.url.path in public_paths:
            return await call_next(request)
        
        # Check for API key in headers
        api_key = request.headers.get("X-API-Key")
        
        if api_key and api_key == settings.API_KEY:
            # Valid API key
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            
            # In production, validate JWT token
            # For now, just pass through
            request.state.user_id = "test_user"
            return await call_next(request)
        
        # No authentication
        # For development, allow all requests
        if settings.APP_ENV == "development":
            request.state.user_id = "dev_user"
            return await call_next(request)
        
        raise HTTPException(status_code=401, detail="Authentication required")

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for error handling"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unhandled error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")