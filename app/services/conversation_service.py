"""
@file: conversation_service.py
@description: Сервис для работы с диалогами пользователей
@dependencies: sqlalchemy, loguru, app.models.conversation
@created: 2025-10-07
@updated: 2025-10-15
"""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.lexicon.ai_prompts import create_system_message
from app.lexicon.gettext import get_log_text
from app.models.conversation import Conversation, ConversationStatus
from app.services.ai_providers.base import ConversationMessage


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
                messages.append(
                    ConversationMessage(
                        role="user",
                        content=conv.message_text,
                        timestamp=conv.created_at,
                    ),
                )

            # Добавляем ответ ассистента
            if conv.response_text:
                messages.append(
                    ConversationMessage(
                        role="assistant",
                        content=conv.response_text,
                        timestamp=conv.processed_at or conv.created_at,
                    ),
                )

        return messages[-limit:] if len(messages) > limit else messages

    except Exception as e:
        logger.error(f"❌ Ошибка при получении истории: {e}")
        return []


async def get_conversation_context(
    session: AsyncSession,
    user_id: int,
    limit: int = 6,
    max_age_hours: int = 12,
) -> dict[str, any]:
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
        history = await get_recent_conversation_history(session, user_id, limit, max_age_hours)
        
        # Анализируем историю для извлечения контекста
        context = {
            "history": history,
            "message_count": len([m for m in history if m.role == "user"]),
            "last_interaction": history[-1].timestamp if history else None,
            "topics": [],
            "emotional_tone": "neutral",
        }
        
        # Извлекаем темы из истории
        all_texts = " ".join([msg.content for msg in history])
        lower_texts = all_texts.lower()
        
        # Определяем темы
        topics = []
        if any(word in lower_texts for word in ["работа", "работу", "работы", "job", "work"]):
            topics.append("work")
        if any(word in lower_texts for word in ["семья", "семье", "семью", "family"]):
            topics.append("family")
        if any(word in lower_texts for word in ["друзья", "друг", "подруга", "friends", "friend"]):
            topics.append("social")
        if any(word in lower_texts for word in ["здоровье", "здоров", "болезнь", "health", "ill", "sick"]):
            topics.append("health")
        if any(word in lower_texts for word in ["деньги", "денег", "заработок", "money", "finance"]):
            topics.append("finance")
        if any(word in lower_texts for word in ["любовь", "люблю", "романтика", "love", "romance"]):
            topics.append("romance")
            
        context["topics"] = topics
        
        # Определяем эмоциональный тон (простой анализ)
        positive_words = ["хорошо", "отлично", "прекрасно", "рад", "счастлив", "fantastic", "great", "happy"]
        negative_words = ["плохо", "ужасно", "грустно", "зло", "ненавижу", "sad", "terrible", "awful"]
        
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


async def save_conversation(
    session: AsyncSession,
    user_id: int,
    user_message: str,
    ai_response: str,
    ai_model: str,
    tokens_used: int,
    response_time: float,
) -> bool:
    """
    Сохранение диалога в базе данных.

    Args:
        session: Сессия базы данных
        user_id: ID пользователя
        user_message: Сообщение пользователя
        ai_response: Ответ AI
        ai_model: Модель AI
        tokens_used: Количество использованных токенов
        response_time: Время ответа в секундах

    Returns:
        bool: True если успешно сохранено, False в случае ошибки
    """
    try:
        # Создаем запись сообщения пользователя
        user_conv = Conversation(
            user_id=user_id,
            message_text=user_message,
            role="user",
            status=ConversationStatus.COMPLETED,
        )
        session.add(user_conv)

        # Создаем запись ответа AI
        ai_conv = Conversation(
            user_id=user_id,
            message_text=user_message,
            response_text=ai_response,
            role="assistant",
            status=ConversationStatus.COMPLETED,
            ai_model=ai_model,
            tokens_used=tokens_used,
            response_time_ms=int(response_time * 1000),
        )
        session.add(ai_conv)

        await session.commit()
        logger.info(
            get_log_text("message.message_conversation_saved").format(user_id=user_id)
        )
        return True

    except Exception:
        logger.exception(
            get_log_text("message.message_conversation_save_error").format(
                user_id=user_id
            )
        )
        await session.rollback()
        return False


async def clear_user_conversation_history(
    session: AsyncSession,
    user_id: int,
) -> bool:
    """
    Очистка истории диалогов пользователя.

    Args:
        session: Сессия базы данных
        user_id: ID пользователя

    Returns:
        bool: True если успешно очищено, False в случае ошибки
    """
    try:
        # Удаляем все сообщения пользователя
        stmt = select(Conversation).where(Conversation.user_id == user_id)
        result = await session.execute(stmt)
        conversations = result.scalars().all()
        
        for conv in conversations:
            await session.delete(conv)
            
        await session.commit()
        logger.info(
            get_log_text("message.message_conversation_history_cleared").format(user_id=user_id)
        )
        return True

    except Exception:
        logger.exception(
            get_log_text("message.message_conversation_history_clear_error").format(
                user_id=user_id
            )
        )
        await session.rollback()
        return False
