"""
Тесты для AuthMiddleware
"""

from unittest.mock import AsyncMock, patch

import pytest
from aiogram import Dispatcher
from aiogram.types import Message, Update, User

from app.middleware.auth import AuthMiddleware
from app.models.user import User as UserModel


@pytest.mark.asyncio
async def test_auth_middleware_user_creation():
    """Тест создания пользователя через AuthMiddleware."""
    # Создаем моки
    bot = AsyncMock()
    dp = Dispatcher()

    # Регистрируем middleware
    auth_middleware = AuthMiddleware()
    dp.message.middleware(auth_middleware)

    # Создаем тестового пользователя Telegram
    telegram_user = User(
        id=987654321,
        is_bot=False,
        first_name="Middleware",
        last_name="Test",
        username="middleware_test",
        language_code="en",
    )

    # Создаем тестовое сообщение
    message = Message(
        message_id=2,
        from_user=telegram_user,
        chat={"id": 987654321, "type": "private"},
        date=1234567891,
        text="Test message",
    )

    # Создаем update
    update = Update(
        update_id=2,
        message=message,
    )

    # Мокаем функцию get_or_update_user для создания нового пользователя
    with patch("app.middleware.auth.get_or_update_user") as mock_get_user:
        # Создаем мок пользователя
        mock_user = UserModel(
            id=1,
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            language_code=telegram_user.language_code or "ru",
        )
        mock_get_user.return_value = mock_user

        # Флаг для проверки, что обработчик был вызван
        handler_called = False
        captured_user = None

        # Обработчик для проверки, что пользователь добавлен в контекст
        async def test_handler(message: Message, user: UserModel):
            nonlocal handler_called, captured_user
            handler_called = True
            captured_user = user

            assert user.telegram_id == telegram_user.id
            assert user.username == telegram_user.username
            assert user.first_name == telegram_user.first_name
            assert user.last_name == telegram_user.last_name
            assert user.language_code == telegram_user.language_code
            return True

        # Регистрируем тестовый обработчик
        dp.message.register(test_handler)

        # Вызываем обработчик через диспетчер
        result = await dp.feed_update(bot=bot, update=update)

        # Проверяем, что обработчик был вызван и вернул True
        assert handler_called is True
        assert result is True

        # Проверяем, что get_or_update_user была вызвана
        mock_get_user.assert_called_once()


@pytest.mark.asyncio
async def test_auth_middleware_user_retrieval():
    """Тест получения существующего пользователя через AuthMiddleware."""
    # Создаем моки
    bot = AsyncMock()
    dp = Dispatcher()

    # Регистрируем middleware
    auth_middleware = AuthMiddleware()
    dp.message.middleware(auth_middleware)

    # Создаем тестового пользователя Telegram
    telegram_user = User(
        id=111222333,
        is_bot=False,
        first_name="Existing",
        last_name="User",
        username="existing_user",
        language_code="ru",
    )

    # Создаем тестовое сообщение
    message = Message(
        message_id=3,
        from_user=telegram_user,
        chat={"id": 111222333, "type": "private"},
        date=1234567892,
        text="Another test message",
    )

    # Создаем существующего пользователя
    existing_user = UserModel(
        id=1,
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        last_name=telegram_user.last_name,
        language_code=telegram_user.language_code or "ru",
    )

    # Создаем update
    update = Update(
        update_id=3,
        message=message,
    )

    # Мокаем функцию get_or_update_user для получения существующего пользователя
    with patch("app.middleware.auth.get_or_update_user") as mock_get_user:
        mock_get_user.return_value = existing_user

        # Флаг для проверки, что обработчик был вызван
        handler_called = False
        captured_user = None

        # Обработчик для проверки, что пользователь добавлен в контекст
        async def test_handler(message: Message, user: UserModel):
            nonlocal handler_called, captured_user
            handler_called = True
            captured_user = user

            assert user.telegram_id == telegram_user.id
            assert user.username == telegram_user.username
            assert user.first_name == telegram_user.first_name
            assert user.last_name == telegram_user.last_name
            assert user.language_code == telegram_user.language_code
            return True

        # Регистрируем тестовый обработчик
        dp.message.register(test_handler)

        # Вызываем обработчик через диспетчер
        result = await dp.feed_update(bot=bot, update=update)

        # Проверяем, что обработчик был вызван и вернул True
        assert handler_called is True
        assert result is True

        # Проверяем, что get_or_update_user была вызвана
        mock_get_user.assert_called_once()
