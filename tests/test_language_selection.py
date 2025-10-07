"""
Test for language selection functionality
"""

import pytest
from aiogram.types import CallbackQuery, Message, User
from unittest.mock import AsyncMock, MagicMock, patch

from app.handlers.language import language_router
from app.models import User as UserModel


@pytest.mark.asyncio
async def test_language_command_shows_keyboard() -> None:
    """Test that /language command shows the language selection keyboard"""
    # Create a mock message
    message = MagicMock(spec=Message)
    message.from_user = User(
        id=12345,
        is_bot=False,
        first_name="Test",
        username="testuser",
        language_code="en",
    )
    message.answer = AsyncMock()

    # Create a mock database user
    db_user = UserModel(
        id=1,
        telegram_id=12345,
        username="testuser",
        first_name="Test",
        language_code="ru",
    )

    # Mock database session
    with (
        patch("app.handlers.language.get_session") as mock_get_session,
    ):
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

        mock_get_session.return_value = session_context

        # Get the handler
        handlers = language_router.message.handlers
        lang_handler = None
        for handler in handlers:
            if handler.callback.__name__ == "handle_language_command":
                lang_handler = handler.callback
                break

        assert lang_handler is not None, "handle_language_command handler not found"

        # Test the handler
        await lang_handler(message)

        # Verify that the message was sent with the language keyboard
        call_args = message.answer.call_args
        assert call_args is not None
        
        # Check that the keyboard contains the correct callback data
        keyboard = call_args[1].get('reply_markup')
        assert keyboard is not None
        assert "select_language:ru" in str(keyboard)
        assert "select_language:en" in str(keyboard)


@pytest.mark.asyncio
async def test_language_selection_callback() -> None:
    """Test that language selection callback works correctly"""
    # Create a mock callback query
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "select_language:en"
    callback.from_user = User(
        id=12345,
        is_bot=False,
        first_name="Test",
        username="testuser",
        language_code="ru",
    )
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    # Create a mock database user
    db_user = UserModel(
        id=1,
        telegram_id=12345,
        username="testuser",
        first_name="Test",
        language_code="ru",  # Currently Russian
    )

    # Mock database session
    with patch("app.handlers.language.get_session") as mock_get_session:
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
        handlers = language_router.callback_query.handlers
        lang_handler = None
        for handler in handlers:
            if handler.callback.__name__ == "handle_language_selection":
                lang_handler = handler.callback
                break

        assert lang_handler is not None, "handle_language_selection handler not found"

        # Test the handler
        await lang_handler(callback)

        # Verify that the language was updated in the database
        # Check that session.execute was called with an update statement
        execute_calls = mock_session.execute.call_args_list
        assert len(execute_calls) == 2  # One for select, one for update
        
        # Verify that the message was updated with confirmation
        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()
        
        # Check that the confirmation message is in the selected language (English)
        edit_call_args = callback.message.edit_text.call_args
        assert "Language successfully changed" in edit_call_args[0][0]