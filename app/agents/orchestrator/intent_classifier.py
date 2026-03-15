"""
WINNING FEATURE #3: Semantic Intent Classification
Replaces brittle keyword matching with LLM understanding
Complete implementation with fallback and statistics
"""

import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core.logging import logger


class SemanticIntentClassifier:
    """
    Uses GPT-4o to understand user intent semantically
    Understands phrases like "I'm not feeling great today" = wellness intent
    This replaces the old keyword-based intent detection
    """
    
    def __init__(self, foundry_agent):
        self.foundry = foundry_agent
        self.classification_history = []
        self.total_classifications = 0
        self.confidence_sum = 0.0
        
    async def initialize(self):
        """Initialize the classifier"""
        logger.info("=" * 80)
        logger.info("INITIALIZING SEMANTIC INTENT CLASSIFIER")
        logger.info("=" * 80)
        logger.info("✅ Semantic Intent Classifier ready - understands context, not just keywords")
    
    async def classify(self, message: str, context: Optional[List[Dict]] = None, user_profile: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Classify intent using semantic understanding, NOT keywords
        
        Examples:
        - "I'm not feeling great today" → WELLNESS (mood_check)
        - "My chest hurts" → EMERGENCY (medical)
        - "Got a weird email from my bank" → SCAM_DETECTION (phishing)
        - "Time for my evening pill" → MEDICATION (reminder)
        """
        self.total_classifications += 1
        
        logger.debug(f"Classifying message: {message[:50]}...")
        
        # Build context string
        context_str = ""
        if context:
            recent = context[-3:]  # Last 3 messages
            context_str = "\n".join([
                f"{m.get('role', 'user')}: {m.get('content', '')}"
                for m in recent
            ])
        
        # Build user profile string
        profile_str = ""
        if user_profile:
            profile_str = f"""
User preferences: {user_profile.get('preferences', {})}
Recent health: {user_profile.get('recent_health', {})}
Emergency contacts: {user_profile.get('emergency_contacts', [])}
"""
        
        prompt = f"""
        You are an intent classification expert for an elderly care system.
        
        USER MESSAGE: "{message}"
        
        CONVERSATION HISTORY:
        {context_str}
        
        USER CONTEXT:
        {profile_str}
        
        CLASSIFY INTO ONE INTENT:
        
        1. EMERGENCY - Life-threatening situations requiring immediate action
           Examples: "I fell and can't get up", "Chest hurts", "Fire in kitchen", "Someone breaking in"
           Indicators: Physical danger, medical crisis, security threat
           Priority: 10 (HIGHEST)
        
        2. SCAM_DETECTION - Suspicious communications, potential fraud
           Examples: "Got a call from someone saying my bank account is frozen", "This email looks fake"
           Indicators: Requests for money/personal info, urgency, unknown callers
           Priority: 8 (HIGH)
        
        3. MEDICATION - Medication-related queries
           Examples: "Time for my pill", "Took my Lisinopril", "Need a refill of aspirin"
           Sub-types: took_medication, missed_medication, check_reminder, refill_needed, add_medication
           Priority: 7 (MEDIUM-HIGH)
        
        4. WELLNESS - Health, mood, activity tracking
           Examples: "Feeling tired today", "Went for a walk", "Slept well last night", "In a good mood"
           Sub-types: mood_check, activity_log, sleep_track, hydration_check, wellness_report
           Priority: 5 (MEDIUM)
        
        5. FAMILY_NOTIFICATION - Contacting family members
           Examples: "Tell my daughter I'm okay", "Call my son", "Notify family", "Let them know I'm safe"
           Indicators: Mentions of family, requests to share information
           Priority: 6 (MEDIUM)
        
        6. GENERAL - Casual conversation, greetings, system questions
           Examples: "Hello", "What can you do?", "How's the weather?", "Thanks"
           Sub-types: greeting, question, feedback, thanks
           Priority: 1 (LOW)

        Return JSON with:
        {{
            "primary_intent": "EMERGENCY|SCAM_DETECTION|MEDICATION|WELLNESS|FAMILY_NOTIFICATION|GENERAL",
            "confidence": 0.0-1.0,
            "sub_intent": "specific action if applicable",
            "priority": 1-10,
            "requires_immediate_action": true/false,
            "extracted_entities": {{
                "medications": [],
                "people": [],
                "times": [],
                "locations": [],
                "numbers": []
            }},
            "reasoning": "Brief explanation of why this classification was chosen",
            "suggested_agent": "which agent should handle this"
        }}
        """
        
        try:
            response = await self.foundry.generate_chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            content = response.get("content", "{}")
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # Ensure required fields
                if "primary_intent" not in result:
                    result["primary_intent"] = "GENERAL"
                if "confidence" not in result:
                    result["confidence"] = 0.5
                if "priority" not in result:
                    result["priority"] = 1
                
                # Store for analytics
                self.classification_history.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": message[:50],
                    "intent": result["primary_intent"],
                    "confidence": result["confidence"],
                    "priority": result["priority"]
                })
                
                self.confidence_sum += result["confidence"]
                
                logger.info(f"🎯 Semantic classification: {result['primary_intent']} (conf: {result['confidence']:.2f}, priority: {result['priority']})")
                
                # Add suggested agent if not present
                if "suggested_agent" not in result:
                    agent_map = {
                        "EMERGENCY": "emergency_agent",
                        "SCAM_DETECTION": "scam_agent",
                        "MEDICATION": "medication_agent",
                        "WELLNESS": "wellness_agent",
                        "FAMILY_NOTIFICATION": "family_agent",
                        "GENERAL": "general_agent"
                    }
                    result["suggested_agent"] = agent_map.get(result["primary_intent"], "general_agent")
                
                return result
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
        
        # Fallback
        logger.warning("Using fallback classification")
        return self._rule_based_fallback(message)
    
    def _rule_based_fallback(self, message: str) -> Dict[str, Any]:
        """Rule-based fallback if LLM fails"""
        message_lower = message.lower()
        
        # Emergency detection
        emergency_keywords = ["help", "emergency", "sos", "fall", "fell", "hurt", "pain", 
                              "chest", "heart", "ambulance", "911", "can't breathe", "fire",
                              "bleeding", "unconscious", "stroke", "attack"]
        if any(word in message_lower for word in emergency_keywords):
            return {
                "primary_intent": "EMERGENCY",
                "confidence": 0.8,
                "priority": 10,
                "requires_immediate_action": True,
                "reasoning": "Emergency keywords detected in fallback",
                "suggested_agent": "emergency_agent",
                "extracted_entities": {}
            }
        
        # Scam detection
        scam_keywords = ["scam", "fraud", "phishing", "suspicious", "fake", "verify account",
                         "bank calling", "microsoft calling", "prize", "lottery", "inheritance"]
        if any(word in message_lower for word in scam_keywords):
            return {
                "primary_intent": "SCAM_DETECTION",
                "confidence": 0.7,
                "priority": 8,
                "requires_immediate_action": False,
                "reasoning": "Scam-related keywords detected in fallback",
                "suggested_agent": "scam_agent",
                "extracted_entities": {}
            }
        
        # Medication detection
        medication_keywords = ["medication", "medicine", "pill", "prescription", "drug", "dose",
                              "take", "took", "missed", "reminder", "refill", "pharmacy"]
        if any(word in message_lower for word in medication_keywords):
            return {
                "primary_intent": "MEDICATION",
                "confidence": 0.7,
                "priority": 7,
                "requires_immediate_action": False,
                "reasoning": "Medication keywords detected in fallback",
                "suggested_agent": "medication_agent",
                "extracted_entities": {}
            }
        
        # Wellness detection
        wellness_keywords = ["feel", "feeling", "mood", "happy", "sad", "tired", "sleep",
                            "slept", "walk", "exercise", "water", "thirsty", "hungry"]
        if any(word in message_lower for word in wellness_keywords):
            return {
                "primary_intent": "WELLNESS",
                "confidence": 0.6,
                "priority": 5,
                "requires_immediate_action": False,
                "reasoning": "Wellness keywords detected in fallback",
                "suggested_agent": "wellness_agent",
                "extracted_entities": {}
            }
        
        # Family notification
        family_keywords = ["family", "son", "daughter", "child", "grandson", "granddaughter",
                          "contact", "call", "message", "text", "notify", "tell"]
        if any(word in message_lower for word in family_keywords):
            return {
                "primary_intent": "FAMILY_NOTIFICATION",
                "confidence": 0.6,
                "priority": 6,
                "requires_immediate_action": False,
                "reasoning": "Family keywords detected in fallback",
                "suggested_agent": "family_agent",
                "extracted_entities": {}
            }
        
        # Default to general
        return {
            "primary_intent": "GENERAL",
            "confidence": 0.5,
            "priority": 1,
            "requires_immediate_action": False,
            "reasoning": "No specific intent detected in fallback",
            "suggested_agent": "general_agent",
            "extracted_entities": {}
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get classification statistics for dashboard"""
        if not self.classification_history:
            return {
                "status": "no_data",
                "total_classified": 0
            }
        
        intents = {}
        for entry in self.classification_history:
            intent = entry.get("intent", "UNKNOWN")
            intents[intent] = intents.get(intent, 0) + 1
        
        avg_confidence = self.confidence_sum / self.total_classifications if self.total_classifications > 0 else 0
        
        return {
            "total_classified": len(self.classification_history),
            "intent_distribution": intents,
            "average_confidence": round(avg_confidence, 2),
            "most_common_intent": max(intents, key=intents.get) if intents else None,
            "recent_classifications": self.classification_history[-5:],
            "timestamp": datetime.utcnow().isoformat()
        }