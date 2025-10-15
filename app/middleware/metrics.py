"""
@file: middleware/metrics.py
@description: Middleware для сбора метрик
@dependencies: aiogram, loguru
@created: 2025-10-09
@updated: 2025-10-15
"""

from collections.abc import Awaitable, Callable
from typing import Any, ClassVar

from aiogram.types import TelegramObject
from loguru import logger

from app.middleware.base import BaseAIMiddleware


class MetricsMiddleware(BaseAIMiddleware):
    """Middleware для сбора метрик."""

    # Статистика по обработке сообщений
    _metrics_stats: ClassVar[dict[str, int]] = {
        "messages_processed": 0,
        "callbacks_processed": 0,
        "errors_occurred": 0,
        "processing_time_ms": 0,
    }

    def __init__(self) -> None:
        """Инициализация MetricsMiddleware."""
        super().__init__()
        logger.debug("MetricsMiddleware инициализирован")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Сбор метрик по обработке событий.

        Args:
            handler: Следующий обработчик в цепочке
            event: Событие Telegram
            data: Данные контекста обработки

        Returns:
            Результат выполнения следующего обработчика
        """
        import time

        start_time = time.time()

        try:
            # Передаем управление следующему обработчику
            result = await handler(event, data)

            # Обновляем статистику
            if hasattr(event, "text"):
                self._metrics_stats["messages_processed"] += 1
            elif hasattr(event, "data"):
                self._metrics_stats["callbacks_processed"] += 1

            return result

        except Exception as e:
            # Увеличиваем счетчик ошибок
            self._metrics_stats["errors_occurred"] += 1
            logger.error(f"Ошибка в MetricsMiddleware: {e}")
            raise

        finally:
            # Вычисляем время обработки
            processing_time = (time.time() - start_time) * 1000
            self._metrics_stats["processing_time_ms"] += int(processing_time)

    @classmethod
    def get_metrics_stats(cls) -> dict[str, int]:
        """
        Получение статистики метрик.

        Returns:
            Словарь со статистикой метрик
        """
        return cls._metrics_stats.copy()

    @classmethod
    def reset_metrics_stats(cls) -> None:
        """Сброс статистики метрик."""
        cls._metrics_stats = {
            "messages_processed": 0,
            "callbacks_processed": 0,
            "errors_occurred": 0,
            "processing_time_ms": 0,
        }


# Экспорт для удобного использования
__all__ = [
    "MetricsMiddleware",
]
