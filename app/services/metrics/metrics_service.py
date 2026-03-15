"""
Metrics Service for tracking application metrics and performance
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid

from app.core.logging import logger


class MetricsService:
    """
    Service for tracking application metrics
    Supports counters, timings, and custom metrics
    """
    
    def __init__(self, app_insights_key: Optional[str] = None, log_analytics_workspace: Optional[str] = None):
        self.app_insights_key = app_insights_key
        self.log_analytics_workspace = log_analytics_workspace
        self.is_healthy = False
        
        # In-memory metrics storage
        self.counters = {}
        self.timings = []
        self.gauges = {}
        self.events = []
        
        # Performance tracking
        self.request_count = 0
        self.error_count = 0
        self.start_time = datetime.utcnow()
        
    async def initialize(self):
        """Initialize the metrics service"""
        self.is_healthy = True
        logger.info("✅ Metrics Service initialized")
    
    async def increment(self, metric: str, tags: Optional[Dict] = None):
        """Increment a counter metric"""
        key = metric
        if tags:
            tag_str = ",".join(f"{k}={v}" for k, v in tags.items())
            key = f"{metric}[{tag_str}]"
        
        self.counters[key] = self.counters.get(key, 0) + 1
        self.request_count += 1
        
        logger.debug(f"📊 Metric increment: {key} = {self.counters[key]}")
    
    async def timing(self, metric: str, value_ms: float, tags: Optional[Dict] = None):
        """Record a timing metric in milliseconds"""
        self.timings.append({
            "metric": metric,
            "value_ms": value_ms,
            "tags": tags or {},
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last 1000 timings
        if len(self.timings) > 1000:
            self.timings = self.timings[-1000:]
        
        logger.debug(f"⏱️ Timing: {metric} = {value_ms:.2f}ms")
    
    async def gauge(self, metric: str, value: float, tags: Optional[Dict] = None):
        """Set a gauge metric"""
        key = metric
        if tags:
            tag_str = ",".join(f"{k}={v}" for k, v in tags.items())
            key = f"{metric}[{tag_str}]"
        
        self.gauges[key] = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.debug(f"📏 Gauge: {key} = {value}")
    
    async def record_event(self, event_type: str, properties: Optional[Dict] = None):
        """Record a custom event"""
        event = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "properties": properties or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.events.append(event)
        
        # Keep only last 500 events
        if len(self.events) > 500:
            self.events = self.events[-500:]
        
        logger.info(f"📝 Event: {event_type}")
    
    async def record_emergency(self, emergency_type: str, severity: str):
        """Record an emergency event"""
        await self.increment("emergencies", {"type": emergency_type, "severity": severity})
        await self.record_event("emergency", {"type": emergency_type, "severity": severity})
        logger.warning(f"🚨 Emergency recorded: {emergency_type} - {severity}")
    
    async def record_chat(self, user_id: str, intent: str, agent: str):
        """Record a chat interaction"""
        await self.increment("chats", {"intent": intent, "agent": agent})
    
    async def record_adherence(self, adherence_rate: float):
        """Record medication adherence rate"""
        await self.gauge("adherence_rate", adherence_rate)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        # Calculate average timing
        avg_timing = 0
        if self.timings:
            avg_timing = sum(t["value_ms"] for t in self.timings) / len(self.timings)
        
        # Calculate p95 timing
        p95_timing = 0
        if len(self.timings) > 20:
            sorted_timings = sorted(t["value_ms"] for t in self.timings)
            p95_index = int(len(sorted_timings) * 0.95)
            p95_timing = sorted_timings[p95_index]
        
        return {
            "counters": self.counters.copy(),
            "gauges": {k: v["value"] for k, v in self.gauges.items()},
            "timings": {
                "count": len(self.timings),
                "average_ms": round(avg_timing, 2),
                "p95_ms": round(p95_timing, 2),
                "recent": self.timings[-10:] if self.timings else []
            },
            "events": {
                "count": len(self.events),
                "recent": self.events[-10:] if self.events else []
            },
            "requests": {
                "total": self.request_count,
                "errors": self.error_count,
                "error_rate": round(self.error_count / max(self.request_count, 1) * 100, 2)
            },
            "uptime_seconds": round(uptime, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed statistics with time bucketing"""
        stats = self.get_stats()
        
        # Add time-based bucketing for last hour
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        
        # Filter recent timings
        recent_timings = [
            t for t in self.timings
            if datetime.fromisoformat(t["timestamp"]) > one_hour_ago
        ]
        
        # Group by minute
        timings_by_minute = {}
        for timing in recent_timings:
            minute_key = timing["timestamp"][:16]  # YYYY-MM-DDTHH:MM
            if minute_key not in timings_by_minute:
                timings_by_minute[minute_key] = []
            timings_by_minute[minute_key].append(timing["value_ms"])
        
        # Calculate averages per minute
        stats["timings_by_minute"] = {
            minute: round(sum(values) / len(values), 2)
            for minute, values in timings_by_minute.items()
        }
        
        return stats
    
    async def health_check(self) -> bool:
        """Check if service is healthy"""
        return self.is_healthy
    
    async def close(self):
        """Close the metrics service"""
        logger.info("MetricsService closed")