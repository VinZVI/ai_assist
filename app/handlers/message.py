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
from app.models.conversation import Conversation, ConversationStatus
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
        logger.info(f"💾 Диалог сохранен для пользователя {user_id}")
        return True

    except Exception as e:
        logger.exception(f"💥 Ошибка при сохранении диалога: {e}")
        await session.rollback()
        return False


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


@message_router.message(F.text)
async def handle_text_message(message: Message) -> None:
    """Обработка входящих текстовых сообщений от пользователей."""
    try:
        logger.info(
            f"📥 Получено сообщение от @{message.from_user.username}: {message.text[:50]}..."
        )

        # Проверяем наличие пользователя
        user = await get_or_update_user(message)
        if not user:
            await message.answer(
                "❌ Извините, возникла проблема с регистрацией. Попробуйте позже.",
            )
            return

        # Проверяем лимиты
        if not user.can_send_message():
            await message.answer(
                "📝 Вы исчерпали дневной лимит сообщений.\n"
                "Завтра вы снова сможете общаться со мной!",
            )
            return

        # Проверяем длину сообщения
        if len(message.text) > 4000:
            await message.answer(
                "📝 Ваше сообщение слишком длинное (более 4000 символов).\n"
                "Пожалуйста, сократите его.",
            )
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
                logger.error(
                    f"❌ Не удалось сохранить диалог для пользователя {user.id}"
                )

        # Отправляем ответ пользователю
        response_text = (
            f"{ai_response}\n\n"
            f"{italic('⏱️ Время ответа:')} {response_time:.1f}с | "
            f"{bold('🤖 Модель:')} {model_name}"
        )

        await message.answer(
            response_text,
            parse_mode="Markdown",
        )

        # Обновляем счетчик сообщений пользователя
        user.increment_message_count()
        logger.info(
            f"📤 Ответ отправлен @{message.from_user.username} "
            f"(токены: {tokens_used}, модель: {model_name})",
        )

    except Exception:
        logger.exception("💥 Ошибка при обработке текстового сообщения")
        await message.answer(
            "😔 Извините, произошла неожиданная ошибка. Попробуйте позже.",
        )
