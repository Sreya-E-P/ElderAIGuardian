"""
Analytics Routes for tracking and reporting user metrics
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.core.logging import logger
from app.core.dependencies import get_orchestrator, get_auth_user

router = APIRouter()

class AnalyticsEvent(BaseModel):
    """Analytics event model"""
    event_type: str
    event_name: str
    properties: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

class AnalyticsResponse(BaseModel):
    """Analytics response model"""
    success: bool
    event_id: Optional[str] = None
    message: Optional[str] = None

class DashboardSummaryResponse(BaseModel):
    """Dashboard summary response model"""
    user_id: str
    health_score: float
    medications_taken: int
    total_medications: int
    next_medication: Optional[str] = None
    heart_rate: Optional[int] = None
    steps: int
    step_goal: int = 5000
    water_glasses: int
    water_goal: int = 8
    mood_today: Optional[int] = None
    sleep_hours: Optional[float] = None
    scams_detected: int
    active_alerts: int
    unread_notifications: int
    emergency_contacts_count: int
    last_emergency: Optional[str] = None
    wellness_insights: List[str]

class UserStatsResponse(BaseModel):
    """User statistics response model"""
    user_id: str
    period_days: int
    total_chats: int
    total_scams_detected: int
    total_medication_checks: int
    total_wellness_entries: int
    total_emergencies: int
    average_mood: Optional[float] = None
    average_sleep: Optional[float] = None
    average_steps: Optional[float] = None
    adherence_rate: Optional[float] = None
    by_day: Dict[str, Any]

class SystemStatsResponse(BaseModel):
    """System statistics response model (admin only)"""
    total_users: int
    active_users_24h: int
    active_users_7d: int
    total_chats: int
    total_scams_detected: int
    total_emergencies: int
    total_notifications_sent: int
    api_requests_24h: int
    avg_response_time_ms: float
    error_rate_24h: float
    uptime_seconds: float
    services_health: Dict[str, bool]

@router.post("/event", response_model=AnalyticsResponse)
async def track_event(
    request: Request,
    event: AnalyticsEvent,
    user = Depends(get_auth_user)
):
    """Track an analytics event"""
    
    # Generate event ID
    event_id = str(uuid.uuid4())
    timestamp = event.timestamp or datetime.utcnow().isoformat()
    
    # Log the event (in production, this would go to a proper analytics service)
    logger.info(f"📊 Analytics event: {event.event_type}.{event.event_name} from user {user.id}")
    
    # In a real implementation, you would store this in a database or send to Azure Application Insights
    # For now, just return success
    
    return AnalyticsResponse(
        success=True,
        event_id=event_id,
        message="Event tracked successfully"
    )

@router.get("/dashboard", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    request: Request,
    user = Depends(get_auth_user),
    orchestrator = Depends(get_orchestrator)
):
    """Get dashboard summary for the current user"""
    
    metrics_service = getattr(orchestrator, 'metrics_service', None)
    
    # Mock dashboard data for development
    return DashboardSummaryResponse(
        user_id=user.id,
        health_score=85,
        medications_taken=3,
        total_medications=4,
        next_medication="Lisinopril - 8:00 PM",
        heart_rate=72,
        steps=3245,
        step_goal=5000,
        water_glasses=4,
        water_goal=8,
        mood_today=4,
        sleep_hours=7.5,
        scams_detected=2,
        active_alerts=0,
        unread_notifications=3,
        emergency_contacts_count=2,
        last_emergency=None,
        wellness_insights=[
            "You seem happier today than yesterday!",
            "Your sleep has improved this week",
            "Try to drink more water in the afternoon"
        ]
    )

@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    request: Request,
    days: int = 7,
    user = Depends(get_auth_user),
    orchestrator = Depends(get_orchestrator)
):
    """Get user statistics for the specified period"""
    
    metrics_service = getattr(orchestrator, 'metrics_service', None)
    
    # Mock statistics for development
    from datetime import timedelta
    
    # Generate mock daily data
    by_day = {}
    end_date = datetime.utcnow()
    for i in range(days):
        day = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
        by_day[day] = {
            "chats": 2 + (i % 3),
            "scams_detected": 0 if i > 2 else 1,
            "medication_checks": 2,
            "wellness_entries": 1 if i % 2 == 0 else 0,
            "mood": 3 + (i % 3),
            "steps": 3000 + (i * 200),
            "sleep": 7.0 + (i % 10) / 10
        }
    
    return UserStatsResponse(
        user_id=user.id,
        period_days=days,
        total_chats=15,
        total_scams_detected=3,
        total_medication_checks=14,
        total_wellness_entries=5,
        total_emergencies=0,
        average_mood=3.8,
        average_sleep=7.2,
        average_steps=3450,
        adherence_rate=0.92,
        by_day=by_day
    )

@router.get("/system", response_model=SystemStatsResponse)
async def get_system_stats(
    request: Request,
    orchestrator = Depends(get_orchestrator),
    user = Depends(get_auth_user)
):
    """Get system statistics (admin only)"""
    
    # Check if user is admin
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view system stats")
    
    metrics_service = getattr(orchestrator, 'metrics_service', None)
    
    # Mock system statistics for development
    return SystemStatsResponse(
        total_users=1250,
        active_users_24h=342,
        active_users_7d=890,
        total_chats=45678,
        total_scams_detected=1234,
        total_emergencies=56,
        total_notifications_sent=8923,
        api_requests_24h=2345,
        avg_response_time_ms=187.5,
        error_rate_24h=0.023,
        uptime_seconds=86400 * 7,  # 7 days
        services_health={
            "api": True,
            "database": True,
            "cache": True,
            "ai_services": True,
            "communication": True
        }
    )

@router.get("/trends/{metric}")
async def get_metric_trends(
    metric: str,
    request: Request,
    days: int = 30,
    user = Depends(get_auth_user),
    orchestrator = Depends(get_orchestrator)
):
    """Get trends for a specific metric"""
    
    # Mock trend data for development
    from datetime import timedelta
    
    data_points = []
    end_date = datetime.utcnow()
    for i in range(min(days, 30)):
        day = end_date - timedelta(days=i)
        data_points.append({
            "date": day.isoformat(),
            "value": 50 + (i * 2) % 50  # Some variation
        })
    
    return {
        "metric": metric,
        "user_id": user.id,
        "period_days": days,
        "data": sorted(data_points, key=lambda x: x["date"]),
        "summary": {
            "min": min(d["value"] for d in data_points),
            "max": max(d["value"] for d in data_points),
            "avg": sum(d["value"] for d in data_points) / len(data_points),
            "trend": "improving" if data_points[0]["value"] < data_points[-1]["value"] else "declining"
        }
    }

@router.get("/export")
async def export_user_data(
    request: Request,
    format: str = "json",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user = Depends(get_auth_user),
    orchestrator = Depends(get_orchestrator)
):
    """Export user data (GDPR compliance)"""
    
    # Mock data export for development
    export_data = {
        "user_id": user.id,
        "export_date": datetime.utcnow().isoformat(),
        "data": {
            "profile": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "created_at": user.created_at
            },
            "statistics": {
                "total_chats": 15,
                "total_scams_detected": 3,
                "total_medication_checks": 14,
                "total_wellness_entries": 5
            },
            "recent_activity": [
                {
                    "type": "chat",
                    "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "data": "Sample chat message"
                },
                {
                    "type": "medication",
                    "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
                    "data": "Marked Lisinopril as taken"
                }
            ]
        }
    }
    
    if format == "json":
        return export_data
    elif format == "csv":
        # In a real implementation, you'd generate CSV
        return {"message": "CSV export not implemented in mock mode"}
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

@router.delete("/data")
async def delete_user_data(
    request: Request,
    confirm: bool = False,
    user = Depends(get_auth_user),
    orchestrator = Depends(get_orchestrator)
):
    """Delete all user data (GDPR right to be forgotten)"""
    
    if not confirm:
        raise HTTPException(status_code=400, detail="Must confirm deletion with confirm=true")
    
    # Mock data deletion for development
    logger.warning(f"🗑️ User {user.id} requested data deletion")
    
    return {
        "success": True,
        "message": "All user data has been deleted",
        "deletion_date": datetime.utcnow().isoformat()
    }