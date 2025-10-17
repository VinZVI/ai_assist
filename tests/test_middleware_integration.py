"""
Простой интеграционный тест для проверки работы middleware и обработчиков
"""

from unittest.mock import AsyncMock, patch

import pytest
from aiogram import Dispatcher
from aiogram.types import Message, User

from app.middleware.auth import AuthMiddleware
from app.models.user import User as UserModel
from app.services.user_service import get_or_update_user


@pytest.mark.asyncio
async def test_middleware_and_handler_integration() -> None:
    """Тест интеграции middleware и обработчиков."""
    # Создаем тестового пользователя Telegram
    telegram_user = User(
        id=123456789,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser",
        language_code="ru",
    )

    # Создаем тестовое сообщение
    message = Message(
        message_id=1,
        from_user=telegram_user,
        chat={"id": 123456789, "type": "private"},
        date=1234567890,
        text="Test message",
    )

    # Мокаем сессию базы данных
    with patch("app.services.user_service.get_session") as mock_get_session:
        # Создаем мок сессии
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Настраиваем контекстный менеджер
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Настраиваем возврат None (пользователь не найден, будет создан)
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        # Вызываем функцию get_or_update_user
        user = await get_or_update_user(message)

        # Проверяем, что пользователь был создан
        assert user is not None
        assert user.telegram_id == telegram_user.id
        assert user.username == telegram_user.username
        assert user.first_name == telegram_user.first_name
        assert user.language_code == (telegram_user.language_code or "ru")

        # Проверяем, что сессия была использована правильно
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()


def test_auth_middleware_initialization() -> None:
    """Тест инициализации AuthMiddleware."""
    # Создаем middleware
    middleware = AuthMiddleware()

    # Проверяем, что статистика инициализирована правильно
    stats = middleware.get_auth_stats()
    assert stats["users_authenticated"] == 0
    assert stats["users_created"] == 0
    assert stats["auth_errors"] == 0
