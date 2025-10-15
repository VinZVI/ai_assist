"""
@file: middleware/anti_spam.py
@description: Middleware для защиты от спама
@dependencies: aiogram, loguru, app.models.user
@created: 2025-10-10
"""

from collections import defaultdict
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, ClassVar

from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram.types import User as TelegramUser
from loguru import logger

from app.config import get_config
from app.lexicon.gettext import get_log_text, get_text
from app.middleware.base import BaseAIMiddleware

if TYPE_CHECKING:
    from app.models.user import User


class AntiSpamMiddleware(BaseAIMiddleware):
    """Middleware для защиты от спама."""

    # Хранилище для отслеживания действий пользователей
    _user_actions: ClassVar[dict[int, list[datetime]]] = defaultdict(list)

    # Хранилище для отслеживания временных блокировок
    _user_blocks: ClassVar[dict[int, datetime]] = {}

    # Статистика по ограничениям
    _anti_spam_stats: ClassVar[dict[str, int]] = {
        "actions_blocked": 0,
        "users_blocked": 0,
        "actions_processed": 0,
    }

    def __init__(self) -> None:
        """Инициализация AntiSpamMiddleware."""
        super().__init__()
        logger.info(get_log_text("middleware.anti_spam_middleware_initialized"))

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Обработка события с защитой от спама.

        Args:
            handler: Следующий обработчик в цепочке
            event: Событие Telegram
            data: Данные контекста обработки

        Returns:
            Результат выполнения следующего обработчика или None, если действие заблокировано
        """
        # Получаем пользователя Telegram из события
        telegram_user: TelegramUser | None = None

        # Проверяем разные типы событий для получения пользователя
        if (isinstance(event, Message) and event.from_user) or \
           (isinstance(event, CallbackQuery) and event.from_user):
            telegram_user = event.from_user

        if telegram_user:
            user_id = telegram_user.id

            # Получаем пользователя из контекста (если уже аутентифицирован)
            user: User | None = data.get("user")

            # Проверяем, является ли пользователь администратором
            is_admin = data.get("is_admin", False)

            # Администраторы не подвержены ограничениям
            if is_admin:
                # Передаем управление следующему обработчику без проверки лимитов
                return await handler(event, data)

            # Проверяем, не заблокирован ли пользователь
            if self._is_user_blocked(user_id):
                # Пользователь еще заблокирован
                if isinstance(event, Message):
                    try:
                        user_lang = user.language_code if user else "ru"
                        await event.answer(
                            get_text(
                                "errors.user_temporarily_blocked", user_lang or "ru"
                            )
                        )
                    except Exception as e:
                        logger.warning(
                            get_log_text("middleware.anti_spam_message_error").format(
                                error=str(e)
                            )
                        )
                elif isinstance(event, CallbackQuery):
                    try:
                        user_lang = user.language_code if user else "ru"
                        await event.answer(
                            get_text(
                                "errors.user_temporarily_blocked", user_lang or "ru"
                            ),
                            show_alert=True,
                        )
                    except Exception as e:
                        logger.warning(
                            get_log_text("middleware.anti_spam_callback_error").format(
                                error=str(e)
                            )
                        )

                # Не передаем управление следующему обработчику
                return None

            # Очищаем старые записи (старше 1 минуты)
            cutoff_time = datetime.now(UTC) - timedelta(minutes=1)
            self._user_actions[user_id] = [
                timestamp
                for timestamp in self._user_actions[user_id]
                if timestamp > cutoff_time
            ]

            self._anti_spam_stats["actions_processed"] += 1

            # Получаем конфигурацию
            config = get_config()
            actions_per_minute_limit = config.user_limits.spam_actions_per_minute

            # Проверяем лимит действий в минуту
            if len(self._user_actions[user_id]) >= actions_per_minute_limit:
                # Превышен лимит действий
                self._anti_spam_stats["actions_blocked"] += 1

                # Логируем только первый раз для пользователя в течение минуты
                if len(self._user_actions[user_id]) == actions_per_minute_limit:
                    self._anti_spam_stats["users_blocked"] += 1
                    logger.warning(
                        get_log_text("middleware.anti_spam_limit_exceeded").format(
                            user_id=user_id,
                            actions_count=len(self._user_actions[user_id]),
                            limit=actions_per_minute_limit,
                        )
                    )

                    # Блокируем пользователя на указанное время
                    block_duration = config.user_limits.spam_restriction_duration
                    self._user_blocks[user_id] = datetime.now(UTC) + timedelta(
                        seconds=block_duration
                    )

                # Отправляем сообщение пользователю
                if isinstance(event, Message):
                    try:
                        user_lang = user.language_code if user else "ru"
                        await event.answer(
                            get_text("errors.spam_limit_exceeded", user_lang or "ru")
                        )
                    except Exception as e:
                        logger.warning(
                            get_log_text("middleware.anti_spam_message_error").format(
                                error=str(e)
                            )
                        )
                elif isinstance(event, CallbackQuery):
                    try:
                        user_lang = user.language_code if user else "ru"
                        await event.answer(
                            get_text("errors.spam_limit_exceeded", user_lang or "ru"),
                            show_alert=True,
                        )
                    except Exception as e:
                        logger.warning(
                            get_log_text("middleware.anti_spam_callback_error").format(
                                error=str(e)
                            )
                        )

                # Не передаем управление следующему обработчику
                return None

            # Добавляем текущее действие
            self._user_actions[user_id].append(datetime.now(UTC))

        # Передаем управление следующему обработчику
        return await handler(event, data)

    def _is_user_blocked(self, user_id: int) -> bool:
        """
        Проверяет, заблокирован ли пользователь.

        Args:
            user_id: ID пользователя

        Returns:
            bool: True если пользователь заблокирован, False если нет
        """
        if user_id in self._user_blocks:
            block_until = self._user_blocks[user_id]
            current_time = datetime.now(UTC)
            # Проверяем, истекла ли блокировка
            if current_time >= block_until:
                # Блокировка истекла, удаляем запись
                del self._user_blocks[user_id]
                return False
            # Блокировка еще действует
            return True
        return False

    @classmethod
    def get_anti_spam_stats(cls) -> dict[str, int]:
        """
        Получение статистики защиты от спама.

        Returns:
            Словарь со статистикой защиты от спама
        """
        return cls._anti_spam_stats.copy()

    @classmethod
    def reset_anti_spam_stats(cls) -> None:
        """Сброс статистики защиты от спама."""
        cls._anti_spam_stats = {
            "actions_blocked": 0,
            "users_blocked": 0,
            "actions_processed": 0,
        }
        cls._user_actions.clear()
        cls._user_blocks.clear()
