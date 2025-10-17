"""
Test for language preference persistence when user sends /start command
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message, User

from app.handlers.language import language_router
from app.handlers.start import start_router
from app.models import User as UserModel


@pytest.mark.asyncio
async def test_start_command_preserves_language() -> None:
    """Test that /start command preserves user's language preference"""
    # Create a mock message
    message = MagicMock(spec=Message)
    message.from_user = User(
        id=12345,
        is_bot=False,
        first_name="Test",
        username="testuser",
        language_code="en",  # Telegram reports English
    )
    message.answer = AsyncMock()

    # Create a mock database user with Russian language preference
    db_user = UserModel(
        id=1,
        telegram_id=12345,
        username="testuser",
        first_name="Test",
        language_code="ru",  # But user previously selected Russian
    )

    # Mock database session for get_or_update_user
    with (
        patch("app.services.user_service.get_session") as mock_get_session,
        patch("app.config.get_config") as mock_get_config,
    ):
        # Mock config
        mock_config = MagicMock()
        mock_config.user_limits.free_messages_limit = 10
        mock_config.user_limits.premium_price = 100
        mock_config.user_limits.premium_duration_days = 30
        mock_get_config.return_value = mock_config

        # Mock the async context manager
        session_context = AsyncMock()
        session_context.__aenter__ = AsyncMock(return_value=session_context)
        session_context.__aexit__ = AsyncMock()

        # Mock the session methods
        mock_session = session_context.__aenter__.return_value
        mock_session.execute = AsyncMock()
        mock_session.execute.return_value.scalar_one_or_none = MagicMock(
            return_value=db_user
        )
        mock_session.commit = AsyncMock()

        mock_get_session.return_value = session_context

        # Get the handler
        handlers = start_router.message.handlers
        start_handler = None
        for handler in handlers:
            if handler.callback.__name__ == "handle_start_command":
                start_handler = handler.callback
                break

        assert start_handler is not None, "handle_start_command handler not found"

        # Test the handler with the user parameter (as provided by middleware)
        await start_handler(message, db_user)

        # Verify that the message was sent with Russian language content
        call_args = message.answer.call_args[0]
        # The welcome message should be in Russian since that's the user's preference
        assert "Добро пожаловать" in call_args[0] or "Welcome" not in call_args[0]
