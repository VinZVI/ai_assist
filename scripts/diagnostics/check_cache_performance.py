#!/usr/bin/env python3
"""
Diagnostic script to check cache performance and identify caching issues.
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


async def diagnose_cache_performance() -> None:
    """Diagnose cache performance issues."""
    logger.info("Starting cache performance diagnosis...")

    # Initialize database
    await init_db()

    # Initialize cache service
    await cache_service.initialize_redis_cache()

    # Check cache stats
    cache_stats = cache_service.get_cache_stats()
    logger.info(f"Cache stats: {cache_stats}")

    # Test user caching
    logger.info("Testing user caching...")

    # Simulate multiple user requests
    test_user_ids = [1, 2, 3, 4, 5]

    for user_id in test_user_ids:
        # Try to get user from cache
        user = await cache_service.get_user(user_id)
        if user:
            logger.info(f"User {user_id} found in cache")
        else:
            logger.info(f"User {user_id} not in cache")

    # Check cache stats again
    cache_stats = cache_service.get_cache_stats()
    logger.info(f"Cache stats after testing: {cache_stats}")

    logger.info("Cache performance diagnosis completed.")


if __name__ == "__main__":
    asyncio.run(diagnose_cache_performance())
