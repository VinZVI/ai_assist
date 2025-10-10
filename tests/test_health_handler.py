"""
Тесты для обычного обработчика healthcheck.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import Message

from app.handlers.health import health_router


@pytest.mark.asyncio
async def test_health_check() -> None:
    """Тест обычной команды /health."""
    # Создаем мок сообщения
    message = MagicMock(spec=Message)
    message.answer = AsyncMock()

    # Получаем обработчик
    handlers = health_router.message.handlers
    health_handler = None
    for handler in handlers:
        if handler.callback.__name__ == "health_check":
            health_handler = handler.callback
            break

    assert health_handler is not None, "Health check handler not found"

    # Тестируем обработчик
    await health_handler(message)

    # Проверяем, что ответ был отправлен
    message.answer.assert_called_once_with("✅ Приложение работает нормально")
