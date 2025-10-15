"""
@file: middleware/auth.py
@description: Middleware для аутентификации пользователей
@dependencies: aiogram, loguru, app.models.user, app.services.user_service
@created: 2025-10-09
"""

from collections.abc import Awaitable, Callable
from typing import Any, ClassVar, cast

from aiogram.types import CallbackQuery, InaccessibleMessage, Message, TelegramObject
from aiogram.types import User as TelegramUser
from loguru import logger

from app.lexicon.gettext import get_log_text
from app.middleware.base import BaseAIMiddleware
from app.services.user_service import get_or_update_user


class AuthMiddleware(BaseAIMiddleware):
    """Middleware для автоматического получения/создания пользователя."""

    # Статистика по аутентификации
    _auth_stats: ClassVar[dict[str, int]] = {
        "users_authenticated": 0,
        "users_created": 0,
        "auth_errors": 0,
    }

    def __init__(self) -> None:
        """Инициализация AuthMiddleware."""
        super().__init__()
        logger.info(get_log_text("middleware.auth_middleware_initialized"))

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Обработка события с аутентификацией пользователя.

        Args:
            handler: Следующий обработчик в цепочке
            event: Событие Telegram
            data: Данные контекста обработки

        Returns:
            Результат выполнения следующего обработчика
        """
        # Получаем пользователя Telegram из события
        telegram_user: TelegramUser | None = None
        message: Message | None = None

        # Проверяем разные типы событий для получения пользователя и сообщения
        if isinstance(event, Message) and event.from_user:
            telegram_user = event.from_user
            message = event
        elif isinstance(event, CallbackQuery) and event.from_user:
            telegram_user = event.from_user
            # Для CallbackQuery проверяем, что message существует и доступен для редактирования
            if event.message and not isinstance(event.message, InaccessibleMessage):
                message = event.message

        # Только если у нас есть и пользователь, и сообщение, пытаемся аутентифицировать
        if telegram_user and message:
            try:
                # Получаем или создаем пользователя в базе данных
                user = await get_or_update_user(message)

                if user:
                    # Добавляем пользователя в данные контекста
                    data["user"] = user
                    self._auth_stats["users_authenticated"] += 1

                    logger.info(
                        get_log_text("middleware.user_authenticated").format(
                            user_id=user.id, username=user.username or "No username"
                        )
                    )
                else:
                    # Ошибка при создании/получении пользователя
                    self._auth_stats["auth_errors"] += 1
                    logger.warning(
                        get_log_text("middleware.user_auth_failed").format(
                            telegram_id=telegram_user.id
                        )
                    )

            except Exception as e:
                self._auth_stats["auth_errors"] += 1
                logger.error(
                    get_log_text("middleware.user_auth_error").format(
                        error=str(e),
                        telegram_id=telegram_user.id if telegram_user else "unknown",
                    )
                )

        # Передаем управление следующему обработчику
        return await handler(event, data)

    @classmethod
    def get_auth_stats(cls) -> dict[str, int]:
        """
        Получение статистики аутентификации.

        Returns:
            Словарь со статистикой аутентификации
        """
        return cls._auth_stats.copy()

    @classmethod
    def reset_auth_stats(cls) -> None:
        """Сброс статистики аутентификации."""
        cls._auth_stats = {
            "users_authenticated": 0,
            "users_created": 0,
            "auth_errors": 0,
        }
