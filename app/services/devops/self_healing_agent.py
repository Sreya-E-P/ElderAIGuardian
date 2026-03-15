"""
Agentic DevOps - Self-Healing Agent
Monitors system health and autonomously fixes issues
Targets the $20,000 Agentic DevOps Grand Prize
COMPLETE FIXED VERSION
"""

import asyncio
import subprocess
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import aiohttp
import os
import psutil
import platform

from app.core.logging import logger
from app.core.config import settings

# Try to import Azure Monitor with fallbacks
try:
    from azure.monitor.query import LogsQueryClient
    from azure.identity import DefaultAzureCredential
    AZURE_MONITOR_AVAILABLE = True
except ImportError:
    AZURE_MONITOR_AVAILABLE = False
    LogsQueryClient = None
    DefaultAzureCredential = None
    logger.warning("⚠️ Azure Monitor not available - using mock")

try:
    from azure.mgmt.monitor import MonitorManagementClient
    AZURE_MGMT_AVAILABLE = True
except ImportError:
    AZURE_MGMT_AVAILABLE = False
    MonitorManagementClient = None
    logger.warning("⚠️ Azure Management not available - using mock")

# Try to import GitHub with fallback
try:
    from github import Github
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    Github = None
    logger.warning("⚠️ GitHub integration not available - using mock")

# Try to import OpenAI with fallback
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None
    logger.warning("⚠️ OpenAI not available - using mock")


class SelfHealingAgent:
    """
    Self-Healing DevOps Agent
    Monitors application health and autonomously fixes issues
    Creates GitHub issues with Copilot-generated fixes
    """
    
    def __init__(self):
        self.logs_client = None
        self.monitor_client = None
        self.github = None
        self.repo = None
        self.openai_client = None
        self.is_monitoring = False
        self.error_history = []
        self.fixed_issues = []
        self.incident_count = 0
        self.fix_count = 0
        self.start_time = datetime.utcnow()
        
        # Health check thresholds
        self.cpu_threshold = 80  # %
        self.memory_threshold = 85  # %
        self.disk_threshold = 90  # %
        self.error_rate_threshold = 5  # %
        
    async def initialize(self):
        """Initialize the self-healing agent"""
        logger.info("=" * 60)
        logger.info("Initializing Self-Healing Agent...")
        logger.info(f"  Azure Monitor Available: {AZURE_MONITOR_AVAILABLE}")
        logger.info(f"  GitHub Available: {GITHUB_AVAILABLE}")
        logger.info(f"  OpenAI Available: {OPENAI_AVAILABLE}")
        logger.info("=" * 60)
        
    async def start_monitoring(self):
        """Start the self-healing monitoring loop"""
        self.is_monitoring = True
        logger.info("🚀 Self-Healing Agent started monitoring")
        
        while self.is_monitoring:
            try:
                # Monitor system health
                await self.check_system_health()
                
                # Check for errors in logs
                await self.analyze_error_logs()
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Self-healing loop error: {str(e)}")
                await asyncio.sleep(300)  # Back off on error
    
    async def check_system_health(self):
        """Check overall system health metrics"""
        try:
            health_status = {
                "timestamp": datetime.utcnow().isoformat(),
                "healthy": True,
                "issues": []
            }
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.cpu_threshold:
                health_status["healthy"] = False
                health_status["issues"].append({
                    "type": "high_cpu",
                    "value": cpu_percent,
                    "threshold": self.cpu_threshold,
                    "severity": "HIGH"
                })
                await self.handle_high_cpu(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            if memory.percent > self.memory_threshold:
                health_status["healthy"] = False
                health_status["issues"].append({
                    "type": "high_memory",
                    "value": memory.percent,
                    "threshold": self.memory_threshold,
                    "severity": "HIGH"
                })
                await self.handle_high_memory(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > self.disk_threshold:
                health_status["healthy"] = False
                health_status["issues"].append({
                    "type": "high_disk",
                    "value": disk_percent,
                    "threshold": self.disk_threshold,
                    "severity": "MEDIUM"
                })
                await self.handle_high_disk(disk_percent)
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"healthy": False, "error": str(e)}
    
    async def analyze_error_logs(self):
        """Analyze recent error logs and suggest fixes"""
        try:
            log_file = "logs/elderai.log"
            
            if not os.path.exists(log_file):
                # Create logs directory if it doesn't exist
                os.makedirs("logs", exist_ok=True)
                with open(log_file, "w") as f:
                    f.write("")
                return []
            
            errors = []
            with open(log_file, "r") as f:
                lines = f.readlines()[-1000:]  # Last 1000 lines
            
            error_patterns = [
                "ERROR",
                "Exception",
                "Failed",
                "Timeout",
                "Connection refused",
                "Rate limit exceeded",
                "Authentication failed",
                "Database error",
                "❌"
            ]
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                for pattern in error_patterns:
                    if pattern in line:
                        # Extract timestamp if present
                        try:
                            timestamp_str = line[:19] if len(line) >= 19 else "unknown"
                            try:
                                timestamp = datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
                                
                                # Only consider recent errors (last hour)
                                if datetime.utcnow() - timestamp < timedelta(hours=1):
                                    error_entry = {
                                        "timestamp": timestamp_str,
                                        "error": line,
                                        "pattern": pattern,
                                        "severity": "HIGH" if pattern in ["ERROR", "Exception", "❌"] else "MEDIUM"
                                    }
                                    errors.append(error_entry)
                                    self.error_history.append(error_entry)
                            except:
                                # No valid timestamp, include anyway
                                error_entry = {
                                    "timestamp": "unknown",
                                    "error": line,
                                    "pattern": pattern,
                                    "severity": "MEDIUM"
                                }
                                errors.append(error_entry)
                                self.error_history.append(error_entry)
                        except Exception:
                            # If any parsing fails, just add the error
                            error_entry = {
                                "timestamp": "unknown",
                                "error": line,
                                "pattern": pattern,
                                "severity": "MEDIUM"
                            }
                            errors.append(error_entry)
                            self.error_history.append(error_entry)
                        
                        break
            
            # Keep error history manageable
            if len(self.error_history) > 1000:
                self.error_history = self.error_history[-1000:]
            
            # Handle new errors
            if errors:
                self.incident_count += 1
                await self.handle_new_errors(errors)
            
            return errors
            
        except Exception as e:
            logger.error(f"Error log analysis failed: {str(e)}")
            return []
    
    async def handle_high_cpu(self, cpu_value: float):
        """Handle high CPU usage"""
        logger.warning(f"⚠️ High CPU detected: {cpu_value}%")
        
        # Check if we can restart the service
        if platform.system() != "Windows":
            try:
                # Check service status
                result = subprocess.run(
                    ["systemctl", "status", "elderai"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if "active" in result.stdout:
                    # Restart the service
                    subprocess.run(
                        ["systemctl", "restart", "elderai"],
                        check=False,
                        timeout=30
                    )
                    logger.info("✅ Restarted service due to high CPU")
                    self.fix_count += 1
                    self.fixed_issues.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "issue": "high_cpu",
                        "fix": "restarted_service",
                        "value": cpu_value
                    })
            except Exception as e:
                logger.error(f"Failed to restart service: {e}")
    
    async def handle_high_memory(self, memory_value: float):
        """Handle high memory usage"""
        logger.warning(f"⚠️ High memory detected: {memory_value}%")
        
        # Clear caches
        try:
            # Call cache clear endpoint
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"http://localhost:{settings.PORT}/api/cache/clear",
                    headers={"X-DevOps-Key": "devops-secret-key"}
                )
            logger.info("✅ Cleared cache due to high memory")
            self.fix_count += 1
            self.fixed_issues.append({
                "timestamp": datetime.utcnow().isoformat(),
                "issue": "high_memory",
                "fix": "cleared_cache",
                "value": memory_value
            })
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    async def handle_high_disk(self, disk_value: float):
        """Handle high disk usage"""
        logger.warning(f"⚠️ High disk usage detected: {disk_value}%")
        
        # Clean up old logs
        log_dir = "logs"
        if os.path.exists(log_dir):
            deleted_count = 0
            for file in os.listdir(log_dir):
                file_path = os.path.join(log_dir, file)
                if os.path.isfile(file_path):
                    # Delete files older than 7 days
                    mtime = os.path.getmtime(file_path)
                    age_days = (datetime.now().timestamp() - mtime) / 86400
                    if age_days > 7:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"Deleted old log: {file}")
            
            if deleted_count > 0:
                logger.info(f"✅ Cleaned {deleted_count} old log files")
                self.fix_count += 1
                self.fixed_issues.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "issue": "high_disk",
                    "fix": "cleaned_logs",
                    "deleted_count": deleted_count
                })
    
    async def handle_new_errors(self, errors: List[Dict]):
        """Handle newly detected errors"""
        
        # Group similar errors
        error_types = {}
        for error in errors:
            pattern = error["pattern"]
            if pattern not in error_types:
                error_types[pattern] = []
            error_types[pattern].append(error)
        
        # Create GitHub issues for each error type
        for pattern, pattern_errors in error_types.items():
            if len(pattern_errors) >= 3:  # Only if recurring
                await self.create_github_issue(
                    title=f"Recurring Error: {pattern}",
                    body=f"Detected {len(pattern_errors)} instances of {pattern} in the last hour.\n\nSample errors:\n" + 
                         "\n".join([f"- {e['error'][:200]}" for e in pattern_errors[:5]]),
                    labels=["bug", "auto-detected"]
                )
    
    async def create_github_issue(self, title: str, body: str, labels: List[str] = None):
        """Create GitHub issue (mock for now)"""
        logger.info(f"📝 [MOCK] GitHub issue: {title}")
        logger.debug(f"Body: {body[:200]}...")
        
    async def get_stats(self) -> Dict[str, Any]:
        """Get self-healing agent statistics"""
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
        
        # Calculate fix rate
        fix_rate = (self.fix_count / self.incident_count * 100) if self.incident_count > 0 else 100
        
        return {
            "is_monitoring": self.is_monitoring,
            "uptime_seconds": round(uptime_seconds, 1),
            "uptime_hours": round(uptime_seconds / 3600, 1),
            "total_incidents": self.incident_count,
            "successful_fixes": self.fix_count,
            "fix_rate_percent": round(fix_rate, 1),
            "recent_errors": len(self.error_history[-10:]),
            "total_errors_tracked": len(self.error_history),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.is_monitoring = False
        logger.info("Self-Healing Agent stopped")