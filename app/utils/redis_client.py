"""
Redis client for caching and OTP storage
"""
import redis.asyncio as redis
from typing import Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client wrapper"""

    def __init__(self, url: str):
        self.url = url
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.from_url(
                self.url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
            )
            await self.client.ping()
            logger.info(f"Connected to Redis: {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        return await self.client.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None):
        """
        Set key-value pair

        Args:
            key: Redis key
            value: Value to store
            ex: Expiration time in seconds
        """
        if not self.client:
            raise RuntimeError("Redis client not connected")
        await self.client.set(key, value, ex=ex)

    async def delete(self, key: str):
        """Delete key"""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        return bool(await self.client.exists(key))

    async def incr(self, key: str) -> int:
        """Increment key value"""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        return await self.client.incr(key)

    async def expire(self, key: str, seconds: int):
        """Set expiration on key"""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        await self.client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """Get TTL of key"""
        if not self.client:
            raise RuntimeError("Redis client not connected")
        return await self.client.ttl(key)


# Global Redis clients
otp_redis_client = RedisClient(settings.redis_otp_url)
session_redis_client = RedisClient(settings.REDIS_URL)


async def get_otp_redis() -> RedisClient:
    """Dependency for OTP Redis client"""
    return otp_redis_client


async def get_session_redis() -> RedisClient:
    """Dependency for session Redis client"""
    return session_redis_client
