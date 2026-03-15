"""
Scam Detection Routes - FIXED
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/api/scam", tags=["Scam Detection"])

class ScamAnalysisRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    user_id: str
    url: Optional[str] = None
    metadata: Optional[dict] = None

class ScamAnalysisResponse(BaseModel):
    is_scam: bool
    risk_score: float
    risk_level: str
    confidence: float
    detection_methods: dict
    details: dict
    recommendations: List[str]
    timestamp: str

@router.post("/analyze", response_model=ScamAnalysisResponse)
async def analyze_scam(request: Request, analysis_request: ScamAnalysisRequest):
    """Analyze message for scams"""

    scam_agent = None
    if hasattr(request.app.state, 'orchestrator') and request.app.state.orchestrator:
        scam_agent = getattr(request.app.state.orchestrator, 'scam_agent', None)

    if not scam_agent:
        # Fallback rule-based analysis when agent not available
        return _rule_based_fallback(analysis_request.message)

    try:
        result = await scam_agent.analyze(
            message=analysis_request.message,
            metadata=analysis_request.metadata
        )

        # FIXED: Map agent result fields to response model
        return ScamAnalysisResponse(
            is_scam=result.get("is_scam", False),
            risk_score=float(result.get("risk_score", 0)),
            risk_level=result.get("risk_level", "LOW"),
            confidence=float(result.get("confidence", 0.5)),
            detection_methods={
                "keyword_analysis": True,
                "ai_reasoning": bool(result.get("reasoning")),
                "threat_profiling": bool(result.get("threat_profile")),
                "community_reports": bool(result.get("community_reports")),
                "scam_type": result.get("scam_type", "general"),
            },
            details={
                "threat_profile": result.get("threat_profile", {}),
                "reasoning": result.get("reasoning", ""),
                "risk_factors": result.get("risk_factors", []),
                "urls_found": result.get("urls_found", []),
                "phones_found": result.get("phones_found", []),
                "educational_tip": result.get("educational_tip", ""),
            },
            recommendations=result.get("recommendations", ["Stay vigilant"]),
            timestamp=result.get("timestamp", datetime.utcnow().isoformat())
        )

    except Exception as e:
        # Return rule-based fallback instead of 500
        return _rule_based_fallback(analysis_request.message)


def _rule_based_fallback(message: str) -> ScamAnalysisResponse:
    """Rule-based scam detection fallback"""
    message_lower = message.lower()
    score = 0
    recommendations = []
    detection_methods = {"keyword_analysis": True}

    # High risk patterns
    high_risk = [
        "won", "winner", "prize", "lottery", "congratulations",
        "million", "billion", "claim", "click here", "urgent",
        "account suspended", "verify your", "password", "social security",
        "wire transfer", "gift card", "irs", "tax refund"
    ]

    medium_risk = [
        "free", "offer", "limited time", "act now", "bank",
        "paypal", "bitcoin", "crypto", "investment", "guaranteed"
    ]

    for word in high_risk:
        if word in message_lower:
            score += 20

    for word in medium_risk:
        if word in message_lower:
            score += 10

    score = min(score, 100)

    if score >= 60:
        risk_level = "HIGH"
        is_scam = True
        recommendations = [
            "⚠️ This message shows HIGH RISK scam indicators",
            "🚨 DO NOT click any links or call any numbers",
            "🚨 DO NOT share personal or financial information",
            "📞 Contact family immediately",
            "🛡️ Block and report the sender"
        ]
    elif score >= 30:
        risk_level = "MEDIUM"
        is_scam = False
        recommendations = [
            "🔍 Verify the source before taking any action",
            "📱 Don't click links - type URLs manually",
            "👪 Ask family if this looks legitimate"
        ]
    else:
        risk_level = "LOW"
        is_scam = False
        recommendations = [
            "✅ Message appears safe",
            "👀 Stay vigilant - if something feels wrong, ask for help"
        ]

    return ScamAnalysisResponse(
        is_scam=is_scam,
        risk_score=float(score),
        risk_level=risk_level,
        confidence=0.85,
        detection_methods=detection_methods,
        details={
            "analysis": "Rule-based keyword analysis",
            "score_breakdown": f"Risk score: {score}/100"
        },
        recommendations=recommendations,
        timestamp=datetime.utcnow().isoformat()
    )


@router.post("/url")
async def check_url(url: str):
    suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq']
    is_suspicious = any(url.endswith(tld) for tld in suspicious_tlds)
    return {
        "url": url,
        "is_suspicious": is_suspicious,
        "risk_level": "HIGH" if is_suspicious else "LOW"
    }


@router.get("/stats/{user_id}")
async def get_scam_stats(user_id: str):
    return {
        "user_id": user_id,
        "total_analyzed": 0,
        "scams_detected": 0,
        "last_analysis": None
    }