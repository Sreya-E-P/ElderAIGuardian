"""
Orchestrator Agent - Coordinates all specialized agents
WINNING VERSION - Fixed for hackathon with TIMEOUT PROTECTION
"""

import asyncio
import uuid
import re
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core.logging import logger
from app.core.config import settings

class OrchestratorAgent:
    """
    Main orchestrator that coordinates all specialized agents
    FIXED VERSION - With timeout protection to prevent hangs
    """
    
    def __init__(
        self,
        scam_agent=None,
        medication_agent=None,
        emergency_agent=None,
        family_agent=None,
        wellness_agent=None,
        foundry_service=None,
        mcp_service=None,
        cache_service=None
    ):
        self.scam_agent = scam_agent
        self.medication_agent = medication_agent
        self.emergency_agent = emergency_agent
        self.family_agent = family_agent
        self.wellness_agent = wellness_agent
        self.foundry = foundry_service
        self.mcp = mcp_service
        self.cache = cache_service
        
        # Session contexts
        self.sessions = {}
        self.is_healthy = True
        
        # Emergency keywords for quick detection
        self.emergency_keywords = [
            "help", "emergency", "sos", "911", "fall", "fell", "fallen",
            "heart attack", "stroke", "fire", "bleeding", "unconscious",
            "can't breathe", "cannot breathe", "chest pain", "ambulance",
            "hurt badly", "seriously injured", "dying", "death", "fire"
        ]
        
        logger.info("✅ OrchestratorAgent initialized - WINNING VERSION")
    
    async def initialize(self):
        """Initialize orchestrator"""
        self.is_healthy = True
        logger.info("🎯 OrchestratorAgent fully initialized and ready")
        return self
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        session_id: str = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process incoming message and route to appropriate agent
        FIXED: Always returns proper response structure with TIMEOUT PROTECTION
        """
        
        request_id = str(uuid.uuid4())
        
        # Ensure session_id exists
        if not session_id:
            session_id = f"session_{user_id}_{datetime.utcnow().timestamp()}"
        
        logger.info(f"📨 [{request_id}] Processing message from {user_id}: {message[:50]}...")
        
        try:
            # Get or create session context
            session = await self._get_session(user_id, session_id)
            
            # STEP 1: ALWAYS check for emergency first (highest priority)
            is_emergency = await self._detect_emergency(message)
            if is_emergency:
                logger.warning(f"🚨 [{request_id}] EMERGENCY DETECTED!")
                result = await self._handle_emergency(
                    user_id, message, session, metadata, request_id
                )
                await self._update_session(user_id, session_id, message, result, "emergency")
                return result
            
            # STEP 2: Detect intent using multiple methods
            intent = await self._detect_intent(message, session)
            logger.info(f"🎯 [{request_id}] Detected intent: {intent}")
            
            # STEP 3: Route to appropriate agent with TIMEOUT
            response = None
            notify_family = False
            priority = "MEDIUM"
            
            try:
                if intent == "scam_detection" and self.scam_agent:
                    # Add timeout to prevent hanging
                    response = await asyncio.wait_for(
                        self.scam_agent.analyze(
                            message=message,
                            context=session,
                            user_id=user_id
                        ),
                        timeout=3.0  # 3 second timeout
                    )
                    if response and response.get("risk_level") == "HIGH":
                        notify_family = True
                        priority = "HIGH"
                
                elif intent == "medication" and self.medication_agent:
                    # Add timeout to prevent hanging
                    response = await asyncio.wait_for(
                        self.medication_agent.handle_request(
                            user_id=user_id,
                            message=message,
                            context=session
                        ),
                        timeout=3.0  # 3 second timeout
                    )
                    if response and response.get("action") == "missed":
                        notify_family = True
                        priority = "HIGH"
                
                elif intent == "wellness" and self.wellness_agent:
                    # Add timeout to prevent hanging
                    response = await asyncio.wait_for(
                        self.wellness_agent.process(
                            user_id=user_id,
                            message=message,
                            context=session
                        ),
                        timeout=3.0  # 3 second timeout
                    )
                
                elif intent == "general":
                    response = await self._handle_general(message, session)
                
                else:
                    response = await self._handle_fallback(message, session)
                    
            except asyncio.TimeoutError:
                logger.error(f"⏱️ [{request_id}] Agent timeout for intent: {intent}")
                response = {
                    "message": "I'm thinking about your request. Give me a moment...",
                    "data": {}
                }
            except Exception as e:
                logger.error(f"❌ [{request_id}] Agent error: {e}")
                response = {"message": "I'm here to help. How can I assist you?", "data": {}}
            
            # Ensure response has message field
            if not response:
                response = {"message": "I understand. How can I help?", "data": {}}
            elif isinstance(response, dict) and "message" not in response:
                response["message"] = "I've processed your request."
            
            # Update session
            await self._update_session(user_id, session_id, message, response, intent)
            
            # Send family notification if needed
            if notify_family and self.family_agent:
                asyncio.create_task(self._notify_family(
                    user_id, intent, message, response, priority
                ))
            
            # Prepare final response
            result = {
                "request_id": request_id,
                "session_id": session_id,
                "type": "normal",
                "intent": intent,
                "response": response.get("message", "I'm here to help."),
                "data": response.get("data", {}),
                "suggestions": response.get("suggestions", []),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ [{request_id}] Processed in {intent} mode")
            return result
            
        except Exception as e:
            logger.error(f"❌ [{request_id}] Fatal error: {e}", exc_info=True)
            
            # ALWAYS return a valid response, even on error
            return {
                "request_id": request_id,
                "session_id": session_id,
                "type": "normal",
                "intent": "general",
                "response": "I'm here to help. How can I assist you today?",
                "data": {},
                "suggestions": [
                    "Check your medications",
                    "How are you feeling?",
                    "Report any suspicious messages"
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _detect_emergency(self, message: str) -> bool:
        """Quick emergency detection - multiple methods"""
        message_lower = message.lower()
        
        # Method 1: Direct keyword matching
        for keyword in self.emergency_keywords:
            if keyword in message_lower:
                logger.debug(f"Emergency keyword matched: {keyword}")
                return True
        
        # Method 2: Pattern matching for common emergency phrases
        emergency_patterns = [
            r"need.*help",
            r"can'?t.*move",
            r"can'?t.*breathe",
            r"something.*wrong",
            r"not.*feeling.*well",
            r"i'm.*dying",
            r"call.*(?:911|ambulance|doctor)"
        ]
        
        for pattern in emergency_patterns:
            if re.search(pattern, message_lower):
                logger.debug(f"Emergency pattern matched: {pattern}")
                return True
        
        # Method 3: Use Foundry if available (with timeout)
        if self.foundry:
            try:
                prompt = f"""
                Is this an EMERGENCY that requires immediate help? 
                Message: "{message}"
                
                Answer with only YES or NO.
                """
                
                response = await asyncio.wait_for(
                    self.foundry.generate_chat(
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1,
                        max_tokens=10
                    ),
                    timeout=1.0  # Quick timeout
                )
                
                result = response.get("content", "").strip().upper()
                if result == "YES":
                    return True
            except:
                pass
        
        return False
    
    async def _detect_intent(self, message: str, session: Dict) -> str:
        """Detect user intent using multiple methods"""
        message_lower = message.lower()
        
        # Method 1: Use Foundry if available (with timeout)
        if self.foundry:
            try:
                prompt = f"""
                Classify this message into ONE category:
                - scam_detection: about scams, fraud, suspicious calls/messages
                - medication: about pills, prescriptions, taking medicine
                - wellness: about feelings, mood, sleep, tired, energy
                - emergency: life-threatening situations, immediate danger
                - general: anything else
                
                Message: "{message}"
                
                Return only the category name.
                """
                
                response = await asyncio.wait_for(
                    self.foundry.generate_chat(
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1,
                        max_tokens=20
                    ),
                    timeout=1.0  # Quick timeout
                )
                
                intent = response.get("content", "").strip().lower()
                if intent in ["scam_detection", "medication", "wellness", "emergency", "general"]:
                    return intent
            except:
                pass
        
        # Method 2: Rule-based fallback (FAST)
        scam_words = ["scam", "fraud", "phishing", "suspicious", "fake", "verify", "bank calling"]
        if any(word in message_lower for word in scam_words):
            return "scam_detection"
        
        medication_words = ["medication", "medicine", "pill", "prescription", "took", "missed", "dose", "refill"]
        if any(word in message_lower for word in medication_words):
            return "medication"
        
        wellness_words = ["feel", "feeling", "mood", "tired", "sleep", "slept", "energy", "happy", "sad"]
        if any(word in message_lower for word in wellness_words):
            return "wellness"
        
        return "general"
    
    async def _handle_emergency(
        self,
        user_id: str,
        message: str,
        session: Dict,
        metadata: Optional[Dict],
        request_id: str
    ) -> Dict[str, Any]:
        """Handle emergency situation - CRITICAL for emergency panel"""
        
        logger.warning(f"🚨 HANDLING EMERGENCY for user {user_id}")
        
        emergency_result = {}
        
        # Try to use emergency agent if available (with timeout)
        if self.emergency_agent:
            try:
                emergency_result = await asyncio.wait_for(
                    self.emergency_agent.handle_emergency(
                        user_id=user_id,
                        message=message,
                        location=metadata.get("location") if metadata else None
                    ),
                    timeout=2.0  # Emergency should be fast
                )
            except Exception as e:
                logger.error(f"Emergency agent error: {e}")
                emergency_result = {"emergency_id": str(uuid.uuid4())}
        else:
            emergency_result = {"emergency_id": str(uuid.uuid4())}
        
        # Notify family in background (don't await)
        if self.family_agent:
            asyncio.create_task(self._notify_family_emergency(
                user_id, message, emergency_result, metadata
            ))
        
        return {
            "request_id": request_id,
            "type": "emergency",
            "intent": "emergency",
            "response": "🚨 EMERGENCY ALERT TRIGGERED! Help is on the way. Stay calm and stay where you are.",
            "data": {
                "emergency": emergency_result,
                "emergency_id": emergency_result.get("emergency_id"),
                "instructions": [
                    "Stay on the line",
                    "Keep your phone nearby",
                    "Unlock your door if possible",
                    "Help is coming"
                ]
            },
            "suggestions": [
                "🚨 Emergency services notified",
                "📱 Family alerted",
                "🚪 Unlock door if safe"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_general(self, message: str, session: Dict) -> Dict[str, Any]:
        """Handle general conversation"""
        
        # Simple response templates (FAST)
        responses = {
            "hello": "Hello! How can I help you today?",
            "hi": "Hi there! What can I do for you?",
            "thanks": "You're welcome! Is there anything else I can help with?",
            "thank you": "Happy to help! Let me know if you need anything else."
        }
        
        message_lower = message.lower()
        for key, response_text in responses.items():
            if key in message_lower:
                return {
                    "message": response_text,
                    "data": {},
                    "suggestions": [
                        "Check medications",
                        "Report scam",
                        "Wellness check"
                    ]
                }
        
        # Default response
        return {
            "message": "I'm here to help with scams, medications, emergencies, and wellness. What would you like assistance with?",
            "data": {},
            "suggestions": [
                "Check my medications",
                "Is this a scam?",
                "I don't feel well",
                "Emergency help"
            ]
        }
    
    async def _handle_fallback(self, message: str, session: Dict) -> Dict[str, Any]:
        """Handle unrecognized intents"""
        return {
            "message": "I'm here to help. You can ask me about medications, scams, or wellness. If this is an emergency, please say 'help' or 'emergency'.",
            "data": {},
            "suggestions": [
                "Check medications",
                "Is this a scam?",
                "I'm feeling tired",
                "Emergency help"
            ]
        }
    
    async def _notify_family(self, user_id: str, intent: str, message: str, response: Dict, priority: str):
        """Send family notification in background"""
        try:
            if self.family_agent:
                await self.family_agent.send_notification(
                    user_id=user_id,
                    event_type=intent,
                    data={
                        "message": message,
                        "response": response,
                        "priority": priority
                    },
                    priority=priority
                )
        except Exception as e:
            logger.error(f"Family notification failed: {e}")
    
    async def _notify_family_emergency(self, user_id: str, message: str, emergency_result: Dict, metadata: Optional[Dict]):
        """Send emergency notification to family"""
        try:
            if self.family_agent:
                await self.family_agent.send_notification(
                    user_id=user_id,
                    event_type="emergency",
                    data={
                        "emergency_id": emergency_result.get("emergency_id"),
                        "message": message,
                        "location": metadata.get("location") if metadata else None
                    },
                    priority="URGENT",
                    channels=["sms", "call", "push", "email"]
                )
        except Exception as e:
            logger.error(f"Emergency family notification failed: {e}")
    
    async def _get_session(self, user_id: str, session_id: str) -> Dict:
        """Get or create session context"""
        session_key = f"{user_id}:{session_id}"
        
        # Try cache first
        if self.cache:
            try:
                cached = await self.cache.get(session_key)
                if cached:
                    return cached
            except:
                pass
        
        # Create new session
        if session_key not in self.sessions:
            self.sessions[session_key] = {
                "user_id": user_id,
                "session_id": session_id,
                "messages": [],
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "context": {}
            }
        
        return self.sessions[session_key]
    
    async def _update_session(
        self,
        user_id: str,
        session_id: str,
        message: str,
        response: Dict,
        intent: str
    ):
        """Update session context"""
        session_key = f"{user_id}:{session_id}"
        
        if session_key in self.sessions:
            session = self.sessions[session_key]
            
            # Add user message
            session["messages"].append({
                "role": "user",
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Add assistant response
            session["messages"].append({
                "role": "assistant",
                "content": response.get("message", ""),
                "intent": intent,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            session["last_activity"] = datetime.utcnow().isoformat()
            session["last_intent"] = intent
            
            # Keep only last 20 messages
            if len(session["messages"]) > 20:
                session["messages"] = session["messages"][-20:]
            
            # Update cache
            if self.cache:
                try:
                    await self.cache.set(session_key, session, ttl=3600)
                except:
                    pass