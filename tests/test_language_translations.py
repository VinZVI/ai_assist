"""
Test for language translation functionality
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message, User

from app.handlers.message import handle_text_message, message_router
from app.handlers.start import handle_start_command, start_router
from app.keyboards.inline import create_main_menu_keyboard
from app.models import User as UserModel


@pytest.mark.asyncio
async def test_keyboard_translations() -> None:
    """Test that keyboards use the correct language based on user preference"""
    # Test Russian keyboard
    ru_keyboard = create_main_menu_keyboard("ru")
    assert "Начать диалог" in str(ru_keyboard)
    assert "Мой профиль" in str(ru_keyboard)

    # Test English keyboard
    en_keyboard = create_main_menu_keyboard("en")
    assert "Start Dialogue" in str(en_keyboard)
    assert "My Profile" in str(en_keyboard)


@pytest.mark.asyncio
async def test_start_command_uses_user_language() -> None:
    """Test that /start command uses user's language preference for keyboards"""
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

    # Mock database session for get_or_create_user
    with (
        patch("app.handlers.start.get_session") as mock_get_session,
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

        # Test the handler
        await start_handler(message)

        # Verify that the message was sent with Russian language content and keyboard
        call_args = message.answer.call_args
        assert call_args is not None

        # Check that the keyboard contains Russian text (user's preference)
        keyboard = call_args[1].get("reply_markup")
        assert keyboard is not None
        assert "Начать диалог" in str(keyboard)  # Russian text
        assert "Start Dialogue" not in str(keyboard)  # Not English text


@pytest.mark.asyncio
async def test_message_handler_uses_user_language() -> None:
    """Test that message handler uses user's language preference for error messages"""
    # Create a mock message
    message = MagicMock(spec=Message)
    message.from_user = User(
        id=12345,
        is_bot=False,
        first_name="Test",
        username="testuser",
        language_code="ru",  # Telegram reports Russian
    )
    message.answer = AsyncMock()
    message.text = "Test message"
    message.chat = MagicMock()
    message.chat.id = 12345

    # Create a mock database user with Russian language preference
    db_user = UserModel(
        id=1,
        telegram_id=12345,
        username="testuser",
        first_name="Test",
        language_code="ru",  # User prefers Russian
    )

    # Mock services to return user with Russian preference
    with patch("app.services.user_service.get_or_update_user") as mock_get_user:
        mock_get_user.return_value = db_user

        # Mock AI manager to raise an exception to test error messages
        with patch("app.handlers.message.generate_ai_response") as mock_generate:
            mock_generate.side_effect = Exception("Test error")

            # Get the handler
            handlers = message_router.message.handlers
            msg_handler = None
            for handler in handlers:
                if handler.callback.__name__ == "handle_text_message":
                    msg_handler = handler.callback
                    break

            assert msg_handler is not None, "handle_text_message handler not found"

            # Test the handler
            await msg_handler(message)

            # Verify that the error message was sent in Russian (user's preference)
            call_args = message.answer.call_args
            assert call_args is not None

            # Check that the error message is in Russian
            error_message = call_args[0][0]
            assert "Ошибка" in error_message or "ошибка" in error_message.lower()
