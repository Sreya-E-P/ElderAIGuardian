"""
Microsoft Agent Framework - Supervisor Agent
Implements sophisticated multi-agent orchestration using the official Microsoft Agent Framework
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from azure.ai.agents import AIAgentClient, AgentGroupChat, ChatClientAgent
from azure.ai.agents.models import Agent, AgentThread, Message, ToolCall
from azure.ai.projects import AIProjectClient
from azure.ai.inference.models import UserMessage, AssistantMessage, SystemMessage
from azure.identity import DefaultAzureCredential

from app.core.logging import logger
from app.core.config import settings
from app.services.mcp.mcp_server import MCPServer
from app.services.devops.self_healing_agent import SelfHealingAgent

class MicrosoftSupervisorAgent:
    """
    Advanced multi-agent supervisor using Microsoft Agent Framework
    Implements A2A (Agent-to-Agent) communication protocol
    """
    
    def __init__(self):
        self.project_client = AIProjectClient(
            endpoint=settings.AZURE_FOUNDRY_ENDPOINT,
            credential=DefaultAzureCredential(),
            project_name=settings.AZURE_FOUNDRY_PROJECT
        )
        self.agents: Dict[str, Agent] = {}
        self.group_chat: Optional[AgentGroupChat] = None
        self.threads: Dict[str, AgentThread] = {}
        self.is_initialized = False
        self.mcp_server = MCPServer()
        self.healing_agent = SelfHealingAgent()
        
    async def initialize(self):
        """Initialize all agents in Microsoft Agent Framework"""
        try:
            logger.info("🚀 Initializing Microsoft Agent Framework...")
            
            # Create specialized agents in Foundry
            await self._create_scam_agent()
            await self._create_emergency_agent()
            await self._create_medication_agent()
            await self._create_wellness_agent()
            await self._create_family_notification_agent()
            
            # Create Supervisor Agent (Group Chat Manager)
            supervisor_config = {
                "name": "elder-supervisor",
                "model": "gpt-4o",
                "instructions": """You are the Supervisor Agent in a multi-agent elderly care system.
                Your responsibilities:
                1. Analyze incoming messages to determine intent
                2. Route tasks to specialized agents using A2A protocol
                3. Coordinate agent collaboration for complex scenarios
                4. Ensure safety and escalation protocols are followed
                5. Maintain context across agent interactions
                
                When a scam is detected, coordinate with Family Notification Agent.
                For emergencies, immediately trigger Emergency Agent and notify family.
                For medication queries, collaborate with Medication Agent.
                Always prioritize user safety above all else.
                """,
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "route_to_agent",
                            "description": "Route a task to a specialized agent",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "agent_name": {"type": "string"},
                                    "task": {"type": "string"},
                                    "priority": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "URGENT"]}
                                }
                            }
                        }
                    }
                ]
            }
            
            supervisor = await self.project_client.agents.create_agent(**supervisor_config)
            self.agents["supervisor"] = supervisor
            
            # Create Agent Group Chat for multi-agent collaboration
            self.group_chat = AgentGroupChat(
                agents=list(self.agents.values()),
                supervisor_agent=supervisor,
                termination_condition=self._termination_condition,
                selector=RoundRobinSelector()  # or use DynamicSelector based on task
            )
            
            self.is_initialized = True
            logger.info(f"✅ Initialized {len(self.agents)} agents in Microsoft Agent Framework")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Microsoft Agent Framework: {str(e)}")
            raise
    
    async def _create_scam_agent(self):
        """Create Scam Detection Agent in Foundry"""
        scam_config = {
            "name": "scam-detector",
            "model": "gpt-4o",
            "instructions": """You are a specialized scam detection agent for elderly protection.
            Analyze messages for:
            1. Phishing URLs and suspicious links
            2. Social engineering patterns
            3. Urgency tactics and fear manipulation
            4. Requests for personal/financial information
            5. Known scam patterns from MCP databases
            
            Use MCP tools to check URLs against threat intelligence.
            Return JSON with:
            - is_scam (boolean)
            - risk_score (0-10)
            - confidence (0-1)
            - risk_factors (list)
            - detected_urls (list)
            - recommendations (list)
            
            For high-risk detections, collaborate with Family Notification Agent.
            """,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "check_url_mcp",
                        "description": "Check URL against threat intelligence via MCP",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"}
                            }
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "notify_family",
                        "description": "Notify family about scam detection",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "user_id": {"type": "string"},
                                "risk_level": {"type": "string"}
                            }
                        }
                    }
                }
            ]
        }
        
        agent = await self.project_client.agents.create_agent(**scam_config)
        self.agents["scam_detection"] = agent
        logger.info("  ✅ Scam Detection Agent created")
    
    async def _create_emergency_agent(self):
        """Create Emergency Response Agent"""
        emergency_config = {
            "name": "emergency-responder",
            "model": "gpt-4o",
            "instructions": """You are an emergency response agent for elderly care.
            Handle:
            1. Fall detection from sensor data
            2. Medical emergencies (heart attack, stroke, etc.)
            3. Fire and security threats
            4. SOS triggers
            
            For every emergency:
            1. Assess severity (CRITICAL/HIGH/MEDIUM/LOW)
            2. Notify emergency services if CRITICAL
            3. Alert all family contacts immediately
            4. Provide real-time instructions to user
            5. Track resolution status
            
            Use MCP tools for location services and emergency contacts.
            """,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "notify_emergency_services",
                        "description": "Contact 911 or local emergency services",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "object"},
                                "emergency_type": {"type": "string"},
                                "severity": {"type": "string"}
                            }
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "detect_fall",
                        "description": "Analyze sensor data for fall detection",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "sensor_data": {"type": "array"}
                            }
                        }
                    }
                }
            ]
        }
        
        agent = await self.project_client.agents.create_agent(**emergency_config)
        self.agents["emergency"] = agent
        logger.info("  ✅ Emergency Response Agent created")
    
    async def _create_medication_agent(self):
        """Create Medication Management Agent"""
        medication_config = {
            "name": "medication-manager",
            "model": "gpt-4o",
            "instructions": """You are a medication management agent.
            Responsibilities:
            1. Track medication schedules
            2. Send reminders at appropriate times
            3. Monitor adherence rates
            4. Detect missed doses
            5. Check for refill needs
            6. Identify potential drug interactions
            
            Use MCP to check pharmacy inventory and drug databases.
            Notify family when adherence drops below 70%.
            """,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "check_pharmacy_mcp",
                        "description": "Check medication availability at pharmacy",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "medication_name": {"type": "string"}
                            }
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "schedule_reminder",
                        "description": "Schedule a medication reminder",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "user_id": {"type": "string"},
                                "medication": {"type": "string"},
                                "time": {"type": "string"}
                            }
                        }
                    }
                }
            ]
        }
        
        agent = await self.project_client.agents.create_agent(**medication_config)
        self.agents["medication"] = agent
        logger.info("  ✅ Medication Management Agent created")
    
    async def _create_wellness_agent(self):
        """Create Wellness Monitoring Agent"""
        wellness_config = {
            "name": "wellness-monitor",
            "model": "gpt-4o",
            "instructions": """You are a wellness monitoring agent.
            Track:
            1. Mood and emotional state
            2. Physical activity levels
            3. Sleep quality and duration
            4. Hydration and nutrition
            5. Social engagement
            
            Provide personalized wellness tips.
            Detect concerning patterns (prolonged low mood, inactivity).
            Collaborate with Family Notification Agent for concerns.
            
            Use MCP for weather-based activity recommendations.
            """,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather_mcp",
                        "description": "Get weather data for activity recommendations",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string"}
                            }
                        }
                    }
                }
            ]
        }
        
        agent = await self.project_client.agents.create_agent(**wellness_config)
        self.agents["wellness"] = agent
        logger.info("  ✅ Wellness Monitoring Agent created")
    
    async def _create_family_notification_agent(self):
        """Create Family Notification Agent"""
        notification_config = {
            "name": "family-notifier",
            "model": "gpt-4o",
            "instructions": """You are the family notification agent.
            Responsibilities:
            1. Send intelligent notifications to family members
            2. Determine notification priority based on urgency
            3. Multi-channel delivery (SMS, email, push, call)
            4. Track delivery and read receipts
            5. Escalate if no response
            
            Priority levels:
            - URGENT: Emergency situations - call + SMS immediately
            - HIGH: Scam alerts, missed medications - SMS + push
            - MEDIUM: Wellness updates, adherence reports - push + email
            - LOW: Daily summaries, tips - push only
            
            Use Azure Communication Services for delivery.
            """,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "send_sms",
                        "description": "Send SMS notification",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "to": {"type": "string"},
                                "message": {"type": "string"}
                            }
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "make_call",
                        "description": "Make automated call",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "to": {"type": "string"},
                                "message": {"type": "string"}
                            }
                        }
                    }
                }
            ]
        }
        
        agent = await self.project_client.agents.create_agent(**notification_config)
        self.agents["family_notification"] = agent
        logger.info("  ✅ Family Notification Agent created")
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process user message through multi-agent collaboration
        Implements A2A (Agent-to-Agent) protocol
        """
        start_time = datetime.utcnow()
        request_id = f"req_{user_id}_{start_time.timestamp()}"
        
        try:
            # Create or get thread for this session
            thread = await self._get_or_create_thread(session_id or user_id)
            
            # Add user message to thread
            await self.project_client.agents.add_message(
                thread_id=thread.id,
                role="user",
                content=message,
                metadata={"user_id": user_id, **metadata} if metadata else {"user_id": user_id}
            )
            
            # Run the group chat (multi-agent collaboration)
            result = await self.group_chat.run(
                thread_id=thread.id,
                max_iterations=10,  # Prevent infinite loops
                temperature=0.7
            )
            
            # Extract agent responses
            responses = []
            for step in result.steps:
                responses.append({
                    "agent": step.agent_name,
                    "content": step.response.content,
                    "confidence": step.metadata.get("confidence", 1.0),
                    "tool_calls": step.tool_calls if hasattr(step, 'tool_calls') else []
                })
            
            # Build final response
            final_response = self._build_final_response(responses)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "request_id": request_id,
                "session_id": session_id,
                "type": "agent_response",
                "responses": responses,
                "final_response": final_response,
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_ms": processing_time,
                "agents_involved": [r["agent"] for r in responses],
                "thread_id": thread.id
            }
            
        except Exception as e:
            logger.error(f"❌ Agent processing failed: {str(e)}")
            
            # Self-healing attempt
            await self.healing_agent.report_error(
                component="supervisor_agent",
                error=str(e),
                context={"user_id": user_id, "message": message[:100]}
            )
            
            return {
                "request_id": request_id,
                "type": "error",
                "error": "I'm having trouble processing your request. Please try again.",
                "error_details": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_or_create_thread(self, session_id: str) -> AgentThread:
        """Get existing thread or create new one"""
        if session_id in self.threads:
            return self.threads[session_id]
        
        thread = await self.project_client.agents.create_thread(
            metadata={"session_id": session_id}
        )
        self.threads[session_id] = thread
        return thread
    
    async def _termination_condition(self, context: Dict) -> bool:
        """Determine when agent collaboration should stop"""
        # Stop if:
        # 1. Emergency handled
        # 2. User acknowledged
        # 3. Max iterations reached
        # 4. All agents have responded
        
        if context.get("emergency_handled"):
            return True
        
        if context.get("user_acknowledged"):
            return True
        
        if context.get("iteration_count", 0) >= 10:
            return True
        
        return False
    
    def _build_final_response(self, responses: List[Dict]) -> str:
        """Build cohesive final response from multiple agent responses"""
        if not responses:
            return "I'm here to help. How can I assist you today?"
        
        # Prioritize emergency responses
        emergency_responses = [r for r in responses if "emergency" in r.get("agent", "").lower()]
        if emergency_responses:
            return emergency_responses[0]["content"]
        
        # Combine responses naturally
        combined = []
        for response in responses:
            agent_name = response["agent"].replace("-", " ").title()
            combined.append(response["content"])
        
        return " ".join(combined)
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        status = {}
        for name, agent in self.agents.items():
            status[name] = {
                "id": agent.id,
                "name": agent.name,
                "status": "healthy" if agent else "unknown",
                "threads": len([t for t in self.threads.values() if t.agent_id == agent.id])
            }
        return status
    
    async def close(self):
        """Clean up resources"""
        for thread in self.threads.values():
            try:
                await self.project_client.agents.delete_thread(thread.id)
            except:
                pass
        
        for agent in self.agents.values():
            try:
                await self.project_client.agents.delete_agent(agent.id)
            except:
                pass
        
        await self.mcp_server.close()
        logger.info("✅ Microsoft Agent Framework shut down")