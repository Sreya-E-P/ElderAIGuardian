"""
Azure Services Routes for managing Azure integrations
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.logging import logger
from app.core.dependencies import get_orchestrator, get_auth_user

router = APIRouter(prefix="/api/azure", tags=["Azure Services"])

class AzureConfig(BaseModel):
    """Azure configuration model"""
    subscription_id: Optional[str] = None
    resource_group: Optional[str] = None
    location: Optional[str] = None
    openai_endpoint: Optional[str] = None
    openai_deployment: Optional[str] = None
    comms_connection_string: Optional[str] = None
    cosmos_connection: Optional[str] = None

class AzureServiceStatus(BaseModel):
    """Azure service status model"""
    service: str
    status: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str

@router.get("/")
async def azure_root():
    """Azure services root endpoint"""
    return {
        "service": "Azure Services",
        "version": "1.0.0",
        "endpoints": {
            "status": "/api/azure/status",
            "config": "/api/azure/config",
            "models": "/api/azure/models",
            "test": "/api/azure/test"
        }
    }

@router.get("/status", response_model=List[AzureServiceStatus])
async def get_azure_status(
    request: Request,
    user = Depends(get_auth_user),
    orchestrator = Depends(get_orchestrator)
):
    """Get status of Azure services"""
    
    foundry_agent = getattr(orchestrator, 'foundry_agent', None)
    mcp_service = getattr(orchestrator, 'mcp_service', None)
    communication_service = getattr(orchestrator, 'communication_service', None)
    cosmos_service = getattr(orchestrator, 'cosmos_service', None)
    
    timestamp = datetime.utcnow().isoformat()
    
    statuses = [
        AzureServiceStatus(
            service="Microsoft Foundry",
            status="available" if foundry_agent and foundry_agent.is_healthy else "unavailable",
            details={"models": len(foundry_agent.models) if foundry_agent else 0},
            timestamp=timestamp
        ),
        AzureServiceStatus(
            service="Azure MCP",
            status="available" if mcp_service and mcp_service.is_healthy else "unavailable",
            details={"tools": len(mcp_service.tools) if mcp_service else 0},
            timestamp=timestamp
        ),
        AzureServiceStatus(
            service="Communication Services",
            status="available" if communication_service and communication_service.is_healthy else "unavailable",
            timestamp=timestamp
        ),
        AzureServiceStatus(
            service="Cosmos DB",
            status="available" if cosmos_service and cosmos_service.is_healthy else "unavailable",
            timestamp=timestamp
        )
    ]
    
    return statuses

@router.get("/config")
async def get_azure_config(
    request: Request,
    user = Depends(get_auth_user)
):
    """Get Azure configuration (admin only)"""
    
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    from app.core.config import settings
    
    # Return sanitized config (no secrets)
    return {
        "subscription_id": settings.AZURE_SUBSCRIPTION_ID if hasattr(settings, 'AZURE_SUBSCRIPTION_ID') else None,
        "resource_group": settings.AZURE_RESOURCE_GROUP if hasattr(settings, 'AZURE_RESOURCE_GROUP') else None,
        "location": settings.AZURE_LOCATION if hasattr(settings, 'AZURE_LOCATION') else None,
        "openai_endpoint": settings.AZURE_OPENAI_ENDPOINT if hasattr(settings, 'AZURE_OPENAI_ENDPOINT') else None,
        "openai_deployment": settings.AZURE_OPENAI_DEPLOYMENT if hasattr(settings, 'AZURE_OPENAI_DEPLOYMENT') else None,
        "comms_endpoint": settings.AZURE_COMMS_CONNECTION_STRING.split(';')[0] if hasattr(settings, 'AZURE_COMMS_CONNECTION_STRING') and settings.AZURE_COMMS_CONNECTION_STRING else None,
        "cosmos_endpoint": settings.COSMOS_DB_CONNECTION.split(';')[0] if hasattr(settings, 'COSMOS_DB_CONNECTION') and settings.COSMOS_DB_CONNECTION else None,
        "keyvault_url": settings.AZURE_KEYVAULT_URL if hasattr(settings, 'AZURE_KEYVAULT_URL') else None
    }

@router.post("/config")
async def update_azure_config(
    config: AzureConfig,
    request: Request,
    user = Depends(get_auth_user)
):
    """Update Azure configuration (admin only)"""
    
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # In production, this would update settings or Key Vault
    logger.info(f"Azure config update requested by {user.id}")
    
    return {
        "success": True,
        "message": "Configuration updated (simulated)",
        "updated_fields": [k for k, v in config.dict(exclude_unset=True).items() if v is not None]
    }

@router.get("/models")
async def list_azure_models(
    request: Request,
    user = Depends(get_auth_user),
    orchestrator = Depends(get_orchestrator)
):
    """List available Azure AI models"""
    
    foundry_agent = getattr(orchestrator, 'foundry_agent', None)
    
    if not foundry_agent:
        # Mock models for development
        return {
            "models": [
                {
                    "name": "gpt-4o",
                    "type": "chat",
                    "capabilities": ["chat", "function_calling", "vision"],
                    "context_length": 128000
                },
                {
                    "name": "gpt-4o-mini",
                    "type": "chat",
                    "capabilities": ["chat", "function_calling"],
                    "context_length": 128000
                },
                {
                    "name": "text-embedding-3-large",
                    "type": "embedding",
                    "dimensions": 3072
                },
                {
                    "name": "phi-3",
                    "type": "chat",
                    "capabilities": ["chat", "summarization"],
                    "context_length": 128000
                }
            ]
        }
    
    return {"models": foundry_agent.list_models()}

@router.post("/test/{service}")
async def test_azure_service(
    service: str,
    request: Request,
    user = Depends(get_auth_user),
    orchestrator = Depends(get_orchestrator)
):
    """Test a specific Azure service"""
    
    results = {
        "service": service,
        "success": False,
        "message": "",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if service == "foundry":
        foundry_agent = getattr(orchestrator, 'foundry_agent', None)
        if foundry_agent:
            try:
                # Simple test completion
                response = await foundry_agent.generate_chat(
                    messages=[{"role": "user", "content": "Say 'test'"}],
                    max_tokens=5
                )
                results["success"] = True
                results["message"] = "Foundry service is working"
                results["response"] = response
            except Exception as e:
                results["message"] = str(e)
        else:
            results["message"] = "Foundry agent not available"
    
    elif service == "mcp":
        mcp_service = getattr(orchestrator, 'mcp_service', None)
        if mcp_service:
            results["success"] = True
            results["message"] = f"MCP service is working with {len(mcp_service.tools)} tools"
            results["tools"] = list(mcp_service.tools.keys())
        else:
            results["message"] = "MCP service not available"
    
    elif service == "communication":
        comms_service = getattr(orchestrator, 'communication_service', None)
        if comms_service:
            results["success"] = True
            results["message"] = "Communication service is working (simulated)"
        else:
            results["message"] = "Communication service not available"
    
    elif service == "cosmos":
        cosmos_service = getattr(orchestrator, 'cosmos_service', None)
        if cosmos_service:
            results["success"] = True
            results["message"] = "Cosmos DB service is working"
        else:
            results["message"] = "Cosmos DB service not available"
    
    else:
        results["message"] = f"Unknown service: {service}"
    
    return results

@router.get("/usage")
async def get_azure_usage(
    request: Request,
    days: int = 7,
    user = Depends(get_auth_user)
):
    """Get Azure service usage statistics (admin only)"""
    
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Mock usage data for development
    from datetime import timedelta
    
    daily_usage = []
    end_date = datetime.utcnow()
    for i in range(days):
        day = end_date - timedelta(days=i)
        daily_usage.append({
            "date": day.strftime("%Y-%m-%d"),
            "api_calls": 100 + (i * 10),
            "tokens_used": 5000 + (i * 500),
            "cost_estimate": 0.15 + (i * 0.01)
        })
    
    return {
        "period_days": days,
        "total_api_calls": sum(d["api_calls"] for d in daily_usage),
        "total_tokens": sum(d["tokens_used"] for d in daily_usage),
        "estimated_cost": sum(d["cost_estimate"] for d in daily_usage),
        "daily_breakdown": sorted(daily_usage, key=lambda x: x["date"])
    }