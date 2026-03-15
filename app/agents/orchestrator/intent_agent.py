"""
Intent Classification Agent using Microsoft Agent Framework
Replaces hardcoded keyword matching with LLM-based intent detection
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelFunction

from app.core.logging import logger, get_tracer

class IntentClassificationAgent:
    """
    Dedicated agent for intent classification using LLM reasoning
    Replaces deterministic keyword matching with semantic understanding
    """
    
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.agent: Optional[ChatCompletionAgent] = None
        self.tracer = get_tracer(__name__)
        self.intent_history = []
        
    async def initialize(self):
        """Initialize the intent classification agent"""
        with self.tracer.start_as_current_span("intent_agent_init"):
            
            self.agent = ChatCompletionAgent(
                kernel=self.kernel,
                name="IntentClassifier",
                instructions="""You are an Intent Classification Agent. Your task is to analyze user messages 
                and determine the primary intent and required agents with high accuracy.

                INTENT CATEGORIES:
                1. EMERGENCY - Life-threatening situations requiring immediate help
                   - Keywords: heart attack, stroke, fire, bleeding, unconscious, can't breathe, fall, fell
                   - Urgency: Immediate, life safety
                
                2. SCAM_DETECTION - Suspicious messages, potential fraud
                   - Keywords: scam, phishing, fraud, suspicious, fake, verify account, bank calling
                   - Urgency: High (security risk)
                
                3. MEDICATION - Medication-related queries
                   - Keywords: pill, medicine, prescription, dose, take, forgot, reminder, refill
                   - Sub-intents: add_medication, mark_taken, check_reminder, adherence_report
                
                4. WELLNESS - Health, mood, activity tracking
                   - Keywords: feel, mood, sleep, walk, exercise, water, tired, happy, sad
                   - Sub-intents: track_mood, log_activity, sleep_track, water_intake, get_tips
                
                5. FAMILY_NOTIFICATION - Contact family members
                   - Keywords: notify family, tell my son/daughter, contact, message, call
                   - Urgency: Based on context (low to high)
                
                6. GENERAL - General conversation, greetings, questions about system
                   - Keywords: hello, hi, what can you do, help, how does this work

                Analyze the message for:
                - Primary intent (one of the above)
                - Confidence score (0-1)
                - Required agents (list of agent names needed)
                - Urgency level (1-10)
                - Extracted entities (medications, people, times, locations)
                - Sub-intent (more specific action)

                Consider:
                - Context from conversation history
                - Multiple intents may be present (prioritize safety)
                - Implicit meanings and synonyms
                - Cultural and linguistic variations

                Return JSON with:
                {
                    "primary_intent": "EMERGENCY|SCAM_DETECTION|MEDICATION|WELLNESS|FAMILY_NOTIFICATION|GENERAL",
                    "confidence": 0.95,
                    "required_agents": ["emergency_agent", "family_agent"],
                    "urgency": 8,
                    "sub_intent": "fall_detected",
                    "extracted_entities": {
                        "medications": ["aspirin"],
                        "people": ["daughter"],
                        "times": ["8:00 AM"],
                        "locations": ["kitchen"]
                    },
                    "reasoning": "User mentions falling and can't get up - indicates emergency",
                    "requires_immediate_action": true,
                    "suggested_response_type": "emergency_protocol"
                }
                """
            )
            
            logger.info("Intent Classification Agent initialized")
    
    async def classify(
        self,
        message: str,
        context: Optional[List[Dict]] = None,
        user_profile: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Classify intent of user message using LLM
        """
        with self.tracer.start_as_current_span("classify_intent"):
            
            # Build context
            context_str = ""
            if context:
                recent = context[-5:]  # Last 5 messages
                context_str = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                    for msg in recent
                ])
            
            # Prepare input for agent
            input_data = {
                "user_message": message,
                "conversation_history": context_str,
                "user_profile": json.dumps(user_profile) if user_profile else "{}"
            }
            
            # Invoke agent
            response = await self.agent.invoke(json.dumps(input_data))
            
            try:
                # Parse response
                content = response.items[0].text if response.items else "{}"
                
                # Extract JSON
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    
                    # Store in history
                    self.intent_history.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": message[:100],
                        "intent": result.get("primary_intent"),
                        "confidence": result.get("confidence")
                    })
                    
                    return result
                else:
                    # Fallback
                    return self._rule_based_fallback(message)
                    
            except Exception as e:
                logger.error(f"Intent classification failed: {e}")
                return self._rule_based_fallback(message)
    
    def _rule_based_fallback(self, message: str) -> Dict[str, Any]:
        """Rule-based fallback if LLM fails"""
        message_lower = message.lower()
        
        # Emergency detection
        emergency_keywords = ["help", "emergency", "sos", "fall", "fell", "hurt", "pain", 
                              "chest", "heart", "ambulance", "911", "can't breathe", "fire"]
        if any(word in message_lower for word in emergency_keywords):
            return {
                "primary_intent": "EMERGENCY",
                "confidence": 0.8,
                "required_agents": ["emergency_agent"],
                "urgency": 10,
                "reasoning": "Emergency keywords detected",
                "requires_immediate_action": True
            }
        
        # Scam detection
        scam_keywords = ["scam", "fraud", "phishing", "suspicious", "fake", "verify account"]
        if any(word in message_lower for word in scam_keywords):
            return {
                "primary_intent": "SCAM_DETECTION",
                "confidence": 0.7,
                "required_agents": ["scam_agent", "family_agent"],
                "urgency": 7,
                "reasoning": "Scam-related keywords detected"
            }
        
        # Default to general
        return {
            "primary_intent": "GENERAL",
            "confidence": 0.5,
            "required_agents": ["general_agent"],
            "urgency": 1,
            "reasoning": "No specific intent detected"
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get intent classification statistics"""
        if not self.intent_history:
            return {"status": "no_data"}
        
        intents = {}
        for entry in self.intent_history:
            intent = entry.get("intent", "UNKNOWN")
            intents[intent] = intents.get(intent, 0) + 1
        
        return {
            "total_classified": len(self.intent_history),
            "intent_distribution": intents,
            "average_confidence": sum(
                e.get("confidence", 0) for e in self.intent_history
            ) / len(self.intent_history),
            "recent": self.intent_history[-5:]
        }