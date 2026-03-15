"""
Health Check Routes - ENHANCED with System Health Dashboard
Gemini Recommendation #5: Automated System Health Checks
"""

from fastapi import APIRouter, Request, Depends
from typing import Dict, Any, List
from datetime import datetime
import psutil
import os
import platform
import socket

from app.core.logging import logger
from app.core.dependencies import get_orchestrator
from app.core.config import settings

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready")
async def readiness_check(request: Request):
    """Kubernetes readiness probe"""
    app = request.app
    
    # Check if orchestrator is initialized
    if not hasattr(app.state, "orchestrator") or not app.state.orchestrator:
        return {"status": "not ready", "reason": "Orchestrator not initialized"}
    
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}


@router.get("/")
async def health_check(request: Request):
    """Detailed health check with system metrics"""
    app = request.app
    
    # Get process info
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    # Get system info
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    
    health_info = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": getattr(app, "version", "1.0.0"),
        "environment": settings.APP_ENV,
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "process": {
            "pid": os.getpid(),
            "cpu_percent": process.cpu_percent(),
            "memory_rss": memory_info.rss,
            "memory_vms": memory_info.vms,
            "memory_percent": process.memory_percent(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections()),
            "threads": process.num_threads(),
            "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
        },
        "system": {
            "boot_time": boot_time.isoformat(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "disk_free": psutil.disk_usage('/').free,
            "disk_total": psutil.disk_usage('/').total
        },
        "components": {
            "orchestrator": hasattr(app.state, "orchestrator") and app.state.orchestrator is not None,
            "foundry_agent": hasattr(app.state, "foundry_agent") and app.state.foundry_agent is not None,
            "mcp_service": hasattr(app.state, "mcp_service") and app.state.mcp_service is not None,
            "cache_service": hasattr(app.state, "cache_service") and app.state.cache_service is not None,
            "cosmos_service": hasattr(app.state, "cosmos_service") and app.state.cosmos_service is not None,
            "devops_agent": hasattr(app.state, "devops_agent") and app.state.devops_agent is not None
        }
    }
    
    return health_info


@router.get("/system")
async def system_health_dashboard(
    request: Request,
    orchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """
    Comprehensive System Health Dashboard
    Gemini Recommendation #5: Automated System Health Checks
    Shows live status of all Azure services and components
    """
    
    # Get DevOps agent if available
    devops_agent = getattr(orchestrator, 'devops_agent', None)
    
    # Base health info
    health_info = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "operational",
        "services": {},
        "components": {},
        "metrics": {},
        "alerts": []
    }
    
    # Check Azure services
    health_info["services"]["azure"] = {
        "foundry": await _check_foundry_health(orchestrator),
        "cosmos_db": await _check_cosmos_health(orchestrator),
        "communication": await _check_communication_health(orchestrator),
        "mcp": await _check_mcp_health(orchestrator),
        "openai": await _check_openai_health(orchestrator)
    }
    
    # Check system resources
    health_info["metrics"]["system"] = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "uptime_seconds": (datetime.utcnow() - datetime.fromtimestamp(psutil.boot_time())).total_seconds()
    }
    
    # Check application metrics
    if devops_agent and hasattr(devops_agent, 'get_stats'):
        devops_stats = await devops_agent.get_stats()
        health_info["metrics"]["application"] = {
            "total_requests": devops_stats.get("total_requests", 0),
            "error_rate": devops_stats.get("error_rate", 0),
            "avg_response_time_ms": devops_stats.get("avg_response_time_ms", 0),
            "active_sessions": devops_stats.get("active_sessions", 0)
        }
        
        # Add recent incidents as alerts
        if devops_stats.get("recent_errors", 0) > 0:
            health_info["alerts"].append({
                "severity": "warning",
                "message": f"{devops_stats.get('recent_errors')} recent errors detected",
                "component": "application"
            })
    
    # Check component health
    components = {}
    if orchestrator:
        components = {
            "supervisor": getattr(orchestrator, 'is_healthy', False),
            "emergency_agent": getattr(orchestrator, 'emergency_agent', None) is not None,
            "scam_agent": getattr(orchestrator, 'scam_agent', None) is not None,
            "medication_agent": getattr(orchestrator, 'medication_agent', None) is not None,
            "wellness_agent": getattr(orchestrator, 'wellness_agent', None) is not None,
            "family_agent": getattr(orchestrator, 'family_agent', None) is not None
        }
    
    health_info["components"] = components
    
    # Determine overall status
    if any(not v for v in health_info["services"]["azure"].values() if v is not None):
        health_info["status"] = "degraded"
    
    if any(v is False for v in health_info["services"]["azure"].values()):
        health_info["status"] = "critical"
        health_info["alerts"].append({
            "severity": "critical",
            "message": "One or more Azure services are unavailable",
            "component": "azure"
        })
    
    return health_info


@router.get("/diagnostics")
async def diagnostic_report(
    request: Request,
    orchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """
    Generate comprehensive diagnostic report
    For admin/guardian dashboard
    """
    
    devops_agent = getattr(orchestrator, 'devops_agent', None)
    
    # Get DevOps stats if available
    devops_stats = {}
    if devops_agent and hasattr(devops_agent, 'get_stats'):
        devops_stats = await devops_agent.get_stats()
    
    # Get supervisor stats
    supervisor_stats = {}
    if orchestrator and hasattr(orchestrator, 'get_statistics'):
        supervisor_stats = await orchestrator.get_statistics()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "uptime": (datetime.utcnow() - request.app.state.startup_time).total_seconds() if hasattr(request.app.state, 'startup_time') else 0,
        "devops": devops_stats,
        "supervisor": supervisor_stats,
        "services": {
            "foundry": await _check_foundry_health(orchestrator),
            "cosmos_db": await _check_cosmos_health(orchestrator),
            "communication": await _check_communication_health(orchestrator),
            "mcp": await _check_mcp_health(orchestrator)
        },
        "system": {
            "cpu": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent
        }
    }


# Helper functions for health checks
async def _check_foundry_health(orchestrator) -> bool:
    """Check Microsoft Foundry health"""
    foundry_agent = getattr(orchestrator, 'foundry_agent', None)
    if foundry_agent and hasattr(foundry_agent, 'is_healthy'):
        return foundry_agent.is_healthy
    return None


async def _check_cosmos_health(orchestrator) -> bool:
    """Check Cosmos DB health"""
    cosmos_service = getattr(orchestrator, 'cosmos_service', None)
    if cosmos_service and hasattr(cosmos_service, 'health_check'):
        try:
            return await cosmos_service.health_check()
        except:
            return False
    return None


async def _check_communication_health(orchestrator) -> bool:
    """Check Communication Services health"""
    comm_service = getattr(orchestrator, 'communication_service', None)
    if comm_service and hasattr(comm_service, 'is_healthy'):
        return comm_service.is_healthy
    return None


async def _check_mcp_health(orchestrator) -> bool:
    """Check MCP service health"""
    mcp_service = getattr(orchestrator, 'mcp_service', None)
    if mcp_service and hasattr(mcp_service, 'is_healthy'):
        return mcp_service.is_healthy
    return None


async def _check_openai_health(orchestrator) -> bool:
    """Check OpenAI/Azure OpenAI health"""
    foundry_agent = getattr(orchestrator, 'foundry_agent', None)
    if foundry_agent and hasattr(foundry_agent, 'chat_client'):
        return foundry_agent.chat_client is not None
    return None


@router.get("/metrics/prometheus")
async def prometheus_metrics():
    """Prometheus metrics endpoint for monitoring"""
    metrics = []
    
    # System metrics
    metrics.append(f"system_cpu_percent {psutil.cpu_percent()}")
    metrics.append(f"system_memory_percent {psutil.virtual_memory().percent}")
    metrics.append(f"system_disk_percent {psutil.disk_usage('/').percent}")
    
    # Process metrics
    process = psutil.Process()
    metrics.append(f"process_cpu_percent {process.cpu_percent()}")
    metrics.append(f"process_memory_rss {process.memory_info().rss}")
    metrics.append(f"process_open_files {len(process.open_files())}")
    metrics.append(f"process_threads {process.num_threads()}")
    
    return "\n".join(metrics)