"""
Тесты для админского обработчика команд.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message, User

from app.handlers.admin import admin_router


@pytest.mark.asyncio
async def test_admin_health_check_authorized() -> None:
    """Тест админской команды /health для авторизованного пользователя."""
    # Создаем мок сообщения
    message = MagicMock(spec=Message)
    message.from_user = User(
        id=123456789, is_bot=False, first_name="Admin", username="adminuser"
    )
    message.answer = AsyncMock()

    # Мокаем конфигурацию и админские ID
    with (
        patch("app.handlers.admin.get_config") as mock_get_config,
        patch("app.handlers.admin.get_session") as mock_get_session,
        patch("app.handlers.admin.get_ai_manager") as mock_get_ai_manager,
    ):
        # Настраиваем мок конфигурации
        mock_telegram_config = MagicMock()
        mock_telegram_config.get_admin_ids.return_value = [123456789]

        mock_config = MagicMock()
        mock_config.telegram = mock_telegram_config
        mock_get_config.return_value = mock_config

        # Настраиваем мок сессии базы данных
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session_context)
        mock_session_context.__aexit__ = AsyncMock()
        mock_session_context.execute = AsyncMock()
        mock_get_session.return_value = mock_session_context

        # Настраиваем мок AI менеджера
        mock_ai_manager = AsyncMock()
        mock_ai_manager.health_check = AsyncMock(
            return_value={
                "manager_status": "healthy",
                "providers": {"openrouter": {"status": "healthy"}},
            }
        )
        mock_get_ai_manager.return_value = mock_ai_manager

        # Получаем обработчик
        handlers = admin_router.message.handlers
        admin_health_handler = None
        for handler in handlers:
            if handler.callback.__name__ == "admin_health_check":
                admin_health_handler = handler.callback
                break

        assert admin_health_handler is not None, "Admin health check handler not found"

        # Тестируем обработчик
        await admin_health_handler(message)

        # Проверяем, что ответ был отправлен
        message.answer.assert_called_once()
        # Проверяем, что ответ содержит информацию о здоровье системы
        call_args = message.answer.call_args[0]
        assert "Расширенный Health Check" in call_args[0]
        assert "healthy" in call_args[0]


@pytest.mark.asyncio
async def test_admin_health_check_unauthorized() -> None:
    """Тест админской команды /health для неавторизованного пользователя."""
    # Создаем мок сообщения
    message = MagicMock(spec=Message)
    message.from_user = User(
        id=987654321, is_bot=False, first_name="User", username="regularuser"
    )
    message.answer = AsyncMock()

    # Мокаем конфигурацию и админские ID
    with patch("app.handlers.admin.get_config") as mock_get_config:
        # Настраиваем мок конфигурации
        mock_telegram_config = MagicMock()
        mock_telegram_config.get_admin_ids.return_value = [
            123456789
        ]  # Другой ID админа

        mock_config = MagicMock()
        mock_config.telegram = mock_telegram_config
        mock_get_config.return_value = mock_config

        # Получаем обработчик
        handlers = admin_router.message.handlers
        admin_health_handler = None
        for handler in handlers:
            if handler.callback.__name__ == "admin_health_check":
                admin_health_handler = handler.callback
                break

        assert admin_health_handler is not None, "Admin health check handler not found"

        # Тестируем обработчик
        await admin_health_handler(message)

        # Проверяем, что ответ не был отправлен неавторизованному пользователю
        message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_admin_health_check_no_user() -> None:
    """Тест админской команды /health для сообщения без информации о пользователе."""
    # Создаем мок сообщения без пользователя
    message = MagicMock(spec=Message)
    message.from_user = None
    message.answer = AsyncMock()

    # Получаем обработчик
    handlers = admin_router.message.handlers
    admin_health_handler = None
    for handler in handlers:
        if handler.callback.__name__ == "admin_health_check":
            admin_health_handler = handler.callback
            break

    assert admin_health_handler is not None, "Admin health check handler not found"

    # Тестируем обработчик
    await admin_health_handler(message)

    # Проверяем, что ответ не был отправлен
    message.answer.assert_not_called()
