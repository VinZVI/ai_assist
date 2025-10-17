#!/usr/bin/env python3
"""
Comprehensive diagnostic script to test cache functionality.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from app.database import init_db
from app.services.cache_service import cache_service
from app.services.redis_cache_service import REDIS_AVAILABLE, RedisCache


async def test_redis_connection() -> None:
    """Test Redis connection."""
    logger.info("Testing Redis connection...")

    if not REDIS_AVAILABLE:
        logger.warning("Redis is not available")
        return

    # Try to create a Redis cache instance
    redis_cache = RedisCache()
    logger.info(f"Redis cache created with URL: {redis_cache.redis_url}")

    # Try to initialize
    try:
        await redis_cache.initialize()
        if redis_cache.redis_client:
            logger.success("Redis connection successful")
            # Test basic operations
            await redis_cache.redis_client.set("test_key", "test_value")
            value = await redis_cache.redis_client.get("test_key")
            logger.info(f"Redis get/set test: {value}")
            await redis_cache.redis_client.delete("test_key")
        else:
            logger.error("Redis client is None after initialization")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")


async def comprehensive_cache_test() -> None:
    """Comprehensive cache test."""
    logger.info("Starting comprehensive cache test...")

    # Initialize database
    await init_db()

    # Test Redis connection
    await test_redis_connection()

    # Initialize cache service
    logger.info("Initializing cache service...")
    await cache_service.initialize_redis_cache()

    # Check cache stats
    cache_stats = cache_service.get_cache_stats()
    logger.info(f"Initial cache stats: {cache_stats}")

    # Test setting and getting a value
    logger.info("Testing cache set/get operations...")

    # Create a simple test user-like object
    class TestUser:
        def __init__(self, telegram_id: int, username: str) -> None:
            self.telegram_id = telegram_id
            self.username = username
            self.id = telegram_id
            self.first_name = "Test"
            self.last_name = "User"
            self.language_code = "en"
            self.is_premium = False
            self.is_active = True
            self.is_blocked = False
            self.daily_message_count = 0
            self.total_messages = 0
            self.last_message_date = None
            from datetime import datetime

            self.created_at = datetime.now()
            self.updated_at = datetime.now()
            self.last_activity_at = datetime.now()

    test_user = TestUser(467055923, "test_user")

    # Set user in cache
    logger.info("Setting user in cache...")
    await cache_service.set_user(test_user)

    # Check cache stats
    cache_stats = cache_service.get_cache_stats()
    logger.info(f"Cache stats after setting user: {cache_stats}")

    # Get user from cache
    logger.info("Getting user from cache...")
    cached_user = await cache_service.get_user(467055923)

    if cached_user:
        logger.success(
            f"User found in cache: {cached_user.telegram_id} - {cached_user.username}"
        )
    else:
        logger.error("User not found in cache")

    # Check cache stats again
    cache_stats = cache_service.get_cache_stats()
    logger.info(f"Cache stats after getting user: {cache_stats}")

    logger.info("Comprehensive cache test completed.")


if __name__ == "__main__":
    asyncio.run(comprehensive_cache_test())
