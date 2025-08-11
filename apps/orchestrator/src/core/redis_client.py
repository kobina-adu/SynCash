"""
Redis client for caching and message queuing
"""

import structlog
import redis.asyncio as redis
from typing import Optional

from src.config.settings import get_settings

logger = structlog.get_logger(__name__)

# Global Redis client
_redis_client: Optional[redis.Redis] = None

async def get_redis_client() -> redis.Redis:
    """Get Redis client instance"""
    global _redis_client
    
    if _redis_client is None:
        settings = get_settings()
        
        _redis_client = redis.from_url(
            settings.redis_url,
            password=settings.redis_password,
            decode_responses=True,
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={},
        )
        
        # Test connection
        try:
            await _redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error("Failed to connect to Redis", exc_info=e)
            raise
    
    return _redis_client

async def init_redis():
    """Initialize Redis connection"""
    await get_redis_client()

async def close_redis():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")
