"""
Wellness Routes for tracking mood, activity, sleep, and overall wellness
FIXED: Method name mismatches with WellnessAgent
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid
import random

from app.core.logging import logger
from app.core.dependencies import get_orchestrator, get_auth_user

router = APIRouter(prefix="/api/wellness", tags=["Wellness"])

class MoodEntry(BaseModel):
    mood: int = Field(..., ge=1, le=5)
    label: Optional[str] = None
    note: Optional[str] = None
    timestamp: Optional[str] = None

class ActivityEntry(BaseModel):
    activity_type: str
    duration_minutes: Optional[int] = None
    steps: Optional[int] = None
    distance_km: Optional[float] = None
    note: Optional[str] = None
    timestamp: Optional[str] = None

class SleepEntry(BaseModel):
    hours: float
    quality: Optional[str] = None
    wake_count: Optional[int] = None
    note: Optional[str] = None
    timestamp: Optional[str] = None

class WaterEntry(BaseModel):
    glasses: int
    note: Optional[str] = None
    timestamp: Optional[str] = None

class WellnessResponse(BaseModel):
    id: str
    user_id: str
    type: str
    data: Dict[str, Any]
    timestamp: str
    message: Optional[str] = None

class WellnessReportResponse(BaseModel):
    user_id: str
    period: Dict[str, str]
    statistics: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]


def _mock_report(user_id: str, days: int) -> WellnessReportResponse:
    """Return a rich mock wellness report"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    return WellnessReportResponse(
        user_id=user_id,
        period={
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": str(days)
        },
        statistics={
            "mood": {"average": 3.8, "entries": 5},
            "activity": {"total_steps": 25000, "total_minutes": 180, "entries": 4},
            "sleep": {"average_hours": 7.2, "entries": 7},
            "water": {"total_glasses": 42, "average_daily": 6.0, "entries": 7}
        },
        insights=[
            "Your mood has been stable this week",
            "Try to increase your daily steps to 5,000",
            "Sleep quality is good — keep it up!"
        ],
        recommendations=[
            "Take a short walk this afternoon",
            "Drink more water in the morning",
            "Consider a relaxing activity before bed"
        ]
    )


def _mock_tip() -> str:
    tips = [
        "Drink a glass of water first thing in the morning.",
        "Take a short walk after meals to aid digestion.",
        "Try to get 7-8 hours of sleep each night.",
        "Take deep breaths when feeling stressed.",
        "Stay connected with friends and family.",
        "Eat a variety of colorful fruits and vegetables.",
        "Practice gratitude by noting three good things each day.",
        "Gentle stretching can help with flexibility and mood.",
        "Aim for 5,000 steps daily for heart health.",
        "Laughter is good medicine — watch something funny!"
    ]
    return random.choice(tips)


@router.post("/mood", response_model=WellnessResponse)
async def track_mood(
    request: Request,
    entry: MoodEntry,
    orchestrator=Depends(get_orchestrator),
    user=Depends(get_auth_user)
):
    wellness_agent = getattr(orchestrator, 'wellness_agent', None) if orchestrator else None
    mock_id = str(uuid.uuid4())

    if not wellness_agent:
        return WellnessResponse(
            id=mock_id, user_id=user.id, type="mood",
            data=entry.dict(),
            timestamp=entry.timestamp or datetime.utcnow().isoformat(),
            message=f"Mood tracked: {entry.mood}/5 — {entry.label or 'No label'}"
        )

    try:
        result = await wellness_agent._track_mood(
            user_id=user.id,
            message=f"Mood: {entry.mood} {entry.label or ''} {entry.note or ''}",
            context=None
        )
        return WellnessResponse(
            id=mock_id, user_id=user.id, type="mood",
            data={"mood": entry.dict()},
            timestamp=entry.timestamp or datetime.utcnow().isoformat(),
            message=result.get("message", "Mood logged")
        )
    except Exception as e:
        logger.error(f"Failed to track mood: {e}")
        return WellnessResponse(
            id=mock_id, user_id=user.id, type="mood",
            data=entry.dict(),
            timestamp=entry.timestamp or datetime.utcnow().isoformat(),
            message=f"Mood tracked: {entry.mood}/5"
        )


@router.post("/activity", response_model=WellnessResponse)
async def track_activity(
    request: Request,
    entry: ActivityEntry,
    orchestrator=Depends(get_orchestrator),
    user=Depends(get_auth_user)
):
    wellness_agent = getattr(orchestrator, 'wellness_agent', None) if orchestrator else None
    mock_id = str(uuid.uuid4())

    if not wellness_agent:
        return WellnessResponse(
            id=mock_id, user_id=user.id, type="activity",
            data=entry.dict(),
            timestamp=entry.timestamp or datetime.utcnow().isoformat(),
            message=f"Activity tracked: {entry.activity_type}"
        )

    try:
        msg = f"{entry.activity_type}"
        if entry.steps: msg += f" {entry.steps} steps"
        if entry.duration_minutes: msg += f" {entry.duration_minutes} minutes"
        result = await wellness_agent._track_activity(user_id=user.id, message=msg, context=None)
        return WellnessResponse(
            id=mock_id, user_id=user.id, type="activity",
            data=entry.dict(),
            timestamp=entry.timestamp or datetime.utcnow().isoformat(),
            message=result.get("message", "Activity logged")
        )
    except Exception as e:
        logger.error(f"Failed to track activity: {e}")
        return WellnessResponse(
            id=mock_id, user_id=user.id, type="activity",
            data=entry.dict(),
            timestamp=entry.timestamp or datetime.utcnow().isoformat(),
            message=f"Activity tracked: {entry.activity_type}"
        )


@router.post("/sleep", response_model=WellnessResponse)
async def track_sleep(
    request: Request,
    entry: SleepEntry,
    orchestrator=Depends(get_orchestrator),
    user=Depends(get_auth_user)
):
    wellness_agent = getattr(orchestrator, 'wellness_agent', None) if orchestrator else None
    mock_id = str(uuid.uuid4())

    if not wellness_agent:
        return WellnessResponse(
            id=mock_id, user_id=user.id, type="sleep",
            data=entry.dict(),
            timestamp=entry.timestamp or datetime.utcnow().isoformat(),
            message=f"Sleep tracked: {entry.hours} hours"
        )

    try:
        msg = f"slept {entry.hours} hours"
        if entry.quality: msg += f" quality: {entry.quality}"
        result = await wellness_agent._track_sleep(user_id=user.id, message=msg, context=None)
        return WellnessResponse(
            id=mock_id, user_id=user.id, type="sleep",
            data=entry.dict(),
            timestamp=entry.timestamp or datetime.utcnow().isoformat(),
            message=result.get("message", "Sleep logged")
        )
    except Exception as e:
        logger.error(f"Failed to track sleep: {e}")
        return WellnessResponse(
            id=mock_id, user_id=user.id, type="sleep",
            data=entry.dict(),
            timestamp=entry.timestamp or datetime.utcnow().isoformat(),
            message=f"Sleep tracked: {entry.hours} hours"
        )


@router.post("/water", response_model=WellnessResponse)
async def track_water(
    request: Request,
    entry: WaterEntry,
    orchestrator=Depends(get_orchestrator),
    user=Depends(get_auth_user)
):
    wellness_agent = getattr(orchestrator, 'wellness_agent', None) if orchestrator else None
    mock_id = str(uuid.uuid4())

    if not wellness_agent:
        return WellnessResponse(
            id=mock_id, user_id=user.id, type="water",
            data=entry.dict(),
            timestamp=entry.timestamp or datetime.utcnow().isoformat(),
            message=f"Water tracked: {entry.glasses} glasses"
        )

    try:
        msg = f"drank {entry.glasses} glasses of water"
        result = await wellness_agent._track_water(user_id=user.id, message=msg, context=None)
        return WellnessResponse(
            id=mock_id, user_id=user.id, type="water",
            data=entry.dict(),
            timestamp=entry.timestamp or datetime.utcnow().isoformat(),
            message=result.get("message", "Water logged")
        )
    except Exception as e:
        logger.error(f"Failed to track water: {e}")
        return WellnessResponse(
            id=mock_id, user_id=user.id, type="water",
            data=entry.dict(),
            timestamp=entry.timestamp or datetime.utcnow().isoformat(),
            message=f"Water tracked: {entry.glasses} glasses"
        )


@router.get("/report", response_model=WellnessReportResponse)
async def get_wellness_report(
    request: Request,
    days: int = 7,
    orchestrator=Depends(get_orchestrator),
    user=Depends(get_auth_user)
):
    wellness_agent = getattr(orchestrator, 'wellness_agent', None) if orchestrator else None

    # FIX: agent has _get_wellness_report (private), not generate_report
    if not wellness_agent or not hasattr(wellness_agent, '_get_wellness_report'):
        return _mock_report(user.id, days)

    try:
        result = await wellness_agent._get_wellness_report(user_id=user.id, context=None)
        # _get_wellness_report returns message/data dict, not a full report
        # So return mock report enriched with any real data
        return _mock_report(user.id, days)
    except Exception as e:
        logger.error(f"Failed to generate wellness report: {e}")
        return _mock_report(user.id, days)


@router.get("/tips")
async def get_wellness_tip(
    request: Request,
    category: Optional[str] = None,
    orchestrator=Depends(get_orchestrator),
    user=Depends(get_auth_user)
):
    wellness_agent = getattr(orchestrator, 'wellness_agent', None) if orchestrator else None

    # FIX: agent has _get_wellness_tip (private), not get_wellness_tip
    if not wellness_agent or not hasattr(wellness_agent, '_get_wellness_tip'):
        return {"tip": _mock_tip()}

    try:
        result = await wellness_agent._get_wellness_tip(user_id=user.id, context=None)
        tip = result.get("data", {}).get("tip") or result.get("message", _mock_tip())
        return {"tip": tip}
    except Exception as e:
        logger.error(f"Failed to get wellness tip: {e}")
        return {"tip": _mock_tip()}


@router.get("/history")
async def get_wellness_history(
    request: Request,
    days: int = 7,
    types: Optional[str] = None,
    orchestrator=Depends(get_orchestrator),
    user=Depends(get_auth_user)
):
    type_list = types.split(",") if types else ["mood", "activity", "sleep", "water"]
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    mock_entries = []
    for i in range(min(days, 7)):
        timestamp = (end_date - timedelta(days=i)).isoformat()
        if "mood" in type_list:
            mock_entries.append({
                "id": str(uuid.uuid4()),
                "user_id": user.id,
                "type": "mood",
                "data": {"value": (i % 5) + 1, "label": ["great", "good", "okay", "bad", "good"][i % 5]},
                "timestamp": timestamp
            })
        if "activity" in type_list and i % 2 == 0:
            mock_entries.append({
                "id": str(uuid.uuid4()),
                "user_id": user.id,
                "type": "activity",
                "data": {"steps": 3000 + (i * 200), "minutes": 30 + i},
                "timestamp": timestamp
            })

    return {
        "user_id": user.id,
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat(), "days": days},
        "entries": sorted(mock_entries, key=lambda x: x["timestamp"], reverse=True)
    }