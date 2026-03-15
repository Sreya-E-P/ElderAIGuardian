"""
Medication Agent
Manages medication schedules, reminders, and adherence tracking
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
import re
import json

from app.core.logging import logger

class MedicationAgent:
    """Agent specialized in medication management"""
    
    def __init__(self, 
                 foundry_agent=None, 
                 model_router=None,
                 cosmos_service=None, 
                 cache_service=None,
                 notification_service=None):
        
        self.foundry_agent = foundry_agent
        self.model_router = model_router
        self.cosmos_service = cosmos_service
        self.cache_service = cache_service
        self.notification_service = notification_service
        self.reminders = {}
        self.medications = {}
        self.is_healthy = False
    
    async def initialize(self):
        """Initialize agent resources"""
        self.is_healthy = True
        logger.info("MedicationAgent initialized")
    
    async def handle_request(
        self,
        user_id: str,
        message: str,
        context: Any,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Handle medication-related requests"""
        
        message_lower = message.lower()
        
        if "add" in message_lower and any(word in message_lower for word in ["medication", "medicine", "pill"]):
            return await self._add_medication(user_id, message, context)
        
        if any(word in message_lower for word in ["list", "show", "my medications"]):
            return await self._list_medications(user_id, context)
        
        if "take" in message_lower or "took" in message_lower:
            return await self._mark_taken(user_id, message, context)
        
        if "miss" in message_lower or "missed" in message_lower:
            return await self._mark_missed(user_id, message, context)
        
        if "next" in message_lower:
            return await self._get_next_reminder(user_id, context)
        
        if any(word in message_lower for word in ["adherence", "report", "progress", "stat"]):
            return await self._get_adherence_report(user_id, context)
        
        if "refill" in message_lower:
            return await self._check_refills(user_id, context)
        
        return {
            "message": "I can help you manage your medications. You can ask me to: add a medication, list your medications, mark when you've taken them, check your next reminder, or get an adherence report.",
            "data": {},
            "notify_family": False
        }
    
    async def _add_medication(self, user_id: str, message: str, context) -> Dict[str, Any]:
        """Add new medication"""
        
        if self.foundry_agent:
            try:
                prompt = f"""
                Extract medication information from this message:
                "{message}"
                
                Return JSON with:
                - name: medication name
                - dosage: dosage amount (e.g., "10mg")
                - frequency: how often (e.g., "twice daily", "once daily")
                - times: list of times (e.g., ["08:00", "20:00"])
                - instructions: any special instructions
                """
                
                response = await self.foundry_agent.generate_chat(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=300
                )
                
                content = response.get("content", "")
                try:
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        extracted = json.loads(json_match.group())
                        
                        medication = {
                            "id": str(uuid.uuid4()),
                            "user_id": user_id,
                            "name": extracted.get("name", "Unknown"),
                            "dosage": extracted.get("dosage", "As prescribed"),
                            "frequency": extracted.get("frequency", "daily"),
                            "schedule": extracted.get("times", ["08:00", "20:00"]),
                            "instructions": extracted.get("instructions", "Take as directed"),
                            "start_date": datetime.utcnow().isoformat(),
                            "active": True,
                            "created_at": datetime.utcnow().isoformat()
                        }
                        
                        if self.cosmos_service:
                            await self.cosmos_service.save_medication(medication)
                        
                        if user_id not in self.medications:
                            self.medications[user_id] = []
                        self.medications[user_id].append(medication)
                        
                        await self._schedule_reminders(user_id, medication)
                        
                        return {
                            "message": f"✅ I've added {medication['name']} ({medication['dosage']}) to your medications. Remember to take it {medication['frequency']}.",
                            "data": {"medication": medication},
                            "notify_family": False
                        }
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Failed to extract medication info: {str(e)}")
        
        # Simple parsing fallback
        words = message.split()
        medication_name = "Unknown"
        
        for i, word in enumerate(words):
            if word.lower() in ["medication", "medicine", "pill", "tablet"] and i + 1 < len(words):
                medication_name = words[i + 1]
                break
        
        medication = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": medication_name,
            "dosage": "As prescribed",
            "frequency": "twice daily",
            "schedule": ["08:00", "20:00"],
            "instructions": "Take with food",
            "start_date": datetime.utcnow().isoformat(),
            "active": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if self.cosmos_service:
            await self.cosmos_service.save_medication(medication)
        
        if user_id not in self.medications:
            self.medications[user_id] = []
        self.medications[user_id].append(medication)
        
        await self._schedule_reminders(user_id, medication)
        
        return {
            "message": f"✅ I've added {medication_name} to your medications. Remember to take it twice daily (morning and evening).",
            "data": {"medication": medication},
            "notify_family": False
        }
    
    async def _list_medications(self, user_id: str, context) -> Dict[str, Any]:
        """List user's medications"""
        
        medications = []
        
        if self.cosmos_service:
            try:
                medications = await self.cosmos_service.get_user_medications(user_id) or []
            except Exception as e:
                logger.error(f"Failed to get medications: {str(e)}")
        
        if not medications and user_id in self.medications:
            medications = self.medications[user_id]
        
        if not medications:
            return {
                "message": "You don't have any medications added yet. Would you like me to add one?",
                "data": {},
                "notify_family": False
            }
        
        med_list = []
        for med in medications:
            if med.get("active", True):
                schedule = ", ".join(med.get("schedule", []))
                med_list.append(f"• {med['name']} - {med.get('dosage', 'As prescribed')} at {schedule}")
        
        if med_list:
            message = "Here are your current medications:\n" + "\n".join(med_list)
        else:
            message = "You don't have any active medications."
        
        return {
            "message": message,
            "data": {"medications": medications},
            "notify_family": False
        }
    
    async def _mark_taken(self, user_id: str, message: str, context) -> Dict[str, Any]:
        """Mark medication as taken"""
        
        medication_name = self._extract_medication_name(message)
        
        if not medication_name:
            return {
                "message": "Which medication did you take? Please specify the name.",
                "data": {},
                "notify_family": False
            }
        
        medication = await self._find_medication(user_id, medication_name)
        
        if not medication:
            return {
                "message": f"I couldn't find '{medication_name}' in your medications. Please check the name or add it first.",
                "data": {},
                "notify_family": False
            }
        
        now = datetime.utcnow()
        current_time = now.strftime("%H:%M")
        
        adherence_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "medication_id": medication["id"],
            "medication_name": medication["name"],
            "status": "taken",
            "scheduled_time": current_time,
            "taken_time": now.isoformat(),
            "timestamp": now.isoformat()
        }
        
        if self.cosmos_service:
            try:
                await self.cosmos_service.save_wellness_entry(adherence_record)
            except Exception as e:
                logger.error(f"Failed to record adherence: {str(e)}")
        
        reminder_key = f"{user_id}:{medication['id']}:{current_time}"
        if reminder_key in self.reminders:
            del self.reminders[reminder_key]
        
        return {
            "message": f"✅ Great! I've recorded that you took {medication['name']}.",
            "data": {"adherence": adherence_record},
            "notify_family": False
        }
    
    async def _mark_missed(self, user_id: str, message: str, context) -> Dict[str, Any]:
        """Mark medication as missed"""
        
        medication_name = self._extract_medication_name(message)
        
        if not medication_name:
            return {
                "message": "Which medication did you miss?",
                "data": {},
                "notify_family": False
            }
        
        medication = await self._find_medication(user_id, medication_name)
        
        if not medication:
            return {
                "message": f"I couldn't find '{medication_name}' in your medications.",
                "data": {},
                "notify_family": False
            }
        
        now = datetime.utcnow()
        
        adherence_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "medication_id": medication["id"],
            "medication_name": medication["name"],
            "status": "missed",
            "scheduled_time": now.strftime("%H:%M"),
            "timestamp": now.isoformat(),
            "notes": message
        }
        
        if self.cosmos_service:
            try:
                await self.cosmos_service.save_wellness_entry(adherence_record)
            except Exception as e:
                logger.error(f"Failed to record missed dose: {str(e)}")
        
        if self.notification_service:
            try:
                await self.notification_service.send_notification(
                    user_id=user_id,
                    type="missed_medication",
                    title="⚠️ Missed Medication",
                    body=f"{medication['name']} was missed at {now.strftime('%I:%M %p')}",
                    data={"medication": medication},
                    priority="HIGH"
                )
            except Exception as e:
                logger.error(f"Failed to send notification: {str(e)}")
        
        return {
            "message": f"I've noted that you missed {medication['name']}. Would you like me to remind you again?",
            "data": {},
            "notify_family": True,
            "notification_type": "missed_medication",
            "priority": "HIGH"
        }
    
    async def _get_next_reminder(self, user_id: str, context) -> Dict[str, Any]:
        """Get next medication reminder"""
        
        now = datetime.utcnow()
        current_time = now.strftime("%H:%M")
        current_minutes = self._time_to_minutes(current_time)
        
        next_reminder = None
        next_time_diff = float('inf')
        
        medications = []
        if self.cosmos_service:
            try:
                medications = await self.cosmos_service.get_user_medications(user_id) or []
            except Exception as e:
                logger.error(f"Failed to get medications: {str(e)}")
        
        if not medications and user_id in self.medications:
            medications = self.medications[user_id]
        
        if not medications:
            return {
                "message": "You don't have any upcoming medication reminders.",
                "data": {},
                "notify_family": False
            }
        
        for med in medications:
            if not med.get("active", True):
                continue
            
            for scheduled_time in med.get("schedule", []):
                scheduled_minutes = self._time_to_minutes(scheduled_time)
                
                if scheduled_minutes > current_minutes:
                    diff = scheduled_minutes - current_minutes
                else:
                    diff = (24*60 - current_minutes) + scheduled_minutes
                
                if diff < next_time_diff:
                    next_time_diff = diff
                    next_reminder = {
                        "medication": med["name"],
                        "dosage": med.get("dosage", "As prescribed"),
                        "time": scheduled_time,
                        "minutes_until": diff
                    }
        
        if next_reminder:
            hours = next_reminder["minutes_until"] // 60
            minutes = next_reminder["minutes_until"] % 60
            
            if hours > 0:
                time_str = f"{hours} hour{'s' if hours > 1 else ''}"
                if minutes > 0:
                    time_str += f" and {minutes} minute{'s' if minutes > 1 else ''}"
            else:
                time_str = f"{minutes} minute{'s' if minutes > 1 else ''}"
            
            return {
                "message": f"Your next reminder is {next_reminder['medication']} ({next_reminder['dosage']}) at {next_reminder['time']} (in {time_str}).",
                "data": {"next_reminder": next_reminder},
                "notify_family": False
            }
        
        return {
            "message": "You don't have any upcoming medication reminders.",
            "data": {},
            "notify_family": False
        }
    
    async def _get_adherence_report(self, user_id: str, context) -> Dict[str, Any]:
        """Get adherence report - FIXED: removed start_date/end_date args"""
        
        records = []
        if self.cosmos_service:
            try:
                # FIXED: was get_adherence_records(user_id, start_date, end_date) - wrong args
                records = await self.cosmos_service.get_adherence_records(user_id, days=7) or []
            except Exception as e:
                logger.error(f"Failed to get adherence records: {str(e)}")
        
        total_doses = len(records)
        taken_doses = sum(1 for r in records if r.get("status") == "taken")
        missed_doses = sum(1 for r in records if r.get("status") == "missed")
        
        adherence_rate = (taken_doses / total_doses * 100) if total_doses > 0 else 100
        
        insights = []
        if adherence_rate >= 95:
            insights.append("Excellent adherence! Keep up the great work! 🎉")
        elif adherence_rate >= 85:
            insights.append("Good adherence. Try to be more consistent with timing.")
        elif adherence_rate >= 70:
            insights.append("Your adherence could use improvement. Consider setting additional reminders.")
        else:
            insights.append("Your medication adherence is low. This is important for your health.")
            insights.append("I've notified your family about this.")
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": 7
            },
            "statistics": {
                "total_doses": total_doses,
                "taken": taken_doses,
                "missed": missed_doses,
                "adherence_rate": round(adherence_rate, 1)
            },
            "insights": insights
        }
        
        notify_family = adherence_rate < 70
        if notify_family and self.notification_service:
            try:
                await self.notification_service.send_notification(
                    user_id=user_id,
                    type="low_adherence",
                    title="⚠️ Low Medication Adherence",
                    body=f"Adherence rate is {adherence_rate:.1f}% over the past 7 days.",
                    data={"report": report},
                    priority="MEDIUM"
                )
            except Exception as e:
                logger.error(f"Failed to send notification: {str(e)}")
        
        message = f"Your medication adherence over the past 7 days is {adherence_rate:.1f}%.\n"
        message += "\n".join([f"• {i}" for i in insights])
        
        return {
            "message": message,
            "data": {"report": report},
            "notify_family": notify_family
        }
    
    async def _check_refills(self, user_id: str, context) -> Dict[str, Any]:
        """Check for medications needing refill"""
        
        medications = []
        if self.cosmos_service:
            try:
                medications = await self.cosmos_service.get_user_medications(user_id) or []
            except Exception as e:
                logger.error(f"Failed to get medications: {str(e)}")
        
        if not medications and user_id in self.medications:
            medications = self.medications[user_id]
        
        if not medications:
            return {
                "message": "You don't have any medications to check for refills.",
                "data": {},
                "notify_family": False
            }
        
        now = datetime.utcnow()
        needing_refill = []
        
        for med in medications:
            if med.get("refill_date"):
                try:
                    refill_date = datetime.fromisoformat(med["refill_date"])
                    days_until = (refill_date - now).days
                    
                    if days_until <= 7:
                        needing_refill.append({
                            "medication": med["name"],
                            "days_until": days_until,
                            "refill_date": med["refill_date"]
                        })
                except Exception:
                    pass
        
        if needing_refill:
            message = "Medications needing refill:\n"
            for med in needing_refill:
                if med["days_until"] <= 0:
                    message += f"• {med['medication']} - OVERDUE (was due {abs(med['days_until'])} days ago)\n"
                else:
                    message += f"• {med['medication']} - due in {med['days_until']} days\n"
            
            return {
                "message": message,
                "data": {"needing_refill": needing_refill},
                "notify_family": True
            }
        
        return {
            "message": "All your medications have refills available when needed.",
            "data": {},
            "notify_family": False
        }
    
    async def send_reminder(self, user_id: str, medication_id: str = None, force: bool = False) -> Dict:
        """Send a medication reminder"""
        
        if medication_id:
            medications = []
            if self.cosmos_service:
                try:
                    medications = await self.cosmos_service.get_user_medications(user_id) or []
                except Exception:
                    pass
            elif user_id in self.medications:
                medications = self.medications[user_id]
            
            medication = next((m for m in medications if m["id"] == medication_id), None)
            
            if medication:
                return {
                    "status": "reminder_sent",
                    "user_id": user_id,
                    "medication": medication["name"],
                    "message": f"Time to take your {medication['name']}"
                }
        
        return {
            "status": "reminder_sent",
            "user_id": user_id,
            "message": "Time to take your medication"
        }
    
    async def _schedule_reminders(self, user_id: str, medication: Dict):
        """Schedule reminders for a medication"""
        for scheduled_time in medication.get("schedule", []):
            reminder_key = f"{user_id}:{medication['id']}:{scheduled_time}"
            self.reminders[reminder_key] = {
                "user_id": user_id,
                "medication_id": medication["id"],
                "medication_name": medication["name"],
                "scheduled_time": scheduled_time,
                "created_at": datetime.utcnow().isoformat()
            }
    
    async def _find_medication(self, user_id: str, name: str) -> Optional[Dict]:
        """Find medication by name"""
        name_lower = name.lower()
        
        if self.cosmos_service:
            try:
                medications = await self.cosmos_service.get_user_medications(user_id) or []
                for med in medications:
                    if name_lower in med["name"].lower():
                        return med
            except Exception:
                pass
        
        if user_id in self.medications:
            for med in self.medications[user_id]:
                if name_lower in med["name"].lower():
                    return med
        
        return None
    
    def _extract_medication_name(self, message: str) -> Optional[str]:
        """Extract medication name from message"""
        words = message.split()
        
        for i, word in enumerate(words):
            if word.lower() in ["took", "take", "missed", "forgot"] and i + 1 < len(words):
                return words[i + 1].strip('.,!?')
        
        common_meds = ["aspirin", "ibuprofen", "tylenol", "lisinopril", "metformin",
                       "atorvastatin", "amlodipine", "omeprazole", "levothyroxine"]
        
        for word in words:
            clean_word = word.strip('.,!?').lower()
            if clean_word in common_meds:
                return clean_word
        
        return None
    
    def _time_to_minutes(self, time_str: str) -> int:
        """Convert time string to minutes since midnight"""
        try:
            if ":" in time_str:
                hours, minutes = map(int, time_str.split(":"))
                return hours * 60 + minutes
        except Exception:
            pass
        return 0