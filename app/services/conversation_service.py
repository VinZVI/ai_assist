"""
@file: conversation_service.py
@description: Сервис для работы с диалогами пользователей
@dependencies: sqlalchemy, loguru, app.models.conversation
@created: 2025-10-07
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.lexicon.ai_prompts import create_system_message
from app.log_lexicon.message import (
    MESSAGE_CONVERSATION_SAVE_ERROR,
    MESSAGE_CONVERSATION_SAVED,
)
from app.models.conversation import Conversation, ConversationStatus
from app.services.ai_providers.base import ConversationMessage


async def get_recent_conversation_history(
    session: AsyncSession,
    user_id: int,
    limit: int = 10,
) -> list[ConversationMessage]:
    """Получение истории последних сообщений пользователя."""
    try:
        # Получаем последние завершенные сообщения
        stmt = (
            select(Conversation)
            .where(
                (Conversation.user_id == user_id)
                & (Conversation.status == ConversationStatus.COMPLETED),
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
        logger.info(MESSAGE_CONVERSATION_SAVED.format(user_id=user_id))
        return True

    except Exception as e:
        logger.exception(MESSAGE_CONVERSATION_SAVE_ERROR.format(error=e))
        await session.rollback()
        return False
