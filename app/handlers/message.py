"""
@file: handlers/message.py
@description: Обработчик входящих сообщений от пользователей
@dependencies: aiogram, sqlalchemy, loguru
@created: 2025-09-07
@updated: 2025-10-15
"""

from collections.abc import Awaitable, Callable
from contextlib import suppress as contextlib_suppress
from datetime import UTC, datetime
from typing import Optional

from aiogram import F, Router
from aiogram.types import Message, SuccessfulPayment
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
from app.lexicon.ai_prompts import (
    create_crisis_intervention_prompt,
    create_mature_content_prompt,
    create_system_message,
)
from app.lexicon.gettext import get_log_text, get_text
from app.models.conversation import Conversation, ConversationStatus
from app.models.user import User
from app.services.ai_manager import AIProviderError, get_ai_manager
from app.services.ai_providers.base import ConversationMessage
from app.services.conversation_service import (
    get_conversation_context,
    save_conversation,
)

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

        # Определяем параметры контекста в зависимости от статуса премиум
        context_limit = 12 if user.is_premium_active() else 6
        context_max_age = 24 if user.is_premium_active() else 12

        # Пытаемся получить контекст из кеша первым делом
        from app.services.cache_service import cache_service

        # Use consistent cache key generation
        conversation_context = await cache_service.get_conversation_context(
            user.id, context_limit, context_max_age
        )

        if not conversation_context:
            # Если нет в кеше, загружаем из БД
            async with get_session() as session:
                from app.services.conversation_service import get_conversation_context

                conversation_context = await get_conversation_context(
                    session,
                    user.id,
                    limit=context_limit,
                    max_age_hours=context_max_age,
                )
            # Кешируем контекст на более длительное время (30 минут для лучшей производительности)
            await cache_service.set_conversation_context(
                user.id, conversation_context, ttl_seconds=1800
            )

        # Формируем сообщения для AI с учетом языка пользователя
        user_language = user.language_code or "ru"
        messages = [create_system_message(user_language)]

        # Добавляем контекст диалога
        if conversation_context["history"]:
            messages.extend(conversation_context["history"])

        # Добавляем текущее сообщение пользователя
        messages.append(
            ConversationMessage(
                role="user",
                content=user_message,
            ),
        )

        # Проверяем, нужно ли активировать специальные режимы
        lower_message = user_message.lower()

        # Проверка на кризисные ситуации
        crisis_keywords = [
            "самоубийство",
            "убить себя",
            "не могу жить",
            "смерть",
            "suicide",
            "kill myself",
            "can't live",
            "death",
        ]
        if any(keyword in lower_message for keyword in crisis_keywords):
            # Добавляем специальный промпт для кризисных ситуаций
            crisis_prompt = create_crisis_intervention_prompt(user_language)
            messages.insert(
                1, ConversationMessage(role="system", content=crisis_prompt)
            )

        # Проверка на темы для взрослых
        mature_keywords = ["секс", "интим", "эротика", "sex", "intimate", "erotic"]
        if any(keyword in lower_message for keyword in mature_keywords):
            # Добавляем специальный промпт для тем для взрослых
            mature_prompt = create_mature_content_prompt(user_language)
            messages.insert(
                1, ConversationMessage(role="system", content=mature_prompt)
            )

        # Устанавливаем параметры генерации в зависимости от статуса премиум
        temperature = 0.7 if user.is_premium_active() else 0.8
        max_tokens = 1500 if user.is_premium_active() else 1000

        # Генерируем ответ с автоматическим fallback
        response = await ai_manager.generate_response(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
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


@message_router.message(F.text & ~F.text.startswith("/"))
async def handle_text_message(
    message: Message,
    user: User,
    user_lang: str = "ru",
    save_conversation_func: Callable[..., Awaitable[None]] | None = None,
) -> None:
    """Обработка входящих текстовых сообщений от пользователей."""
    # Проверяем, что у сообщения есть текст
    if not message.text:
        return

    try:
        # Проверяем длину сообщения
        if len(message.text) > 4000:
            await message.answer(get_text("errors.message_too_long", user_lang))
            return

        # Проверяем лимиты пользователя
        if not user.can_send_message(100 if user.is_premium_active() else 10):
            await message.answer(get_text("errors.daily_limit_exceeded", user_lang))
            return

        # Отправляем статус "печатает"
        if message.bot:
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

        # Сохраняем диалог через middleware функцию если доступна
        if save_conversation_func:
            await save_conversation_func(
                user_id=user.id,
                user_message=message.text,
                ai_response=ai_response,
                ai_model=model_name,
                tokens_used=tokens_used,
                response_time=response_time,
            )

        # Увеличиваем счетчик сообщений пользователя
        user.increment_message_count()

        # Логируем обработку сообщения
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
            get_log_text("message.message_error").format(user_id=user.id, error=str(e))
        )

        # Отправляем пользователю сообщение об ошибке
        try:
            await message.answer(get_text("errors.general_error", user_lang))
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

    # Удаляем потенциально опасные символы, которые могут вызвать ошибки парсинга
    # Удаляем непечатаемые символы и специальные Unicode символы
    import re

    # Удаляем control characters кроме \n, \r, \t
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

    # Удаляем символы, которые могут вызвать ошибки парсинга в Telegram
    # Удаляем символы < и >, которые могут быть интерпретированы как HTML/XML теги
    text = text.replace("<", "&lt;").replace(">", "&gt;")

    # Удаляем символы &, которые могут быть интерпретированы как HTML entities
    # Но оставляем существующие HTML entities
    text = re.sub(r"&(?![a-zA-Z]+;|#\d+;|#x[a-fA-F0-9]+;)", "&amp;", text)

    # Удаляем одиночные кавычки, которые могут вызвать проблемы
    text = text.replace("`", "'")

    # Удаляем звездочки, которые могут быть интерпретированы как Markdown
    text = text.replace("*", "&#42;")

    # Удаляем символы подчеркивания, которые могут быть интерпретированы как Markdown
    text = text.replace("_", "&#95;")

    # Ограничиваем длину сообщения до 4096 символов (лимит Telegram)
    if len(text) > 4096:
        text = text[:4093] + "..."

    return text


@message_router.message(F.successful_payment)
async def handle_successful_payment(
    message: Message, successful_payment: SuccessfulPayment, user: User
) -> None:
    """Обработка успешного платежа Telegram Stars."""
    try:
        if not message.from_user:
            return

        # Process payment
        from app.config import get_config

        config = get_config()

        from aiogram import Bot

        from app.services.payment_service import TelegramStarsPaymentService

        bot = Bot(token=config.telegram.bot_token)
        payment_service = TelegramStarsPaymentService(bot)

        success = await payment_service.handle_successful_payment(
            successful_payment, message.from_user.id
        )

        # Use the user object from middleware context instead of querying database
        user_lang = user.language_code if user and user.language_code else "ru"

        if success:
            # Send confirmation message
            await message.answer(get_text("premium.payment_success", user_lang))
        else:
            # Handle error
            await message.answer(
                get_text("errors.payment_processing_failed", user_lang)
            )

    except Exception as e:
        from loguru import logger

        logger.error(f"Error handling successful payment: {e}")
        # Try to send error message in default language
        with contextlib_suppress(Exception):
            await message.answer(get_text("errors.general_error", "ru"))


# Экспорт роутера
__all__ = ["message_router"]
