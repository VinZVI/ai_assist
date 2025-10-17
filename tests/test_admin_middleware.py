"""
Тесты для AdminMiddleware.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, Message, User

from app.config import AppConfig, TelegramConfig
from app.middleware.admin import AdminMiddleware


@pytest.fixture
def admin_middleware() -> AdminMiddleware:
    """Фикстура для создания экземпляра AdminMiddleware."""
    return AdminMiddleware()


@pytest.fixture
def mock_config() -> MagicMock:
    """Фикстура для мока конфигурации."""
    # Создаем мок для AdminConfig
    admin_config = MagicMock()
    admin_config.get_admin_ids.return_value = [123456789]

    # Создаем мок для AppConfig
    config = MagicMock(spec=AppConfig)
    config.admin = admin_config

    return config


@pytest.mark.asyncio
async def test_admin_middleware_message_admin(
    admin_middleware: AdminMiddleware, mock_config: MagicMock
) -> None:
    """Тест AdminMiddleware для сообщения от администратора."""
    # Мокаем конфигурацию
    with patch("app.middleware.admin.get_config", return_value=mock_config):
        # Создаем мок сообщения от администратора
        message = MagicMock(spec=Message)
        message.from_user = User(id=123456789, is_bot=False, first_name="Admin")

        # Создаем мок обработчика
        handler = AsyncMock()

        # Создаем данные контекста
        data = {}

        # Вызываем middleware
        await admin_middleware(handler, message, data)

        # Проверяем, что флаг is_admin установлен в True
        assert data["is_admin"] is True

        # Проверяем, что обработчик был вызван
        handler.assert_awaited_once_with(message, data)


@pytest.mark.asyncio
async def test_admin_middleware_message_non_admin(
    admin_middleware: AdminMiddleware, mock_config: MagicMock
) -> None:
    """Тест AdminMiddleware для сообщения от обычного пользователя."""
    # Мокаем конфигурацию
    with patch("app.middleware.admin.get_config", return_value=mock_config):
        # Создаем мок сообщения от обычного пользователя
        message = MagicMock(spec=Message)
        message.from_user = User(id=987654321, is_bot=False, first_name="User")

        # Создаем мок обработчика
        handler = AsyncMock()

        # Создаем данные контекста
        data = {}

        # Вызываем middleware
        await admin_middleware(handler, message, data)

        # Проверяем, что флаг is_admin установлен в False
        assert data["is_admin"] is False

        # Проверяем, что обработчик был вызван
        handler.assert_awaited_once_with(message, data)


@pytest.mark.asyncio
async def test_admin_middleware_callback_query_admin(
    admin_middleware: AdminMiddleware, mock_config: MagicMock
) -> None:
    """Тест AdminMiddleware для callback query от администратора."""
    # Мокаем конфигурацию
    with patch("app.middleware.admin.get_config", return_value=mock_config):
        # Создаем мок callback query от администратора
        callback_query = MagicMock(spec=CallbackQuery)
        callback_query.from_user = User(id=123456789, is_bot=False, first_name="Admin")

        # Создаем мок обработчика
        handler = AsyncMock()

        # Создаем данные контекста
        data = {}

        # Вызываем middleware
        await admin_middleware(handler, callback_query, data)

        # Проверяем, что флаг is_admin установлен в True
        assert data["is_admin"] is True

        # Проверяем, что обработчик был вызван
        handler.assert_awaited_once_with(callback_query, data)


@pytest.mark.asyncio
async def test_admin_middleware_callback_query_non_admin(
    admin_middleware: AdminMiddleware, mock_config: MagicMock
) -> None:
    """Тест AdminMiddleware для callback query от обычного пользователя."""
    # Мокаем конфигурацию
    with patch("app.middleware.admin.get_config", return_value=mock_config):
        # Создаем мок callback query от обычного пользователя
        callback_query = MagicMock(spec=CallbackQuery)
        callback_query.from_user = User(id=987654321, is_bot=False, first_name="User")

        # Создаем мок обработчика
        handler = AsyncMock()

        # Создаем данные контекста
        data = {}

        # Вызываем middleware
        await admin_middleware(handler, callback_query, data)

        # Проверяем, что флаг is_admin установлен в False
        assert data["is_admin"] is False

        # Проверяем, что обработчик был вызван
        handler.assert_awaited_once_with(callback_query, data)


@pytest.mark.asyncio
async def test_admin_middleware_no_user(
    admin_middleware: AdminMiddleware, mock_config: MagicMock
) -> None:
    """Тест AdminMiddleware для события без информации о пользователе."""
    # Мокаем конфигурацию
    with patch("app.middleware.admin.get_config", return_value=mock_config):
        # Создаем мок сообщения без пользователя
        message = MagicMock(spec=Message)
        message.from_user = None

        # Создаем мок обработчика
        handler = AsyncMock()

        # Создаем данные контекста
        data = {}

        # Вызываем middleware
        await admin_middleware(handler, message, data)

        # Проверяем, что флаг is_admin установлен в False
        assert data["is_admin"] is False

        # Проверяем, что обработчик был вызван
        handler.assert_awaited_once_with(message, data)
