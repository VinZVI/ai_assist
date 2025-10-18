"""
Рефакторинг conversation_service без циркулярных импортов.
"""

from datetime import UTC, datetime, timedelta
from typing import Any, List

from loguru import logger
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, ConversationStatus
from app.services.ai_providers.base import ConversationMessage
from app.core.dependencies import container


class ConversationService:
    """Сервис для работы с диалогами без циркулярных импортов."""

    def __init__(self):
        self._cache_service = None
        self._initialized = False

    async def initialize(self):
        """Асинхронная инициализация сервиса."""
        if self._initialized:
            return

        self._cache_service = container.get("cache_service")
        self._initialized = True
        logger.info("ConversationService initialized")

    @property
    def cache_service(self):
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
        try:
            cutoff_time = datetime.now(UTC) - timedelta(hours=max_age_hours)

            stmt = (
                select(Conversation)
                .where(
                    and_(
                        Conversation.user_id == user_id,
                        Conversation.status == ConversationStatus.COMPLETED,
                        Conversation.created_at >= cutoff_time,
                    )
                )
                .order_by(desc(Conversation.created_at))
                .limit(limit)
            )

            result = await session.execute(stmt)
            conversations = result.scalars().all()

            messages = []
            for conv in reversed(conversations):
                if conv.message_text:
                    messages.append(
                        ConversationMessage(
                            role="user",
                            content=conv.message_text,
                            timestamp=conv.created_at,
                        )
                    )

                if conv.response_text:
                    messages.append(
                        ConversationMessage(
                            role="assistant",
                            content=conv.response_text,
                            timestamp=conv.processed_at or conv.created_at,
                        )
                    )

            return messages[-limit:] if len(messages) > limit else messages

        except Exception as e:
            logger.error(f"❌ Ошибка при получении истории: {e}")
            return []

    async def save_conversation_with_cache(
        self,
        user_id: int,
        user_message: str,
        ai_response: str,
        ai_model: str,
        tokens_used: int,
        response_time: float,
    ) -> bool:
        """Сохранение диалога с использованием кэша."""
        try:
            # Валидация входных данных
            from app.utils.validators import InputValidator

            is_valid, error_msg = InputValidator.validate_message_length(user_message)
            if not is_valid:
                logger.error(f"Invalid user message: {error_msg}")
                return False

            # Подготовка данных для кэша
            conversation_data = {
                "user_message": user_message,
                "ai_response": ai_response,
                "ai_model": ai_model,
                "tokens_used": tokens_used,
                "response_time": response_time,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            # Сохранение через персистентность
            if hasattr(self.cache_service, "conversation_persistence"):
                await self.cache_service.conversation_persistence.save_conversation_context(
                    user_id, {"conversation_data": conversation_data}
                )
            else:
                # Fallback на старый метод
                await self.cache_service.set_conversation_data(
                    user_id, conversation_data
                )

            # Обновляем активность пользователя
            await self.cache_service.set_user_activity(user_id)

            logger.info(f"Conversation cached for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save conversation for user {user_id}: {e}")
            return False

    async def save_all_pending_conversations(self) -> int:
        """Сохранение всех ожидающих диалогов из кэша в БД."""
        saved_count = 0

        try:
            # Используем персистентность если доступна
            if hasattr(self.cache_service, "conversation_persistence"):
                persistence = self.cache_service.conversation_persistence

                # Принудительно сбрасываем все данные из буфера
                for user_id in list(persistence.memory_buffer.keys()):
                    try:
                        await persistence._flush_to_database(user_id)
                        saved_count += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to flush conversation for user {user_id}: {e}"
                        )

            else:
                # Используем старый метод
                from app.database import get_session

                pending_data = (
                    self.cache_service.memory_cache._conversation_context_cache.copy()
                )

                for user_id, data_entry in pending_data.items():
                    try:
                        if datetime.now(UTC) <= data_entry["expires_at"]:
                            data = data_entry["data"]

                            async with get_session() as session:
                                success = await self._save_conversation_to_db(
                                    session, user_id, data
                                )

                                if success:
                                    await self.cache_service.memory_cache.delete_pending_conversation_data(
                                        user_id
                                    )
                                    saved_count += 1

                    except Exception as e:
                        logger.error(
                            f"Failed to save conversation for user {user_id}: {e}"
                        )

            logger.info(f"Saved {saved_count} pending conversations to database")

        except Exception as e:
            logger.error(f"Error saving pending conversations: {e}")

        return saved_count

    async def _save_conversation_to_db(
        self, session: AsyncSession, user_id: int, conversation_data: dict
    ) -> bool:
        """Прямое сохранение диалога в БД."""
        try:
            # Создаем записи диалога
            user_conv = Conversation(
                user_id=user_id,
                message_text=conversation_data["user_message"],
                role="user",
                status=ConversationStatus.COMPLETED,
            )
            session.add(user_conv)

            ai_conv = Conversation(
                user_id=user_id,
                message_text=conversation_data["user_message"],
                response_text=conversation_data["ai_response"],
                role="assistant",
                status=ConversationStatus.COMPLETED,
                ai_model=conversation_data["ai_model"],
                tokens_used=conversation_data["tokens_used"],
                response_time_ms=int(conversation_data["response_time"] * 1000),
            )
            session.add(ai_conv)

            await session.commit()
            return True

        except Exception as e:
            logger.error(f"Database save error for user {user_id}: {e}")
            await session.rollback()
            return False
