"""
Elder AI Guardian - Main Application
Complete Production-Ready Backend with Microsoft Foundry Integration
FINAL VERSION WITH LIVE WEBSOCKET ALERTS
"""

import os
import uuid
import asyncio
import json
import re
import inspect
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Dict, Optional, List, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
import uvicorn
from dotenv import load_dotenv

# Azure SDKs
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.inference import ChatCompletionsClient, EmbeddingsClient
from azure.ai.textanalytics import TextAnalyticsClient
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.translation.text import TextTranslationClient
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.communication.sms import SmsClient
from azure.communication.callautomation import CallAutomationClient
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
from azure.keyvault.secrets import SecretClient
from azure.monitor.opentelemetry import configure_azure_monitor
from azure.search.documents import SearchClient
from azure.servicebus import ServiceBusClient
from azure.eventgrid import EventGridPublisherClient

# MCP imports - correct package naming
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
    print("MCP SDK loaded")
except ImportError:
    MCP_AVAILABLE = False
    print("MCP SDK not available")

# For Azure MCP specific functionality
try:
    from msmcp_azure import AzureMCPServer
    AZURE_MCP_AVAILABLE = True
    print("Azure MCP loaded")
except ImportError:
    AZURE_MCP_AVAILABLE = False
    print("Azure MCP not available")

# Microsoft Agent Framework
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

# Import agents - using your actual constructors
from app.agents.foundry.foundry_agent import FoundryAgent
from app.agents.foundry.model_router import ModelRouter
from app.agents.orchestrator.supervisor_agent import SupervisorAgent
from app.agents.scam_detection.scam_agent import ScamDetectionAgent
from app.agents.medication.medication_agent import MedicationAgent
from app.agents.emergency.emergency_agent import EmergencyAgent
from app.agents.family_notification.notification_agent import FamilyNotificationAgent
from app.agents.wellness.wellness_agent import WellnessAgent

# Import services
from app.services.azure.communication_service import CommunicationService
from app.services.azure.storage_service import StorageService
from app.services.azure.search_service import SearchService
from app.services.azure.event_service import EventService
from app.services.azure.mcp_service import MCPService
from app.services.cache.cache_service import CacheService
from app.services.database.cosmos_service import CosmosService
from app.services.auth.auth_service import AuthService
from app.services.metrics.metrics_service import MetricsService
from app.services.notification.notification_service import NotificationService
from app.services.devops.devops_agent import DevOpsAgent

# Import config
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.middleware import (
    RequestLoggingMiddleware,
    RateLimitMiddleware,
    AuthenticationMiddleware,
    ErrorHandlingMiddleware
)
from app.core.exceptions import setup_exception_handlers

# Import API routes
from app.api.routes import (
    health_router,
    auth_router,
    chat_router,
    scam_router,
    medication_router,
    emergency_router,
    notification_router,
    wellness_router,
    user_router,
    analytics_router,
    azure_router,
    websocket_router,
    family_router,
    devops_router,
    admin_router,
    hero_router,
    dashboard_router
)

# Load environment
load_dotenv()
setup_logging()

# Security
security = HTTPBearer()

# Global services
foundry_agent: Optional[FoundryAgent] = None
model_router: Optional[ModelRouter] = None
orchestrator: Optional[SupervisorAgent] = None
communication_service: Optional[CommunicationService] = None
storage_service: Optional[StorageService] = None
search_service: Optional[SearchService] = None
event_service: Optional[EventService] = None
cache_service: Optional[CacheService] = None
cosmos_service: Optional[CosmosService] = None
auth_service: Optional[AuthService] = None
metrics_service: Optional[MetricsService] = None
notification_service: Optional[NotificationService] = None
mcp_service: Optional[MCPService] = None
devops_agent: Optional[DevOpsAgent] = None

# Microsoft Agent Framework components
kernel: Optional[Kernel] = None
supervisor_agent: Optional[ChatCompletionAgent] = None

# WebSocket connections and connection info
active_connections: Dict[str, WebSocket] = {}
connection_sessions: Dict[str, str] = {}  # connection_id -> user_id
connection_info: Dict[str, Dict[str, Any]] = {}  # Store additional connection metadata

# Pending alerts storage
pending_alerts: Dict[str, List[Dict[str, Any]]] = {}  # user_id -> list of pending alerts

# Metrics for DevOps agent
request_counter = 0
startup_time = datetime.utcnow()


# Helper function to create agents with flexible parameters
async def create_agent(agent_class, **kwargs):
    """Create an agent instance with only the parameters it accepts"""
    # Get the signature of the agent's __init__ method
    sig = inspect.signature(agent_class.__init__)
    
    # Filter kwargs to only include parameters that the constructor accepts
    valid_params = {}
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
        if param_name in kwargs:
            valid_params[param_name] = kwargs[param_name]
        # Handle cases where parameter has a default value
        elif param.default is not param.empty:
            # Parameter has default, we can skip it
            pass
    
    logger.info(f"Creating {agent_class.__name__} with params: {list(valid_params.keys())}")
    
    # Create the agent with only valid parameters
    agent = agent_class(**valid_params)
    
    # If the agent has an initialize method, call it
    if hasattr(agent, 'initialize') and callable(agent.initialize):
        await agent.initialize()
    
    return agent


# ========== DEPENDENCY FUNCTION ==========
async def get_auth_user(request: Request):
    """Get authenticated user from request state"""
    # For development, return mock user
    user_id = getattr(request.state, "user_id", None)
    if not user_id and settings.APP_ENV == "development":
        user_id = "dev_user"
    
    return type('User', (), {
        'id': user_id or 'dev_user',
        'role': 'user',
        'name': 'Dev User',
        'email': 'dev@example.com'
    })()
# ==========================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup and shutdown"""
    global foundry_agent, model_router, orchestrator, communication_service
    global storage_service, search_service, event_service, cache_service
    global cosmos_service, auth_service, metrics_service
    global notification_service, mcp_service, kernel, supervisor_agent
    global devops_agent, startup_time
    
    print("=" * 80)
    print("    ELDER AI GUARDIAN - MICROSOFT FOUNDRY EDITION")
    print("    Hero Technologies: Foundry, MCP, Agent Framework, Agentic DevOps")
    print("=" * 80)
    
    startup_time = datetime.utcnow()
    
    try:
        # Initialize Azure credentials
        credential = DefaultAzureCredential()
        logger.info("Azure credentials initialized")
        
        # Initialize Microsoft Agent Framework (Semantic Kernel)
        logger.info("\nInitializing Microsoft Agent Framework...")
        kernel = Kernel()
        
        # Only initialize Azure Chat if credentials are available
        if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_KEY:
            azure_chat_service = AzureChatCompletion(
                deployment_name=settings.AZURE_OPENAI_DEPLOYMENT or "gpt-4o",
                endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_KEY
            )
            kernel.add_service(azure_chat_service)
            logger.info("Microsoft Agent Framework initialized with Azure OpenAI")
        else:
            logger.warning("Azure OpenAI not configured - Semantic Kernel will use fallback")
        
        # Initialize Foundry Agent
        logger.info("\nInitializing Microsoft Foundry Agent...")
        foundry_agent = await create_agent(
            FoundryAgent,
            project_client=None,
            cache_service=cache_service,
            metrics=metrics_service,
            kernel=kernel,
            credential=credential
        )
        logger.info("Foundry Agent initialized with {} models".format(
            len(foundry_agent.models) if hasattr(foundry_agent, 'models') and foundry_agent.models else 0
        ))
        
        # Initialize Model Router
        if foundry_agent:
            model_router = await foundry_agent.get_model_router()
            logger.info("Model Router initialized with dynamic routing capabilities")
            logger.info("   Routing Strategies:")
            for task, strategy in {
                "emergency": "direct_generation (0.1 temp)",
                "scam_detection": "chain_of_thought (0.2 temp)",
                "medication": "structured_extraction (0.3 temp)",
                "wellness": "sentiment_analysis (0.7 temp)",
                "general": "conversational (0.8 temp)"
            }.items():
                logger.info(f"     - {task}: {strategy}")
        
        # Initialize Azure MCP (Model Context Protocol)
        logger.info("\nInitializing Azure MCP...")
        if AZURE_MCP_AVAILABLE and settings.AZURE_MCP_ENDPOINT:
            try:
                mcp_service = MCPService(mcp_client=None)
                await mcp_service.initialize()
                logger.info("MCP Service initialized")
                if hasattr(mcp_service, 'tools') and mcp_service.tools:
                    logger.info("   MCP Tools:")
                    for tool_name in mcp_service.tools.keys():
                        logger.info(f"     - {tool_name}")
            except Exception as e:
                logger.warning(f"MCP initialization failed: {e}")
                mcp_service = MCPService(None)
                await mcp_service.initialize()
                logger.info("MCP Service initialized in mock mode")
        else:
            logger.warning("Azure MCP not configured - using mock")
            mcp_service = await create_agent(MCPService, mcp_client=None)
        
        # Initialize Communication Services
        logger.info("\nInitializing Communication Services...")
        sms_client = None
        call_client = None
        chat_client = None
        
        if settings.AZURE_COMMS_CONNECTION_STRING:
            try:
                sms_client = SmsClient.from_connection_string(
                    settings.AZURE_COMMS_CONNECTION_STRING
                )
                logger.info("  SMS client initialized")
            except Exception as e:
                logger.warning(f"  SMS client initialization failed: {e}")
            
            try:
                call_client = CallAutomationClient.from_connection_string(
                    settings.AZURE_COMMS_CONNECTION_STRING
                )
                logger.info("  Call client initialized")
            except Exception as e:
                logger.warning(f"  Call client initialization failed: {e}")
        
        communication_service = await create_agent(
            CommunicationService,
            sms_client=sms_client,
            call_client=call_client,
            chat_client=chat_client
        )
        logger.info("Communication Services initialized")
        
        # Initialize Storage Service
        logger.info("\nInitializing Storage Service...")
        if settings.AZURE_STORAGE_CONNECTION:
            try:
                blob_client = BlobServiceClient.from_connection_string(
                    settings.AZURE_STORAGE_CONNECTION
                )
                storage_service = await create_agent(StorageService, blob_client=blob_client)
                logger.info("Storage Service initialized")
            except Exception as e:
                logger.warning(f"Storage Service initialization failed: {e}")
                storage_service = await create_agent(StorageService, blob_client=None)
        else:
            logger.warning("Azure Storage not configured - using mock")
            storage_service = await create_agent(StorageService, blob_client=None)
        
        # Initialize Search Service
        logger.info("\nInitializing Search Service...")
        if settings.AZURE_SEARCH_ENDPOINT:
            try:
                search_client = SearchClient(
                    endpoint=settings.AZURE_SEARCH_ENDPOINT,
                    index_name=settings.AZURE_SEARCH_INDEX or "elderai-index",
                    credential=credential
                )
                search_service = await create_agent(SearchService, search_client=search_client)
                logger.info("Search Service initialized")
            except Exception as e:
                logger.warning(f"Search Service initialization failed: {e}")
                search_service = await create_agent(SearchService, search_client=None)
        else:
            logger.warning("Azure Search not configured - using mock")
            search_service = await create_agent(SearchService, search_client=None)
        
        # Initialize Event Service
        logger.info("\nInitializing Event Service...")
        servicebus_client = None
        eventgrid_client = None
        
        if settings.AZURE_SERVICEBUS_CONNECTION:
            try:
                servicebus_client = ServiceBusClient.from_connection_string(
                    settings.AZURE_SERVICEBUS_CONNECTION
                )
                logger.info("  Service Bus client initialized")
            except Exception as e:
                logger.warning(f"  Service Bus client initialization failed: {e}")
        
        if settings.AZURE_EVENTGRID_ENDPOINT:
            try:
                eventgrid_client = EventGridPublisherClient(
                    endpoint=settings.AZURE_EVENTGRID_ENDPOINT,
                    credential=credential
                )
                logger.info("  Event Grid client initialized")
            except Exception as e:
                logger.warning(f"  Event Grid client initialization failed: {e}")
        
        event_service = await create_agent(
            EventService,
            servicebus_client=servicebus_client,
            eventgrid_client=eventgrid_client
        )
        logger.info("Event Service initialized")
        
        # Initialize Cosmos DB (PRIMARY DATABASE)
        logger.info("\nInitializing Cosmos DB (Primary Database)...")
        if settings.COSMOS_DB_CONNECTION:
            try:
                cosmos_client = CosmosClient.from_connection_string(
                    settings.COSMOS_DB_CONNECTION
                )
                cosmos_service = await create_agent(CosmosService, client=cosmos_client)
                logger.info("Cosmos DB initialized - PRIMARY DATABASE")
            except Exception as e:
                logger.error(f"Cosmos DB initialization failed: {e}")
                raise
        else:
            logger.error("COSMOS_DB_CONNECTION not found in .env")
            raise ValueError("Cosmos DB connection string required")
        
        # Initialize Cache
        logger.info("\nInitializing Cache...")
        cache_service = await create_agent(
            CacheService,
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            ssl=settings.REDIS_SSL
        )
        logger.info("Cache initialized")
        
        # Initialize Auth Service (using Cosmos DB)
        logger.info("\nInitializing Auth Service...")
        auth_service = await create_agent(
            AuthService,
            db_service=cosmos_service,
            cache_service=cache_service,
            secret_key=settings.SECRET_KEY
        )
        logger.info("Auth Service initialized with Cosmos DB")
        
        # Initialize Metrics Service
        logger.info("\nInitializing Metrics Service...")
        metrics_service = await create_agent(
            MetricsService,
            app_insights_key=settings.APPINSIGHTS_INSTRUMENTATION_KEY,
            log_analytics_workspace=settings.LOG_ANALYTICS_WORKSPACE_ID
        )
        logger.info("Metrics Service initialized")
        
        # Initialize Notification Service (using Cosmos DB)
        logger.info("\nInitializing Notification Service...")
        notification_service = await create_agent(
            NotificationService,
            communication_service=communication_service,
            db_service=cosmos_service,
            cache_service=cache_service
        )
        logger.info("Notification Service initialized")
        
        # Initialize DevOps Agent
        logger.info("\nInitializing DevOps Agent...")
        devops_agent = DevOpsAgent(
            cache_service=cache_service,
            metrics_service=metrics_service
        )
        await devops_agent.initialize()
        logger.info("DevOps Agent initialized")
        logger.info("   Autonomous Capabilities:")
        capabilities = [
            "CPU spike mitigation",
            "Memory leak cleanup",
            "Disk space management",
            "Error rate monitoring",
            "Service auto-restart"
        ]
        for cap in capabilities:
            logger.info(f"     - {cap}")
        
        # Start DevOps monitoring
        asyncio.create_task(devops_agent.start_monitoring())
        logger.info("DevOps monitoring started")
        
        # Initialize AI Agents - USING UNIVERSAL CREATION
        logger.info("\nInitializing Specialized AI Agents...")
        
        # Scam Detection Agent
        scam_agent = await create_agent(
            ScamDetectionAgent,
            foundry_service=foundry_agent,
            mcp_service=mcp_service,
            cache_service=cache_service
        )
        logger.info("  Scam Detection Agent initialized")
        
        # Medication Agent
        medication_agent = await create_agent(
            MedicationAgent,
            foundry_agent=foundry_agent,
            model_router=model_router,
            cosmos_service=cosmos_service,
            cache_service=cache_service,
            notification_service=notification_service
        )
        logger.info("  Medication Agent initialized")
        
        # Emergency Agent
        emergency_agent = await create_agent(
            EmergencyAgent,
            foundry_agent=foundry_agent,
            model_router=model_router,
            communication_service=communication_service,
            db_service=cosmos_service,
            cache_service=cache_service,
            notification_service=notification_service,
            metrics_service=metrics_service
        )
        logger.info("  Emergency Agent initialized")
        
        # Family Notification Agent
        family_agent = await create_agent(
            FamilyNotificationAgent,
            foundry_agent=foundry_agent,
            model_router=model_router,
            communication_service=communication_service,
            db_service=cosmos_service,
            cache_service=cache_service,
            notification_service=notification_service
        )
        logger.info("  Family Notification Agent initialized")
        
        # Wellness Agent
        wellness_agent = await create_agent(
            WellnessAgent,
            foundry_agent=foundry_agent,
            model_router=model_router,
            db_service=cosmos_service,
            cache_service=cache_service,
            notification_service=notification_service
        )
        logger.info("  Wellness Agent initialized")
        
        # Initialize Supervisor Agent (Microsoft Agent Framework)
        logger.info("\nInitializing Supervisor Agent with Microsoft Agent Framework...")
        orchestrator = await create_agent(
            SupervisorAgent,
            kernel=kernel,
            foundry_service=foundry_agent,
            mcp_service=mcp_service,
            scam_agent=scam_agent,
            medication_agent=medication_agent,
            emergency_agent=emergency_agent,
            family_agent=family_agent,
            wellness_agent=wellness_agent,
            cache_service=cache_service,
            db_service=cosmos_service,
            notification_service=notification_service,
            metrics_service=metrics_service,
            event_service=event_service
        )
        logger.info("Supervisor Agent initialized with Microsoft Agent Framework")
        
        # Store in app state for route access
        app.state.orchestrator = orchestrator
        app.state.foundry_agent = foundry_agent
        app.state.mcp_service = mcp_service
        app.state.metrics_service = metrics_service
        app.state.cosmos_service = cosmos_service
        app.state.cache_service = cache_service
        app.state.devops_agent = devops_agent
        app.state.startup_time = startup_time
        
        print("\n" + "=" * 80)
        print("    ELDER AI GUARDIAN IS READY!")
        print("    Version: 1.0.0")
        print("    Environment: {}".format(settings.APP_ENV))
        print("    Primary Database: Azure Cosmos DB")
        print("    Hero Technologies:")
        print("      - Microsoft Foundry (Model Router)")
        print("      - Azure MCP (Tool Integration)")
        print("      - Microsoft Agent Framework (Supervisor)")
        print("      - Agentic DevOps (Self-Healing)")
        print("      - Live WebSocket Alerts")
        print("=" * 80)
        print("\nMetrics endpoint: /api/metrics")
        print("API Documentation: /api/docs")
        print("Health Check: /api/health")
        print("WebSocket: /ws/{user_id}")
        print("Dashboard: /api/dashboard")
        print("Chat: /api/chat")
        print("Emergency: /api/emergency/sos")
        print("=" * 80)
        
        yield
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}", exc_info=True)
        print(f"\nFATAL: Startup failed: {str(e)}")
        raise
    
    finally:
        print("\nShutting down...")
        
        # Cleanup connections
        if cache_service and hasattr(cache_service, 'close'):
            await cache_service.close()
        if cosmos_service and hasattr(cosmos_service, 'close'):
            await cosmos_service.close()
        if communication_service and hasattr(communication_service, 'close'):
            await communication_service.close()
        if storage_service and hasattr(storage_service, 'close'):
            await storage_service.close()
        if search_service and hasattr(search_service, 'close'):
            await search_service.close()
        if event_service and hasattr(event_service, 'close'):
            await event_service.close()
        if foundry_agent and hasattr(foundry_agent, 'close'):
            await foundry_agent.close()
        if mcp_service and hasattr(mcp_service, 'cleanup_old_contexts'):
            await mcp_service.cleanup_old_contexts()
        if devops_agent and hasattr(devops_agent, 'stop_monitoring'):
            await devops_agent.stop_monitoring()
        
        # Close WebSocket connections
        for connection_id, websocket in active_connections.items():
            try:
                await websocket.close(code=1001, reason="Server shutting down")
            except:
                pass
        
        print("Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Elder AI Guardian API",
    description="Complete Multi-Agent Elder Care System with Microsoft Foundry",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# Setup exception handlers
setup_exception_handlers(app)

# ============================================================================
# INCLUDE ALL ROUTERS - THIS IS THE CRITICAL SECTION
# ============================================================================

# Health & Monitoring
app.include_router(health_router)

# Authentication
app.include_router(auth_router)

# Core Features
app.include_router(dashboard_router)
app.include_router(chat_router)
app.include_router(emergency_router)
app.include_router(scam_router)
app.include_router(medication_router)
app.include_router(wellness_router)
app.include_router(family_router)

# Notifications
app.include_router(notification_router)

# User Management
app.include_router(user_router)

# Analytics & Metrics
app.include_router(analytics_router)
app.include_router(azure_router)

# WebSocket (Real-time) - DISABLED: @app.websocket below handles this
# app.include_router(websocket_router)

# DevOps & Admin
app.include_router(devops_router)
app.include_router(admin_router)

# Hero Technologies Showcase
app.include_router(hero_router)

# ============================================================================

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    global request_counter
    request_counter += 1
    
    # Get devops stats if available
    devops_stats = {}
    if devops_agent and hasattr(devops_agent, 'get_stats'):
        try:
            devops_stats = await devops_agent.get_stats()
        except:
            pass
    
    return {
        "service": "Elder AI Guardian",
        "version": "1.0.0",
        "powered_by": "Microsoft Hero Technologies",
        "status": "operational",
        "environment": settings.APP_ENV,
        "uptime_seconds": (datetime.utcnow() - startup_time).total_seconds(),
        "total_requests": request_counter,
        "active_websockets": len(active_connections),
        "documentation": "/api/docs",
        "health_check": "/api/health",
        "metrics": "/api/metrics",
        "dashboard": "/api/dashboard",
        "primary_database": "Azure Cosmos DB",
        "hero_technologies": {
            "microsoft_foundry": bool(foundry_agent),
            "azure_mcp": bool(mcp_service),
            "microsoft_agent_framework": bool(orchestrator),
            "agentic_devops": bool(devops_agent),
            "azure_communication": bool(communication_service),
            "cosmos_db": bool(cosmos_service),
            "live_websocket_alerts": True,
            "model_router": bool(model_router)
        },
        "agents": {
            "supervisor": "active" if orchestrator else "inactive",
            "scam_detection": "active" if 'scam_agent' in locals() else "inactive",
            "medication": "active" if 'medication_agent' in locals() else "inactive",
            "emergency": "active" if 'emergency_agent' in locals() else "inactive",
            "family_notification": "active" if 'family_agent' in locals() else "inactive",
            "wellness": "active" if 'wellness_agent' in locals() else "inactive"
        },
        "azure_services": {
            "foundry": bool(foundry_agent),
            "mcp": bool(mcp_service),
            "communication": bool(communication_service),
            "cosmos": bool(cosmos_service),
            "storage": bool(storage_service),
            "search": bool(search_service),
            "event_grid": bool(event_service)
        },
        "devops": devops_stats,
        "endpoints": {
            "chat": "/api/chat",
            "scam_analysis": "/api/scam/analyze",
            "medication": "/api/medication",
            "emergency": "/api/emergency/sos",
            "wellness": "/api/wellness",
            "dashboard": "/api/dashboard",
            "family_dashboard": "/api/family/dashboard/{elder_id}",
            "websocket": "/ws/{user_id}",
            "admin": "/api/admin/dashboard"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/metrics")
async def get_metrics():
    """Metrics endpoint for DevOps monitoring"""
    global request_counter
    
    metrics = {
        "service": "Elder AI Guardian",
        "uptime_seconds": (datetime.utcnow() - startup_time).total_seconds(),
        "total_requests": request_counter,
        "active_websockets": len(active_connections),
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Add service health metrics
    if orchestrator:
        metrics["components"]["supervisor"] = getattr(orchestrator, 'is_healthy', False)
    
    if foundry_agent:
        metrics["components"]["foundry"] = getattr(foundry_agent, 'is_healthy', False)
        if hasattr(foundry_agent, 'metrics') and foundry_agent.metrics:
            metrics["model_stats"] = foundry_agent.metrics.get_stats()
    
    if mcp_service:
        metrics["components"]["mcp"] = getattr(mcp_service, 'is_healthy', False)
        metrics["mcp_contexts"] = len(getattr(mcp_service, 'contexts', {})) if hasattr(mcp_service, 'contexts') else 0
        metrics["mcp_tools"] = len(getattr(mcp_service, 'tools', {})) if hasattr(mcp_service, 'tools') else 0
    
    if cache_service:
        metrics["components"]["cache"] = getattr(cache_service, 'is_healthy', False)
    
    if communication_service:
        metrics["components"]["communication"] = getattr(communication_service, 'is_healthy', False)
    
    if cosmos_service:
        metrics["components"]["cosmos_db"] = await cosmos_service.health_check()
    
    if devops_agent:
        metrics["components"]["devops"] = getattr(devops_agent, 'is_healthy', False)
        if hasattr(devops_agent, 'get_stats'):
            try:
                devops_stats = await devops_agent.get_stats()
                metrics["devops"] = devops_stats
            except:
                pass
    
    # Connection info
    metrics["connections"] = {
        "active": len(active_connections),
        "users": len(set(connection_sessions.values()))
    }
    
    return metrics


# ========== PENDING ALERTS FUNCTIONS ==========

async def send_pending_alert_to_family(elder_id: str, alert_data: Dict[str, Any]):
    """
    Send pending alert to family dashboard in real-time
    This uses WebSocket to push alerts without page refresh
    """
    global pending_alerts, active_connections, connection_sessions, connection_info, cosmos_service
    
    sent_count = 0
    
    # Store in pending alerts
    if elder_id not in pending_alerts:
        pending_alerts[elder_id] = []
    pending_alerts[elder_id].append(alert_data)
    
    # Keep only last 20 alerts
    if len(pending_alerts[elder_id]) > 20:
        pending_alerts[elder_id] = pending_alerts[elder_id][-20:]
    
    # Get family contacts for this elder
    family_contacts = []
    if cosmos_service:
        try:
            contacts = await cosmos_service.get_emergency_contacts(elder_id) or []
            family_contacts = [c.get("id") for c in contacts if c.get("id")]
        except:
            pass
    
    # Send to all connected family members
    for conn_id, ws in active_connections.items():
        user_id = connection_sessions.get(conn_id)
        
        # Check if this connection is a family member of this elder
        if user_id in family_contacts or user_id == elder_id:
            try:
                # Check if subscribed to alerts
                if conn_id in connection_info and connection_info[conn_id].get("subscribed_to_alerts", False):
                    await ws.send_json({
                        "type": "pending_alert",
                        "data": alert_data,
                        "elder_id": elder_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send pending alert: {e}")
    
    if sent_count > 0:
        logger.info(f"Sent pending alert to {sent_count} family members for elder {elder_id}")
    
    return sent_count


# Add endpoint to get pending alerts (fallback if WebSocket not connected)
@app.get("/api/alerts/pending/{elder_id}")
async def get_pending_alerts(
    elder_id: str,
    request: Request,
    current_user = Depends(get_auth_user)
) -> List[Dict[str, Any]]:
    """Get pending alerts for an elder (fallback for non-WebSocket clients)"""
    
    # Check authorization
    is_authorized = False
    if cosmos_service:
        try:
            contacts = await cosmos_service.get_emergency_contacts(elder_id) or []
            current_user_id = getattr(current_user, 'id', '')
            is_authorized = any(c.get("id") == current_user_id for c in contacts) or getattr(current_user, 'role', '') == "admin"
        except:
            pass
    
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return pending_alerts.get(elder_id, [])


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time communication with LIVE ALERTS support"""
    global request_counter
    
    await websocket.accept()
    connection_id = f"conn_{uuid.uuid4().hex[:8]}"
    active_connections[connection_id] = websocket
    connection_sessions[connection_id] = user_id
    
    # Initialize connection info for this connection
    connection_info[connection_id] = {
        "user_id": user_id,
        "connected_at": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat(),
        "message_count": 0,
        "subscribed_to_alerts": False,
        "alert_user_id": None
    }
    
    logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
    
    try:
        # Send connection confirmation with hero tech info
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Elder AI Guardian",
            "connection_id": connection_id,
            "hero_technologies": {
                "foundry": bool(foundry_agent),
                "mcp": bool(mcp_service),
                "agent_framework": bool(orchestrator),
                "devops": bool(devops_agent),
                "cosmos_db": bool(cosmos_service),
                "live_alerts": True
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send initial metrics if available
        if metrics_service:
            await websocket.send_json({
                "type": "metrics",
                "data": {
                    "active_connections": len(active_connections),
                    "uptime": (datetime.utcnow() - startup_time).total_seconds()
                },
                "timestamp": datetime.utcnow().isoformat()
            })
        
        while True:
            data = await websocket.receive_json()
            request_counter += 1
            message_type = data.get("type", "unknown")
            
            # Update connection info
            if connection_id in connection_info:
                connection_info[connection_id]["last_activity"] = datetime.utcnow().isoformat()
                connection_info[connection_id]["message_count"] += 1
            
            if message_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            elif message_type == "chat":
                # Process chat message through orchestrator
                if orchestrator:
                    try:
                        result = await orchestrator.process_message(
                            user_id=user_id,
                            message=data.get("content", ""),
                            session_id=data.get("sessionId"),
                            metadata=data.get("metadata", {})
                        )
                        
                        await websocket.send_json({
                            "type": "chat_response",
                            "data": result,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
                        # Track metrics
                        if metrics_service:
                            await metrics_service.record_chat(
                                user_id=user_id,
                                intent=result.get("intent", "unknown"),
                                agent="supervisor"
                            )
                    except Exception as e:
                        logger.error(f"Chat processing error: {str(e)}")
                        await websocket.send_json({
                            "type": "error",
                            "error": str(e),
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    
            elif message_type == "emergency":
                # Process emergency
                if orchestrator and hasattr(orchestrator, 'emergency_agent') and orchestrator.emergency_agent:
                    try:
                        result = await orchestrator.emergency_agent.handle_emergency(
                            user_id=user_id,
                            message=data.get("message", "Emergency via WebSocket"),
                            location=data.get("location")
                        )
                        
                        await websocket.send_json({
                            "type": "emergency_response",
                            "data": result,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
                        # Track emergency metric
                        if metrics_service:
                            await metrics_service.record_emergency(
                                emergency_type=result.get("type", "unknown"),
                                severity=result.get("severity", "MEDIUM")
                            )
                    except Exception as e:
                        logger.error(f"Emergency processing error: {str(e)}")
                        await websocket.send_json({
                            "type": "error",
                            "error": str(e),
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    
            elif message_type == "sensor_data":
                # Process sensor data for fall detection
                if orchestrator and hasattr(orchestrator, 'emergency_agent') and orchestrator.emergency_agent:
                    try:
                        result = await orchestrator.emergency_agent.detect_fall(
                            data.get("sensor_data", [])
                        )
                        
                        if result.get("is_fall"):
                            # Auto-trigger emergency
                            emergency_result = await orchestrator.emergency_agent.handle_emergency(
                                user_id=user_id,
                                message="Fall detected via sensors",
                                location=data.get("location")
                            )
                            
                            await websocket.send_json({
                                "type": "fall_detected",
                                "data": {
                                    "fall_analysis": result,
                                    "emergency": emergency_result
                                },
                                "timestamp": datetime.utcnow().isoformat()
                            })
                            
                            # Track fall detection
                            if metrics_service:
                                await metrics_service.record_emergency(
                                    emergency_type="fall",
                                    severity=result.get("severity", "HIGH")
                                )
                        else:
                            await websocket.send_json({
                                "type": "sensor_data_processed",
                                "data": result,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                    except Exception as e:
                        logger.error(f"Sensor data processing error: {str(e)}")
                        
            elif message_type == "typing":
                # Broadcast typing indicator to other users in session
                await broadcast_typing(user_id, data.get("sessionId"), exclude=[connection_id])
                
            elif message_type == "read_receipt":
                # Update read receipts
                await update_read_receipt(user_id, data.get("messageId"))
                
            elif message_type == "location_update":
                # Update user location
                if orchestrator and hasattr(orchestrator, 'emergency_agent') and orchestrator.emergency_agent:
                    await orchestrator.emergency_agent.update_user_location(
                        user_id=user_id,
                        location=data.get("location")
                    )
                    
            elif message_type == "get_metrics":
                # Send current metrics
                await websocket.send_json({
                    "type": "metrics",
                    "data": {
                        "active_connections": len(active_connections),
                        "total_requests": request_counter,
                        "uptime": (datetime.utcnow() - startup_time).total_seconds()
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            elif message_type == "mcp_tools":
                # List available MCP tools
                if mcp_service:
                    tools_list = list(mcp_service.tools.keys()) if hasattr(mcp_service, 'tools') and mcp_service.tools else []
                    await websocket.send_json({
                        "type": "mcp_tools",
                        "data": {
                            "tools": tools_list,
                            "count": len(tools_list)
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
            elif message_type == "check_phone":
                # Check phone number against scam database
                if mcp_service:
                    result = await mcp_service.execute_tool(
                        "check_phone_number",
                        {"phone_number": data.get("phone_number")}
                    )
                    await websocket.send_json({
                        "type": "phone_check_result",
                        "data": result.data if hasattr(result, 'data') else result,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
            elif message_type == "report_scam":
                # Report scam to community database
                if mcp_service:
                    result = await mcp_service.execute_tool(
                        "report_scam",
                        {
                            "phone_number": data.get("phone_number"),
                            "email": data.get("email"),
                            "url": data.get("url"),
                            "scam_type": data.get("scam_type", "other"),
                            "description": data.get("description", "")
                        }
                    )
                    await websocket.send_json({
                        "type": "scam_report_result",
                        "data": result.data if hasattr(result, 'data') else result,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            # ========== LIVE ALERT SUBSCRIPTION ==========
            elif message_type == "subscribe_alerts":
                # Subscribe to live alerts for this user
                subscribe_user_id = data.get("user_id", user_id)
                
                # Store subscription in connection info
                if connection_id in connection_info:
                    connection_info[connection_id]["subscribed_to_alerts"] = True
                    connection_info[connection_id]["alert_user_id"] = subscribe_user_id
                
                await websocket.send_json({
                    "type": "subscribed",
                    "message": f"Subscribed to live alerts for user {subscribe_user_id}",
                    "user_id": subscribe_user_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                logger.info(f"Connection {connection_id} subscribed to alerts for user {subscribe_user_id}")
            
            elif message_type == "unsubscribe_alerts":
                # Unsubscribe from live alerts
                if connection_id in connection_info:
                    connection_info[connection_id]["subscribed_to_alerts"] = False
                
                await websocket.send_json({
                    "type": "unsubscribed",
                    "message": "Unsubscribed from live alerts",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # ========== TEST ALERT (for development) ==========
            elif message_type == "test_alert":
                # Send a test alert (for development/demo)
                alert_data = {
                    "alert_id": f"alert_{uuid.uuid4().hex[:8]}",
                    "type": data.get("alert_type", "test"),
                    "severity": data.get("severity", "INFO"),
                    "title": data.get("title", "Test Alert"),
                    "message": data.get("message", "This is a test alert"),
                    "actions": data.get("actions", [])
                }
                
                # Send to this specific connection
                await websocket.send_json({
                    "type": "live_alert",
                    "data": alert_data,
                    "timestamp": datetime.utcnow().isoformat()
                })
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id} for user {user_id}")
        if connection_id in active_connections:
            del active_connections[connection_id]
        if connection_id in connection_sessions:
            del connection_sessions[connection_id]
        if connection_id in connection_info:
            del connection_info[connection_id]
        
    except Exception as e:
        logger.error(f"WebSocket error for {user_id}: {str(e)}")
        if connection_id in active_connections:
            del active_connections[connection_id]
        if connection_id in connection_sessions:
            del connection_sessions[connection_id]
        if connection_id in connection_info:
            del connection_info[connection_id]

# ========== HELPER FUNCTIONS ==========

async def broadcast_typing(user_id: str, session_id: str, exclude: List[str] = None):
    """Broadcast typing indicator to other users in session"""
    if not exclude:
        exclude = []
    
    # Find other connections for this user's session
    for conn_id, ws in active_connections.items():
        if conn_id not in exclude:
            try:
                await ws.send_json({
                    "type": "typing",
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except:
                pass


async def update_read_receipt(user_id: str, message_id: str):
    """Update read receipt for a message"""
    # In production, this would update database
    logger.debug(f"Read receipt for message {message_id} from user {user_id}")


async def send_live_alert(user_id: str, alert_data: Dict[str, Any]):
    """
    Send live alert to all connected clients for this user
    This is the main function for real-time alerts
    """
    sent_count = 0
    
    for conn_id, ws in active_connections.items():
        # Check if this connection belongs to the target user
        if connection_sessions.get(conn_id) == user_id:
            # Check if this connection has subscribed to alerts
            subscribed = False
            if conn_id in connection_info:
                subscribed = connection_info[conn_id].get("subscribed_to_alerts", False)
                # Also check if they're subscribed to this specific user
                alert_user_id = connection_info[conn_id].get("alert_user_id")
                if alert_user_id and alert_user_id != user_id:
                    continue
            
            # If not subscribed, still send critical alerts (optional)
            if not subscribed and alert_data.get("severity") not in ["CRITICAL", "HIGH"]:
                continue
            
            try:
                await ws.send_json({
                    "type": "live_alert",
                    "data": alert_data,
                    "timestamp": datetime.utcnow().isoformat()
                })
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send live alert to {conn_id}: {e}")
    
    if sent_count > 0:
        logger.info(f"Sent live alert to {sent_count} connections for user {user_id}")
    
    return sent_count


async def send_bulk_alerts(user_ids: List[str], alert_data: Dict[str, Any]):
    """Send live alert to multiple users"""
    total_sent = 0
    for user_id in user_ids:
        sent = await send_live_alert(user_id, alert_data)
        total_sent += sent
    return total_sent


# DevOps self-healing endpoint
@app.post("/api/devops/heal")
async def devops_heal(request: Request):
    """Endpoint for DevOps agent to trigger self-healing"""
    auth_header = request.headers.get("X-DevOps-Key")
    if auth_header != os.getenv("DEVOPS_API_KEY", "devops-secret-key"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    actions_taken = []
    
    # Check cache service
    if cache_service and hasattr(cache_service, 'is_healthy') and not cache_service.is_healthy:
        try:
            await cache_service.initialize()
            actions_taken.append("reinitialized_cache")
        except:
            pass
    
    # Check communication service
    if communication_service and hasattr(communication_service, 'is_healthy') and not communication_service.is_healthy:
        try:
            await communication_service.initialize()
            actions_taken.append("reinitialized_communication")
        except:
            pass
    
    # Check Cosmos DB
    if cosmos_service:
        try:
            healthy = await cosmos_service.health_check()
            if not healthy:
                # Can't reinitialize Cosmos DB easily, but we can log it
                actions_taken.append("cosmos_db_connection_checked")
        except:
            pass
    
    # Clear old MCP contexts
    if mcp_service:
        try:
            await mcp_service.cleanup_old_contexts(max_age_hours=1)
            actions_taken.append("cleaned_mcp_contexts")
        except:
            pass
    
    return {
        "status": "healed" if actions_taken else "healthy",
        "actions_taken": actions_taken,
        "timestamp": datetime.utcnow().isoformat()
    }


# Test alert endpoint
@app.post("/api/alerts/test/{user_id}")
async def send_test_alert(user_id: str, request: Request):
    """Send a test alert to a specific user (for development)"""
    alert_data = {
        "alert_id": f"alert_{uuid.uuid4().hex[:8]}",
        "type": "test",
        "severity": "INFO",
        "title": "Test Alert",
        "message": "This is a test alert from the system",
        "actions": [
            {"label": "View", "action": "/dashboard"},
            {"label": "Dismiss", "action": "dismiss"}
        ]
    }
    
    sent = await send_live_alert(user_id, alert_data)
    
    return {
        "success": True,
        "sent_count": sent,
        "alert": alert_data,
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=port,
        reload=settings.APP_ENV == "development" if hasattr(settings, 'APP_ENV') else False,
        workers=int(os.getenv("WORKERS", "4")),
        log_level="info"
    )