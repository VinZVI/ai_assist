"""
@file: middleware/user_language.py
@description: Middleware для управления языком пользователя
@dependencies: aiogram, loguru, app.models.user
@created: 2025-10-09
"""

from collections.abc import Awaitable, Callable
from typing import Any, ClassVar

from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram.types import User as TelegramUser
from loguru import logger

from app.lexicon.gettext import get_log_text
from app.middleware.base import BaseAIMiddleware


class UserLanguageMiddleware(BaseAIMiddleware):
    """Middleware для управления языком пользователя."""

    # Статистика по языкам
    _language_stats: ClassVar[dict[str, int]] = {
        "language_requests_processed": 0,
        "users_with_language": 0,
    }

    def __init__(self) -> None:
        """Инициализация UserLanguageMiddleware."""
        super().__init__()
        logger.info(get_log_text("middleware.user_language_middleware_initialized"))

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Обработка события с управлением языком пользователя.

        Args:
            handler: Следующий обработчик в цепочке
            event: Событие Telegram
            data: Данные контекста обработки

        Returns:
            Результат выполнения следующего обработчика
        """
        # Получаем пользователя из данных контекста (предоставленный AuthMiddleware)
        user = data.get("user")

        if user:
            # Устанавливаем язык пользователя в данные контекста
            user_lang = user.language_code or "ru"
            data["user_lang"] = user_lang
            self._language_stats["users_with_language"] += 1

            logger.debug(
                get_log_text("middleware.user_language_set").format(
                    user_id=user.id, language=user_lang
                )
            )
        else:
            # Если пользователь не найден, используем язык по умолчанию
            data["user_lang"] = "ru"

        self._language_stats["language_requests_processed"] += 1

        # Передаем управление следующему обработчику
        return await handler(event, data)

    @classmethod
    def get_language_stats(cls) -> dict[str, int]:
        """
        Получение статистики по языкам.

        Returns:
            Словарь со статистикой по языкам
        """
        return cls._language_stats.copy()

    @classmethod
    def reset_language_stats(cls) -> None:
        """Сброс статистики по языкам."""
        cls._language_stats = {
            "language_requests_processed": 0,
            "users_with_language": 0,
        }
