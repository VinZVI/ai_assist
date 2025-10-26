"""Сервис для работы с диалогами пользователей.

Этот сервис управляет контекстом диалогов пользователей, сохраняя отдельно
последние 5 сообщений пользователя и 5 ответов ИИ для каждого пользователя.
Контекст сохраняется в кэше и периодически сбрасывается в базу данных
после периода неактивности пользователя.
"""

from datetime import UTC, datetime
from typing import Any, Dict, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import container
from app.models.conversation import Conversation
from app.services.ai_providers.base import (
    ConversationMessage,
    UserAIConversationContext,
)
from app.services.conversation.conversation_history import (
    get_conversation_context_from_db,
    get_recent_conversation_history,
)
from app.services.conversation.conversation_storage import (
    save_all_pending_conversations,
    save_conversation_context_from_cache,
    save_conversation_to_db,
)


class ConversationService:
    """Сервис для работы с диалогами.

    Управляет контекстом диалогов пользователей, обеспечивая:
    1. Хранение отдельно последних 5 сообщений пользователя и 5 ответов ИИ
    2. Автоматическое ограничение количества сообщений
    3. Сохранение контекста в кэше и базе данных
    4. Восстановление контекста при перезапуске приложения
    """

    def __init__(self) -> None:
        self._cache_service = None
        self._initialized = False

    async def initialize(self) -> None:
        """Асинхронная инициализация сервиса."""
        if self._initialized:
            return

        self._cache_service = container.get("cache_service")
        self._initialized = True
        logger.info("ConversationService initialized")

    @property
    def cache_service(self) -> Any:
        """Ленивое получение cache_service."""
        if not self._cache_service:
            self._cache_service = container.get("cache_service")
        return self._cache_service

    async def get_recent_conversation_history(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
        max_age_hours: int = 24,
    ) -> list[ConversationMessage]:
        """Получение истории последних сообщений пользователя."""
        return await get_recent_conversation_history(
            session, user_id, limit, max_age_hours
        )

    async def get_conversation_context(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
        max_age_hours: int = 24,
    ) -> dict[str, Any]:
        """Получение контекста диалога в правильном формате.

        Создает контекст диалога с разделением на последние 5 сообщений пользователя
        и 5 ответов ИИ. Использует UserAIConversationContext для автоматического
        ограничения количества сообщений.

        Args:
            session: Сессия базы данных
            user_id: ID пользователя
            limit: Максимальное количество сообщений
            max_age_hours: Максимальный возраст сообщений в часах

        Returns:
            dict: Контекст диалога с метаинформацией
        """
        try:
            history = await self.get_recent_conversation_history(
                session, user_id, limit, max_age_hours
            )

            # Создаем новый контекст с разделением на пользовательские сообщения и ответы ИИ
            context = UserAIConversationContext(
                user_messages=[msg for msg in history if msg.role == "user"][
                    -5:
                ],  # Последние 5
                ai_responses=[msg for msg in history if msg.role == "assistant"][
                    -5:
                ],  # Последние 5
                last_interaction=history[-1].timestamp if history else None,
                topics=[],  # Populate with real topics if available
                emotional_tone="neutral",  # Default, should be updated based on content
            )

            # Преобразуем в словарь для совместимости
            context_dict = context.to_dict()
            # Добавляем дополнительные поля для совместимости
            # Исправляем ошибку сериализации ConversationMessage объектов
            context_dict["history"] = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                }
                for msg in context.get_combined_history()
            ]
            context_dict["message_count"] = len(context.user_messages)

            return context_dict

        except Exception as e:
            logger.error(f"❌ Ошибка при получении контекста: {e}")
            # Return empty context as fallback
            return {
                "user_messages": [],
                "ai_responses": [],
                "history": [],
                "message_count": 0,
                "last_interaction": None,
                "topics": [],
                "emotional_tone": "neutral",
            }

    async def save_conversation_with_cache(
        self,
        user_id: int,
        user_message: str,
        ai_response: str,
        ai_model: str,
        tokens_used: int,
        response_time: float,
    ) -> bool:
        """Сохранение диалога с использованием кэша.

        Сохраняет диалог в кэше с использованием UserAIConversationContext,
        который автоматически ограничивает количество сообщений до 5 для
        каждого типа (пользовательские сообщения и ответы ИИ).

        Args:
            user_id: ID пользователя
            user_message: Сообщение пользователя
            ai_response: Ответ ИИ
            ai_model: Модель ИИ
            tokens_used: Количество использованных токенов
            response_time: Время ответа в секундах

        Returns:
            bool: True если успешно сохранено, False в случае ошибки
        """
        try:
            # Валидация входных данных
            from app.utils.validators import InputValidator

            is_valid, error_msg = InputValidator.validate_message_length(user_message)
            if not is_valid:
                logger.error(f"Invalid user message: {error_msg}")
                return False

            # Подготовка данных для кэша в правильном формате
            conversation_data = {
                "user_message": user_message,
                "ai_response": ai_response,
                "ai_model": ai_model,
                "tokens_used": tokens_used,
                "response_time": response_time,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            # Получаем существующий контекст из кэша
            existing_context_dict = await self.cache_service.get_conversation_context(
                user_id, limit=10, max_age_hours=24
            )

            # Если нет существующего контекста, создаем новый
            if not existing_context_dict or not isinstance(existing_context_dict, dict):
                context = UserAIConversationContext(
                    user_messages=[],
                    ai_responses=[],
                    last_interaction=None,
                    topics=[],
                    emotional_tone="neutral",
                )
            else:
                # Создаем контекст из существующих данных
                try:
                    context = UserAIConversationContext.from_dict(existing_context_dict)
                except Exception:
                    # Если возникла ошибка, создаем новый контекст
                    context = UserAIConversationContext(
                        user_messages=[],
                        ai_responses=[],
                        last_interaction=None,
                        topics=[],
                        emotional_tone="neutral",
                    )

            # Добавляем новые сообщения в контекст
            context.add_user_message(
                ConversationMessage(
                    role="user", content=user_message, timestamp=datetime.now(UTC)
                )
            )

            context.add_ai_response(
                ConversationMessage(
                    role="assistant", content=ai_response, timestamp=datetime.now(UTC)
                )
            )

            # Преобразуем контекст в словарь для сохранения
            context_dict = context.to_dict()
            # Добавляем дополнительные поля для совместимости
            # Исправляем ошибку сериализации ConversationMessage объектов
            context_dict["history"] = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                }
                for msg in context.get_combined_history()
            ]
            context_dict["message_count"] = len(context.user_messages)

            # Сохранение через персистентность
            if (
                hasattr(self.cache_service, "conversation_persistence")
                and self.cache_service.conversation_persistence
            ):
                await self.cache_service.conversation_persistence.save_conversation_context(
                    user_id,
                    {"conversation_data": conversation_data, "context": context_dict},
                    immediate_backup=True,
                )
            else:
                # Fallback на старый метод
                await self.cache_service.set_conversation_data(
                    user_id,
                    {"conversation_data": conversation_data, "context": context_dict},
                )
                # Also save the context properly
                await self.cache_service.set_conversation_context(
                    user_id, context_dict, limit=6, max_age_hours=12, ttl_seconds=1800
                )

            # Обновляем активность пользователя
            await self.cache_service.set_user_activity(user_id)

            logger.info(f"Conversation cached for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save conversation for user {user_id}: {e}")
            return False

    async def save_all_pending_conversations(self) -> int:
        """Сохранение всех ожидающих диалогов из кэша в БД.

        Принудительно сбрасывает все данные из кэша в базу данных,
        обеспечивая сохранность данных при завершении работы приложения.

        Returns:
            int: Количество успешно сохраненных диалогов
        """
        return await save_all_pending_conversations(self.cache_service)

    async def _save_conversation_to_db(
        self, session: AsyncSession, user_id: int, conversation_data: dict
    ) -> bool:
        """Прямое сохранение диалога в БД."""
        try:
            # Извлекаем данные разговора
            conv_data = conversation_data.get("conversation_data", {})

            # Создаем записи диалога
            user_conv = Conversation(
                user_id=user_id,
                message_text=conv_data.get("user_message", ""),
                role="user",
                status="completed",  # Using string literal to avoid import issues
            )
            session.add(user_conv)

            ai_conv = Conversation(
                user_id=user_id,
                message_text=conv_data.get("user_message", ""),
                response_text=conv_data.get("ai_response", ""),
                role="assistant",
                status="completed",  # Using string literal to avoid import issues
                ai_model=conv_data.get("ai_model", ""),
                tokens_used=conv_data.get("tokens_used", 0),
                response_time_ms=int(conv_data.get("response_time", 0) * 1000),
            )
            session.add(ai_conv)

            await session.commit()
            return True

        except Exception as e:
            logger.error(f"Database save error for user {user_id}: {e}")
            await session.rollback()
            return False
