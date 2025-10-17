"""
Test for language selection functionality
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.handlers.language import language_router
from app.lexicon.gettext import get_text
from app.models import User


@pytest.mark.asyncio
async def test_handle_language_command_success() -> None:
    """Test the handle_language_command function with successful execution"""
    # Create a mock message
    message = MagicMock(spec=Message)
    message.from_user = MagicMock()
    message.from_user.id = 12345
    message.answer = AsyncMock()

    # Mock user data
    mock_user = User(
        id=1,
        telegram_id=12345,
        username="testuser",
        first_name="Test",
        last_name="User",
        language_code="ru",
    )

    # Mock database session
    with patch("app.handlers.language.get_session") as mock_get_session:
        # Create an async context manager mock
        session_context = AsyncMock()
        session_context.__aenter__ = AsyncMock(return_value=AsyncMock())
        session_context.__aexit__ = AsyncMock(return_value=None)

        # Mock the session methods
        mock_session = session_context.__aenter__.return_value
        mock_session.execute = AsyncMock()
        mock_session.execute.return_value.scalar_one_or_none = MagicMock(
            return_value=mock_user
        )

        mock_get_session.return_value = session_context

        # Get the handle_language_command handler from the router
        handlers = language_router.message.handlers
        language_command_handler = None
        for handler in handlers:
            if handler.callback.__name__ == "handle_language_command":
                language_command_handler = handler.callback
                break

        assert language_command_handler is not None, (
            "handle_language_command handler not found"
        )

        # Test successful execution
        await language_command_handler(message)

        # Check that answer was called with the correct text
        assert message.answer.call_count == 1
        # Check that the answer contains the language title
        call_args = message.answer.call_args[0]
        assert "🌐" in call_args[0]  # Should contain the globe emoji
        assert (
            "Выбор языка" in call_args[0] or "Language Selection" in call_args[0]
        )  # Should contain title


@pytest.mark.asyncio
async def test_handle_language_selection_success() -> None:
    """Test the handle_language_selection function with successful execution"""
    # Create a mock callback query
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "select_language:en"
    callback.from_user = MagicMock()
    callback.from_user.id = 12345
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()

    # Mock user data
    mock_user = User(
        id=1,
        telegram_id=12345,
        username="testuser",
        first_name="Test",
        last_name="User",
        language_code="ru",
    )

    # Mock database session
    with patch("app.handlers.language.get_session") as mock_get_session:
        # Create an async context manager mock
        session_context = AsyncMock()
        session_context.__aenter__ = AsyncMock(return_value=AsyncMock())
        session_context.__aexit__ = AsyncMock(return_value=None)

        # Mock the session methods
        mock_session = session_context.__aenter__.return_value
        mock_session.execute = AsyncMock()
        mock_session.execute.return_value.scalar_one_or_none = MagicMock(
            return_value=mock_user
        )
        mock_session.commit = AsyncMock()

        mock_get_session.return_value = session_context

        # Get the handle_language_selection handler from the router
        handlers = language_router.callback_query.handlers
        language_selection_handler = None
        for handler in handlers:
            if handler.callback.__name__ == "handle_language_selection":
                language_selection_handler = handler.callback
                break

        assert language_selection_handler is not None, (
            "handle_language_selection handler not found"
        )

        # Test successful execution
        await language_selection_handler(callback)

        # Check that edit_text was called with the correct text
        assert callback.message.edit_text.call_count == 1
        call_args = callback.message.edit_text.call_args[0]
        assert "✅" in call_args[0]  # Should contain the checkmark emoji
        assert "English" in call_args[0]  # Should contain the language name

        # Check that answer was called
        assert callback.answer.call_count == 1
