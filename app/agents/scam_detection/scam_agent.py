"""
Scam Detection Agent with Advanced Reasoning
Detects phishing, fraud, and scam attempts with threat profiling
FIXED: Added asyncio timeout to prevent 30s hang on Foundry calls
"""

import re
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
import json

from app.core.logging import logger

class ScamDetectionAgent:
    """Agent for detecting scams with advanced threat profiling"""
    
    def __init__(self, foundry_service=None, mcp_service=None, cache_service=None):
        self.foundry = foundry_service
        self.mcp = mcp_service
        self.cache = cache_service
        self.is_healthy = False
    
    async def initialize(self):
        self.is_healthy = True
        logger.info("ScamDetectionAgent initialized with advanced reasoning")
    
    async def analyze(
        self,
        message: str,
        context: Optional[Dict] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Analyze message for scams with threat profiling"""
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(message)
            if self.cache:
                try:
                    cached = await self.cache.get(cache_key)
                    if cached:
                        return cached
                except Exception:
                    pass
            
            # Extract URLs and phones
            urls = self._extract_urls(message)
            phones = self._extract_phones(message)
            emails = self._extract_emails(message)
            
            # FIXED: Use asyncio.wait_for to prevent 30s timeout hang
            try:
                threat_profile = await asyncio.wait_for(
                    self._analyze_with_reasoning(message, urls, phones, emails, user_id),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                logger.warning("Foundry analysis timed out - using rule-based fallback")
                threat_profile = self._rule_based_analysis(message, urls, phones)
            
            # Check community database via MCP
            community_reports = []
            if self.mcp and phones:
                for phone in phones:
                    try:
                        result = await asyncio.wait_for(
                            self.mcp.execute_tool("check_phone_number", {"phone_number": phone}),
                            timeout=2.0
                        )
                        if hasattr(result, 'success') and result.success and result.data.get("is_scam"):
                            community_reports.append({
                                "phone": phone,
                                "reports": result.data.get("report_count", 0),
                                "type": result.data.get("scam_type", "unknown")
                            })
                    except Exception:
                        pass
            
            risk_level = self._determine_risk_level(threat_profile, community_reports)
            recommendations = self._generate_recommendations(risk_level, threat_profile)
            educational_tip = self._get_educational_tip(threat_profile.get("scam_type", "general"))
            
            result = {
                "is_scam": threat_profile.get("is_scam", False),
                "risk_score": threat_profile.get("risk_score", 0),
                "risk_level": risk_level,
                "confidence": threat_profile.get("confidence", 0),
                "scam_type": threat_profile.get("scam_type", "unknown"),
                "threat_profile": {
                    "urgency_level": threat_profile.get("urgency_level", "LOW"),
                    "emotional_manipulation": threat_profile.get("emotional_manipulation", "LOW"),
                    "social_engineering_score": threat_profile.get("social_engineering_score", 0),
                    "requested_info": threat_profile.get("requested_info", []),
                    "deception_techniques": threat_profile.get("deception_techniques", [])
                },
                "reasoning": threat_profile.get("reasoning", "Analysis complete"),
                "risk_factors": threat_profile.get("risk_factors", []),
                "urls_found": urls,
                "phones_found": phones,
                "emails_found": emails,
                "community_reports": community_reports,
                "recommendations": recommendations,
                "educational_tip": educational_tip,
                "notify_family": risk_level in ["HIGH", "CRITICAL"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cache high risk results
            if self.cache and risk_level in ["HIGH", "CRITICAL"]:
                try:
                    await self.cache.set(cache_key, result, ttl=300)
                except Exception:
                    pass
            
            return result
            
        except Exception as e:
            logger.error(f"Scam analysis failed: {str(e)}")
            # Return rule-based result instead of empty error response
            urls = self._extract_urls(message)
            phones = self._extract_phones(message)
            threat_profile = self._rule_based_analysis(message, urls, phones)
            risk_level = self._determine_risk_level(threat_profile, [])
            return {
                "is_scam": threat_profile.get("is_scam", False),
                "risk_score": threat_profile.get("risk_score", 0),
                "risk_level": risk_level,
                "confidence": threat_profile.get("confidence", 0.7),
                "scam_type": threat_profile.get("scam_type", "general"),
                "threat_profile": {},
                "reasoning": "Rule-based fallback analysis",
                "risk_factors": threat_profile.get("risk_factors", []),
                "urls_found": urls,
                "phones_found": phones,
                "emails_found": [],
                "community_reports": [],
                "recommendations": self._generate_recommendations(risk_level, threat_profile),
                "educational_tip": self._get_educational_tip("general"),
                "notify_family": risk_level in ["HIGH", "CRITICAL"],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _analyze_with_reasoning(
        self,
        message: str,
        urls: List[str],
        phones: List[str],
        emails: List[str],
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Use Foundry for advanced reasoning-based scam analysis"""
        
        if not self.foundry:
            return self._rule_based_analysis(message, urls, phones)
        
        try:
            prompt = f"""
            Analyze this message for scam indicators using advanced reasoning.
            Consider the psychology and manipulation tactics, not just keywords.

            Message: "{message}"
            
            Extracted data:
            - URLs: {urls}
            - Phone numbers: {phones}
            - Emails: {emails}
            
            Return JSON with:
            {{
                "is_scam": boolean,
                "risk_score": 0-100,
                "confidence": 0-1,
                "scam_type": "phishing|tech_support|grandparent|lottery|romance|investment|job|charity|general",
                "urgency_level": "LOW|MEDIUM|HIGH|CRITICAL",
                "emotional_manipulation": "LOW|MEDIUM|HIGH",
                "social_engineering_score": 0-100,
                "requested_info": [],
                "deception_techniques": [],
                "risk_factors": [{{"factor": "...", "severity": "HIGH", "explanation": "..."}}],
                "reasoning": "Detailed explanation"
            }}
            """
            
            response = await self.foundry.generate_chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            content = response.get("content", "{}")
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                if "is_scam" not in result:
                    result["is_scam"] = False
                if "risk_score" not in result:
                    result["risk_score"] = 0
                if "confidence" not in result:
                    result["confidence"] = 0.5
                if "risk_factors" not in result:
                    result["risk_factors"] = []
                return result
                
        except Exception as e:
            logger.error(f"Reasoning-based analysis failed: {e}")
        
        return self._rule_based_analysis(message, urls, phones)
    
    def _rule_based_analysis(self, message: str, urls: List[str], phones: List[str]) -> Dict[str, Any]:
        """Rule-based analysis as fallback"""
        score = 0
        factors = []
        message_lower = message.lower()
        
        # Prize/lottery scams
        prize_words = ["won", "winner", "prize", "lottery", "congratulations", "selected", "claim", "million", "billion", "reward"]
        prize_count = sum(1 for w in prize_words if w in message_lower)
        if prize_count > 0:
            score += prize_count * 15
            factors.append({
                "factor": "Prize/lottery scam indicators",
                "severity": "HIGH",
                "explanation": "Message claims you won something — classic scam tactic"
            })
        
        # Urgency detection
        urgency_words = ["urgent", "immediately", "asap", "now", "today only", "limited time", "act now", "hurry", "expire"]
        urgency_count = sum(1 for w in urgency_words if w in message_lower)
        if urgency_count > 0:
            score += urgency_count * 10
            factors.append({
                "factor": "Urgency tactics detected",
                "severity": "HIGH" if urgency_count > 2 else "MEDIUM",
                "explanation": "Message creates false urgency"
            })
        
        # Fear tactics
        fear_words = ["suspended", "closed", "legal action", "lawsuit", "arrest", "police", "irs", "tax"]
        if any(w in message_lower for w in fear_words):
            score += 20
            factors.append({
                "factor": "Fear tactics used",
                "severity": "HIGH",
                "explanation": "Message uses fear to manipulate"
            })
        
        # Money requests
        money_words = ["money", "cash", "wire", "transfer", "bank details", "credit card", "payment", "fee", "gift card"]
        if any(w in message_lower for w in money_words):
            score += 15
            factors.append({
                "factor": "Financial information requested",
                "severity": "HIGH",
                "explanation": "Asking for money or financial details"
            })
        
        # Personal info
        personal_words = ["ssn", "social security", "password", "pin", "date of birth", "account number"]
        if any(w in message_lower for w in personal_words):
            score += 25
            factors.append({
                "factor": "Personal information requested",
                "severity": "CRITICAL",
                "explanation": "Request for sensitive personal data"
            })
        
        # URLs
        if urls:
            score += 10 * len(urls)
            factors.append({
                "factor": f"Contains {len(urls)} URL(s)",
                "severity": "MEDIUM",
                "explanation": "Links can lead to phishing sites"
            })
        
        # Phones
        if phones:
            score += 5 * len(phones)
            factors.append({
                "factor": f"Contains {len(phones)} phone number(s)",
                "severity": "LOW",
                "explanation": "Unknown phone numbers could be scams"
            })
        
        # Determine scam type
        scam_type = "general"
        if "bank" in message_lower or "paypal" in message_lower or "account" in message_lower:
            scam_type = "phishing"
        elif "microsoft" in message_lower or "apple" in message_lower or "tech support" in message_lower:
            scam_type = "tech_support"
        elif "grandson" in message_lower or "granddaughter" in message_lower:
            scam_type = "grandparent"
        elif any(w in message_lower for w in ["won", "prize", "lottery", "winner"]):
            scam_type = "lottery"
        elif "love" in message_lower or "dating" in message_lower:
            scam_type = "romance"
        
        score = min(score, 100)
        
        return {
            "is_scam": score > 40,
            "risk_score": score,
            "confidence": min(0.5 + (score / 200), 0.95),
            "scam_type": scam_type,
            "urgency_level": "HIGH" if urgency_count > 2 else "MEDIUM" if urgency_count > 0 else "LOW",
            "emotional_manipulation": "HIGH" if any(w in message_lower for w in fear_words) else "MEDIUM" if urgency_count > 0 else "LOW",
            "social_engineering_score": score,
            "requested_info": [],
            "deception_techniques": [],
            "risk_factors": factors,
            "reasoning": f"Rule-based analysis: {len(factors)} risk indicators found, score {score}/100"
        }
    
    def _determine_risk_level(self, threat_profile: Dict, community_reports: List) -> str:
        risk_score = threat_profile.get("risk_score", 0)
        
        if community_reports:
            for report in community_reports:
                if report.get("reports", 0) > 10:
                    risk_score += 30
                elif report.get("reports", 0) > 5:
                    risk_score += 20
                else:
                    risk_score += 10
        
        risk_score = min(risk_score, 100)
        
        if risk_score >= 80:
            return "CRITICAL"
        elif risk_score >= 60:
            return "HIGH"
        elif risk_score >= 30:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendations(self, risk_level: str, threat_profile: Dict) -> List[str]:
        if risk_level == "CRITICAL":
            return [
                "🚨 DO NOT RESPOND to this message",
                "🚨 DO NOT CLICK any links",
                "🚨 DO NOT SHARE any personal information",
                "📞 Call your family member immediately",
                "🔒 Contact your bank directly using the number on your card",
                "📱 Block the sender",
                "👮 Report to FTC at reportfraud.ftc.gov"
            ]
        elif risk_level == "HIGH":
            return [
                "⚠️ Be very cautious with this message",
                "⚠️ Verify with a family member before responding",
                "⚠️ Do not share personal information",
                "📞 Contact the organization directly using official channels",
                "👀 Check the sender's identity carefully"
            ]
        elif risk_level == "MEDIUM":
            return [
                "🔍 Verify the source before taking any action",
                "📱 Don't click links - type URLs manually",
                "👪 Ask family if they've heard of this offer/request",
                "ℹ️ When in doubt, don't respond"
            ]
        else:
            return [
                "✅ Message appears safe",
                "👀 Stay vigilant - if something feels wrong, ask for help",
                "📚 Learn about common scams to protect yourself"
            ]
    
    def _get_educational_tip(self, scam_type: str) -> str:
        tips = {
            "phishing": "Legitimate companies never ask for passwords via email or text. Always type website addresses manually.",
            "tech_support": "Real tech support will never call you unsolicited. Hang up and call the company directly.",
            "grandparent": "Always verify by calling the family member directly on their known number.",
            "lottery": "If you didn't enter, you can't win. Never pay fees to receive a prize.",
            "romance": "Never send money to someone you haven't met in person.",
            "investment": "Guaranteed returns with no risk are a red flag for investment scams.",
            "job": "Legitimate employers don't ask for money upfront.",
            "charity": "Verify charities at CharityNavigator.org before donating.",
            "general": "When in doubt, don't respond. Verify with family and trust your instincts."
        }
        return tips.get(scam_type, tips["general"])
    
    def _extract_urls(self, text: str) -> List[str]:
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        return re.findall(url_pattern, text)
    
    def _extract_phones(self, text: str) -> List[str]:
        phone_pattern = r'(\+?\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}'
        return re.findall(phone_pattern, text)
    
    def _extract_emails(self, text: str) -> List[str]:
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(email_pattern, text)
    
    def _get_cache_key(self, message: str) -> str:
        content_hash = hashlib.md5(message.encode()).hexdigest()
        return f"scam:{content_hash}"