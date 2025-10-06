"""
Test for command handlers
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message, User
from app.models.assistant_personality import AssistantPersonality
from sqlalchemy import select

from app.handlers.start import (
    help_command,
    limits_command,
    list_personalities_command,
    premium_command,
    profile_command,
    select_personality_command,
)
from app.models.user import User as UserModel


@pytest.mark.asyncio
async def test_help_command():
    """Test the /help command handler"""
    # Create a mock message
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.answer = AsyncMock()

    # Test the help command
    await help_command(message)

    # Verify that the help message was sent
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    assert "Справка по командам бота" in args[0]
    assert kwargs["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_profile_command():
    """Test the /profile command handler"""
    # Create a mock message
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.from_user.username = "testuser"
    message.answer = AsyncMock()

    # Mock the database session and user
    user = MagicMock(spec=UserModel)
    user.telegram_id = 12345
    user.first_name = "Test"
    user.last_name = "User"
    user.username = "testuser"
    user.personality_id = None

    with patch('app.handlers.start.get_session') as mock_session:
        mock_session.return_value.__aenter__.return_value.execute.return_value.scalar_one_or_none.return_value = user

        # Test the profile command
        await profile_command(message)

        # Verify that the profile message was sent
        message.answer.assert_called_once()
        args, kwargs = message.answer.call_args
        assert "Ваш профиль" in args[0]
        assert kwargs["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_limits_command():
    """Test the /limits command handler"""
    # Create a mock message
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.answer = AsyncMock()

    # Mock the database session and user
    user = MagicMock(spec=UserModel)
    user.telegram_id = 12345
    user.is_premium_active.return_value = False
    user.daily_message_count = 5

    with patch('app.handlers.start.get_session') as mock_session:
        mock_session.return_value.__aenter__.return_value.execute.return_value.scalar_one_or_none.return_value = user

        with patch('app.handlers.start.get_config') as mock_config:
            mock_config.return_value.user_limits.free_messages_limit = 10

            # Test the limits command
            await limits_command(message)

            # Verify that the limits message was sent
            message.answer.assert_called_once()
            args, kwargs = message.answer.call_args
            assert "Ваши лимиты" in args[0]
            assert kwargs["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_premium_command():
    """Test the /premium command handler"""
    # Create a mock message
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.answer = AsyncMock()

    # Mock the database session and user
    user = MagicMock(spec=UserModel)
    user.telegram_id = 12345
    user.is_premium_active.return_value = False

    with patch('app.handlers.start.get_session') as mock_session:
        mock_session.return_value.__aenter__.return_value.execute.return_value.scalar_one_or_none.return_value = user

        with patch('app.handlers.start.get_config') as mock_config:
            mock_config.return_value.user_limits.premium_price = 99
            mock_config.return_value.user_limits.premium_duration_days = 30

            # Test the premium command
            await premium_command(message)

            # Verify that the premium message was sent
            message.answer.assert_called_once()
            args, kwargs = message.answer.call_args
            assert "Премиум доступ" in args[0]
            assert kwargs["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_list_personalities_command():
    """Test the /personalities command handler"""
    # Create a mock message
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.answer = AsyncMock()

    # Mock the database session and personalities
    personality = MagicMock(spec=AssistantPersonality)
    personality.id = 1
    personality.name = "Test Personality"
    personality.description = "A test personality for testing purposes"
    personality.is_adult = False
    personality.is_active = True

    with patch('app.handlers.start.get_session') as mock_session:
        mock_session.return_value.__aenter__.return_value.execute.return_value.scalars.return_value.all.return_value = [personality]

        # Test the personalities command
        await list_personalities_command(message)

        # Verify that the personalities message was sent
        message.answer.assert_called_once()
        args, kwargs = message.answer.call_args
        assert "Доступные персональности ассистента" in args[0]
        assert kwargs["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_select_personality_command():
    """Test the /select_personality command handler"""
    # Create a mock message
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.text = "/select_personality 1"
    message.answer = AsyncMock()

    # Mock the database session and objects
    personality = MagicMock(spec=AssistantPersonality)
    personality.id = 1
    personality.name = "Test Personality"
    personality.is_adult = False
    personality.is_active = True

    user = MagicMock(spec=UserModel)
    user.telegram_id = 12345
    user.is_premium_active.return_value = False

    with patch('app.handlers.start.get_session') as mock_session:
        # Mock the personality query
        mock_session.return_value.__aenter__.return_value.execute.return_value.scalar_one_or_none.side_effect = [personality, user]

        # Test the select_personality command
        await select_personality_command(message)

        # Verify that the success message was sent
        message.answer.assert_called_once()
        args, kwargs = message.answer.call_args
        assert "Вы успешно выбрали персональность" in args[0]
        assert kwargs["parse_mode"] == "HTML"
