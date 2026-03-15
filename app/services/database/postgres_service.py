"""
PostgreSQL Database Service with AsyncPG
"""

import asyncpg
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json

from app.core.logging import logger
from app.core.config import settings

class PostgresService:
    """PostgreSQL database service using asyncpg"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
        self.is_healthy = False
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=settings.DB_POOL_SIZE,
                max_size=settings.DB_MAX_OVERFLOW,
                command_timeout=60,
                max_queries=50000,
                max_inactive_connection_lifetime=300
            )
            
            # Create tables if they don't exist
            await self._create_tables()
            
            self.is_healthy = True
            logger.info("PostgreSQL service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {str(e)}")
            raise
    
    async def _create_tables(self):
        """Create database tables"""
        async with self.pool.acquire() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(36) PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    phone VARCHAR(20),
                    date_of_birth VARCHAR(10),
                    gender VARCHAR(10),
                    address JSONB,
                    hashed_password VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_verified BOOLEAN DEFAULT FALSE,
                    role VARCHAR(20) DEFAULT 'user',
                    created_at VARCHAR(30) NOT NULL,
                    updated_at VARCHAR(30) NOT NULL,
                    last_login VARCHAR(30)
                )
            """)
            
            # User preferences table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id VARCHAR(36) PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    preferences JSONB NOT NULL,
                    updated_at VARCHAR(30) NOT NULL
                )
            """)
            
            # Chat sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(255),
                    context JSONB,
                    created_at VARCHAR(30) NOT NULL,
                    updated_at VARCHAR(30) NOT NULL,
                    metadata JSONB
                )
            """)
            
            # Chat messages table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id VARCHAR(36) PRIMARY KEY,
                    session_id VARCHAR(36) NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    intent VARCHAR(50),
                    confidence FLOAT,
                    agent VARCHAR(50),
                    data JSONB,
                    metadata JSONB,
                    timestamp VARCHAR(30) NOT NULL
                )
            """)
            
            # Medications table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS medications (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    dosage VARCHAR(100) NOT NULL,
                    form VARCHAR(50),
                    strength VARCHAR(50),
                    schedule JSONB NOT NULL,
                    start_date VARCHAR(10) NOT NULL,
                    end_date VARCHAR(10),
                    refill_date VARCHAR(10),
                    refill_reminder BOOLEAN DEFAULT TRUE,
                    quantity INTEGER,
                    instructions TEXT,
                    side_effects JSONB,
                    prescribed_by VARCHAR(255),
                    pharmacy JSONB,
                    active BOOLEAN DEFAULT TRUE,
                    created_at VARCHAR(30) NOT NULL,
                    updated_at VARCHAR(30)
                )
            """)
            
            # Medication reminders table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS medication_reminders (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    medication_id VARCHAR(36) NOT NULL REFERENCES medications(id) ON DELETE CASCADE,
                    medication_name VARCHAR(255) NOT NULL,
                    scheduled_time VARCHAR(10) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    taken_time VARCHAR(30),
                    notes TEXT,
                    created_at VARCHAR(30) NOT NULL
                )
            """)
            
            # Emergencies table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS emergencies (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    message TEXT,
                    location JSONB,
                    timestamp VARCHAR(30) NOT NULL,
                    resolved_at VARCHAR(30),
                    cancelled_at VARCHAR(30),
                    resolved_by VARCHAR(36),
                    cancelled_by VARCHAR(36),
                    contacts_notified JSONB,
                    services_notified BOOLEAN DEFAULT FALSE,
                    actions_taken JSONB,
                    resolution_note TEXT,
                    metadata JSONB
                )
            """)
            
            # Emergency contacts table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS emergency_contacts (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    relationship VARCHAR(100) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    email VARCHAR(255),
                    priority VARCHAR(20) NOT NULL,
                    notify_sms BOOLEAN DEFAULT TRUE,
                    notify_call BOOLEAN DEFAULT TRUE,
                    notify_whatsapp BOOLEAN DEFAULT FALSE,
                    created_at VARCHAR(30) NOT NULL,
                    updated_at VARCHAR(30)
                )
            """)
            
            # Wellness entries table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS wellness_entries (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    entry_type VARCHAR(50) NOT NULL,
                    data JSONB NOT NULL,
                    timestamp VARCHAR(30) NOT NULL
                )
            """)
            
            # Scam reports table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS scam_reports (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    message TEXT NOT NULL,
                    analysis_result JSONB NOT NULL,
                    user_action VARCHAR(50),
                    timestamp VARCHAR(30) NOT NULL,
                    metadata JSONB
                )
            """)
            
            # Notifications table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    type VARCHAR(50) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    body TEXT NOT NULL,
                    priority VARCHAR(20) NOT NULL,
                    data JSONB,
                    read BOOLEAN DEFAULT FALSE,
                    read_at VARCHAR(30),
                    action_url VARCHAR(500),
                    image_url VARCHAR(500),
                    created_at VARCHAR(30) NOT NULL,
                    expires_at VARCHAR(30)
                )
            """)
            
            # Notification preferences table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS notification_preferences (
                    user_id VARCHAR(36) PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    email_enabled BOOLEAN DEFAULT TRUE,
                    sms_enabled BOOLEAN DEFAULT TRUE,
                    push_enabled BOOLEAN DEFAULT TRUE,
                    whatsapp_enabled BOOLEAN DEFAULT FALSE,
                    quiet_hours_start INTEGER,
                    quiet_hours_end INTEGER,
                    emergency_always_notify BOOLEAN DEFAULT TRUE,
                    medication_reminders BOOLEAN DEFAULT TRUE,
                    scam_alerts BOOLEAN DEFAULT TRUE,
                    wellness_tips BOOLEAN DEFAULT TRUE,
                    daily_summary BOOLEAN DEFAULT TRUE,
                    weekly_report BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Analytics events table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36),
                    event_type VARCHAR(100) NOT NULL,
                    event_name VARCHAR(100) NOT NULL,
                    properties JSONB,
                    timestamp VARCHAR(30) NOT NULL,
                    session_id VARCHAR(36)
                )
            """)
            
            logger.info("Database tables created/verified")
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict]:
        """Fetch one row"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetch_all(self, query: str, *args) -> List[Dict]:
        """Fetch all rows"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def execute(self, query: str, *args) -> str:
        """Execute query"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def execute_many(self, query: str, args_list: List[tuple]):
        """Execute many queries"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany(query, args_list)
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection closed")

# Dependency
async def get_postgres_service() -> PostgresService:
    """Get postgres service instance"""
    from app.main import postgres_service
    return postgres_service