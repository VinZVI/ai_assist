"""
@file: handlers/premium.py
@description: Обработчик команды /premium с информацией о премиум-доступе
@dependencies: aiogram, loguru, sqlalchemy
@created: 2025-10-07
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from app.database import get_session
from app.lexicon.gettext import get_log_text, get_text
from app.models import User

# Создаем роутер для обработчиков команды premium
premium_router = Router(name="premium")


@premium_router.message(Command("premium"))
async def handle_premium_command(message: Message) -> None:
    """
    Обработчик команды /premium.

    Отправляет пользователю информацию о премиум-доступе.

    Args:
        message: Объект сообщения от пользователя
    """
    try:
        # Проверяем, что у сообщения есть пользователь
        if not message.from_user:
            logger.error("Message without user information")
            return

        # Логируем попытку получения информации о премиуме
        logger.info(
            get_log_text("premium.premium_command_processed").format(
                user_id=message.from_user.id
            )
        )

        # Получаем пользователя из базы данных
        async with get_session() as session:
            from sqlalchemy import select

            stmt = select(User).where(User.telegram_id == message.from_user.id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

        # Определяем язык пользователя
        lang_code = user.language_code if user and user.language_code else "ru"

        # Формируем сообщение с информацией о премиуме
        premium_text = f"<b>{get_text('premium.title', lang_code)}</b>\n\n"
        premium_text += get_text("callbacks.placeholder_message", lang_code)

        # Отправляем сообщение
        await message.answer(premium_text, parse_mode="HTML")

        logger.info(
            get_log_text("premium.premium_command_processed").format(
                user_id=message.from_user.id
            )
        )

    except Exception as e:
        if message.from_user:
            logger.error(
                get_log_text("premium.premium_command_error").format(
                    user_id=message.from_user.id, error=e
                )
            )
            try:
                await message.answer(get_text("errors.general_error"))
            except Exception as send_error:
                logger.error(
                    get_log_text("premium.premium_error_sending_message").format(
                        error=send_error,
                    )
                )
