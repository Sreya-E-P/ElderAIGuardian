"""
Medication Routes
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

router = APIRouter(prefix="/api/medication", tags=["Medication"])

class Medication(BaseModel):
    """Medication model"""
    id: Optional[str] = None
    name: str
    dosage: str
    schedule: List[str]
    instructions: Optional[str] = None
    start_date: Optional[str] = None
    active: bool = True

class ReminderRequest(BaseModel):
    """Reminder request"""
    user_id: str
    medication_id: Optional[str] = None

class AdherenceRecord(BaseModel):
    """Adherence record"""
    user_id: str
    medication_id: str
    medication_name: str
    status: str  # taken, missed, skipped
    scheduled_time: str
    taken_time: Optional[str] = None
    notes: Optional[str] = None

@router.post("/add")
async def add_medication(user_id: str, medication: Medication):
    """Add new medication"""
    medication.id = str(uuid.uuid4())
    medication.start_date = datetime.utcnow().isoformat()
    
    # In production, save to database
    return {
        "status": "success",
        "medication": medication.dict()
    }

@router.get("/list/{user_id}")
async def list_medications(user_id: str):
    """List user's medications"""
    # In production, get from database
    medications = []
    return {
        "user_id": user_id,
        "medications": medications,
        "count": len(medications)
    }

@router.post("/remind")
async def send_reminder(request: Request, reminder_request: ReminderRequest):
    """Send medication reminder"""
    
    medication_agent = request.app.state.orchestrator.medication_agent if request.app.state.orchestrator else None
    
    if not medication_agent:
        raise HTTPException(status_code=503, detail="Medication service not available")
    
    # Simplified reminder
    return {
        "status": "reminder_sent",
        "user_id": reminder_request.user_id,
        "message": "Time to take your medication"
    }

@router.post("/adherence/record")
async def record_adherence(record: AdherenceRecord):
    """Record medication adherence"""
    # In production, save to database
    return {
        "status": "recorded",
        "record": record.dict()
    }

@router.get("/adherence/{user_id}")
async def get_adherence(user_id: str, days: int = 7):
    """Get adherence statistics"""
    # In production, calculate from database
    return {
        "user_id": user_id,
        "period_days": days,
        "adherence_rate": 85.5,
        "total_doses": 14,
        "taken": 12,
        "missed": 2,
        "trend": "improving"
    }

@router.delete("/{medication_id}")
async def delete_medication(medication_id: str):
    """Delete medication"""
    return {
        "status": "deleted",
        "medication_id": medication_id
    }
