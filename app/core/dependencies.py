"""
Dependencies for FastAPI
"""

from fastapi import Request, HTTPException, Depends
from app.core.config import settings

async def get_orchestrator(request: Request):
    """Get orchestrator from app state"""
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    return orchestrator

async def get_auth_user(request: Request):
    """Get authenticated user from request state"""
    user_id = getattr(request.state, "user_id", None)
    if not user_id and settings.APP_ENV != "development":
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Return mock user for development
    return type('User', (), {
        'id': user_id or 'dev_user',
        'email': 'dev@example.com',
        'name': 'Dev User'
    })