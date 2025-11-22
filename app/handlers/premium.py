"""
@file: handlers/premium.py
@description: Обработчик команды /premium с информацией о премиум-доступе
@dependencies: aiogram, loguru, sqlalchemy
@created: 2025-10-07
@updated: 2025-10-15
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from app.config import get_config
from app.lexicon.gettext import get_log_text, get_text
from app.models import User

# Создаем роутер для обработчиков команды premium
premium_router = Router(name="premium")


@premium_router.message(Command("premium"))
async def handle_premium_command(message: Message, user: User) -> None:
    """
    Обработчик команды /premium.

    Отправляет пользователю информацию о премиум-доступе.

    Args:
        message: Объект сообщения от пользователя
        user: Объект пользователя из middleware
    """
    try:
        # Логируем попытку получения информации о премиуме
        logger.info(
            get_log_text("premium.premium_command_processed").format(user_id=user.id)
        )

        # Определяем язык пользователя
        lang_code = user.language_code if user.language_code else "ru"

        # Получаем конфигурацию
        config = get_config()

        # Формируем сообщение с информацией о премиуме
        premium_text = f"<b>{get_text('premium.title', lang_code)}</b>\n\n"
        premium_text += f"{get_text('premium.description', lang_code)}\n\n"
        premium_text += f"{get_text('premium.price', lang_code).format(price=config.user_limits.premium_price)}\n"
        premium_text += f"{get_text('premium.duration', lang_code).format(days=config.user_limits.premium_duration_days)}\n\n"

        # Добавляем преимущества премиум подписки
        premium_text += "<b>🌟 Преимущества премиум подписки:</b>\n"
        for benefit in get_text("premium.benefits", lang_code):
            premium_text += f"• {benefit}\n"

        # Добавляем специальные преимущества для эмоциональной поддержки
        premium_text += (
            "\n<b>💖 Специальные преимущества эмоциональной поддержки:</b>\n"
        )
        premium_text += "• Приоритетная обработка запросов\n"
        premium_text += "• Расширенные лимиты сообщений (до 100 в день)\n"
        premium_text += (
            "• Персонализированные ответы на основе вашего эмоционального профиля\n"
        )
        premium_text += "• Доступ к специализированным режимам поддержки\n"
        premium_text += "• Улучшенный контекст разговора (до 24 часов истории)\n"

        # Отправляем сообщение
        await message.answer(premium_text, parse_mode="HTML")

        logger.info(
            get_log_text("premium.premium_command_processed").format(user_id=user.id)
        )

    except Exception as e:
        logger.error(
            get_log_text("premium.premium_command_error").format(
                user_id=user.id, error=e
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
