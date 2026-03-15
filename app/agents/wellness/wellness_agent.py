"""
Wellness Agent
Monitors health metrics, activity, and overall wellness
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
import random

from app.core.logging import logger

class WellnessAgent:
    """Agent specialized in wellness monitoring"""
    
    def __init__(self, 
                 foundry_agent=None,
                 model_router=None,
                 db_service=None, 
                 cache_service=None,
                 notification_service=None):
        
        self.foundry_agent = foundry_agent
        self.model_router = model_router
        self.db_service = db_service
        self.cache_service = cache_service
        self.notification_service = notification_service
        self.wellness_data = {}
        self.daily_tips = self._load_daily_tips()
        
        logger.info("WellnessAgent initialized")
    
    async def initialize(self):
        """Initialize agent resources"""
        logger.info("WellnessAgent initialized")
    
    async def process(
        self,
        user_id: str,
        message: str,
        context: Any,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Process wellness-related requests"""
        
        message_lower = message.lower()
        
        # Mood tracking
        if any(word in message_lower for word in ["feeling", "mood", "how are you"]):
            return await self._track_mood(user_id, message, context)
        
        # Activity tracking
        if any(word in message_lower for word in ["walk", "exercise", "activity"]):
            return await self._track_activity(user_id, message, context)
        
        # Sleep tracking
        if any(word in message_lower for word in ["sleep", "slept", "bed"]):
            return await self._track_sleep(user_id, message, context)
        
        # Water intake
        if any(word in message_lower for word in ["water", "drank", "thirsty"]):
            return await self._track_water(user_id, message, context)
        
        # Wellness report
        if any(word in message_lower for word in ["wellness", "health", "report"]):
            return await self._get_wellness_report(user_id, context)
        
        # Tips
        if any(word in message_lower for word in ["tip", "advice", "suggest"]):
            return await self._get_wellness_tip(user_id, context)
        
        # Default response
        return {
            "message": "I can help you track your wellness. You can tell me about your mood, activities, sleep, or ask for wellness tips.",
            "data": {},
            "notify_family": False
        }
    
    async def _track_mood(self, user_id: str, message: str, context) -> Dict[str, Any]:
        """Track mood entry"""
        
        # Extract mood (simple)
        mood_map = {
            "great": 5, "good": 4, "okay": 3, "bad": 2, "terrible": 1,
            "happy": 5, "sad": 2, "tired": 3, "energetic": 5,
            "anxious": 2, "calm": 4, "stressed": 2, "depressed": 1,
            "excellent": 5, "poor": 2, "awful": 1, "wonderful": 5
        }
        
        mood_score = 3  # Default
        mood_label = "okay"
        
        message_lower = message.lower()
        for word, score in mood_map.items():
            if word in message_lower:
                mood_score = score
                mood_label = word
                break
        
        # Create mood entry
        mood_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "mood",
            "value": mood_score,
            "label": mood_label,
            "note": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save to database
        if self.db_service:
            try:
                await self.db_service.save_wellness_entry(mood_entry)
            except Exception as e:
                logger.error(f"Failed to save mood: {str(e)}")
        
        # Store in memory
        if user_id not in self.wellness_data:
            self.wellness_data[user_id] = []
        self.wellness_data[user_id].append(mood_entry)
        
        # Generate response based on mood
        if mood_score <= 2:
            response = f"I'm sorry to hear you're feeling {mood_label}. Is there anything I can do to help? Would you like me to suggest some activities or contact a family member?"
            notify_family = True
            notification_type = "low_mood"
            priority = "MEDIUM"
        elif mood_score == 3:
            response = f"Thanks for sharing. You're feeling {mood_label}. Remember, it's okay to have ups and downs. Would you like a wellness tip?"
            notify_family = False
            notification_type = None
            priority = "LOW"
        else:
            response = f"That's great that you're feeling {mood_label}! Keep up the positive energy! 😊"
            notify_family = False
            notification_type = None
            priority = "LOW"
        
        # Send notification if needed
        if notify_family and self.notification_service:
            await self.notification_service.send_notification(
                user_id=user_id,
                type="mood_alert",
                title="Mood Update",
                body=f"{user_id} is feeling {mood_label}.",
                data={"mood": mood_score, "label": mood_label},
                priority=priority
            )
        
        return {
            "message": response,
            "data": {"mood": mood_entry},
            "notify_family": notify_family,
            "notification_type": notification_type,
            "priority": priority
        }
    
    async def _track_activity(self, user_id: str, message: str, context) -> Dict[str, Any]:
        """Track activity entry"""
        
        # Try to extract steps or duration
        words = message.split()
        steps = None
        minutes = None
        activity_type = "walking"
        
        # Determine activity type
        if "run" in message.lower() or "jog" in message.lower():
            activity_type = "running"
        elif "walk" in message.lower():
            activity_type = "walking"
        elif "exercise" in message.lower():
            activity_type = "exercise"
        elif "bike" in message.lower() or "cycling" in message.lower():
            activity_type = "cycling"
        
        for i, word in enumerate(words):
            if word.isdigit():
                value = int(word)
                if i + 1 < len(words):
                    if words[i + 1].lower() in ["steps", "step"]:
                        steps = value
                    elif words[i + 1].lower() in ["minutes", "mins", "min"]:
                        minutes = value
                    elif words[i + 1].lower() in ["miles", "mile"]:
                        # Convert miles to steps (approx 2000 steps per mile)
                        steps = value * 2000
                    elif words[i + 1].lower() in ["km", "kilometers"]:
                        # Convert km to steps (approx 1300 steps per km)
                        steps = value * 1300
        
        # If no steps found but minutes found, estimate steps
        if not steps and minutes:
            if activity_type == "walking":
                steps = minutes * 100  # ~100 steps per minute walking
            elif activity_type == "running":
                steps = minutes * 150  # ~150 steps per minute running
        
        # Create activity entry
        activity_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "activity",
            "activity_type": activity_type,
            "steps": steps,
            "minutes": minutes,
            "note": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save to database
        if self.db_service:
            try:
                await self.db_service.save_wellness_entry(activity_entry)
            except Exception as e:
                logger.error(f"Failed to save activity: {str(e)}")
        
        # Store in memory
        if user_id not in self.wellness_data:
            self.wellness_data[user_id] = []
        self.wellness_data[user_id].append(activity_entry)
        
        response_parts = []
        if steps:
            response_parts.append(f"{steps:,} steps")
        if minutes:
            response_parts.append(f"{minutes} minutes")
        
        # Get today's total
        today_steps = await self._get_today_steps(user_id)
        
        if response_parts:
            response = f"Great job! I've recorded {' and '.join(response_parts)} of {activity_type}. "
            if today_steps:
                response += f"You've taken {today_steps:,} steps today. "
            if today_steps and today_steps > 5000:
                response += "You're exceeding your daily goal! 🎉"
            elif today_steps:
                response += f"Keep going! Your goal is 5,000 steps."
        else:
            response = f"Thanks for sharing your {activity_type} activity. Every bit of movement counts!"
        
        return {
            "message": response,
            "data": {"activity": activity_entry},
            "notify_family": False
        }
    
    async def _track_sleep(self, user_id: str, message: str, context) -> Dict[str, Any]:
        """Track sleep entry"""
        
        # Try to extract hours
        words = message.split()
        hours = None
        quality = None
        
        for i, word in enumerate(words):
            if word.isdigit():
                value = int(word)
                if i + 1 < len(words):
                    if words[i + 1].lower() in ["hours", "hrs", "hour"]:
                        hours = value
                else:
                    # Assume number is hours
                    hours = value
        
        # Check for quality indicators
        message_lower = message.lower()
        if "good" in message_lower or "well" in message_lower or "great" in message_lower:
            quality = "good"
        elif "bad" in message_lower or "poor" in message_lower or "terrible" in message_lower:
            quality = "poor"
        elif "ok" in message_lower:
            quality = "okay"
        
        # If no hours found, try to parse time range
        if not hours and "to" in message_lower:
            try:
                # Simple parsing for "slept from 10 to 6"
                parts = message_lower.split("to")
                if len(parts) == 2:
                    start = re.findall(r'\d+', parts[0])
                    end = re.findall(r'\d+', parts[1])
                    if start and end:
                        start_hour = int(start[-1])
                        end_hour = int(end[0])
                        if end_hour < start_hour:
                            end_hour += 12
                        hours = end_hour - start_hour
            except:
                pass
        
        # Create sleep entry
        sleep_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "sleep",
            "hours": hours,
            "quality": quality,
            "note": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save to database
        if self.db_service:
            try:
                await self.db_service.save_wellness_entry(sleep_entry)
            except Exception as e:
                logger.error(f"Failed to save sleep: {str(e)}")
        
        # Store in memory
        if user_id not in self.wellness_data:
            self.wellness_data[user_id] = []
        self.wellness_data[user_id].append(sleep_entry)
        
        # Generate response
        if hours:
            if hours < 7:
                response = f"You got {hours} hours of sleep. Try to aim for 7-8 hours for better health. Would you like tips for better sleep?"
                notify_family = False
            elif hours > 9:
                response = f"You got {hours} hours of sleep. That's quite a lot! Make sure you're staying active during the day."
                notify_family = False
            else:
                response = f"Great! {hours} hours is a healthy amount of sleep. You should feel well-rested!"
                notify_family = False
        else:
            response = "Thanks for sharing your sleep info. Quality rest is important for health! Try to aim for 7-8 hours."
            notify_family = False
        
        return {
            "message": response,
            "data": {"sleep": sleep_entry},
            "notify_family": notify_family
        }
    
    async def _track_water(self, user_id: str, message: str, context) -> Dict[str, Any]:
        """Track water intake"""
        
        # Try to extract glasses
        words = message.split()
        glasses = None
        
        for i, word in enumerate(words):
            if word.isdigit():
                value = int(word)
                if i + 1 < len(words):
                    if words[i + 1].lower() in ["glass", "glasses", "cup", "cups"]:
                        glasses = value
                else:
                    glasses = value
        
        if not glasses:
            glasses = 1  # Default to 1 glass
        
        # Create water entry
        water_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "water",
            "glasses": glasses,
            "note": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save to database
        if self.db_service:
            try:
                await self.db_service.save_wellness_entry(water_entry)
            except Exception as e:
                logger.error(f"Failed to save water: {str(e)}")
        
        # Store in memory
        if user_id not in self.wellness_data:
            self.wellness_data[user_id] = []
        self.wellness_data[user_id].append(water_entry)
        
        # Get today's total
        today_total = await self._get_today_water_total(user_id)
        
        response = f"Great! I've recorded {glasses} glass{'es' if glasses > 1 else ''} of water. "
        response += f"You've had {today_total} glass{'es' if today_total > 1 else ''} today. "
        
        if today_total >= 8:
            response += "Excellent! You've reached your daily goal of 8 glasses! 💧"
        else:
            remaining = 8 - today_total
            response += f"Try to drink {remaining} more glass{'es' if remaining > 1 else ''} to reach your daily goal."
        
        return {
            "message": response,
            "data": {"water": water_entry, "today_total": today_total},
            "notify_family": False
        }
    
    async def _get_wellness_report(self, user_id: str, context) -> Dict[str, Any]:
        """Generate wellness report"""
        
        # Get last 7 days of data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        entries = []
        if self.db_service:
            try:
                entries = await self.db_service.get_wellness_entries(
                    user_id, start_date, end_date
                )
            except Exception as e:
                logger.error(f"Failed to get wellness entries: {str(e)}")
        
        # If no entries, use memory cache
        if not entries and user_id in self.wellness_data:
            entries = [
                e for e in self.wellness_data[user_id]
                if start_date <= datetime.fromisoformat(e["timestamp"]) <= end_date
            ]
        
        # Calculate statistics
        mood_entries = [e for e in entries if e["type"] == "mood"]
        activity_entries = [e for e in entries if e["type"] == "activity"]
        sleep_entries = [e for e in entries if e["type"] == "sleep"]
        water_entries = [e for e in entries if e["type"] == "water"]
        
        avg_mood = sum(e["value"] for e in mood_entries) / len(mood_entries) if mood_entries else 0
        total_steps = sum(e.get("steps", 0) for e in activity_entries)
        total_activity_minutes = sum(e.get("minutes", 0) for e in activity_entries)
        avg_sleep = sum(e.get("hours", 0) for e in sleep_entries) / len(sleep_entries) if sleep_entries else 0
        total_water = sum(e.get("glasses", 0) for e in water_entries)
        
        # Generate insights
        insights = []
        
        if mood_entries:
            if avg_mood < 3:
                insights.append("📉 Your mood has been lower than usual lately. Consider talking to someone or doing activities you enjoy.")
            elif avg_mood > 4:
                insights.append("📈 Your mood has been great! Keep up whatever you're doing.")
        
        if activity_entries:
            if total_steps < 35000:  # 5000 steps per day average
                insights.append("🚶 Your activity level is lower than recommended. Try to increase your daily steps to 5,000.")
            elif total_steps > 70000:
                insights.append("🏃 You've been very active! Great job maintaining an active lifestyle.")
        
        if sleep_entries:
            if avg_sleep < 7:
                insights.append("😴 You're not getting enough sleep. Aim for 7-8 hours per night for better health.")
            elif avg_sleep > 9:
                insights.append("😴 You're sleeping quite a lot. Make sure you're staying active during the day.")
        
        if water_entries:
            if total_water < 56:  # 8 glasses per day
                insights.append("💧 Your water intake is low. Stay hydrated by drinking more water (aim for 8 glasses daily).")
        
        if not insights:
            insights.append("📊 Keep tracking your wellness to get personalized insights!")
        
        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": 7
            },
            "statistics": {
                "mood": {
                    "average": round(avg_mood, 1),
                    "entries": len(mood_entries)
                },
                "activity": {
                    "total_steps": total_steps,
                    "total_minutes": total_activity_minutes,
                    "entries": len(activity_entries),
                    "average_daily_steps": round(total_steps / 7) if total_steps > 0 else 0
                },
                "sleep": {
                    "average_hours": round(avg_sleep, 1),
                    "entries": len(sleep_entries)
                },
                "water": {
                    "total_glasses": total_water,
                    "entries": len(water_entries),
                    "average_daily": round(total_water / 7, 1) if total_water > 0 else 0
                }
            },
            "insights": insights
        }
        
        # Generate message
        if insights:
            message = "📊 Here's your wellness report for the past 7 days:\n\n" + "\n".join([f"• {i}" for i in insights])
        else:
            message = "📊 Your wellness looks good! Keep up the healthy habits. Track more activities to get detailed insights."
        
        return {
            "message": message,
            "data": {"report": report},
            "notify_family": False
        }
    
    async def _get_wellness_tip(self, user_id: str, context) -> Dict[str, Any]:
        """Get wellness tip"""
        
        # Try to get personalized tip from Foundry
        if self.foundry_agent:
            try:
                # Get user context for personalization
                user_info = ""
                if user_id in self.wellness_data and self.wellness_data[user_id]:
                    recent = self.wellness_data[user_id][-5:]
                    user_info = f"User's recent data: {json.dumps(recent)}"
                
                prompt = f"""Give a personalized wellness tip for an elderly person.
                {user_info}
                
                The tip should be:
                - Short and clear
                - Actionable
                - Positive and encouraging
                - Focus on one of: exercise, hydration, sleep, mental health, or nutrition
                
                Return just the tip, no additional text."""
                
                response = await self.foundry_agent.generate_chat(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=100
                )
                
                tip = response.get("content", "").strip()
                if tip:
                    return {
                        "message": f"💡 Wellness tip: {tip}",
                        "data": {"tip": tip},
                        "notify_family": False
                    }
            except Exception as e:
                logger.error(f"Failed to get personalized tip: {str(e)}")
        
        # Fallback to random tip
        tip = random.choice(self.daily_tips)
        
        return {
            "message": f"💡 Wellness tip: {tip}",
            "data": {"tip": tip},
            "notify_family": False
        }
    
    async def _get_today_water_total(self, user_id: str) -> int:
        """Get total water intake for today"""
        today = datetime.utcnow().date()
        
        total = 0
        if user_id in self.wellness_data:
            for entry in self.wellness_data[user_id]:
                if entry["type"] == "water":
                    try:
                        entry_date = datetime.fromisoformat(entry["timestamp"]).date()
                        if entry_date == today:
                            total += entry.get("glasses", 0)
                    except:
                        pass
        
        return total
    
    async def _get_today_steps(self, user_id: str) -> int:
        """Get total steps for today"""
        today = datetime.utcnow().date()
        
        total = 0
        if user_id in self.wellness_data:
            for entry in self.wellness_data[user_id]:
                if entry["type"] == "activity" and entry.get("steps"):
                    try:
                        entry_date = datetime.fromisoformat(entry["timestamp"]).date()
                        if entry_date == today:
                            total += entry.get("steps", 0)
                    except:
                        pass
        
        return total
    
    def _load_daily_tips(self) -> List[str]:
        """Load daily wellness tips"""
        return [
            "Drink a glass of water first thing in the morning.",
            "Take a short walk after meals to aid digestion.",
            "Try to get 7-8 hours of sleep each night.",
            "Take deep breaths when feeling stressed.",
            "Stay connected with friends and family.",
            "Eat a variety of colorful fruits and vegetables.",
            "Take breaks from screens every hour.",
            "Practice gratitude by noting three good things each day.",
            "Gentle stretching can help with flexibility and mood.",
            "Keep a regular schedule for meals and sleep.",
            "Social connection is important - call a friend today.",
            "Aim for 5,000 steps daily for heart health.",
            "Limit caffeine in the afternoon for better sleep.",
            "Sunlight exposure in the morning helps regulate sleep.",
            "Stay mentally active with puzzles or reading.",
            "Listen to your body and rest when needed.",
            "Stay hydrated - keep a water bottle nearby.",
            "Practice balance exercises to prevent falls.",
            "Eat protein with each meal to maintain muscle.",
            "Laughter is good medicine - watch something funny!"
        ]