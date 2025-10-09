"""
@file: middleware/logging.py
@description: Middleware для централизованного логирования запросов
@dependencies: aiogram, loguru
@created: 2025-10-09
"""

import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, ClassVar

from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram.types import User as TelegramUser
from loguru import logger

from app.lexicon.gettext import get_log_text
from app.middleware.base import BaseAIMiddleware


class LoggingMiddleware(BaseAIMiddleware):
    """Middleware для централизованного логирования запросов."""

    # Статистика по логированию
    _logging_stats: ClassVar[dict[str, int]] = {
        "messages_logged": 0,
        "callbacks_logged": 0,
        "other_events_logged": 0,
    }

    def __init__(self) -> None:
        """Инициализация LoggingMiddleware."""
        super().__init__()
        logger.info(get_log_text("middleware.logging_middleware_initialized"))

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Обработка события с логированием.

        Args:
            handler: Следующий обработчик в цепочке
            event: Событие Telegram
            data: Данные контекста обработки

        Returns:
            Результат выполнения следующего обработчика
        """
        # Получаем пользователя Telegram из события
        telegram_user: TelegramUser | None = None

        # Проверяем разные типы событий для получения пользователя
        if hasattr(event, "from_user") and event.from_user:
            telegram_user = event.from_user
        elif hasattr(event, "message") and event.message and event.message.from_user:
            telegram_user = event.message.from_user
        elif (
            hasattr(event, "callback_query")
            and event.callback_query
            and event.callback_query.from_user
        ):
            telegram_user = event.callback_query.from_user

        # Формируем информацию о событии для логирования
        log_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": type(event).__name__,
            "user_id": telegram_user.id if telegram_user else None,
            "username": telegram_user.username if telegram_user else None,
        }

        # Добавляем специфичную информацию для разных типов событий
        if isinstance(event, Message):
            log_data.update(
                {
                    "message_id": event.message_id,
                    "chat_id": event.chat.id,
                    "text_length": len(event.text) if event.text else 0,
                    "text_preview": event.text[:50] if event.text else None,
                }
            )
            self._logging_stats["messages_logged"] += 1
            log_message = get_log_text("middleware.message_received")
        elif isinstance(event, CallbackQuery):
            log_data.update(
                {
                    "callback_id": event.id,
                    "callback_data": event.data,
                    "message_id": event.message.message_id if event.message else None,
                }
            )
            self._logging_stats["callbacks_logged"] += 1
            log_message = get_log_text("middleware.callback_received")
        else:
            self._logging_stats["other_events_logged"] += 1
            log_message = get_log_text("middleware.other_event_received")

        # Логируем информацию о событии
        logger.info(log_message.format(**log_data))

        try:
            # Передаем управление следующему обработчику
            result = await handler(event, data)

            # Логируем успешную обработку
            logger.info(
                get_log_text("middleware.event_processed").format(
                    event_type=type(event).__name__,
                    user_id=telegram_user.id if telegram_user else None,
                )
            )

            return result

        except Exception as e:
            # Логируем ошибку обработки
            logger.error(
                get_log_text("middleware.event_processing_error").format(
                    event_type=type(event).__name__,
                    user_id=telegram_user.id if telegram_user else None,
                    error=str(e),
                )
            )
            raise

    @classmethod
    def get_logging_stats(cls) -> dict[str, int]:
        """
        Получение статистики логирования.

        Returns:
            Словарь со статистикой логирования
        """
        return cls._logging_stats.copy()

    @classmethod
    def reset_logging_stats(cls) -> None:
        """Сброс статистики логирования."""
        cls._logging_stats = {
            "messages_logged": 0,
            "callbacks_logged": 0,
            "other_events_logged": 0,
        }
