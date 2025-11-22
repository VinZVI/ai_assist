"""
@file: handlers/limits.py
@description: Обработчик команды /limits с информацией о лимитах пользователя
@dependencies: aiogram, loguru, sqlalchemy
@created: 2025-10-07
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from app.lexicon.gettext import get_log_text, get_text
from app.models import User

# Создаем роутер для обработчиков команды limits
limits_router = Router(name="limits")


@limits_router.message(Command("limits"))
async def handle_limits_command(message: Message, user: User) -> None:
    """
    Обработчик команды /limits.

    Отправляет пользователю информацию о его лимитах.

    Args:
        message: Объект сообщения от пользователя
        user: Объект пользователя из middleware
    """
    try:
        # Логируем попытку получения лимитов
        logger.info(
            get_log_text("limits.limits_command_processed").format(user_id=user.id)
        )

        # Определяем язык пользователя
        lang_code = user.language_code if user.language_code else "ru"

        # Формируем сообщение с информацией о лимитах
        limits_text = f"<b>{get_text('limits.title', lang_code)}</b>\n\n"
        limits_text += get_text("callbacks.placeholder_message", lang_code)

        # Отправляем сообщение
        await message.answer(limits_text, parse_mode="HTML")

        logger.info(
            get_log_text("limits.limits_command_processed").format(user_id=user.id)
        )

    except Exception as e:
        logger.error(
            get_log_text("limits.limits_command_error").format(user_id=user.id, error=e)
        )
        try:
            await message.answer(get_text("errors.general_error"))
        except Exception as send_error:
            logger.error(
                get_log_text("limits.limits_error_sending_message").format(
                    error=send_error,
                )
            )
