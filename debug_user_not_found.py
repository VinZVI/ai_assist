#!/usr/bin/env python3
"""
Debug script to test user not found scenario
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import Message
from aiogram.types import User as TelegramUser

from app.models.user import User


async def test_user_not_found() -> None:
    """Test the user not found scenario"""
    # Create a mock message
    mock_message = MagicMock(spec=Message)
    mock_message.from_user = MagicMock(spec=TelegramUser)
    mock_message.from_user.id = 123456
    mock_message.from_user.username = "testuser"
    mock_message.from_user.first_name = "Test"
    mock_message.from_user.last_name = "User"
    mock_message.from_user.language_code = "en"

    # Mock the session context manager
    mock_session_ctx = MagicMock()
    mock_session = AsyncMock()
    mock_session_ctx.__aenter__.return_value = mock_session

    # Mock the query result - user not found
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Mock session.add and commit
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    with patch("app.models.user.get_session", return_value=mock_session_ctx):
        # Import inside the patch context
        from app.models.user import get_or_update_user

        result = await get_or_update_user(mock_message)
        print(f"Result: {result}")
        if result:
            print(f"User ID: {result.id}")
            print(f"Telegram ID: {result.telegram_id}")
            print(f"Username: {result.username}")


if __name__ == "__main__":
    asyncio.run(test_user_not_found())
