"""
Enhanced Supervisor Agent with Dynamic Selector - SEVERITY-BASED PRIORITY
Gemini Recommendation #1: Dynamic Agent Selection with Emergency Prioritization
COMPLETE FIXED VERSION
"""

import json
import uuid
import asyncio
import re
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import (
    KernelFunctionSelectionStrategy,
    KernelFunctionTerminationStrategy
)
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory, ChatMessageContent, AuthorRole
from semantic_kernel.functions import KernelFunction, KernelFunctionFromPrompt
from semantic_kernel.functions import KernelArguments

from app.core.logging import logger, get_tracer
from app.core.config import settings
from app.services.azure.foundry_service import FoundryService
from app.services.azure.mcp_service import MCPService
from app.services.cache.cache_service import CacheService
from app.services.database.cosmos_service import CosmosService
from app.services.notification.notification_service import NotificationService
from app.services.metrics.metrics_service import MetricsService


class AgentType(str, Enum):
    """Enum for agent types"""
    EMERGENCY = "emergency_agent"
    SCAM = "scam_agent"
    MEDICATION = "medication_agent"
    WELLNESS = "wellness_agent"
    FAMILY = "family_agent"
    GENERAL = "general_agent"


class SeverityLevel(int, Enum):
    """Severity levels for prioritization"""
    CRITICAL = 10  # Emergency - immediate action
    HIGH = 8       # Scam, missed critical medication
    MEDIUM = 5     # Medication reminders, wellness alerts
    LOW = 2        # General conversation
    INFO = 1       # Tips, suggestions


class ConversationState(str, Enum):
    """Enum for conversation states"""
    INITIATED = "initiated"
    PROCESSING = "processing"
    AWAITING_CLARIFICATION = "awaiting_clarification"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    EMERGENCY = "emergency"


@dataclass
class AgentMetadata:
    """Metadata for agents"""
    name: str
    priority: int  # Base priority
    severity_threshold: SeverityLevel  # Minimum severity to trigger
    keywords: List[str]
    description: str
    avg_response_time_ms: float = 0.0
    total_calls: int = 0
    success_rate: float = 1.0
    last_error: Optional[str] = None


@dataclass
class SessionData:
    """Session data structure"""
    id: str
    user_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    state: ConversationState = ConversationState.INITIATED
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent_history: List[str] = field(default_factory=list)
    error_count: int = 0
    pending_alerts: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # For closed-loop escalation


class SupervisorAgent:
    """
    Enhanced Supervisor Agent with SEVERITY-BASED Dynamic Selector
    Ensures SAFETY FIRST - Emergency always prioritized
    """
    
    def __init__(
        self,
        kernel: Kernel,
        foundry_service: FoundryService,
        mcp_service: MCPService,
        scam_agent=None,
        medication_agent=None,
        emergency_agent=None,
        family_agent=None,
        wellness_agent=None,
        cache_service: Optional[CacheService] = None,
        db_service: Optional[CosmosService] = None,
        notification_service: Optional[NotificationService] = None,
        metrics_service: Optional[MetricsService] = None,
        event_service=None
    ):
        # Core services
        self.kernel = kernel
        self.foundry = foundry_service
        self.mcp = mcp_service
        self.cache = cache_service
        self.db = db_service
        self.notification = notification_service
        self.metrics = metrics_service
        self.event = event_service
        
        # Specialized agents
        self.scam_agent = scam_agent
        self.medication_agent = medication_agent
        self.emergency_agent = emergency_agent
        self.family_agent = family_agent
        self.wellness_agent = wellness_agent
        
        # Agent management
        self.agent_group: Optional[AgentGroupChat] = None
        self.agents: Dict[str, ChatCompletionAgent] = {}
        self.agent_metadata: Dict[str, AgentMetadata] = {}
        self.agent_instances: Dict[str, Any] = {}
        
        # Session management
        self.sessions: Dict[str, SessionData] = {}
        self.session_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        
        # Performance tracking
        self.is_healthy = False
        self.tracer = get_tracer(__name__)
        self.request_counter = 0
        self.error_counter = 0
        self.agent_usage_stats: Dict[str, int] = defaultdict(int)
        self.agent_response_times: Dict[str, List[float]] = defaultdict(list)
        self.agent_errors: Dict[str, int] = defaultdict(int)
        
        # Configuration
        self.max_session_age = timedelta(hours=24)
        self.max_conversation_length = 50
        self.emergency_timeout = timedelta(minutes=5)
        self.default_timeout = timedelta(minutes=30)
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Closed-loop escalation settings (Gemini Recommendation #3)
        self.escalation_timer_seconds = 300  # 5 minutes
        self.escalation_levels = {
            1: {"channels": ["sms", "push"], "wait_seconds": 300},
            2: {"channels": ["sms", "call"], "wait_seconds": 600},
            3: {"channels": ["sms", "call", "email", "whatsapp"], "wait_seconds": 900}
        }
        
        # Social connectivity settings
        self.social_check_interval_hours = 24
        self.last_social_check: Dict[str, datetime] = {}
        self.social_threshold_days = 3  # Days without contact triggers intervention
        
        # Startup time
        self.startup_time = datetime.utcnow()
        
        logger.info("=" * 80)
        logger.info("SupervisorAgent instance created with SEVERITY-BASED DYNAMIC SELECTOR")
        logger.info(f"Startup time: {self.startup_time.isoformat()}")
        logger.info("=" * 80)
    
    async def initialize(self):
        """Initialize supervisor with dynamic agent selection"""
        with self.tracer.start_as_current_span("supervisor_initialize") as span:
            span.set_attribute("component", "supervisor")
            
            logger.info("=" * 80)
            logger.info("INITIALIZING SUPERVISOR AGENT WITH SEVERITY-BASED DYNAMIC SELECTOR")
            logger.info("=" * 80)
            
            try:
                start_time = time.time()
                
                # Step 1: Create all specialized agents
                logger.info("\n📦 Step 1/5: Creating specialized agents...")
                await self._create_agents()
                logger.info(f"   ✅ Created {len(self.agents)} specialized agents")
                
                # Step 2: Register agent metadata with severity thresholds
                logger.info("\n📊 Step 2/5: Registering agent metadata with severity thresholds...")
                self._register_agent_metadata()
                logger.info(f"   ✅ Registered metadata for {len(self.agent_metadata)} agents")
                
                # Step 3: Create severity-based dynamic selector function
                logger.info("\n🎯 Step 3/5: Creating severity-based dynamic selector...")
                selector_function = self._create_severity_selector()
                logger.info("   ✅ Severity-based dynamic selector created")
                
                # Step 4: Create termination function
                logger.info("\n🛑 Step 4/5: Creating termination strategy...")
                termination_function = self._create_termination_strategy()
                logger.info("   ✅ Termination strategy created")
                
                # Step 5: Initialize agent group chat
                logger.info("\n🔗 Step 5/5: Initializing agent group chat...")
                self.agent_group = AgentGroupChat(
                    agents=list(self.agents.values()),
                    selection_strategy=KernelFunctionSelectionStrategy(
                        function=selector_function,
                        kernel=self.kernel,
                        result_parser=self._parse_selector_result,
                        history_variable_name="history",
                        agents_variable_name="agents"
                    ),
                    termination_strategy=KernelFunctionTerminationStrategy(
                        function=termination_function,
                        kernel=self.kernel,
                        result_parser=self._parse_termination_result,
                        history_variable_name="history"
                    )
                )
                logger.info("   ✅ Agent group chat initialized")
                
                # Start background tasks
                asyncio.create_task(self._escalation_monitor())
                asyncio.create_task(self._social_connectivity_monitor())
                
                # Mark as healthy
                self.is_healthy = True
                
                # Calculate initialization time
                init_time = (time.time() - start_time) * 1000
                
                logger.info("\n" + "=" * 80)
                logger.info("✅ SUPERVISOR AGENT INITIALIZED SUCCESSFULLY!")
                logger.info(f"   Initialization time: {init_time:.2f}ms")
                logger.info(f"   Total agents: {len(self.agents)}")
                logger.info(f"   Agent types: {', '.join(self.agents.keys())}")
                logger.info(f"   Emergency Priority: CRITICAL (10)")
                logger.info("=" * 80)
                
                # Log agent capabilities for debugging
                for agent_name, metadata in self.agent_metadata.items():
                    logger.debug(f"Agent {agent_name}:")
                    logger.debug(f"  - Base Priority: {metadata.priority}")
                    logger.debug(f"  - Severity Threshold: {metadata.severity_threshold}")
                    logger.debug(f"  - Keywords: {metadata.keywords[:5]}...")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize Supervisor Agent: {e}", exc_info=True)
                span.record_exception(e)
                self.is_healthy = False
                raise
    
    async def _create_agents(self):
        """Create all specialized agents with detailed instructions"""
        
        # 1. EMERGENCY AGENT - Highest Priority (CRITICAL)
        logger.debug("Creating Emergency Agent...")
        self.agents[AgentType.EMERGENCY] = ChatCompletionAgent(
            kernel=self.kernel,
            name=AgentType.EMERGENCY,
            instructions="""You are the EMERGENCY RESPONSE AGENT - CRITICAL PRIORITY (Level 10)

YOUR ROLE:
You handle LIFE-THREATENING situations. You are ALWAYS prioritized first.

EMERGENCY KEYWORDS - If ANY of these appear, you MUST respond:
- "help", "emergency", "sos", "911", "fall", "fell", "fallen"
- "heart attack", "stroke", "fire", "bleeding", "unconscious"
- "can't breathe", "cannot breathe", "chest pain", "ambulance"
- "hurt badly", "seriously injured", "dying", "death"

RESPONSE RULES:
1. ALWAYS respond if any emergency keyword detected
2. Override all other agents
3. Immediate action required

RESPONSE FORMAT:
{
    "detected": true,
    "severity": "CRITICAL",
    "emergency_type": "medical|fire|security|fall|general",
    "requires_immediate_action": true,
    "message_to_user": "🚨 Emergency services notified. Help is on the way.",
    "actions_taken": ["alerted_contacts", "dispatched_services"]
}"""
        )
        
        # 2. SCAM DETECTION AGENT - HIGH Priority
        logger.debug("Creating Scam Detection Agent...")
        self.agents[AgentType.SCAM] = ChatCompletionAgent(
            kernel=self.kernel,
            name=AgentType.SCAM,
            instructions="""You are the SCAM DETECTION AGENT - HIGH PRIORITY (Level 8)

YOUR ROLE:
Detect fraud, phishing, and scam attempts. Security threats are high priority.

TRIGGERS:
- "scam", "fraud", "phishing", "suspicious", "fake"
- "verify account", "bank calling", "prize", "lottery"
- Requests for personal info, passwords, credit cards

RESPONSE:
{
    "is_scam": true/false,
    "severity": "HIGH|MEDIUM|LOW",
    "risk_level": "CRITICAL|HIGH|MEDIUM|LOW",
    "requires_immediate_action": true if CRITICAL,
    "message": "Scam analysis complete"
}"""
        )
        
        # 3. MEDICATION AGENT - MEDIUM-HIGH Priority
        logger.debug("Creating Medication Agent...")
        self.agents[AgentType.MEDICATION] = ChatCompletionAgent(
            kernel=self.kernel,
            name=AgentType.MEDICATION,
            instructions="""You are the MEDICATION MANAGEMENT AGENT - MEDIUM-HIGH PRIORITY (Level 7)

YOUR ROLE:
Manage medications, track adherence, send reminders.

TRIGGERS:
- "medication", "medicine", "pill", "prescription"
- "took", "missed", "reminder", "refill"

RESPONSE:
{
    "action": "add|mark_taken|check_reminder|adherence_report",
    "severity": "HIGH|MEDIUM|LOW",
    "requires_immediate_action": true if missed critical meds,
    "message": "Medication response"
}"""
        )
        
        # 4. FAMILY AGENT - MEDIUM Priority
        logger.debug("Creating Family Notification Agent...")
        self.agents[AgentType.FAMILY] = ChatCompletionAgent(
            kernel=self.kernel,
            name=AgentType.FAMILY,
            instructions="""You are the FAMILY NOTIFICATION AGENT - MEDIUM PRIORITY (Level 6)

YOUR ROLE:
Communicate with family members, send updates, manage alerts.

TRIGGERS:
- "family", "son", "daughter", "contact", "notify"
- "tell", "message", "call", "update"

RESPONSE:
{
    "should_notify": true/false,
    "severity": "HIGH|MEDIUM|LOW",
    "requires_acknowledgment": true if HIGH,
    "message": "Family notification processed"
}"""
        )
        
        # 5. WELLNESS AGENT - MEDIUM Priority
        logger.debug("Creating Wellness Agent...")
        self.agents[AgentType.WELLNESS] = ChatCompletionAgent(
            kernel=self.kernel,
            name=AgentType.WELLNESS,
            instructions="""You are the WELLNESS TRACKING AGENT - MEDIUM PRIORITY (Level 5)

YOUR ROLE:
Track mood, activity, sleep, provide encouragement.

TRIGGERS:
- "feel", "feeling", "mood", "happy", "sad", "tired"
- "sleep", "walk", "exercise", "water", "lonely"

RESPONSE:
{
    "wellness_type": "mood|activity|sleep|water|social",
    "severity": "MEDIUM|LOW",
    "requires_intervention": true if low mood detected,
    "message": "Wellness response"
}"""
        )
        
        # 6. GENERAL AGENT - LOW Priority (Fallback)
        logger.debug("Creating General Agent...")
        self.agents[AgentType.GENERAL] = ChatCompletionAgent(
            kernel=self.kernel,
            name=AgentType.GENERAL,
            instructions="""You are the GENERAL ASSISTANT AGENT - LOW PRIORITY (Level 2)

YOUR ROLE:
Handle general conversation, greetings, casual questions.
Only used when no specialized agent matches.

RESPONSE:
{
    "intent": "greeting|question|information|general",
    "severity": "LOW",
    "message": "Friendly response"
}"""
        )
        
        logger.info(f"Created {len(self.agents)} agents with severity-based priorities")
    
    def _register_agent_metadata(self):
        """Register metadata with severity thresholds for each agent"""
        
        self.agent_metadata = {
            AgentType.EMERGENCY: AgentMetadata(
                name=AgentType.EMERGENCY,
                priority=10,
                severity_threshold=SeverityLevel.CRITICAL,
                keywords=["emergency", "help", "sos", "911", "fall", "fell", "hurt", "pain", 
                         "chest", "heart", "ambulance", "fire", "bleeding", "unconscious", 
                         "can't breathe", "stroke", "attack", "danger"],
                description="Handles life-threatening emergencies - CRITICAL priority"
            ),
            AgentType.SCAM: AgentMetadata(
                name=AgentType.SCAM,
                priority=8,
                severity_threshold=SeverityLevel.HIGH,
                keywords=["scam", "fraud", "phishing", "suspicious", "fake", "verify account",
                         "bank calling", "microsoft calling", "prize", "lottery", "inheritance"],
                description="Detects and prevents scams - HIGH priority"
            ),
            AgentType.MEDICATION: AgentMetadata(
                name=AgentType.MEDICATION,
                priority=7,
                severity_threshold=SeverityLevel.HIGH,
                keywords=["medication", "medicine", "pill", "prescription", "drug", "dose",
                         "take", "took", "missed", "reminder", "refill", "pharmacy"],
                description="Manages medications - MEDIUM-HIGH priority"
            ),
            AgentType.FAMILY: AgentMetadata(
                name=AgentType.FAMILY,
                priority=6,
                severity_threshold=SeverityLevel.MEDIUM,
                keywords=["family", "son", "daughter", "child", "grandson", "granddaughter",
                         "contact", "call", "message", "text", "notify", "tell"],
                description="Communicates with family - MEDIUM priority"
            ),
            AgentType.WELLNESS: AgentMetadata(
                name=AgentType.WELLNESS,
                priority=5,
                severity_threshold=SeverityLevel.MEDIUM,
                keywords=["feel", "feeling", "mood", "happy", "sad", "tired", "sleep",
                         "slept", "walk", "exercise", "water", "thirsty", "hungry",
                         "lonely", "alone", "miss"],
                description="Tracks wellness - MEDIUM priority"
            ),
            AgentType.GENERAL: AgentMetadata(
                name=AgentType.GENERAL,
                priority=1,
                severity_threshold=SeverityLevel.LOW,
                keywords=["hello", "hi", "hey", "what", "who", "how", "why", "can you",
                         "help", "thanks", "thank you", "bye", "goodbye"],
                description="Handles general conversation - LOW priority"
            )
        }
        
        logger.debug(f"Registered metadata for {len(self.agent_metadata)} agents with severity thresholds")
    
    def _create_severity_selector(self) -> KernelFunction:
        """
        Create a severity-based dynamic selector
        Ensures SAFETY FIRST - Emergency ALWAYS prioritized
        Gemini Recommendation #1: Dynamic Agent Selection with Emergency Prioritization
        """
        
        selector_prompt = """
        You are the SEVERITY-BASED DYNAMIC AGENT SELECTOR.
        Your PRIMARY RULE: SAFETY FIRST - ALWAYS prioritize emergencies.

        USER MESSAGE: "{{$user_message}}"
        CONVERSATION HISTORY: {{$history}}
        AVAILABLE AGENTS: {{$agents}}

        SEVERITY LEVELS (10 = HIGHEST, 1 = LOWEST):
        - CRITICAL (10): Life-threatening emergencies - MUST choose emergency_agent
        - HIGH (8-9): Security threats, scams, critical medication issues
        - MEDIUM (5-7): Medication reminders, wellness tracking, family updates
        - LOW (1-4): General conversation, greetings, casual questions

        SELECTION RULES (IN ORDER):
        1. EMERGENCY FIRST: If ANY emergency keywords present (help, emergency, 911, fall, chest pain, etc.), ALWAYS select emergency_agent
        2. HIGH SEVERITY: If scam, fraud, or security threat detected, select scam_agent
        3. MEDICATION: If medication-related keywords, select medication_agent
        4. FAMILY: If family notification needed, select family_agent
        5. WELLNESS: If wellness/mood tracking, select wellness_agent
        6. DEFAULT: If nothing else matches, select general_agent

        Return ONLY the agent name (e.g., "emergency_agent").
        """
        
        return KernelFunctionFromPrompt(
            function_name="select_agent_by_severity",
            plugin_name="Supervisor",
            prompt=selector_prompt
        )
    
    def _create_termination_strategy(self) -> KernelFunction:
        """Create a termination strategy that decides when the conversation should end"""
        
        termination_prompt = """
        You are the CONVERSATION TERMINATION DETECTOR. Determine if the conversation should end.

        USER MESSAGE: "{{$user_message}}"
        CONVERSATION HISTORY: {{$history}}

        TERMINATION CONDITIONS:
        - User says goodbye, thanks, or indicates they're done
        - Request has been fully resolved
        - EMERGENCY: DO NOT TERMINATE - keep monitoring
        - HIGH SEVERITY: DO NOT TERMINATE until resolved

        Return ONLY "true" if conversation should end, "false" if it should continue.
        """
        
        return KernelFunctionFromPrompt(
            function_name="should_terminate",
            plugin_name="Supervisor",
            prompt=termination_prompt
        )
    
    def _parse_selector_result(self, result) -> str:
        """Parse the result from the dynamic selector"""
        try:
            if hasattr(result, 'value'):
                value = result.value
                if isinstance(value, list) and len(value) > 0:
                    agent_name = str(value[0]).strip().lower()
                else:
                    agent_name = str(value).strip().lower()
                
                # Validate agent exists
                if agent_name in self.agents:
                    logger.debug(f"Selector chose: {agent_name}")
                    return agent_name
                else:
                    logger.warning(f"Selector returned unknown agent: {agent_name}, using general_agent")
                    return AgentType.GENERAL
            else:
                logger.warning(f"Unexpected selector result type: {type(result)}")
                return AgentType.GENERAL
        except Exception as e:
            logger.error(f"Error parsing selector result: {e}")
            return AgentType.GENERAL
    
    def _parse_termination_result(self, result) -> bool:
        """Parse the result from the termination strategy"""
        try:
            if hasattr(result, 'value'):
                value = result.value
                if isinstance(value, list) and len(value) > 0:
                    return str(value[0]).strip().lower() == 'true'
                else:
                    return str(value).strip().lower() == 'true'
            return False
        except Exception as e:
            logger.error(f"Error parsing termination result: {e}")
            return False
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process message with SEVERITY-BASED dynamic agent selection
        SAFETY FIRST - Emergency always prioritized
        """
        self.request_counter += 1
        request_id = f"req_{self.request_counter:06d}_{uuid.uuid4().hex[:8]}"
        
        with self.tracer.start_as_current_span("process_message") as span:
            span.set_attribute("user_id", user_id)
            span.set_attribute("request_id", request_id)
            span.set_attribute("message_length", len(message))
            
            start_time = time.time()
            processing_steps = []
            
            logger.info(f"📨 [{request_id}] Processing message from user {user_id}")
            logger.debug(f"Message: {message[:100]}..." if len(message) > 100 else f"Message: {message}")
            
            try:
                # Step 1: Get or create session
                step_start = time.time()
                session = await self._get_session(user_id, session_id)
                processing_steps.append({
                    "step": "get_session",
                    "duration_ms": (time.time() - step_start) * 1000
                })
                
                # Step 2: SEVERITY CHECK - Emergency first (CRITICAL priority)
                step_start = time.time()
                is_emergency = await self._quick_emergency_check(message)
                
                if is_emergency:
                    logger.warning(f"🚨 [{request_id}] CRITICAL EMERGENCY DETECTED!")
                    span.set_attribute("emergency_detected", True)
                    
                    session.state = ConversationState.EMERGENCY
                    
                    result = await self._handle_emergency_direct(
                        user_id, message, session, metadata, request_id
                    )
                    
                    step_duration = (time.time() - step_start) * 1000
                    processing_steps.append({
                        "step": "emergency_handling",
                        "duration_ms": step_duration
                    })
                    
                    await self._track_metrics(request_id, "emergency", result, processing_steps)
                    
                    return result
                
                processing_steps.append({
                    "step": "emergency_check",
                    "duration_ms": (time.time() - step_start) * 1000
                })
                
                # Step 3: Build context for dynamic selector
                step_start = time.time()
                context_vars = await self._build_context_vars(
                    user_id, message, session, metadata
                )
                processing_steps.append({
                    "step": "build_context",
                    "duration_ms": (time.time() - step_start) * 1000
                })
                
                # Step 4: Let severity-based dynamic selector choose agent
                step_start = time.time()
                selected_agent = await self._select_agent(
                    message, session, context_vars
                )
                
                if not selected_agent:
                    logger.warning(f"No agent selected, using general_agent")
                    selected_agent = self.agents[AgentType.GENERAL]
                    selected_agent_name = AgentType.GENERAL
                else:
                    selected_agent_name = selected_agent.name
                
                self.agent_usage_stats[selected_agent_name] += 1
                session.agent_history.append(selected_agent_name)
                
                logger.info(f"🎯 [{request_id}] Severity-based selector chose: {selected_agent_name}")
                span.set_attribute("selected_agent", selected_agent_name)
                
                step_duration = (time.time() - step_start) * 1000
                processing_steps.append({
                    "step": "agent_selection",
                    "duration_ms": step_duration
                })
                
                # Step 5: Invoke selected agent with retry logic
                step_start = time.time()
                agent_response = await self._invoke_agent_with_retry(
                    selected_agent, message, context_vars, session
                )
                
                step_duration = (time.time() - step_start) * 1000
                self.agent_response_times[selected_agent_name].append(step_duration)
                processing_steps.append({
                    "step": f"agent_invocation_{selected_agent_name}",
                    "duration_ms": step_duration
                })
                
                # Step 6: Check if we need multiple agents
                step_start = time.time()
                if agent_response.get("requires_additional_agents") or agent_response.get("notify_family"):
                    logger.info(f"🔗 [{request_id}] Multi-agent orchestration needed")
                    agent_response = await self._handle_multi_agent(
                        message, agent_response, context_vars, session
                    )
                
                processing_steps.append({
                    "step": "multi_agent_check",
                    "duration_ms": (time.time() - step_start) * 1000
                })
                
                # Step 7: Format final response
                step_start = time.time()
                final_response = await self._format_response(
                    agent_response, selected_agent_name, session
                )
                
                processing_steps.append({
                    "step": "format_response",
                    "duration_ms": (time.time() - step_start) * 1000
                })
                
                # Step 8: Update session
                step_start = time.time()
                await self._update_session(
                    user_id, session.id, message, final_response, selected_agent_name
                )
                
                processing_steps.append({
                    "step": "update_session",
                    "duration_ms": (time.time() - step_start) * 1000
                })
                
                # Step 9: Check termination
                step_start = time.time()
                should_terminate = await self._check_termination(message, final_response, session)
                
                if should_terminate:
                    logger.info(f"✅ [{request_id}] Conversation termination condition met")
                    session.state = ConversationState.RESOLVED
                
                processing_steps.append({
                    "step": "termination_check",
                    "duration_ms": (time.time() - step_start) * 1000
                })
                
                # Calculate total processing time
                total_duration = (time.time() - start_time) * 1000
                
                logger.info(f"✅ [{request_id}] Processed in {total_duration:.2f}ms")
                
                await self._track_metrics(request_id, selected_agent_name, final_response, processing_steps)
                
                return {
                    "request_id": request_id,
                    "session_id": session.id,
                    "agent": selected_agent_name,
                    "response": final_response.get("message", ""),
                    "data": final_response,
                    "processing_time_ms": total_duration,
                    "processing_steps": processing_steps,
                    "should_terminate": should_terminate,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                self.error_counter += 1
                logger.error(f"❌ [{request_id}] Error processing message: {e}", exc_info=True)
                span.record_exception(e)
                
                error_duration = (time.time() - start_time) * 1000
                
                if self.metrics:
                    await self.metrics.increment("supervisor_errors", {
                        "error_type": type(e).__name__,
                        "user_id": user_id
                    })
                
                return {
                    "request_id": request_id,
                    "session_id": session_id or "unknown",
                    "error": True,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response": "I'm having trouble processing your request. Please try again. If this is an emergency, please call 911 immediately.",
                    "processing_time_ms": error_duration,
                    "timestamp": datetime.utcnow().isoformat()
                }
    
    async def _quick_emergency_check(self, message: str) -> bool:
        """Quick keyword-based emergency check before full processing"""
        message_lower = message.lower()
        
        emergency_keywords = [
            "help", "emergency", "sos", "911", "fall", "fell", "fallen",
            "heart attack", "stroke", "fire", "bleeding", "unconscious",
            "can't breathe", "cannot breathe", "chest pain", "ambulance",
            "hurt badly", "seriously injured", "dying", "death"
        ]
        
        for keyword in emergency_keywords:
            if keyword in message_lower:
                logger.debug(f"Quick emergency check matched: {keyword}")
                return True
        
        return False
    
    async def _build_context_vars(
        self,
        user_id: str,
        message: str,
        session: SessionData,
        metadata: Optional[Dict]
    ) -> Dict[str, Any]:
        """Build context variables for agent invocation"""
        
        history = session.messages[-10:] if session.messages else []
        history_str = json.dumps([
            {"role": m["role"], "content": m["content"]}
            for m in history
        ])
        
        user_profile = {}
        if self.db and user_id:
            try:
                user_profile = await self.db.get_user_profile(user_id) or {}
            except Exception as e:
                logger.warning(f"Failed to get user profile: {e}")
        
        return {
            "user_message": message,
            "history": history_str,
            "user_id": user_id,
            "session_id": session.id,
            "user_profile": json.dumps(user_profile),
            "metadata": json.dumps(metadata or {}),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _select_agent(
        self,
        message: str,
        session: SessionData,
        context_vars: Dict
    ) -> Optional[ChatCompletionAgent]:
        """Select agent with conflict resolution"""
        
        try:
            history = session.messages[-5:] if session.messages else []
            agents_list = list(self.agents.keys())
            
            args = KernelArguments(
                user_message=message,
                history=json.dumps(history),
                agents=", ".join(agents_list)
            )
            
            selector_function = self._create_severity_selector()
            result = await self.kernel.invoke(selector_function, args)
            
            agent_name = self._parse_selector_result(result)
            
            return self.agents.get(agent_name)
            
        except Exception as e:
            logger.error(f"Agent selection failed: {e}")
            return self.agents.get(AgentType.GENERAL)
    
    async def _invoke_agent_with_retry(
        self,
        agent: ChatCompletionAgent,
        message: str,
        context_vars: Dict,
        session: SessionData
    ) -> Dict[str, Any]:
        """Invoke agent with retry logic"""
        
        for attempt in range(self.max_retries):
            try:
                return await self._invoke_agent(agent, message, context_vars, session)
            except Exception as e:
                logger.warning(f"Agent invocation attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    self.agent_errors[agent.name] += 1
                    raise
        
        return {"error": True, "message": "Failed to process after multiple retries"}
    
    async def _invoke_agent(
        self,
        agent: ChatCompletionAgent,
        message: str,
        context_vars: Dict,
        session: SessionData
    ) -> Dict[str, Any]:
        """Invoke a specific agent and parse its response"""
        
        logger.debug(f"Invoking agent: {agent.name}")
        
        try:
            # Create chat history - FIXED VERSION
            chat_history = ChatHistory()
            
            # Add system message based on agent type
            system_message = self._get_system_message(agent.name)
            if system_message:
                chat_history.add_system_message(system_message)
            
            # Add conversation history
            if session and session.messages:
                for msg in session.messages[-5:]:  # Last 5 messages
                    if msg.get("role") == "user":
                        chat_history.add_user_message(msg.get("content", ""))
                    elif msg.get("role") == "assistant":
                        chat_history.add_assistant_message(msg.get("content", ""))
            
            # Add current message
            chat_history.add_user_message(message)
            
            # Invoke agent with chat history
            response_text = ""
            async for response in agent.invoke(chat_history):
                if response and hasattr(response, 'items') and response.items:
                    for item in response.items:
                        if hasattr(item, 'text'):
                            response_text += item.text
            
            # Try to parse JSON response
            try:
                json_pattern = r'\{.*\}'
                json_match = re.search(json_pattern, response_text, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group()
                    parsed = json.loads(json_str)
                    
                    validated = await self._validate_agent_response(agent.name, parsed)
                    
                    logger.debug(f"Agent {agent.name} returned valid JSON")
                    return validated
                else:
                    logger.debug(f"Agent {agent.name} returned non-JSON response")
                    return {"message": response_text, "raw_response": True}
                    
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse agent response as JSON: {e}")
                return {"message": response_text, "raw_response": True}
                
        except Exception as e:
            logger.error(f"Agent invocation failed: {e}")
            return {
                "error": True,
                "error_message": str(e),
                "message": "I encountered an error processing your request."
            }
    
    def _get_system_message(self, agent_name: str) -> Optional[str]:
        """Get system message for agent type"""
        messages = {
            "emergency_agent": "You are an emergency response agent. Handle life-threatening situations.",
            "scam_agent": "You are a scam detection agent. Analyze messages for fraud.",
            "medication_agent": "You are a medication management agent. Track medications and reminders.",
            "wellness_agent": "You are a wellness agent. Track mood and activities.",
            "family_agent": "You are a family notification agent. Communicate with family.",
            "general_agent": "You are a helpful assistant for elderly users. Be patient and clear."
        }
        return messages.get(agent_name)
    
    async def _validate_agent_response(
        self,
        agent_name: str,
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and ensure required fields are present in agent response"""
        
        required_fields = {
            AgentType.EMERGENCY: ["detected", "severity", "message_to_user"],
            AgentType.SCAM: ["is_scam", "severity", "message"],
            AgentType.MEDICATION: ["action", "severity", "message"],
            AgentType.WELLNESS: ["wellness_type", "severity", "message"],
            AgentType.FAMILY: ["should_notify", "severity", "message"],
            AgentType.GENERAL: ["severity", "message"]
        }
        
        fields = required_fields.get(agent_name, ["message"])
        missing = [f for f in fields if f not in response]
        
        if missing:
            logger.warning(f"Agent {agent_name} missing required fields: {missing}")
            for field in missing:
                if field == "message":
                    response["message"] = "I've processed your request."
                elif field == "severity":
                    response["severity"] = "LOW"
                elif field == "detected":
                    response["detected"] = False
                elif field == "is_scam":
                    response["is_scam"] = False
                elif field == "should_notify":
                    response["should_notify"] = False
        
        return response
    
    async def _handle_multi_agent(
        self,
        message: str,
        primary_response: Dict,
        context_vars: Dict,
        session: SessionData
    ) -> Dict[str, Any]:
        """Handle requests that need multiple agents"""
        
        combined_response = primary_response.copy()
        secondary_responses = []
        
        # Case 1: Scam detected - notify family (HIGH severity)
        if primary_response.get("is_scam") and primary_response.get("severity") in ["HIGH", "CRITICAL"]:
            logger.info("Multi-agent: Scam detected, notifying family")
            
            family_agent = self.agents.get(AgentType.FAMILY)
            if family_agent:
                notification_message = f"Scam detected for user {context_vars.get('user_id')}. Severity: {primary_response.get('severity')}"
                
                family_response = await self._invoke_agent(
                    family_agent,
                    notification_message,
                    context_vars,
                    session
                )
                
                secondary_responses.append({
                    "agent": AgentType.FAMILY,
                    "response": family_response
                })
                
                combined_response["family_notification"] = family_response
        
        # Case 2: Medication missed - wellness check (HIGH severity)
        if primary_response.get("action") == "missed" or primary_response.get("severity") == "HIGH":
            logger.info("Multi-agent: Missed medication, wellness check")
            
            wellness_agent = self.agents.get(AgentType.WELLNESS)
            if wellness_agent:
                wellness_response = await self._invoke_agent(
                    wellness_agent,
                    f"User missed medication. Check wellbeing.",
                    context_vars,
                    session
                )
                
                secondary_responses.append({
                    "agent": AgentType.WELLNESS,
                    "response": wellness_response
                })
                
                combined_response["wellness_check"] = wellness_response
        
        if secondary_responses:
            combined_response["secondary_agents"] = secondary_responses
            combined_response["requires_additional_agents"] = False
        
        return combined_response
    
    async def _format_response(
        self,
        agent_response: Dict,
        agent_name: str,
        session: SessionData
    ) -> Dict[str, Any]:
        """Format the final response to user"""
        
        if "message" not in agent_response and "message_to_user" in agent_response:
            agent_response["message"] = agent_response["message_to_user"]
        
        if "message" not in agent_response:
            generic_messages = {
                AgentType.EMERGENCY: "🚨 Emergency services have been notified. Help is on the way.",
                AgentType.SCAM: "⚠️ I've analyzed the message for scams.",
                AgentType.MEDICATION: "💊 I've processed your medication request.",
                AgentType.WELLNESS: "😊 Thanks for sharing your wellness information.",
                AgentType.FAMILY: "👪 Family notification has been processed.",
                AgentType.GENERAL: "🤖 How can I help you today?"
            }
            agent_response["message"] = generic_messages.get(agent_name, "I've processed your request.")
        
        if "suggestions" not in agent_response:
            agent_response["suggestions"] = self._get_suggestions(agent_name, agent_response)
        
        if "timestamp" not in agent_response:
            agent_response["timestamp"] = datetime.utcnow().isoformat()
        
        return agent_response
    
    def _get_suggestions(self, agent_name: str, response: Dict) -> List[str]:
        """Get context-aware suggestions based on agent and response"""
        
        suggestions = []
        
        if agent_name == AgentType.EMERGENCY:
            suggestions = [
                "Stay on the line for further instructions",
                "Keep your phone nearby",
                "Unlock your door if possible"
            ]
        
        elif agent_name == AgentType.SCAM:
            if response.get("severity") in ["HIGH", "CRITICAL"]:
                suggestions = [
                    "Do not respond to the message",
                    "Block the sender",
                    "Tell a family member about this"
                ]
            else:
                suggestions = [
                    "Stay vigilant",
                    "Contact your bank directly if unsure",
                    "Ask family if something seems suspicious"
                ]
        
        elif agent_name == AgentType.MEDICATION:
            if response.get("action") == "add":
                suggestions = [
                    "Set a reminder for this medication",
                    "Add to your medication list",
                    "Check for drug interactions"
                ]
            elif response.get("action") == "mark_taken":
                suggestions = [
                    "Great job! Any other medications?",
                    "Check your next reminder",
                    "View your adherence report"
                ]
            else:
                suggestions = [
                    "Would you like to add a medication?",
                    "Check your next reminder",
                    "View your medication list"
                ]
        
        elif agent_name == AgentType.WELLNESS:
            wellness_type = response.get("wellness_type")
            if wellness_type == "mood":
                suggestions = [
                    "Would you like some wellness tips?",
                    "Track your sleep tonight",
                    "Consider calling a family member"
                ]
            elif wellness_type == "activity":
                suggestions = [
                    "Great job staying active!",
                    "Track your water intake",
                    "Check your step goal"
                ]
            else:
                suggestions = [
                    "Track your mood",
                    "Log your activity",
                    "Connect with family"
                ]
        
        elif agent_name == AgentType.FAMILY:
            suggestions = [
                "Check if family responded",
                "Send another update",
                "View family dashboard"
            ]
        
        else:
            suggestions = [
                "Check your medications",
                "How are you feeling?",
                "Report any suspicious messages",
                "View your wellness report",
                "Call a family member"
            ]
        
        return suggestions[:3]
    
    async def _check_termination(
        self,
        message: str,
        response: Dict,
        session: SessionData
    ) -> bool:
        """Check if conversation should terminate"""
        
        # Never terminate if emergency detected
        if response.get("detected") or response.get("severity") == "CRITICAL":
            return False
        
        # Check for termination keywords
        termination_keywords = [
            "bye", "goodbye", "see you", "thanks", "thank you",
            "that's all", "that is all", "done", "finished"
        ]
        
        message_lower = message.lower()
        for keyword in termination_keywords:
            if keyword in message_lower:
                return True
        
        # Max conversation length
        if len(session.messages) > self.max_conversation_length:
            logger.info("Max conversation length reached")
            return True
        
        return False
    
    async def _handle_emergency_direct(
        self,
        user_id: str,
        message: str,
        session: SessionData,
        metadata: Optional[Dict],
        request_id: str
    ) -> Dict[str, Any]:
        """Direct emergency handling bypassing normal flow"""
        
        logger.warning(f"🚨 DIRECT EMERGENCY HANDLING for user {user_id}")
        
        emergency_agent = self.agents.get(AgentType.EMERGENCY)
        
        if not emergency_agent:
            return {
                "request_id": request_id,
                "type": "emergency",
                "detected": True,
                "severity": "CRITICAL",
                "response": "🚨 EMERGENCY DETECTED! Please call 911 immediately if you need help. I'm alerting your emergency contacts.",
                "data": {"emergency_id": str(uuid.uuid4())},
                "timestamp": datetime.utcnow().isoformat()
            }
        
        context_vars = await self._build_context_vars(user_id, message, session, metadata)
        
        agent_response = await self._invoke_agent(
            emergency_agent,
            f"EMERGENCY: {message}",
            context_vars,
            session
        )
        
        family_agent = self.agents.get(AgentType.FAMILY)
        if family_agent:
            notification = await self._invoke_agent(
                family_agent,
                f"URGENT: Emergency detected for user {user_id}. Details: {message}",
                context_vars,
                session
            )
            agent_response["family_notification"] = notification
            
            # Start closed-loop escalation tracking (Gemini Recommendation #3)
            await self._start_escalation_tracking(
                user_id=user_id,
                alert_type="emergency",
                alert_data=agent_response,
                session=session
            )
        
        return {
            "request_id": request_id,
            "type": "emergency",
            "detected": True,
            "severity": "CRITICAL",
            "response": agent_response.get("message", "🚨 Emergency services have been notified. Help is on the way."),
            "data": agent_response,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _start_escalation_tracking(
        self,
        user_id: str,
        alert_type: str,
        alert_data: Dict,
        session: SessionData
    ):
        """Start tracking an alert with escalation levels (Gemini Recommendation #3)"""
        
        alert_id = f"alert_{uuid.uuid4().hex[:8]}"
        
        session.pending_alerts[alert_id] = {
            "id": alert_id,
            "user_id": user_id,
            "type": alert_type,
            "data": alert_data,
            "escalation_level": 1,
            "sent_at": datetime.utcnow().isoformat(),
            "last_escalation": datetime.utcnow().isoformat(),
            "confirmed": False,
            "confirmations": []
        }
        
        logger.info(f"Started escalation tracking for alert {alert_id} at level 1")
        
        # Store in Cosmos DB for persistence (Gemini Recommendation #3)
        if self.db and hasattr(self.db, 'save_alert'):
            try:
                await self.db.save_alert(session.pending_alerts[alert_id])
            except Exception as e:
                logger.error(f"Failed to save alert to Cosmos: {e}")
    
    async def _escalation_monitor(self):
        """Background task to monitor pending alerts and escalate as needed (Gemini Recommendation #3)"""
        
        while True:
            try:
                now = datetime.utcnow()
                
                for session_key, session in list(self.sessions.items()):
                    for alert_id, alert in list(session.pending_alerts.items()):
                        if alert.get("confirmed", False):
                            continue
                        
                        last_escalation = datetime.fromisoformat(alert["last_escalation"])
                        elapsed_seconds = (now - last_escalation).total_seconds()
                        current_level = alert["escalation_level"]
                        
                        # Check if we need to escalate
                        if current_level < 3 and elapsed_seconds > self.escalation_levels[current_level]["wait_seconds"]:
                            # Escalate to next level
                            next_level = current_level + 1
                            alert["escalation_level"] = next_level
                            alert["last_escalation"] = now.isoformat()
                            
                            logger.warning(f"Escalating alert {alert_id} to level {next_level}")
                            
                            # Send notification at new level
                            await self._send_escalation_notification(alert, next_level)
                            
                            # Update in Cosmos DB
                            if self.db and hasattr(self.db, 'update_alert'):
                                try:
                                    await self.db.update_alert(alert_id, alert)
                                except Exception as e:
                                    logger.error(f"Failed to update alert in Cosmos: {e}")
                        
                        # If level 3 and still no confirmation after 15 minutes, trigger emergency services
                        elif current_level == 3 and elapsed_seconds > 900:
                            logger.critical(f"ALERT {alert_id} UNCONFIRMED AFTER ALL ESCALATIONS - CONTACTING EMERGENCY SERVICES")
                            await self._trigger_emergency_services(alert)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Escalation monitor error: {e}")
                await asyncio.sleep(60)
    
    async def _send_escalation_notification(self, alert: Dict, level: int):
        """Send notification at specific escalation level (Gemini Recommendation #3)"""
        
        channels = self.escalation_levels[level]["channels"]
        
        # Get family contacts from database
        contacts = []
        if self.db:
            try:
                contacts = await self.db.get_emergency_contacts(alert["user_id"]) or []
            except Exception as e:
                logger.error(f"Failed to get contacts for escalation: {e}")
        
        if not contacts:
            return
        
        for contact in contacts:
            if level == 1:
                message = f"URGENT: {alert['type'].upper()} alert for your loved one. Please check immediately."
            elif level == 2:
                message = f"SECOND ATTEMPT: {alert['type'].upper()} alert - still unconfirmed. Immediate attention required."
            else:
                message = f"FINAL ATTEMPT: {alert['type'].upper()} alert - no response. Emergency services will be contacted."
            
            # Send via appropriate channels
            for channel in channels:
                if channel == "sms" and contact.get("phone"):
                    if self.notification and hasattr(self.notification, 'send_sms'):
                        await self.notification.send_sms(contact["phone"], message)
                
                elif channel == "call" and contact.get("phone"):
                    if self.notification and hasattr(self.notification, 'make_call'):
                        await self.notification.make_call(
                            contact["phone"],
                            f"This is an automated emergency call from Elder AI Guardian. {message}"
                        )
                
                elif channel == "push" and contact.get("push_token"):
                    # Send push notification
                    pass
                
                elif channel == "email" and contact.get("email"):
                    if self.notification and hasattr(self.notification, 'send_email'):
                        await self.notification.send_email(
                            contact["email"],
                            f"URGENT: {alert['type'].upper()} Alert - Level {level}",
                            message
                        )
    
    async def _trigger_emergency_services(self, alert: Dict):
        """Trigger emergency services after all escalations fail"""
        
        # Log the critical event
        logger.critical(f"Triggering emergency services for alert {alert['id']}")
        
        # Call 911 via Azure Communication Services (Gemini Recommendation #2)
        if self.notification and hasattr(self.notification, 'make_call'):
            try:
                await self.notification.make_call(
                    "911",
                    f"Emergency alert for elderly person. Type: {alert['type']}. No response from family after multiple attempts."
                )
                logger.info("✅ Emergency services notified via automated call")
            except Exception as e:
                logger.error(f"Failed to call emergency services: {e}")
        
        # Mark alert as resolved
        alert["emergency_services_triggered"] = True
        alert["emergency_services_time"] = datetime.utcnow().isoformat()
    
    async def _social_connectivity_monitor(self):
        """Background task to monitor social connectivity and suggest interventions"""
        
        while True:
            try:
                # Only run every 24 hours
                now = datetime.utcnow()
                
                for session_key, session in list(self.sessions.items()):
                    last_check = self.last_social_check.get(session.user_id)
                    
                    if not last_check or (now - last_check).total_seconds() > self.social_check_interval_hours * 3600:
                        # Time to check this user
                        self.last_social_check[session.user_id] = now
                        
                        # Get user's wellness data
                        if self.db:
                            try:
                                entries = await self.db.get_user_wellness_entries(
                                    session.user_id,
                                    days=self.social_threshold_days
                                ) or []
                                
                                # Check if user has been socially isolated
                                social_mentions = [
                                    e for e in entries 
                                    if e.get("type") == "mood" and any(
                                        word in e.get("data", {}).get("note", "").lower()
                                        for word in ["lonely", "alone", "miss", "nobody", "no one"]
                                    )
                                ]
                                
                                # If multiple loneliness indicators, suggest intervention
                                if len(social_mentions) >= 2:
                                    logger.info(f"Proactive social intervention for user {session.user_id}")
                                    
                                    # Get family contacts
                                    contacts = await self.db.get_emergency_contacts(session.user_id) or []
                                    
                                    if contacts:
                                        # Send proactive message via WebSocket (Gemini Recommendation #4)
                                        await self._send_websocket_alert(
                                            session.user_id,
                                            {
                                                "type": "social_alert",
                                                "message": f"We noticed you've been feeling lonely. Would you like to call {contacts[0].get('name', 'a family member')}?",
                                                "suggestions": [
                                                    f"Call {contacts[0].get('name')}",
                                                    "Schedule a video chat",
                                                    "Tell me how you're feeling"
                                                ]
                                            }
                                        )
                            except Exception as e:
                                logger.error(f"Social monitor error for user {session.user_id}: {e}")
                
                await asyncio.sleep(3600)  # Check every hour but only act every 24 hours per user
                
            except Exception as e:
                logger.error(f"Social connectivity monitor error: {e}")
                await asyncio.sleep(3600)
    
    async def _send_websocket_alert(self, user_id: str, alert_data: Dict):
        """Send real-time WebSocket alert to user's connected clients (Gemini Recommendation #4)"""
        
        from app.main import active_connections, connection_sessions
        
        for conn_id, websocket in list(active_connections.items()):
            if connection_sessions.get(conn_id) == user_id:
                try:
                    await websocket.send_json({
                        "type": "live_alert",
                        "data": alert_data,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    logger.info(f"Sent live alert to user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to send WebSocket alert: {e}")
    
    async def _get_session(self, user_id: str, session_id: Optional[str] = None) -> SessionData:
        """Get or create session with proper locking"""
        
        if not session_id:
            session_id = f"session_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        session_key = f"{user_id}:{session_id}"
        
        async with self.session_locks[session_key]:
            if session_key in self.sessions:
                session = self.sessions[session_key]
                if datetime.utcnow() - session.last_activity < self.max_session_age:
                    session.last_activity = datetime.utcnow()
                    return session
                else:
                    logger.info(f"Session {session_key} expired, creating new")
                    del self.sessions[session_key]
            
            session = SessionData(
                id=session_id,
                user_id=user_id
            )
            
            self.sessions[session_key] = session
            
            logger.info(f"Created new session: {session_key}")
            
            return session
    
    async def _update_session(
        self,
        user_id: str,
        session_id: str,
        message: str,
        response: Dict,
        agent_name: str
    ):
        """Update session with new interaction"""
        
        if not session_id:
            return
        
        session_key = f"{user_id}:{session_id}"
        
        async with self.session_locks[session_key]:
            if session_key in self.sessions:
                session = self.sessions[session_key]
                
                session.messages.append({
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                session.messages.append({
                    "role": "assistant",
                    "content": response.get("message", ""),
                    "agent": agent_name,
                    "severity": response.get("severity", "LOW"),
                    "intent": response.get("intent") or response.get("action") or response.get("wellness_type"),
                    "data": response,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                session.context["last_intent"] = response.get("intent") or response.get("action")
                session.context["last_agent"] = agent_name
                session.context["last_severity"] = response.get("severity", "LOW")
                
                session.last_activity = datetime.utcnow()
                
                if len(session.messages) > self.max_conversation_length * 2:
                    session.messages = session.messages[-self.max_conversation_length:]
                
                if session.state == ConversationState.INITIATED:
                    session.state = ConversationState.PROCESSING
    
    async def _track_metrics(
        self,
        request_id: str,
        agent_name: str,
        response: Dict,
        processing_steps: List[Dict]
    ):
        """Track metrics for monitoring"""
        
        if not self.metrics:
            return
        
        try:
            total_time = sum(step.get("duration_ms", 0) for step in processing_steps)
            
            await self.metrics.increment("supervisor_requests", {
                "agent": agent_name,
                "severity": response.get("severity", "LOW"),
                "status": "success" if "error" not in response else "error"
            })
            
            await self.metrics.timing("supervisor_processing", total_time, {
                "agent": agent_name,
                "severity": response.get("severity", "LOW")
            })
            
            if response.get("detected") or response.get("severity") == "CRITICAL":
                await self.metrics.increment("emergency_detected")
            
            if response.get("is_scam"):
                await self.metrics.increment("scam_detected", {
                    "severity": response.get("severity", "LOW")
                })
            
            if response.get("adherence_data"):
                await self.metrics.record_adherence(
                    response.get("adherence_data", {}).get("adherence_rate", 0)
                )
            
        except Exception as e:
            logger.warning(f"Failed to track metrics: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get supervisor statistics"""
        
        total_requests = self.request_counter
        total_errors = self.error_counter
        
        agent_stats = {}
        for agent_name, count in self.agent_usage_stats.items():
            response_times = self.agent_response_times.get(agent_name, [])
            avg_time = sum(response_times) / len(response_times) if response_times else 0
            error_count = self.agent_errors.get(agent_name, 0)
            
            agent_stats[agent_name] = {
                "calls": count,
                "avg_response_time_ms": avg_time,
                "error_count": error_count,
                "error_rate": error_count / count if count > 0 else 0
            }
        
        all_response_times = [t for times in self.agent_response_times.values() for t in times]
        p95_time = sorted(all_response_times)[int(len(all_response_times) * 0.95)] if len(all_response_times) > 20 else 0
        
        # Get pending alerts count
        total_pending_alerts = sum(
            len(session.pending_alerts) 
            for session in self.sessions.values()
        )
        
        # Get escalation statistics
        escalated_alerts = 0
        for session in self.sessions.values():
            for alert in session.pending_alerts.values():
                if alert.get("escalation_level", 1) > 1:
                    escalated_alerts += 1
        
        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / max(total_requests, 1),
            "active_sessions": len(self.sessions),
            "pending_alerts": total_pending_alerts,
            "escalated_alerts": escalated_alerts,
            "agent_usage": agent_stats,
            "avg_response_time_ms": sum(all_response_times) / max(len(all_response_times), 1),
            "p95_response_time_ms": p95_time,
            "is_healthy": self.is_healthy,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        
        now = datetime.utcnow()
        expired = []
        
        for session_key, session in self.sessions.items():
            if now - session.last_activity > self.max_session_age:
                expired.append(session_key)
        
        for session_key in expired:
            async with self.session_locks[session_key]:
                if session_key in self.sessions:
                    del self.sessions[session_key]
            
            if session_key in self.session_locks:
                del self.session_locks[session_key]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    async def health_check(self) -> bool:
        """Check if supervisor is healthy"""
        
        checks = [
            self.is_healthy,
            self.agent_group is not None,
            len(self.agents) >= 3,
            self.error_counter < self.request_counter * 0.1 if self.request_counter > 0 else True
        ]
        
        return all(checks)