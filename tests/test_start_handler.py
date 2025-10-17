"""
Тесты для обработчика команды /start
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message, User

from app.handlers.start import handle_start_command
from app.models.user import User as UserModel


@pytest.mark.asyncio
async def test_start_command_with_middleware_user() -> None:
    """Тест команды /start с пользователем из middleware."""
    # Создаем тестового пользователя Telegram
    telegram_user = User(
        id=123456789,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser",
        language_code="ru",
    )

    # Создаем тестовое сообщение с моком для answer
    message = MagicMock(spec=Message)
    message.from_user = telegram_user
    message.answer = AsyncMock()

    # Создаем тестового пользователя в БД
    db_user = UserModel(
        id=1,
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        last_name=telegram_user.last_name,
        language_code=telegram_user.language_code or "ru",
    )

    # Mock config
    mock_config = MagicMock()
    mock_config.user_limits.free_messages_limit = 10
    mock_config.user_limits.premium_price = 100
    mock_config.user_limits.premium_duration_days = 30

    # Mock the async context manager for session
    session_context = AsyncMock()
    session_context.__aenter__ = AsyncMock(return_value=session_context)
    session_context.__aexit__ = AsyncMock()

    with (
        patch("app.handlers.start.get_session") as mock_get_session,
        patch("app.handlers.start.get_config") as mock_get_config,
    ):
        mock_get_config.return_value = mock_config
        mock_get_session.return_value = session_context

        # Вызываем обработчик напрямую с пользователем из middleware
        await handle_start_command(message, db_user)

    # Проверяем, что бот отправил сообщение
    message.answer.assert_called()  # type: ignore[attr-defined]

    # Проверяем, что отправленное сообщение содержит ожидаемый текст
    call_args = message.answer.call_args
    assert call_args is not None

    # Проверяем, что текст содержит ожидаемые элементы
    sent_text = call_args[0][0]
    assert "🤖" in sent_text
    assert "Test User" in sent_text  # Имя пользователя в приветствии
