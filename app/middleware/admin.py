"""
@file: middleware/admin.py
@description: Middleware для проверки прав администратора
@dependencies: aiogram, loguru
@created: 2025-10-10
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram.types import CallbackQuery, Message, TelegramObject
from loguru import logger

from app.config import get_config
from app.lexicon.gettext import get_log_text
from app.middleware.base import BaseAIMiddleware


class AdminMiddleware(BaseAIMiddleware):
    """Middleware для проверки прав администратора."""

    def __init__(self) -> None:
        """Инициализация AdminMiddleware."""
        super().__init__()
        logger.info(get_log_text("middleware.admin_middleware_initialized"))

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Обработка события с проверкой прав администратора.

        Args:
            handler: Следующий обработчик в цепочке
            event: Событие Telegram
            data: Данные контекста обработки

        Returns:
            Результат выполнения следующего обработчика
        """
        user_id = None
        
        # Проверяем, является ли событие сообщением
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        # Проверяем, является ли событие callback query
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        # Если удалось получить ID пользователя, проверяем права администратора
        if user_id is not None:
            # Получаем конфигурацию для проверки админских ID
            config = get_config()
            admin_ids = config.admin.get_admin_ids()

            # Проверяем, является ли пользователь администратором
            if user_id in admin_ids:
                # Добавляем информацию о правах администратора в данные контекста
                data["is_admin"] = True
                logger.debug(
                    get_log_text("middleware.admin_access_granted").format(
                        admin_id=user_id
                    )
                )
            else:
                # Пользователь не является администратором
                data["is_admin"] = False
                logger.debug(
                    get_log_text("middleware.admin_access_denied").format(
                        user_id=user_id
                    )
                )
        else:
            # Если не удалось получить информацию о пользователе, устанавливаем флаг по умолчанию
            data["is_admin"] = False

        # Передаем управление следующему обработчику
        return await handler(event, data)