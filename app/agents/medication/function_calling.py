"""
WINNING FEATURE #4: Function Calling for Intelligent Entity Extraction
Replaces brittle string parsing with structured data extraction using LLM
Complete implementation with comprehensive medication understanding
"""

import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core.logging import logger


class MedicationFunctionCalling:
    """
    Uses function calling to extract medication information from ANY sentence structure
    Handles complex sentences, brand names, generic names, and implied information
    
    Examples handled:
    - "I took my aspirin" → medication: aspirin, action: took
    - "Just took the blue pill for my blood pressure" → medication: unknown, action: took
    - "Missed my evening Lisinopril" → medication: lisinopril, action: missed, time: evening
    - "Need a refill of Metformin 500mg" → medication: metformin, dosage: 500mg, action: refill
    - "Adding a new prescription for Amlodipine 10mg once daily" → medication: amlodipine, dosage: 10mg, frequency: once daily
    - "What are the side effects of ibuprofen?" → medication: ibuprofen, action: asking
    """
    
    def __init__(self, foundry_agent):
        self.foundry = foundry_agent
        self.extraction_history = []
        self.medication_database = self._load_medication_database()
        
    def _load_medication_database(self) -> Dict[str, Dict]:
        """Load common medications and their properties"""
        return {
            # Common medications with brand/generic mappings
            "aspirin": {
                "generic": "aspirin",
                "brands": ["aspirin", "bayer", "ecotrin"],
                "common_dosages": ["81mg", "325mg", "500mg"],
                "category": "pain_reliever"
            },
            "ibuprofen": {
                "generic": "ibuprofen",
                "brands": ["ibuprofen", "advil", "motrin"],
                "common_dosages": ["200mg", "400mg", "600mg", "800mg"],
                "category": "nsaid"
            },
            "acetaminophen": {
                "generic": "acetaminophen",
                "brands": ["acetaminophen", "tylenol", "paracetamol"],
                "common_dosages": ["325mg", "500mg", "650mg"],
                "category": "pain_reliever"
            },
            "lisinopril": {
                "generic": "lisinopril",
                "brands": ["lisinopril", "zestril", "prinivil"],
                "common_dosages": ["2.5mg", "5mg", "10mg", "20mg", "40mg"],
                "category": "ace_inhibitor"
            },
            "metformin": {
                "generic": "metformin",
                "brands": ["metformin", "glucophage", "fortamet"],
                "common_dosages": ["500mg", "750mg", "850mg", "1000mg"],
                "category": "diabetes"
            },
            "atorvastatin": {
                "generic": "atorvastatin",
                "brands": ["atorvastatin", "lipitor"],
                "common_dosages": ["10mg", "20mg", "40mg", "80mg"],
                "category": "statin"
            },
            "amlodipine": {
                "generic": "amlodipine",
                "brands": ["amlodipine", "norvasc"],
                "common_dosages": ["2.5mg", "5mg", "10mg"],
                "category": "calcium_channel_blocker"
            },
            "omeprazole": {
                "generic": "omeprazole",
                "brands": ["omeprazole", "prilosec"],
                "common_dosages": ["10mg", "20mg", "40mg"],
                "category": "ppi"
            },
            "levothyroxine": {
                "generic": "levothyroxine",
                "brands": ["levothyroxine", "synthroid", "levoxyl"],
                "common_dosages": ["25mcg", "50mcg", "75mcg", "88mcg", "100mcg", "112mcg", "125mcg", "137mcg", "150mcg", "175mcg", "200mcg"],
                "category": "thyroid"
            },
            "hydrochlorothiazide": {
                "generic": "hydrochlorothiazide",
                "brands": ["hydrochlorothiazide", "hctz", "microzide"],
                "common_dosages": ["12.5mg", "25mg", "50mg"],
                "category": "diuretic"
            }
        }
    
    def get_function_schema(self) -> Dict:
        """Define the function schema for medication extraction"""
        return {
            "name": "extract_medication_info",
            "description": "Extract structured medication information from natural language with high accuracy",
            "parameters": {
                "type": "object",
                "properties": {
                    "medication_name": {
                        "type": "string",
                        "description": "Name of the medication (brand or generic) - extract even if implied"
                    },
                    "dosage": {
                        "type": "string",
                        "description": "Dosage amount and unit (e.g., '10mg', '1 tablet', '2 puffs', '500mg')"
                    },
                    "frequency": {
                        "type": "string",
                        "description": "How often taken (e.g., 'once daily', 'twice daily', 'every 8 hours', 'as needed')"
                    },
                    "times": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific times taken (e.g., ['8am', '8pm'], ['morning', 'night'], ['breakfast', 'dinner'])"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["took", "missed", "adding", "asking_about", "refill_needed", "reminder", "info"],
                        "description": "What the user is doing with this medication"
                    },
                    "instructions": {
                        "type": "string",
                        "description": "Special instructions (e.g., 'with food', 'before bed', 'on empty stomach', 'avoid alcohol')"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Number of pills/units taken (if specified)"
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence in extraction (0.0-1.0)"
                    }
                },
                "required": ["medication_name", "action"]
            }
        }
    
    async def extract(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract medication information using function calling
        Handles ANY sentence structure intelligently
        
        Args:
            message: User's message about medication
            context: Additional context (conversation history, user profile)
        
        Returns:
            Structured medication information
        """
        
        logger.debug(f"Extracting medication from: {message[:50]}...")
        
        # First try rule-based extraction for speed
        rule_based = self._rule_based_extraction(message)
        if rule_based["confidence"] > 0.8:
            logger.debug("Rule-based extraction succeeded with high confidence")
            self.extraction_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": message[:50],
                "method": "rule_based",
                "result": rule_based
            })
            return rule_based
        
        # Otherwise use function calling
        function_schema = self.get_function_schema()
        
        # Build context string
        context_str = ""
        if context:
            if context.get("recent_medications"):
                context_str += f"User's recent medications: {context['recent_medications']}\n"
            if context.get("adherence_rate"):
                context_str += f"User's adherence rate: {context['adherence_rate']}\n"
        
        prompt = f"""
        Extract medication information from this user message.
        
        Message: "{message}"
        
        {context_str}
        
        Common medications database: {json.dumps(list(self.medication_database.keys()))}
        
        Understand:
        - Brand names (Advil = ibuprofen, Tylenol = acetaminophen)
        - Common abbreviations (mg = milligram, bid = twice daily, qd = once daily)
        - Implicit times ("morning" = 8am, "night" = 8pm, "with breakfast" = morning)
        - Context clues for the action being taken
        
        Use the extract_medication_info function to return structured data.
        """
        
        try:
            response = await self.foundry.generate_chat(
                messages=[{"role": "user", "content": prompt}],
                functions=[function_schema],
                function_call={"name": "extract_medication_info"},
                temperature=0.1,
                max_tokens=300
            )
            
            # Extract function call arguments
            if response.get("function_calls"):
                function_call = response["function_calls"][0]
                if function_call["name"] == "extract_medication_info":
                    result = function_call["arguments"]
                    
                    # Validate and enhance result
                    result = self._validate_and_enhance(result, message)
                    
                    # Add metadata
                    result["extraction_method"] = "function_calling"
                    result["timestamp"] = datetime.utcnow().isoformat()
                    result["raw_message"] = message[:100]
                    
                    # Store history
                    self.extraction_history.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": message[:50],
                        "method": "function_calling",
                        "confidence": result.get("confidence", 0.9)
                    })
                    
                    logger.info(f"✅ Function calling extracted: {result.get('medication_name')} ({result.get('action')})")
                    
                    return result
            
            # Fallback to rule-based
            logger.warning("Function calling failed, using rule-based fallback")
            return rule_based
            
        except Exception as e:
            logger.error(f"Function calling failed: {e}")
            return rule_based
    
    def _rule_based_extraction(self, message: str) -> Dict[str, Any]:
        """Fast rule-based extraction as fallback"""
        message_lower = message.lower()
        
        result = {
            "medication_name": "unknown",
            "dosage": None,
            "frequency": None,
            "times": [],
            "action": "unknown",
            "instructions": None,
            "quantity": None,
            "confidence": 0.5,
            "extraction_method": "rule_based"
        }
        
        # Find medication name
        for med_name, med_info in self.medication_database.items():
            # Check generic name
            if med_name in message_lower:
                result["medication_name"] = med_name
                result["confidence"] = 0.8
                break
            
            # Check brand names
            for brand in med_info["brands"]:
                if brand in message_lower:
                    result["medication_name"] = med_name
                    result["confidence"] = 0.8
                    break
        
        # Determine action
        if any(word in message_lower for word in ["took", "take", "had", "taken"]):
            result["action"] = "took"
            result["confidence"] += 0.1
        elif any(word in message_lower for word in ["miss", "missed", "forgot"]):
            result["action"] = "missed"
            result["confidence"] += 0.1
        elif any(word in message_lower for word in ["refill", "need more", "order"]):
            result["action"] = "refill_needed"
            result["confidence"] += 0.1
        elif any(word in message_lower for word in ["add", "new", "starting"]):
            result["action"] = "adding"
            result["confidence"] += 0.1
        elif any(word in message_lower for word in ["what", "side effects", "information", "tell me about"]):
            result["action"] = "info"
            result["confidence"] += 0.1
        elif any(word in message_lower for word in ["remind", "reminder"]):
            result["action"] = "reminder"
            result["confidence"] += 0.1
        else:
            result["action"] = "asking_about"
        
        # Extract dosage
        import re
        dosage_pattern = r'(\d+)\s*(mg|mcg|g|ml|tablet|pill|cap|unit)s?'
        matches = re.findall(dosage_pattern, message_lower)
        if matches:
            result["dosage"] = f"{matches[0][0]}{matches[0][1]}"
            result["confidence"] += 0.1
        
        # Extract times
        time_patterns = {
            "morning": "08:00",
            "afternoon": "14:00",
            "evening": "20:00",
            "night": "22:00",
            "bedtime": "22:00",
            "breakfast": "08:00",
            "lunch": "12:00",
            "dinner": "18:00"
        }
        for time_word, time_value in time_patterns.items():
            if time_word in message_lower:
                result["times"].append(time_value)
        
        # Extract frequency
        if "twice" in message_lower or "two times" in message_lower:
            result["frequency"] = "twice daily"
        elif "once" in message_lower or "one time" in message_lower:
            result["frequency"] = "once daily"
        elif "three times" in message_lower:
            result["frequency"] = "three times daily"
        elif "every" in message_lower:
            hour_match = re.search(r'every (\d+) hours?', message_lower)
            if hour_match:
                result["frequency"] = f"every {hour_match.group(1)} hours"
        
        # Extract quantity
        quantity_match = re.search(r'(\d+)\s*(pills?|tablets?|caps?|units?)', message_lower)
        if quantity_match:
            result["quantity"] = int(quantity_match.group(1))
        
        # Extract instructions
        if "with food" in message_lower:
            result["instructions"] = "with food"
        elif "empty stomach" in message_lower:
            result["instructions"] = "on empty stomach"
        elif "before bed" in message_lower:
            result["instructions"] = "before bed"
        
        result["confidence"] = min(result["confidence"], 1.0)
        
        return result
    
    def _validate_and_enhance(self, result: Dict, original_message: str) -> Dict:
        """Validate and enhance the extraction result"""
        
        # Ensure medication name is present
        if not result.get("medication_name") or result["medication_name"] == "unknown":
            # Try to find in database
            message_lower = original_message.lower()
            for med_name in self.medication_database.keys():
                if med_name in message_lower:
                    result["medication_name"] = med_name
                    break
            
            # Try brand names
            if result["medication_name"] == "unknown":
                for med_name, med_info in self.medication_database.items():
                    for brand in med_info["brands"]:
                        if brand in message_lower:
                            result["medication_name"] = med_name
                            break
        
        # Ensure action is valid
        valid_actions = ["took", "missed", "adding", "asking_about", "refill_needed", "reminder", "info"]
        if result.get("action") not in valid_actions:
            result["action"] = "asking_about"
        
        # Ensure confidence is set
        if "confidence" not in result:
            result["confidence"] = 0.7
        
        return result
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get extraction statistics"""
        if not self.extraction_history:
            return {"status": "no_data"}
        
        methods = {}
        for entry in self.extraction_history:
            method = entry.get("method", "unknown")
            methods[method] = methods.get(method, 0) + 1
        
        return {
            "total_extractions": len(self.extraction_history),
            "methods_used": methods,
            "average_confidence": sum(e.get("confidence", 0) for e in self.extraction_history) / len(self.extraction_history),
            "recent": self.extraction_history[-5:],
            "timestamp": datetime.utcnow().isoformat()
        }