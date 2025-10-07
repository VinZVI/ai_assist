"""
@file: message.py
@description: Обработчик текстовых сообщений для AI диалогов
              с поддержкой множественных провайдеров
@dependencies: aiogram, sqlalchemy, loguru, app.services.ai_manager
@created: 2025-09-12
@updated: 2025-09-20
"""

from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.types import Message
from aiogram.utils.markdown import bold, italic
from loguru import logger
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_config
from app.constants.errors import (
    AI_ALL_PROVIDERS_FAILED,
    AI_AUTH_ERROR,
    AI_CONNECTION_ERROR,
    AI_EMPTY_RESPONSE_ERROR,
    AI_INVALID_RESPONSE_ERROR,
    AI_PROVIDER_ERROR,
    AI_RATE_LIMIT_ERROR,
    AI_TIMEOUT_ERROR,
    CONVERSATION_HISTORY_ERROR,
    CONVERSATION_SAVE_ERROR,
    DB_CONNECTION_ERROR,
    DB_INTEGRITY_ERROR,
    DB_SQLALCHEMY_ERROR,
    USER_CREATION_ERROR,
    USER_NOT_FOUND_ERROR,
    USER_UPDATE_ERROR,
)
from app.constants.errors import (
    AI_QUOTA_ERROR as AI_QUOTA_ERROR_CONST,
)
from app.database import get_session
from app.lexicon.ai_prompts import create_system_message
from app.lexicon.message import (
    AI_ALL_PROVIDERS_DOWN,
    AI_GENERAL_ERROR,
    AI_QUOTA_ERROR,
    AI_UNEXPECTED_ERROR,
    DAILY_LIMIT_EXCEEDED,
    MESSAGE_TOO_LONG,
    PROCESSING_ERROR,
    USER_REGISTRATION_ERROR,
)
from app.log_lexicon.message import (
    MESSAGE_AI_GENERATING,
    MESSAGE_AI_RESPONSE,
    MESSAGE_AI_RESPONSE_GENERATED,
    MESSAGE_CONVERSATION_SAVE_ERROR,
    MESSAGE_CONVERSATION_SAVED,
    MESSAGE_ERROR,
    MESSAGE_PROCESSING,
    MESSAGE_RECEIVED,
    MESSAGE_SENT,
    MESSAGE_USER_LIMIT_EXCEEDED,
)
from app.models.conversation import Conversation, ConversationStatus
from app.models.user import User
from app.services.ai_manager import AIProviderError, get_ai_manager
from app.services.ai_providers.base import ConversationMessage
from app.services.conversation_service import (
    get_recent_conversation_history,
    save_conversation,
)
from app.services.user_service import get_or_update_user

# Создаем роутер для обработчиков сообщений
message_router = Router()


async def generate_ai_response(
    user: User,
    user_message: str,
) -> tuple[str, int, str, float]:
    """
    Генерация ответа от AI с поддержкой множественных провайдеров.

    Returns:
        tuple: (response_text, tokens_used, model_name, response_time)
    """
    try:
        ai_manager = get_ai_manager()
        start_time = datetime.now(UTC)

        # Получаем историю диалога
        async with get_session() as session:
            conversation_history = await get_recent_conversation_history(
                session,
                user.id,
                limit=6,  # Последние 3 обмена
            )

        # Формируем сообщения для AI
        messages = [create_system_message()]

        # Добавляем историю
        messages.extend(conversation_history)

        # Добавляем текущее сообщение пользователя
        messages.append(
            ConversationMessage(
                role="user",
                content=user_message,
            ),
        )

        # Генерируем ответ с автоматическим fallback
        response = await ai_manager.generate_response(
            messages=messages,
            temperature=0.8,  # Немного больше креативности для эмпатии
            max_tokens=1000,
        )

        response_time = (datetime.now(UTC) - start_time).total_seconds()

        logger.info(
            MESSAGE_AI_RESPONSE.format(
                provider=response.provider,
                chars=len(response.content),
                tokens=response.tokens_used,
                duration=f"{response.response_time:.2f}",
            )
        )

        return response.content, response.tokens_used, response.model, response_time

    except AIProviderError as e:
        error_msg = str(e)
        provider = getattr(e, "provider", "unknown")
        logger.error(AI_PROVIDER_ERROR.format(provider=provider, error=error_msg))

        # Проверяем на ошибки с балансом/квотой
        if any(
            keyword in error_msg.lower()
            for keyword in [
                "недостаточно средств",
                "quota",
                "billing",
                "payment",
                "402",
            ]
        ):
            return (
                AI_QUOTA_ERROR,
                0,
                "quota_error",
                0.0,
            )

        # Проверяем критические ошибки (все провайдеры недоступны)
        if "все ai провайдеры недоступны" in error_msg.lower():
            return (
                AI_ALL_PROVIDERS_DOWN,
                0,
                "all_providers_down",
                0.0,
            )

        # Возвращаем общий fallback ответ
        return (
            AI_GENERAL_ERROR,
            0,
            "fallback",
            0.0,
        )

    except Exception:
        logger.exception("💥 Неожиданная ошибка при генерации AI ответа")
        return (
            AI_UNEXPECTED_ERROR,
            0,
            "error",
            0.0,
        )


@message_router.message(F.text)
async def handle_text_message(message: Message) -> None:
    """Обработка входящих текстовых сообщений от пользователей."""
    try:
        logger.info(
            MESSAGE_RECEIVED.format(
                username=message.from_user.username or f"ID:{message.from_user.id}",
                chars=len(message.text[:50]),
            )
            + f"... ({message.text[:50]})"
        )

        # Проверяем наличие пользователя
        user = await get_or_update_user(message)
        if not user:
            await message.answer(USER_REGISTRATION_ERROR)
            return

        # Проверяем лимиты
        if not user.can_send_message():
            await message.answer(DAILY_LIMIT_EXCEEDED)
            logger.info(MESSAGE_USER_LIMIT_EXCEEDED.format(user_id=user.id))
            return

        # Проверяем длину сообщения
        if len(message.text) > 4000:
            await message.answer(MESSAGE_TOO_LONG)
            return

        # Отправляем статус "печатает"
        await message.bot.send_chat_action(
            chat_id=message.chat.id,
            action="typing",
        )

        # Генерируем ответ от AI
        logger.info(MESSAGE_AI_GENERATING)
        (
            ai_response,
            tokens_used,
            model_name,
            response_time,
        ) = await generate_ai_response(user, message.text)
        logger.info(
            MESSAGE_AI_RESPONSE_GENERATED.format(response=ai_response[:50] + "...")
        )

        # Сохраняем диалог
        async with get_session() as session:
            success = await save_conversation(
                session=session,
                user_id=user.id,
                user_message=message.text,
                ai_response=ai_response,
                ai_model=model_name,
                tokens_used=tokens_used,
                response_time=response_time,
            )

            if not success:
                logger.error(CONVERSATION_SAVE_ERROR.format(user_id=user.id))

        # Отправляем ответ пользователю
        response_text = f"{ai_response}"

        await message.answer(
            response_text,
            parse_mode="Markdown",
        )

        # Обновляем счетчик сообщений пользователя
        user.increment_message_count()
        # Сохраняем изменения в базе данных
        async with get_session() as session:
            session.add(user)
            await session.commit()
        logger.info(
            MESSAGE_SENT.format(
                username=message.from_user.username or f"ID:{message.from_user.id}",
                chars=len(response_text),
                tokens=tokens_used,
                duration=f"{response_time:.2f}",
            )
        )

    except Exception as e:
        logger.exception(
            MESSAGE_ERROR.format(
                user_id=getattr(message.from_user, "id", "unknown"), error=e
            )
        )
        await message.answer(PROCESSING_ERROR)
