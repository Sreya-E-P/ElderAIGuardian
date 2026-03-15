"""
API Routes Package
"""

from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.scam import router as scam_router
from app.api.routes.medication import router as medication_router
from app.api.routes.emergency import router as emergency_router
from app.api.routes.notification import router as notification_router
from app.api.routes.wellness import router as wellness_router
from app.api.routes.users import router as user_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.azure import router as azure_router
from app.api.routes.websocket import router as websocket_router
from app.api.routes.family import router as family_router
from app.api.routes.devops import router as devops_router
from app.api.routes.admin import router as admin_router
from app.api.routes.hero import router as hero_router
from app.api.routes.dashboard import router as dashboard_router

__all__ = [
    "health_router",
    "auth_router",
    "chat_router",
    "scam_router",
    "medication_router",
    "emergency_router",
    "notification_router",
    "wellness_router",
    "user_router",
    "analytics_router",
    "azure_router",
    "websocket_router",
    "family_router",
    "devops_router",
    "admin_router",
    "hero_router",
    "dashboard_router",
]