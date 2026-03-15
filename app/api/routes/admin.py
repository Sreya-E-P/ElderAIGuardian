"""
Admin Routes - System Health Dashboard
Gemini Recommendation #5: Automated System Health Checks for Admin View
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, List
from datetime import datetime, timedelta
import psutil

from app.core.logging import logger
from app.core.dependencies import get_orchestrator, get_auth_user
from app.core.config import settings

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/dashboard")
async def admin_dashboard(
    request: Request,
    orchestrator = Depends(get_orchestrator),
    current_user = Depends(get_auth_user)
) -> Dict[str, Any]:
    """
    Admin dashboard with system health metrics
    Only accessible by admin users
    """
    
    # Check if user is admin
    user_role = getattr(current_user, 'role', 'user')
    if user_role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get DevOps agent
    devops_agent = getattr(orchestrator, 'devops_agent', None)
    
    # Get system health
    system_health = {}
    if devops_agent and hasattr(devops_agent, 'check_system_health'):
        system_health = await devops_agent.check_system_health()
    
    # Get application performance
    app_performance = {}
    if devops_agent and hasattr(devops_agent, 'check_application_performance'):
        app_performance = await devops_agent.check_application_performance()
    
    # Get Azure services health
    azure_health = {}
    if devops_agent and hasattr(devops_agent, 'check_azure_services'):
        azure_health = await devops_agent.check_azure_services()
    
    # Get recent errors
    recent_errors = []
    if devops_agent and hasattr(devops_agent, 'error_history'):
        recent_errors = devops_agent.error_history[-20:]
    
    # Get recent fixes
    recent_fixes = []
    if devops_agent and hasattr(devops_agent, 'fixed_issues'):
        recent_fixes = devops_agent.fixed_issues[-20:]
    
    # Get supervisor statistics
    supervisor_stats = {}
    if orchestrator and hasattr(orchestrator, 'get_statistics'):
        supervisor_stats = await orchestrator.get_statistics()
    
    # Get Cosmos DB stats
    cosmos_stats = {}
    cosmos_service = getattr(orchestrator, 'cosmos_service', None)
    if cosmos_service and hasattr(cosmos_service, 'get_stats'):
        try:
            cosmos_stats = await cosmos_service.get_stats()
        except:
            pass
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.APP_ENV,
        "version": "1.0.0",
        "system_health": system_health,
        "application_performance": app_performance,
        "azure_services": azure_health,
        "supervisor": supervisor_stats,
        "cosmos_db": cosmos_stats,
        "recent_errors": recent_errors,
        "recent_fixes": recent_fixes,
        "hero_technologies": {
            "microsoft_foundry": True,
            "azure_mcp": True,
            "microsoft_agent_framework": True,
            "agentic_devops": devops_agent is not None,
            "closed_loop_safety": True
        }
    }


@router.get("/users")
async def list_users_admin(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    orchestrator = Depends(get_orchestrator),
    current_user = Depends(get_auth_user)
) -> List[Dict[str, Any]]:
    """List all users (admin only)"""
    
    # Check if user is admin
    user_role = getattr(current_user, 'role', 'user')
    if user_role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    cosmos_service = getattr(orchestrator, 'cosmos_service', None)
    
    if not cosmos_service or not hasattr(cosmos_service, 'get_all_users'):
        return []
    
    try:
        users = await cosmos_service.get_all_users(skip=skip, limit=limit)
        # Remove sensitive data
        for user in users:
            if 'hashed_password' in user:
                del user['hashed_password']
        return users
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/pending")
async def get_pending_alerts(
    request: Request,
    orchestrator = Depends(get_orchestrator),
    current_user = Depends(get_auth_user)
) -> List[Dict[str, Any]]:
    """Get all pending alerts across all users (admin only)"""
    
    # Check if user is admin
    user_role = getattr(current_user, 'role', 'user')
    if user_role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    pending_alerts = []
    
    if hasattr(orchestrator, 'sessions') and orchestrator.sessions:
        for session_key, session in orchestrator.sessions.items():
            if hasattr(session, 'pending_alerts') and session.pending_alerts:
                for alert_id, alert in session.pending_alerts.items():
                    if not alert.get("confirmed", False):
                        pending_alerts.append({
                            "id": alert_id,
                            "user_id": getattr(session, 'user_id', 'unknown'),
                            "type": alert.get("type", "unknown"),
                            "escalation_level": alert.get("escalation_level", 1),
                            "sent_at": alert.get("sent_at"),
                            "time_elapsed": (datetime.utcnow() - datetime.fromisoformat(alert.get("sent_at", datetime.utcnow().isoformat()))).total_seconds() if alert.get("sent_at") else 0
                        })
    
    return pending_alerts


@router.post("/alerts/clear/{alert_id}")
async def clear_alert(
    alert_id: str,
    request: Request,
    orchestrator = Depends(get_orchestrator),
    current_user = Depends(get_auth_user)
) -> Dict[str, Any]:
    """Manually clear a pending alert (admin only)"""
    
    # Check if user is admin
    user_role = getattr(current_user, 'role', 'user')
    if user_role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find and clear the alert
    if hasattr(orchestrator, 'sessions') and orchestrator.sessions:
        for session_key, session in orchestrator.sessions.items():
            if hasattr(session, 'pending_alerts') and alert_id in session.pending_alerts:
                alert = session.pending_alerts[alert_id]
                alert["confirmed"] = True
                alert["confirmed_by"] = "admin"
                alert["confirmed_at"] = datetime.utcnow().isoformat()
                
                return {
                    "success": True,
                    "alert_id": alert_id,
                    "message": "Alert cleared by admin"
                }
    
    raise HTTPException(status_code=404, detail="Alert not found")


@router.post("/thresholds/update")
async def update_system_thresholds(
    request: Request,
    thresholds: Dict[str, Any],
    orchestrator = Depends(get_orchestrator),
    current_user = Depends(get_auth_user)
) -> Dict[str, Any]:
    """Update system health thresholds (admin only)"""
    
    # Check if user is admin
    user_role = getattr(current_user, 'role', 'user')
    if user_role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    devops_agent = getattr(orchestrator, 'devops_agent', None)
    
    if not devops_agent:
        raise HTTPException(status_code=503, detail="DevOps agent not available")
    
    # Update thresholds
    if "cpu" in thresholds:
        devops_agent.cpu_threshold = thresholds["cpu"]
    if "memory" in thresholds:
        devops_agent.memory_threshold = thresholds["memory"]
    if "disk" in thresholds:
        devops_agent.disk_threshold = thresholds["disk"]
    if "error_rate" in thresholds:
        devops_agent.error_rate_threshold = thresholds["error_rate"]
    if "response_time" in thresholds:
        devops_agent.response_time_threshold = thresholds["response_time"]
    
    return {
        "success": True,
        "message": "Thresholds updated",
        "thresholds": {
            "cpu": devops_agent.cpu_threshold,
            "memory": devops_agent.memory_threshold,
            "disk": devops_agent.disk_threshold,
            "error_rate": devops_agent.error_rate_threshold,
            "response_time_ms": devops_agent.response_time_threshold
        }
    }