"""
@file: middleware/conversation.py
@description: Middleware для сохранения диалогов
@dependencies: aiogram, loguru, app.models.user, app.services.conversation.conversation_storage
@created: 2025-10-09
@updated: 2025-10-26
"""

from collections.abc import Awaitable, Callable
from typing import Any, ClassVar

from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram.types import User as TelegramUser
from loguru import logger

from app.config import get_config
from app.database import get_session
from app.lexicon.gettext import get_log_text
from app.middleware.base import BaseAIMiddleware
from app.services.conversation.conversation_storage import (
    save_conversation_context_from_cache,
    save_conversation_to_db,
)


class ConversationMiddleware(BaseAIMiddleware):
    """Middleware для сохранения диалогов."""

    # Статистика по сохранению диалогов
    _conversation_stats: ClassVar[dict[str, int]] = {
        "conversations_saved": 0,
        "conversations_save_errors": 0,
        "save_requests_processed": 0,
    }

    def __init__(self) -> None:
        """Инициализация ConversationMiddleware."""
        super().__init__()
        logger.info(get_log_text("middleware.conversation_middleware_initialized"))

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Обработка события с сохранением диалогов.

        Args:
            handler: Следующий обработчик в цепочке
            event: Событие Telegram
            data: Данные контекста обработки

        Returns:
            Результат выполнения следующего обработчика
        """
        # Добавляем функцию сохранения диалога в данные контекста
        data["save_conversation"] = self._save_conversation_context

        # Передаем управление следующему обработчику
        result = await handler(event, data)

        # После выполнения обработчика проверяем, есть ли данные для сохранения
        if "conversation_data" in data:
            await self._process_conversation_save(data)

        return result

    async def _save_conversation_context(
        self,
        user_id: int,
        user_message: str,
        ai_response: str,
        ai_model: str,
        tokens_used: int,
        response_time: float,
    ) -> bool:
        """
        Сохранение диалога через контекст middleware с использованием кэша и проверки неактивности.

        Args:
            user_id: ID пользователя
            user_message: Сообщение пользователя
            ai_response: Ответ AI
            ai_model: Модель AI
            tokens_used: Количество использованных токенов
            response_time: Время ответа в секундах

        Returns:
            bool: True если успешно сохранено, False в случае ошибки
        """
        # Сохраняем данные для последующего сохранения
        self._conversation_stats["save_requests_processed"] += 1

        config = get_config()
        if not config.conversation.enable_saving:
            return True

        # Используем новый метод сохранения из кэша с проверкой неактивности
        from app.services.cache_service import cache_service

        # Обновляем время активности пользователя в кэше
        await cache_service.set_user_activity(user_id)

        # Сохраняем данные диалога в кэше для последующего сохранения в БД
        conversation_data = {
            "user_message": user_message,
            "ai_response": ai_response,
            "ai_model": ai_model,
            "tokens_used": tokens_used,
            "response_time": response_time,
        }

        # Сохраняем в кэш с TTL из конфигурации (время неактивности пользователя)
        await cache_service.set_conversation_data(
            user_id, conversation_data, ttl_seconds=config.conversation.cache_ttl
        )

        logger.info(
            get_log_text("middleware.conversation_cached").format(user_id=user_id)
        )
        return True

    async def _process_conversation_save(self, data: dict[str, Any]) -> None:
        """
        Обработка сохранения диалога после выполнения обработчика.

        Args:
            data: Данные контекста обработки
        """
        conversation_data = data["conversation_data"]
        config = get_config()

        if not config.conversation.enable_saving:
            return

        # Используем новый метод сохранения из кэша с проверкой неактивности
        success = await save_conversation_context_from_cache(
            user_id=conversation_data["user_id"],
            user_message=conversation_data["user_message"],
            ai_response=conversation_data["ai_response"],
            ai_model=conversation_data["ai_model"],
            tokens_used=conversation_data["tokens_used"],
            response_time=conversation_data["response_time"],
            cache_ttl=config.conversation.cache_ttl,
        )

        if success:
            self._conversation_stats["conversations_saved"] += 1
            logger.info(
                get_log_text("middleware.conversation_saved").format(
                    user_id=conversation_data["user_id"]
                )
            )
        else:
            self._conversation_stats["conversations_save_errors"] += 1
            logger.error(
                get_log_text("middleware.conversation_save_error").format(
                    user_id=conversation_data["user_id"]
                )
            )

    @classmethod
    def get_conversation_stats(cls) -> dict[str, int]:
        """
        Получение статистики по сохранению диалогов.

        Returns:
            Словарь со статистикой по сохранению диалогов
        """
        return cls._conversation_stats.copy()

    @classmethod
    def reset_conversation_stats(cls) -> None:
        """Сброс статистики по сохранению диалогов."""
        cls._conversation_stats = {
            "conversations_saved": 0,
            "conversations_save_errors": 0,
            "save_requests_processed": 0,
        }
