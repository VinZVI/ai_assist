"""Модуль для работы с историей диалогов пользователей."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, List

from loguru import logger
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, ConversationStatus
from app.services.ai_providers.base import (
    ConversationMessage,
    UserAIConversationContext,
)
from app.utils.validators import InputValidator

# if TYPE_CHECKING:
#     from app.services.conversation.conversation_context import UserAIConversationContext


async def get_recent_conversation_history(
    session: AsyncSession,
    user_id: int,
    limit: int = 10,
    max_age_hours: int = 24,
) -> list[ConversationMessage]:
    """Получение истории последних сообщений пользователя."""
    try:
        # Вычисляем время cutoff для ограничения по возрасту
        cutoff_time = datetime.now(UTC) - timedelta(hours=max_age_hours)

        # Получаем последние завершенные сообщения
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

        # Преобразуем в ConversationMessage
        messages = []
        for conv in reversed(conversations):  # Обращаем порядок для хронологии
            # Добавляем сообщение пользователя
            if conv.message_text:
                # Санитизация текста пользователя
                sanitized_message = InputValidator.sanitize_text(conv.message_text)
                messages.append(
                    ConversationMessage(
                        role="user",
                        content=sanitized_message,
                        timestamp=conv.created_at,
                    ),
                )

            # Добавляем ответ ассистента
            if conv.response_text:
                # Санитизация текста ответа
                sanitized_response = InputValidator.sanitize_text(conv.response_text)
                messages.append(
                    ConversationMessage(
                        role="assistant",
                        content=sanitized_response,
                        timestamp=conv.processed_at or conv.created_at,
                    ),
                )

        return messages[-limit:] if len(messages) > limit else messages

    except Exception as e:
        logger.error(f"❌ Ошибка при получении истории: {e}")
        return []


async def get_conversation_context_from_db(
    session: AsyncSession,
    user_id: int,
    limit: int = 6,
    max_age_hours: int = 12,
) -> dict[str, Any]:
    """
    Получение контекста диалога пользователя для более точной генерации ответов.

    Args:
        session: Сессия базы данных
        user_id: ID пользователя
        limit: Максимальное количество сообщений в истории
        max_age_hours: Максимальный возраст сообщений в часах

    Returns:
        dict: Контекст диалога с метаинформацией
    """
    try:
        # Получаем историю разговоров
        history = await get_recent_conversation_history(
            session, user_id, limit, max_age_hours
        )

        # Преобразуем ConversationMessage объекты в словари для сериализации
        serialized_history = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
            }
            for msg in history
        ]

        # Анализируем историю для извлечения контекста
        context = {
            "history": serialized_history,
            "message_count": len([m for m in history if m.role == "user"]),
            "last_interaction": history[-1].timestamp.isoformat()
            if history and history[-1].timestamp
            else None,
            "topics": [],
            "emotional_tone": "neutral",
        }

        # Извлекаем темы из истории
        all_texts = " ".join([msg.content for msg in history])
        lower_texts = all_texts.lower()

        # Определяем темы
        topics = []
        topic_keywords = {
            "work": ["работа", "работу", "работы", "job", "work"],
            "family": ["семья", "семье", "семью", "family"],
            "social": ["друзья", "друг", "подруга", "friends", "friend"],
            "health": ["здоровье", "здоров", "болезнь", "health", "ill", "sick"],
            "finance": ["деньги", "денег", "заработок", "money", "finance"],
            "romance": ["любовь", "люблю", "романтика", "love", "romance"],
        }

        for topic, keywords in topic_keywords.items():
            if any(word in lower_texts for word in keywords):
                topics.append(topic)

        context["topics"] = topics

        # Определяем эмоциональный тон (простой анализ)
        positive_words = [
            "хорошо",
            "отлично",
            "прекрасно",
            "рад",
            "счастлив",
            "fantastic",
            "great",
            "happy",
        ]
        negative_words = [
            "плохо",
            "ужасно",
            "грустно",
            "зло",
            "ненавижу",
            "sad",
            "terrible",
            "awful",
        ]

        pos_count = sum(lower_texts.count(word) for word in positive_words)
        neg_count = sum(lower_texts.count(word) for word in negative_words)

        if pos_count > neg_count:
            context["emotional_tone"] = "positive"
        elif neg_count > pos_count:
            context["emotional_tone"] = "negative"
        else:
            context["emotional_tone"] = "neutral"

        return context

    except Exception as e:
        logger.error(f"❌ Ошибка при получении контекста диалога: {e}")
        return {
            "history": [],
            "message_count": 0,
            "last_interaction": None,
            "topics": [],
            "emotional_tone": "neutral",
        }
