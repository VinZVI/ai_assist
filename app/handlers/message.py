"""
@file: handlers/message.py
@description: Обработчик входящих сообщений от пользователей
@dependencies: aiogram, sqlalchemy, loguru
@created: 2025-09-07
@updated: 2025-10-07
"""

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
from app.lexicon.gettext import get_log_text, get_text
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

        # Формируем сообщения для AI с учетом языка пользователя
        user_language = user.language_code or "ru"
        messages = [create_system_message(user_language)]

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
            get_log_text("message.message_ai_response").format(
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

        # Определяем язык пользователя для сообщений об ошибках
        user_lang = user.language_code or "ru"

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
                get_text("errors.ai_quota_error", user_lang, provider=provider),
                0,
                "quota_error",
                0.0,
            )

        # Проверяем критические ошибки (все провайдеры недоступны)
        if "все ai провайдеры недоступны" in error_msg.lower():
            return (
                get_text("errors.ai_all_providers_down", user_lang),
                0,
                "all_providers_down",
                0.0,
            )

        # Возвращаем общий fallback ответ
        return (
            get_text("errors.ai_general_error", user_lang),
            0,
            "fallback",
            0.0,
        )

    except Exception:
        logger.exception(
            get_log_text("message.message_error").format(
                user_id="unknown", error="Неожиданная ошибка при генерации AI ответа"
            )
        )
        # Определяем язык пользователя для сообщений об ошибках
        user_lang = user.language_code or "ru"
        return (
            get_text("errors.ai_unexpected_error", user_lang),
            0,
            "error",
            0.0,
        )


@message_router.message(F.text)
async def handle_text_message(message: Message) -> None:
    """Обработка входящих текстовых сообщений от пользователей."""
    user = None  # Initialize user variable
    try:
        # Определяем язык пользователя для логирования
        user_lang = "ru"  # Default language for logging
        if message.from_user:
            logger.info(
                get_log_text("message.message_received").format(
                    username=message.from_user.username or f"ID:{message.from_user.id}",
                    chars=len(message.text[:50]),
                )
                + f"... ({message.text[:50]})"
            )

        # Проверяем наличие пользователя
        user = await get_or_update_user(message)
        if not user:
            # Используем язык по умолчанию для сообщения об ошибке если пользователь не найден
            await message.answer(get_text("errors.user_registration_error", "ru"))
            return

        # Устанавливаем язык пользователя
        user_lang = user.language_code or "ru"

        # Проверяем лимиты
        if not user.can_send_message():
            await message.answer(get_text("errors.daily_limit_exceeded", user_lang))
            logger.info(
                get_log_text("message.message_user_limit_exceeded").format(
                    user_id=user.id
                )
            )
            return

        # Проверяем длину сообщения
        if len(message.text) > 4000:
            await message.answer(get_text("errors.message_too_long", user_lang))
            return

        # Отправляем статус "печатает"
        await message.bot.send_chat_action(
            chat_id=message.chat.id,
            action="typing",
        )

        # Генерируем ответ от AI
        (
            ai_response,
            tokens_used,
            model_name,
            response_time,
        ) = await generate_ai_response(user, message.text)

        # Санитизируем ответ AI для безопасной отправки в Telegram
        sanitized_response = sanitize_telegram_message(ai_response)

        # Отправляем ответ пользователю без parse_mode чтобы избежать ошибок парсинга
        await message.answer(sanitized_response)

        # Сохраняем диалог в базе данных если это разрешено в конфигурации
        config = get_config()
        if config.conversation.enable_saving:
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
                        get_log_text("message.message_conversation_saved").format(
                            user_id=user.id
                        )
                    )
                else:
                    logger.error(
                        get_log_text("message.message_conversation_save_error").format(
                            user_id=user.id
                        )
                    )

        # Обновляем счетчик сообщений пользователя если это разрешено в конфигурации
        if config.conversation.enable_saving:
            async with get_session() as session:
                from sqlalchemy import update

                stmt = (
                    update(User)
                    .where(User.id == user.id)
                    .values(
                        daily_message_count=User.daily_message_count + 1,
                        last_message_date=datetime.now(UTC).date(),
                    )
                )
                await session.execute(stmt)
                await session.commit()

        # Логируем обработку сообщения независимо от того, сохраняется ли диалог
        logger.info(
            get_log_text("message.message_processed").format(
                user_id=user.id,
                chars=len(ai_response),
                tokens=tokens_used,
                model=model_name,
                duration=f"{response_time:.2f}",
            )
        )

    except Exception as e:
        logger.exception(
            get_log_text("message.message_error").format(
                user_id=user.id if user else "unknown", error=str(e)
            )
        )

        # Определяем язык пользователя для сообщения об ошибке
        error_lang = user.language_code if user and user.language_code else "ru"

        # Отправляем пользователю сообщение об ошибке
        try:
            await message.answer(get_text("errors.general_error", error_lang))
        except Exception:
            # Если не удалось отправить сообщение на языке пользователя, отправляем на русском
            await message.answer(get_text("errors.general_error", "ru"))


def sanitize_telegram_message(text: str) -> str:
    """
    Санитизирует текст для безопасной отправки в Telegram.

    Args:
        text: Текст для санитизации

    Returns:
        str: Санитизированный текст
    """
    # Удаляем или заменяем специальные теги, которые могут вызвать ошибки парсинга
    # Удаляем специальные маркеры начала/конца предложения
    text = text.replace("｜begin▁of▁sentence｜", "")
    text = text.replace("｜end▁of▁sentence｜", "")
    
    # Удаляем другие потенциально проблемные специальные символы
    # Заменяем неразрывные пробелы на обычные пробелы
    text = text.replace("\u00a0", " ")  # Неразрывный пробел
    text = text.replace("\u2007", " ")  # Неразрывный пробел в числовой форме
    text = text.replace("\u202f", " ")  # Узкий неразрывный пробел
    
    # Дополнительно удаляем другие специальные символы, которые могут вызвать проблемы
    text = text.replace("｜", "|")  # Заменяем вертикальные линии
    
    # Удаляем другие специальные символы Unicode, которые могут вызвать проблемы
    import re
    # Удаляем control characters кроме \n, \r, \t
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # Ограничиваем длину сообщения до 4096 символов (лимит Telegram)
    if len(text) > 4096:
        text = text[:4093] + "..."

    return text
