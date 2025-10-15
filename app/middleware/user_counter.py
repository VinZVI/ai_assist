"""
@file: middleware/user_counter.py
@description: Middleware для подсчета сообщений пользователей
@dependencies: aiogram, loguru, app.models.user
@created: 2025-10-09
"""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, ClassVar

from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram.types import User as TelegramUser
from loguru import logger
from sqlalchemy import update

from app.config import get_config
from app.database import get_session
from app.lexicon.gettext import get_log_text
from app.middleware.base import BaseAIMiddleware
from app.models.user import User


class MessageCountingMiddleware(BaseAIMiddleware):
    """Middleware для подсчета сообщений пользователей."""

    # Статистика по счетчикам
    _counter_stats: ClassVar[dict[str, int]] = {
        "message_counts_updated": 0,
        "counter_errors": 0,
        "messages_counted": 0,
    }

    # Буфер для пакетных обновлений
    _batch_buffer: ClassVar[dict[int, datetime]] = {}
    _batch_timer: ClassVar[Any] = None
    _batch_interval: ClassVar[int] = 30  # Интервал пакетных обновлений в секундах

    def __init__(self) -> None:
        """Инициализация MessageCountingMiddleware."""
        super().__init__()
        logger.info(get_log_text("middleware.user_counter_middleware_initialized"))

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Обработка события с подсчетом сообщений пользователей.

        Args:
            handler: Следующий обработчик в цепочке
            event: Событие Telegram
            data: Данные контекста обработки

        Returns:
            Результат выполнения следующего обработчика
        """
        # Передаем управление следующему обработчику
        result = await handler(event, data)

        # После выполнения обработчика проверяем, нужно ли обновить счетчик
        # Только для текстовых сообщений (не команд и не callback'ов)
        if self._should_count_message(event):
            await self._increment_user_message_count(data)

        return result

    def _should_count_message(self, event: TelegramObject) -> bool:
        """
        Определяет, следует ли считать это сообщение в лимиты.

        Args:
            event: Событие Telegram

        Returns:
            bool: True если сообщение должно быть посчитано, False если нет
        """
        # Только текстовые сообщения от пользователей
        if isinstance(event, Message) and event.text:
            # Исключаем команды (сообщения, начинающиеся с /)
            if not event.text.startswith("/"):
                return True
        return False

    async def _increment_user_message_count(self, data: dict[str, Any]) -> None:
        """
        Увеличение счетчика сообщений пользователя.

        Args:
            data: Данные контекста обработки
        """
        user = data.get("user")
        if not user:
            return

        self._counter_stats["messages_counted"] += 1

        config = get_config()
        if not config.conversation.enable_saving:
            return

        try:
            # Добавляем пользователя в буфер для пакетного обновления
            self._batch_buffer[user.id] = datetime.now(UTC)

            # Запускаем таймер для пакетного обновления, если он еще не запущен
            if self._batch_timer is None:
                self._batch_timer = asyncio.get_event_loop().call_later(
                    self._batch_interval,
                    lambda: asyncio.create_task(self._process_batch_updates()),
                )

            # Обновляем статистику
            self._counter_stats["message_counts_updated"] += 1
            logger.info(
                get_log_text("middleware.user_message_count_updated").format(
                    user_id=user.id
                )
            )

        except Exception as e:
            self._counter_stats["counter_errors"] += 1
            logger.error(
                get_log_text("middleware.user_message_count_error").format(
                    user_id=user.id if user else "unknown", error=str(e)
                )
            )

    async def _process_batch_updates(self) -> None:
        """
        Обработка пакетных обновлений счетчиков сообщений пользователей.
        """
        if not self._batch_buffer:
            self._batch_timer = None
            return

        try:
            # Копируем буфер и очищаем его
            batch_updates = self._batch_buffer.copy()
            self._batch_buffer.clear()

            # Выполняем пакетное обновление
            async with get_session() as session:
                for user_id, activity_time in batch_updates.items():
                    stmt = (
                        update(User)
                        .where(User.id == user_id)
                        .values(
                            daily_message_count=User.daily_message_count + 1,
                            last_message_date=activity_time.date(),
                        )
                    )
                    await session.execute(stmt)
                await session.commit()

            logger.info(
                get_log_text("middleware.batch_updates_processed").format(
                    count=len(batch_updates)
                )
            )

        except Exception as e:
            self._counter_stats["counter_errors"] += 1
            logger.error(
                get_log_text("middleware.batch_updates_error").format(error=str(e))
            )
        finally:
            self._batch_timer = None

    @classmethod
    def get_counter_stats(cls) -> dict[str, int]:
        """
        Получение статистики по счетчикам.

        Returns:
            Словарь со статистикой по счетчикам
        """
        return cls._counter_stats.copy()

    @classmethod
    def reset_counter_stats(cls) -> None:
        """Сброс статистики по счетчикам."""
        cls._counter_stats = {
            "message_counts_updated": 0,
            "counter_errors": 0,
            "messages_counted": 0,
        }
        # Очищаем буфер пакетных обновлений
        cls._batch_buffer.clear()
        if cls._batch_timer:
            cls._batch_timer.cancel()
            cls._batch_timer = None
