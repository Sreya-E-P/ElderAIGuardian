"""
Azure MCP (Model Context Protocol) Service
Hero Technology: Model Context Protocol for agent tool integration
FULLY CORRECTED VERSION - WITH LIVE THREAT FEED TOOL
"""

import asyncio
import json
import hashlib
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta

# Import logger first
from app.core.logging import logger

# Define base classes that will be used regardless of import success
class Tool:
    """Base Tool class"""
    def __init__(self, name=None, description=None, input_schema=None):
        self.name = name
        self.description = description
        self.input_schema = input_schema

class Context:
    """Base Context class"""
    def __init__(self, id=None, session_id=None, messages=None, system_prompt=None, 
                 max_tokens=None, current_tokens=0, created_at=None, last_updated=None, metadata=None):
        self.id = id
        self.session_id = session_id
        self.messages = messages or []
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.current_tokens = current_tokens
        self.created_at = created_at
        self.last_updated = last_updated
        self.metadata = metadata or {}

class Message:
    """Base Message class"""
    def __init__(self, role=None, content=None, timestamp=None, tokens=0, metadata=None):
        self.role = role
        self.content = content
        self.timestamp = timestamp
        self.tokens = tokens
        self.metadata = metadata or {}

class ToolResult:
    """Base ToolResult class"""
    def __init__(self, success=True, data=None, error=None):
        self.success = success
        self.data = data or {}
        self.error = error

class MCPClient:
    """Base MCPClient class"""
    def __init__(self, endpoint=None, credential=None, server=None):
        self.endpoint = endpoint
        self.credential = credential
        self.server = server
        
    async def register_tool(self, tool):
        pass
        
    async def close(self):
        pass

# Try to import actual MCP packages and override base classes if successful
try:
    # Try the standard mcp package first
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import (
        CallToolResult,
        TextContent,
        ImageContent,
        EmbeddedResource
    )
    
    # We'll keep our base classes - they're compatible
    MCP_AVAILABLE = True
    MCP_SOURCE = "standard"
    logger.info("✅ MCP SDK loaded from mcp package")
    
except ImportError:
    try:
        # Try the Azure MCP package
        from msmcp_azure import AzureMCPServer as AzureMCPClient
        from msmcp_azure.models import (
            Context as AzureContext,
            Message as AzureMessage,
            Tool as AzureTool,
            ToolCall,
            ToolResult as AzureToolResult,
            Resource,
            ResourceTemplate
        )
        
        # Override base classes with Azure versions if they provide more functionality
        # But keep our base classes as fallback
        MCP_AVAILABLE = True
        MCP_SOURCE = "azure"
        logger.info("✅ Azure MCP loaded from msmcp_azure")
        
    except ImportError:
        # Fallback - use our base classes
        MCP_AVAILABLE = False
        MCP_SOURCE = "mock"
        logger.warning("⚠️ MCP not available - using mock mode")

class MCPService:
    """
    Service for Model Context Protocol
    Enables agents to access external tools and data sources
    This is a key hero technology for the hackathon
    """
    
    def __init__(self, mcp_client: Optional[MCPClient] = None):
        self.mcp_client = mcp_client
        self.contexts = {}
        self.context_stats = {}
        self.is_healthy = False
        self.max_context_length = 128000
        self.reserved_tokens = 4000
        self.mcp_available = MCP_AVAILABLE
        self.mcp_source = MCP_SOURCE
        
        # Add these for hackathon showcase
        self.tool_calls = 0
        self.tool_stats = {}
        
        # Community scam database (in-memory for demo)
        self.scam_database = {
            "reported_phones": {
                "+1234567890": {"count": 15, "type": "phishing", "last_reported": "2024-01-15"},
                "+1987654321": {"count": 8, "type": "grandparent_scam", "last_reported": "2024-01-20"},
                "+1555123456": {"count": 3, "type": "tech_support", "last_reported": "2024-01-10"}
            },
            "reported_urls": {
                "scam-bank.com": {"count": 25, "type": "phishing", "last_reported": "2024-01-18"},
                "verify-account-now.com": {"count": 12, "type": "phishing", "last_reported": "2024-01-22"},
                "microsoft-support-scam.net": {"count": 7, "type": "tech_support", "last_reported": "2024-01-19"}
            },
            "reported_emails": {
                "security@fakebank.com": {"count": 30, "type": "phishing", "last_reported": "2024-01-21"},
                "support@microsoft-scam.org": {"count": 10, "type": "tech_support", "last_reported": "2024-01-17"}
            }
        }
        
        # Live threat feed data (updated in real-time for demo)
        self.threat_feed = {
            "phishing": [
                {
                    "url": "fake-bank-verification.com",
                    "reported": "2024-03-10",
                    "source": "APWG",
                    "confidence": 0.95,
                    "active": True
                },
                {
                    "url": "secure-account-update.net",
                    "reported": "2024-03-09",
                    "source": "PhishTank",
                    "confidence": 0.98,
                    "active": True
                },
                {
                    "url": "microsoft-verify-account.com",
                    "reported": "2024-03-08",
                    "source": "Microsoft Threat Intelligence",
                    "confidence": 0.99,
                    "active": True
                }
            ],
            "phone_scams": [
                {
                    "number": "+15551234567",
                    "type": "tech_support",
                    "reports": 234,
                    "active": True,
                    "first_seen": "2024-02-15"
                },
                {
                    "number": "+15559876543",
                    "type": "irs_impersonation",
                    "reports": 567,
                    "active": True,
                    "first_seen": "2024-01-20"
                },
                {
                    "number": "+15551112222",
                    "type": "grandparent_scam",
                    "reports": 89,
                    "active": True,
                    "first_seen": "2024-03-01"
                }
            ],
            "email_scams": [
                {
                    "domain": "secure-verify.net",
                    "impersonating": "microsoft.com",
                    "first_seen": "2024-03-01",
                    "reports": 45
                },
                {
                    "domain": "account-security.com",
                    "impersonating": "paypal.com",
                    "first_seen": "2024-02-28",
                    "reports": 123
                }
            ],
            "current_tactics": [
                {
                    "name": "Fake Package Delivery",
                    "description": "Scammers send fake delivery notifications with tracking links",
                    "first_seen": "2024-03-05",
                    "severity": "HIGH"
                },
                {
                    "name": "AI Voice Cloning",
                    "description": "Scammers use AI to clone family member voices for grandparent scams",
                    "first_seen": "2024-02-20",
                    "severity": "CRITICAL"
                },
                {
                    "name": "Fake Banking Alerts",
                    "description": "SMS messages claiming bank accounts are frozen",
                    "first_seen": "2024-03-01",
                    "severity": "HIGH"
                }
            ]
        }
        
        # Register MCP tools (as dictionaries first, will convert to Tool objects)
        self.tools = {}  # Will be populated in initialize
        self.tool_definitions = self._get_tool_definitions()
        
    async def initialize(self):
        """Initialize MCP service with tool registration"""
        logger.info("=" * 60)
        logger.info("Initializing Azure MCP Service...")
        logger.info(f"MCP Source: {self.mcp_source}")
        logger.info(f"MCP Available: {self.mcp_available}")
        logger.info("=" * 60)
        
        # Convert tool definitions to Tool objects
        self.tools = self._register_tools()
        
        if not self.mcp_available or not self.mcp_client:
            logger.warning("⚠️ MCP not available - running in mock mode")
            self.is_healthy = True
            logger.info(f"✅ Registered {len(self.tools)} mock MCP tools")
            return
        
        # Register all tools with MCP server
        for tool_name, tool in self.tools.items():
            try:
                if hasattr(self.mcp_client, 'register_tool'):
                    await self.mcp_client.register_tool(tool)
                    logger.info(f"  ✅ Registered MCP tool: {tool_name}")
                else:
                    logger.info(f"  📝 Mock registration for tool: {tool_name}")
            except Exception as e:
                logger.error(f"  ❌ Failed to register tool {tool_name}: {e}")
        
        self.is_healthy = True
        logger.info("=" * 60)
        logger.info(f"✅ MCPService initialized with {len(self.tools)} tools")
        logger.info("=" * 60)
    
    def _get_tool_definitions(self) -> Dict[str, Dict]:
        """Get tool definitions as dictionaries"""
        return {
            "emergency_services": {
                "name": "emergency_services",
                "description": "Contact emergency services (911) with location and emergency details",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "emergency_type": {
                            "type": "string",
                            "enum": ["medical", "fire", "police", "general"],
                            "description": "Type of emergency"
                        },
                        "location": {
                            "type": "object",
                            "properties": {
                                "latitude": {"type": "number"},
                                "longitude": {"type": "number"},
                                "address": {"type": "string"}
                            }
                        },
                        "user_id": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["emergency_type", "user_id"]
                }
            },
            "medication_database": {
                "name": "medication_database",
                "description": "Query medication information, interactions, and side effects",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "medication_name": {"type": "string"},
                        "query_type": {
                            "type": "string",
                            "enum": ["info", "interactions", "side_effects", "dosage"]
                        }
                    },
                    "required": ["medication_name", "query_type"]
                }
            },
            "family_notification": {
                "name": "family_notification",
                "description": "Send notifications to family members via multiple channels",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "notification_type": {
                            "type": "string",
                            "enum": ["emergency", "medication", "wellness", "general"]
                        },
                        "message": {"type": "string"},
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "urgent"]
                        },
                        "channels": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["sms", "email", "push", "call"]
                            }
                        },
                        "requires_acknowledgment": {"type": "boolean", "default": False}
                    },
                    "required": ["user_id", "message"]
                }
            },
            "weather_service": {
                "name": "weather_service",
                "description": "Get weather information for location-based wellness recommendations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"},
                        "date": {"type": "string", "format": "date"}
                    }
                }
            },
            "pharmacy_locator": {
                "name": "pharmacy_locator",
                "description": "Find nearby pharmacies and medication availability",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "object",
                            "properties": {
                                "latitude": {"type": "number"},
                                "longitude": {"type": "number"}
                            }
                        },
                        "radius_km": {"type": "number", "default": 5},
                        "medication_name": {"type": "string"}
                    }
                }
            },
            "scam_database": {
                "name": "scam_database",
                "description": "Check against known scam patterns and reported numbers from community",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "phone_number": {"type": "string"},
                        "email": {"type": "string"},
                        "url": {"type": "string"}
                    }
                }
            },
            "check_phone_number": {
                "name": "check_phone_number",
                "description": "Check if a phone number has been reported as a scam in the community database",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "phone_number": {"type": "string", "description": "Phone number to check (e.g., +1234567890)"}
                    },
                    "required": ["phone_number"]
                }
            },
            "report_scam": {
                "name": "report_scam",
                "description": "Report a scam to the community database to help protect others",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "phone_number": {"type": "string", "description": "Suspicious phone number"},
                        "email": {"type": "string", "description": "Suspicious email address"},
                        "url": {"type": "string", "description": "Suspicious URL"},
                        "scam_type": {
                            "type": "string",
                            "enum": ["phishing", "tech_support", "grandparent", "lottery", "romance", "investment", "other"]
                        },
                        "description": {"type": "string", "description": "Description of the scam attempt"}
                    },
                    "required": ["scam_type", "description"]
                }
            },
            # NEW: Live Threat Feed Tool (Gemini Recommendation #3)
            "threat_feed": {
                "name": "threat_feed",
                "description": "Get real-time threat intelligence on current scams, phishing attacks, and fraud tactics",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "threat_type": {
                            "type": "string",
                            "enum": ["phishing", "phone", "email", "tactics", "all"],
                            "description": "Type of threat intelligence to retrieve",
                            "default": "all"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of threats to return",
                            "default": 10
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL", "all"],
                            "description": "Filter by severity level",
                            "default": "all"
                        }
                    }
                }
            }
        }
    
    def _register_tools(self) -> Dict[str, Tool]:
        """
        Convert tool definitions to Tool objects
        """
        tools = {}
        for tool_name, tool_def in self.tool_definitions.items():
            tools[tool_name] = Tool(
                name=tool_def["name"],
                description=tool_def["description"],
                input_schema=tool_def["input_schema"]
            )
        return tools
    
    async def create_context(
        self,
        session_id: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 128000
    ) -> Context:
        """Create a new MCP context window"""
        context_id = hashlib.md5(session_id.encode()).hexdigest()
        
        context = Context(
            id=context_id,
            session_id=session_id,
            messages=[],
            system_prompt=system_prompt,
            max_tokens=min(max_tokens, self.max_context_length),
            current_tokens=0,
            created_at=datetime.utcnow().isoformat(),
            last_updated=datetime.utcnow().isoformat(),
            metadata={}
        )
        
        if system_prompt:
            context.current_tokens += len(system_prompt) // 4
        
        self.contexts[context_id] = context
        self.context_stats[context_id] = {
            "messages_added": 0,
            "tokens_processed": 0,
            "prunes_performed": 0,
            "tools_called": 0
        }
        
        logger.info(f"Created MCP context {context_id} for session {session_id}")
        return context
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context_id: Optional[str] = None
    ) -> ToolResult:
        """
        Execute an MCP tool
        This is the core of A2A (Agent-to-Agent) communication
        """
        logger.info(f"Executing MCP tool: {tool_name}")
        
        if tool_name not in self.tools:
            return ToolResult(
                success=False,
                error=f"Tool {tool_name} not found",
                data={}
            )
        
        try:
            # Track tool usage - ADD THESE LINES FOR HACKATHON
            self.tool_calls += 1
            if not hasattr(self, 'tool_stats'):
                self.tool_stats = {}
            self.tool_stats[tool_name] = self.tool_stats.get(tool_name, 0) + 1
            
            if context_id and context_id in self.context_stats:
                self.context_stats[context_id]["tools_called"] += 1
            
            # Execute based on tool type
            if tool_name == "emergency_services":
                result = await self._execute_emergency_tool(arguments)
            elif tool_name == "medication_database":
                result = await self._execute_medication_tool(arguments)
            elif tool_name == "family_notification":
                result = await self._execute_notification_tool(arguments)
            elif tool_name == "weather_service":
                result = await self._execute_weather_tool(arguments)
            elif tool_name == "pharmacy_locator":
                result = await self._execute_pharmacy_tool(arguments)
            elif tool_name == "scam_database":
                result = await self._execute_scam_tool(arguments)
            elif tool_name == "check_phone_number":
                result = await self._execute_check_phone_tool(arguments)
            elif tool_name == "report_scam":
                result = await self._execute_report_scam_tool(arguments)
            elif tool_name == "threat_feed":
                result = await self._execute_threat_feed_tool(arguments)
            else:
                result = {"message": f"Tool {tool_name} executed", "success": True}
            
            return ToolResult(
                success=True,
                data=result,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                data={}
            )
    
    async def _execute_emergency_tool(self, args: Dict) -> Dict:
        """Execute emergency services tool"""
        return {
            "status": "dispatched",
            "estimated_response_time": 300,
            "service_contacted": "911",
            "incident_id": f"inc_{datetime.utcnow().timestamp()}",
            "message": f"Emergency services notified for {args.get('emergency_type')} emergency"
        }
    
    async def _execute_medication_tool(self, args: Dict) -> Dict:
        """Execute medication database tool"""
        medication_db = {
            "aspirin": {
                "info": "Pain reliever and anti-inflammatory",
                "side_effects": ["Stomach upset", "Heartburn", "Nausea"],
                "interactions": ["Blood thinners", "Methotrexate"],
                "dosage": "325-650mg every 4-6 hours"
            },
            "lisinopril": {
                "info": "ACE inhibitor for high blood pressure",
                "side_effects": ["Dry cough", "Dizziness", "Headache"],
                "interactions": ["Potassium supplements", "Diuretics"],
                "dosage": "10-40mg once daily"
            },
            "metformin": {
                "info": "Diabetes medication",
                "side_effects": ["Nausea", "Diarrhea", "Stomach upset"],
                "interactions": ["Alcohol", "Contrast dyes"],
                "dosage": "500-2000mg daily"
            }
        }
        
        med_name = args.get("medication_name", "").lower()
        query_type = args.get("query_type", "info")
        
        if med_name in medication_db:
            return {
                "medication": med_name,
                "query_type": query_type,
                "result": medication_db[med_name].get(query_type, "Information not available"),
                "disclaimer": "Always consult with healthcare provider"
            }
        else:
            return {
                "medication": med_name,
                "error": "Medication not found in database",
                "suggestions": list(medication_db.keys())
            }
    
    async def _execute_notification_tool(self, args: Dict) -> Dict:
        """Execute family notification tool"""
        channels = args.get("channels", ["sms"])
        priority = args.get("priority", "medium")
        requires_ack = args.get("requires_acknowledgment", False)
        
        return {
            "notification_id": f"notif_{datetime.utcnow().timestamp()}",
            "channels_used": channels,
            "priority": priority,
            "status": "sent",
            "estimated_delivery": "immediate",
            "message_preview": args.get("message", "")[:50] + "...",
            "requires_acknowledgment": requires_ack,
            "acknowledgment_deadline": (datetime.utcnow() + timedelta(minutes=5)).isoformat() if requires_ack else None
        }
    
    async def _execute_weather_tool(self, args: Dict) -> Dict:
        """Execute weather service tool"""
        return {
            "location": f"{args.get('latitude', 0)}, {args.get('longitude', 0)}",
            "temperature": 72,
            "conditions": "Partly cloudy",
            "humidity": 45,
            "wind_speed": 8,
            "recommendations": [
                "Good day for a short walk",
                "Stay hydrated",
                "Sun protection recommended"
            ]
        }
    
    async def _execute_pharmacy_tool(self, args: Dict) -> Dict:
        """Execute pharmacy locator tool"""
        return {
            "pharmacies": [
                {
                    "name": "CVS Pharmacy",
                    "distance_km": 1.2,
                    "address": "123 Main St",
                    "phone": "555-0123",
                    "has_medication": args.get("medication_name") in ["aspirin", "ibuprofen"],
                    "hours": "Open until 9pm"
                },
                {
                    "name": "Walgreens",
                    "distance_km": 2.5,
                    "address": "456 Oak Ave",
                    "phone": "555-0124",
                    "has_medication": True,
                    "hours": "24 hours"
                }
            ],
            "search_radius_km": args.get("radius_km", 5)
        }
    
    async def _execute_scam_tool(self, args: Dict) -> Dict:
        """Execute scam database tool - enhanced with community reporting"""
        scam_numbers = ["555-0000", "555-9999"]
        scam_domains = ["scam.com", "phishing.net"]
        
        phone = args.get("phone_number")
        email = args.get("email")
        url = args.get("url")
        
        result = {
            "is_scam": False,
            "risk_level": "LOW",
            "reported": False,
            "details": [],
            "community_reports": []
        }
        
        # Check against static list
        if phone and phone in scam_numbers:
            result["is_scam"] = True
            result["risk_level"] = "HIGH"
            result["reported"] = True
            result["details"].append(f"Phone number {phone} reported as scam")
        
        if url and any(domain in url for domain in scam_domains):
            result["is_scam"] = True
            result["risk_level"] = "HIGH"
            result["reported"] = True
            result["details"].append(f"Domain reported as phishing site")
        
        # Check against community database
        if phone and phone in self.scam_database["reported_phones"]:
            report = self.scam_database["reported_phones"][phone]
            result["is_scam"] = True
            result["risk_level"] = "HIGH" if report["count"] > 10 else "MEDIUM"
            result["community_reports"].append({
                "type": report["type"],
                "count": report["count"],
                "last_reported": report["last_reported"]
            })
            result["details"].append(f"Phone number reported {report['count']} times in community database")
        
        if url and url in self.scam_database["reported_urls"]:
            report = self.scam_database["reported_urls"][url]
            result["is_scam"] = True
            result["risk_level"] = "HIGH" if report["count"] > 15 else "MEDIUM"
            result["community_reports"].append({
                "type": report["type"],
                "count": report["count"],
                "last_reported": report["last_reported"]
            })
        
        if email and email in self.scam_database["reported_emails"]:
            report = self.scam_database["reported_emails"][email]
            result["is_scam"] = True
            result["risk_level"] = "HIGH" if report["count"] > 20 else "MEDIUM"
            result["community_reports"].append({
                "type": report["type"],
                "count": report["count"],
                "last_reported": report["last_reported"]
            })
        
        return result
    
    async def _execute_check_phone_tool(self, args: Dict) -> Dict:
        """Specialized tool for checking phone numbers against scam database"""
        phone = args.get("phone_number")
        
        if not phone:
            return {
                "error": "Phone number required",
                "is_scam": False
            }
        
        # Normalize phone number (simple version)
        normalized = phone.replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
        
        result = {
            "phone_number": phone,
            "normalized": normalized,
            "is_scam": False,
            "risk_level": "LOW",
            "report_count": 0,
            "scam_type": None,
            "recent_reports": []
        }
        
        # Check community database
        if normalized in self.scam_database["reported_phones"]:
            report = self.scam_database["reported_phones"][normalized]
            result["is_scam"] = True
            result["risk_level"] = "HIGH" if report["count"] > 5 else "MEDIUM"
            result["report_count"] = report["count"]
            result["scam_type"] = report["type"]
            result["recent_reports"].append({
                "date": report["last_reported"],
                "type": report["type"]
            })
        
        # Add recommendations
        if result["is_scam"]:
            result["recommendations"] = [
                "Do NOT answer calls from this number",
                "Block this number immediately",
                "Tell family members about this scam attempt",
                "Report to FTC at reportfraud.ftc.gov"
            ]
        else:
            result["recommendations"] = [
                "No reports found for this number",
                "Still be cautious - scammers use new numbers constantly",
                "Trust your instincts - if something feels wrong, hang up"
            ]
        
        return result
    
    async def _execute_report_scam_tool(self, args: Dict) -> Dict:
        """Tool for reporting scams to community database"""
        phone = args.get("phone_number")
        email = args.get("email")
        url = args.get("url")
        scam_type = args.get("scam_type", "other")
        description = args.get("description", "")
        
        report_id = f"report_{datetime.utcnow().timestamp()}"
        
        # Add to community database
        if phone:
            if phone not in self.scam_database["reported_phones"]:
                self.scam_database["reported_phones"][phone] = {
                    "count": 0,
                    "type": scam_type,
                    "last_reported": datetime.utcnow().isoformat()
                }
            self.scam_database["reported_phones"][phone]["count"] += 1
            self.scam_database["reported_phones"][phone]["last_reported"] = datetime.utcnow().isoformat()
        
        if url:
            if url not in self.scam_database["reported_urls"]:
                self.scam_database["reported_urls"][url] = {
                    "count": 0,
                    "type": scam_type,
                    "last_reported": datetime.utcnow().isoformat()
                }
            self.scam_database["reported_urls"][url]["count"] += 1
            self.scam_database["reported_urls"][url]["last_reported"] = datetime.utcnow().isoformat()
        
        if email:
            if email not in self.scam_database["reported_emails"]:
                self.scam_database["reported_emails"][email] = {
                    "count": 0,
                    "type": scam_type,
                    "last_reported": datetime.utcnow().isoformat()
                }
            self.scam_database["reported_emails"][email]["count"] += 1
            self.scam_database["reported_emails"][email]["last_reported"] = datetime.utcnow().isoformat()
        
        return {
            "report_id": report_id,
            "success": True,
            "message": "Thank you for reporting this scam. Your report helps protect others in the community.",
            "reported_items": {
                "phone": phone,
                "email": email,
                "url": url
            },
            "scam_type": scam_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # NEW: Live Threat Feed Tool Implementation
    async def _execute_threat_feed_tool(self, args: Dict) -> Dict:
        """
        Execute threat feed tool to get real-time scam intelligence
        Gemini Recommendation #3: Live threat intelligence
        """
        threat_type = args.get("threat_type", "all")
        limit = args.get("limit", 10)
        severity_filter = args.get("severity", "all")
        
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "threat_type": threat_type,
            "total_threats": 0,
            "threats": [],
            "current_tactics": [],
            "recommendations": [],
            "data_source": "Live Threat Intelligence Feed (simulated)"
        }
        
        # Add threats based on type
        if threat_type in ["phishing", "all"]:
            for threat in self.threat_feed["phishing"][:limit]:
                result["threats"].append({
                    "type": "phishing",
                    "url": threat["url"],
                    "reported": threat["reported"],
                    "source": threat["source"],
                    "confidence": threat["confidence"],
                    "active": threat["active"]
                })
        
        if threat_type in ["phone", "all"]:
            for threat in self.threat_feed["phone_scams"][:limit]:
                result["threats"].append({
                    "type": "phone_scam",
                    "number": threat["number"],
                    "scam_type": threat["type"],
                    "reports": threat["reports"],
                    "active": threat["active"],
                    "first_seen": threat["first_seen"]
                })
        
        if threat_type in ["email", "all"]:
            for threat in self.threat_feed["email_scams"][:limit]:
                result["threats"].append({
                    "type": "email_scam",
                    "domain": threat["domain"],
                    "impersonating": threat["impersonating"],
                    "reports": threat["reports"],
                    "first_seen": threat["first_seen"]
                })
        
        if threat_type in ["tactics", "all"]:
            for tactic in self.threat_feed["current_tactics"]:
                if severity_filter == "all" or tactic["severity"] == severity_filter:
                    result["current_tactics"].append({
                        "name": tactic["name"],
                        "description": tactic["description"],
                        "first_seen": tactic["first_seen"],
                        "severity": tactic["severity"]
                    })
        
        # Calculate total
        result["total_threats"] = len(result["threats"])
        
        # Add contextual recommendations based on threats
        if result["total_threats"] > 0:
            result["recommendations"] = [
                "⚠️ Be extremely cautious of unsolicited messages claiming urgent action",
                "📞 Verify any calls claiming to be from banks/government by calling official numbers",
                "🔗 Never click links in messages - type URLs manually",
                "👪 Always verify with family before sending money or sharing information",
                "📱 Report suspicious numbers to the FTC at reportfraud.ftc.gov"
            ]
            
            # Add specific recommendations based on threat types
            if any(t.get("type") == "phone_scam" for t in result["threats"]):
                result["recommendations"].insert(0, "📵 New phone scams detected - screen unknown calls")
            
            if any(t.get("type") == "phishing" for t in result["threats"]):
                result["recommendations"].insert(0, "📧 New phishing campaigns detected - check email carefully")
        
        return result
    
    async def add_message(
        self,
        context_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Message:
        """Add a message to context window"""
        if context_id not in self.contexts:
            raise ValueError(f"Context {context_id} not found")
        
        context = self.contexts[context_id]
        
        estimated_tokens = len(content) // 4
        
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat(),
            tokens=estimated_tokens,
            metadata=metadata or {}
        )
        
        if context.current_tokens + estimated_tokens > context.max_tokens - self.reserved_tokens:
            await self._prune_context(context_id)
        
        context.messages.append(message)
        context.current_tokens += estimated_tokens
        context.last_updated = datetime.utcnow().isoformat()
        
        self.context_stats[context_id]["messages_added"] += 1
        self.context_stats[context_id]["tokens_processed"] += estimated_tokens
        
        return message
    
    async def get_formatted_messages(
        self,
        context_id: str,
        include_system: bool = True,
        max_messages: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """Get messages formatted for API"""
        if context_id not in self.contexts:
            return []
        
        context = self.contexts[context_id]
        formatted = []
        
        if include_system and context.system_prompt:
            formatted.append({
                "role": "system",
                "content": context.system_prompt
            })
        
        messages = context.messages
        if max_messages:
            messages = messages[-max_messages:]
        
        for msg in messages:
            formatted.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return formatted
    
    async def _prune_context(self, context_id: str):
        """Prune oldest messages to free up space"""
        if context_id not in self.contexts:
            return
        
        context = self.contexts[context_id]
        
        target_tokens = context.max_tokens - self.reserved_tokens
        current_tokens = context.current_tokens
        
        if current_tokens <= target_tokens:
            return
        
        tokens_to_remove = current_tokens - target_tokens
        removed_tokens = 0
        messages_to_keep = []
        
        for msg in reversed(context.messages):
            if removed_tokens < tokens_to_remove:
                removed_tokens += msg.tokens
            else:
                messages_to_keep.insert(0, msg)
        
        context.messages = messages_to_keep
        context.current_tokens = current_tokens - removed_tokens
        
        self.context_stats[context_id]["prunes_performed"] += 1
        
        logger.info(f"Pruned context {context_id}, removed {removed_tokens} tokens")
    
    async def get_context_stats(self, context_id: str) -> Dict[str, Any]:
        """Get statistics for a context"""
        return self.context_stats.get(context_id, {})
    
    async def cleanup_old_contexts(self, max_age_hours: int = 24):
        """Remove contexts older than max_age"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        to_delete = []
        for context_id, context in self.contexts.items():
            last_updated = datetime.fromisoformat(context.last_updated)
            if last_updated < cutoff:
                to_delete.append(context_id)
        
        for context_id in to_delete:
            del self.contexts[context_id]
            if context_id in self.context_stats:
                del self.context_stats[context_id]
        
        logger.info(f"Cleaned up {len(to_delete)} old contexts")
    
    async def health_check(self) -> bool:
        """Check if service is healthy"""
        return self.is_healthy
    
    # ========== ADD THIS METHOD FOR HACKATHON SHOWCASE ==========
    async def get_stats(self) -> Dict[str, Any]:
        """Get MCP statistics for dashboard - SHOWCASE FOR JUDGES"""
        # Calculate average messages in contexts
        avg_messages = 0
        if self.contexts:
            total_messages = sum(len(c.messages) for c in self.contexts.values())
            avg_messages = total_messages / len(self.contexts) if self.contexts else 0
        
        return {
            "tools": {
                "total": len(self.tools),
                "list": list(self.tools.keys()),
                "calls": {
                    "total": getattr(self, 'tool_calls', 0),
                    "by_tool": getattr(self, 'tool_stats', {})
                }
            },
            "contexts": {
                "active": len(self.contexts),
                "total_created": len(self.contexts),
                "avg_messages": round(avg_messages, 1)
            },
            "protocol_version": "1.0",
            "timestamp": datetime.utcnow().isoformat()
        }