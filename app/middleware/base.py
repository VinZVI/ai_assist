"""
@file: middleware/base.py
@description: Базовый класс для middleware компонентов
@dependencies: aiogram, loguru
@created: 2025-10-09
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram.types import TelegramObject
from loguru import logger


class BaseAIMiddleware:
    """Базовый класс для всех middleware компонентов."""

    def __init__(self) -> None:
        """Инициализация базового middleware."""
        logger.debug(f"Initializing {self.__class__.__name__}")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Базовый метод обработки события.

        Args:
            handler: Следующий обработчик в цепочке
            event: Событие Telegram
            data: Данные контекста обработки

        Returns:
            Результат выполнения следующего обработчика
        """
        return await handler(event, data)
