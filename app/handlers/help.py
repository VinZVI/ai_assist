"""
@file: handlers/help.py
@description: Обработчик команды /help с информацией о командах бота
@dependencies: aiogram, loguru
@created: 2025-10-07
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from app.database import get_session
from app.lexicon.gettext import get_log_text, get_text
from app.models import User

# Создаем роутер для обработчиков команды help
help_router = Router(name="help")


@help_router.message(Command("help"))
async def handle_help_command(message: Message) -> None:
    """
    Обработчик команды /help.

    Отправляет пользователю информацию о доступных командах бота.

    Args:
        message: Объект сообщения от пользователя
    """
    try:
        # Проверяем, что у сообщения есть пользователь
        if not message.from_user:
            logger.error("Message without user information")
            return

        # Логируем попытку получения справки
        logger.info(
            get_log_text("help.help_command_processed").format(
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

        # Формируем сообщение со справкой
        help_text = f"<b>{get_text('help.title', lang_code)}</b>\n\n"

        # Добавляем информацию о командах
        help_commands = get_text("help.commands", lang_code)
        for command, description in help_commands:
            help_text += f"{command} - {description}\n"

        # Отправляем сообщение
        await message.answer(help_text, parse_mode="HTML")

        logger.info(
            get_log_text("help.help_command_processed").format(
                user_id=message.from_user.id
            )
        )

    except Exception as e:
        if message.from_user:
            logger.error(
                get_log_text("help.help_command_error").format(
                    user_id=message.from_user.id, error=e
                )
            )
            try:
                await message.answer(get_text("errors.general_error"))
            except Exception as send_error:
                logger.error(
                    get_log_text("help.help_error_sending_message").format(
                        error=send_error,
                    )
                )
