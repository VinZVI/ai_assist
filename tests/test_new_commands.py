"""
Test for new command handlers (/help, /profile, /limits, /premium)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import Message, User

from app.handlers.help import help_router
from app.handlers.limits import limits_router
from app.handlers.premium import premium_router
from app.handlers.profile import profile_router


@pytest.mark.asyncio
async def test_help_command() -> None:
    """Test the /help command handler"""
    # Create a mock message
    message = MagicMock(spec=Message)
    message.from_user = User(
        id=12345, is_bot=False, first_name="Test", username="testuser"
    )
    message.answer = AsyncMock()

    # Get the handler
    handlers = help_router.message.handlers
    help_handler = None
    for handler in handlers:
        if handler.callback.__name__ == "handle_help_command":
            help_handler = handler.callback
            break

    assert help_handler is not None, "Help command handler not found"

    # Test the handler
    await help_handler(message)
    message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_profile_command() -> None:
    """Test the /profile command handler"""
    # Create a mock message
    message = MagicMock(spec=Message)
    message.from_user = User(
        id=12345, is_bot=False, first_name="Test", username="testuser"
    )
    message.answer = AsyncMock()

    # Get the handler
    handlers = profile_router.message.handlers
    profile_handler = None
    for handler in handlers:
        if handler.callback.__name__ == "handle_profile_command":
            profile_handler = handler.callback
            break

    assert profile_handler is not None, "Profile command handler not found"

    # Test the handler
    await profile_handler(message)
    message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_limits_command() -> None:
    """Test the /limits command handler"""
    # Create a mock message
    message = MagicMock(spec=Message)
    message.from_user = User(
        id=12345, is_bot=False, first_name="Test", username="testuser"
    )
    message.answer = AsyncMock()

    # Get the handler
    handlers = limits_router.message.handlers
    limits_handler = None
    for handler in handlers:
        if handler.callback.__name__ == "handle_limits_command":
            limits_handler = handler.callback
            break

    assert limits_handler is not None, "Limits command handler not found"

    # Test the handler
    await limits_handler(message)
    message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_premium_command() -> None:
    """Test the /premium command handler"""
    # Create a mock message
    message = MagicMock(spec=Message)
    message.from_user = User(
        id=12345, is_bot=False, first_name="Test", username="testuser"
    )
    message.answer = AsyncMock()

    # Get the handler
    handlers = premium_router.message.handlers
    premium_handler = None
    for handler in handlers:
        if handler.callback.__name__ == "handle_premium_command":
            premium_handler = handler.callback
            break

    assert premium_handler is not None, "Premium command handler not found"

    # Test the handler
    await premium_handler(message)
    message.answer.assert_called_once()
