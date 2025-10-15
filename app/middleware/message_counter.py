"""
@file: middleware/message_counter.py
@description: Middleware для подсчета сообщений пользователей
@dependencies: aiogram, loguru, app.models.user
@created: 2025-10-09
@updated: 2025-10-15
"""

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, ClassVar

from aiogram.types import Message, TelegramObject
from loguru import logger

from app.config import get_config
from app.database import get_session
from app.lexicon.gettext import get_log_text
from app.middleware.base import BaseAIMiddleware
from app.models.user import User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class MessageCountingMiddleware(BaseAIMiddleware):
    """Middleware для подсчета сообщений пользователей."""

    # Статистика по сообщениям
    _message_count_stats: ClassVar[dict[str, int]] = {
        "total_messages": 0,
        "free_user_messages": 0,
        "premium_user_messages": 0,
    }

    def __init__(self) -> None:
        """Инициализация MessageCountingMiddleware."""
        super().__init__()
        logger.debug("MessageCountingMiddleware инициализирован")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Подсчет сообщений пользователей.

        Args:
            handler: Следующий обработчик в цепочке
            event: Событие Telegram
            data: Данные контекста обработки

        Returns:
            Результат выполнения следующего обработчика
        """
        # Обрабатываем только текстовые сообщения
        if isinstance(event, Message) and event.text:
            user: User | None = data.get("user")
            if user:
                # Сбрасываем счетчик если прошел день
                user.reset_daily_count_if_needed()

                # Обновляем статистику
                self._message_count_stats["total_messages"] += 1
                if user.is_premium_active():
                    self._message_count_stats["premium_user_messages"] += 1
                else:
                    self._message_count_stats["free_user_messages"] += 1

        # Передаем управление следующему обработчику
        return await handler(event, data)

    @classmethod
    def get_message_count_stats(cls) -> dict[str, int]:
        """
        Получение статистики по сообщениям.

        Returns:
            Словарь со статистикой сообщений
        """
        return cls._message_count_stats.copy()

    @classmethod
    def reset_message_count_stats(cls) -> None:
        """Сброс статистики сообщений."""
        cls._message_count_stats = {
            "total_messages": 0,
            "free_user_messages": 0,
            "premium_user_messages": 0,
        }


# Экспорт для удобного использования
__all__ = [
    "MessageCountingMiddleware",
]
