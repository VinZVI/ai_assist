"""
@file: message.py
@description: Обработчик текстовых сообщений для AI диалогов
              с поддержкой множественных провайдеров
@dependencies: aiogram, sqlalchemy, loguru, app.services.ai_manager
@created: 2025-09-12
@updated: 2025-09-20
"""

from datetime import UTC, datetime, timezone

from aiogram import F, Router
from aiogram.types import Message
from aiogram.utils.markdown import bold, italic
from loguru import logger
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_config
from app.database import get_session
from app.models.conversation import Conversation, ConversationStatus, save_conversation
from app.models.user import User, get_or_update_user
from app.services.ai_manager import AIProviderError, get_ai_manager
from app.services.ai_providers.base import ConversationMessage

# Создаем роутер для обработчиков сообщений
message_router = Router()


async def get_recent_conversation_history(
    session: AsyncSession,
    user_id: int,
    limit: int = 10,
) -> list[ConversationMessage]:
    """Получение истории последних сообщений пользователя."""
    try:
        from sqlalchemy import desc, select

        from app.models.conversation import ConversationStatus

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


def create_system_message() -> ConversationMessage:
    """Создание системного сообщения для AI."""
    return ConversationMessage(
        role="system",
        content=(
            "Ты - эмпатичный AI-помощник и компаньон. "
            "Твоя задача - предоставлять эмоциональную поддержку и понимание. "
            "Отвечай доброжелательно, поддерживающе и с пониманием. "
            "Задавай уточняющие вопросы, чтобы лучше понять чувства "
            "и потребности пользователя. "
            "Избегай давать медицинские или юридические советы. "
            "Если пользователь находится в кризисной ситуации, "
            "мягко предложи обратиться к специалисту."
        ),
    )


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
            f"🤖 AI ответ получен от {response.provider}: "
            f"{len(response.content)} символов, {response.tokens_used} токенов, "
            f"{response.response_time:.2f}с",
        )

        return response.content, response.tokens_used, response.model, response_time

    except AIProviderError as e:
        error_msg = str(e)
        provider = getattr(e, "provider", "unknown")
        logger.error(f"❌ Ошибка AI провайдера {provider}: {error_msg}")

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
                "💳 Извините, у нас временные трудности с AI сервисом.\n"
                "Мы уже работаем над решением этой проблемы.\n\n"
                "🕰️ Попробуйте еще раз через несколько минут.",
                0,
                "quota_error",
                0.0,
            )

        # Проверяем критические ошибки (все провайдеры недоступны)
        if "все ai провайдеры недоступны" in error_msg.lower():
            return (
                "😔 К сожалению, все наши AI сервисы временно недоступны.\n"
                "Мы работаем над устранением проблемы.\n\n"
                "🔄 Пожалуйста, попробуйте позже.",
                0,
                "all_providers_down",
                0.0,
            )

        # Возвращаем общий fallback ответ
        return (
            "Извините, у меня временные технические трудности. "
            "Я понимаю, что вам нужна поддержка. "
            "Попробуйте написать еще раз через несколько минут.",
            0,
            "fallback",
            0.0,
        )

    except Exception:
        logger.exception("💥 Неожиданная ошибка при генерации AI ответа")
        return (
            "Произошла неожиданная ошибка. Пожалуйста, попробуйте еще раз.",
            0,
            "error",
            0.0,
        )


@message_router.message(F.text & ~F.text.startswith("/"))
async def handle_text_message(message: Message) -> None:
    """
    Обработчик текстовых сообщений.

    Логика:
    1. Проверяем, что пользователь зарегистрирован
    2. Проверяем лимиты сообщений
    3. Генерируем ответ AI
    4. Сохраняем диалог
    5. Отправляем ответ пользователю
    """
    # Проверка наличия данных
    if not message.from_user or not message.text:
        logger.warning("⚠️ Получено сообщение без данных пользователя или текста")
        return

    user_id = message.from_user.id
    user_text = message.text

    logger.info(
        f"💬 Получено сообщение от пользователя {user_id}: {len(user_text)} символов",
    )

    # Проверяем длину сообщения
    if len(user_text.strip()) < 2:
        await message.answer(
            "⚠️ Пожалуйста, напишите более содержательное "
            "сообщение (минимум 2 символа).",
        )
        return

    if len(user_text) > 2000:  # Ограничиваем длину для эффективности
        await message.answer(
            "⚠️ Ваше сообщение слишком длинное. "
            "Пожалуйста, сократите его до 2000 символов.",
        )
        return

    # Получаем данные пользователя
    user = await get_or_update_user(message)
    if not user:
        await message.answer(
            "👋 Добро пожаловать! Пожалуйста, начните с команды "
            "/start для регистрации.",
        )
        return

    # Сбрасываем дневной счетчик если нужно
    user.reset_daily_count_if_needed()

    # Проверяем лимиты сообщений
    if not user.can_send_message():
        config = get_config()
        if config.user_limits:
            premium_price = config.user_limits.premium_price
            free_messages_limit = config.user_limits.free_messages_limit
        else:
            premium_price = 99
            free_messages_limit = 10

        await message.answer(
            f"🚫 **Превышен дневной лимит сообщений**\n\n"
            f"Бесплатный лимит: {free_messages_limit} сообщений в день\n"
            f"Использовано: {user.daily_message_count}\n\n"
            f"💎 **Премиум доступ** ({premium_price}₽):\n"
            f"• Безлимитные сообщения\n"
            f"• Приоритетная поддержка\n"
            f"• Расширенные возможности\n\n"
            f"Используйте /premium для оформления премиум доступа.",
            parse_mode="Markdown",
        )
        return

    # Показываем индикатор набора текста
    if message.bot:
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Генерируем ответ AI
        (
            ai_response,
            tokens_used,
            model_name,
            response_time,
        ) = await generate_ai_response(user, user_text)

        # Обновляем счетчик сообщений пользователя и сохраняем диалог
        async with get_session() as session:
            # Получаем пользователя заново для обновления
            user_db = await session.get(User, user.id)
            if user_db:
                user_db.daily_message_count += 1
                user_db.total_messages += 1
                await session.commit()

                # Сохраняем диалог
                await save_conversation(
                    session=session,
                    user_id=user.id,
                    user_message=user_text,
                    ai_response=ai_response,
                    ai_model=model_name,
                    tokens_used=tokens_used,
                    response_time=response_time,
                )

        # Отправляем ответ пользователю
        await message.answer(
            text=ai_response,
            parse_mode="Markdown",
        )

        logger.info(
            f"✅ Ответ отправлен пользователю {user_id}: "
            f"{len(ai_response)} символов, {tokens_used} токенов, "
            f"{response_time:.2f}с",
        )

    except Exception as e:
        logger.exception(f"💥 Критическая ошибка при обработке сообщения: {e}")

        await message.answer(
            "😔 Произошла ошибка при обработке вашего сообщения. "
            "Пожалуйста, попробуйте еще раз через несколько секунд.",
        )


# Экспорт роутера
__all__ = ["message_router"]
