"""
Redis Cache Configuration
"""
import json
import redis.asyncio as redis
from typing import Any, Optional
from app.core.config import settings

class RedisClient:
    """Async Redis client wrapper with TTL support"""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self._client.ping()
            print("✅ Redis cache connected")
        except Exception as e:
            print(f"⚠️ Redis not available: {e}")
            self._client = None
    
    async def close(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._client:
            return None
        
        value = await self._client.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional TTL"""
        if not self._client:
            return False
        
        ttl = ttl or settings.CACHE_TTL
        await self._client.setex(
            key,
            ttl,
            json.dumps(value, default=str)
        )
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._client:
            return False
        
        await self._client.delete(key)
        return True
    
    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self._client:
            return 0
        
        keys = await self._client.keys(pattern)
        if keys:
            return await self._client.delete(*keys)
        return 0
    
    def cache_key(self, prefix: str, *args) -> str:
        """Generate cache key"""
        return f"{prefix}:{':'.join(str(arg) for arg in args)}"

redis_client = RedisClient()
