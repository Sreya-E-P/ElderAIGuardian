"""
Cache Service for Redis caching with in-memory fallback
"""

from typing import Optional, Any, List
import json
from datetime import datetime

from app.core.logging import logger

# Try to import redis with fallback
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    logger.warning("⚠️ Redis not available - using in-memory cache")


class CacheService:
    """Service for caching with Redis fallback to in-memory"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, password: Optional[str] = None, ssl: bool = False):
        self.host = host
        self.port = port
        self.password = password
        self.ssl = ssl
        self.redis_client = None
        self.is_healthy = False
        self._memory_cache = {}  # Simple in-memory fallback
        self.redis_available = REDIS_AVAILABLE
    
    async def initialize(self):
        """Initialize the cache service"""
        if self.redis_available:
            try:
                # Try to connect to Redis
                self.redis_client = await redis.from_url(
                    f"redis://{'ssl' if self.ssl else 'tcp'}://{self.host}:{self.port}",
                    password=self.password,
                    decode_responses=True
                )
                await self.redis_client.ping()
                self.is_healthy = True
                logger.info(f"✅ Redis cache initialized at {self.host}:{self.port}")
            except Exception as e:
                logger.warning(f"⚠️ Redis connection failed, using in-memory cache: {str(e)}")
                self.is_healthy = True
                self._memory_cache = {}
        else:
            logger.info("✅ Using in-memory cache (Redis not available)")
            self.is_healthy = True
            self._memory_cache = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        if self.redis_available and self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    try:
                        return json.loads(value)
                    except:
                        return value
            except Exception as e:
                logger.error(f"Redis get failed: {str(e)}")
        
        # Fallback to memory cache
        return self._memory_cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set a value in cache"""
        if self.redis_available and self.redis_client:
            try:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                if ttl:
                    await self.redis_client.setex(key, ttl, value)
                else:
                    await self.redis_client.set(key, value)
                return True
            except Exception as e:
                logger.error(f"Redis set failed: {str(e)}")
        
        # Fallback to memory cache
        self._memory_cache[key] = value
        return True
    
    async def delete(self, key: str):
        """Delete a key from cache"""
        if self.redis_available and self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete failed: {str(e)}")
        
        if key in self._memory_cache:
            del self._memory_cache[key]
    
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern"""
        if self.redis_available and self.redis_client:
            try:
                return await self.redis_client.keys(pattern)
            except Exception as e:
                logger.error(f"Redis keys failed: {str(e)}")
        
        # Fallback to memory cache
        return [k for k in self._memory_cache.keys() if pattern.replace("*", "") in k]
    
    async def close(self):
        """Close the cache service"""
        if self.redis_available and self.redis_client:
            await self.redis_client.close()
        self._memory_cache.clear()
        logger.info("CacheService closed")


# Dependency function to get cache service instance
async def get_cache_service() -> CacheService:
    """Get cache service instance (for FastAPI dependencies)"""
    from app.main import cache_service
    return cache_service


# Alias for backward compatibility
get_cache_service_instance = get_cache_service