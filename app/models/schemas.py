"""
Database Models and Schemas
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import uuid
import re

# ============================================================================
# USER MODELS
# ============================================================================

class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    emergency_contacts: Optional[List[Dict[str, Any]]] = []
    medical_conditions: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    medications: Optional[List[str]] = []
    preferences: Optional[Dict[str, Any]] = {}

class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v

class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str

class User(UserBase):
    """User response model"""
    id: str
    is_active: bool = True
    is_verified: bool = False
    role: str = "user"
    created_at: str
    updated_at: str
    last_login: Optional[str] = None

class UserInDB(User):
    """User in database model (includes hashed password)"""
    hashed_password: str

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User

# ============================================================================
# CHAT MODELS
# ============================================================================

class Message(BaseModel):
    """Chat message model"""
    id: str
    role: str  # user, assistant, system
    content: str
    timestamp: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    agent: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatSession(BaseModel):
    """Chat session model"""
    id: str
    user_id: str
    title: Optional[str] = None
    messages: List[Message] = []
    context: Dict[str, Any] = {}
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    stream: bool = False
    temperature: float = 0.7
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    """Chat response model"""
    id: str
    session_id: str
    response: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    agent: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    timestamp: str
    processing_time_ms: float

class ChatHistory(BaseModel):
    """Chat history model"""
    session_id: str
    messages: List[Message]
    context: Dict[str, Any]
    created_at: str
    updated_at: str

# ============================================================================
# EMERGENCY MODELS
# ============================================================================

class Location(BaseModel):
    """Location model"""
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    timestamp: Optional[str] = None

class EmergencyContact(BaseModel):
    """Emergency contact model"""
    id: str
    name: str
    relationship: str
    phone: str
    email: Optional[str] = None
    priority: str  # primary, secondary
    notify_sms: bool = True
    notify_call: bool = True
    notify_whatsapp: bool = False
    created_at: str
    updated_at: Optional[str] = None

class Emergency(BaseModel):
    """Emergency model"""
    id: str
    user_id: str
    type: str  # medical, fire, security, fall, general
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    status: str  # ACTIVE, RESOLVED, CANCELLED
    message: str
    location: Optional[Location] = None
    timestamp: str
    resolved_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    resolved_by: Optional[str] = None
    cancelled_by: Optional[str] = None
    contacts_notified: List[str] = []
    services_notified: bool = False
    actions_taken: List[Dict[str, Any]] = []
    resolution_note: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# ============================================================================
# MEDICATION MODELS
# ============================================================================

class MedicationSchedule(BaseModel):
    """Medication schedule model"""
    time: str  # HH:MM format
    days: List[str]  # Monday, Tuesday, etc. or daily
    dosage: str
    instructions: Optional[str] = None

class Medication(BaseModel):
    """Medication model"""
    id: str
    user_id: str
    name: str
    dosage: str
    form: str  # tablet, capsule, liquid, injection
    strength: str
    schedule: List[MedicationSchedule]
    start_date: str
    end_date: Optional[str] = None
    refill_date: Optional[str] = None
    refill_reminder: bool = True
    quantity: int
    instructions: Optional[str] = None
    side_effects: Optional[List[str]] = None
    prescribed_by: Optional[str] = None
    pharmacy: Optional[Dict[str, Any]] = None
    active: bool = True
    created_at: str
    updated_at: Optional[str] = None

class MedicationReminder(BaseModel):
    """Medication reminder model"""
    id: str
    user_id: str
    medication_id: str
    medication_name: str
    scheduled_time: str
    status: str  # pending, taken, missed, skipped
    taken_time: Optional[str] = None
    notes: Optional[str] = None
    created_at: str

class MedicationAdherence(BaseModel):
    """Medication adherence model"""
    id: str
    user_id: str
    medication_id: str
    medication_name: str
    date: str
    scheduled_count: int
    taken_count: int
    missed_count: int
    adherence_rate: float
    notes: Optional[str] = None

# ============================================================================
# WELLNESS MODELS
# ============================================================================

class MoodEntry(BaseModel):
    """Mood entry model"""
    id: str
    user_id: str
    mood: int  # 1-5 scale
    label: Optional[str] = None
    note: Optional[str] = None
    timestamp: str

class ActivityEntry(BaseModel):
    """Activity entry model"""
    id: str
    user_id: str
    activity_type: str  # walking, running, exercise, etc.
    duration_minutes: Optional[int] = None
    steps: Optional[int] = None
    distance_km: Optional[float] = None
    calories_burned: Optional[int] = None
    heart_rate_avg: Optional[int] = None
    note: Optional[str] = None
    timestamp: str

class SleepEntry(BaseModel):
    """Sleep entry model"""
    id: str
    user_id: str
    sleep_start: str
    sleep_end: str
    duration_hours: float
    quality: Optional[str] = None  # poor, fair, good, excellent
    deep_sleep_minutes: Optional[int] = None
    rem_sleep_minutes: Optional[int] = None
    wake_count: Optional[int] = None
    note: Optional[str] = None
    timestamp: str

class WaterEntry(BaseModel):
    """Water intake entry model"""
    id: str
    user_id: str
    glasses: int
    ounces: Optional[int] = None
    note: Optional[str] = None
    timestamp: str

class HealthMetric(BaseModel):
    """Health metric model"""
    id: str
    user_id: str
    metric_type: str  # heart_rate, blood_pressure, weight, glucose, etc.
    value: float
    unit: str
    timestamp: str
    notes: Optional[str] = None

class WellnessReport(BaseModel):
    """Wellness report model"""
    user_id: str
    start_date: str
    end_date: str
    mood_stats: Dict[str, Any]
    activity_stats: Dict[str, Any]
    sleep_stats: Dict[str, Any]
    water_stats: Dict[str, Any]
    health_metrics: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]

# ============================================================================
# SCAM DETECTION MODELS
# ============================================================================

class ScamAnalysisRequest(BaseModel):
    """Scam analysis request"""
    message: str
    url: Optional[str] = None
    sender: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ScamAnalysisResponse(BaseModel):
    """Scam analysis response"""
    is_scam: bool
    risk_score: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float
    detection_methods: List[str]
    risk_factors: List[str]
    urls_found: List[str]
    phones_found: List[str]
    recommendations: List[str]
    timestamp: str
    analysis_id: Optional[str] = None

class ScamReport(BaseModel):
    """Scam report model"""
    id: str
    user_id: str
    message: str
    analysis_result: ScamAnalysisResponse
    user_action: str  # reported, ignored, clicked, responded
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

# ============================================================================
# NOTIFICATION MODELS
# ============================================================================

class Notification(BaseModel):
    """Notification model"""
    id: str
    user_id: str
    type: str  # emergency, medication, scam, wellness, system
    title: str
    body: str
    priority: str  # LOW, MEDIUM, HIGH, URGENT
    data: Optional[Dict[str, Any]] = None
    read: bool = False
    read_at: Optional[str] = None
    action_url: Optional[str] = None
    image_url: Optional[str] = None
    created_at: str
    expires_at: Optional[str] = None

class NotificationPreference(BaseModel):
    """Notification preference model"""
    user_id: str
    email_enabled: bool = True
    sms_enabled: bool = True
    push_enabled: bool = True
    whatsapp_enabled: bool = False
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
    emergency_always_notify: bool = True
    medication_reminders: bool = True
    scam_alerts: bool = True
    wellness_tips: bool = True
    daily_summary: bool = True
    weekly_report: bool = True

# ============================================================================
# ANALYTICS MODELS
# ============================================================================

class AnalyticsEvent(BaseModel):
    """Analytics event model"""
    id: str
    user_id: Optional[str] = None
    event_type: str
    event_name: str
    properties: Dict[str, Any]
    timestamp: str
    session_id: Optional[str] = None

class DashboardSummary(BaseModel):
    """Dashboard summary model"""
    user_id: str
    health_score: float
    medications_taken: int
    total_medications: int
    next_medication: Optional[str] = None
    heart_rate: Optional[int] = None
    steps: int
    step_goal: int = 5000
    water_glasses: int
    water_goal: int = 8
    mood_today: Optional[int] = None
    sleep_hours: Optional[float] = None
    scams_detected: int
    active_alerts: int
    unread_notifications: int
    emergency_contacts_count: int
    last_emergency: Optional[str] = None
    wellness_insights: List[str]

# ============================================================================
# RESPONSE MODELS
# ============================================================================

class ResponseModel(BaseModel):
    """Generic response model"""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class PaginatedResponse(BaseModel):
    """Paginated response model"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_previous: bool