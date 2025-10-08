"""
Test for callback handlers to verify the fix for "message is not modified" error
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, Message, User

from app.handlers.callbacks import callback_router
from app.lexicon.gettext import get_text

# Get the main menu text using the new lexicon system
MAIN_MENU_TEXT = get_text("callbacks.main_menu_title")


@pytest.mark.asyncio
async def test_show_main_menu_success() -> None:
    """Test the show_main_menu function with successful edit"""
    # Create a mock callback query
    callback = MagicMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.message = MagicMock(spec=Message)
    callback.message.edit_text = AsyncMock()
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 123456

    # Mock message content to be different from new text to trigger edit
    callback.message.text = "Old text"
    callback.message.reply_markup = None

    # Get the show_main_menu handler from the router
    handlers = callback_router.callback_query.handlers
    show_main_menu_handler = handlers[0].callback  # First handler is show_main_menu

    # Mock the database session
    mock_session_ctx = MagicMock()
    mock_session = AsyncMock()
    mock_session_ctx.__aenter__.return_value = mock_session
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Test successful execution
    with patch("app.handlers.callbacks.get_session", return_value=mock_session_ctx):
        await show_main_menu_handler(callback)

    # Since we're mocking the message content to be different, it should try to edit
    assert callback.message.edit_text.call_count == 1
    # In successful case, answer is not called after edit_text


@pytest.mark.asyncio
async def test_show_main_menu_same_content() -> None:
    """Test the show_main_menu function when content is the same"""
    # Create a mock callback query
    callback = MagicMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.message = MagicMock(spec=Message)
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 123456

    # Mock message content to be the same as new text
    callback.message.text = MAIN_MENU_TEXT
    callback.message.reply_markup = None  # Different from actual keyboard

    # Get the show_main_menu handler from the router
    handlers = callback_router.callback_query.handlers
    show_main_menu_handler = handlers[0].callback  # First handler is show_main_menu

    # Mock the database session
    mock_session_ctx = MagicMock()
    mock_session = AsyncMock()
    mock_session_ctx.__aenter__.return_value = mock_session
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Test execution with same content
    with patch("app.handlers.callbacks.get_session", return_value=mock_session_ctx):
        await show_main_menu_handler(callback)

    # Since text is the same but keyboard is different, it should still try to edit
    assert callback.answer.call_count == 1


@pytest.mark.asyncio
async def test_show_main_menu_message_not_modified() -> None:
    """Test the show_main_menu function handling 'message is not modified' error"""
    # Create a mock callback query
    callback = MagicMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.message = MagicMock(spec=Message)
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 123456

    # Mock the edit_text to raise an exception with "message is not modified"
    callback.message.edit_text = AsyncMock(
        side_effect=Exception("message is not modified")
    )

    # Mock message content to be different from new text to trigger edit
    callback.message.text = "Old text"
    callback.message.reply_markup = None

    # Get the show_main_menu handler from the router
    handlers = callback_router.callback_query.handlers
    show_main_menu_handler = handlers[0].callback  # First handler is show_main_menu

    # Mock the database session
    mock_session_ctx = MagicMock()
    mock_session = AsyncMock()
    mock_session_ctx.__aenter__.return_value = mock_session
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Test handling of "message is not modified" error
    with patch("app.handlers.callbacks.get_session", return_value=mock_session_ctx):
        await show_main_menu_handler(callback)

    assert callback.answer.call_count == 1  # Should still call answer even with error
