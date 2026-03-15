"""
Metrics Collection Service
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json

from app.core.logging import logger

class MetricsCollector:
    """Simple metrics collector"""
    
    def __init__(self):
        self.metrics = {
            "requests": 0,
            "errors": 0,
            "emergencies": 0,
            "scams_detected": 0,
            "chats": 0,
            "medications_tracked": 0,
            "notifications_sent": 0
        }
        self.timings = []
    
    def increment(self, metric: str, tags: Dict = None):
        """Increment a metric"""
        if metric in self.metrics:
            self.metrics[metric] += 1
        logger.debug(f"Metric: {metric} = {self.metrics.get(metric, 0)}")
    
    def timing(self, metric: str, value: float):
        """Record a timing metric"""
        self.timings.append({
            "metric": metric,
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        })
        # Keep only last 1000 timings
        if len(self.timings) > 1000:
            self.timings = self.timings[-1000:]
    
    async def record_emergency(self, emergency_type: str, severity: str):
        """Record an emergency"""
        self.increment("emergencies")
        logger.info(f"Emergency recorded: {emergency_type} - {severity}")
    
    async def record_chat(self, user_id: str, intent: str, agent: str):
        """Record a chat interaction"""
        self.increment("chats")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        return {
            "counters": self.metrics.copy(),
            "timings_count": len(self.timings),
            "timestamp": datetime.utcnow().isoformat()
        }