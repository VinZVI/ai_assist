"""
@file: middleware/rate_limit.py
@description: Middleware для ограничения частоты запросов
@dependencies: aiogram, loguru, app.models.user
@created: 2025-10-09
"""

from collections import defaultdict
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, ClassVar

from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram.types import User as TelegramUser
from loguru import logger

from app.lexicon.gettext import get_log_text, get_text
from app.middleware.base import BaseAIMiddleware

if TYPE_CHECKING:
    from app.models.user import User


class RateLimitMiddleware(BaseAIMiddleware):
    """Middleware для ограничения частоты запросов."""

    # Хранилище для отслеживания запросов пользователей
    _request_counts: ClassVar[dict[int, list[datetime]]] = defaultdict(list)

    # Статистика по ограничениям
    _rate_limit_stats: ClassVar[dict[str, int]] = {
        "requests_limited": 0,
        "users_limited": 0,
        "requests_processed": 0,
    }

    def __init__(self, requests_per_minute: int = 10) -> None:
        """
        Инициализация RateLimitMiddleware.

        Args:
            requests_per_minute: Максимальное количество запросов в минуту
        """
        super().__init__()
        self.requests_per_minute = requests_per_minute
        logger.info(
            get_log_text("middleware.rate_limit_middleware_initialized").format(
                limit=requests_per_minute
            )
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Обработка события с ограничением частоты запросов.

        Args:
            handler: Следующий обработчик в цепочке
            event: Событие Telegram
            data: Данные контекста обработки

        Returns:
            Результат выполнения следующего обработчика или None, если запрос ограничен
        """
        # Получаем пользователя Telegram из события
        telegram_user: TelegramUser | None = None

        # Проверяем разные типы событий для получения пользователя
        if isinstance(event, Message) and event.from_user:
            telegram_user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            telegram_user = event.from_user

        if telegram_user:
            user_id = telegram_user.id

            # Получаем пользователя из контекста (если уже аутентифицирован)
            user: User | None = data.get("user")

            # Для премиум пользователей увеличиваем лимит в 2 раза
            max_requests = self.requests_per_minute * (
                2 if user and user.is_premium else 1
            )

            # Очищаем старые записи (старше 1 минуты)
            cutoff_time = datetime.now(UTC) - timedelta(minutes=1)
            self._request_counts[user_id] = [
                timestamp
                for timestamp in self._request_counts[user_id]
                if timestamp > cutoff_time
            ]

            # Проверяем, следует ли применять ограничение частоты для этого события
            if self._should_apply_rate_limit(event):
                self._rate_limit_stats["requests_processed"] += 1

                # Проверяем лимит
                if len(self._request_counts[user_id]) >= max_requests:
                    # Превышен лимит запросов
                    self._rate_limit_stats["requests_limited"] += 1

                    # Логируем только первый раз для пользователя в течение минуты
                    if len(self._request_counts[user_id]) == max_requests:
                        self._rate_limit_stats["users_limited"] += 1
                        logger.warning(
                            get_log_text("middleware.rate_limit_exceeded").format(
                                user_id=user_id,
                                requests_count=len(self._request_counts[user_id]),
                                limit=max_requests,
                            )
                        )

                    # Отправляем сообщение пользователю только для сообщений
                    # Для callback queries отправляем ответ на callback
                    if isinstance(event, Message):
                        try:
                            user_lang = user.language_code if user else "ru"
                            await event.answer(
                                get_text(
                                    "errors.rate_limit_exceeded", user_lang or "ru"
                                )
                            )
                        except Exception as e:
                            logger.warning(
                                get_log_text(
                                    "middleware.rate_limit_message_error"
                                ).format(error=str(e))
                            )
                    elif isinstance(event, CallbackQuery):
                        try:
                            user_lang = user.language_code if user else "ru"
                            await event.answer(
                                get_text(
                                    "errors.rate_limit_exceeded", user_lang or "ru"
                                ),
                                show_alert=True,
                            )
                        except Exception as e:
                            logger.warning(
                                get_log_text(
                                    "middleware.rate_limit_callback_error"
                                ).format(error=str(e))
                            )

                    # Не передаем управление следующему обработчику
                    return None

            # Добавляем текущий запрос только если применяем ограничение
            # Но не считаем callback-запросы в лимит сообщений
            if self._should_apply_rate_limit(
                event
            ) and self._should_count_toward_message_limit(event):
                self._request_counts[user_id].append(datetime.now(UTC))

        # Передаем управление следующему обработчику
        return await handler(event, data)

    def _should_apply_rate_limit(self, event: TelegramObject) -> bool:
        """
        Определяет, следует ли применять ограничение частоты для этого события.

        Args:
            event: Событие Telegram

        Returns:
            bool: True если следует применять ограничение, False если нет
        """
        # Применяем ограничение к текстовым сообщениям (не командам) и callback-запросам
        if isinstance(event, Message):
            # Проверяем, есть ли текст у сообщения
            if hasattr(event, "text") and event.text:
                # Исключаем команды (сообщения, начинающиеся с /)
                if not event.text.startswith("/"):
                    return True
        elif isinstance(event, CallbackQuery):
            # Применяем ограничение к callback-запросам
            return True
        return False

    def _should_count_toward_message_limit(self, event: TelegramObject) -> bool:
        """
        Определяет, следует ли считать это событие в лимит сообщений.

        Args:
            event: Событие Telegram

        Returns:
            bool: True если следует считать в лимит, False если нет
        """
        # Считаем только текстовые сообщения (не команды)
        if isinstance(event, Message):
            # Проверяем, есть ли текст у сообщения
            if hasattr(event, "text") and event.text:
                # Исключаем команды (сообщения, начинающиеся с /)
                if not event.text.startswith("/"):
                    return True
        # Callback-запросы и команды не считаются в лимит сообщений
        return False

    @classmethod
    def get_rate_limit_stats(cls) -> dict[str, int]:
        """
        Получение статистики ограничения частоты запросов.

        Returns:
            Словарь со статистикой ограничения частоты
        """
        return cls._rate_limit_stats.copy()

    @classmethod
    def reset_rate_limit_stats(cls) -> None:
        """Сброс статистики ограничения частоты запросов."""
        cls._rate_limit_stats = {
            "requests_limited": 0,
            "users_limited": 0,
            "requests_processed": 0,
        }
        cls._request_counts.clear()
