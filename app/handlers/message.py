from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.types import Message
from loguru import logger
from sqlalchemy import select

from app.config import get_config
from app.constants.errors import (
    AI_PROVIDER_ERROR,
)
from app.constants.errors import (
    AI_QUOTA_ERROR as AI_QUOTA_ERROR_CONST,
)
from app.database import get_session
from app.lexicon.ai_prompts import create_system_message
from app.lexicon.gettext import get_text
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
                get_text("errors.ai_quota_error", "ru", provider=provider),
                0,
                "quota_error",
                0.0,
            )

        # Проверяем критические ошибки (все провайдеры недоступны)
        if "все ai провайдеры недоступны" in error_msg.lower():
            return (
                get_text("errors.ai_all_providers_down"),
                0,
                "all_providers_down",
                0.0,
            )

        # Возвращаем общий fallback ответ
        return (
            get_text("errors.ai_general_error"),
            0,
            "fallback",
            0.0,
        )

    except Exception:
        logger.exception(
            MESSAGE_ERROR.format(
                user_id="unknown", error="Неожиданная ошибка при генерации AI ответа"
            )
        )
        return (
            get_text("errors.ai_unexpected_error"),
            0,
            "error",
            0.0,
        )


@message_router.message(F.text)
async def handle_text_message(message: Message) -> None:
    """Обработка входящих текстовых сообщений от пользователей."""
    user = None  # Initialize user variable
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
            await message.answer(get_text("errors.user_registration_error"))
            return

        # Проверяем лимиты
        if not user.can_send_message():
            await message.answer(get_text("errors.daily_limit_exceeded"))
            logger.info(MESSAGE_USER_LIMIT_EXCEEDED.format(user_id=user.id))
            return

        # Проверяем длину сообщения
        if len(message.text) > 4000:
            await message.answer(get_text("errors.message_too_long"))
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

            if success:
                logger.info(
                    MESSAGE_CONVERSATION_SAVED.format(
                        user_id=user.id,
                        chars=len(ai_response),
                        tokens=tokens_used,
                        model=model_name,
                    )
                )
            else:
                logger.error(
                    MESSAGE_CONVERSATION_SAVE_ERROR.format(
                        user_id=user.id,
                        error="Failed to save conversation",
                    )
                )

        # Отправляем ответ пользователю с Markdown форматированием
        await message.answer(ai_response, parse_mode="Markdown")

        # Логируем успешную отправку
        logger.info(
            MESSAGE_SENT.format(
                username=message.from_user.username or f"ID:{message.from_user.id}",
                chars=len(ai_response),
                tokens=tokens_used,
                duration=f"{response_time:.2f}",
            )
        )

        # Обновляем статистику пользователя
        user.increment_message_count()
        logger.info(MESSAGE_PROCESSING.format(user_id=user.id))

    except Exception as e:
        user_id = (
            user.id
            if user
            else (message.from_user.id if message.from_user else "unknown")
        )
        logger.error(MESSAGE_ERROR.format(user_id=user_id, error=e))
        # Отправляем пользователю сообщение об ошибке
        await message.answer(get_text("errors.general_error"))
