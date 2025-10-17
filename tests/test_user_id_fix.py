"""
Test for handling user_id attribute error in message handler
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Chat, Message, User

from app.handlers.message import handle_text_message
from app.lexicon.gettext import get_text
from app.models.user import User as UserModel


@pytest.mark.asyncio
async def test_handle_text_message_user_id_error() -> None:
    """Test handle_text_message with user_id attribute error"""
    # Create a mock message with a user
    message = MagicMock(spec=Message)
    message.text = "Test message"
    message.from_user = MagicMock(spec=User)
    message.from_user.username = "testuser"
    message.from_user.id = 12345
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 12345
    message.answer = AsyncMock()
    message.bot = MagicMock()
    message.bot.send_chat_action = AsyncMock()

    # Mock the get_or_update_user function to return a user
    user = MagicMock(spec=UserModel)
    user.id = 1
    user.can_send_message.return_value = True
    user.total_messages = 0
    user.daily_message_count = 0
    user.is_premium_active.return_value = False
    user.personality_id = None
    user.increment_message_count = MagicMock()

    # Mock the generate_ai_response to raise an exception with 'user_id' attribute
    class MockExceptionError(Exception):
        def __init__(self) -> None:
            super().__init__("Test error")
            # This would cause the 'user_id' attribute error
            self.user_id = property(lambda self: self._user_id)

    with patch("app.handlers.message.get_or_update_user", return_value=user):
        with patch(
            "app.handlers.message.generate_ai_response",
            side_effect=Exception("Test error with 'user_id' attribute"),
        ):
            # Test that the error is handled gracefully
            await handle_text_message(message)
            # Verify that the error is handled gracefully
            message.answer.assert_called_with(get_text("errors.general_error"))


@pytest.mark.asyncio
async def test_handle_text_message_with_none_from_user() -> None:
    """Test handle_text_message when message.from_user is None"""
    # Create a mock message without a user
    message = MagicMock(spec=Message)
    message.text = "Test message"
    message.from_user = None
    message.answer = AsyncMock()

    # Test handling when from_user is None
    await handle_text_message(message)

    # Verify that the error is handled gracefully
    message.answer.assert_called_with(get_text("errors.general_error"))
