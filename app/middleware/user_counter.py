"""
@file: middleware/user_counter.py
@description: Middleware для подсчета сообщений пользователей
@dependencies: aiogram, loguru, app.models.user
@created: 2025-10-09
"""

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


class UserCounterMiddleware(BaseAIMiddleware):
    """Middleware для подсчета сообщений пользователей."""

    # Статистика по счетчикам
    _counter_stats: ClassVar[dict[str, int]] = {
        "message_counts_updated": 0,
        "counter_errors": 0,
        "update_requests_processed": 0,
    }

    def __init__(self) -> None:
        """Инициализация UserCounterMiddleware."""
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
        # Добавляем функцию обновления счетчика в данные контекста
        data["increment_user_message_count"] = self._increment_user_message_count

        # Передаем управление следующему обработчику
        result = await handler(event, data)

        # После выполнения обработчика проверяем, нужно ли обновить счетчик
        if data.get("update_user_count"):
            await self._process_user_count_update(data)

        return result

    async def _increment_user_message_count(self, user_id: int) -> bool:
        """
        Увеличение счетчика сообщений пользователя через контекст middleware.

        Args:
            user_id: ID пользователя

        Returns:
            bool: True если успешно обновлено, False в случае ошибки
        """
        self._counter_stats["update_requests_processed"] += 1

        config = get_config()
        if not config.conversation.enable_saving:
            return True

        try:
            async with get_session() as session:
                stmt = (
                    update(User)
                    .where(User.id == user_id)
                    .values(
                        daily_message_count=User.daily_message_count + 1,
                        last_message_date=datetime.now(UTC).date(),
                    )
                )
                await session.execute(stmt)
                await session.commit()

                self._counter_stats["message_counts_updated"] += 1
                logger.info(
                    get_log_text("middleware.user_message_count_updated").format(
                        user_id=user_id
                    )
                )
                return True

        except Exception as e:
            self._counter_stats["counter_errors"] += 1
            logger.error(
                get_log_text("middleware.user_message_count_error").format(
                    user_id=user_id, error=str(e)
                )
            )
            return False

    async def _process_user_count_update(self, data: dict[str, Any]) -> None:
        """
        Обработка обновления счетчика пользователя после выполнения обработчика.

        Args:
            data: Данные контекста обработки
        """
        user = data.get("user")
        if not user:
            return

        config = get_config()
        if not config.conversation.enable_saving:
            return

        try:
            async with get_session() as session:
                stmt = (
                    update(User)
                    .where(User.id == user.id)
                    .values(
                        daily_message_count=User.daily_message_count + 1,
                        last_message_date=datetime.now(UTC).date(),
                    )
                )
                await session.execute(stmt)
                await session.commit()

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
            "update_requests_processed": 0,
        }
