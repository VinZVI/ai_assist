#!/usr/bin/env python3
"""
Diagnostic script to test authentication flow and caching.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any
from unittest.mock import Mock

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from aiogram.types import Message, User
from loguru import logger

from app.database import init_db
from app.middleware.auth import AuthMiddleware
from app.services.cache_service import cache_service


async def test_auth_flow() -> None:
    """Test authentication flow and caching."""
    logger.info("Starting authentication flow test...")

    # Initialize database
    await init_db()

    # Initialize cache service
    await cache_service.initialize_redis_cache()

    # Create auth middleware
    auth_middleware = AuthMiddleware()

    # Wait for Redis initialization
    if (
        hasattr(auth_middleware, "_redis_init_task")
        and auth_middleware._redis_init_task
    ):
        await auth_middleware._redis_init_task

    # Create a mock message with a user
    mock_user = User(
        id=467055923,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="test_user",
        language_code="en",
    )

    mock_message = Mock(spec=Message)
    mock_message.from_user = mock_user

    # Test data
    data: dict[str, Any] = {}

    # Mock handler
    async def mock_handler(_event: Any, _data: dict[str, Any]) -> str:
        return "Handler executed"

    # First authentication - should create user and cache it
    logger.info("First authentication attempt...")
    result1 = await auth_middleware(mock_handler, mock_message, data)
    logger.info(f"First auth result: {result1}")

    # Check if user was added to data
    if "user" in data:
        user = data["user"]
        logger.info(f"User authenticated: {user.telegram_id} - {user.username}")
    else:
        logger.error("User not found in data after first authentication")

    # Check cache stats
    cache_stats = auth_middleware.get_cache_stats()
    logger.info(f"Cache stats after first auth: {cache_stats}")

    # Second authentication - should use cache
    logger.info("Second authentication attempt...")
    data = {}  # Reset data
    result2 = await auth_middleware(mock_handler, mock_message, data)
    logger.info(f"Second auth result: {result2}")

    # Check if user was added to data
    if "user" in data:
        user = data["user"]
        logger.info(
            f"User authenticated from cache: {user.telegram_id} - {user.username}"
        )
    else:
        logger.error("User not found in data after second authentication")

    # Check cache stats
    cache_stats = auth_middleware.get_cache_stats()
    logger.info(f"Cache stats after second auth: {cache_stats}")

    logger.info("Authentication flow test completed.")


if __name__ == "__main__":
    asyncio.run(test_auth_flow())
