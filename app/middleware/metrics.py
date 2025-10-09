"""
@file: middleware/metrics.py
@description: Middleware для сбора метрик использования
@dependencies: aiogram, loguru
@created: 2025-10-09
"""

from collections import defaultdict
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar

from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram.types import User as TelegramUser
from loguru import logger

from app.lexicon.gettext import get_log_text
from app.middleware.base import BaseAIMiddleware


class MetricsMiddleware(BaseAIMiddleware):
    """Middleware для сбора метрик использования."""

    # Метрики использования
    _metrics: ClassVar[dict[str, Any]] = {
        "total_requests": 0,
        "message_requests": 0,
        "callback_requests": 0,
        "other_requests": 0,
        "user_requests": defaultdict(int),
        "request_timestamps": [],
    }

    def __init__(self) -> None:
        """Инициализация MetricsMiddleware."""
        super().__init__()
        logger.info(get_log_text("middleware.metrics_middleware_initialized"))

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Обработка события с сбором метрик.

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

        # Обновляем метрики
        timestamp = datetime.now(UTC)
        self._metrics["total_requests"] += 1
        self._metrics["request_timestamps"].append(timestamp)

        # Удаляем старые временные метки (старше 1 часа)
        cutoff_time = timestamp - timedelta(hours=1)
        self._metrics["request_timestamps"] = [
            ts for ts in self._metrics["request_timestamps"] if ts > cutoff_time
        ]

        # Обновляем метрики по типам запросов
        if isinstance(event, Message):
            self._metrics["message_requests"] += 1
        elif isinstance(event, CallbackQuery):
            self._metrics["callback_requests"] += 1
        else:
            self._metrics["other_requests"] += 1

        # Обновляем метрики по пользователям
        if telegram_user:
            user_id = telegram_user.id
            self._metrics["user_requests"][user_id] += 1

        # Логируем сбор метрик
        logger.debug(
            get_log_text("middleware.metrics_collected").format(
                total_requests=self._metrics["total_requests"],
                message_requests=self._metrics["message_requests"],
                callback_requests=self._metrics["callback_requests"],
            )
        )

        # Передаем управление следующему обработчику
        return await handler(event, data)

    @classmethod
    def get_usage_metrics(cls) -> dict[str, Any]:
        """
        Получение метрик использования.

        Returns:
            Словарь с метриками использования
        """
        # Вычисляем дополнительные метрики
        total_requests = cls._metrics["total_requests"]
        request_timestamps = cls._metrics["request_timestamps"]

        # Вычисляем запросы в минуту (за последнюю минуту)
        if request_timestamps:
            cutoff_time = datetime.now(UTC) - timedelta(minutes=1)
            requests_last_minute = len(
                [ts for ts in request_timestamps if ts > cutoff_time]
            )
        else:
            requests_last_minute = 0

        return {
            "total_requests": total_requests,
            "message_requests": cls._metrics["message_requests"],
            "callback_requests": cls._metrics["callback_requests"],
            "other_requests": cls._metrics["other_requests"],
            "unique_users": len(cls._metrics["user_requests"]),
            "requests_per_user": dict(cls._metrics["user_requests"]),
            "requests_last_minute": requests_last_minute,
        }

    @classmethod
    def reset_metrics(cls) -> None:
        """Сброс метрик использования."""
        cls._metrics = {
            "total_requests": 0,
            "message_requests": 0,
            "callback_requests": 0,
            "other_requests": 0,
            "user_requests": defaultdict(int),
            "request_timestamps": [],
        }
