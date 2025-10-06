"""
Test for message handler to verify the fix for 'user_id' error
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Chat, Message, User

from app.handlers.message import handle_text_message
from app.lexicon.message import PROCESSING_ERROR
from app.models.user import User as UserModel


@pytest.mark.asyncio
async def test_handle_text_message_with_user() -> None:
    """Test handle_text_message with a valid user"""
    # Create a mock message with a user
    message = MagicMock(spec=Message)
    message.text = "Hello, bot!"
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.from_user.username = "testuser"
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.from_user.language_code = "en"
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 12345
    message.answer = AsyncMock()
    message.bot = MagicMock()
    message.bot.send_chat_action = AsyncMock()

    # Mock the get_or_update_user function to return a user
    user = MagicMock(spec=UserModel)
    user.id = 12345
    user.can_send_message.return_value = True
    user.personality_id = None
    user.increment_message_count = MagicMock()

    with patch("app.handlers.message.get_or_update_user", return_value=user):
        with patch(
            "app.handlers.message.generate_ai_response",
            return_value=("Test response", 10, "test-model", 0.1),
        ):
            with patch("app.handlers.message.save_conversation", return_value=True):
                with patch("app.handlers.message.get_session") as mock_session:
                    mock_session.return_value.__aenter__.return_value = MagicMock()

                    # Test successful execution
                    await handle_text_message(message)

                    # Verify that the message was processed without errors
                    message.answer.assert_called_with(
                        "Test response", parse_mode="Markdown"
                    )


@pytest.mark.asyncio
async def test_handle_text_message_without_user() -> None:
    """Test handle_text_message when message.from_user is None"""
    # Create a mock message without a user
    message = MagicMock(spec=Message)
    message.text = "Hello, bot!"
    message.from_user = None
    message.answer = AsyncMock()

    # Test handling when from_user is None
    await handle_text_message(message)

    # Verify that the error is handled gracefully
    message.answer.assert_called_with(PROCESSING_ERROR)


@pytest.mark.asyncio
async def test_handle_text_message_exception_handling() -> None:
    """Test handle_text_message exception handling with proper user_id extraction"""
    # Create a mock message with a user
    message = MagicMock(spec=Message)
    message.text = "Hello, bot!"
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.answer = AsyncMock()

    # Mock get_or_update_user to raise an exception
    with patch(
        "app.handlers.message.get_or_update_user", side_effect=Exception("Test error")
    ):
        # Test exception handling
        await handle_text_message(message)

        # Verify that the error is handled gracefully
        message.answer.assert_called_with(PROCESSING_ERROR)
