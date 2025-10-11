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
from sqlalchemy import select, update

from app.config import get_config
from app.database import get_session
from app.lexicon.gettext import get_log_text, get_text
from app.middleware.base import BaseAIMiddleware
from app.models.user import User


class MessageCountingMiddleware(BaseAIMiddleware):
    """Middleware для подсчета сообщений пользователей."""

    # Статистика по счетчикам
    _counter_stats: ClassVar[dict[str, int]] = {
        "message_counts_updated": 0,
        "counter_errors": 0,
        "messages_counted": 0,
        "limits_exceeded": 0,
    }

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
            Результат выполнения следующего обработчика или None, если лимит исчерпан
        """
        # Проверяем лимиты только для текстовых сообщений (не команд и не callback'ов)
        if self._should_count_message(event):
            user: User | None = data.get("user")
            if user:
                # Проверяем, может ли пользователь отправить сообщение
                can_send = await self._check_user_message_limit(user, event, data)
                if not can_send:
                    # Лимит исчерпан, не передаем управление следующему обработчику
                    return None

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

    async def _check_user_message_limit(
        self, user: User, event: TelegramObject, data: dict[str, Any]
    ) -> bool:
        """
        Проверяет, может ли пользователь отправить сообщение в соответствии с лимитами.

        Args:
            user: Пользователь
            event: Событие Telegram
            data: Данные контекста обработки

        Returns:
            bool: True если можно отправить сообщение, False если лимит исчерпан
        """
        config = get_config()
        daily_limit = config.user_limits.daily_message_limit

        # Для премиум пользователей нет ограничений
        if user.is_premium_active():
            return True

        # Сброс счетчика если прошел день
        today = datetime.now(UTC).date()
        if user.last_message_date is not None and user.last_message_date < today:
            # Сбрасываем счетчик в базе данных
            try:
                async with get_session() as session:
                    stmt = (
                        update(User)
                        .where(User.id == user.id)
                        .values(
                            daily_message_count=0,
                            last_message_date=today,
                        )
                    )
                    await session.execute(stmt)
                    await session.commit()
                    # Обновляем объект пользователя
                    user.daily_message_count = 0
                    user.last_message_date = today
            except Exception as e:
                logger.error(
                    get_log_text("middleware.user_message_count_error").format(
                        user_id=user.id, error=str(e)
                    )
                )

        # Проверяем лимит
        if user.daily_message_count >= daily_limit:
            # Лимит исчерпан
            self._counter_stats["limits_exceeded"] += 1
            logger.warning(
                get_log_text("middleware.daily_limit_exceeded").format(
                    user_id=user.id,
                    daily_count=user.daily_message_count,
                    limit=daily_limit,
                )
            )

            # Отправляем сообщение пользователю
            if isinstance(event, Message):
                try:
                    user_lang = user.language_code if user else "ru"
                    await event.answer(
                        get_text("errors.daily_limit_exceeded", user_lang or "ru")
                    )
                except Exception as e:
                    logger.warning(
                        get_log_text("middleware.daily_limit_message_error").format(
                            error=str(e)
                        )
                    )

            return False

        return True

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
            async with get_session() as session:
                stmt = (
                    update(User)
                    .where(User.id == user.id)
                    .values(
                        daily_message_count=User.daily_message_count + 1,
                        total_messages=User.total_messages + 1,
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
            "messages_counted": 0,
            "limits_exceeded": 0,
        }
