#!/usr/bin/env python3
"""
Debug script to test handle_text_message function
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram import Bot
from aiogram.types import Chat, Message
from aiogram.types import User as TelegramUser

from app.models.user import User


async def test_handle_text_message_success() -> None:
    """Test the handle_text_message function success case"""
    # Create a mock message exactly like in the test
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=TelegramUser)
    message.from_user.id = 123456
    message.from_user.username = "testuser"
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 789012
    message.text = "Hello, AI!"
    message.answer = AsyncMock()
    message.bot = MagicMock(spec=Bot)
    message.bot.send_chat_action = AsyncMock()

    # Create a mock user
    mock_user = User(
        id=1,
        telegram_id=123456,
        username="testuser",
        first_name="Test",
        last_name="User",
        daily_message_count=5,
        is_premium=False,
    )

    with patch("app.handlers.message.get_or_update_user") as mock_get_user:
        mock_get_user.return_value = mock_user

        with patch(
            "app.handlers.message.generate_ai_response"
        ) as mock_generate_response:
            mock_generate_response.return_value = ("AI response", 10, "test-model", 0.5)

            with patch("app.handlers.message.save_conversation") as mock_save_conv:
                mock_save_conv.return_value = True

                # Mock session context manager
                mock_session_ctx = MagicMock()
                mock_session = AsyncMock()
                mock_session_ctx.__aenter__.return_value = mock_session

                with patch(
                    "app.handlers.message.get_session", return_value=mock_session_ctx
                ):
                    # Import the function inside the patch context
                    from app.handlers.message import handle_text_message

                    # Act
                    await handle_text_message(message)

                    # Check how many times message.answer was called
                    print(f"message.answer called {message.answer.call_count} times")
                    for i, call in enumerate(message.answer.call_args_list):
                        print(f"Call {i + 1}: {call}")


if __name__ == "__main__":
    asyncio.run(test_handle_text_message_success())
