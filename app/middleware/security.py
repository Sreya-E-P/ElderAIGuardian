"""
Security Middleware for Prompt Injection Protection
Cybersecurity Edge - Prevents malicious inputs from reaching LLMs
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

from app.core.logging import logger
from app.core.config import settings


class PromptInjectionProtection:
    """
    Security layer that scans all user inputs for prompt injection attempts
    and malicious patterns before they reach the LLM.
    """
    
    def __init__(self, db_service=None):
        self.db_service = db_service
        self.attack_patterns = self._load_attack_patterns()
        self.suspicious_keywords = self._load_suspicious_keywords()
        self.blocked_attempts = []
        
    def _load_attack_patterns(self) -> List[Dict[str, Any]]:
        """Load known prompt injection patterns"""
        return [
            {
                "pattern": r"ignore (all )?(previous|above|prior).*instructions",
                "severity": "HIGH",
                "description": "Instruction override attempt"
            },
            {
                "pattern": r"forget (everything|all|context)",
                "severity": "HIGH",
                "description": "Context reset attempt"
            },
            {
                "pattern": r"you are now (.*?)(?!assistant)",
                "severity": "MEDIUM",
                "description": "Role-play manipulation"
            },
            {
                "pattern": r"system.?prompt",
                "severity": "MEDIUM",
                "description": "System prompt extraction attempt"
            },
            {
                "pattern": r"reveal.*(instructions|guidelines|rules)",
                "severity": "HIGH",
                "description": "Instruction extraction attempt"
            },
            {
                "pattern": r"bypass (restrictions|filters|security)",
                "severity": "CRITICAL",
                "description": "Security bypass attempt"
            },
            {
                "pattern": r"<(script|iframe|img|embed|object)",
                "severity": "CRITICAL",
                "description": "HTML injection attempt"
            },
            {
                "pattern": r"javascript:",
                "severity": "CRITICAL",
                "description": "JavaScript injection attempt"
            },
            {
                "pattern": r"on\w+\s*=",
                "severity": "HIGH",
                "description": "Event handler injection"
            },
            {
                "pattern": r"eval\s*\(",
                "severity": "CRITICAL",
                "description": "Eval() injection attempt"
            }
        ]
    
    def _load_suspicious_keywords(self) -> List[str]:
        """Load suspicious keywords for input sanitization"""
        return [
            "hack", "exploit", "bypass", "jailbreak", "dan", "ignore instructions",
            "system prompt", "developer mode", "sudo", "admin", "root",
            "password", "credentials", "secret key", "api key", "token",
            "database", "delete", "drop table", "truncate", "alter table",
            "exec(", "system(", "os.", "subprocess", "import os", "import sys",
            "rm -rf", "format c:", "del /f", "chmod 777"
        ]
    
    async def scan_input(self, user_input: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Scan user input for prompt injection attempts
        Returns scan result with risk assessment
        """
        if not user_input:
            return {"safe": True, "risk_level": "LOW", "reasons": []}
        
        input_lower = user_input.lower()
        risk_factors = []
        matched_patterns = []
        
        # Check for attack patterns
        for pattern in self.attack_patterns:
            if re.search(pattern["pattern"], input_lower, re.IGNORECASE):
                matched_patterns.append(pattern)
                risk_factors.append({
                    "type": "pattern_match",
                    "pattern": pattern["pattern"],
                    "severity": pattern["severity"],
                    "description": pattern["description"]
                })
        
        # Check for suspicious keywords
        for keyword in self.suspicious_keywords:
            if keyword in input_lower:
                risk_factors.append({
                    "type": "suspicious_keyword",
                    "keyword": keyword,
                    "severity": "MEDIUM"
                })
        
        # Check for unusual length (potential data exfiltration)
        if len(user_input) > 5000:
            risk_factors.append({
                "type": "excessive_length",
                "length": len(user_input),
                "severity": "MEDIUM"
            })
        
        # Check for encoded content
        if self._contains_encoding(user_input):
            risk_factors.append({
                "type": "encoded_content",
                "severity": "HIGH"
            })
        
        # Determine overall risk level
        risk_level = self._determine_risk_level(risk_factors)
        
        # Log suspicious attempts
        if risk_level in ["HIGH", "CRITICAL"]:
            await self._log_attack_attempt(user_input, user_id, risk_factors)
        
        return {
            "safe": risk_level == "LOW",
            "risk_level": risk_level,
            "reasons": risk_factors,
            "sanitized_input": self._sanitize_input(user_input) if risk_level != "LOW" else user_input
        }
    
    def _contains_encoding(self, text: str) -> bool:
        """Check for encoded content (base64, hex, etc.)"""
        # Check for base64 pattern
        base64_pattern = r'^[A-Za-z0-9+/]{4,}=*$'
        if re.search(base64_pattern, text):
            return True
        
        # Check for hex pattern
        hex_pattern = r'^[0-9a-fA-F]{20,}$'
        if re.search(hex_pattern, text.replace(' ', '')):
            return True
        
        # Check for URL encoding
        if '%' in text and re.search(r'%[0-9A-Fa-f]{2}', text):
            return True
        
        return False
    
    def _determine_risk_level(self, risk_factors: List[Dict]) -> str:
        """Determine overall risk level based on factors"""
        if not risk_factors:
            return "LOW"
        
        # Check for critical severity
        for factor in risk_factors:
            if factor.get("severity") == "CRITICAL":
                return "CRITICAL"
        
        # Count high severity
        high_count = sum(1 for f in risk_factors if f.get("severity") == "HIGH")
        if high_count >= 2:
            return "CRITICAL"
        if high_count >= 1:
            return "HIGH"
        
        # Medium severity
        medium_count = sum(1 for f in risk_factors if f.get("severity") == "MEDIUM")
        if medium_count >= 3:
            return "HIGH"
        if medium_count >= 1:
            return "MEDIUM"
        
        return "LOW"
    
    def _sanitize_input(self, text: str) -> str:
        """Sanitize input by removing dangerous patterns"""
        # Remove script tags
        text = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', text, flags=re.IGNORECASE)
        
        # Remove event handlers
        text = re.sub(r'\bon\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
        
        # Remove javascript: URLs
        text = re.sub(r'javascript:\s*', '', text, flags=re.IGNORECASE)
        
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    async def _log_attack_attempt(self, input_text: str, user_id: Optional[str], risk_factors: List[Dict]):
        """Log attack attempts for security auditing"""
        attempt_hash = hashlib.sha256(input_text.encode()).hexdigest()[:16]
        
        log_entry = {
            "id": f"attack_{datetime.utcnow().timestamp()}",
            "timestamp": datetime.utcnow().isoformat(),
            "input_hash": attempt_hash,
            "input_preview": input_text[:200],
            "user_id": user_id,
            "risk_factors": risk_factors,
            "source_ip": None  # Would be populated from request
        }
        
        self.blocked_attempts.append(log_entry)
        
        # Keep only last 1000 attempts
        if len(self.blocked_attempts) > 1000:
            self.blocked_attempts = self.blocked_attempts[-1000:]
        
        # Log to database if available
        if self.db_service and hasattr(self.db_service, 'log_audit_event'):
            try:
                await self.db_service.log_audit_event({
                    "event_type": "prompt_injection_attempt",
                    "severity": "HIGH",
                    "details": log_entry
                })
            except:
                pass
        
        logger.warning(f"🚨 Prompt injection attempt blocked: {attempt_hash} - {risk_factors[0].get('description', 'Unknown')}")
    
    async def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics for dashboard"""
        return {
            "total_blocked": len(self.blocked_attempts),
            "recent_attempts": self.blocked_attempts[-10:],
            "attack_patterns": len(self.attack_patterns),
            "suspicious_keywords": len(self.suspicious_keywords),
            "timestamp": datetime.utcnow().isoformat()
        }


# Middleware for FastAPI
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware to protect against prompt injection"""
    
    def __init__(self, app, security_service=None):
        super().__init__(app)
        self.security = security_service or PromptInjectionProtection()
    
    async def dispatch(self, request: Request, call_next):
        # Only scan POST/PUT requests with JSON body
        if request.method in ["POST", "PUT"] and "application/json" in request.headers.get("content-type", ""):
            try:
                body = await request.json()
                
                # Extract user input from common fields
                user_input = None
                if isinstance(body, dict):
                    for field in ["message", "content", "text", "input", "prompt"]:
                        if field in body and isinstance(body[field], str):
                            user_input = body[field]
                            break
                
                if user_input:
                    # Get user ID if available
                    user_id = None
                    if hasattr(request.state, "user_id"):
                        user_id = request.state.user_id
                    
                    # Scan input
                    scan_result = await self.security.scan_input(user_input, user_id)
                    
                    # Block if critical risk
                    if scan_result["risk_level"] == "CRITICAL":
                        raise HTTPException(
                            status_code=400,
                            detail="Input blocked for security reasons"
                        )
                    
                    # Replace with sanitized version if needed
                    if scan_result["sanitized_input"] != user_input:
                        # Update the body with sanitized input
                        for field in ["message", "content", "text", "input", "prompt"]:
                            if field in body:
                                body[field] = scan_result["sanitized_input"]
                                break
                        
                        # Replace request body (requires hack - in production use proper middleware)
                        request._body = json.dumps(body).encode()
            
            except Exception as e:
                logger.error(f"Security middleware error: {e}")
        
        return await call_next(request)